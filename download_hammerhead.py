#!/usr/bin/env python3
"""Download USS Hammerhead 4th War Patrol Report images and create searchable PDF."""

import os
import urllib.request
import time

# Create output directory
output_dir = "hammerhead_patrol_report"
os.makedirs(output_dir, exist_ok=True)

# Base URL pattern
base_url = "https://s3.amazonaws.com/NARAprodstorage/lz/microfilm-publications/M1752-US_SubWarPatrolReports_1941-194/M1752_00451-00475/images/"

total_pages = 39
print(f"Downloading {total_pages} pages of USS Hammerhead 4th War Patrol Report...")
print(f"Source: National Archives (NAID 74823150)")
print()

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

for page in range(1, total_pages + 1):
    filename = f"07{page:02d}.jpg"
    url = base_url + filename
    output_file = os.path.join(output_dir, f"page_{page:02d}.jpg")
    
    if os.path.exists(output_file):
        print(f"  Page {page}/{total_pages}: already exists, skipping")
        continue
    
    print(f"  Page {page}/{total_pages}: downloading...", end=" ", flush=True)
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as response:
            with open(output_file, 'wb') as f:
                f.write(response.read())
        print("done")
        time.sleep(0.5)  # Be polite to the server
    except Exception as e:
        print(f"FAILED: {e}")

# Verify downloads
downloaded = len([f for f in os.listdir(output_dir) if f.endswith('.jpg')])
print(f"\nDownloaded {downloaded} of {total_pages} pages to {output_dir}/")
