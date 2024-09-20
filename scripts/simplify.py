import logging

import pandas as pd
import geopandas as gpd
import xarray as xr
import boto3
import s3fs
from multiprocessing import Pool

logging.basicConfig()

logger = logging.getLogger("gfts")
logger.setLevel(logging.DEBUG)
ENDPOINT = "https://s3.gra.perf.cloud.ovh.net/"
BUCKET = "gfts-ifremer"
PREFIX = "tags/bargip/tracks_4/"
PROFILE = "ovh_gfts"
REGION = "gra"
NR_OF_CELLS_PER_TIMESLICE = 200
POOL = 10


boto3.setup_default_session(profile_name=PROFILE)


def simplify(tag):
    logger.debug(f"Opening tag {tag}")

    fsg = s3fs.S3FileSystem(
        anon=False,
        profile=PROFILE,
        client_kwargs={
            "endpoint_url": ENDPOINT,
            "region_name": REGION,
        },
    )
    store = s3fs.S3Map(
        root=f"s3://{BUCKET}/{PREFIX}{tag}/states.zarr",
        s3=fsg,
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
        grp = data.where(data.time == time, drop=True)
        df = grp.to_dataframe().dropna().reset_index()
        del df["x"]
        del df["y"]
        df = df.sort_values("states", ascending=False)
        if len(dfs) % 25 == 0:
            logger.debug(
                f"Finished {len(dfs) + 1} timesteps for {tag} currently at {time.values}"
            )

        dfs.append(df[:NR_OF_CELLS_PER_TIMESLICE])

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
    track.to_file(f"data/{tag}.geojson", driver="GeoJSON")


def to_parquet(df, tag):
    logger.debug(f"Writing parquet file for {tag}")

    # Convert variables to integer for better compression
    df["longitude"] = (df["longitude"] * 1e6).astype("int32")
    df["latitude"] = (df["latitude"] * 1e6).astype("int32")
    max_value = df["states"].max()
    df["states"] = (df["states"] / max_value * 65535).astype("uint16")

    df = df.set_index(["time", "longitude", "latitude"])

    df.to_parquet(f"data/{tag}.parquet")


def list_tags():
    s3 = boto3.resource(service_name="s3", endpoint_url=ENDPOINT)

    folders = s3.meta.client.list_objects(Bucket=BUCKET, Prefix=PREFIX, Delimiter="/")
    tags = [dat["Prefix"].split("/")[-2] for dat in folders["CommonPrefixes"]]
    return tags


def process_tag(tag):
    df = simplify(tag=tag)
    to_geojson(df=df, tag=tag)
    to_parquet(df=df, tag=tag)


def main():
    logger.debug("Listing tags")
    tags = list_tags()

    with Pool(POOL) as pl:
        pl.map(process_tag, tags)


if __name__ == "__main__":
    main()
