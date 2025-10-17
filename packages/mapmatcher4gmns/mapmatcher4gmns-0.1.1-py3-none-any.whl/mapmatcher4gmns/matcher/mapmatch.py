import math
import os
from dataclasses import dataclass
from typing import List, Tuple, Dict, Optional, Set
import contextlib

import numpy as np
import pandas as pd
import networkx as nx
from shapely.geometry import Point, LineString, box
from shapely.strtree import STRtree
import multiprocessing
import io

from mapmatcher4gmns.networkclass.macronet import Network, Link
import sys
import threading
from tqdm import tqdm


@dataclass
class Candidate:
    link: Link
    proj_point_xy: Point
    proj_position: float
    link_length: float
    distance: float
    emission_logp: float


class _ShortestPathCache:
    def __init__(self, graph: nx.DiGraph, *, weight_key: str = 'weight', cutoff: Optional[float] = None):
        self.graph = graph
        self.weight_key = weight_key
        self.cutoff = cutoff
        self._dist_cache: Dict[int, Dict[int, float]] = {}
        self._path_cache: Dict[int, Dict[int, List[int]]] = {}

    def _ensure_source(self, source: int) -> None:
        if source in self._dist_cache:
            return
        if source not in self.graph:
            raise KeyError(f"source {source} not in graph")
        dist, paths = nx.single_source_dijkstra(
            self.graph,
            source,
            weight=self.weight_key,
            cutoff=self.cutoff,
        )
        self._dist_cache[source] = dist
        self._path_cache[source] = paths

    def get_distance(self, source: int, target: int) -> float:
        self._ensure_source(source)
        return self._dist_cache[source].get(target, float('inf'))

    def get_path(self, source: int, target: int) -> List[int]:
        self._ensure_source(source)
        return self._path_cache[source].get(target, [])

    def clear(self) -> None:
        self._dist_cache.clear()
        self._path_cache.clear()


class mapmatching:
    def __init__(self,
                 network: Network,
                 *,
                 # Data field configuration
                 agent_field: str = 'journey_id',
                 lng_field: str = 'longitude',
                 lat_field: str = 'latitude',
                 time_field: Optional[str] = 'local_time',
                 speed_field: Optional[str] = 'speed_mph',
                 heading_field: Optional[str] = 'heading',
                 # Time gap filtering
                 max_gap_seconds: float = 60.0,
                 # Core matching parameters
                 search_radius: float = 12.0,
                 noise_sigma: float = 30.0,
                 trans_weight: float = 6.0,
                 dist_penalty: float = 0.1,
                 max_candidates: int = 10,
                 use_heading: bool = True,
                 heading_sigma: float = 30.0,
                 time_format: Optional[str] = None,
                 extra_fields: Optional[List[str]] = None,
                 # Movement consistency parameters
                 turn_sigma: float = 45.0,
                 heading_len: float = 15.0,
                 route_gap: float = 15.0,
                 use_node_restrict: bool = False,
                 # Stationary point filtering
                 filter_dwell: bool = True,
                 dwell_dist: float = 5.0,
                 dwell_count: int = 2,
                 # Output configuration
                 export_csv: bool = True,
                 export_geo: bool = False,
                 out_dir: str = 'mapmatching',
                 export_route: bool = True,
                 result_file: str = 'matched_result.csv',
                 route_file: str = 'matched_route.csv',
                 # Processing constraints
                 min_link_len: float = 6.0,
                 # Speed and direction parameters
                 speed_limit: float = 200.0,
                 heading_weights: Optional[List[float]] = None,
                 max_agents: Optional[int] = None,
                 # Debug and control
                 debug: bool = False,
                 verbose: bool = True,
                 show_progress: bool = True,
                 # Parallel defaults
                 core_num: Optional[int] = None,
                 batch_size: Optional[int] = 1,
                 stop_event: Optional[threading.Event] = None,
                 ):
        self.net: Network = network
        
        # Core matching parameters
        self.search_radius = float(search_radius)
        self.noise_sigma = noise_sigma
        self.trans_weight = trans_weight
        self.dist_penalty = float(dist_penalty)
        self.max_candidates = max_candidates
        self.use_heading = use_heading
        self.heading_sigma = heading_sigma
        self.time_format = time_format
        self.extra_fields = [f for f in (extra_fields or []) if isinstance(f, str)]
        
        # Movement consistency parameters
        self.turn_sigma = max(1e-6, float(turn_sigma))
        self.heading_len = float(heading_len)
        self.route_gap = float(route_gap)
        self.use_node_restrict = bool(use_node_restrict)
        
        # Stationary point filtering
        self.filter_dwell = filter_dwell
        self.dwell_dist = dwell_dist
        self.dwell_count = int(max(1, dwell_count))
        
        # Output configuration
        self.export_csv = export_csv
        self.export_geo = export_geo
        self.out_dir = out_dir
        self.export_route = export_route
        self.route_file = route_file
        self.result_file = result_file
        
        # Processing constraints
        self.min_link_len = min_link_len
        self.max_agents = max_agents if (max_agents is None or max_agents > 0) else None
        
        # Speed and direction parameters
        self.speed_limit = float(speed_limit)
        self.heading_weights = None
        self.angle_slice = None
        if heading_weights is not None and isinstance(heading_weights, list) and len(heading_weights) > 0:
            self.heading_weights = [float(x) for x in heading_weights]
            self.angle_slice = 180.0 / float(len(self.heading_weights))
        # node restrict default
        self.gps_node_field = 'node_id'
        # debug / verbosity
        self.debug = bool(debug)
        self.verbose = bool(verbose)
        self.show_progress = bool(show_progress)
        # parallel defaults
        self.default_core_num: Optional[int] = None if (core_num is None or (isinstance(core_num, int) and core_num <= 0)) else int(core_num)
        self.default_batch_size: Optional[int] = 1 if (batch_size is None) else max(1, int(batch_size))

        # cache: mapping (from_link_id, to_link_id) -> node sequence used in transition
        self._ft_node_path: Dict[Tuple[int, int], List[int]] = {}

        self._build_spatial_index()
        self._build_graph()
        self._full_graph = self._G
        self._active_graph = self._G
        self._path_cutoff: Optional[float] = None
        self._full_path_cache = _ShortestPathCache(self._G, cutoff=self._path_cutoff)
        self._path_cache: _ShortestPathCache = self._full_path_cache
        self._xy_columns: Tuple[str, str] = ('__m4g_x', '__m4g_y')
        self._node_pair_cost: Dict[Tuple[int, int], float] = {}
        # cooperative cancel support
        self.stop_event = stop_event
        
        # Data field configuration
        self.agent_field = agent_field
        self.lng_field = lng_field
        self.lat_field = lat_field
        self.time_field = time_field
        self.heading_field = heading_field
        self.speed_field = speed_field
        self.max_gap_seconds = max_gap_seconds

    def _filter_dwell_points(self, sub: pd.DataFrame, lng_col: str, lat_col: str) -> pd.DataFrame:
        if (not self.filter_dwell) or (self.dwell_count <= 1) or (self.dwell_dist <= 0) or (len(sub) <= 2):
            return sub
        # compute XY
        pts: List[Point] = []
        for i in range(len(sub)):
            x, y = self.net.GT.from_latlon(float(sub.loc[i, lng_col]), float(sub.loc[i, lat_col]))
            pts.append(Point(x, y))
        # distances between consecutive points (index aligned to point i)
        dist = [0.0]
        for i in range(1, len(pts)):
            dist.append(float(pts[i].distance(pts[i-1])))
        small = pd.Series([d < self.dwell_dist for d in dist])
        # mark drops where last dwell_n moves are small
        drops = set()
        for i in range(len(sub)):
            if i == 0:
                continue
            ok = True
            for k in range(self.dwell_count):
                j = i - k
                if j < 1:
                    ok = False
                    break
                if not small.iloc[j]:
                    ok = False
                    break
            if ok:
                drops.add(i)
        # always keep first/last
        if len(sub) - 1 in drops:
            drops.remove(len(sub) - 1)
        keep_idx = [i for i in range(len(sub)) if i not in drops]
        if len(keep_idx) < 2:
            return sub
        out = sub.iloc[keep_idx].reset_index(drop=True)
        return out

    def _build_spatial_index(self):
        # use XY (meter) geometries for spatial search
        self._links: List[Link] = []
        self._geoms: List[LineString] = []
        self._linkid_to_index: Dict[int, int] = {}
        for _, link in self.net.link_dict.items():
            geom_xy = getattr(link, 'geometry_xy', None)
            if geom_xy is None:
                # fallback to create XY via GT if only lonlat geometry exists
                if link.geometry is not None:
                    geom_xy = self.net.GT.geo_from_latlon(link.geometry)
                    link.geometry_xy = geom_xy
            if geom_xy is not None and not geom_xy.is_empty:
                self._links.append(link)
                self._geoms.append(geom_xy)
        self._strtree = STRtree(self._geoms)
        # index -> link / geometry mappings
        self._index_to_link: List[Link] = list(self._links)
        self._wkb_to_index: Dict[bytes, int] = {g.wkb: i for i, g in enumerate(self._geoms)}
        for idx, lk in enumerate(self._index_to_link):
            try:
                self._linkid_to_index[int(lk.link_id)] = idx
            except Exception:
                continue
        # node -> link indices for node restriction
        self._node_to_indices: Dict[int, Set[int]] = {}
        for idx, lk in enumerate(self._index_to_link):
            if getattr(lk, 'from_node', None) is not None:
                self._node_to_indices.setdefault(int(lk.from_node.node_id), set()).add(idx)
            if getattr(lk, 'to_node', None) is not None:
                self._node_to_indices.setdefault(int(lk.to_node.node_id), set()).add(idx)

    def _build_graph(self):
        G = nx.DiGraph()
        for node_id, node in self.net.node_dict.items():
            G.add_node(node_id)
        for link_id, link in self.net.link_dict.items():
            if (link.from_node is None) or (link.to_node is None):
                continue
            u = link.from_node.node_id
            v = link.to_node.node_id
            length = getattr(link, 'length', None)
            if length is None:
                geom_xy = getattr(link, 'geometry_xy', None)
                if geom_xy is None and link.geometry is not None:
                    geom_xy = self.net.GT.geo_from_latlon(link.geometry)
                length = geom_xy.length if geom_xy is not None else 1.0
            G.add_edge(u, v, weight=float(length), link=link)
        self._G = G

    def _get_active_graph(self) -> nx.DiGraph:
        return self._active_graph if self._active_graph is not None else self._G

    def _make_path_cache(self, graph: nx.DiGraph) -> _ShortestPathCache:
        return _ShortestPathCache(graph, cutoff=self._path_cutoff)

    def _restore_full_graph(self) -> None:
        self._active_graph = self._full_graph
        self._path_cache = self._full_path_cache

    def _build_agent_graph(self, link_indices: Optional[Set[int]]) -> nx.DiGraph:
        if not link_indices:
            return self._full_graph
        indices = {idx for idx in link_indices if 0 <= idx < len(self._index_to_link)}
        if not indices:
            return self._full_graph
        # Avoid unnecessary subgraph creation when nearly all links are included
        if len(indices) >= max(1, int(0.9 * len(self._index_to_link))):
            return self._full_graph
        G = nx.DiGraph()
        for idx in indices:
            link = self._index_to_link[idx]
            if link is None:
                continue
            if getattr(link, 'from_node', None) is None or getattr(link, 'to_node', None) is None:
                continue
            u = int(link.from_node.node_id)
            v = int(link.to_node.node_id)
            length = getattr(link, 'length', None)
            if length is None:
                geom_xy = getattr(link, 'geometry_xy', None)
                length = geom_xy.length if geom_xy is not None else 1.0
            G.add_node(u)
            G.add_node(v)
            G.add_edge(u, v, weight=float(length), link=link)
        if G.number_of_edges() == 0:
            return self._full_graph
        return G

    @contextlib.contextmanager
    def _use_agent_graph(self, link_indices: Optional[Set[int]]):
        new_graph = self._build_agent_graph(link_indices)
        if new_graph is self._active_graph:
            yield
            return
        prev_graph = self._active_graph
        prev_cache = self._path_cache
        try:
            if new_graph is self._full_graph:
                self._restore_full_graph()
            else:
                self._active_graph = new_graph
                self._path_cache = self._make_path_cache(new_graph)
            yield
        finally:
            self._active_graph = prev_graph
            self._path_cache = prev_cache

    def _edge_data(self, u: int, v: int) -> Optional[Dict]:
        graph = self._get_active_graph()
        data = graph.get_edge_data(u, v)
        if data is None and graph is not self._full_graph:
            data = self._full_graph.get_edge_data(u, v)
        if data is None:
            data = graph.get_edge_data(v, u)
            if data is None and graph is not self._full_graph:
                data = self._full_graph.get_edge_data(v, u)
        return data

    def _node_path_to_links(self, node_path: List[int]) -> List[Link]:
        if not node_path or len(node_path) < 2:
            return []
        links: List[Link] = []
        for a, b in zip(node_path[:-1], node_path[1:]):
            data = self._edge_data(a, b)
            if not data:
                continue
            lk = data.get('link')
            if lk is not None:
                links.append(lk)
        return links

    def _project_point_onto_line(self, point_xy: Point, line_xy: LineString) -> Tuple[Point, float, float, float]:
        # distance in meters (XY)
        s = line_xy.project(point_xy)
        p = line_xy.interpolate(s)
        d = p.distance(point_xy)
        L = float(line_xy.length) if line_xy.length is not None else 0.0
        return p, float(d), float(s), L

    def _bearing_of_line(self, line_xy: LineString) -> float:
        x0, y0 = line_xy.coords[0]
        x1, y1 = line_xy.coords[-1]
        ang = math.degrees(math.atan2(y1 - y0, x1 - x0)) % 360.0
        return ang

    def _local_bearing(self, line_xy: LineString, at_point_xy: Point) -> float:
        try:
            L = float(line_xy.length)
            if L <= 0.0:
                return self._bearing_of_line(line_xy)
            s = line_xy.project(at_point_xy)
            # choose a small window around s to compute tangent
            delta = min(5.0, max(1.0, 0.05 * L))
            s1 = max(0.0, s - delta)
            s2 = min(L, s + delta)
            if abs(s2 - s1) < 1e-6:
                return self._bearing_of_line(line_xy)
            p1 = line_xy.interpolate(s1)
            p2 = line_xy.interpolate(s2)
            ang = math.degrees(math.atan2(p2.y - p1.y, p2.x - p1.x)) % 360.0
            return float(ang)
        except Exception:
            return self._bearing_of_line(line_xy)

    def _angle_diff(self, a: float, b: float) -> float:
        d = abs(a - b) % 360.0
        return d if d <= 180.0 else 360.0 - d

    def _emission_logp(self, distance: float, heading_deg: Optional[float], link_bearing: Optional[float],
                       est_speed_mph: Optional[float]) -> float:
        # Distance term: -0.5 * (dist_penalty * d / noise_sigma)^2
        logp = -0.5 * ((self.dist_penalty * distance) / max(self.noise_sigma, 1e-6)) ** 2
        # heading term
        if self.use_heading and heading_deg is not None and link_bearing is not None:
            dh = self._angle_diff(heading_deg, link_bearing)
            # If heading weights are provided, use them; otherwise use Gaussian
            if self.heading_weights is not None and self.angle_slice is not None:
                bin_idx = int(min(len(self.heading_weights) - 1, max(0, dh // self.angle_slice)))
                w = max(1e-8, self.heading_weights[bin_idx])
                logp += float(np.log(w))
            else:
                logp += - (dh * dh) / (2.0 * self.heading_sigma * self.heading_sigma)
        # Speed consistency (threshold): apply strong penalty only when exceeding threshold
        if est_speed_mph is not None and est_speed_mph >= 0:
            if est_speed_mph > self.speed_limit:
                logp += -10.0
        return float(logp)

    def _prefilter_link_indices_by_route_band(self, points_xy: List[Point]) -> Set[int]:
        if not points_xy:
            return set(range(len(self._geoms)))
        try:
            line = LineString([(p.x, p.y) for p in points_xy])
            gap = float(self.route_gap)
            if gap > 0:
                minx, miny, maxx, maxy = line.bounds
                band = box(minx - gap, miny - gap, maxx + gap, maxy + gap)
            else:
                band = line.envelope
            items = self._strtree.query(band)
            idx_set: Set[int] = set()
            for it in items:
                if hasattr(it, 'wkb'):
                    idx = self._wkb_to_index.get(it.wkb)
                    if idx is None:
                        continue
                else:
                    try:
                        idx = int(it)
                    except Exception:
                        continue
                if 0 <= idx < len(self._geoms):
                    idx_set.add(idx)
            return idx_set if idx_set else set(range(len(self._geoms)))
        except Exception:
            return set(range(len(self._geoms)))

    def _candidates_from_point_xy(self, point_xy: Optional[Point],
                                  *, allowed_indices: Optional[Set[int]] = None) -> List[Candidate]:
        if point_xy is None:
            return []
        idx_list = self._candidate_indices_for_point(point_xy, allowed_indices)
        cand_pairs: List[Tuple[float, Candidate]] = []
        gap = float(self.search_radius)
        for idx in idx_list:
            geom = self._geoms[idx]
            link = self._index_to_link[idx]
            proj_p, dist, proj_s, link_len = self._project_point_onto_line(point_xy, geom)
            if dist > gap:
                continue
            cand_pairs.append((dist, Candidate(link=link,
                                               proj_point_xy=proj_p,
                                               proj_position=proj_s,
                                               link_length=link_len,
                                               distance=dist,
                                               emission_logp=0.0)))
        if not cand_pairs:
            return []
        cand_pairs.sort(key=lambda x: x[0])
        return [c for _, c in cand_pairs[: self.max_candidates]]

    def _candidates_for_point(self, lon: float, lat: float, heading_deg: Optional[float],
                              *, allowed_indices: Optional[Set[int]] = None) -> List[Candidate]:
        x, y = self.net.GT.from_latlon(lon, lat)
        point_xy = Point(x, y)
        return self._candidates_from_point_xy(point_xy, allowed_indices=allowed_indices)

    def _batch_candidates(self,
                          points_xy: List[Optional[Point]],
                          per_point_allowed: List[Optional[Set[int]]]) -> List[List[Candidate]]:
        results: List[List[Candidate]] = [[] for _ in points_xy]
        valid: List[Tuple[int, Point]] = [(idx, p) for idx, p in enumerate(points_xy) if p is not None]
        if not valid:
            return results
        gap = float(self.search_radius)
        for orig_idx, point_xy in valid:
            allowed = per_point_allowed[orig_idx]
            idx_list = self._candidate_indices_for_point(point_xy, allowed)
            for idx in idx_list:
                geom = self._geoms[idx]
                link = self._index_to_link[idx]
                proj_p, dist, proj_s, link_len = self._project_point_onto_line(point_xy, geom)
                if dist > gap:
                    continue
                results[orig_idx].append((dist, Candidate(link=link,
                                                          proj_point_xy=proj_p,
                                                          proj_position=proj_s,
                                                          link_length=link_len,
                                                          distance=dist,
                                                          emission_logp=0.0)))
        for idx in range(len(results)):
            cand_pairs = results[idx]
            if not cand_pairs:
                results[idx] = []
                continue
            cand_pairs.sort(key=lambda x: x[0])
            results[idx] = [c for _, c in cand_pairs[: self.max_candidates]]
        return results

    def _candidate_indices_for_point(self,
                                     point_xy: Point,
                                     allowed_indices: Optional[Set[int]]) -> List[int]:
        gap = float(self.search_radius)
        rect = box(point_xy.x - gap, point_xy.y - gap, point_xy.x + gap, point_xy.y + gap)
        try:
            items = self._strtree.query(rect)
        except Exception:
            items = []
        idx_list: List[int] = []
        for it in items:
            if hasattr(it, 'wkb'):
                idx = self._wkb_to_index.get(it.wkb)
                if idx is None:
                    continue
            else:
                try:
                    idx = int(it)
                except Exception:
                    continue
            if idx < 0 or idx >= len(self._geoms):
                continue
            if allowed_indices is not None and idx not in allowed_indices:
                continue
            idx_list.append(idx)
        return idx_list

    def _compute_transition_scores(self,
                                   prev_states: List[Candidate],
                                   curr_states: List[Candidate],
                                   adj_dis: float,
                                   prev_dp: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        m = len(prev_states)
        n = len(curr_states)
        if m == 0 or n == 0:
            return np.full((n,), -np.inf, dtype=float), np.full((n,), -1, dtype=int)

        prev_proj = np.array([c.proj_position for c in prev_states], dtype=float)
        curr_proj = np.array([c.proj_position for c in curr_states], dtype=float)
        prev_tail = np.array([max(0.0, c.link_length - c.proj_position) for c in prev_states], dtype=float)
        curr_head = np.array([max(0.0, c.proj_position) for c in curr_states], dtype=float)
        prev_link_ids = np.array([int(getattr(c.link, 'link_id', -1)) for c in prev_states], dtype=int)
        curr_link_ids = np.array([int(getattr(c.link, 'link_id', -1)) for c in curr_states], dtype=int)
        prev_to_nodes = np.array([int(c.link.to_node.node_id) if c.link and c.link.to_node else -1 for c in prev_states], dtype=int)
        curr_from_nodes = np.array([int(c.link.from_node.node_id) if c.link and c.link.from_node else -1 for c in curr_states], dtype=int)

        route_len = np.full((m, n), np.inf, dtype=float)

        same_mask = prev_link_ids[:, None] == curr_link_ids[None, :]
        if np.any(same_mask):
            route_len[same_mask] = np.abs(prev_proj[:, None] - curr_proj[None, :])[same_mask]

        for i in range(m):
            u = prev_to_nodes[i]
            if u < 0:
                continue
            tail_val = prev_tail[i]
            for j in range(n):
                if same_mask[i, j]:
                    continue
                v = curr_from_nodes[j]
                if v < 0:
                    continue
                key = (u, v)
                mid_cost = self._node_pair_cost.get(key)
                if mid_cost is None:
                    mid_cost = self._shortest_path_length(u, v)
                    self._node_pair_cost[key] = mid_cost
                if math.isinf(mid_cost):
                    continue
                route_len[i, j] = tail_val + mid_cost + curr_head[j]

        trans_matrix = np.full((m, n), -1e12, dtype=float)
        valid_mask = np.isfinite(route_len)
        if np.any(valid_mask):
            beta = max(self.trans_weight, 1e-6)
            gap_vals = np.abs(adj_dis - route_len[valid_mask])
            trans_matrix[valid_mask] = - self.dist_penalty * gap_vals / beta

        scores = prev_dp[:, None] + trans_matrix
        best_indices = np.argmax(scores, axis=0)
        best_scores = scores[best_indices, np.arange(n)]

        invalid_mask = ~np.isfinite(best_scores) | (best_scores <= -1e11)
        best_scores = best_scores.astype(float)
        best_scores[invalid_mask] = -np.inf
        best_indices = best_indices.astype(int)
        # Don't set best_indices to -1 for invalid scores - keep the best available transition
        # This ensures backtracking continuity even when probabilities are very low
        return best_scores, best_indices

    def _ensure_xy_columns(self, df: pd.DataFrame, lng_col: str, lat_col: str) -> Tuple[str, str]:
        x_col, y_col = self._xy_columns
        if x_col in df.columns and y_col in df.columns:
            return x_col, y_col
        xs: List[float] = []
        ys: List[float] = []
        lng_vals = df[lng_col].to_numpy()
        lat_vals = df[lat_col].to_numpy()
        for lon, lat in zip(lng_vals, lat_vals):
            try:
                if pd.isna(lon) or pd.isna(lat):
                    xs.append(np.nan)
                    ys.append(np.nan)
                else:
                    x, y = self.net.GT.from_latlon(float(lon), float(lat))
                    xs.append(float(x))
                    ys.append(float(y))
            except Exception:
                xs.append(np.nan)
                ys.append(np.nan)
        df[x_col] = xs
        df[y_col] = ys
        return x_col, y_col

    def _mask_points_within_buffer(self,
                                   points_xy: List[Optional[Point]],
                                   per_point_allowed: List[Optional[Set[int]]]) -> List[bool]:
        mask = [False] * len(points_xy)
        valid: List[Tuple[int, Point]] = [(idx, p) for idx, p in enumerate(points_xy) if p is not None]
        if not valid:
            return mask
        gap = float(self.search_radius)
        for orig_idx, point_xy in valid:
            allowed = per_point_allowed[orig_idx] if per_point_allowed else None
            idx_list = self._candidate_indices_for_point(point_xy, allowed)
            if not idx_list:
                continue
            for idx in idx_list:
                geom = self._geoms[idx]
                _, dist, _, _ = self._project_point_onto_line(point_xy, geom)
                if dist <= gap:
                    mask[orig_idx] = True
                    break
        return mask

    def _shortest_path_length(self, u: int, v: int) -> float:
        caches = (self._path_cache,) if self._path_cache is self._full_path_cache else (self._path_cache, self._full_path_cache)
        for cache in caches:
            try:
                length = cache.get_distance(u, v)
            except KeyError:
                continue
            if length is None or math.isinf(length):
                continue
            return float(length)
        return float('inf')

    def _shortest_path_nodes(self, u: int, v: int) -> List[int]:
        caches = (self._path_cache,) if self._path_cache is self._full_path_cache else (self._path_cache, self._full_path_cache)
        for cache in caches:
            try:
                path = cache.get_path(u, v)
            except KeyError:
                continue
            if path:
                return list(path)
        return []

    def _shortest_path_links(self, u: int, v: int) -> List[Link]:
        node_path = self._shortest_path_nodes(u, v)
        return self._node_path_to_links(node_path)

    def _shortest_path_links_undirected(self, u: int, v: int) -> List[Link]:
        graph = self._get_active_graph()
        try:
            UG = graph.to_undirected()
            node_path = nx.shortest_path(UG, u, v, weight='weight')
            return self._node_path_to_links(node_path)
        except Exception:
            pass
        if graph is not self._full_graph:
            try:
                UG = self._full_graph.to_undirected()
                node_path = nx.shortest_path(UG, u, v, weight='weight')
                return self._node_path_to_links(node_path)
            except Exception:
                pass
        return []

    def _connect_links_with_mids(self, prev_link: Link, curr_link: Link) -> List[Link]:
        candidates: List[Tuple[List[Link], float]] = []
        pairs: List[Tuple[Optional[int], Optional[int]]] = []
        u1 = prev_link.to_node.node_id if prev_link and prev_link.to_node else None
        u2 = prev_link.from_node.node_id if prev_link and prev_link.from_node else None
        v1 = curr_link.from_node.node_id if curr_link and curr_link.from_node else None
        v2 = curr_link.to_node.node_id if curr_link and curr_link.to_node else None
        for u in (u1, u2):
            for v in (v1, v2):
                if (u is not None) and (v is not None):
                    pairs.append((u, v))

        def path_cost(ls: List[Link]) -> float:
            total = 0.0
            for lk in ls:
                L = getattr(lk, 'length', None)
                if L is None:
                    geom = getattr(lk, 'geometry_xy', None)
                    if geom is not None:
                        L = float(geom.length)
                    else:
                        L = 1.0
                total += float(L)
            return total

        for (u, v) in pairs:
            ls = self._shortest_path_links(u, v)
            if ls:
                candidates.append((ls, path_cost(ls)))
            else:
                ls2 = self._shortest_path_links_undirected(u, v)
                if ls2:
                    candidates.append((ls2, path_cost(ls2)))
        if not candidates:
            return []
        candidates.sort(key=lambda x: x[1])
        return candidates[0][0]

    def _nearest_endpoint_node_id(self, link: Link, lon: float, lat: float) -> Optional[int]:
        try:
            x, y = self.net.GT.from_latlon(lon, lat)
            p = Point(x, y)
            line = link.geometry_xy
            if line is None:
                if link.geometry is not None:
                    line = self.net.GT.geo_from_latlon(link.geometry)
                else:
                    return None
            s = line.project(p)
            L = float(line.length) if line.length is not None else 0.0
            if (link.from_node is None) or (link.to_node is None):
                return None
            # choose nearest endpoint by along-line distance
            if L <= 0.0:
                return link.from_node.node_id
            return link.from_node.node_id if s <= (L - s) else link.to_node.node_id
        except Exception:
            return None

    def _transition_logp(self, prev_c: Candidate, curr_c: Candidate, adj_dis: float) -> float:
        # Compute route length (including tail/head partials) and straight-line gap (dis_gap)
        if prev_c.link is curr_c.link:
            route_len = abs(curr_c.proj_position - prev_c.proj_position)
        else:
            # Strictly from prev.to_node -> curr.from_node
            try:
                u = int(prev_c.link.to_node.node_id)
                v = int(curr_c.link.from_node.node_id)
            except Exception:
                return -1e12
            key = (u, v)
            mid_cost = self._node_pair_cost.get(key)
            if mid_cost is None:
                mid_cost = self._shortest_path_length(u, v)
                self._node_pair_cost[key] = mid_cost
            if math.isinf(mid_cost):
                return -1e12
            # Remaining tail of previous + middle shortest path + head of next
            route_len = max(0.0, prev_c.link_length - prev_c.proj_position) + mid_cost + max(0.0, curr_c.proj_position)

        dis_gap = abs(float(adj_dis) - float(route_len))
        # Transition log p = - dist_penalty * dis_gap / trans_weight
        return - self.dist_penalty * dis_gap / max(self.trans_weight, 1e-6)

    def _filter_journeys_with_large_time_gaps(self, gps_df: pd.DataFrame, agent_field: str, time_field: str, max_gap_seconds: float = 60.0) -> pd.DataFrame:
        """
        Filter out journeys that have time gaps larger than max_gap_seconds between consecutive points.
        
        Args:
            gps_df: GPS DataFrame sorted by agent and time
            max_gap_seconds: Maximum allowed time gap in seconds (default: 60.0)
            
        Returns:
            Filtered GPS DataFrame with problematic journeys removed
        """
        if gps_df.empty:
            return gps_df
            
        # Create a temporary time column for calculation
        tmp_time_col = '__temp_time__'
        
        try:
            # Parse time column
            if self.time_format:
                gps_df[tmp_time_col] = pd.to_datetime(gps_df[self.time_field], errors='coerce', format=self.time_format)
            else:
                gps_df[tmp_time_col] = pd.to_datetime(gps_df[self.time_field], errors='coerce')
            
            # Get valid journeys (those with valid timestamps)
            valid_mask = gps_df[tmp_time_col].notna()
            valid_df = gps_df[valid_mask].copy()
            
            if valid_df.empty:
                print("No valid timestamps found, keeping all data")
                del gps_df[tmp_time_col]
                return gps_df
            
            # Group by journey and check time gaps
            journeys_to_keep = []
            journeys_to_remove = []
            
            for journey_id, journey_data in valid_df.groupby(agent_field):
                if len(journey_data) <= 1:
                    # Single point journeys are always kept
                    journeys_to_keep.append(journey_id)
                    continue
                
                # Sort by time to ensure proper order
                journey_sorted = journey_data.sort_values(by=tmp_time_col)
                
                # Calculate time differences between consecutive points
                time_diffs = journey_sorted[tmp_time_col].diff().dt.total_seconds()
                
                # Check if any time gap exceeds the threshold
                max_gap = time_diffs.max()
                if pd.isna(max_gap) or max_gap <= max_gap_seconds:
                    journeys_to_keep.append(journey_id)
                else:
                    journeys_to_remove.append(journey_id)
            
            # Filter the original DataFrame
            if journeys_to_remove:
                print(f"Removing {len(journeys_to_remove)} journeys with time gaps > {max_gap_seconds}s")
                print(f"Keeping {len(journeys_to_keep)} journeys")
                
                # Keep only journeys without large time gaps
                filtered_df = gps_df[gps_df[agent_field].isin(journeys_to_keep)].copy()
                
                # Also remove journeys with invalid timestamps (if any)
                invalid_journeys = gps_df[~valid_mask][agent_field].unique()
                if len(invalid_journeys) > 0:
                    print(f"Also removing {len(invalid_journeys)} journeys with invalid timestamps")
                    filtered_df = filtered_df[~filtered_df[agent_field].isin(invalid_journeys)]
                
                del filtered_df[tmp_time_col]
                return filtered_df
            else:
                print(f"All {len(journeys_to_keep)} journeys have acceptable time gaps")
                del gps_df[tmp_time_col]
                return gps_df
                
        except Exception as e:
            print(f"Error during time gap filtering: {e}")
            # Return original data if filtering fails
            if tmp_time_col in gps_df.columns:
                del gps_df[tmp_time_col]
            return gps_df

    def match(self, gps_df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict, List]:
        # If defaults indicate parallel, delegate to multi_core_match
        try:
            # Use parallel when constructor requested cores > 1 or batch_size >= 1
            cpu_cnt = os.cpu_count() or 1
            desired_core = self.default_core_num if (self.default_core_num is not None) else min(2, cpu_cnt)
            if desired_core and int(desired_core) > 1:
                return self.multi_core_match(gps_df, core_num=desired_core, batch_size=self.default_batch_size)
        except Exception:
            pass

        # Sort GPS data by agent and time first - CRITICAL for proper matching
        if self.time_field and self.time_field in gps_df.columns:
            tmp_col = '__time_sort__'
            
            if self.time_format:
                # Use the specified format strictly
                try:
                    gps_df[tmp_col] = pd.to_datetime(gps_df[self.time_field], errors='coerce', format=self.time_format)
                    valid_time_count = gps_df[tmp_col].notna().sum()
                    print(f"Time parsing with specified format '{self.time_format}': {valid_time_count}/{len(gps_df)} rows have valid time")
                    
                    if valid_time_count == 0:
                        print("Warning: No valid time data found with the specified format.")
                        print(f"Sample time values: {gps_df[self.time_field].head().tolist()}")
                        print(f"Specified format: {self.time_format}")
                        # Keep all data but sort by agent only
                        gps_df = gps_df.sort_values(by=[self.agent_field], ascending=True, ignore_index=True)
                    else:
                        # Remove rows with invalid time and sort by agent and time
                        gps_df = gps_df.dropna(subset=[tmp_col])
                        if not gps_df.empty:
                            gps_df = gps_df.sort_values(by=[self.agent_field, tmp_col], ascending=[True, True], ignore_index=True)
                            print(f"GPS data sorted by {self.agent_field} and {self.time_field}")
                except Exception as e:
                    print(f"Error parsing time with specified format '{self.time_format}': {e}")
                    # Keep all data but sort by agent only
                    gps_df = gps_df.sort_values(by=[self.agent_field], ascending=True, ignore_index=True)
            else:
                # No format specified, use auto-detection
                try:
                    gps_df[tmp_col] = pd.to_datetime(gps_df[self.time_field], errors='coerce', infer_datetime_format=True)
                    valid_time_count = gps_df[tmp_col].notna().sum()
                    print(f"Time parsing with auto-detection: {valid_time_count}/{len(gps_df)} rows have valid time")
                    
                    if valid_time_count == 0:
                        print("Warning: No valid time data found with auto-detection.")
                        print(f"Sample time values: {gps_df[self.time_field].head().tolist()}")
                        # Keep all data but sort by agent only
                        gps_df = gps_df.sort_values(by=[self.agent_field], ascending=True, ignore_index=True)
                    else:
                        # Remove rows with invalid time and sort by agent and time
                        gps_df = gps_df.dropna(subset=[tmp_col])
                        if not gps_df.empty:
                            gps_df = gps_df.sort_values(by=[self.agent_field, tmp_col], ascending=[True, True], ignore_index=True)
                            print(f"GPS data sorted by {self.agent_field} and {self.time_field}")
                except Exception as e:
                    print(f"Auto-detection failed: {e}")
                    # Keep all data but sort by agent only
                    gps_df = gps_df.sort_values(by=[self.agent_field], ascending=True, ignore_index=True)
            
            del gps_df[tmp_col]
        else:
            # Sort by agent only if no time field
            gps_df = gps_df.sort_values(by=[self.agent_field], ascending=True, ignore_index=True)
        
        # Filter out journeys with large time gaps
        if self.time_field and self.time_field in gps_df.columns:
            gps_df = self._filter_journeys_with_large_time_gaps(gps_df, self.agent_field, self.time_field, self.max_gap_seconds)
        
        # group by agent
        assert self.agent_field in gps_df.columns
        x_col, y_col = self._ensure_xy_columns(gps_df, self.lng_field, self.lat_field)
        agents_all = gps_df[self.agent_field].unique().tolist()
        agents = list(agents_all)
        if self.max_agents is not None:
            try:
                limit = int(self.max_agents)
                if limit > 0:
                    agents = agents[:limit]
            except Exception:
                pass
        if self.max_agents is not None and len(agents) < len(agents_all):
            print(f"limiting processed agents to {len(agents)} (max_agents={self.max_agents})")
        results: List[pd.DataFrame] = []
        warn_info: Dict = {}
        err_agents: List = []
        def _finalize_results(current_results: List[pd.DataFrame]) -> pd.DataFrame:
            base_desired = [self.agent_field, 'seq', 'time', 'link_id', 'from_node_id', 'to_node_id', 'longitude', 'latitude', 'speed_mph', 'match_heading', 'route_dis']
            user_keep = [c for c in self.extra_fields if (c not in base_desired and c in gps_df.columns)]
            desired_cols = base_desired + user_keep
            if current_results:
                non_empty = [df for df in current_results if isinstance(df, pd.DataFrame) and not df.empty and df.columns.size > 0]
                if non_empty:
                    # Filter out empty DataFrames and DataFrames with all-NA columns to avoid FutureWarning
                    filtered_dfs = []
                    for df in non_empty:
                        if not df.empty:
                            # Remove columns that are all NA
                            df_clean = df.dropna(axis=1, how='all')
                            if not df_clean.empty:
                                filtered_dfs.append(df_clean)
                    
                    if filtered_dfs:
                        res_local = pd.concat(filtered_dfs, ignore_index=True)
                    else:
                        res_local = pd.DataFrame(columns=desired_cols)
                else:
                    res_local = pd.DataFrame(columns=desired_cols)
            else:
                res_local = pd.DataFrame(columns=desired_cols)
            # reorder columns if present
            for c in desired_cols:
                if c not in res_local.columns:
                    res_local[c] = None
            res_local = res_local[desired_cols]
            # ensure output order: prefer agent+time if available, else agent+seq
            try:
                if not res_local.empty and (self.agent_field in res_local.columns):
                    if 'time' in res_local.columns and res_local['time'].notna().any():
                        tmpc = '__sort_time__'
                        try:
                            if self.time_format:
                                res_local[tmpc] = pd.to_datetime(res_local['time'], errors='coerce', format=self.time_format)
                            else:
                                res_local[tmpc] = pd.to_datetime(res_local['time'], errors='coerce', infer_datetime_format=True)
                            res_local = res_local.sort_values(by=[self.agent_field, tmpc], ascending=[True, True], ignore_index=True)
                            del res_local[tmpc]
                        except Exception:
                            if 'seq' in res_local.columns:
                                res_local = res_local.sort_values(by=[self.agent_field, 'seq'], ascending=[True, True], ignore_index=True)
                    elif 'seq' in res_local.columns:
                        res_local = res_local.sort_values(by=[self.agent_field, 'seq'], ascending=[True, True], ignore_index=True)
            except Exception:
                pass
            # optional export
            try:
                import os
                if self.export_csv:
                    os.makedirs(self.out_dir, exist_ok=True)
                    res_local.to_csv(os.path.join(self.out_dir, self.result_file), index=False)
                    if self.export_route and not res_local.empty:
                        # build expanded route per agent using recorded ft_node_path (4gmns-like)
                        route_rows = []
                        for agent, df_g in res_local.groupby(self.agent_field):
                            df_g = df_g.sort_values(by=['seq' if 'seq' in df_g.columns else 'time'], ascending=True)
                            df_g = df_g.reset_index(drop=True)
                            expanded: List[int] = []
                            if len(df_g) == 0:
                                continue
                            def _append_link_id(lid: int):
                                if not expanded or expanded[-1] != int(lid):
                                    expanded.append(int(lid))
                            first_link = self.net.link_dict.get(int(df_g.at[0, 'link_id']))
                            if first_link is None:
                                continue
                            _append_link_id(int(first_link.link_id))
                            for i in range(len(df_g) - 1):
                                cur_lk = self.net.link_dict.get(int(df_g.at[i, 'link_id']))
                                nxt_lk = self.net.link_dict.get(int(df_g.at[i+1, 'link_id']))
                                if cur_lk is None or nxt_lk is None:
                                    continue
                                # if already continuous or same link
                                if (int(cur_lk.link_id) == int(nxt_lk.link_id)) or \
                                   (getattr(cur_lk, 'to_node', None) and getattr(nxt_lk, 'from_node', None) and \
                                    int(cur_lk.to_node.node_id) == int(nxt_lk.from_node.node_id)):
                                    _append_link_id(int(nxt_lk.link_id))
                                    continue
                                key = (int(cur_lk.link_id), int(nxt_lk.link_id))
                                nodes = self._ft_node_path.get(key, [])
                                if not nodes:
                                    try:
                                        u = int(cur_lk.to_node.node_id)
                                        v = int(nxt_lk.from_node.node_id)
                                        nodes = self._shortest_path_nodes(u, v)
                                    except Exception:
                                        nodes = []
                                if nodes:
                                    # map nodes to links along path
                                    for j in range(len(nodes) - 1):
                                        data = self._edge_data(nodes[j], nodes[j+1])
                                        if not data:
                                            continue
                                        lk = data.get('link')
                                        if lk is None:
                                            continue
                                        _append_link_id(int(lk.link_id))
                                _append_link_id(int(nxt_lk.link_id))
                            # emit rows
                            for step_idx, lid in enumerate(expanded):
                                lk = self.net.link_dict.get(int(lid))
                                route_rows.append({
                                    self.agent_field: agent,
                                    'step': step_idx,
                                    'link_id': int(lid),
                                    'from_node_id': int(lk.from_node.node_id) if lk and lk.from_node else None,
                                    'to_node_id': int(lk.to_node.node_id) if lk and lk.to_node else None,
                                })
                        if route_rows:
                            route_df = pd.DataFrame(route_rows)
                            route_df = route_df.sort_values(by=[self.agent_field, 'step'], ascending=[True, True], ignore_index=True)
                            
                            grouped_routes = []
                            for journey_id, group in route_df.groupby(self.agent_field):
                                link_ids = group['link_id'].astype(str).tolist()
                                grouped_routes.append({
                                    'journey_id': journey_id,
                                    'link_ids': ','.join(link_ids)
                                })
                            
                            grouped_route_df = pd.DataFrame(grouped_routes)
                            grouped_route_df.to_csv(os.path.join(self.out_dir, self.route_file), index=False)
                if self.export_geo and not res_local.empty:
                    try:
                        import geopandas as gpd
                        rows = []
                        for _, r in res_local.iterrows():
                            lk = self.net.link_dict.get(int(r['link_id']))
                            if lk is None or lk.geometry is None:
                                continue
                            rows.append({'journey_id': r[self.agent_field], 'seq': int(r['seq']), 'link_id': int(r['link_id']), 'geometry': lk.geometry})
                        if rows:
                            gdf = gpd.GeoDataFrame(rows, geometry='geometry', crs='EPSG:4326')
                            gdf.to_file(os.path.join(self.out_dir, 'matched_result.geojson'), driver='GeoJSON')
                    except Exception:
                        pass
            except Exception:
                pass
            return res_local

        total_agents = len(agents)
        if self.show_progress:
            with tqdm(total=total_agents,
                      desc="Processing agents",
                      dynamic_ncols=True,
                      ascii=True,
                      bar_format="{desc}: {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]",
                      file=sys.stdout) as pbar:
                for a in agents:
                    if self.stop_event is not None and self.stop_event.is_set():
                        if self.verbose:
                            print("Stopping Map Matching process...")
                        res = _finalize_results(results)
                        return res, warn_info, err_agents
                    try:
                        sub = gps_df[gps_df[self.agent_field] == a].copy()
                        self._current_agent = a
                        sub = sub.reset_index(drop=True)
                        if self.filter_dwell:
                            sub = self._filter_dwell_points(sub, self.lng_field, self.lat_field)
                        base_cols = {'seq','time','link_id','from_node_id','to_node_id','longitude','latitude','speed_mph','dis_to_next','match_heading','route_dis', self.agent_field}
                        keep_user_fields = [c for c in self.extra_fields if (c in sub.columns and c not in base_cols)]
                        allowed_idx: Optional[Set[int]] = None
                        if self.route_gap and self.route_gap > 0:
                            pts_xy: List[Point] = []
                            for _, r in sub.iterrows():
                                try:
                                    x, y = float(r[x_col]), float(r[y_col])
                                    pts_xy.append(Point(x, y))
                                except Exception:
                                    continue
                            allowed_idx = self._prefilter_link_indices_by_route_band(pts_xy)
                        path_df = self._match_one_agent(sub, self.lng_field, self.lat_field, self.time_field, self.heading_field, self.speed_field, keep_user_fields, allowed_idx, x_col, y_col)
                        path_df[self.agent_field] = a
                        results.append(path_df)
                    except Exception as e:
                        err_agents.append(a)
                        warn_info[str(a)] = repr(e)
                    finally:
                        pbar.update(1)
        else:
            for a in agents:
                if self.stop_event is not None and self.stop_event.is_set():
                    if self.verbose:
                        print("Stopping Map Matching process...")
                    res = _finalize_results(results)
                    return res, warn_info, err_agents
                try:
                    sub = gps_df[gps_df[self.agent_field] == a].copy()
                    self._current_agent = a
                    sub = sub.reset_index(drop=True)
                    if self.filter_dwell:
                        sub = self._filter_dwell_points(sub, self.lng_field, self.lat_field)
                    base_cols = {'seq','time','link_id','from_node_id','to_node_id','longitude','latitude','speed_mph','dis_to_next','match_heading','route_dis', self.agent_field}
                    keep_user_fields = [c for c in self.extra_fields if (c in sub.columns and c not in base_cols)]
                    allowed_idx: Optional[Set[int]] = None
                    if self.route_gap and self.route_gap > 0:
                        pts_xy: List[Point] = []
                        for _, r in sub.iterrows():
                            try:
                                x, y = float(r[x_col]), float(r[y_col])
                                pts_xy.append(Point(x, y))
                            except Exception:
                                continue
                        allowed_idx = self._prefilter_link_indices_by_route_band(pts_xy)
                    path_df = self._match_one_agent(sub, self.lng_field, self.lat_field, self.time_field, self.heading_field, self.speed_field, keep_user_fields, allowed_idx, x_col, y_col)
                    path_df[self.agent_field] = a
                    results.append(path_df)
                except Exception as e:
                    err_agents.append(a)
                    warn_info[str(a)] = repr(e)

        if self.verbose:
            print("Map Matching Completed")
        res = _finalize_results(results)
        return res, warn_info, err_agents

    def _match_one_agent(self, sub: pd.DataFrame,
                          lng_col: str,
                          lat_col: str,
                          time_col: Optional[str],
                          heading_col: Optional[str],
                          speed_col: Optional[str],
                          keep_user_fields: Optional[List[str]],
                          allowed_indices: Optional[Set[int]],
                          x_col: str,
                          y_col: str) -> pd.DataFrame:
        base_allowed = None if allowed_indices is None else set(allowed_indices)
        node_restrict_active = self.use_node_restrict and (self.gps_node_field in sub.columns)

        def _build_allowed_list(df: pd.DataFrame) -> List[Optional[Set[int]]]:
            res: List[Optional[Set[int]]] = []
            for idx in range(len(df)):
                allowed_t = None if base_allowed is None else set(base_allowed)
                if node_restrict_active:
                    try:
                        nid_val = df.iloc[idx][self.gps_node_field]
                    except Exception:
                        nid_val = None
                    if pd.notna(nid_val):
                        node_set = self._node_to_indices.get(int(nid_val), set())
                        if node_set:
                            node_set = set(node_set)
                            if allowed_t is None:
                                allowed_t = node_set
                            else:
                                allowed_t &= node_set
                        else:
                            allowed_t = set()
                res.append(allowed_t if allowed_t is not None else None)
            return res

        def _build_points(df: pd.DataFrame) -> List[Optional[Point]]:
            xs = df[x_col].to_numpy()
            ys = df[y_col].to_numpy()
            pts: List[Optional[Point]] = []
            for xv, yv in zip(xs, ys):
                if np.isnan(xv) or np.isnan(yv):
                    pts.append(None)
                else:
                    pts.append(Point(float(xv), float(yv)))
            return pts

        per_point_allowed_initial = _build_allowed_list(sub)

        gps_xy_initial = _build_points(sub)

        keep_mask = self._mask_points_within_buffer(gps_xy_initial, per_point_allowed_initial)
        keep_indices = [i for i, keep in enumerate(keep_mask) if keep]
        if not keep_indices:
            return pd.DataFrame(columns=['seq', 'time', 'link_id', 'from_node_id', 'to_node_id', 'longitude', 'latitude', 'speed_mph', 'dis_to_next', 'match_heading', 'route_dis'])
        if len(keep_indices) != len(sub):
            sub = sub.iloc[keep_indices].reset_index(drop=True)
        else:
            sub = sub.reset_index(drop=True)

        per_point_allowed = _build_allowed_list(sub)

        gps_xy_all = _build_points(sub)

        obs = []
        prev_xy: Optional[Point] = None
        prev_time = None
        for i, row in sub.iterrows():
            lon = float(row[lng_col])
            lat = float(row[lat_col])
            heading_deg = None
            if heading_col and heading_col in sub.columns:
                try:
                    heading_deg = float(row[heading_col])
                except Exception:
                    heading_deg = None
            point_xy = gps_xy_all[i]
            # estimate speed mph from consecutive points
            est_speed_mph = None
            if prev_xy is not None and prev_time is not None and time_col and time_col in sub.columns:
                try:
                    t_curr = pd.to_datetime(row[time_col], errors='coerce')
                    if pd.notna(t_curr) and pd.notna(prev_time):
                        dt = (t_curr.value - prev_time.value) / 1e9
                        if dt > 0 and point_xy is not None and prev_xy is not None:
                            d = point_xy.distance(prev_xy)
                            est_speed_mph = d / dt * 2.23693629
                            prev_xy = point_xy
                            prev_time = t_curr
                        else:
                            pass
                    else:
                        prev_xy = None
                        prev_time = None
                except Exception:
                    prev_xy = None
                    prev_time = None
            else:
                prev_xy = point_xy
                try:
                    prev_time = pd.to_datetime(row[time_col], errors='coerce') if (time_col and time_col in sub.columns) else None
                except Exception:
                    prev_time = None
            obs.append((lon, lat, heading_deg, est_speed_mph))

        candidate_lists = self._batch_candidates(gps_xy_all, per_point_allowed)

        with self._use_agent_graph(allowed_indices):
            backptr: List[Dict[int, int]] = []  # time(step) -> {state_idx: prev_state_idx}
            states: List[List[Candidate]] = []
            dp: List[np.ndarray] = []
            kept_indices: List[int] = []  # map step index -> original row index

            # iterate all observations; drop those with no candidates (strict)
            initialized = False
            for t in range(len(obs)):
                lont, latt, hdt, vt = obs[t]
                candt = candidate_lists[t]
                if not candt:
                    # skip this observation (drop)
                    continue
                # emission for this time
                for j in range(len(candt)):
                    bearing = self._bearing_of_line(candt[j].link.geometry_xy)
                    candt[j].emission_logp = self._emission_logp(
                        candt[j].distance,
                        (None if not initialized else hdt),
                        bearing,
                        vt,
                    )
                if not initialized:
                    if self.debug:
                        try:
                            top_debug = sorted(
                                [(int(getattr(c.link, 'link_id', -1)), c.distance) for c in candt],
                                key=lambda x: x[1],
                            )[:5]
                            print(f"[m4g-debug] first-point top candidates (link_id, dist): {top_debug}")
                        except Exception:
                            pass
                    states.append(candt)
                    dp.append(np.array([c.emission_logp for c in candt], dtype=float))
                    backptr.append({i: -1 for i in range(len(candt))})
                    kept_indices.append(t)
                    initialized = True
                    continue
                # t >= first valid step
                prev_states = states[-1]
                prev_dp = dp[-1]
                m, n = len(prev_states), len(candt)
                if m == 0 or n == 0:
                    continue
                try:
                    prev_orig_idx = kept_indices[-1]
                    p_prev = gps_xy_all[prev_orig_idx]
                    p_curr = gps_xy_all[t]
                    adj_dis = float(p_prev.distance(p_curr)) if (p_prev is not None and p_curr is not None) else prev_states[0].proj_point_xy.distance(candt[0].proj_point_xy)
                except Exception:
                    adj_dis = prev_states[0].proj_point_xy.distance(candt[0].proj_point_xy)

                best_scores, best_indices = self._compute_transition_scores(prev_states, candt, adj_dis, prev_dp)
                emission_arr = np.array([c.emission_logp for c in candt], dtype=float)
                cur_dp = best_scores + emission_arr
                cur_bp: Dict[int, int] = {j: (int(best_indices[j]) if best_indices[j] >= 0 else -1) for j in range(n)}
                
                # Debug: Track HMM computation for specific journey
                if self.debug and hasattr(self, '_current_agent') and self._current_agent == '2bd302da9400692a':
                    print(f"[HMM-debug] Step {t}: {m} prev states -> {n} curr states")
                    print(f"  Adj distance: {adj_dis:.2f}m")
                    print(f"  Best scores range: {np.min(best_scores):.2f} to {np.max(best_scores):.2f}")
                    print(f"  Emission range: {np.min(emission_arr):.2f} to {np.max(emission_arr):.2f}")
                    print(f"  Cur_dp range: {np.min(cur_dp):.2f} to {np.max(cur_dp):.2f}")
                    print(f"  Finite cur_dp: {np.sum(np.isfinite(cur_dp))}/{len(cur_dp)}")
                    if len(candt) <= 5:
                        for j, c in enumerate(candt):
                            print(f"    State {j}: link_id={getattr(c.link, 'link_id', -1)}, dist={c.distance:.2f}m, emission={c.emission_logp:.2f}")

                for j2 in range(n):
                    bi = cur_bp[j2]
                    if bi is not None and 0 <= bi < m:
                        prev_lk = prev_states[bi].link
                        cur_lk = candt[j2].link
                        u = int(prev_lk.to_node.node_id) if prev_lk.to_node is not None else None
                        v = int(cur_lk.from_node.node_id) if cur_lk.from_node is not None else None
                        if (u is not None) and (v is not None):
                            key = (int(prev_lk.link_id), int(cur_lk.link_id))
                            if key not in self._ft_node_path:
                                nodes = self._shortest_path_nodes(u, v)
                                if nodes:
                                    self._ft_node_path[key] = nodes

                # Numerical stability: normalize log probabilities (like gotrackit)
                finite_mask = np.isfinite(cur_dp)
                if np.any(finite_mask):
                    max_val = np.max(cur_dp[finite_mask])
                    cur_dp = cur_dp - max_val
                    # Debug: Track numerical stability
                    if self.debug and hasattr(self, '_current_agent') and self._current_agent == '2bd302da9400692a':
                        print(f"  Numerical stability: max_val={max_val:.2f}, finite={np.sum(finite_mask)}/{len(cur_dp)}")
                        print(f"  After normalization: range {np.min(cur_dp):.2f} to {np.max(cur_dp):.2f}")
                else:
                    # If all values are infinite, set to a very small log probability
                    # This prevents complete failure while maintaining numerical stability
                    cur_dp = np.full_like(cur_dp, -1e10, dtype=float)
                    # Debug: Track numerical stability
                    if self.debug and hasattr(self, '_current_agent') and self._current_agent == '2bd302da9400692a':
                        print("  WARNING: All cur_dp values are infinite! Setting to -1e10")

                states.append(candt)
                dp.append(cur_dp)
                backptr.append(cur_bp)
                kept_indices.append(t)

            if not states:
                return pd.DataFrame(columns=['seq', 'time', 'link_id', 'from_node_id', 'to_node_id', 'longitude', 'latitude', 'speed_mph', 'dis_to_next', 'match_heading', 'route_dis'])

            # backtrace - handle log probabilities properly (like gotrackit)
            final_dp = dp[-1]
            finite_mask = np.isfinite(final_dp)
            
            if np.any(finite_mask):
                # Find the state with maximum log probability among finite values
                finite_indices = np.where(finite_mask)[0]
                finite_values = final_dp[finite_mask]
                max_idx = finite_indices[np.argmax(finite_values)]
                seq_idx = int(max_idx)
            else:
                # If all values are infinite, use the first state
                seq_idx = 0
            
            seq = []
            
            # Debug: Track backtrace process
            if self.debug and hasattr(self, '_current_agent') and self._current_agent == '2bd302da9400692a':
                print(f"[HMM-debug] Backtrace: starting from state {seq_idx} with score {dp[-1][seq_idx]:.2f}")
                print(f"  Total states: {len(states)}")
                print(f"  Final dp range: {np.min(dp[-1]):.2f} to {np.max(dp[-1]):.2f}")
                print(f"  Final dp finite: {np.sum(np.isfinite(dp[-1]))}/{len(dp[-1])}")
            
            for step in reversed(range(len(states))):
                seq.append((step, states[step][seq_idx]))
                old_seq_idx = seq_idx
                seq_idx = backptr[step].get(seq_idx, -1)
                
                # Debug: Track backtrace steps
                if self.debug and hasattr(self, '_current_agent') and self._current_agent == '2bd302da9400692a':
                    print(f"  Step {step}: state {old_seq_idx} -> {seq_idx}")
                
                if seq_idx < 0 and step > 0:
                    if self.debug and hasattr(self, '_current_agent') and self._current_agent == '2bd302da9400692a':
                        print(f"  WARNING: Backtrace broken at step {step}")
                    break
            seq.reverse()
            
            # Debug: Track final sequence
            if self.debug and hasattr(self, '_current_agent') and self._current_agent == '2bd302da9400692a':
                print(f"[HMM-debug] Final sequence length: {len(seq)}")
                for i, (step, state) in enumerate(seq[:5]):
                    print(f"  {i}: step {step}, link_id={getattr(state.link, 'link_id', -1)}")
                if len(seq) > 5:
                    print(f"  ... and {len(seq) - 5} more")

            # build rich output rows
            rows = []
            # precompute gps xy list for all points
            gps_xy = []
            for i in range(len(sub)):
                x, y = self.net.GT.from_latlon(float(sub.loc[i, lng_col]), float(sub.loc[i, lat_col]))
                gps_xy.append(Point(x, y))

            cumulative_route = 0.0
            for idx in range(len(seq)):
                step_t, cand = seq[idx]
                link = cand.link
                orig_t = kept_indices[step_t]
                time_val = sub.loc[orig_t, time_col] if (time_col and time_col in sub.columns) else None
                # speed mph: strictly from original gps column if provided
                speed_mph = None
                if speed_col and speed_col in sub.columns:
                    val = sub.loc[orig_t, speed_col]
                    speed_mph = float(val) if pd.notna(val) else None

                # cumulative route distance from first matched step to current step
                if idx == 0:
                    route_dis = 0.0
                else:
                    _, cand_prev = seq[idx - 1]
                    if cand.link is cand_prev.link:
                        line = cand.link.geometry_xy
                        s1 = line.project(cand_prev.proj_point_xy)
                        s2 = line.project(cand.proj_point_xy)
                        inc = abs(s2 - s1)
                    else:
                        # add tail(prev) + shortest_path(prev.to_node -> curr.from_node) + head(curr)
                        try:
                            line_prev = cand_prev.link.geometry_xy
                            s_prev = line_prev.project(cand_prev.proj_point_xy)
                            L_prev = float(line_prev.length) if line_prev.length is not None else 0.0
                            tail = max(0.0, L_prev - s_prev)
                        except Exception:
                            tail = 0.0
                        try:
                            line_curr = cand.link.geometry_xy
                            s_curr = line_curr.project(cand.proj_point_xy)
                            head = max(0.0, s_curr)
                        except Exception:
                            head = 0.0
                        try:
                            u = cand_prev.link.to_node.node_id
                            v = cand.link.from_node.node_id
                            mid = self._shortest_path_length(u, v)
                        except Exception:
                            mid = float('inf')
                        if math.isinf(mid):
                            inc = cand_prev.proj_point_xy.distance(cand.proj_point_xy)
                        else:
                            inc = tail + mid + head
                    cumulative_route += inc
                    route_dis = cumulative_route

                row = {
                    'seq': int(idx),
                    'time': time_val if time_val is not None else None,
                    'link_id': int(link.link_id),
                    'from_node_id': int(link.from_node.node_id) if link.from_node is not None else None,
                    'to_node_id': int(link.to_node.node_id) if link.to_node is not None else None,
                    'longitude': float(sub.loc[orig_t, lng_col]),
                    'latitude': float(sub.loc[orig_t, lat_col]),
                    'speed_mph': speed_mph,
                    'match_heading': self._bearing_of_line(link.geometry_xy) if hasattr(link, 'geometry_xy') and link.geometry_xy is not None else None,
                    'route_dis': route_dis,
                }
                if keep_user_fields:
                    for uf in keep_user_fields:
                        try:
                            row[uf] = sub.loc[orig_t, uf]
                        except Exception:
                            row[uf] = None
                rows.append(row)

        df = pd.DataFrame(rows)
        # ensure column order
        cols = ['seq', 'time', 'link_id', 'from_node_id', 'to_node_id', 'longitude', 'latitude', 'speed_mph', 'match_heading', 'route_dis']
        # Append user fields in the specified order if any
        if keep_user_fields:
            for uf in keep_user_fields:
                if uf not in df.columns:
                    df[uf] = None
            cols = cols + [uf for uf in keep_user_fields if uf in df.columns]
        return df[cols]


# ----------------------------
# Multiprocessing helpers
# ----------------------------
def _split_groups(items: List, n: int) -> List[List]:
    if n <= 1 or len(items) <= 1:
        return [list(items)]
    n = max(1, int(n))
    size = max(1, (len(items) + n - 1) // n)
    groups: List[List] = []
    for i in range(0, len(items), size):
        groups.append(items[i:i+size])
    return groups


def _m4g_worker_match(args) -> Tuple[pd.DataFrame, Dict, List]:
    network, gps_chunk_df, init_kwargs = args
    # Ensure workers do not write files; the parent will export once
    init_kwargs = dict(init_kwargs)
    init_kwargs['export_csv'] = False
    init_kwargs['export_geo'] = False
    init_kwargs['export_route'] = False
    matcher = mapmatching(network=network, **init_kwargs)
    # Silence stdout/stderr inside worker to avoid interleaved logs
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        res_df, warn_info, err_agents = matcher.match(gps_chunk_df)
    return res_df, warn_info, err_agents


# Persistent worker matcher for per-agent streaming
_WK_MATCHER = None


def _m4g_worker_init(network: Network, init_kwargs: Dict):
    global _WK_MATCHER
    init_kwargs = dict(init_kwargs)
    init_kwargs['export_csv'] = False
    init_kwargs['export_geo'] = False
    init_kwargs['export_route'] = False
    # force single-core inside worker to avoid nested parallelism
    init_kwargs['core_num'] = 1
    # Silence construction-time prints for worker
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
        _WK_MATCHER = mapmatching(network=network, **init_kwargs)


def _m4g_worker_match_agent(args) -> Tuple[pd.DataFrame, Optional[str]]:
    sub_df, agent_field = args
    try:
        matcher = _WK_MATCHER
        if matcher is None:
            return pd.DataFrame(), 'worker not initialized'
        # ensure xy
        x_col, y_col = matcher._ensure_xy_columns(sub_df, matcher.lng_field, matcher.lat_field)
        # optional route band allowed indices
        allowed_idx: Optional[Set[int]] = None
        if matcher.route_gap and matcher.route_gap > 0:
            pts_xy: List[Point] = []
            for _, r in sub_df.iterrows():
                try:
                    x, y = float(r[x_col]), float(r[y_col])
                    pts_xy.append(Point(x, y))
                except Exception:
                    continue
            allowed_idx = matcher._prefilter_link_indices_by_route_band(pts_xy)
        base_cols = {'seq','time','link_id','from_node_id','to_node_id','longitude','latitude','speed_mph','dis_to_next','match_heading','route_dis', agent_field}
        keep_user_fields = [c for c in matcher.extra_fields if (c in sub_df.columns and c not in base_cols)]
        path_df = matcher._match_one_agent(sub_df.reset_index(drop=True), matcher.lng_field, matcher.lat_field, matcher.time_field, matcher.heading_field, matcher.speed_field, keep_user_fields, allowed_idx, x_col, y_col)
        if not path_df.empty:
            a = sub_df.iloc[0][agent_field]
            path_df[agent_field] = a
        return path_df, None
    except Exception as e:
        return pd.DataFrame(), repr(e)


def _m4g_worker_match_batch(chunk_df: pd.DataFrame) -> Tuple[pd.DataFrame, int, Dict, List]:
    try:
        matcher = _WK_MATCHER
        if matcher is None:
            return pd.DataFrame(), 0, {}, []
        # Run full match quietly inside worker on this chunk (multiple agents)
        import io as _io
        from contextlib import redirect_stdout as _rs, redirect_stderr as _re
        _buf = _io.StringIO()
        with _rs(_buf), _re(_buf):
            res_df, warn_info, err_agents = matcher.match(chunk_df)
        try:
            processed = int(chunk_df[matcher.agent_field].nunique())
        except Exception:
            processed = 0
        return res_df, processed, warn_info or {}, err_agents or []
    except Exception:
        return pd.DataFrame(), 0, {}, []


class mapmatching(mapmatching):
    def multi_core_match(self, gps_df: pd.DataFrame, core_num: Optional[int] = None, batch_size: Optional[int] = None) -> Tuple[pd.DataFrame, Dict, List]:
        # Validate agent field
        assert self.agent_field in gps_df.columns, f'gps data is missing {self.agent_field} field'

        # Parent-side: time parsing/sorting and gap filtering for consolidated logging
        if self.time_field and self.time_field in gps_df.columns:
            tmp_col = '__time_sort__'
            if self.time_format:
                try:
                    gps_df[tmp_col] = pd.to_datetime(gps_df[self.time_field], errors='coerce', format=self.time_format)
                    valid_time_count = gps_df[tmp_col].notna().sum()
                    if self.verbose:
                        print(f"Time parsing with specified format '{self.time_format}': {valid_time_count}/{len(gps_df)} rows have valid time")
                    if valid_time_count == 0:
                        if self.verbose:
                            print("Warning: No valid time data found with the specified format.")
                        gps_df = gps_df.sort_values(by=[self.agent_field], ascending=True, ignore_index=True)
                    else:
                        gps_df = gps_df.dropna(subset=[tmp_col])
                        if not gps_df.empty:
                            gps_df = gps_df.sort_values(by=[self.agent_field, tmp_col], ascending=[True, True], ignore_index=True)
                            if self.verbose:
                                print(f"GPS data sorted by {self.agent_field} and {self.time_field}")
                except Exception as e:
                    if self.verbose:
                        print(f"Error parsing time with specified format '{self.time_format}': {e}")
                    gps_df = gps_df.sort_values(by=[self.agent_field], ascending=True, ignore_index=True)
            else:
                try:
                    gps_df[tmp_col] = pd.to_datetime(gps_df[self.time_field], errors='coerce', infer_datetime_format=True)
                    valid_time_count = gps_df[tmp_col].notna().sum()
                    if self.verbose:
                        print(f"Time parsing with auto-detection: {valid_time_count}/{len(gps_df)} rows have valid time")
                    if valid_time_count == 0:
                        if self.verbose:
                            print("Warning: No valid time data found with auto-detection.")
                        gps_df = gps_df.sort_values(by=[self.agent_field], ascending=True, ignore_index=True)
                    else:
                        gps_df = gps_df.dropna(subset=[tmp_col])
                        if not gps_df.empty:
                            gps_df = gps_df.sort_values(by=[self.agent_field, tmp_col], ascending=[True, True], ignore_index=True)
                            if self.verbose:
                                print(f"GPS data sorted by {self.agent_field} and {self.time_field}")
                except Exception as e:
                    if self.verbose:
                        print(f"Auto-detection failed: {e}")
                    gps_df = gps_df.sort_values(by=[self.agent_field], ascending=True, ignore_index=True)
            del gps_df[tmp_col]
        else:
            gps_df = gps_df.sort_values(by=[self.agent_field], ascending=True, ignore_index=True)

        if self.time_field and self.time_field in gps_df.columns:
            gps_df = self._filter_journeys_with_large_time_gaps(gps_df, self.agent_field, self.time_field, self.max_gap_seconds)

        # Determine core number and list agents
        cpu_cnt = os.cpu_count() or 1
        desired_core = core_num if core_num is not None else self.default_core_num
        if desired_core is None:
            desired_core = max(1, cpu_cnt // 2)
        n_proc = cpu_cnt if desired_core > cpu_cnt else max(1, int(desired_core))
        agent_ids = list(gps_df[self.agent_field].unique())
        total_agents = len(agent_ids)
        print(f'using multiprocessing - {n_proc} cores')

        # Prepare init kwargs for worker reconstruction
        init_kwargs = {
            'agent_field': self.agent_field,
            'lng_field': self.lng_field,
            'lat_field': self.lat_field,
            'time_field': self.time_field,
            'speed_field': self.speed_field,
            'heading_field': self.heading_field,
            'max_gap_seconds': self.max_gap_seconds,
            'search_radius': self.search_radius,
            'noise_sigma': self.noise_sigma,
            'trans_weight': self.trans_weight,
            'dist_penalty': self.dist_penalty,
            'max_candidates': self.max_candidates,
            'use_heading': self.use_heading,
            'heading_sigma': self.heading_sigma,
            'time_format': self.time_format,
            'extra_fields': self.extra_fields,
            'turn_sigma': self.turn_sigma,
            'heading_len': self.heading_len,
            'route_gap': self.route_gap,
            'use_node_restrict': self.use_node_restrict,
            'filter_dwell': self.filter_dwell,
            'dwell_dist': self.dwell_dist,
            'dwell_count': self.dwell_count,
            'out_dir': self.out_dir,
            'min_link_len': self.min_link_len,
            'speed_limit': self.speed_limit,
            'heading_weights': self.heading_weights,
            'max_agents': None,
            'debug': False,
            'stop_event': None,
        }

        # Batch streaming (improves throughput): split agents into chunks and stream per-chunk
        res_parts: List[pd.DataFrame] = []
        warn_info_agg: Dict = {}
        err_agents_all: List = []
        # choose chunk size to balance IPC: default target ~100 agents/worker task; override by batch_size
        desired_batch = batch_size if batch_size is not None else self.default_batch_size
        if desired_batch is not None:
            try:
                chunk_size = max(1, int(desired_batch))
            except Exception:
                chunk_size = max(50, min(200, total_agents // max(1, n_proc)))
        else:
            chunk_size = max(50, min(200, total_agents // max(1, n_proc)))
        agent_chunks = _split_groups(agent_ids, max(1, (total_agents + chunk_size - 1) // chunk_size))

        with multiprocessing.Pool(processes=n_proc, initializer=_m4g_worker_init, initargs=(self.net, init_kwargs)) as pool:
            iterable_chunks = (gps_df[gps_df[self.agent_field].isin(chunk)].copy() for chunk in agent_chunks)
            pbar = tqdm(total=total_agents,
                        desc="Processing agents",
                        dynamic_ncols=True,
                        ascii=True,
                        bar_format="{desc}: {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]",
                        file=sys.stdout)
            try:
                for res_df, processed, warn_info, err_agents in pool.imap_unordered(_m4g_worker_match_batch, iterable_chunks, chunksize=1):
                    if isinstance(res_df, pd.DataFrame) and not res_df.empty:
                        res_parts.append(res_df)
                    if isinstance(warn_info, dict) and warn_info:
                        warn_info_agg.update(warn_info)
                    if isinstance(err_agents, list) and err_agents:
                        err_agents_all.extend(err_agents)
                    if pbar is not None:
                        pbar.update(processed if isinstance(processed, int) and processed > 0 else 0)
            finally:
                if pbar is not None:
                    pbar.close()

        # Aggregate done

        # Finalize results similar to single-core path
        def _finalize_results(current_results: List[pd.DataFrame]) -> pd.DataFrame:
            base_desired = [self.agent_field, 'seq', 'time', 'link_id', 'from_node_id', 'to_node_id', 'longitude', 'latitude', 'speed_mph', 'match_heading', 'route_dis']
            user_keep = [c for c in self.extra_fields if (c not in base_desired and c in gps_df.columns)]
            desired_cols = base_desired + user_keep
            if current_results:
                non_empty = [df for df in current_results if isinstance(df, pd.DataFrame) and not df.empty and df.columns.size > 0]
                if non_empty:
                    filtered_dfs = []
                    for df in non_empty:
                        if not df.empty:
                            df_clean = df.dropna(axis=1, how='all')
                            if not df_clean.empty:
                                filtered_dfs.append(df_clean)
                    if filtered_dfs:
                        res_local = pd.concat(filtered_dfs, ignore_index=True)
                    else:
                        res_local = pd.DataFrame(columns=desired_cols)
                else:
                    res_local = pd.DataFrame(columns=desired_cols)
            else:
                res_local = pd.DataFrame(columns=desired_cols)
            for c in desired_cols:
                if c not in res_local.columns:
                    res_local[c] = None
            res_local = res_local[desired_cols]
            try:
                if not res_local.empty and (self.agent_field in res_local.columns):
                    if 'time' in res_local.columns and res_local['time'].notna().any():
                        tmpc = '__sort_time__'
                        try:
                            if self.time_format:
                                res_local[tmpc] = pd.to_datetime(res_local['time'], errors='coerce', format=self.time_format)
                            else:
                                res_local[tmpc] = pd.to_datetime(res_local['time'], errors='coerce', infer_datetime_format=True)
                            res_local = res_local.sort_values(by=[self.agent_field, tmpc], ascending=[True, True], ignore_index=True)
                            del res_local[tmpc]
                        except Exception:
                            if 'seq' in res_local.columns:
                                res_local = res_local.sort_values(by=[self.agent_field, 'seq'], ascending=[True, True], ignore_index=True)
                    elif 'seq' in res_local.columns:
                        res_local = res_local.sort_values(by=[self.agent_field, 'seq'], ascending=[True, True], ignore_index=True)
            except Exception:
                pass
            try:
                if self.export_csv:
                    os.makedirs(self.out_dir, exist_ok=True)
                    res_local.to_csv(os.path.join(self.out_dir, self.result_file), index=False)
                    if self.export_route and not res_local.empty:
                        route_rows = []
                        for agent, df_g in res_local.groupby(self.agent_field):
                            df_g = df_g.sort_values(by=['seq' if 'seq' in df_g.columns else 'time'], ascending=True)
                            df_g = df_g.reset_index(drop=True)
                            expanded: List[int] = []
                            if len(df_g) == 0:
                                continue
                            def _append_link_id(lid: int):
                                if not expanded or expanded[-1] != int(lid):
                                    expanded.append(int(lid))
                            first_link = self.net.link_dict.get(int(df_g.at[0, 'link_id']))
                            if first_link is None:
                                continue
                            _append_link_id(int(first_link.link_id))
                            for i in range(len(df_g) - 1):
                                cur_lk = self.net.link_dict.get(int(df_g.at[i, 'link_id']))
                                nxt_lk = self.net.link_dict.get(int(df_g.at[i+1, 'link_id']))
                                if cur_lk is None or nxt_lk is None:
                                    continue
                                if (int(cur_lk.link_id) == int(nxt_lk.link_id)) or \
                                   (getattr(cur_lk, 'to_node', None) and getattr(nxt_lk, 'from_node', None) and \
                                    int(cur_lk.to_node.node_id) == int(nxt_lk.from_node.node_id)):
                                    _append_link_id(int(nxt_lk.link_id))
                                    continue
                                nodes = []
                                try:
                                    u = int(cur_lk.to_node.node_id)
                                    v = int(nxt_lk.from_node.node_id)
                                    nodes = self._shortest_path_nodes(u, v)
                                except Exception:
                                    nodes = []
                                if nodes:
                                    for j in range(len(nodes) - 1):
                                        data = self._edge_data(nodes[j], nodes[j+1])
                                        if not data:
                                            continue
                                        lk = data.get('link')
                                        if lk is None:
                                            continue
                                        _append_link_id(int(lk.link_id))
                                _append_link_id(int(nxt_lk.link_id))
                            for step_idx, lid in enumerate(expanded):
                                lk = self.net.link_dict.get(int(lid))
                                route_rows.append({
                                    self.agent_field: agent,
                                    'step': step_idx,
                                    'link_id': int(lid),
                                    'from_node_id': int(lk.from_node.node_id) if lk and lk.from_node else None,
                                    'to_node_id': int(lk.to_node.node_id) if lk and lk.to_node else None,
                                })
                        if route_rows:
                            route_df = pd.DataFrame(route_rows)
                            route_df = route_df.sort_values(by=[self.agent_field, 'step'], ascending=[True, True], ignore_index=True)
                            grouped_routes = []
                            for journey_id, group in route_df.groupby(self.agent_field):
                                link_ids = group['link_id'].astype(str).tolist()
                                grouped_routes.append({
                                    'journey_id': journey_id,
                                    'link_ids': ','.join(link_ids)
                                })
                            grouped_route_df = pd.DataFrame(grouped_routes)
                            grouped_route_df.to_csv(os.path.join(self.out_dir, self.route_file), index=False)
            except Exception:
                pass
            return res_local

        final_res = _finalize_results(res_parts)
        return final_res, warn_info_agg, err_agents_all
