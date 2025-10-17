# -- coding: utf-8 --
"""
MapMatcher4GMNS - A high-performance map matching tool for GMNS networks

This package provides map matching functionality for GPS trajectories on
GMNS (General Modeling Network Specification) formatted networks.
"""

__version__ = "0.1.1"
__author__ = "MapMatcher4GMNS Contributors"
__license__ = "MIT"

from .io.load_from_csv import loadNetFromCSV
from .matcher.mapmatch import mapmatching

# Export main classes for convenience
from .networkclass.macronet import Network, Node, Link

__all__ = [
    'loadNetFromCSV',
    'mapmatching',
    'Network',
    'Node',
    'Link',
    '__version__',
]


def _network_to_gdfs(network):
	"""Convert mrnet Network to link_gdf/node_gdf (GeoDataFrame)."""
	import pandas as pd
	import geopandas as gpd
	from shapely.geometry import Point, LineString

	# nodes
	n_rows = []
	for node_id, node in network.node_dict.items():
		# network.geometry is lon/lat; skip if missing
		if node.geometry is None:
			continue
		n_rows.append({
			'node_id': node_id,
			'x_coord': float(node.geometry.x),
			'y_coord': float(node.geometry.y),
			'geometry': Point(node.geometry.x, node.geometry.y)
		})
	node_df = pd.DataFrame(n_rows)
	node_gdf = gpd.GeoDataFrame(node_df[['node_id', 'geometry']], geometry='geometry', crs='EPSG:4326')

	# links
	l_rows = []
	for link_id, link in network.link_dict.items():
		if link.geometry is None:
			continue
		l_rows.append({
			'link_id': link_id,
			'from_node': link.from_node.node_id,
			'to_node': link.to_node.node_id,
			'dir': int(getattr(link, 'dir_flag', 1) or 1),
			'length': getattr(link, 'length', None),
			'geometry': LineString(link.geometry.coords)
		})
	link_df = pd.DataFrame(l_rows)
	link_gdf = gpd.GeoDataFrame(link_df[['link_id','from_node','to_node','dir','geometry']], geometry='geometry', crs='EPSG:4326')
	if 'length' in link_df.columns and link_df['length'].notna().any():
		link_gdf['length'] = link_df['length']
	else:
		link_gdf_3857 = link_gdf.to_crs('EPSG:3857')
		link_gdf['length'] = link_gdf_3857.geometry.length

	return link_gdf, node_gdf


