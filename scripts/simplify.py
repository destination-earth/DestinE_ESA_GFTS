import logging

import pandas as pd
import geopandas as gpd
import xarray as xr

logging.basicConfig()

logger = logging.getLogger("gfts")
logger.setLevel(logging.DEBUG)

NR_OF_CELLS_PER_TIMESLICE = 200


def simplify(tag):
    logger.debug(f"Opening tag {tag}")
    data = xr.open_zarr(f"data/{tag}.zarr")

    vars_to_keep = ["states", "latitude", "longitude", "time"]
    vars_to_drop = [var for var in data.variables if var not in vars_to_keep]
    logger.debug(f"Dropping vars {vars_to_drop}")
    data = data.drop_vars(vars_to_drop)

    # max_probability = data.states.max().values
    # threshold = max_probability * 1e-4

    # logger.debug(f"Threholding data to {threshold}")
    # data = data.where(data > threshold)

    # Do one by one to save memory. Most timestamps have
    # a lot of nodata.
    logger.debug("Creating dataframe")
    dfs = []
    # for time, grp in data.groupby("time"):
    for time in data.time:
        logger.debug(f"Working on time {time.values}")
        grp = data.where(data.time == time, drop=True)
        grp = grp.where(data.states > 1e-6)
        df = grp.to_dataframe().dropna().reset_index()
        del df["x"]
        del df["y"]
        df = df.sort_values("states", ascending=False)
        dfs.append(df[:NR_OF_CELLS_PER_TIMESLICE])
        if len(dfs) > 10:
            break

    combined = pd.concat(dfs)

    combined = gpd.GeoDataFrame(
        combined[["time", "states"]],
        geometry=gpd.points_from_xy(combined.longitude, combined.latitude),
        crs="EPSG:4326",
    )

    # Convert probability to integer
    max_value = combined["states"].max()
    combined["states"] = (combined["states"] / max_value * 65535).astype("uint16")

    return combined


def to_geojson(df, tag):
    highest_probability = (
        df.sort_values("states", ascending=False)
        .drop_duplicates("time")
        .sort_values("time")
    )
    highest_probability.to_file("data/bla.gejson", driver="GeoJSON")


def to_parquet(df, tag):
    pq = df.copy()
    pq["longitude"] = (pq["longitude"] * 1e6).astype("int16")
    pq["latitude"] = (pq["latitude"] * 1e6).astype("int16")

    pq = pq.set_index(["time", "longitude", "latitude"])
    pq.to_parquet(f"data/{tag}.parquet")


def main(tag):
    logger.debug("Simplyfing")
    df = simplify(tag=tag)
    logger.debug("Writing geojson")
    to_geojson(df=df, tag=tag)
    logger.debug("Writing parquet")
    to_parquet(df=df, tag=tag)


if __name__ == "__main__":
    # aws s3 --profile ovh_gfts --endpoint-url https://s3.gra.perf.cloud.ovh.net/ ls s3://gfts-ifremer/tags/bargip/
    main("AD_A11806")
    # main("CB_A11071")
