import io
import logging
from multiprocessing import Pool

import boto3
import geopandas as gpd
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
POOL = 10


boto3.setup_default_session(profile_name=PROFILE)


def simplify_timestep(data, time):
    grp = data.copy().where(data.time == time, drop=True)
    df = grp.to_dataframe().dropna().reset_index()
    del df["x"]
    del df["y"]
    df = df.sort_values("states", ascending=False)

    return df[:NR_OF_CELLS_PER_TIMESLICE]


def get_filesystem():
    return s3fs.S3FileSystem(
        anon=False,
        profile=PROFILE,
        client_kwargs={
            "endpoint_url": ENDPOINT,
            "region_name": REGION,
        },
    )


def simplify(tag):
    logger.debug(f"Opening tag {tag}")

    store = s3fs.S3Map(
        root=f"s3://{SOURCE_BUCKET}/{PREFIX}{tag}/states.zarr",
        s3=get_filesystem(),
        check=False,
    )
    data = xr.open_zarr(store=store)

    vars_to_keep = ["states", "latitude", "longitude", "time"]
    vars_to_drop = [var for var in data.variables if var not in vars_to_keep]
    data = data.drop_vars(vars_to_drop)

    # Do one by one to save memory. Most timestamps have a lot of nodata
    # that can be dropped in the loop. If done in one step this will grow fast.
    dfs = []
    for time in data.time:
        dfs.append(simplify_timestep(data, time))
        if len(dfs) % 25 == 0:
            logger.debug(
                f"Finished {len(dfs) + 1} timesteps for {tag} currently at {time.values}"
            )
    return pd.concat(dfs)


def to_geojson(df, tag):
    logger.debug(f"Writing geojson file for {tag}")

    track = df.sort_values("states", ascending=False).drop_duplicates("time")
    track = track.sort_values("time")

    geom = gpd.points_from_xy(track.longitude, track.latitude)
    track = gpd.GeoDataFrame(
        track[["time", "states"]],
        geometry=geom,
        crs="EPSG:4326",
    )
    with io.BytesIO() as buf:
        track.to_file(buf, driver="GeoJSON")
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


def main():
    logger.debug("Listing tags")
    tags = list_tags()

    if POOL == 1:
        for tag in tags:
            process_tag(tag)
    else:
        with Pool(POOL) as pl:
            pl.map(process_tag, tags)


if __name__ == "__main__":
    main()
