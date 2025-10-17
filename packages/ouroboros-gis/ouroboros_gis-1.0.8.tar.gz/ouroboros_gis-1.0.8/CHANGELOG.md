# Changelog

## v1.1.0 (planned)

- First stable release

## v1.0.8 (latest)

- Add export methods back to `FeatureClass`
- Add CONTRIBUTING.md
- Bump for Python 3.14 and prerelese testing for 3.15
- Overhaul GitHub actions
- Refactor dev environment to use Pixi and Ruff
- Refactor some class getter methods into properties
- Docs and example notebooks updates

## v1.0.7

- sanitize_gdf_geometry() enforces compatibility with feature class geometries
- FeatureClass.show() displays a simple plot of the geometry
- get_info() uses xmltodict rather than GDAL
- Fixed notebook tables in docs, added ArcPy comparison notebook
- Test with Python 3.14.0-rc2

## v1.0.6

- Bumped test docker to Python 3.14.0-rc2
- Added ouroboros.__version__
- Added getter methods for FeatureClass and FeatureDataset
- Docs updates

## v1.0.5

- Dockerfile and GitHub action to test source with Python 3.14.0-rc1
- Removed FeatureClass.to_arrow() to avoid dependency on Pyarrow
- Removed function delete_fc() to avoid dependency on Fiona
- Simplified FeatureClass.calculate()
- Added checks to validate inputs
- Restructured API documentation

## v1.0.4

- Tested with Python 3.14.0-rc1
- GitHub Action to test source against Python prerelease
- Removed FeatureClass.to_arrow() to avoid dependency on Pyarrow

## v1.0.3

- Check existence of input files
- Documentation improvements
- Miscellaneous bugfixes and tweaks

## v1.0.2

- Fixed installation instructions and other docs tweaks

## v1.0.1

- FeatureClass.calculate()
- Instantiating a FeatureClass from an existing DataFrame uses a deep copy
- Updated README.md and docs

## v1.0.0 🎉

- Released on conda-forge
- GDAL raster support by default in conda, optional in pip install
- Removed Rasterio dependency, instead using GDAL directly
- Added data manipulation methods FeatureClass to help with processing
- Pass FeatureClass and FeatureDataset sequences on instantiation
- Getter methods return dicts instead of tuples
- Provided more details with get_info()
- Dev environment setup/test/build batch scripts
- Added TODO.md list for long-term goals

## 1.0.0-beta7

- Pass kwargs to the GeoTIFF write operation
- Added get_info() and list_rasters() utility functions
- Docs additions and updates
- CI cross-platform testing fixes

## 1.0.0-beta6

- Added a utility function for exporting raster datasets to GeoTIFF
- Docs updates

## 1.0.0-beta5

- Switched sphinx theme to PyData for dark mode
- Added more example usage notebooks

## 1.0.0-beta4

- Major refactor:
  - Dropped arcpy as a dependency
  - Rereleased as ouroboros-gis on PyPI to reflect dropping arcpy, and archived ouroboros-arcpy
  - Added GeoDatabase and FeatureDataset classes for OOP flexibility
  - Using GeoPandas under the hood
  - Added FeatureClass export methods to various formats (shp, geojson, arrow, etc.)
  - Removed extraneous requirements files
  - Reverse engineered feature datasets for `ouroboros.list_datasets` function
- README and documentation updates
- Added GitHub actions for cross-platform testing, black, pylint, and coverage
- Skipping v1.0.0b3 to re-upload to PyPI

## 1.0.0-beta2

- Bump requests from 2.32.3 to 2.32.4 in /docs

## 1.0.0-beta1

- Initial release as ouroboros-arcpy in PyPI
- Proof of concept class `ouroboros.core.FeatureClass`
- Test suite (pytest) 
- Sample data geodatabase
- Jupyter notebook with basic examples 
- Documentation
