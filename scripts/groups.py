import xarray as xr
import numpy as np

from simplify import (
    has_states,
    logger,
    open_dataset,
    rotate_data,
    get_filesystem,
    TARGET_BUCKET,
    TARGET_PREFIX,
)

NSIDE = 4096


def convert_to_parquet(data: xr.Dataset):
    for quarter, group in data.groupby("quarter"):
        logger.info(f"Writing parquet file for quarter {quarter}")
        subset = (
            group.to_dataframe()
            .reset_index()
            .set_index(["cell_ids", "quarter"])
            .unstack("quarter")
        )
        # better than deleting the "cell"?
        subset = subset[["states"]]
        subset = subset.reset_index()
        subset.columns = ["cell_ids", "states"]
        subset = subset[subset > 1e-7].dropna()

        with get_filesystem().open(
            f"s3://{TARGET_BUCKET}/{TARGET_PREFIX}q{quarter}.parquet",
            "wb",
        ) as fl:
            subset.to_parquet(fl, index=False)


def rotate_group(data: xr.Dataset):
    if "cells" in data.dims:
        logger.debug("ds is already a HEALPix grid")
        vars_to_keep = ["states", "cell_ids", "quarter"]
        vars_to_drop = [var for var in data.variables if var not in vars_to_keep]
        rotated = (
            # in case of rotation, the result is a unindexed ds with variable states[quarter, cell] and coordinate cell_ids[cell]
            data.drop_vars(vars_to_drop)
            .rename({"cells": "cell"})
            .drop_indexes("quarter", errors="ignore")
            .drop_vars("quarter", errors="ignore")
        )
    else:
        rotated = rotate_data(data.rename_dims({"quarter": "time"}))
        rotated = rotated.rename_dims({"time": "quarter"})

    return rotated


def create_groups(tags: list[str], method="intersection", cell_ids=None):
    """Regroups quarterly all the states.zarr files found for a list of tags.
    Optionally, `cell_ids` along with `method` can be used to account for cases where the states.zarr files cover different studied areas.
    **The option assumes that the data has the coordinates ``cell_ids`` and is indexed by ``cells`` (i.e., HEALPix data).**


    Parameters
    ----------
    - tags : list[str]
        The names of the tags to process.
    - method : str, default to "intersection"
        Method to use in case of different areas covered by the tags. It must be used along with `cell_ids`.
        Possible values are ["intersection", "union"]:

            - ``"intersection"``: subset the tags to `cell_ids`.
            - ``"union"``: extend the tags to `cell_ids`.

    - cell_ids : array-like, optional
        Cell indices to account for different studied areas among the fish tags.

    Returns
    -------
    xarray.Dataset
        The quarterly regrouped dataset.
    """

    if (cell_ids is not None) and (method not in ["intersection", "union"]):
        raise ValueError(
            'The "method" parameter must be either "intersection" or "union".'
        )

    result = None
    timpesteps = 0
    for idx, tag in enumerate(tags):
        if not has_states(tag):
            logger.debug(f"No states.zarr file found for {tag}")
            continue
        logger.debug(f"Processing tag {tag} ({idx + 1}/{len(tags)})")

        data = open_dataset(tag)

        if cell_ids is not None:
            # intersection
            if method == "intersection":
                mask = data["cell_ids"].compute().isin(cell_ids)
                data = data.where(mask, drop=True)
            # union
            else:
                # swaps dimension and fills values
                data = data.swap_dims({"cells": "cell_ids"})
                data = data.reindex(cell_ids=cell_ids, fill_value=0)
                # and puts back cells index
                data = data.assign_coords(
                    cells=(
                        "cell_ids",
                        np.arange(data["cell_ids"].size).astype(np.int64),
                    )
                )
                data = data.swap_dims(({"cell_ids": "cells"})).reset_index(
                    "cells", drop=True
                )

        timpesteps += data.time.shape[0]
        data = data.fillna(0)

        avg_by_quarter = data.groupby("time.quarter").sum("time").compute()

        if result is None:
            result = avg_by_quarter
        else:
            # Combine both datasets and sum by quarter
            try:
                result = xr.concat(
                    [avg_by_quarter, result],
                    dim="quarter",
                )
                result = result.groupby("quarter").sum("quarter")
            except Exception as e:
                logger.debug(e)
                timpesteps -= data.time.shape[0]

        result = result.fillna(0)
        result = result.compute()

    result = result / timpesteps

    result = result.where(result != 0, other=np.nan)
    return result


if __name__ == "__main__":
    from simplify import list_tags

    tags = list_tags()
    result = create_groups(tags)
    result = rotate_group(result)
    convert_to_parquet()
