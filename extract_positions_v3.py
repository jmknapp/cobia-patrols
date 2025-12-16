#!/usr/bin/env python3
"""
Extract lat/lon positions from USS Cobia patrol reports - Version 3
Handles multiple formats:
- "Lat. XX-XXN Long. YY-YYE" 
- "Position: XX-XX.X S YYY-YY E"
- Table formats
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

# Pattern 1: "Lat. XX-XXN Long. YY-YYE" (attached direction)
PATTERN1 = re.compile(
    r'Lat\.?\s*(\d{1,3})[°\-](\d{1,2})[\'"]?\s*([NS])\s*Long\.?\s*(\d{1,3})[°\-](\d{1,2})[\'"]?\s*([EW])',
    re.IGNORECASE
)

# Pattern 2: "Position: XX-XX.X S YYY-YY.X E" (space before direction, decimal minutes)
PATTERN2 = re.compile(
    r'Position[:\s]+(\d{1,3})[°\-](\d{1,2}(?:\.\d)?)\s*([NS])\s+(\d{1,3})[°\-](\d{1,2}(?:\.\d)?)\s*([EW])',
    re.IGNORECASE
)

# Pattern 3: Just coordinate pairs like "28-24N" and "148-32E" on nearby lines
LAT_ALONE = re.compile(r'(\d{1,3})[°\-](\d{1,2}(?:\.\d)?)\s*([NS])', re.IGNORECASE)
LON_ALONE = re.compile(r'(\d{1,3})[°\-](\d{1,2}(?:\.\d)?)\s*([EW])', re.IGNORECASE)

DATE_PATTERN = re.compile(
    r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),?\s*(\d{4})?',
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
        if direction.upper() in ['S', 'W']:
            decimal = -decimal
        return round(decimal, 4), None
    except:
        return None, "Parse error"

def validate_position(lat, lon):
    """Check if position is sensible."""
    issues = []
    if lat is not None and abs(lat) > 60:
        issues.append(f"Lat {lat} extreme")
    return issues

def extract_from_page(text, patrol_num, page_num):
    """Extract positions from a single page."""
    positions = []
    seen = set()  # Avoid duplicates
    
    lines = text.split('\n')
    current_date = None
    
    for i, line in enumerate(lines):
        # Update date
        dm = DATE_PATTERN.search(line)
        if dm:
            month, day, year = dm.groups()
            current_date = f"{month} {day}" + (f", {year}" if year else "")
        
        # Try Pattern 1
        for m in PATTERN1.finditer(line):
            lat_deg, lat_min, lat_dir, lon_deg, lon_min, lon_dir = m.groups()
            key = f"{lat_deg}-{lat_min}{lat_dir}_{lon_deg}-{lon_min}{lon_dir}"
            if key in seen:
                continue
            seen.add(key)
            
            lat, lat_err = parse_coord(lat_deg, lat_min, lat_dir)
            lon, lon_err = parse_coord(lon_deg, lon_min, lon_dir)
            issues = validate_position(lat, lon)
            if lat_err: issues.append(lat_err)
            if lon_err: issues.append(lon_err)
            
            positions.append({
                'patrol': patrol_num, 'page': page_num,
                'date': current_date or "",
                'type': "Noon" if "noon" in line.lower() else "Position",
                'latitude': lat, 'longitude': lon,
                'lat_raw': f"{lat_deg}-{lat_min}{lat_dir}",
                'lon_raw': f"{lon_deg}-{lon_min}{lon_dir}",
                'issues': '; '.join(issues)
            })
        
        # Try Pattern 2
        for m in PATTERN2.finditer(line):
            lat_deg, lat_min, lat_dir, lon_deg, lon_min, lon_dir = m.groups()
            key = f"{lat_deg}-{lat_min}{lat_dir}_{lon_deg}-{lon_min}{lon_dir}"
            if key in seen:
                continue
            seen.add(key)
            
            lat, lat_err = parse_coord(lat_deg, lat_min, lat_dir)
            lon, lon_err = parse_coord(lon_deg, lon_min, lon_dir)
            issues = validate_position(lat, lon)
            if lat_err: issues.append(lat_err)
            if lon_err: issues.append(lon_err)
            
            positions.append({
                'patrol': patrol_num, 'page': page_num,
                'date': current_date or "",
                'type': "Position",
                'latitude': lat, 'longitude': lon,
                'lat_raw': f"{lat_deg}-{lat_min}{lat_dir}",
                'lon_raw': f"{lon_deg}-{lon_min}{lon_dir}",
                'issues': '; '.join(issues)
            })
    
    # Second pass: look for standalone lat/lon pairs
    for i, line in enumerate(lines):
        lat_matches = list(LAT_ALONE.finditer(line))
        lon_matches = list(LON_ALONE.finditer(line))
        
        # If we have both on same line (but not already captured)
        if lat_matches and lon_matches:
            for lat_m in lat_matches:
                for lon_m in lon_matches:
                    lat_deg, lat_min, lat_dir = lat_m.groups()
                    lon_deg, lon_min, lon_dir = lon_m.groups()
                    key = f"{lat_deg}-{lat_min}{lat_dir}_{lon_deg}-{lon_min}{lon_dir}"
                    if key in seen:
                        continue
                    seen.add(key)
                    
                    lat, lat_err = parse_coord(lat_deg, lat_min, lat_dir)
                    lon, lon_err = parse_coord(lon_deg, lon_min, lon_dir)
                    if lat is None or lon is None:
                        continue
                    
                    issues = validate_position(lat, lon)
                    if lat_err: issues.append(lat_err)
                    if lon_err: issues.append(lon_err)
                    
                    positions.append({
                        'patrol': patrol_num, 'page': page_num,
                        'date': "",
                        'type': "Pair",
                        'latitude': lat, 'longitude': lon,
                        'lat_raw': f"{lat_deg}-{lat_min}{lat_dir}",
                        'lon_raw': f"{lon_deg}-{lon_min}{lon_dir}",
                        'issues': '; '.join(issues)
                    })
    
    return positions

def main():
    all_positions = []
    
    print("Extracting positions from patrol reports (v3)...")
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
    
    # Issues
    issues = [p for p in all_positions if p['issues']]
    print(f"Positions with issues: {len(issues)}")
    for p in issues[:8]:
        print(f"  Patrol {p['patrol']}, p{p['page']}: {p['lat_raw']}/{p['lon_raw']} - {p['issues']}")

if __name__ == "__main__":
    main()
