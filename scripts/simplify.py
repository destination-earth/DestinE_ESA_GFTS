import json
import logging

import pandas as pd
import xarray as xr

logging.basicConfig()

logger = logging.getLogger("gfts")
logger.setLevel(logging.DEBUG)

NR_OF_CELLS_PER_TIMESLICE = 200

def simplify(tag):
    logger.debug(f"Opening tag {tag}")
    data = xr.open_zarr(f"data/{tag}.zarr")

    vars_to_keep = ["pdf", "latitude", "longitude", "time"]
    vars_to_drop = [var for var in data.variables if var not in vars_to_keep]
    logger.debug(f"Dropping vars {vars_to_drop}")
    data = data.drop_vars(vars_to_drop)

    # max_probability = data.pdf.max().values
    # threshold = max_probability * 1e-4

    # logger.debug(f"Threholding data to {threshold}")
    # data = data.where(data > threshold)

    # Do one by one to save memory. Most timestamps have
    # a lot of nodata.
    logger.debug(f"Creating dataframe")
    dfs = []
    # for time, grp in data.groupby("time"):
    for time in data.time:
        logger.debug(f"Working on time {time.values}")
        grp = data.where(data.time == time, drop=True)
        grp = grp.where(data.pdf > 1e-6)
        df = grp.to_dataframe().dropna().reset_index()
        del df["x"]
        del df["y"]
        df = df.sort_values("pdf", ascending=False)
        dfs.append(df[:NR_OF_CELLS_PER_TIMESLICE])
        # if len(dfs) > 50:
        #     break

    combined = pd.concat(dfs)

    # Convert probability to integer
    # max_value = combined["pdf"].max()
    # combined["pdf"] = (combined["pdf"] / max_value * 65535).astype("uint16")

    return combined


def to_geojson(df, tag):
    geo_path = df.sort_values('pdf', ascending=False).drop_duplicates('time').sort_values("time")

    feature = {
        "type": "Feature",
        "geometry": {"type": "LineString", "coordinates": []},
        "properties": {"time": [], "value": []},
    }

    feature["geometry"]["coordinates"] = list(zip(geo_path["longitude"], geo_path["latitude"]))
    feature["properties"]["time"] = [str(dat.date()) for dat in geo_path.time.to_list()]
    feature["properties"]["pdf"] = geo_path["pdf"].to_list()
    # d = geo_path.to_dict()


    # for i in range(len(d["time"])):
        
    #     feature["properties"]["time"].append(round(d["time"][i].timestamp()))
    #     feature["properties"]["value"].append(d["pdf"][i])

    with open(f"data/{tag}.geojson", "w") as f:
        json.dump(feature, f)


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
    
