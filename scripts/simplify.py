import io
import logging

import boto3
import geopandas as gpd
import numpy as np
import pandas as pd
import s3fs
import xarray as xr

logging.basicConfig()

logger = logging.getLogger("gfts")
logger.setLevel(logging.DEBUG)
ENDPOINT = "https://s3.gra.perf.cloud.ovh.net/"
SOURCE_BUCKET = "gfts-ifremer"
TARGET_BUCKET = "destine-gfts-visualisation-data"
PREFIX = "tags/bargip/tracks_4/"
PROFILE = "ovh_gfts"
REGION = "gra"
NR_OF_CELLS_PER_TIMESLICE = 200
POOL = 1


boto3.setup_default_session(profile_name=PROFILE)


def get_top_values(time_slice):
    time_slice = time_slice.squeeze()
    time_slice = time_slice.sortby("states", ascending=False)
    size = time_slice.sizes["c"]
    nodata_count = int(time_slice.states.isnull().sum().values)
    # Ensure we always slice 200 cells, even if less than 100 have data in them.
    if nodata_count + NR_OF_CELLS_PER_TIMESLICE > size:
        target_slice = slice(size - NR_OF_CELLS_PER_TIMESLICE, size)
    else:
        target_slice = slice(nodata_count, nodata_count + NR_OF_CELLS_PER_TIMESLICE)
    time_slice = time_slice.isel(c=target_slice)
    time_slice = time_slice.reset_coords(["latitude", "longitude"])
    time_slice = time_slice.expand_dims("time", axis=0)
    return time_slice


def get_filesystem():
    return s3fs.S3FileSystem(
        anon=False,
        profile=PROFILE,
        client_kwargs={
            "endpoint_url": ENDPOINT,
            "region_name": REGION,
        },
    )


def get_template(data):
    array = np.zeros((data.sizes["time"], NR_OF_CELLS_PER_TIMESLICE))
    template = xr.Dataset(
        data_vars=dict(
            states=(["time", "c"], array),
            latitude=(["time", "c"], array),
            longitude=(["time", "c"], array),
        ),
        coords={"time": data.time},
    )
    return template.chunk({"time": 1, "c": -1})


def prepare_data(data):
    vars_to_keep = ["states", "latitude", "longitude", "time"]
    vars_to_drop = [var for var in data.variables if var not in vars_to_keep]
    data = data.drop_vars(vars_to_drop)
    data = data.stack(c=("x", "y"))
    data = data.reset_index("c")
    data = data.drop_vars(["x", "y"])
    data = data.chunk({"time": 1, "c": -1})
    return data


def open_dataset(tag):
    logger.debug(f"Opening tag {tag}")

    store = s3fs.S3Map(
        root=f"s3://{SOURCE_BUCKET}/{PREFIX}{tag}/states.zarr",
        s3=get_filesystem(),
        check=False,
    )
    fs = get_filesystem()
    fs.open(f"s3://{SOURCE_BUCKET}/{PREFIX}{tag}/states.zarr")
    return xr.open_zarr(store)


def simplify(tag):
    data = open_dataset(tag)
    data = prepare_data(data)
    template = get_template(data)

    top_values = data.map_blocks(get_top_values, template=template)

    return top_values.to_dataframe().dropna().reset_index()


def get_tag_timeseries(track, tag):
    path = f"s3://gfts-ifremer/bargip/tag/formatted/{tag}/dst.csv"
    fs = get_filesystem()

    if not fs.exists(path):
        raise ValueError(f"Track data for {tag} does not exist")

    with fs.open(path) as fl:
        ts = pd.read_csv(fl)
    ts.time = pd.to_datetime(ts.time).dt.tz_localize(None)

    # Compute time interval in most probable track
    deltas = [
        track.time.iloc[i + 1] - track.time.iloc[i] for i in range(len(track) - 1)
    ]
    if len(set(deltas)) > 1:
        raise ValueError(f"Found more than 1 time interval in dataset {set(deltas)}")
    delta = deltas[0]

    # Average sensor measurements to the time step of the track
    temperatures = []
    pressures = []
    temperatures_std = []
    pressures_std = []
    for time in track.time.values:
        filtered = ts[(ts.time > time) & (ts.time < (time + delta))]
        temperatures.append(filtered.temperature.mean())
        pressures.append(filtered.pressure.mean())
        temperatures_std.append(filtered.temperature.std())
        pressures_std.append(filtered.pressure.std())

    track["temperature"] = temperatures
    track["pressure"] = pressures
    track["temperature_std"] = temperatures_std
    track["pressure_std"] = pressures_std

    return track


def to_geojson(df, tag):
    logger.debug(f"Writing geojson file for {tag}")

    track = df.sort_values("states", ascending=False).drop_duplicates("time")
    track = track.sort_values("time")

    geom = gpd.points_from_xy(track.longitude, track.latitude)
    track = gpd.GeoDataFrame(
        track[["time"]],
        geometry=geom,
        crs="EPSG:4326",
    )

    track = get_tag_timeseries(track, tag)

    with io.BytesIO() as buf:
        track.to_file(
            buf, driver="GeoJSON", SIGNIFICANT_FIGURES=5, COORDINATE_PRECISION=7
        )
        buf.seek(0)
        with get_filesystem().open(
            f"s3://destine-gfts-visualisation-data/{PREFIX}{tag}/{tag}.geojson", "wb"
        ) as fl:
            fl.write(buf.read())


def to_parquet(df, tag):
    logger.debug(f"Writing parquet file for {tag}")

    # Convert variables to integer for better compression
    df["longitude"] = (df["longitude"] * 1e6).astype("int32")
    df["latitude"] = (df["latitude"] * 1e6).astype("int32")
    max_value = df["states"].max()
    df["states"] = (df["states"] / max_value * 65535).astype("uint16")

    df = df.set_index(["time", "longitude", "latitude"])
    with get_filesystem().open(
        f"s3://destine-gfts-visualisation-data/{PREFIX}{tag}/{tag}.parquet", "wb"
    ) as fl:
        df.to_parquet(fl)


def list_tags():
    s3 = boto3.resource(service_name="s3", endpoint_url=ENDPOINT)

    folders = s3.meta.client.list_objects(
        Bucket=SOURCE_BUCKET, Prefix=PREFIX, Delimiter="/"
    )
    tags = [dat["Prefix"].split("/")[-2] for dat in folders["CommonPrefixes"]]
    return tags


def process_tag(tag):
    df = simplify(tag=tag)
    to_geojson(df=df, tag=tag)
    to_parquet(df=df, tag=tag)


def already_processed(tag):
    return get_filesystem().exists(
        f"s3://destine-gfts-visualisation-data/{PREFIX}{tag}/{tag}.geojson"
    )


def has_states(tag):
    return get_filesystem().exists(f"s3://{SOURCE_BUCKET}/{PREFIX}{tag}/states.zarr")


def main():
    logger.debug("Listing tags")
    tags = list_tags()
    for tag in tags:
        if already_processed(tag):
            continue
        if not has_states(tag):
            logger.debug(f"No states.zarr file found for {tag}")
            continue
        process_tag(tag)


if __name__ == "__main__":
    main()
