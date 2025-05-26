"""
Download ocean forecast data by geometry

This script downloads ocean forecast data from DestinE poytope
for a specified area of interest (AOI) defined by coordinates.

# Data catalogue:

# 3D ocean variables
# https://confluence.ecmwf.int/display/DDCZ/Climate+DT+Phase+1+data+catalogue#ClimateDTPhase1datacatalogue-Ocean(levtypeo3d)
# Time resolution: 1 x daily (date=YYYYMMDD,time=0000)
# NEMO: 75 model levels: (1, ..., 75)
# FESOM: 72 model levels: (1, ..., 72)
# param id, name, short name, units, model
# 263500, Time-mean sea water practical salinity, avg_so, g kg**-1, ICON/IFS-NEMO/IFS-FESOM
# 263501, Time-mean sea water potential temperature, avg_thetao, K, ICON/IFS-NEMO/IFS-FESOM

# 2D ocean variables
# https://confluence.ecmwf.int/display/DDCZ/Climate+DT+Phase+1+data+catalogue#ClimateDTPhase1datacatalogue-Ocean(levtypeo2d)
# Time resolution: Daily mean (date=YYYYMMDD,time=0000)
# param id, name, short name, units, model
# 263100, Time-mean sea surface practical salinity, avg_sos, g kg**-1, ICON/IFS-NEMO/IFS-FESOM
# 263101, Time-mean sea surface potential temperature, avg_tos, K, ICON/IFS-NEMO/IFS-FESOM

# Time range
https://destine.ecmwf.int/climate-change-adaptation-digital-twin-climate-dt/#1737392094446-739c56b7-c2b2

Future projection
	ICON 	5km across Earth system components 	2020-2039
    IFS-NEMO 	4.4 km atmosphere, 1/12 ocean/sea-ice 	2020-2039
"""
import calendar
from concurrent.futures import ThreadPoolExecutor

import earthkit.data


def get_month_dates(year, month):
    """Generate a string of dates for a given year and month in format YYYYMMDD.
    Returns dates separated by '/' for all days in the month."""

    _, num_days = calendar.monthrange(year, month)

    dates = []
    for day in range(1, num_days + 1):
        date_str = f"{year}{month:02d}{day:02d}"
        dates.append(date_str)

    return "/".join(dates)


def get_data(model, param, dates, shape):
    print(
        f"Downloading data for model {model}, param {param}, dates {dates[:8]} {dates[-8:]}"
    )

    request = {
        "class": "d1",
        "dataset": "climate-dt",
        "activity": "ScenarioMIP",
        "experiment": "SSP3-7.0",
        "model": model,
        "generation": "1",
        "realization": "1",
        "resolution": "high",
        "expver": "0001",
        "stream": "clte",
        "time": "0000",
        "date": dates,
        "type": "fc",
        "levtype": "o2d",
        "param": param,
        "feature": {
            "type": "polygon",
            "shape": shape,
        },
    }

    data = earthkit.data.from_source(
        "polytope",
        "destination-earth",
        request,
        stream=False,
        address="polytope.lumi.apps.dte.destination-earth.eu",
    )

    data = data.to_xarray()

    data.to_zarr(f"data/{model}-{param}-{dates[:4]}-{dates[4:6]}.zarr")
    data


aoi = [[40.92, -14.65], [40.92, 9.40], [56.74, 9.40], [56.74, -14.65], [40.92, -14.65]]

combos = [
    ("ICON", "263100", year, month, aoi)
    for year in range(2025, 2040)
    for month in range(1, 13)
]

combo = combos[0]
data = get_data(combo[0], combo[1], get_month_dates(combo[2], combo[3]), combo[4])

with ThreadPoolExecutor() as pool:
    pool.map(
        lambda combo: get_data(
            combo[0],  # model
            combo[1],  # param
            get_month_dates(combo[2], combo[3]),  # dates string for year/month
            combo[4],  # aoi shape
        ),
        combos,
    )
