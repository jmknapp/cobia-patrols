#!/usr/bin/env python3
"""
Download ETOPO bathymetry data for the South China Sea region.
Uses NOAA's ERDDAP server for reliable access.
"""

import urllib.request
import os

def download_etopo_data():
    """Download ETOPO 2022 bathymetry data for the South China Sea region."""
    
    # Region bounds (with some padding)
    lon_min, lon_max = 99, 116
    lat_min, lat_max = 1, 21
    
    # NOAA ERDDAP server - ETOPO 2022 (60 arc-second resolution)
    # This provides bathymetry/topography in NetCDF format
    base_url = "https://www.ngdc.noaa.gov/thredds/ncss/global/ETOPO2022/60s/60s_bed_elev_netcdf/ETOPO_2022_v1_60s_N90W180_bed.nc"
    
    params = {
        'var': 'z',
        'north': lat_max,
        'south': lat_min,
        'east': lon_max,
        'west': lon_min,
        'horizStride': 1,
        'accept': 'netcdf'
    }
    
    query = '&'.join([f'{k}={v}' for k, v in params.items()])
    url = f"{base_url}?{query}"
    
    output_file = os.path.join(os.path.dirname(__file__), 'south_china_sea_bathymetry.nc')
    
    print(f"Downloading ETOPO 2022 bathymetry data...")
    print(f"Region: {lon_min}°E to {lon_max}°E, {lat_min}°N to {lat_max}°N")
    print(f"URL: {url[:100]}...")
    
    try:
        urllib.request.urlretrieve(url, output_file)
        print(f"Downloaded: {output_file}")
        
        # Check file size
        size_mb = os.path.getsize(output_file) / (1024 * 1024)
        print(f"File size: {size_mb:.2f} MB")
        return output_file
        
    except Exception as e:
        print(f"ETOPO download failed: {e}")
        print("Trying alternative source (GEBCO via OPeNDAP)...")
        return download_gebco_alternative()


def download_gebco_alternative():
    """Alternative: Download from GEBCO's OPeNDAP server."""
    
    # GEBCO 2023 via BODC OPeNDAP
    lon_min, lon_max = 99, 116  
    lat_min, lat_max = 1, 21
    
    # GEBCO 2023 grid - subset via OPeNDAP
    # The GEBCO grid is at 15 arc-second resolution
    base_url = "https://www.bodc.ac.uk/data/open_download/gebco/gebco_2023_sub_ice_topo/zip/"
    
    print("Note: GEBCO full download requires manual access from https://download.gebco.net/")
    print("Attempting alternative bathymetry source...")
    
    # Try NOAA Coastwatch ERDDAP for bathymetry
    erddap_url = (
        "https://coastwatch.pfeg.noaa.gov/erddap/griddap/usgsCeSrtm30v6.nc?"
        f"topo[({lat_min}):1:({lat_max})][({lon_min}):1:({lon_max})]"
    )
    
    output_file = os.path.join(os.path.dirname(__file__), 'south_china_sea_bathymetry.nc')
    
    try:
        print(f"Trying SRTM30+ from ERDDAP...")
        urllib.request.urlretrieve(erddap_url, output_file)
        print(f"Downloaded: {output_file}")
        size_mb = os.path.getsize(output_file) / (1024 * 1024)
        print(f"File size: {size_mb:.2f} MB")
        return output_file
    except Exception as e:
        print(f"Alternative download also failed: {e}")
        return None


if __name__ == '__main__':
    download_etopo_data()








