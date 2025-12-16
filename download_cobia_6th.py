#!/usr/bin/env python3
"""Download USS Cobia 6th War Patrol Report images."""

import os
import urllib.request
import time

output_dir = "cobia_6th_patrol_report"
os.makedirs(output_dir, exist_ok=True)

base_url = "https://s3.amazonaws.com/NARAprodstorage/lz/microfilm-publications/WWII_WarDiaries/0002/A_1852/A_1852/images/"

total_pages = 26
start_num = 555

print(f"Downloading {total_pages} pages of USS Cobia 6th War Patrol Report...")
print(f"Source: National Archives (NAID 83564995)")
print()

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

for page in range(1, total_pages + 1):
    img_num = start_num + page - 1
    filename = f"0{img_num}.jpg"
    url = base_url + filename
    output_file = os.path.join(output_dir, f"page_{page:02d}.jpg")
    
    if os.path.exists(output_file):
        print(f"  Page {page}/{total_pages}: already exists, skipping")
        continue
    
    print(f"  Page {page}/{total_pages}: downloading {filename}...", end=" ", flush=True)
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as response:
            with open(output_file, 'wb') as f:
                f.write(response.read())
        print("done")
        time.sleep(0.3)
    except Exception as e:
        print(f"FAILED: {e}")

downloaded = len([f for f in os.listdir(output_dir) if f.endswith('.jpg')])
print(f"\nDownloaded {downloaded} of {total_pages} pages to {output_dir}/")
