#!/usr/bin/env python3
"""
Extract lat/lon positions from USS Cobia patrol reports - Version 5
Handles multi-line formats where lat and lon are on separate lines.
"""

import os
import re
import json
import csv

REPORTS_DIR = "/home/jmknapp/cobia/patrolReports"

PATROLS = [
    ("USS_Cobia_1st_Patrol_Report", 1),
    ("USS_Cobia_2nd_Patrol_Report", 2),
    ("USS_Cobia_3rd_Patrol_Report", 3),
    ("USS_Cobia_4th_Patrol_Report", 4),
    ("USS_Cobia_5th_Patrol_Report", 5),
    ("USS_Cobia_6th_Patrol_Report", 6),
]

# Pattern for lat/lon on same line
SAME_LINE = re.compile(
    r'(?:Lat\.?\s*)?(\d{1,3})[°\-](\d{1,2}(?:\.\d)?)\s*([NS])\s*(?:Long\.?\s*)?(\d{1,3})[°\-](\d{1,2}(?:\.\d)?)\s*([EW])',
    re.IGNORECASE
)

# Position format with S/E
POSITION_FMT = re.compile(
    r'Position[:\s]+(\d{1,3})[°\-](\d{1,2}(?:\.\d)?)\s*([NS])\s+(\d{1,3})[°\-](\d{1,2}(?:\.\d)?)\s*([EW])',
    re.IGNORECASE
)

# Standalone latitude (with N/S attached or space before)
LAT_PATTERN = re.compile(r'(\d{1,2})[°\-](\d{1,2})\s*([NS])(?:\s|[^0-9EW]|$)', re.IGNORECASE)

# Standalone longitude (3 digits often, E/W attached or implied)
LON_PATTERN = re.compile(r'(\d{2,3})[°\-](\d{1,2})(?:\s*([EW]))?(?:[:\s]|$)', re.IGNORECASE)

DATE_PATTERN = re.compile(
    r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2})',
    re.IGNORECASE
)

def parse_coord(degrees, minutes, direction, is_lon=False):
    try:
        deg = int(degrees)
        min_val = float(minutes)
        if min_val > 59.9:
            return None
        if is_lon and (deg < 100 or deg > 180):
            return None  # Pacific longitudes are 100-180 E
        if not is_lon and deg > 60:
            return None
        decimal = deg + min_val / 60.0
        if direction and direction.upper() in ['S', 'W']:
            decimal = -decimal
        return round(decimal, 4)
    except:
        return None

def extract_from_page(text, patrol_num, page_num):
    positions = []
    seen = set()
    lines = text.split('\n')
    current_date = None
    
    # First pass: same-line patterns
    for line in lines:
        dm = DATE_PATTERN.search(line)
        if dm:
            current_date = f"{dm.group(1)} {dm.group(2)}"
        
        # Position format
        for m in POSITION_FMT.finditer(line):
            lat_deg, lat_min, lat_dir, lon_deg, lon_min, lon_dir = m.groups()
            key = f"{lat_deg}-{lat_min}{lat_dir}_{lon_deg}-{lon_min}{lon_dir}"
            if key not in seen:
                seen.add(key)
                lat = parse_coord(lat_deg, lat_min, lat_dir)
                lon = parse_coord(lon_deg, lon_min, lon_dir, is_lon=True)
                if lat and lon:
                    positions.append({
                        'patrol': patrol_num, 'page': page_num,
                        'date': current_date or "",
                        'type': "Position",
                        'latitude': lat, 'longitude': lon,
                        'lat_raw': f"{lat_deg}-{lat_min}{lat_dir}",
                        'lon_raw': f"{lon_deg}-{lon_min}{lon_dir}",
                        'issues': ''
                    })
        
        # Same line lat/lon
        for m in SAME_LINE.finditer(line):
            lat_deg, lat_min, lat_dir, lon_deg, lon_min, lon_dir = m.groups()
            key = f"{lat_deg}-{lat_min}{lat_dir}_{lon_deg}-{lon_min}{lon_dir}"
            if key not in seen:
                seen.add(key)
                lat = parse_coord(lat_deg, lat_min, lat_dir)
                lon = parse_coord(lon_deg, lon_min, lon_dir, is_lon=True)
                if lat and lon:
                    positions.append({
                        'patrol': patrol_num, 'page': page_num,
                        'date': current_date or "",
                        'type': "Noon" if "noon" in line.lower() else "Position",
                        'latitude': lat, 'longitude': lon,
                        'lat_raw': f"{lat_deg}-{lat_min}{lat_dir}",
                        'lon_raw': f"{lon_deg}-{lon_min}{lon_dir}",
                        'issues': ''
                    })
    
    # Second pass: multi-line (lat on one line, lon on next)
    for i, line in enumerate(lines):
        lat_match = LAT_PATTERN.search(line)
        if lat_match:
            lat_deg, lat_min, lat_dir = lat_match.groups()
            
            # Look for longitude in next few lines
            for j in range(i, min(i+3, len(lines))):
                lon_match = LON_PATTERN.search(lines[j])
                if lon_match:
                    lon_deg, lon_min, lon_dir = lon_match.groups()
                    lon_dir = lon_dir or 'E'
                    
                    key = f"{lat_deg}-{lat_min}{lat_dir}_{lon_deg}-{lon_min}{lon_dir}"
                    if key not in seen:
                        lat = parse_coord(lat_deg, lat_min, lat_dir)
                        lon = parse_coord(lon_deg, lon_min, lon_dir, is_lon=True)
                        if lat and lon:
                            seen.add(key)
                            positions.append({
                                'patrol': patrol_num, 'page': page_num,
                                'date': current_date or "",
                                'type': "Contact",
                                'latitude': lat, 'longitude': lon,
                                'lat_raw': f"{lat_deg}-{lat_min}{lat_dir}",
                                'lon_raw': f"{lon_deg}-{lon_min}{lon_dir}",
                                'issues': 'Multi-line'
                            })
                    break  # Found a match, move on
    
    return positions

def main():
    all_positions = []
    
    print("Extracting positions from patrol reports (v5)...")
    print("=" * 60)
    
    for report_name, patrol_num in PATROLS:
        json_path = os.path.join(REPORTS_DIR, f"{report_name}_gv_ocr.json")
        
        if not os.path.exists(json_path):
            print(f"  Patrol {patrol_num}: OCR file not found")
            continue
        
        with open(json_path, 'r', encoding='utf-8') as f:
            ocr_data = json.load(f)
        
        patrol_positions = []
        for page_str, text in ocr_data.items():
            page_num = int(page_str)
            positions = extract_from_page(text, patrol_num, page_num)
            patrol_positions.extend(positions)
        
        print(f"  Patrol {patrol_num}: {len(patrol_positions)} positions")
        all_positions.extend(patrol_positions)
    
    # Sort and deduplicate
    all_positions.sort(key=lambda x: (x['patrol'], x['page']))
    
    # Write CSV
    csv_path = os.path.join(REPORTS_DIR, "cobia_positions.csv")
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'patrol', 'page', 'date', 'type',
            'latitude', 'longitude', 
            'lat_raw', 'lon_raw', 'issues'
        ])
        writer.writeheader()
        writer.writerows(all_positions)
    
    print(f"\n{'=' * 60}")
    print(f"Total positions: {len(all_positions)}")
    print(f"CSV saved: {csv_path}")
    
    print("\nBy patrol:")
    for pn in range(1, 7):
        cnt = len([p for p in all_positions if p['patrol'] == pn])
        print(f"  Patrol {pn}: {cnt} positions")

if __name__ == "__main__":
    main()
