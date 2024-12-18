import xdggs

from simplify import has_states, list_tags, logger, open_dataset

NSIDE = 4096


def main():
    logger.debug("Listing tags")
    tags = list_tags()
    result = None
    timpesteps = 0
    for tag in tags:
        if not has_states(tag):
            logger.debug(f"No states.zarr file found for {tag}")
            continue

        data = open_dataset(tag)
        timpesteps += data.time.shape[0]

        data.cell_ids.attrs = {
            "grid_name": "healpix",
            "nside": NSIDE,
            "nest": True,
        }

        data = data.drop_vars(["latitude", "longitude"]).stack(
            cell=["x", "y"], create_index=False
        )
        data = data.set_xindex("cell_ids", xdggs.DGGSIndex)

        avg_by_quarter = data.groupby("time.quarter").sum("time", skipna=True)

        if result is None:
            result = avg_by_quarter
        else:
            result += avg_by_quarter

    result = result / timpesteps

    result.to_zarr("data/pollock_average.zarr")

    # Also export normalized and sretched as uint16
    max_value = result.states.max()
    result.states = (result.states / max_value * 65535).astype("uint16")

    result.to_zarr("data/pollock_average_uint16.zarr")


if __name__ == "__main__":
    main()
