import xarray as xr
import cfgrib
from pathlib import Path

def read_grib_file(filepath):
    """
    Read a GRIB file and return an xarray Dataset.
    
    Args:
        filepath (str): Path to the GRIB file
    
    Returns:
        xarray.Dataset: The loaded dataset
    """
    ds = xr.open_dataset(filepath, engine='cfgrib', decode_timedelta=True)
    return ds

def print_dataset_info(ds):
    """
    Print basic information about the dataset.
    
    Args:
        ds (xarray.Dataset): The dataset to analyze
    """
    print("\nDataset Info:")
    print(ds.info())
    
    print("\nVariables in dataset:")
    for var in ds.data_vars:
        print(f"- {var}: {ds[var].attrs.get('long_name', 'No long name available')}")

def print_temperature_dates(ds):
    """
    Print the first and last dates with their respective values for all variables.
    
    Args:
        ds (xarray.Dataset): The dataset to analyze
    """
    valid_time = ds.valid_time.values
    
    print("\nData Summary:")
    print(f"Valid time: {valid_time}")
    print(f"Total number of observations: {len(ds[list(ds.data_vars)[0]].values):,}")
    
    def print_observation_values(ds, index, label):
        print(f"\n{label} observation values:")
        try:
            lat = ds.latitude.values[index]
            lon = ds.longitude.values[index]
            print(f"- location: {lat:.4f}°N, {lon:.4f}°E")
        except Exception as e:
            print(f"- location: Error reading coordinates - {str(e)}")
        
        for var in ds.data_vars:
            if var not in ['latitude', 'longitude']:  # Skip coordinates as we already printed them
                try:
                    value = ds[var].values[index]
                    units = ds[var].attrs.get('units', 'N/A')
                    long_name = ds[var].attrs.get('long_name', var)
                    print(f"- {var}: {value:.2f} {units} ({long_name})")
                except Exception as e:
                    print(f"- {var}: Error reading value - {str(e)}")
    
    print_observation_values(ds, 0, "First")
    print_observation_values(ds, -1, "Last")


if __name__ == "__main__":
    # Get all GRIB files in the current directory
    grib_files = list(Path('.').glob('*.grib'))
    
    if grib_files:
        print(f"Found {len(grib_files)} GRIB files")
        
        # Process each GRIB file
        for i, grib_file in enumerate(grib_files, 1):
            print(f"\n{'='*50}")
            print(f"Processing file {i}/{len(grib_files)}: {grib_file}")
            print(f"{'='*50}")
            
            # Read the GRIB file
            ds = read_grib_file(grib_file)
            
            # Print information about the dataset
            #print_dataset_info(ds)
            
            # Print temperature dates
            print_temperature_dates(ds)
            
            # Close the dataset when done
            ds.close()
    else:
        print("No GRIB files found in the current directory") 