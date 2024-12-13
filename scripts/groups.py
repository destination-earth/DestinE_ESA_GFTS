from simplify import has_states, list_tags, logger, open_dataset


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

        data.cell_ids.attrs.update(
            {
                "grid_name": "healpix",
                "level": 10,
                # "resolution": data.resolution.values,
            }
        )

        # data = xdggs.decode(data)

        avg_by_quarter = data.groupby("time.quarter").sum("time")

        if result is None:
            result = avg_by_quarter
        else:
            result += avg_by_quarter

    result = result / timpesteps

    # Normalize and sretch to uint16 range
    max_value = result.states.max()
    avg_by_quarter.states = (avg_by_quarter.states / max_value * 65535).astype("uint16")

    result.to_zarr("data/pollock_average.zarr")


if __name__ == "__main__":
    main()
