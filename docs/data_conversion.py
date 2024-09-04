import pandas as pd
import numpy as np
from datetime import datetime
import csv
import json
import os
import pytz
import s3fs


def show_data_csv(chemin_fichier):
    with open(chemin_fichier, newline="", encoding="latin-1") as csvfile:
        # Créer un lecteur CSV
        lecteur_csv = csv.reader(csvfile, delimiter=",")

        for ligne in lecteur_csv:
            if ligne != []:  ### Removes empty spaces
                print(ligne)


def create_metadata_file(file_path, destination_path, remote=False):
    """
    Create a metadata JSON file based on the provided data path.

    Args:
        file_path (str): The path from which to extract the tag name.
        destination_path (str): The path where you want the metadata file to be written.
        remote (bool): If True, save the file to an S3 path. If False, save it locally.

    Returns:
        None
    """
    # Extract the tag name from the file path
    tag_id = extract_name(file_path)

    # Create the metadata dictionary
    metadata = {
        "pit_tag_id": tag_id,
        "scientific_name": "Dicentrarchus labrax",
        "common_name": "European seabass",
        "project": "BARGIP",
    }

    # Set the filename for the metadata file
    filename = "metadata.json"

    if remote:
        # If remote is True, save the file to an S3 path
        s3 = s3fs.S3FileSystem(
            anon=False,
            client_kwargs={
                "endpoint_url": "https://s3.gra.perf.cloud.ovh.net",  # S3 endpoint for OVH
            },
        )
        full_destination_path = os.path.join(destination_path, filename)
        with s3.open(full_destination_path, "w") as f:
            json.dump(metadata, f)
    else:
        # If remote is False, save the file locally
        full_destination_path = os.path.join(destination_path, filename)
        with open(full_destination_path, "w") as f:
            json.dump(metadata, f)


def extract_name(file_path):
    """
    Extracts the filename without extension from the given path.

    Args:
    path (str): The file path.

    Returns:
    str: The filename without extension.
    """
    # Use os.path.basename to get the filename
    file_name = os.path.basename(file_path)
    # Use os.path.splitext to separate the filename from its extension and get the first element
    file_name_without_extension = os.path.splitext(file_name)[0]
    return file_name_without_extension


def convert_to_utc_with_formatting(date, time_zone):
    """
    Convert the given date string to UTC time, with flexible date format parsing.

    Parameters:
        date (str): A string representing the date and time.
                    Supports various formats including '%d/%m/%Y %H:%M', '%d/%m/%y %H:%M',
                    '%d/%m/%Y %H:%M:%S', '%d/%m/%y %H:%M:%S', '%y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M:%S'.
        time_zone (str): A string representing the time zone, e.g., 'America/New_York', 'Europe/London', etc.

    Returns:
        str: A string representing the converted date and time in UTC in the format 'yyyy-mm-ddThh:mm:ssZ'.

    Raises:
        ValueError: If the input date string is not in any of the supported formats or the time zone is invalid.
    """
    # Define possible date formats
    possible_formats = [
        "%d/%m/%Y %H:%M",
        "%d/%m/%y %H:%M",
        "%d/%m/%Y %H:%M:%S",
        "%d/%m/%y %H:%M:%S",
        "%y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%SZ",
    ]

    # Try parsing the date with different formats
    for fmt in possible_formats:
        try:
            # Attempt to parse the date with the current format
            parsed_date = datetime.strptime(date, fmt)
            # Convert the parsed date to the specified time zone
            tz = pytz.timezone(time_zone)
            localized_time = tz.localize(parsed_date)
            # Convert the localized time to UTC
            utc_time = localized_time.astimezone(pytz.utc)
            # Format the UTC time as a string and return it
            return utc_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            # If parsing fails with the current format, try the next one
            pass

    # If none of the formats work, raise a ValueError
    raise ValueError("Invalid date format: {}".format(date))


def format_date(date):
    """
    Convert the date to the accurate ISO8601 time format
    """
    possible_formats = [
        "%d/%m/%Y %H:%M",
        "%d/%m/%y %H:%M",
        "%d/%m/%Y %H:%M:%S",
        "%d/%m/%y %H:%M:%S",
        "%y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
    ]

    # Try parsing the date with different formats
    for fmt in possible_formats:
        try:
            # Attempt to parse the date with the current format
            parsed_date = datetime.strptime(date, fmt)
            # Convert the parsed date to ISO8601 format and return it
            return parsed_date.strftime("%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            # If parsing fails with the current format, try the next one
            pass

    # If none of the formats work, raise a ValueError
    raise ValueError("Invalid date format: {}".format(date))


def format_coord(coordinate_str):
    """
    Convert a coordinate string into a numeric value.

    Parameters:
        coordinate_str (str): A string representing a coordinate in the format "value direction",
                              where direction is either 'E' or 'W' for longitude, or 'N' or 'S' for latitude.

    Returns:
        float: The numeric value of the coordinate. Positive if the direction is 'E' or 'N',
               negative if the direction is 'W' or 'S'.
    """
    # Split the numeric value and direction (E or W, N or S)
    val, direction = coordinate_str.split()

    # Convert the value to float64
    val = np.float64(val)

    # Check the direction and adjust the value accordingly
    if direction.upper() == "W" or direction.upper() == "S":
        val = -val

    return val


def extract_tagging_events(file_path, time_zone="Europe/Paris", remote=False):
    """
    Extracts releasing date and presumed date of fish death from a CSV file stored locally or on S3.

    Args:
        file_path (str): The path to the CSV file. For remote files, provide the S3 URI.
        time_zone (str): The time zone to use for date conversion.
        remote (bool): If True, fetch the file from S3. If False, read the file locally.

    Returns:
        pd.DataFrame: A DataFrame containing event names, times, longitudes, and latitudes.
    """
    release_date = None
    fish_death = None
    lon = []
    lat = []

    if remote:
        # Use s3fs to connect to the S3-compatible storage
        s3 = s3fs.S3FileSystem(
            anon=False,
            client_kwargs={
                "endpoint_url": "https://s3.gra.perf.cloud.ovh.net",  # S3 endpoint for OVH
            },
        )
        # Open the file from S3
        csvfile = s3.open(file_path, mode="r", encoding="latin-1")
    else:
        # Open the file locally
        csvfile = open(file_path, newline="", encoding="latin-1")

    try:
        # Create a CSV reader
        csv_reader = csv.reader(csvfile, delimiter=",")

        # Read each line of the CSV file
        for line in csv_reader:
            if line:
                # Extract the release date and convert it to UTC
                if line[0] == "releasing date ":
                    release_date = convert_to_utc_with_formatting(
                        line[1], time_zone=time_zone
                    )

                # Extract the presumed date of fish death and convert it to UTC
                if line[0] == "presumed date of fish death  ":
                    fish_death = convert_to_utc_with_formatting(
                        line[1], time_zone=time_zone
                    )

                # Extract the fish release position (latitude and longitude)
                if line[0] == "fish release position ":
                    if line[1] != "unknown":
                        lat.append(format_coord(line[1]))
                        lon.append(format_coord(line[2]))
                    else:
                        lat.append(np.nan)  # Use NaN if the position is unknown
                        lon.append(np.nan)

                # Extract the fish recapture position (latitude and longitude)
                if line[0] == "fish recapture position ":
                    if line[1] != "unknown":
                        lat.append(format_coord(line[1]))
                        lon.append(format_coord(line[2]))
                    else:
                        lat.append(np.nan)  # Use NaN if the position is unknown
                        lon.append(np.nan)

        # Combine the extracted data into a DataFrame
        dates = [release_date, fish_death]
        data = {
            "event_name": ["release", "fish_death"],
            "time": dates,
            "longitude": lon,
            "latitude": lat,
        }
        events = pd.DataFrame(data)

    finally:
        # Close the file after reading
        csvfile.close()

    # Return the DataFrame containing the extracted events
    return events


def extract_DST(file_path, time_zone, remote=False):
    """
    Extracts time, pressure, and temperature data from a CSV file containing time series data.

    Args:
        file_path (str): The path to the CSV file. For remote files, provide the S3 URI.
        time_zone (str): The time zone for date conversion.
        remote (bool): If True, fetch the file from S3. If False, read the file locally.

    Returns:
        pandas.DataFrame: A DataFrame containing the extracted data.
    """
    # List to store all the data
    all_data = []
    expected_length = 0

    # Extracting tag ID from the file path
    tag_id = extract_name(file_path)

    if remote:
        # Use s3fs to connect to the S3-compatible storage
        s3 = s3fs.S3FileSystem(
            anon=False,
            client_kwargs={
                "endpoint_url": "https://s3.gra.perf.cloud.ovh.net",  # S3 endpoint for OVH
            },
        )
        # Open the file from S3
        csvfile = s3.open(file_path, mode="r", encoding="latin-1")
    else:
        # Open the file locally
        csvfile = open(file_path, newline="", encoding="latin-1")

    try:
        # Create a CSV reader
        csv_reader = csv.reader(csvfile, delimiter=",")

        # Variables to store data for the current block
        data = []
        reached_target_line = False

        # Read each line of the CSV file
        for line in csv_reader:
            # If the line is not empty and contains information about the expected length of data
            if line and "Data points available =" in line[0]:
                expected_length += int(line[0].split(sep="=")[1])

            # Check if the current line is the target line
            if not reached_target_line:
                if line == ["Date/Time Stamp", "Pressure", "Temp"]:
                    reached_target_line = True
            else:
                # If the line is empty, add the data of the current block to the total and reset the data of the block
                if not line:
                    if data:
                        all_data.extend(data)
                        data = []
                    reached_target_line = False
                else:
                    # Otherwise, add the line of data to the current block
                    line[0] = format_date(line[0])  # Format date to ISO8601
                    line[1] = np.float64(
                        line[1]
                    )  # Convert data type from str to float64
                    line[2] = np.float64(
                        line[2]
                    )  # Convert data type from str to float64

                    data.append(line)

    finally:
        # Close the file after reading
        csvfile.close()

    # Convert all the data into a pandas DataFrame
    df = pd.DataFrame(all_data, columns=["time", "pressure", "temperature"])[
        ["time", "temperature", "pressure"]
    ]

    # Getting all the timestamps
    time_stamps = pd.to_datetime(df["time"])

    # Calculting time deltas
    time_deltas = time_stamps - time_stamps.iloc[0]

    # Getting first timestamp and converting it to utc.
    initial_time = time_stamps.iloc[0].strftime("%Y-%m-%dT%H:%M:%SZ")
    time_utc = pd.to_datetime(
        convert_to_utc_with_formatting(initial_time, "Europe/Paris")
    )

    # Calculating the new timestamps series and formatting it to ISO8601
    corrected_timestamps = time_deltas + time_utc
    formatted_corrected_timestamps = corrected_timestamps.dt.strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )

    # Replacing the in the dataframe
    df["time"] = formatted_corrected_timestamps

    # Check if the expected length matches the actual length of data extracted
    if expected_length == df.shape[0]:
        print("Extraction for tag {} complete, no missing data".format(tag_id))
    else:
        print("Extraction for tag {} might be incomplete, be careful".format(tag_id))

    return df


def compat_checking(check_filepath, ref_filepath):
    """
    Check the compatibility between a generated file and a reference file.

    Args:
        check_filepath (str): Path to the generated file that needs to be checked.
        ref_filepath (str): Path to the reference file already in a pangeo-fish compatible format.

    Returns:
        None

    """
    # Load the generated file
    generated_df = pd.read_csv(check_filepath)

    # Load the reference file
    reference_df = pd.read_csv(ref_filepath)

    print("tests:")
    # Test 1: Check if the columns are the same
    if list(generated_df.columns) == list(reference_df.columns):
        print("- Column names match.")
    else:
        print("- Column names do not match.")

    # Test 2: Check if the data types are the same
    if generated_df.dtypes.equals(reference_df.dtypes):
        print("- Data types match.")
    else:
        print("- Data types do not match.")


def save_dataframe_to_s3(dataframe, destination_path):
    """
    Save a pandas DataFrame to a CSV file on an S3 path.

    Args:
        dataframe (pd.DataFrame): The DataFrame to save.
        destination_path (str): The S3 destination path where the CSV will be saved.

    Returns:
        None
    """
    # Create an S3 filesystem object
    s3 = s3fs.S3FileSystem(
        anon=False,
        client_kwargs={
            "endpoint_url": "https://s3.gra.perf.cloud.ovh.net",  # S3 endpoint for OVH
        },
    )

    # Save the DataFrame to the specified S3 path
    with s3.open(destination_path, "w") as f:
        dataframe.to_csv(f)
