#!/usr/bin/env python3
"""
Extract lat/lon positions from USS Cobia patrol reports - Version 4
Handles all observed formats including table formats without E/W suffix.
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

# Pattern 1: "Lat. XX-XXN Long. YY-YYE"
PATTERN1 = re.compile(
    r'Lat\.?\s*(\d{1,3})[°\-](\d{1,2})[\'"]?\s*([NS])\s*Long\.?\s*(\d{1,3})[°\-](\d{1,2})[\'"]?\s*([EW])',
    re.IGNORECASE
)

# Pattern 2: "Position: XX-XX.X S YYY-YY.X E"
PATTERN2 = re.compile(
    r'Position[:\s]+(\d{1,3})[°\-](\d{1,2}(?:\.\d)?)\s*([NS])\s+(\d{1,3})[°\-](\d{1,2}(?:\.\d)?)\s*([EW])',
    re.IGNORECASE
)

# Pattern 3: Lat like "18-30N" followed by lon like "120-30" (no E) on same line
# This handles table formats where E is implied
PATTERN3 = re.compile(
    r'(\d{1,2})[°\-](\d{1,2})\s*([NS])[^0-9]*?(\d{2,3})[°\-](\d{1,2})(?:\s*([EW]))?',
    re.IGNORECASE
)

# Pattern 4: coordinates with space before direction "16-7 N" then "145-7"
PATTERN4 = re.compile(
    r'(\d{1,2})[°\-](\d{1,2})\s+([NS])[^0-9]*?(\d{2,3})[°\-](\d{1,2})',
    re.IGNORECASE
)

DATE_PATTERN = re.compile(
    r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2})',
    re.IGNORECASE
)

def parse_coord(degrees, minutes, direction):
    """Convert degrees-minutes to decimal degrees."""
    try:
        deg = int(degrees)
        min_val = float(minutes)
        if deg > 180 or min_val > 59.9:
            return None, f"Invalid: {deg}-{minutes}{direction}"
        decimal = deg + min_val / 60.0
        if direction and direction.upper() in ['S', 'W']:
            decimal = -decimal
        return round(decimal, 4), None
    except:
        return None, "Parse error"

def validate_position(lat, lon):
    issues = []
    if lat is not None and abs(lat) > 60:
        issues.append(f"Lat extreme")
    return issues

def extract_from_page(text, patrol_num, page_num):
    positions = []
    seen = set()
    
    lines = text.split('\n')
    current_date = None
    
    for line in lines:
        dm = DATE_PATTERN.search(line)
        if dm:
            current_date = f"{dm.group(1)} {dm.group(2)}"
        
        # Try Pattern 1
        for m in PATTERN1.finditer(line):
            lat_deg, lat_min, lat_dir, lon_deg, lon_min, lon_dir = m.groups()
            key = f"{lat_deg}-{lat_min}{lat_dir}_{lon_deg}-{lon_min}{lon_dir}"
            if key not in seen:
                seen.add(key)
                lat, _ = parse_coord(lat_deg, lat_min, lat_dir)
                lon, _ = parse_coord(lon_deg, lon_min, lon_dir)
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
        
        # Try Pattern 2
        for m in PATTERN2.finditer(line):
            lat_deg, lat_min, lat_dir, lon_deg, lon_min, lon_dir = m.groups()
            key = f"{lat_deg}-{lat_min}{lat_dir}_{lon_deg}-{lon_min}{lon_dir}"
            if key not in seen:
                seen.add(key)
                lat, _ = parse_coord(lat_deg, lat_min, lat_dir)
                lon, _ = parse_coord(lon_deg, lon_min, lon_dir)
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
        
        # Try Pattern 3 (table format with implied E)
        for m in PATTERN3.finditer(line):
            groups = m.groups()
            lat_deg, lat_min, lat_dir = groups[0], groups[1], groups[2]
            lon_deg, lon_min = groups[3], groups[4]
            lon_dir = groups[5] if len(groups) > 5 and groups[5] else 'E'  # Default to E
            
            key = f"{lat_deg}-{lat_min}{lat_dir}_{lon_deg}-{lon_min}{lon_dir}"
            if key not in seen:
                seen.add(key)
                lat, _ = parse_coord(lat_deg, lat_min, lat_dir)
                lon, _ = parse_coord(lon_deg, lon_min, lon_dir)
                if lat and lon and 100 <= abs(lon) <= 180:  # Valid Pacific longitude
                    positions.append({
                        'patrol': patrol_num, 'page': page_num,
                        'date': current_date or "",
                        'type': "Contact",
                        'latitude': lat, 'longitude': lon,
                        'lat_raw': f"{lat_deg}-{lat_min}{lat_dir}",
                        'lon_raw': f"{lon_deg}-{lon_min}{lon_dir}",
                        'issues': '' if groups[5] else 'E implied'
                    })
    
    return positions

def main():
    all_positions = []
    
    print("Extracting positions from patrol reports (v4)...")
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
    
    # Sort
    all_positions.sort(key=lambda x: (x['patrol'], x['page']))
    
    # Remove obvious duplicates and bad data
    clean = []
    for p in all_positions:
        lat, lon = p['latitude'], p['longitude']
        # Skip impossible coordinates
        if lat is None or lon is None:
            continue
        if abs(lat) > 50:  # Too extreme for Pacific ops
            continue
        clean.append(p)
    
    # Write CSV
    csv_path = os.path.join(REPORTS_DIR, "cobia_positions.csv")
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'patrol', 'page', 'date', 'type',
            'latitude', 'longitude', 
            'lat_raw', 'lon_raw', 'issues'
        ])
        writer.writeheader()
        writer.writerows(clean)
    
    print(f"\n{'=' * 60}")
    print(f"Total positions extracted: {len(all_positions)}")
    print(f"After filtering: {len(clean)}")
    print(f"CSV saved: {csv_path}")
    
    print("\nBy patrol:")
    for pn in range(1, 7):
        cnt = len([p for p in clean if p['patrol'] == pn])
        print(f"  Patrol {pn}: {cnt} positions")

if __name__ == "__main__":
    main()
