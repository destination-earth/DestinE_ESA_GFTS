# Destination Earth Data Download and Processing

This repository contains scripts for downloading and processing
data from the Destination Earth (DestinE) Digital Twin of the
Ocean through the Polytope API.

## Project Structure

- `desp-authentication.py`: Authentication setup for the DESP platform
- `download-data-by-geom.py`: Script for downloading ocean data for a specific polygon
  geometry using the Polytope API. Downloads sea surface temperature and salinity data
  for a defined area in the North Atlantic between 2025-2040.
- `average-dt-data.py`: Script for processing and analyzing the downloaded data:
  - Creates seasonal summaries (mean and standard deviation) of temperature and salinity
  - Resamples data between different HEALPix grid resolutions (4096 to 1024)
  - Computes weighted seasonal averages using sea bass distribution data
  - Exports processed data to zarr and CSV formats

## Prerequisites

### System Requirements

- Python 3.x

### Python Dependencies

```bash
pip install polytope-client xarray cfgrib conflator lxml earthkit-data earthkit-plots earthkit-regrid covjsonkit
```

## Authentication Setup

You need to have a valid ECMWF API key or DESP key

To create credentials based on your email and password run

```bash
python desp-authentication.py
```

This will write auth keys into a config file at `~/.polytopeapirc` in JSON format.

## Usage

### Data Variables

We download and process [2D ocean data for the IFS-NEMO model](<https://confluence.ecmwf.int/display/DDCZ/Climate+DT+Phase+1+data+catalogue#ClimateDTPhase1datacatalogue-Ocean(levtypeo2d)>)
of the DestinE Climate Adaptation Digital Twin.

We process two variables

1. Time-mean sea surface practical salinity

   - Short name `avg_sos`
   - Parameter ID: 263100
   - [Link to parameter docs](https://codes.ecmwf.int/grib/param-db/?id=263100)

2. Time-mean sea surface temperature
   - Short name `avg_tos`
   - Parameter ID: 263101
   - [Link to parameter docs](https://codes.ecmwf.int/grib/param-db/?id=263101)

#### Download data

The data is downloaded for the North Atlantic region defined by the following bounding box:

- Longitude: -14.65°E to 9.40°E
- Latitude: 40.92°N to 56.74°N

To download the ocean data (sea surface temperature and salinity) for this region, run:

```bash
python download-data-by-geom.py
```

### Processing Data

To process the downloaded data and generate seasonal summaries,
resample to different HEALPix resolutions, and compute weighted
averages using sea bass distribution data, run:

```bash
python average-dt-data.py
```
