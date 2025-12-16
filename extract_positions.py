#!/usr/bin/env python3
"""
Extract lat/lon positions from USS Cobia patrol reports.
Creates a CSV with patrol, date, time, latitude, longitude.
"""

import os
import re
import json
import csv
from datetime import datetime

REPORTS_DIR = "/home/jmknapp/cobia/patrolReports"

# Patrol report mappings
PATROLS = [
    ("USS_Cobia_1st_Patrol_Report", 1),
    ("USS_Cobia_2nd_Patrol_Report", 2),
    ("USS_Cobia_3rd_Patrol_Report", 3),
    ("USS_Cobia_4th_Patrol_Report", 4),
    ("USS_Cobia_5th_Patrol_Report", 5),
    ("USS_Cobia_6th_Patrol_Report", 6),
]

# Regex patterns for positions
# Examples: "Lat. 14-48N Long. 115-18E", "Lat. 8-56N Long. 108-29E"
LAT_LON_PATTERN = re.compile(
    r'Lat\.?\s*(\d+)[°\-](\d+)[\'"]?\s*([NS])\s*'
    r'Long\.?\s*(\d+)[°\-](\d+)[\'"]?\s*([EW])',
    re.IGNORECASE
)

# Pattern for dates like "May 9, 1945" or "June 26, 1944"
DATE_PATTERN = re.compile(
    r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),?\s*(\d{4})',
    re.IGNORECASE
)

# Pattern for "Noon Position"
NOON_PATTERN = re.compile(r'Noon\s+Position', re.IGNORECASE)

def parse_coord(degrees, minutes, direction):
    """Convert degrees-minutes to decimal degrees."""
    try:
        deg = int(degrees)
        min = int(minutes)
        decimal = deg + min / 60.0
        if direction.upper() in ['S', 'W']:
            decimal = -decimal
        return round(decimal, 4)
    except:
        return None

def validate_position(lat, lon, patrol_num):
    """Check if position is sensible for Pacific WWII submarine patrol."""
    issues = []
    
    # USS Cobia operated in Pacific theater
    # Reasonable bounds: Lat -10 to 40, Lon 100 to 180 (or -180 to -120 for east Pacific)
    
    if lat is not None:
        if lat < -20 or lat > 50:
            issues.append(f"Latitude {lat} out of expected range")
    
    if lon is not None:
        # Pacific theater: mostly 100E to 180E, or west coast US area
        if not ((lon >= 100 and lon <= 180) or (lon >= -180 and lon <= -100)):
            # Could be in Indian Ocean or elsewhere
            if not (lon >= 70 and lon < 100):  # Allow for some Indian Ocean ops
                issues.append(f"Longitude {lon} unusual for Pacific theater")
    
    return issues

def extract_positions_from_text(text, patrol_num, page_num):
    """Extract position data from page text."""
    positions = []
    
    # Find all lat/lon matches
    lines = text.split('\n')
    current_date = None
    
    for i, line in enumerate(lines):
        # Check for date
        date_match = DATE_PATTERN.search(line)
        if date_match:
            month, day, year = date_match.groups()
            try:
                current_date = f"{month} {day}, {year}"
            except:
                pass
        
        # Check for position
        pos_match = LAT_LON_PATTERN.search(line)
        if pos_match:
            lat_deg, lat_min, lat_dir, lon_deg, lon_min, lon_dir = pos_match.groups()
            
            lat = parse_coord(lat_deg, lat_min, lat_dir)
            lon = parse_coord(lon_deg, lon_min, lon_dir)
            
            # Determine time (usually "Noon Position")
            time = "Noon" if NOON_PATTERN.search(line) else "Unknown"
            
            # Look for time in previous lines if current line doesn't have "Noon"
            if time == "Unknown" and i > 0:
                prev_line = lines[i-1] if i > 0 else ""
                if NOON_PATTERN.search(prev_line):
                    time = "Noon"
            
            # Validate
            issues = validate_position(lat, lon, patrol_num)
            
            positions.append({
                'patrol': patrol_num,
                'page': page_num,
                'date': current_date or "Unknown",
                'time': time,
                'latitude': lat,
                'longitude': lon,
                'lat_raw': f"{lat_deg}-{lat_min}{lat_dir}",
                'lon_raw': f"{lon_deg}-{lon_min}{lon_dir}",
                'issues': '; '.join(issues) if issues else ''
            })
    
    return positions

def main():
    all_positions = []
    
    print("Extracting positions from patrol reports...")
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
            positions = extract_positions_from_text(text, patrol_num, page_num)
            patrol_positions.extend(positions)
        
        print(f"  Patrol {patrol_num}: {len(patrol_positions)} positions found")
        all_positions.extend(patrol_positions)
    
    # Sort by patrol and date
    all_positions.sort(key=lambda x: (x['patrol'], x['page']))
    
    # Write CSV
    csv_path = os.path.join(REPORTS_DIR, "cobia_positions.csv")
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'patrol', 'page', 'date', 'time', 
            'latitude', 'longitude', 
            'lat_raw', 'lon_raw', 'issues'
        ])
        writer.writeheader()
        writer.writerows(all_positions)
    
    print(f"\n{'=' * 60}")
    print(f"Total positions: {len(all_positions)}")
    print(f"CSV saved: {csv_path}")
    
    # Summary of issues
    issues = [p for p in all_positions if p['issues']]
    if issues:
        print(f"\nPositions with potential issues: {len(issues)}")
        for p in issues[:10]:
            print(f"  Patrol {p['patrol']}, {p['date']}: {p['lat_raw']} / {p['lon_raw']} - {p['issues']}")
        if len(issues) > 10:
            print(f"  ... and {len(issues) - 10} more")
    else:
        print("\nNo obvious issues found!")

if __name__ == "__main__":
    main()
