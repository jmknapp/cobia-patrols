#!/usr/bin/env python3
"""
Parse contact tables from all USS Cobia patrol reports.
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

def load_ocr(report_name):
    path = f'{REPORTS_DIR}/{report_name}_gv_ocr.json'
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {}

def find_ship_contact_pages(ocr):
    """Find pages that contain ship contact tables."""
    pages = []
    for page_num, text in ocr.items():
        if 'SHIP' in text.upper() and 'CONTACT' in text.upper():
            pages.append(int(page_num))
    return sorted(pages)

def find_aircraft_contact_pages(ocr):
    """Find pages that contain aircraft contact tables."""
    pages = []
    for page_num, text in ocr.items():
        if 'AIRCRAFT' in text.upper() and ('CONTACT' in text.upper() or 'Date' in text):
            pages.append(int(page_num))
    return sorted(pages)

def parse_ship_contacts(ocr, patrol_num, year):
    """Parse ship contacts from all relevant pages."""
    contacts = []
    pages = find_ship_contact_pages(ocr)
    
    contact_pattern = re.compile(r'^(\d{1,2})\s*[:\s]*(\d{4})\s*[:\s]*(\d{1,2}/\d{1,2})')
    
    for page_num in pages:
        text = ocr.get(str(page_num), '')
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            match = contact_pattern.match(line.strip())
            if match:
                contact_no = int(match.group(1))
                time = match.group(2)
                date = match.group(3)
                
                # Search nearby for coordinates
                search_text = '\n'.join(lines[i:min(len(lines), i+4)])
                
                # Latitude: 1-2 digits - 2 digits
                lat_match = re.search(r'[:\s](\d{1,2})-(\d{2})', search_text)
                # Longitude: 3 digits - 2 digits  
                lon_match = re.search(r'(\d{3})-(\d{2})', search_text)
                
                lat = lon = None
                if lat_match:
                    lat_deg = int(lat_match.group(1))
                    lat_min = int(lat_match.group(2))
                    if 0 <= lat_deg <= 40:
                        lat = lat_deg + lat_min / 60
                
                if lon_match:
                    lon_deg = int(lon_match.group(1))
                    lon_min = int(lon_match.group(2))
                    if 100 <= lon_deg <= 180:
                        lon = lon_deg + lon_min / 60
                
                # Ship type
                ship_type = ''
                for kw in ['Sampan', 'Trawler', 'DD', 'DE', 'Sub', 'AK', 'Escort', 
                          'Patrol', 'Cargo', 'Tanker', 'Maru', 'Junk', 'Lugger']:
                    if kw.lower() in search_text.lower():
                        ship_type = kw
                        break
                
                sunk = 'sunk' in search_text.lower()
                damaged = 'damag' in search_text.lower()
                
                contacts.append({
                    'patrol': patrol_num,
                    'contact_no': contact_no,
                    'page': page_num,
                    'time': time,
                    'date': date,
                    'year': year,
                    'latitude': lat,
                    'longitude': lon,
                    'type': ship_type,
                    'sunk': sunk,
                    'damaged': damaged
                })
    
    return contacts

def parse_aircraft_contacts(ocr, patrol_num, year):
    """Parse aircraft contacts from all relevant pages."""
    contacts = []
    pages = find_aircraft_contact_pages(ocr)
    
    months = ['January', 'February', 'March', 'April', 'May', 'June',
              'July', 'August', 'September', 'October', 'November', 'December']
    
    contact_num = 0
    for page_num in pages:
        text = ocr.get(str(page_num), '')
        
        # Find dates with month names
        date_pattern = re.compile(r'(\d{1,2})\s+(' + '|'.join(months) + ')', re.IGNORECASE)
        dates = date_pattern.findall(text)
        
        # Find positions
        pos_pattern = re.compile(r'(\d{1,2})-(\d{2})(?:\.\d)?([NS])?\s+(\d{2,3})-(\d{2})')
        positions = pos_pattern.findall(text)
        
        # Find aircraft types
        ac_types = []
        for ac in ['PBM', 'PBY', 'B-24', 'B-25', 'Sally', 'Emily', 'Kate', 'Betty', 
                   'Nell', 'Mavis', 'Zero', 'Oscar', 'Jake', 'Jill']:
            # Count occurrences
            count = len(re.findall(ac, text, re.IGNORECASE))
            ac_types.extend([ac] * count)
        
        for i, (day, month) in enumerate(dates):
            contact_num += 1
            
            lat = lon = None
            if i < len(positions):
                p = positions[i]
                lat_deg = int(p[0])
                lat_min = int(p[1])
                lat = lat_deg + lat_min / 60
                if p[2] == 'S':
                    lat = -lat
                lon_deg = int(p[3])
                lon_min = int(p[4])
                lon = lon_deg + lon_min / 60
                
                # Validate
                if lon < 100 or lon > 180:
                    lat = lon = None
            
            ac_type = ac_types[i] if i < len(ac_types) else ''
            friendly = ac_type in ['PBM', 'PBY', 'B-24', 'B-25']
            
            contacts.append({
                'patrol': patrol_num,
                'contact_no': contact_num,
                'page': page_num,
                'date': f"{day} {month}",
                'year': year,
                'latitude': lat,
                'longitude': lon,
                'type': ac_type,
                'friendly': friendly
            })
    
    return contacts

def main():
    all_ships = []
    all_aircraft = []
    
    print("Parsing contact tables from all patrol reports...")
    print("=" * 70)
    
    for patrol_num, report_name, year in PATROLS:
        ocr = load_ocr(report_name)
        if not ocr:
            continue
        
        ships = parse_ship_contacts(ocr, patrol_num, year)
        aircraft = parse_aircraft_contacts(ocr, patrol_num, year)
        
        ships_with_pos = sum(1 for s in ships if s['latitude'] and s['longitude'])
        ac_with_pos = sum(1 for a in aircraft if a['latitude'] and a['longitude'])
        
        sunk = sum(1 for s in ships if s['sunk'])
        
        print(f"Patrol {patrol_num}: {len(ships)} ships ({ships_with_pos} w/pos, {sunk} sunk), "
              f"{len(aircraft)} aircraft ({ac_with_pos} w/pos)")
        
        all_ships.extend(ships)
        all_aircraft.extend(aircraft)
    
    # Summary
    total_ships = len(all_ships)
    ships_pos = sum(1 for s in all_ships if s['latitude'] and s['longitude'])
    total_ac = len(all_aircraft)
    ac_pos = sum(1 for a in all_aircraft if a['latitude'] and a['longitude'])
    total_sunk = sum(1 for s in all_ships if s['sunk'])
    
    print("\n" + "=" * 70)
    print(f"TOTAL SHIPS: {total_ships} ({ships_pos} with positions, {total_sunk} sunk)")
    print(f"TOTAL AIRCRAFT: {total_ac} ({ac_pos} with positions)")
    
    # Save CSVs
    if all_ships:
        with open(f'{REPORTS_DIR}/all_ship_contacts.csv', 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=all_ships[0].keys())
            writer.writeheader()
            writer.writerows(all_ships)
        print(f"\nSaved: all_ship_contacts.csv")
    
    if all_aircraft:
        with open(f'{REPORTS_DIR}/all_aircraft_contacts.csv', 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=all_aircraft[0].keys())
            writer.writeheader()
            writer.writerows(all_aircraft)
        print(f"Saved: all_aircraft_contacts.csv")
    
    # Show ships with positions
    print("\n" + "=" * 70)
    print("SHIPS WITH POSITIONS:")
    print("-" * 70)
    for s in all_ships:
        if s['latitude'] and s['longitude']:
            sunk = " [SUNK]" if s['sunk'] else ""
            print(f"  P{s['patrol']} #{s['contact_no']:2d}: ({s['latitude']:6.2f}, {s['longitude']:7.2f}) {s['type']}{sunk}")

if __name__ == "__main__":
    main()
