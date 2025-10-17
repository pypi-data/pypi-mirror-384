
# pandasgeo

[English](README.md) | [简体中文](README.zh-CN.md)

`pandasgeo` is a Python package for geospatial data processing and analysis. Built on top of `geopandas` and `pandas`, it provides a series of utility functions that simplify common GIS operations.

## Features

*   **Distance Calculation**: Efficiently compute the nearest distance between point pairs.
*   **Spatial Analysis**: Create buffers, Voronoi polygons, Delaunay triangulations, and more.
*   **Format Conversion**: Conveniently convert between `GeoDataFrame` and formats like `Shapefile`, `KML`, etc.
*   **Coordinate Aggregation**: Tools for aggregating coordinate points to grids.
*   **Geometric Operations**: Including polygon merging, centroid calculation, sector addition, and more.

## Installation

You can install `pandasgeo` from PyPI via pip (once released):

```bash
pip install pandasgeo
```
Alternatively, install the latest version directly from the GitHub repository:
```bash
pip install git+https://github.com/yourusername/pandasgeo.git
```
Quick Start
Here's a simple example of how to use pandasgeo to calculate the nearest distance between two point sets:

```bash
import pandas as pd
import pandasgeo as pdg

# Create two sample DataFrames
data1 = {'id': ['A', 'B'], 'lon1': [114.0, 114.1], 'lat1': [30.0, 30.1]}
df1 = pd.DataFrame(data1)

data2 = {'id': ['p1', 'p2', 'p3'], 'lon2': [114.01, 114.05, 114.12], 'lat2': [30.01, 30.05, 30.12]}
df2 = pd.DataFrame(data2)

# Calculate the nearest point in df2 for each point in df1
result = pdg.min_distance_twotable(df1, df2, n=1)

print(result)
```

## Contributing
Contributions of all kinds are welcome, including feature requests, bug reports, and code contributions.

## License
This project is licensed under the MIT License.