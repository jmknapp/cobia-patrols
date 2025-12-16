#!/usr/bin/env python3
"""Download USS Cobia decommissioning muster roll pages (May 1946)."""

import os
import urllib.request

output_dir = "cobia_muster_rolls"
os.makedirs(output_dir, exist_ok=True)

base_url = "https://s3.amazonaws.com/NARAprodstorage/lz/partnerships/32662/0001/DD00901/32662_241042/"

# Pages 109-112: May 1946 muster rolls (files 00108-00111)
pages = [
    ("00108", "page_109_May1_1946.jpg"),
    ("00109", "page_110_May22_1946_decommissioning.jpg"),
    ("00110", "page_111_May22_1946_decommissioning.jpg"),
    ("00111", "page_112_May22_1946_decommissioning.jpg"),
]

print("Downloading USS Cobia decommissioning muster rolls (May 1946)...")
print("Source: National Archives (NAID 125745304)")
print()

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

for file_num, output_name in pages:
    url = f"{base_url}32662_241042-{file_num}.jpg"
    output_file = os.path.join(output_dir, output_name)
    
    print(f"  Downloading {output_name}...", end=" ", flush=True)
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as response:
            with open(output_file, 'wb') as f:
                f.write(response.read())
        print("done")
    except Exception as e:
        print(f"FAILED: {e}")

print(f"\nDownloaded to {output_dir}/")
print("\nThese muster rolls list every sailor aboard on decommissioning day (May 22, 1946).")
