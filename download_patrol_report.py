#!/usr/bin/env python3
"""Download all 45 pages of USS Cobia's 5th War Patrol Report from National Archives."""

import urllib.request
import os
import time

# Base URL pattern discovered from the NARA catalog page
# First image: https://s3.amazonaws.com/NARAprodstorage/lz/microfilm-publications/WWII_WarDiaries/0003/200279/A_1751/A_1751/images/0739.jpg

base_url = "https://s3.amazonaws.com/NARAprodstorage/lz/microfilm-publications/WWII_WarDiaries/0003/200279/A_1751/A_1751/images/"

output_dir = "patrol_report_5th"
os.makedirs(output_dir, exist_ok=True)

# The images appear to start at 0739 and go for 45 pages
start_num = 739
total_pages = 45

print(f"Downloading {total_pages} pages of USS Cobia 5th War Patrol Report...")

for i in range(total_pages):
    img_num = start_num + i
    url = f"{base_url}{img_num:04d}.jpg"
    output_file = os.path.join(output_dir, f"page_{i+1:02d}_{img_num:04d}.jpg")
    
    if os.path.exists(output_file):
        print(f"  Page {i+1}: already exists, skipping")
        continue
    
    try:
        print(f"  Page {i+1}: downloading {img_num:04d}.jpg...", end=" ")
        urllib.request.urlretrieve(url, output_file)
        size_kb = os.path.getsize(output_file) / 1024
        print(f"OK ({size_kb:.0f} KB)")
        time.sleep(0.5)  # Be nice to the server
    except Exception as e:
        print(f"FAILED: {e}")

print("Done!")
print(f"Files saved to: {output_dir}/")
