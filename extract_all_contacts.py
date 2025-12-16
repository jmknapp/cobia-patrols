#!/usr/bin/env python3
"""
Extract ship and aircraft contacts from all USS Cobia patrol reports.
Saves to CSV and prepares data for mapping.
"""

import json
import re
import csv
import os
from collections import defaultdict

REPORTS_DIR = "/home/jmknapp/cobia/patrolReports"

# Patrol report info
PATROLS = [
    (1, "USS_Cobia_1st_Patrol_Report", 1944, "July-August"),
    (2, "USS_Cobia_2nd_Patrol_Report", 1944, "September-November"),
    (3, "USS_Cobia_3rd_Patrol_Report", 1945, "January-February"),
    (4, "USS_Cobia_4th_Patrol_Report", 1945, "March-May"),
    (5, "USS_Cobia_5th_Patrol_Report", 1945, "May-July"),
    (6, "USS_Cobia_6th_Patrol_Report", 1945, "July-August"),
]

def load_ocr(report_name):
    """Load OCR JSON for a report."""
    json_path = f'{REPORTS_DIR}/{report_name}_gv_ocr.json'
    if os.path.exists(json_path):
        with open(json_path, 'r') as f:
            return json.load(f)
    return {}

def find_contact_pages(ocr_data, contact_type="SHIP"):
    """Find pages containing contact tables."""
    pages = []
    for page_num, text in ocr_data.items():
        if contact_type.upper() in text.upper() and 'CONTACT' in text.upper():
            pages.append(int(page_num))
    return sorted(pages)

def extract_ship_contacts(ocr_data, patrol_num, year):
    """Extract ship contacts from OCR data."""
    contacts = []
    
    # Find pages with ship contacts
    for page_num, text in ocr_data.items():
        if 'SHIP' not in text.upper() or 'CONTACT' not in text.upper():
            continue
            
        lines = text.split('\n')
        
        # Pattern for ship contact lines
        ship_pattern = re.compile(r'^(\d{1,2})\s*[:\s]*(\d{4})\s*[:\s]*(\d{1,2}/\d{1,2})')
        
        for line in lines:
            match = ship_pattern.match(line.strip())
            if match:
                contact_no = match.group(1)
                time = match.group(2)
                date_raw = match.group(3)
                
                # Parse date
                month, day = date_raw.split('/')
                month_num = int(month)
                
                # Extract position
                pos_match = re.search(r'(\d{1,2}-\d{2}[NS]?)\s*[:\s]*(\d{2,3}-\d{2}[EW]?)', line)
                lat, lon = '', ''
                if pos_match:
                    lat, lon = pos_match.groups()
                
                # Extract type
                ship_types = ['AK', 'DD', 'DE', 'CV', 'BB', 'CA', 'CL', 'SS', 'Sub', 
                             'Sampan', 'Trawler', 'Escort', 'Patrol', 'Cargo', 
                             'Tanker', 'Transport', 'Maru', 'Vessel', 'Destroyer']
                ship_type = ''
                for st in ship_types:
                    if st.lower() in line.lower():
                        ship_type = st
                        break
                
                # Check for sunk/damaged
                sunk = 'sunk' in line.lower()
                damaged = 'damag' in line.lower()
                
                contacts.append({
                    'patrol': patrol_num,
                    'contact_no': int(contact_no),
                    'page': int(page_num),
                    'time': time,
                    'date_raw': date_raw,
                    'year': year,
                    'latitude': lat,
                    'longitude': lon,
                    'type': ship_type,
                    'sunk': sunk,
                    'damaged': damaged,
                    'raw': line.strip()[:120]
                })
    
    return contacts

def extract_aircraft_contacts(ocr_data, patrol_num, year):
    """Extract aircraft contacts from OCR data."""
    contacts = []
    
    # Find pages with aircraft contacts
    aircraft_pages = []
    for page_num, text in ocr_data.items():
        if 'AIRCRAFT' in text.upper() and ('CONTACT' in text.upper() or 'Time' in text):
            aircraft_pages.append(int(page_num))
    
    if not aircraft_pages:
        return contacts
    
    # Extract dates and aircraft types from each page
    months = ['January', 'February', 'March', 'April', 'May', 'June', 
              'July', 'August', 'September', 'October', 'November', 'December']
    
    ac_types_jp = ['Sally', 'Emily', 'Kate', 'Betty', 'Nell', 'Mavis', 'Zero', 
                   'Oscar', 'Tony', 'Jake', 'Jill', 'Judy', 'Frances', 'Grace']
    ac_types_us = ['PBM', 'PBY', 'B-24', 'B-25', 'B-29', 'P-38', 'P-47', 'F6F', 'TBF']
    
    contact_num = 0
    for page_num in sorted(aircraft_pages):
        text = ocr_data.get(str(page_num), '')
        
        # Find dates
        date_pattern = re.compile(r'(\d{1,2})\s+(' + '|'.join(months) + ')', re.IGNORECASE)
        date_matches = date_pattern.findall(text)
        
        # Find aircraft types
        ac_found = []
        for ac in ac_types_jp + ac_types_us:
            if ac.lower() in text.lower():
                ac_found.append(ac)
        
        # Find positions
        pos_pattern = re.compile(r'(\d{1,2}-\d{2}(?:\.\d)?[NS]?)\s+(\d{2,3}-\d{2}(?:\.\d)?[EW]?)')
        pos_matches = pos_pattern.findall(text)
        
        # Create contacts for each date found
        for i, (day, month) in enumerate(date_matches):
            contact_num += 1
            pos = pos_matches[i] if i < len(pos_matches) else ('', '')
            ac_type = ac_found[i] if i < len(ac_found) else ''
            
            # Determine if friendly or enemy
            is_friendly = ac_type in ac_types_us
            
            contacts.append({
                'patrol': patrol_num,
                'contact_no': contact_num,
                'page': page_num,
                'date': f"{day} {month}",
                'year': year,
                'latitude': pos[0],
                'longitude': pos[1],
                'type': ac_type,
                'friendly': is_friendly
            })
    
    return contacts

def main():
    all_ship_contacts = []
    all_aircraft_contacts = []
    
    print("Extracting contacts from all patrol reports...")
    print("=" * 70)
    
    for patrol_num, report_name, year, period in PATROLS:
        print(f"\nPatrol {patrol_num} ({year}, {period})")
        print("-" * 50)
        
        ocr = load_ocr(report_name)
        if not ocr:
            print(f"  No OCR data found")
            continue
        
        # Extract contacts
        ships = extract_ship_contacts(ocr, patrol_num, year)
        aircraft = extract_aircraft_contacts(ocr, patrol_num, year)
        
        print(f"  Ship contacts: {len(ships)}")
        print(f"  Aircraft contacts: {len(aircraft)}")
        
        # Count sunk ships
        sunk = sum(1 for s in ships if s['sunk'])
        if sunk:
            print(f"  Ships sunk: {sunk}")
        
        all_ship_contacts.extend(ships)
        all_aircraft_contacts.extend(aircraft)
    
    print("\n" + "=" * 70)
    print(f"TOTAL SHIP CONTACTS: {len(all_ship_contacts)}")
    print(f"TOTAL AIRCRAFT CONTACTS: {len(all_aircraft_contacts)}")
    
    # Save ship contacts
    ship_csv = f'{REPORTS_DIR}/all_ship_contacts.csv'
    with open(ship_csv, 'w', newline='') as f:
        if all_ship_contacts:
            writer = csv.DictWriter(f, fieldnames=all_ship_contacts[0].keys())
            writer.writeheader()
            writer.writerows(all_ship_contacts)
    print(f"\nSaved: {ship_csv}")
    
    # Save aircraft contacts
    ac_csv = f'{REPORTS_DIR}/all_aircraft_contacts.csv'
    with open(ac_csv, 'w', newline='') as f:
        if all_aircraft_contacts:
            writer = csv.DictWriter(f, fieldnames=all_aircraft_contacts[0].keys())
            writer.writeheader()
            writer.writerows(all_aircraft_contacts)
    print(f"Saved: {ac_csv}")
    
    # Summary by patrol
    print("\n" + "=" * 70)
    print("SUMMARY BY PATROL")
    print("=" * 70)
    print(f"{'Patrol':<8} {'Ships':<8} {'Sunk':<6} {'Aircraft':<10}")
    print("-" * 40)
    for patrol_num, _, _, _ in PATROLS:
        ships = [s for s in all_ship_contacts if s['patrol'] == patrol_num]
        aircraft = [a for a in all_aircraft_contacts if a['patrol'] == patrol_num]
        sunk = sum(1 for s in ships if s['sunk'])
        print(f"{patrol_num:<8} {len(ships):<8} {sunk:<6} {len(aircraft):<10}")
    
    return all_ship_contacts, all_aircraft_contacts

if __name__ == "__main__":
    main()
