import logging

import fsspec

import boto3
import click
import healpy as hp
import numpy as np
import pandas as pd
import s3fs
import xarray as xr
import xdggs
import os
import json

logging.basicConfig()

logger = logging.getLogger("gfts")
logger.setLevel(logging.DEBUG)

NR_OF_CELLS_PER_TIMESLICE = 800
NSIDE = 4096
NEST = True
UINT16_MAX = 65535

# remote access
ENDPOINT = "https://s3.gra.perf.cloud.ovh.net/"
PROFILE = "ovh_gfts"
REGION = "gra"

# I/O variables
# .zarr files are expected to be {SOURCE_BUCKET}/{SOURCE_PREFIX}{tag}/{SOURCE_SUFFIX}states.zarr
# .parquet files are stored to {TARGET_BUCKET}/{TARGET_PREFIX}{tag}/{tag}_healpix.parquet

SOURCE_BUCKET = os.environ.get("SOURCE_BUCKET", "gfts-ifremer")
TARGET_BUCKET = os.environ.get("TARGET_BUCKET", "destine-gfts-visualisation-data")
TAG_ROOT = os.environ.get("TAG_ROOT")
TAG_ROOT_STORAGE_OPTIONS = json.loads(os.environ.get("TAG_ROOT_STORAGE_OPTIONS", "{}"))  # type: dict
SOURCE_PREFIX = os.environ.get("SOURCE_PREFIX")
SOURCE_SUFFIX = os.environ.get("SOURCE_SUFFIX", "")
TARGET_PREFIX = os.environ.get("TARGET_PREFIX")

# BARGIP campaign settings
# TAG_ROOT = "bargip/tag/formatted/"
# TAG_ROOT_STORAGE_OPTIONS = {
#     "anon": False,
#     "profile": PROFILE,
#     "client_kwargs": {
#         "endpoint_url": ENDPOINT,
#         "region_name": REGION,
#     },
# }
# SOURCE_PREFIX = "tags/bargip/tracks_4/"
# SOURCE_SUFFIX = ""
# TARGET_PREFIX = "bargip_sea_bass/"

# FISH-INTEL Pollock settings
# TAG_ROOT = "https://data-taos.ifremer.fr/data_tmp/cleaned/tag/"
# TAG_ROOT_STORAGE_OPTIONS = {}
# SOURCE_PREFIX = "bar_taos/run/quentinmaz/pollock/"
# SOURCE_SUFFIX = ""
# TARGET_PREFIX = "taos_pollock/"

# FISH-INTEL Sea bass settings
# TAG_ROOT = "bar_taos/formatted/"
# TAG_ROOT_STORAGE_OPTIONS = {
#     "anon": False,
#     "profile": PROFILE,
#     "client_kwargs": {
#         "endpoint_url": ENDPOINT,
#         "region_name": REGION,
#     },
# }
# SOURCE_PREFIX = "NO DATA YET"
# SOURCE_SUFFIX = ""
# TARGET_PREFIX = "taos_sea_bass/"


boto3.setup_default_session(profile_name=PROFILE)


def get_filesystem():
    """return a S3FileSystem based on global settings."""
    return s3fs.S3FileSystem(
        anon=False,
        profile=PROFILE,
        client_kwargs={
            "endpoint_url": ENDPOINT,
            "region_name": REGION,
        },
    )


def regrid_to_rotate(data, cell_ids_rotated, ids_weight, weight):
    in_map = {}
    for i in range(4):
        for j in ids_weight[i]:
            in_map[j] = 0.0

    for k in range(len(cell_ids_rotated)):
        in_map[cell_ids_rotated[k]] = data[k]
    result = weight[0] * np.array([in_map[k] for k in ids_weight[0]])
    result += weight[1] * np.array([in_map[k] for k in ids_weight[1]])
    result += weight[2] * np.array([in_map[k] for k in ids_weight[2]])
    result += weight[3] * np.array([in_map[k] for k in ids_weight[3]])
    return data


def _rotate_data(ds: xr.Dataset) -> xr.Dataset:
    logger.debug("Rotating tag data")

    data = (
        ds.rename_vars({"latitude": "lat_good", "longitude": "lon_good"}).stack(
            cell=["x", "y"], create_index=False
        )
    ).chunk({"time": 1})

    data.cell_ids.attrs = {
        "grid_name": "healpix",
        "nside": NSIDE,
        "nest": NEST,
    }
    data = data.pipe(xdggs.decode)

    # compute the rotated latitude and longituted based on the rotated cell_ids.
    data = (
        data.assign_coords(data.dggs.cell_centers().coords)
        .rename_vars({"longitude": "lon_rotated"})
        .drop_vars("latitude")
    )
    # This fix is due to the way that xdggs computes the cell centers.
    data["lon_rotated"] -= 180

    # drop cell's which only has the np.nan for all the time series here.
    data = data.dropna(dim="cell", subset=["states"], how="all")

    rotated_angle_lon = (data.lon_rotated[0] - data.lon_good[0]).data.compute()

    data["states_rotated"] = data.states
    data["cell_ids_rotated"] = data.cell_ids
    theta = (90 - data.lat_good.compute()) / 180 * np.pi
    ph = (data.lon_good.compute() + 180) / 180 * np.pi
    ph = np.fmod(ph, np.pi * 2)
    cell_id_new = hp.ang2pix(
        NSIDE, data.lon_good, data.lat_good, nest=NEST, lonlat=True
    )
    data["cell_ids"] = cell_id_new
    ph_rotated = ph + rotated_angle_lon / 180 * np.pi
    ids_weight, weight = hp.get_interp_weights(NSIDE, theta, ph_rotated, nest=NEST)

    data = data.chunk({"time": 1, "cell": -1})

    logger.debug("Applying ufunc for regridding")
    data["states"][:, :] = xr.apply_ufunc(
        regrid_to_rotate,
        data.states_rotated,
        data.cell_ids_rotated,
        ids_weight,
        weight,
        input_core_dims=[["cell"], ["cell"], ["z", "cell"], ["z", "cell"]],
        output_core_dims=[
            ["cell"],
        ],
        exclude_dims=set(("z",)),
        vectorize=True,
        dask="parallelized",
        output_dtypes=[data.states.dtype],
    )

    vars_to_keep = ["states", "cell_ids", "time"]
    vars_to_drop = [var for var in data.variables if var not in vars_to_keep]
    data = data.drop_vars(vars_to_drop)

    return data


def rotate_data(ds: xr.Dataset):
    if "cells" in ds.dims:
        logger.debug("ds is already a HEALPix grid")
        vars_to_keep = ["states", "cell_ids", "time"]
        vars_to_drop = [var for var in ds.variables if var not in vars_to_keep]
        return (
            ds.drop_vars(vars_to_drop)
            .rename({"cells": "cell"})
            .chunk({"time": 1, "cell": -1})
        )
    elif all(d in ds.dims for d in ["x", "y"]):
        return _rotate_data(ds)
    else:
        raise ValueError('ds\'s dimensions must either include "cells" or ["x", "y"].')


def top_values(x: xr.Dataset):
    time_slice = x.fillna(0).isel(time=0)
    sorted_dataset = time_slice.sortby("states", ascending=False)
    threshold = sorted_dataset.isel(cell=200)
    filtered_dataset = x.where(x.states > threshold.states, 0)
    return filtered_dataset


def filter_top_values(data: xr.Dataset):
    logger.debug("Extracting top values for each time")
    filtered_data = (
        data.chunk({"time": 1, "cell": -1})
        .map_blocks(top_values, template=data)
        .compute()
    )
    filtered_data = filtered_data.where(filtered_data != 0).dropna("cell", how="all")
    return filtered_data


def open_dataset(tag):
    """open a remote states.zarr array."""
    logger.debug(f"Opening tag {tag}")

    store = s3fs.S3Map(
        root=f"s3://{SOURCE_BUCKET}/{SOURCE_PREFIX}{tag}/{SOURCE_SUFFIX}states.zarr",
        s3=get_filesystem(),
        check=False,
    )
    return xr.open_zarr(store)


def open_dst(root: str, tag_name: str, storage_options={}):
    if not root.endswith("/"):
        root += "/"

    if storage_options == {}:
        path = f"{root}{tag_name}/dst.csv"
    else:
        path = f"s3://{SOURCE_BUCKET}/{root}{tag_name}/dst.csv"

    return pd.read_csv(path, storage_options=storage_options)[
        ["time", "temperature", "pressure"]
    ]


def open_metadata(root: str, tag_name: str, storage_options={}) -> dict:
    logger.debug(f"Writing markdown file for {tag_name}.")

    if not root.endswith("/"):
        root += "/"

    if storage_options == {}:
        path = f"{root}{tag_name}/metadata.json"
    else:
        path = f"s3://{SOURCE_BUCKET}/{root}{tag_name}/metadata.json"

    try:
        with fsspec.open(path, mode="r", **storage_options) as f:
            return json.load(f)
    except Exception:
        logger.log(f'An error occurred when fetching: "{path}".')
        return {}


def dict_to_md_table(data: dict, columns: list):
    if (not isinstance(columns, list)) or len(columns) != 2:
        columns = ["Key", "Value"]

    headers = [f"| {columns[0]}  | {columns[1]} |", "| ------------- | ------------- |"]
    rows = [f"| {k} | {v} |" for k, v in data.items()]
    return "\n".join(headers + rows)


def save_metadata(md_content: str, tag: str):
    logger.debug(f"Writing markdown file for {tag}")

    with get_filesystem().open(
        f"s3://{TARGET_BUCKET}/{TARGET_PREFIX}{tag}/{tag}.md",
        "w",
    ) as fl:
        fl.write(md_content)


def add_pressure_and_temperature(df: pd.DataFrame, tag: str) -> pd.DataFrame:
    """Adds temperature and pression columns to df.
    The values are added only to the most probable daily cell/cell_ids for each time.
    """
    logger.debug(f"Adding pressure and temperature {tag}")

    ts = open_dst(TAG_ROOT, tag, TAG_ROOT_STORAGE_OPTIONS)

    ts.time = pd.to_datetime(ts.time).dt.tz_localize(None)

    ts = ts.set_index("time").resample("D").mean()

    most_probable_cells = (
        df.sort_values("states", ascending=False)
        .drop_duplicates("time")
        .set_index("time")
    )

    mpc_with_temp = most_probable_cells.merge(
        ts, left_index=True, right_index=True
    ).reset_index()
    mpc_with_temp = mpc_with_temp[["time", "cell_ids", "pressure", "temperature"]]
    mpc_with_temp = mpc_with_temp.set_index(["time", "cell_ids"])

    df = df.set_index(["time", "cell_ids"])
    # detects hourly-indexed `df`
    # better to do it before re-indexing?
    # pd.DatetimeIndex(pd.to_datetime(df["time"]).drop_duplicates()).inferred_freq
    freq = df.index.get_level_values(0).drop_duplicates().inferred_freq
    if freq is None:
        msg = f"The time frequency of the location estimations of tag {tag} could not be inferred."
        logger.debug(msg)

    if freq.lower() == "h":
        logger.debug("Aggregating `df` daily...")
        df = df.groupby([pd.Grouper(level="time", freq="D"), "cell_ids"]).mean()
        df["cell"] = df["cell"].astype("Int64")

    daily_with_mpc_temp = df.merge(
        mpc_with_temp, left_index=True, right_index=True, how="left"
    )

    return daily_with_mpc_temp.reset_index()


def to_parquet(df: pd.DataFrame, tag: str):
    logger.debug(f"Writing parquet file for {tag}")

    df = df.set_index(["time", "cell_ids"])

    with get_filesystem().open(
        f"s3://{TARGET_BUCKET}/{TARGET_PREFIX}{tag}/{tag}_healpix.parquet",
        "wb",
    ) as fl:
        df.to_parquet(fl)


def list_tags():
    logger.debug("Listing tags")

    s3 = boto3.resource(service_name="s3", endpoint_url=ENDPOINT)

    folders = s3.meta.client.list_objects(
        Bucket=SOURCE_BUCKET, Prefix=SOURCE_PREFIX, Delimiter="/"
    )
    tags = [dat["Prefix"].split("/")[-2] for dat in folders["CommonPrefixes"]]
    return tags


def process_tag(tag: str):
    data = open_dataset(tag)
    result = rotate_data(data)
    result = filter_top_values(result)
    result = result.to_dataframe().dropna().reset_index()
    result_with_temp = add_pressure_and_temperature(result, tag)

    to_parquet(df=result_with_temp, tag=tag)

    data = open_metadata(TAG_ROOT, tag, TAG_ROOT_STORAGE_OPTIONS)
    md_content = dict_to_md_table(data, columns=["Attribute", "Description"])
    save_metadata(md_content, tag)


def already_processed(tag: str):
    return get_filesystem().exists(
        f"s3://{TARGET_BUCKET}/{SOURCE_PREFIX}{tag}/{tag}_healpix.parquet"
    )


def has_states(tag: str):
    return get_filesystem().exists(
        f"s3://{SOURCE_BUCKET}/{SOURCE_PREFIX}{tag}/states.zarr"
    )


def filter_tags(tags: list[str], start: int, end: int):
    logger.debug(f"Filtering tags from start {start} to end {end}")
    if start is not None:
        tags = tags[start:end]
    return [tag for tag in tags if not already_processed(tag) and has_states(tag)]
    # return [tag for tag in tags if has_states(tag)]


@click.command()
@click.option("--start", default=None, help="Start index for tags.", type=int)
@click.option("--end", default=None, help="End index for tags", type=int)
def main(start, end):
    tags = list_tags()
    tags = filter_tags(tags, start, end)

    logger.debug(f"About to process {len(tags)} tags...")

    for tag in tags:
        process_tag(tag)


if __name__ == "__main__":
    main()
