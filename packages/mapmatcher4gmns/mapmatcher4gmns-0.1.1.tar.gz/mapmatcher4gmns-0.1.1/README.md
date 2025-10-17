# MapMatcher4GMNS

A high-performance map matching tool for GPS trajectories on GMNS (General Modeling Network Specification) networks.

## Features

- **High-Performance Map Matching**: Efficient Hidden Markov Model (HMM) based map matching algorithm
- **GMNS Network Support**: Native support for GMNS network format (node.csv, link.csv)
- **Multi-Core Processing**: Built-in parallel processing support for large-scale GPS data
- **Flexible Configuration**: Comprehensive parameters for fine-tuning matching quality
- **Route Generation**: Automatic generation of complete routes between matched points

## Installation

### From PyPI (when published)

```bash
pip install mapmatcher4gmns
```

## Quick Start

```python
import mapmatcher4gmns as m4g
import pandas as pd

def main():
    # Load network from GMNS format
    net = m4g.loadNetFromCSV(
        folder='path/to/network',
        node_file='node.csv',
        link_file='link.csv'
    )

    # Load GPS data
    gps_df = pd.read_csv('gps_data.csv')

    # Create matcher
    matcher = m4g.mapmatching(
        network=net,
        time_field='timestamp',
        time_format='%Y-%m-%dT%H:%M:%S.%fZ',
        out_dir='output',
        result_file='matched_result.csv',
        route_file='matched_route.csv',
    )

    # Perform map matching
    matcher.match(gps_df)

if __name__ == '__main__':
    main()
```


## Input Data Requirements

### Network Files (GMNS Format)

**node.csv** (required fields):
- `node_id`: Unique node identifier
- `x_coord`: Longitude (if coordinate_type='lonlat') or X coordinate
- `y_coord`: Latitude (if coordinate_type='lonlat') or Y coordinate

**link.csv** (required fields):
- `link_id`: Unique link identifier
- `from_node_id`: Starting node ID
- `to_node_id`: Ending node ID
- `lanes`: Number of lanes
- `geometry`: LineString geometry in WKT format

### GPS Data

**Required fields**:
- `journey_id` (or custom agent_field): Unique identifier for each GPS trajectory
- `longitude`: GPS longitude
- `latitude`: GPS latitude

**Optional but recommended**:
- `time` (or custom time_field): Timestamp for temporal ordering
- `speed`: Speed
- `heading`: Heading direction in degrees

## Configuration Parameters

### Core Matching Parameters

- `search_radius` (default: 12.0): Search radius in meters for candidate links
- `noise_sigma` (default: 30.0): GPS noise standard deviation in meters
- `trans_weight` (default: 6.0): Weight for transition probability
- `max_candidates` (default: 10): Maximum number of candidate links per GPS point

### Movement Consistency

- `turn_sigma` (default: 45.0): Turn angle standard deviation in degrees
- `heading_sigma` (default: 30.0): Heading difference standard deviation
- `use_heading` (default: True): Whether to use heading information

### Filtering

- `filter_dwell` (default: True): Filter out stationary points
- `dwell_dist` (default: 5.0): Distance threshold for dwell detection in meters
- `dwell_count` (default: 2): Minimum consecutive points to be considered dwelling
- `max_gap_seconds` (default: 60.0): Maximum time gap allowed between consecutive points

### Performance

- `core_num`: Number of CPU cores to use (default: auto-detect)
- `batch_size`: Batch size for parallel processing (default: 1)

## Output

The tool generates two main output files:

### 1. Matched Results (`matched_result.csv`)

Contains the matched GPS points with:
- `journey_id`: Trajectory identifier
- `seq`: Sequence number
- `time`: Timestamp
- `link_id`: Matched link ID
- `from_node_id`, `to_node_id`: Link endpoints
- `longitude`, `latitude`: Original GPS coordinates
- `speed_mph`: Speed (if provided)
- `dis_to_next`: Distance to next point
- `match_heading`: Heading of matched link
- `route_dis`: Route distance to next point

### 2. Route File (`matched_route.csv`)

Contains the complete route for each journey:
- `journey_id`: Trajectory identifier
- `link_ids`: Comma-separated list of link IDs forming the complete route

## Advanced Usage

**Note:** When using multiprocessing features, wrap your code in `if __name__ == '__main__':` to avoid issues, especially on Windows.

### Multi-Core Processing

```python
matcher = m4g.mapmatching(
    network=net,
    core_num=4,  # Use 4 CPU cores
    batch_size=10,  # Process 10 journeys per batch
    # ... other parameters
)
```

### Custom Field Names

```python
matcher = m4g.mapmatching(
    network=net,
    agent_field='vehicle_id',  # Custom trajectory ID field
    lng_field='lon',           # Custom longitude field
    lat_field='lat',            # Custom latitude field
    time_field='timestamp',     # Custom time field
    # ... other parameters
)
```

### Extra Fields

Keep additional fields from input GPS data in the output:

```python
matcher = m4g.mapmatching(
    network=net,
    extra_fields=['vehicle_type', 'driver_id', 'trip_purpose'],
    # ... other parameters
)
```

## Requirements

- Python >= 3.8
- numpy >= 1.20.0
- pandas >= 1.3.0
- shapely >= 2.0.0
- geopandas >= 0.10.0
- networkx >= 2.6.0
- tqdm >= 4.60.0

## Citation

If you use this tool in your research, please cite:

```
[Add your citation here]
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Acknowledgments

This package was inspired by and references the excellent work of the [TrackIt (GoTrackIt)](https://github.com/zdsjjtTLG/TrackIt) project. We are grateful for their contributions to the open-source map matching community and their innovative approach to HMM-based map matching algorithms.

### References

- **TrackIt/GoTrackIt**: A comprehensive map matching Python package based on Hidden Markov Model (HMM)
  - GitHub: https://github.com/zdsjjtTLG/TrackIt
  - Documentation: https://gotrackit.readthedocs.io/
  - Developed by: TangKai and contributors at Hangzhou Zecheng Data Technology Co., Ltd.

This tool is designed to work with the General Modeling Network Specification (GMNS) format, supporting transportation network analysis and GPS trajectory processing.

## Support

For questions, issues, or feature requests, please contact us.

