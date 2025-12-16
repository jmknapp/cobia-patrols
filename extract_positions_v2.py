#!/usr/bin/env python3
"""
Extract lat/lon positions from USS Cobia patrol reports - Version 2
Handles both "Noon Position" format and tabular contact formats.
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

# More flexible coordinate patterns
LAT_PATTERN = re.compile(r'(\d{1,3})[°\-](\d{1,2})[\'"]?\s*([NS])', re.IGNORECASE)
LON_PATTERN = re.compile(r'(\d{1,3})[°\-](\d{1,2})[\'"]?\s*([EW])', re.IGNORECASE)

# Combined pattern for "Lat. XX-XXN Long. YY-YYE" on same line
COMBINED_PATTERN = re.compile(
    r'Lat\.?\s*(\d{1,3})[°\-](\d{1,2})[\'"]?\s*([NS])\s*Long\.?\s*(\d{1,3})[°\-](\d{1,2})[\'"]?\s*([EW])',
    re.IGNORECASE
)

DATE_PATTERN = re.compile(
    r'(\d{1,2})\s*(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Oct|Nov|Dec)',
    re.IGNORECASE
)
DATE_PATTERN2 = re.compile(
    r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),?\s*(\d{4})?',
    re.IGNORECASE
)

def parse_coord(degrees, minutes, direction):
    """Convert degrees-minutes to decimal degrees."""
    try:
        deg = int(degrees)
        min_val = int(minutes)
        # Sanity check
        if deg > 180 or min_val > 59:
            return None, f"Invalid: {deg}-{min_val}{direction}"
        decimal = deg + min_val / 60.0
        if direction.upper() in ['S', 'W']:
            decimal = -decimal
        return round(decimal, 4), None
    except:
        return None, "Parse error"

def validate_position(lat, lon):
    """Check if position is sensible for WWII Pacific theater."""
    issues = []
    if lat is not None:
        if abs(lat) > 60:
            issues.append(f"Lat {lat} too extreme")
    if lon is not None:
        # Most Pacific ops: 100E to 180E, or US west coast
        if not ((lon >= 90 and lon <= 180) or (lon >= -180 and lon <= -100)):
            issues.append(f"Lon {lon} unusual")
    return issues

def extract_from_page(text, patrol_num, page_num):
    """Extract positions from a single page."""
    positions = []
    lines = text.split('\n')
    
    current_date = None
    
    # First try combined pattern (Noon Position style)
    for i, line in enumerate(lines):
        # Update date context
        dm = DATE_PATTERN2.search(line)
        if dm:
            month, day, year = dm.groups()
            current_date = f"{month} {day}" + (f", {year}" if year else "")
        
        # Look for combined lat/lon
        cm = COMBINED_PATTERN.search(line)
        if cm:
            lat_deg, lat_min, lat_dir, lon_deg, lon_min, lon_dir = cm.groups()
            lat, lat_err = parse_coord(lat_deg, lat_min, lat_dir)
            lon, lon_err = parse_coord(lon_deg, lon_min, lon_dir)
            
            pos_type = "Noon" if "noon" in line.lower() else "Position"
            issues = validate_position(lat, lon)
            if lat_err: issues.append(lat_err)
            if lon_err: issues.append(lon_err)
            
            positions.append({
                'patrol': patrol_num,
                'page': page_num,
                'date': current_date or "",
                'type': pos_type,
                'latitude': lat,
                'longitude': lon,
                'lat_raw': f"{lat_deg}-{lat_min}{lat_dir}",
                'lon_raw': f"{lon_deg}-{lon_min}{lon_dir}",
                'issues': '; '.join(issues)
            })
    
    # Also look for table-style: separate lat and lon values
    # Find lines with "Position" or coordinate headers
    lat_values = []
    lon_values = []
    
    for i, line in enumerate(lines):
        # Check for date in table format (e.g., "7 July")
        dm = DATE_PATTERN.search(line)
        if dm and len(line.strip()) < 20:
            day, month = dm.groups()
            current_date = f"{day} {month}"
        
        # Look for standalone coordinates
        lat_matches = LAT_PATTERN.findall(line)
        lon_matches = LON_PATTERN.findall(line)
        
        # If line has "Lat" header or multiple lat values
        if 'lat' in line.lower() and lat_matches:
            for m in lat_matches:
                lat_values.append((m, current_date, i))
        
        # If line has "Long" header or multiple lon values
        if 'long' in line.lower() and lon_matches:
            for m in lon_matches:
                lon_values.append((m, current_date, i))
    
    # Try to pair lat/lon values that are close together in line numbers
    for lat_data, lat_date, lat_line in lat_values:
        lat_deg, lat_min, lat_dir = lat_data
        lat, lat_err = parse_coord(lat_deg, lat_min, lat_dir)
        
        # Find matching longitude within a few lines
        best_lon = None
        best_dist = 999
        for lon_data, lon_date, lon_line in lon_values:
            dist = abs(lon_line - lat_line)
            if dist < best_dist and dist <= 3:
                best_dist = dist
                best_lon = lon_data
        
        if best_lon and lat is not None:
            lon_deg, lon_min, lon_dir = best_lon
            lon, lon_err = parse_coord(lon_deg, lon_min, lon_dir)
            
            # Avoid duplicates
            dup = False
            for p in positions:
                if p['lat_raw'] == f"{lat_deg}-{lat_min}{lat_dir}" and p['lon_raw'] == f"{lon_deg}-{lon_min}{lon_dir}":
                    dup = True
                    break
            
            if not dup and lon is not None:
                issues = validate_position(lat, lon)
                if lat_err: issues.append(lat_err)
                if lon_err: issues.append(lon_err)
                
                positions.append({
                    'patrol': patrol_num,
                    'page': page_num,
                    'date': lat_date or "",
                    'type': "Contact",
                    'latitude': lat,
                    'longitude': lon,
                    'lat_raw': f"{lat_deg}-{lat_min}{lat_dir}",
                    'lon_raw': f"{lon_deg}-{lon_min}{lon_dir}",
                    'issues': '; '.join(issues)
                })
    
    return positions

def main():
    all_positions = []
    
    print("Extracting positions from patrol reports (v2)...")
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
        
        # Count by type
        noon_count = len([p for p in patrol_positions if p['type'] == 'Noon'])
        contact_count = len([p for p in patrol_positions if p['type'] == 'Contact'])
        other_count = len(patrol_positions) - noon_count - contact_count
        
        print(f"  Patrol {patrol_num}: {len(patrol_positions)} positions (Noon: {noon_count}, Contact: {contact_count}, Other: {other_count})")
        all_positions.extend(patrol_positions)
    
    # Sort
    all_positions.sort(key=lambda x: (x['patrol'], x['page']))
    
    # Write CSV
    csv_path = os.path.join(REPORTS_DIR, "cobia_positions_v2.csv")
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
    
    # Summary by patrol
    print("\nBy patrol:")
    for patrol_num in range(1, 7):
        patrol_pos = [p for p in all_positions if p['patrol'] == patrol_num]
        print(f"  Patrol {patrol_num}: {len(patrol_pos)} positions")
    
    # Issues
    issues = [p for p in all_positions if p['issues']]
    if issues:
        print(f"\nPositions with issues: {len(issues)}")
        for p in issues[:5]:
            print(f"  Patrol {p['patrol']}, p{p['page']}: {p['lat_raw']}/{p['lon_raw']} - {p['issues']}")

if __name__ == "__main__":
    main()
