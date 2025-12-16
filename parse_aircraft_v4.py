#!/usr/bin/env python3
"""
Parse aircraft contact tables from Patrol 1 (pages 22-28).
Simple approach: separate lat/lon purely by degree values.
"""

import json
import re
import csv

REPORTS_DIR = "/home/jmknapp/cobia/patrolReports"

def extract_positions(text):
    """Extract lat/lon based on degree values only."""
    lats = []
    lons = []
    
    # Match any coordinate pattern: DD-MM.D or DDD-MM.D with optional direction
    pattern = r'(\d{1,3})-(\d{2})(?:\.(\d))?([NSEW])?'
    
    for m in re.finditer(pattern, text):
        deg = int(m.group(1))
        mins = int(m.group(2))
        dec = int(m.group(3)) if m.group(3) else 0
        direction = m.group(4)
        
        value = deg + (mins + dec/10) / 60
        
        if deg <= 40:  # Latitude
            if direction == 'S':
                value = -value
            lats.append(value)
        elif 100 <= deg <= 180:  # Longitude
            if direction == 'W':
                value = -value
            lons.append(value)
    
    return lats, lons

def extract_dates(text):
    months = ['January', 'February', 'March', 'April', 'May', 'June', 
              'July', 'August', 'September', 'October', 'November', 'December']
    pattern = r'(\d{1,2})\s+(' + '|'.join(months) + ')'
    matches = re.findall(pattern, text, re.IGNORECASE)
    return [f"{m[0]} {m[1]}" for m in matches]

def extract_times(text):
    times = []
    for line in text.split('\n'):
        line = line.strip()
        if re.match(r'^\d{4}$', line):
            val = int(line)
            if 0 <= val <= 2359:
                times.append(line)
    return times

def extract_types(text):
    types = []
    type_patterns = [
        (r'US\s*PBM|PBM', 'PBM', True),
        (r'PBY', 'PBY', True),
        (r'Sally', 'Sally', False),
        (r'Emily', 'Emily', False),
        (r'Kate', 'Kate', False),
        (r'Bett?y|Botty', 'Betty', False),
        (r'Nell', 'Nell', False),
    ]
    
    all_matches = []
    for pattern, name, friendly in type_patterns:
        for m in re.finditer(pattern, text, re.IGNORECASE):
            all_matches.append((m.start(), name, friendly))
    
    all_matches.sort(key=lambda x: x[0])
    return [(m[1], m[2]) for m in all_matches]

def parse_page(page_num, text, start_contact, num_contacts):
    dates = extract_dates(text)
    times = extract_times(text)
    lats, lons = extract_positions(text)
    types = extract_types(text)
    
    print(f"  Page {page_num}: contacts {start_contact}-{start_contact+num_contacts-1}, dates={len(dates)}, times={len(times)}, lats={len(lats)}, lons={len(lons)}")
    
    contacts = []
    for i in range(num_contacts):
        contact_no = start_contact + i
        contacts.append({
            'patrol': 1,
            'year': 1944,
            'contact_no': contact_no,
            'page': page_num,
            'date': dates[i] if i < len(dates) else '',
            'time': times[i] if i < len(times) else '',
            'latitude': lats[i] if i < len(lats) else None,
            'longitude': lons[i] if i < len(lons) else None,
            'type': types[i][0] if i < len(types) else '',
            'friendly': types[i][1] if i < len(types) else False
        })
    
    return contacts

def main():
    with open(f'{REPORTS_DIR}/USS_Cobia_1st_Patrol_Report_gv_ocr.json') as f:
        ocr = json.load(f)
    
    print("Parsing Patrol 1 Aircraft Contacts")
    print("=" * 70)
    
    page_map = [
        (22, 1, 5),
        (23, 6, 5),
        (24, 11, 5),
        (25, 16, 5),
        (26, 21, 5),
        (27, 26, 5),
        (28, 31, 2),
    ]
    
    all_contacts = []
    for page_num, start_contact, num_contacts in page_map:
        text = ocr.get(str(page_num), '')
        contacts = parse_page(page_num, text, start_contact, num_contacts)
        all_contacts.extend(contacts)
    
    print(f"\n{'='*70}")
    print(f"Extracted {len(all_contacts)} aircraft contacts")
    print(f"{'='*70}")
    
    print(f"\n{'#':>3} {'Date':>12} {'Time':>5} {'Latitude':>10} {'Longitude':>12} {'Type':>8} {'Friendly'}")
    print("-" * 70)
    
    with_pos = 0
    for c in all_contacts:
        lat_str = f"{c['latitude']:.2f}" if c['latitude'] else "-"
        lon_str = f"{c['longitude']:.2f}" if c['longitude'] else "-"
        if c['latitude'] and c['longitude']:
            with_pos += 1
        fnd = "Yes" if c['friendly'] else ""
        print(f"{c['contact_no']:3d} {c['date']:>12} {c['time']:>5} {lat_str:>10} {lon_str:>12} {c['type']:>8} {fnd}")
    
    print(f"\nContacts with positions: {with_pos}/{len(all_contacts)}")
    
    # Save to CSV
    with open(f'{REPORTS_DIR}/patrol1_aircraft_contacts.csv', 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['patrol', 'year', 'contact_no', 'date', 'time', 
                                                'latitude', 'longitude', 'type', 'friendly'])
        writer.writeheader()
        writer.writerows(all_contacts)
    
    print(f"\nSaved to patrol1_aircraft_contacts.csv")

if __name__ == "__main__":
    main()
