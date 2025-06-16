from pathlib import Path
import xarray as xr
import healpy as hp
import numpy as np
import xdggs
import pandas as pd
import os

DT_NSIDE = 1024
FISH_NSIDE = 4096

BASE_DIR = os.environ.get("BASE_DIR", "~/Documents/repos/DestinE_ESA_GFTS")
SPECIES = "pollock"
DATA_DIR = os.environ.get("DATA_DIR", "~/Documents/repos/gfts/static/data/pollock")


def create_seasonal_summaries(model="IFS-NEMO", params=["263100", "263101"]):
    combined = None
    for param in params:
        datasets = []
        for path in Path(f"{BASE_DIR}/forecast-data/data").glob(
            f"{model}-{param}-*.zarr"
        ):
            print(path)
            ds = xr.open_dataset(path)
            ds = ds.isel(number=0, steps=0)
            ds = ds.assign_coords(y=xr.where(ds.y > 180, ds.y - 360, ds.y))
            ds["datetimes"] = ds.datetimes.astype("datetime64[ns]")
            datasets.append(ds)
        datasets = xr.concat(datasets, dim="datetimes")
        if combined is None:
            combined = datasets
        else:
            combined = xr.merge([combined, datasets])

    combined = combined.assign_coords(
        year=combined.datetimes.dt.year, quarter=combined.datetimes.dt.quarter
    )

    seasonal = combined.groupby(["year", "quarter"])

    seasonal_avg = seasonal.mean(dim="datetimes")
    seasonal_std = seasonal.std(dim="datetimes")

    seasonal_avg["std_sos"] = seasonal_std.avg_sos
    seasonal_avg["std_tos"] = seasonal_std.avg_tos

    theta = (90 - (seasonal_avg.x.compute())) / 180 * np.pi
    ph = (seasonal_avg.y.compute() + 360) / 180 * np.pi
    ph = np.fmod(ph, np.pi * 2)

    cell_ids = hp.ang2pix(DT_NSIDE, theta, ph, nest=True)
    seasonal_avg.coords["cell_ids"] = xr.DataArray(
        cell_ids, attrs={"grid_name": "healpix", "nside": DT_NSIDE, "nest": True}
    )

    seasonal_avg = seasonal_avg.pipe(xdggs.decode)
    seasonal_avg = seasonal_avg.swap_dims({"points": "cell_ids"})
    seasonal_avg = seasonal_avg.drop(["z", "x", "y", "number", "steps", "points"])

    seasonal_avg.to_zarr(f"{BASE_DIR}/forecast-data/merged-data/{model}-seasonal.zarr")


def export_seasonal_summaries(model="IFS-NEMO"):
    seasonal_avg = xr.open_zarr(
        f"{BASE_DIR}/forecast-data/merged-data/{model}-seasonal.zarr"
    )
    for quarter in range(1, 5):
        df = seasonal_avg.sel(quarter=quarter).to_dataframe().reset_index()
        del df["std_sos"]
        del df["std_tos"]
        del df["quarter"]
        df = df[df.avg_sos.notna()]
        df.loc[:, "avg_tos"] -= 273.15
        print(f"Writing to parquet for quarter {quarter}")
        df.to_parquet(
            f"{BASE_DIR}/forecast-data/merged-data/{model}-seasonal-q{quarter}.parquet",
            index=False,
        )


def aggregate(df):
    data = xr.Dataset.from_dataframe(df)

    data.coords["cell_ids"] = xr.DataArray(
        data.cell_ids,
        attrs={"grid_name": "healpix", "nside": FISH_NSIDE, "nest": True},
    )
    data = data.pipe(xdggs.decode)

    # Get the angular coordinates for fish pixels
    fish_pixels = data.cell_ids.values
    theta_fish, phi_fish = hp.pix2ang(FISH_NSIDE, fish_pixels, nest=True)

    # Convert to the target resolution
    fish_pixels_1024 = hp.ang2pix(DT_NSIDE, theta_fish, phi_fish, nest=True)

    # Create a mapping from high-res to low-res pixels
    unique_pixels_1024, inverse_indices = np.unique(
        fish_pixels_1024, return_inverse=True
    )

    # Aggregate the weights to the lower resolution
    weights_1024 = np.zeros(len(unique_pixels_1024))
    np.add.at(weights_1024, inverse_indices, data.states.values)

    # Create a new dataset with the resampled weights
    return xr.Dataset(
        data_vars={"states": (["cell_ids"], weights_1024)},
        coords={"cell_ids": unique_pixels_1024},
    )


def compute_weighted_seasonal_summaries(model="IFS-NEMO"):
    seasonal_avg_dt = xr.open_zarr(
        f"{BASE_DIR}/forecast-data/merged-data/{model}-seasonal.zarr"
    )

    results = []
    for quarter in range(4):
        print(quarter)

        df = pd.read_parquet(f"{DATA_DIR}/{SPECIES}_average_q{quarter}.parquet")

        data_1024 = aggregate(df)

        seasonal_avg = seasonal_avg_dt.sel(quarter=quarter + 1)

        # Compute weighted averages for each variable
        weighted_avgs = {}
        for var in ["avg_sos", "std_sos", "avg_tos", "std_tos"]:
            # Align the weights with the seasonal data
            weights_aligned = data_1024.states.reindex(
                cell_ids=seasonal_avg.cell_ids, fill_value=0
            )
            # Compute weighted average across all cells for each year and quarter
            weighted_avg = (seasonal_avg[var] * weights_aligned).sum(
                dim="cell_ids"
            ) / weights_aligned.sum()
            weighted_avgs[var] = weighted_avg

        # Create a new dataset with the weighted averages
        weighted_dataset = xr.Dataset(
            {
                f"weighted_{var}": weighted_avgs[var]
                for var in ["avg_sos", "std_sos", "avg_tos", "std_tos"]
            }
        )

        # Print the results
        print("\nWeighted averages by year and quarter:")
        print(weighted_dataset)

        results.append(weighted_dataset)

    combined = xr.concat(results, dim="quarter")

    combined.to_dataframe().reset_index().to_csv(
        f"{BASE_DIR}/forecast-data/merged-data/{model}-{SPECIES}-weighted-seasonal.csv",
        index=False,
    )


if __name__ == "__main__":
    # create_seasonal_summaries()
    # export_seasonal_summaries()
    compute_weighted_seasonal_summaries()
