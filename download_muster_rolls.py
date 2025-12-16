#!/usr/bin/env python3
"""
Download all 115 pages of USS Cobia muster rolls from NARA.
Source: https://catalog.archives.gov/id/125745304
"""

import os
import urllib.request
import time

# Output directory
OUTPUT_DIR = "/home/jmknapp/cobia/cobia_muster_rolls/full_set"

# Base URL pattern - pages are 00000 to 00114
BASE_URL = "https://s3.amazonaws.com/NARAprodstorage/lz/partnerships/32662/0001/DD00901/32662_241042/32662_241042-{:05d}.jpg"

# Number of pages
NUM_PAGES = 115

def download_page(page_num):
    """Download a single page."""
    url = BASE_URL.format(page_num)
    filename = f"page_{page_num:03d}.jpg"
    filepath = os.path.join(OUTPUT_DIR, filename)
    
    if os.path.exists(filepath):
        print(f"  {filename} already exists, skipping")
        return True
    
    try:
        print(f"  Downloading {filename}...", end=" ", flush=True)
        urllib.request.urlretrieve(url, filepath)
        print("done")
        return True
    except Exception as e:
        print(f"FAILED: {e}")
        return False

def main():
    # Create output directory if needed
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    print(f"Downloading {NUM_PAGES} muster roll pages to {OUTPUT_DIR}")
    print("=" * 60)
    
    success = 0
    failed = 0
    
    for i in range(NUM_PAGES):
        if download_page(i):
            success += 1
        else:
            failed += 1
        
        # Small delay to be polite to the server
        time.sleep(0.2)
    
    print("=" * 60)
    print(f"Complete: {success} downloaded, {failed} failed")

if __name__ == "__main__":
    main()



