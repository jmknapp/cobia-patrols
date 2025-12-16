#!/usr/bin/env python3
"""
Parse multi-column contact tables from patrol report OCR.
The tables have columns for: No, Time, Date, Zone, Lat, Long, Type, Range, etc.
"""

import json
import re
import csv
from collections import defaultdict

REPORTS_DIR = "/home/jmknapp/cobia/patrolReports"

def parse_ship_contacts_patrol1(ocr):
    """Parse ship contacts from 1st Patrol Report page 21."""
    text = ocr.get('21', '')
    
    contacts = []
    
    # The data appears in a pattern where contact info is scattered
    # Let's extract all the components and then correlate them
    
    # First, find all contact number entries with time and date
    # Pattern: number, time (4 digits), date (m/d)
    contact_pattern = re.compile(r'(\d{1,2})\s*[:\s]*(\d{4})\s*[:\s]*(\d{1,2}/\d{1,2})')
    
    # Find all lat/long pairs
    # Latitude: 2 digits - 2 digits (like 27-18, 28-25, 31-39)
    # Longitude: 3 digits - 2 digits (like 141-18, 142-05, 137-27)
    latlon_pattern = re.compile(r'(\d{2})-(\d{2})[^\d]*(\d{3})-(\d{2})')
    
    lines = text.split('\n')
    
    # Extract contacts with their line positions
    contact_info = []
    for i, line in enumerate(lines):
        match = contact_pattern.match(line.strip())
        if match:
            contact_info.append({
                'line': i,
                'contact_no': int(match.group(1)),
                'time': match.group(2),
                'date': match.group(3),
                'raw_line': line
            })
    
    # Now look for lat/long near each contact
    for ci in contact_info:
        line_idx = ci['line']
        # Search in nearby lines for coordinates
        search_text = '\n'.join(lines[max(0, line_idx):min(len(lines), line_idx+3)])
        
        # Look for latitude (2 digits - 2 digits, typically 8-35 for Pacific)
        lat_match = re.search(r'[:\s](\d{1,2})-(\d{2})[NS]?\s', search_text)
        lon_match = re.search(r'(\d{3})-(\d{2})[EW]?', search_text)
        
        lat = None
        lon = None
        if lat_match:
            lat_deg = int(lat_match.group(1))
            lat_min = int(lat_match.group(2))
            if 5 <= lat_deg <= 35:  # Valid range for Pacific
                lat = lat_deg + lat_min / 60
        
        if lon_match:
            lon_deg = int(lon_match.group(1))
            lon_min = int(lon_match.group(2))
            if 100 <= lon_deg <= 180:  # Valid range for Pacific
                lon = lon_deg + lon_min / 60
        
        # Find ship type
        ship_type = ''
        type_keywords = ['Sampan', 'Trawler', 'DD', 'Sub', 'AK', 'Escort', 'Patrol', 
                        'Cargo', 'Tanker', 'Maru', 'Vessel']
        for kw in type_keywords:
            if kw.lower() in search_text.lower():
                ship_type = kw
                break
        
        # Check for sunk
        sunk = 'sunk' in search_text.lower()
        
        contacts.append({
            'patrol': 1,
            'contact_no': ci['contact_no'],
            'time': ci['time'],
            'date': ci['date'],
            'year': 1944,
            'latitude': lat,
            'longitude': lon,
            'type': ship_type,
            'sunk': sunk
        })
    
    return contacts

def parse_aircraft_contacts_patrol1(ocr):
    """Parse aircraft contacts from pages 22-28."""
    contacts = []
    
    # Aircraft contact numbers and their corresponding data
    # The table shows 5 contacts per page typically
    
    page_data = {
        22: {'contacts': range(1, 6), 'dates': ['27 June', '27 June', '30 June', '12 July', '2 July']},
        23: {'contacts': range(6, 11), 'dates': ['7 July', '8 July', '9 July', '10 July', '10 July']},
        24: {'contacts': range(11, 16), 'dates': ['10 July', '11 July', '11 July', '12 July', '12 July']},
        25: {'contacts': range(16, 21), 'dates': ['12 July', '12 July', '13 July', '13 July', '14 July']},
        26: {'contacts': range(21, 26), 'dates': ['15 July', '19 July', '26 July', '27 July', '31 July']},
        27: {'contacts': range(26, 31), 'dates': ['1 August', '5 August', '5 August', '11 August', '11 August']},
        28: {'contacts': range(31, 33), 'dates': ['13 August', '13 August']},
    }
    
    for page_num, data in page_data.items():
        text = ocr.get(str(page_num), '')
        
        # Find aircraft types
        ac_types = []
        for ac in ['PBM', 'PBY', 'Sally', 'Emily', 'Kate', 'Betty', 'Betry', 'Botty', 'Nell', 'Mavis', 'Zero']:
            if ac.lower() in text.lower():
                ac_types.append(ac)
        
        # Find positions
        pos_pattern = re.compile(r'(\d{2})-(\d{2})(?:\.\d)?([NS])?\s+(\d{2,3})-(\d{2})')
        positions = pos_pattern.findall(text)
        
        for i, contact_no in enumerate(data['contacts']):
            date = data['dates'][i] if i < len(data['dates']) else ''
            
            lat, lon = None, None
            if i < len(positions):
                p = positions[i]
                lat = int(p[0]) + int(p[1]) / 60
                if p[2] == 'S':
                    lat = -lat
                lon = int(p[3]) + int(p[4]) / 60
            
            ac_type = ac_types[i] if i < len(ac_types) else ''
            friendly = ac_type in ['PBM', 'PBY']
            
            contacts.append({
                'patrol': 1,
                'contact_no': contact_no,
                'page': page_num,
                'date': date,
                'year': 1944,
                'latitude': lat,
                'longitude': lon,
                'type': ac_type,
                'friendly': friendly
            })
    
    return contacts

def main():
    # Load OCR for Patrol 1
    with open(f'{REPORTS_DIR}/USS_Cobia_1st_Patrol_Report_gv_ocr.json') as f:
        ocr1 = json.load(f)
    
    print("Parsing Patrol 1 contact tables...")
    print("=" * 70)
    
    # Parse ship contacts
    ships = parse_ship_contacts_patrol1(ocr1)
    ships_with_pos = [s for s in ships if s['latitude'] and s['longitude']]
    
    print(f"\nSHIP CONTACTS: {len(ships)} total, {len(ships_with_pos)} with positions")
    print("-" * 50)
    for s in ships:
        pos = f"({s['latitude']:.2f}, {s['longitude']:.2f})" if s['latitude'] else "(no pos)"
        sunk = " [SUNK]" if s['sunk'] else ""
        print(f"  #{s['contact_no']:2d}  {s['date']:5s}  {s['time']}  {pos:20s}  {s['type']}{sunk}")
    
    # Parse aircraft contacts
    aircraft = parse_aircraft_contacts_patrol1(ocr1)
    ac_with_pos = [a for a in aircraft if a['latitude'] and a['longitude']]
    
    print(f"\nAIRCRAFT CONTACTS: {len(aircraft)} total, {len(ac_with_pos)} with positions")
    print("-" * 50)
    for a in aircraft[:15]:  # Show first 15
        pos = f"({a['latitude']:.2f}, {a['longitude']:.2f})" if a['latitude'] else "(no pos)"
        friendly = " (friendly)" if a['friendly'] else ""
        print(f"  #{a['contact_no']:2d}  {a['date']:12s}  {pos:20s}  {a['type']}{friendly}")
    if len(aircraft) > 15:
        print(f"  ... and {len(aircraft) - 15} more")
    
    # Save to CSV
    print("\n" + "=" * 70)
    
    with open(f'{REPORTS_DIR}/patrol1_ship_contacts_parsed.csv', 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=ships[0].keys())
        writer.writeheader()
        writer.writerows(ships)
    print(f"Saved: patrol1_ship_contacts_parsed.csv")
    
    with open(f'{REPORTS_DIR}/patrol1_aircraft_contacts_parsed.csv', 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=aircraft[0].keys())
        writer.writeheader()
        writer.writerows(aircraft)
    print(f"Saved: patrol1_aircraft_contacts_parsed.csv")

if __name__ == "__main__":
    main()
