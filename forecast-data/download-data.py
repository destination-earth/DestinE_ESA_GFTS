#!/usr/bin/env python3
"""
Download climate data from the Destination Earth Polytope API.

This script downloads climate data including:
- Sea water potential temperature (thetao)
- Time-mean sea surface temperature (tos)

The data is downloaded from the Destination Earth Polytope API using the polytope client.
Authentication can be configured via environment variables or a config file.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional

from polytope.api import Client

# Default Polytope API endpoint
POLYTOPE_ADDRESS = "polytope.lumi.apps.dte.destination-earth.eu"

def setup_client(
    address: str = POLYTOPE_ADDRESS,
    user_email: Optional[str] = None,
    user_key: Optional[str] = None
) -> Client:
    """
    Set up the Polytope client with authentication.
    
    Args:
        address: Polytope API endpoint
        user_email: User email for authentication
        user_key: API key for authentication
    
    Returns:
        Client: Configured Polytope client
    """
    return Client(
        address=address,
        user_email=user_email,
        user_key=user_key
    )

def download_data(client: Client, request: Dict) -> List[str]:
    """
    Download data using the Polytope client.
    
    Args:
        client: Configured Polytope client
        request: Request parameters for data download
    
    Returns:
        List of downloaded file paths
    """
    return client.retrieve("destination-earth", request)

def get_thetao_request() -> Dict:
    """Get request parameters for sea water potential temperature data."""
    return {
        "class": "d1",
        "dataset": "climate-dt",
        "activity": "ScenarioMIP",
        "experiment": "SSP3-7.0",
        "model": "IFS-NEMO",
        "generation": "1",
        "realization": "1",
        "resolution": "high",
        "expver": "0001",
        "stream": "clte",
        "time": "0000",
        "date": "20250601",
        "type": "fc",
        "levtype": "o3d",
        "levelist": "1",
        "param": "263501"
    }

def get_tos_request() -> Dict:
    """Get request parameters for time-mean sea surface temperature data."""
    return {
        "class": "d1",
        "dataset": "climate-dt",
        "activity": "ScenarioMIP",
        "experiment": "SSP3-7.0",
        "model": "IFS-NEMO",
        "generation": "1",
        "realization": "1",
        "resolution": "high",
        "expver": "0001",
        "stream": "clte",
        "time": "0000",
        "date": "20250601",
        "type": "fc",
        "levtype": "o2d",
        "levelist": "",
        "param": "263101"
    }

def main():
    """Main function to download climate data."""
    # Set up client
    client = setup_client()
    
    # Revoke previous requests
    client.revoke("all")
    
    # Download sea water potential temperature data
    print("Downloading sea water potential temperature data...")
    thetao_files = download_data(client, get_thetao_request())
    print(f"Downloaded thetao files: {thetao_files}")
    
    # Download sea surface temperature data
    print("\nDownloading sea surface temperature data...")
    tos_files = download_data(client, get_tos_request())
    print(f"Downloaded tos files: {tos_files}")
    
    # Print summary
    all_files = thetao_files + tos_files
    print(f"\nTotal files downloaded: {len(all_files)}")
    for i, file in enumerate(all_files, 1):
        print(f"{i}. {file}")

if __name__ == "__main__":
    main() 