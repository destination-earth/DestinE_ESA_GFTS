import logging

import boto3
import healpy as hp
import numpy as np
import pandas as pd
import s3fs
import xarray as xr
import xdggs

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
NSIDE = 4096
NEST = True
UINT16_MAX = 65535


boto3.setup_default_session(profile_name=PROFILE)


def get_filesystem():
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


def rotate_data(ds):
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


def top_values(x):
    time_slice = x.fillna(0).isel(time=0)
    sorted_dataset = time_slice.sortby("states", ascending=False)
    filtered_dataset = sorted_dataset.isel(cell=slice(0, NR_OF_CELLS_PER_TIMESLICE))
    return filtered_dataset.expand_dims(time=[x.time.values[0]])


def filter_top_values(data):
    logger.debug("Extracting top values for each time")
    template = data.isel(cell=slice(0, NR_OF_CELLS_PER_TIMESLICE))
    filtered_data = (
        data.chunk({"time": 1, "cell": -1})
        .map_blocks(top_values, template=template)
        .compute()
    )

    return filtered_data


def open_dataset(tag):
    logger.debug(f"Opening tag {tag}")
    store = s3fs.S3Map(
        root=f"s3://{SOURCE_BUCKET}/{PREFIX}{tag}/states.zarr",
        s3=get_filesystem(),
        check=False,
    )
    return xr.open_zarr(store)


def add_pressure_and_temperature(df, tag):
    logger.debug(f"Adding pressure and temperature {tag}")

    path = f"s3://gfts-ifremer/bargip/tag/formatted/{tag}/dst.csv"
    fs = get_filesystem()

    if not fs.exists(path):
        raise ValueError(f"Track data for {tag} does not exist")

    with fs.open(path) as fl:
        ts = pd.read_csv(fl)

    # Remove stale column
    del ts["Unnamed: 0"]

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

    daily_with_mpc_temp = df.merge(
        mpc_with_temp, left_index=True, right_index=True, how="left"
    )

    return daily_with_mpc_temp.reset_index()


def to_parquet(df, tag):
    logger.debug(f"Writing parquet file for {tag}")

    df = df.set_index(["time", "cell_ids"])

    with get_filesystem().open(
        f"s3://destine-gfts-visualisation-data/{PREFIX}{tag}/{tag}_healpix.parquet",
        "wb",
    ) as fl:
        df.to_parquet(fl)


def list_tags():
    logger.debug("Listing tags")

    s3 = boto3.resource(service_name="s3", endpoint_url=ENDPOINT)

    folders = s3.meta.client.list_objects(
        Bucket=SOURCE_BUCKET, Prefix=PREFIX, Delimiter="/"
    )
    tags = [dat["Prefix"].split("/")[-2] for dat in folders["CommonPrefixes"]]
    return tags


def process_tag(tag):
    data = open_dataset(tag)
    result = rotate_data(data)
    result = filter_top_values(result)
    result = result.to_dataframe().dropna().reset_index()
    result_with_temp = add_pressure_and_temperature(result, tag)

    to_parquet(df=result_with_temp, tag=tag)


def already_processed(tag):
    return get_filesystem().exists(
        f"s3://destine-gfts-visualisation-data/{PREFIX}{tag}/{tag}_healpix.parquet"
    )


def has_states(tag):
    return get_filesystem().exists(f"s3://{SOURCE_BUCKET}/{PREFIX}{tag}/states.zarr")


def filter_tags(tags):
    logger.debug("Filtering tags")
    # return [tag for tag in tags if not already_processed(tag) and has_states(tag)]
    return [tag for tag in tags if has_states(tag)]


def main():
    tags = list_tags()
    tags = filter_tags(tags)
    for tag in tags:
        process_tag(tag)


if __name__ == "__main__":
    main()
