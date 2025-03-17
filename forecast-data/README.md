# Destination Earth Data Download and Processing

This repository contains scripts for downloading and processing data from the Destination Earth (DestinE) Digital Twin of the Ocean through the Polytope API.

## Project Structure

- `download-data.py`: Script for downloading ocean data using the Polytope API
- `read_grib.py`: Utilities for reading and processing GRIB files using xarray
- `desp-authentication.py`: Authentication setup for the DESP platform

## Prerequisites

### System Requirements
- Python 3.x
- ECMWF ecCodes library (for GRIB file processing)

### Python Dependencies
```bash
pip install polytope-client xarray cfgrib
```

## Authentication Setup

1. You need to have a valid ECMWF API key or DESP key
2. Configure your credentials using one of these methods:
   - Create a `~/.polytopeapirc` file (JSON format)
   - Set environment variables (`POLYTOPE_USER_EMAIL` and `POLYTOPE_USER_KEY`)
   - Pass credentials directly to the `setup_client` function (not recommended)

## Usage

### Downloading Data

The script downloads two types of ocean temperature data for a specific region:

1. Sea Water Potential Temperature (thetao)
   - 3D ocean temperature data
   - Parameter ID: 263501
   - Level type: o3d

2. Sea Surface Temperature (tos)
   - 2D surface temperature data
   - Parameter ID: 263101
   - Level type: o2d

#### Region of Interest
The data is downloaded for the North Atlantic region defined by the following bounding box:
- Longitude: -14.65°E to 9.40°E
- Latitude: 40.92°N to 56.74°N

```bash
python download-data.py
```

This will:
1. Set up the Polytope client
2. Revoke any previous requests
3. Download both thetao and tos data files in GRIB format for the specified region
4. Display a summary of downloaded files

### Processing Data

```bash
python read_grib.py
```

This script provides utilities to:
- Read GRIB files into xarray Datasets
- Display dataset information and structure
- Show first and last observations with their locations
- Display temperature values in both Kelvin and Celsius
- Optionally convert to NetCDF format

## Data Processing Functions

The `read_grib.py` script provides these main functions:

- `read_grib_file(filepath)`: Read a GRIB file into an xarray Dataset
- `print_dataset_info(ds)`: Display information about the dataset structure
- `print_temperature_dates(ds)`: Show first and last observations with locations and values
- `save_as_netcdf(ds, output_path)`: Convert and save as NetCDF

## Example Usage

```python
from read_grib import read_grib_file, print_dataset_info, print_temperature_dates

# Read a GRIB file
ds = read_grib_file('path_to_your_grib_file')

# Display dataset information
print_dataset_info(ds)

# Show first and last observations
print_temperature_dates(ds)
```

## Data Details

### Download Parameters
- Dataset: climate-dt
- Activity: ScenarioMIP
- Experiment: SSP3-7.0
- Model: IFS-NEMO
- Resolution: high
- Time: 0000
- Region: North Atlantic (40.92°N-56.74°N, -14.65°E-9.40°E)

### Data Format
- Input: GRIB format
- Grid: HEALPix
- Coordinates: latitude/longitude
- Units: Kelvin (K)

## Notes

- The downloaded files are in GRIB format
- Data is from the DestinE Digital Twin Climate
- Requests use the SSP3-7.0 scenario
- Default resolution is set to "high"
- Time is set to "0000" by default
- Temperature values are in Kelvin (K)
- Data is limited to the North Atlantic region
