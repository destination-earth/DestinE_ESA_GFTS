import earthkit.data
import xarray as xr

AOI = {
    "type": "Feature",
    "properties": {
        "name": "Download Area",
        "description": "Polygon area for climate forecast data download - North Atlantic region",
    },
    "geometry": {
        "type": "Polygon",
        "coordinates": [
            [
                [-14.65, 40.92],
                [9.40, 40.92],
                [9.40, 56.74],
                [-14.65, 56.74],
                [-14.65, 40.92],
            ]
        ],
    },
}

AOI_SMALL = {
    "type": "Feature",
    "properties": {
        "name": "Download Area",
        "description": "Polygon area for climate forecast data download - North Atlantic region",
    },
    "geometry": {
        "type": "Polygon",
        "coordinates": [
            [
                [-4.302114705361248, 47.84753399497097],
                [-4.302114705361248, 45.613524433333595],
                [-1.9232431194369894, 45.613524433333595],
                [-1.9232431194369894, 47.84753399497097],
                [-4.302114705361248, 47.84753399497097],
            ]
        ],
    },
}


def get_month_dates(year, month):
    """Generate a string of dates for a given year and month in format YYYYMMDD.
    Returns dates separated by '/' for all days in the month."""
    import calendar

    # Get number of days in the month
    _, num_days = calendar.monthrange(year, month)

    # Generate list of date strings
    dates = []
    for day in range(1, num_days + 1):
        date_str = f"{year}{month:02d}{day:02d}"
        dates.append(date_str)

    return "/".join(dates)


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


def get_data(model, param, date):
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
        "date": date,
        "type": "fc",
        "levtype": "o2d",
        # "levelist": "1/2/3/4/5/6/7/8/9/10",
        "param": param,
        "feature": {
            "type": "polygon",
            "shape": AOI["geometry"]["coordinates"],
        },
    }

    return earthkit.data.from_source(
        "polytope",
        "destination-earth",
        request,
        stream=False,
        address="polytope.lumi.apps.dte.destination-earth.eu",
    )


model = "IFS-NEMO"

year = 2026
month = 6
dates = get_month_dates(year, month)

param = "263101"
data = get_data(model, param, dates)


data = data.to_xarray()
data.to_netcdf(f"data/{model}-{param}-{year}-{month}.nc")

param = "263100"
data = get_data(model, param, dates)
data = data.to_xarray()
data.to_netcdf(f"data/{model}-{param}-{year}-{month}.nc")


ds = xr.open_mfdataset("data/IFS-NEMO-263100-june.nc")

print(ds)
