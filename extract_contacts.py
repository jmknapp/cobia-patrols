#!/usr/bin/env python3
"""
Extract ship and aircraft contacts from USS Cobia patrol reports.
"""

import json
import re
import csv
import os

REPORTS_DIR = "/home/jmknapp/cobia/patrolReports"

def extract_patrol1_contacts():
    """Extract contacts from 1st Patrol Report."""
    
    with open(f'{REPORTS_DIR}/USS_Cobia_1st_Patrol_Report_gv_ocr.json') as f:
        ocr = json.load(f)
    
    # Ship contacts from page 21
    ship_contacts = []
    page21 = ocr.get('21', '')
    
    # Pattern: contact#, time, date, then position and type info
    lines = page21.split('\n')
    ship_pattern = re.compile(r'^(\d{1,2})\s*[:\s]*(\d{4})\s*[:\s]*(\d{1,2}/\d{1,2})')
    
    for line in lines:
        match = ship_pattern.match(line.strip())
        if match:
            # Extract position if present
            pos_match = re.search(r'(\d{1,2}-\d{2})\s*[:\s]*(\d{2,3}-\d{2})', line)
            lat, lon = '', ''
            if pos_match:
                lat, lon = pos_match.groups()
            
            # Extract type - look for common ship types
            type_keywords = ['AK', 'DD', 'Sub', 'Sampan', 'Trawler', 'Escort', 'Patrol', 
                           'Cargo', 'Vessel', 'Mast', 'Periscope', 'AF']
            ship_type = ''
            for kw in type_keywords:
                if kw.lower() in line.lower():
                    ship_type = kw
                    break
            
            # Check for sunk
            sunk = 'Sunk' in line
            
            ship_contacts.append({
                'patrol': 1,
                'contact_no': match.group(1),
                'time': match.group(2),
                'date': f"1944-07-{match.group(3).split('/')[1].zfill(2)}" if '7/' in match.group(3) else f"1944-08-{match.group(3).split('/')[1].zfill(2)}",
                'date_raw': match.group(3),
                'latitude': lat,
                'longitude': lon,
                'type': ship_type,
                'sunk': sunk,
                'raw': line.strip()[:100]
            })
    
    # Aircraft contacts from pages 22-28
    aircraft_contacts = []
    
    for page_num in range(22, 29):
        page_text = ocr.get(str(page_num), '')
        lines = page_text.split('\n')
        
        # Look for contact number lines (numbers 1-32 followed by date)
        contact_pattern = re.compile(r'^(\d{1,2})\s+(\d{1,2})\s+(June|July|August)')
        
        for i, line in enumerate(lines):
            # Also check for date in format "7 July" etc
            date_match = re.search(r'(\d{1,2})\s+(June|July|August)', line, re.IGNORECASE)
            if date_match and re.match(r'^\d{1,2}\s', line.strip()):
                parts = line.strip().split()
                if len(parts) >= 3 and parts[0].isdigit():
                    contact_no = parts[0]
                    
                    # Get time from next column
                    time_match = re.search(r'\d{4}', line)
                    time = time_match.group() if time_match else ''
                    
                    # Get position
                    pos_match = re.search(r'(\d{1,2}-\d{2}[NS]?)\s*(\d{2,3}-\d{2}[EW]?)', page_text[page_text.find(line):page_text.find(line)+200])
                    lat, lon = '', ''
                    if pos_match:
                        lat, lon = pos_match.groups()
                    
                    # Get aircraft type
                    ac_types = ['PBM', 'PBY', 'Sally', 'Emily', 'Kate', 'Betty', 'Nell', 'Mavis', 'Zero']
                    ac_type = ''
                    for ac in ac_types:
                        if ac.lower() in page_text[page_text.find(line):page_text.find(line)+300].lower():
                            ac_type = ac
                            break
                    
                    aircraft_contacts.append({
                        'patrol': 1,
                        'contact_no': contact_no,
                        'page': page_num,
                        'date': f"{date_match.group(1)} {date_match.group(2)} 1944",
                        'time': time,
                        'latitude': lat,
                        'longitude': lon,
                        'type': ac_type,
                        'raw': line.strip()[:80]
                    })
    
    return ship_contacts, aircraft_contacts

def main():
    print("Extracting contacts from Patrol Report #1...")
    print("=" * 60)
    
    ship_contacts, aircraft_contacts = extract_patrol1_contacts()
    
    print(f"\nShip Contacts: {len(ship_contacts)}")
    print("-" * 40)
    for c in ship_contacts[:10]:
        sunk_mark = " [SUNK]" if c['sunk'] else ""
        print(f"  #{c['contact_no']:2s} {c['date_raw']:5s} {c['time']} - {c['type']}{sunk_mark}")
    if len(ship_contacts) > 10:
        print(f"  ... and {len(ship_contacts) - 10} more")
    
    print(f"\nAircraft Contacts: {len(aircraft_contacts)}")
    print("-" * 40)
    for c in aircraft_contacts[:10]:
        print(f"  #{c['contact_no']:2s} {c['date']:15s} {c['time']} - {c['type']}")
    if len(aircraft_contacts) > 10:
        print(f"  ... and {len(aircraft_contacts) - 10} more")
    
    # Save to CSV
    ship_csv = f'{REPORTS_DIR}/patrol1_ship_contacts.csv'
    with open(ship_csv, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['patrol', 'contact_no', 'time', 'date', 'date_raw', 
                                                'latitude', 'longitude', 'type', 'sunk', 'raw'])
        writer.writeheader()
        writer.writerows(ship_contacts)
    print(f"\nSaved: {ship_csv}")
    
    aircraft_csv = f'{REPORTS_DIR}/patrol1_aircraft_contacts.csv'
    with open(aircraft_csv, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['patrol', 'contact_no', 'page', 'date', 'time',
                                                'latitude', 'longitude', 'type', 'raw'])
        writer.writeheader()
        writer.writerows(aircraft_contacts)
    print(f"Saved: {aircraft_csv}")

if __name__ == "__main__":
    main()
