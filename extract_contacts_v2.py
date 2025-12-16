#!/usr/bin/env python3
"""
Extract ship and aircraft contacts with better position parsing.
"""

import json
import re
import csv
import os

REPORTS_DIR = "/home/jmknapp/cobia/patrolReports"

PATROLS = [
    (1, "USS_Cobia_1st_Patrol_Report", 1944),
    (2, "USS_Cobia_2nd_Patrol_Report", 1944),
    (3, "USS_Cobia_3rd_Patrol_Report", 1945),
    (4, "USS_Cobia_4th_Patrol_Report", 1945),
    (5, "USS_Cobia_5th_Patrol_Report", 1945),
    (6, "USS_Cobia_6th_Patrol_Report", 1945),
]

def parse_lat_lon(text):
    """Extract lat/lon from text like '27-18N' '141-32E' or '27-18' '141-32'."""
    # Look for patterns like 27-18N or 27-18 followed by 141-32E or 141-32
    pos_pattern = re.compile(r'(\d{1,2})-(\d{2})([NS]?).*?(\d{2,3})-(\d{2})([EW]?)')
    match = pos_pattern.search(text)
    if match:
        lat_deg = int(match.group(1))
        lat_min = int(match.group(2))
        lat_dir = match.group(3) or 'N'
        lon_deg = int(match.group(4))
        lon_min = int(match.group(5))
        lon_dir = match.group(6) or 'E'
        
        lat = lat_deg + lat_min / 60
        if lat_dir == 'S':
            lat = -lat
        
        lon = lon_deg + lon_min / 60
        if lon_dir == 'W':
            lon = -lon
        
        # Validate for Pacific theater
        if abs(lat) <= 50 and 100 <= lon <= 180:
            return lat, lon
    return None, None

def load_ocr(report_name):
    json_path = f'{REPORTS_DIR}/{report_name}_gv_ocr.json'
    if os.path.exists(json_path):
        with open(json_path, 'r') as f:
            return json.load(f)
    return {}

def extract_all_contacts():
    all_ship = []
    all_aircraft = []
    
    for patrol_num, report_name, year in PATROLS:
        ocr = load_ocr(report_name)
        if not ocr:
            continue
        
        # Extract ship contacts
        for page_num, text in ocr.items():
            if 'SHIP' not in text.upper():
                continue
            
            lines = text.split('\n')
            for line in lines:
                # Match ship contact pattern
                match = re.match(r'^(\d{1,2})\s*[:\s]*(\d{4})\s*[:\s]*(\d{1,2}/\d{1,2})', line.strip())
                if match:
                    lat, lon = parse_lat_lon(line)
                    
                    # Ship type
                    ship_type = ''
                    for st in ['AK', 'DD', 'DE', 'Sampan', 'Trawler', 'Escort', 'Patrol', 'Sub', 'Cargo', 'Tanker']:
                        if st.lower() in line.lower():
                            ship_type = st
                            break
                    
                    all_ship.append({
                        'patrol': patrol_num,
                        'contact_no': int(match.group(1)),
                        'time': match.group(2),
                        'date_raw': match.group(3),
                        'year': year,
                        'latitude': lat,
                        'longitude': lon,
                        'type': ship_type,
                        'sunk': 'sunk' in line.lower()
                    })
        
        # Extract aircraft contacts - look for date patterns
        for page_num, text in ocr.items():
            if 'AIRCRAFT' not in text.upper():
                continue
            
            months = ['June', 'July', 'August', 'September', 'October', 'November', 'December', 
                     'January', 'February', 'March', 'April', 'May']
            
            lines = text.split('\n')
            contact_num = len([a for a in all_aircraft if a['patrol'] == patrol_num])
            
            for line in lines:
                for month in months:
                    if month in line:
                        date_match = re.search(r'(\d{1,2})\s+' + month, line, re.IGNORECASE)
                        if date_match:
                            contact_num += 1
                            lat, lon = parse_lat_lon(text[text.find(line):text.find(line)+200])
                            
                            # Aircraft type
                            ac_type = ''
                            for ac in ['PBM', 'PBY', 'Sally', 'Emily', 'Kate', 'Betty', 'Zero']:
                                if ac.lower() in text[text.find(line):text.find(line)+100].lower():
                                    ac_type = ac
                                    break
                            
                            all_aircraft.append({
                                'patrol': patrol_num,
                                'contact_no': contact_num,
                                'date': f"{date_match.group(1)} {month}",
                                'year': year,
                                'latitude': lat,
                                'longitude': lon,
                                'type': ac_type,
                                'friendly': ac_type in ['PBM', 'PBY']
                            })
                        break
    
    return all_ship, all_aircraft

def main():
    ships, aircraft = extract_all_contacts()
    
    # Count positions
    ships_with_pos = [s for s in ships if s['latitude']]
    aircraft_with_pos = [a for a in aircraft if a['latitude']]
    
    print(f"Ship contacts: {len(ships)} ({len(ships_with_pos)} with positions)")
    print(f"Aircraft contacts: {len(aircraft)} ({len(aircraft_with_pos)} with positions)")
    
    # Save
    with open(f'{REPORTS_DIR}/all_ship_contacts.csv', 'w', newline='') as f:
        if ships:
            writer = csv.DictWriter(f, fieldnames=ships[0].keys())
            writer.writeheader()
            writer.writerows(ships)
    
    with open(f'{REPORTS_DIR}/all_aircraft_contacts.csv', 'w', newline='') as f:
        if aircraft:
            writer = csv.DictWriter(f, fieldnames=aircraft[0].keys())
            writer.writeheader()
            writer.writerows(aircraft)
    
    print("\nSaved to CSV files")
    
    # Show sample with positions
    print("\nShip contacts with positions:")
    for s in ships_with_pos[:5]:
        print(f"  Patrol {s['patrol']} #{s['contact_no']}: {s['latitude']:.2f}, {s['longitude']:.2f} - {s['type']}")

if __name__ == "__main__":
    main()
