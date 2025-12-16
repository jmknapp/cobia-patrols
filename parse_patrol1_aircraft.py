#!/usr/bin/env python3
"""
Parse aircraft contact tables from Patrol 1 (pages 22-28).
Produces clean CSV with position validation.
"""

import json
import re
import csv

REPORTS_DIR = "/home/jmknapp/cobia/patrolReports"

def extract_positions(text):
    """Extract lat/lon based on degree values with validation."""
    lats = []
    lons = []
    
    # Match any coordinate pattern
    pattern = r'(\d{1,3})-(\d{2})(?:\.(\d))?([NSEW])?'
    
    for m in re.finditer(pattern, text):
        deg = int(m.group(1))
        mins = int(m.group(2))
        dec = int(m.group(3)) if m.group(3) else 0
        direction = m.group(4)
        
        value = deg + (mins + dec/10) / 60
        
        # Validate Pacific theater ranges
        if deg <= 40 and (direction in ['N', 'S', None]):
            if direction == 'S':
                value = -value
            lats.append(value)
        elif 100 <= deg <= 180 and (direction in ['E', 'W', None]):
            if direction == 'W':
                value = -value
            lons.append(value)
        # Fix OCR error: 119-XXN should be 19-XXN (latitude)
        elif 110 <= deg <= 120 and direction in ['N', 'S', None]:
            # This is likely a latitude with OCR adding a leading "1"
            corrected_deg = deg - 100
            value = corrected_deg + (mins + dec/10) / 60
            if direction == 'S':
                value = -value
            lats.append(value)
    
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
    
    print(f"  Page {page_num}: contacts {start_contact}-{start_contact+num_contacts-1}")
    print(f"           dates={len(dates)}, times={len(times)}, lats={len(lats)}, lons={len(lons)}, types={len(types)}")
    
    contacts = []
    for i in range(num_contacts):
        contact_no = start_contact + i
        lat = lats[i] if i < len(lats) else None
        lon = lons[i] if i < len(lons) else None
        
        # Validate position makes sense for Pacific theater
        if lat and (lat < -10 or lat > 40):
            print(f"      Warning: contact {contact_no} lat={lat:.2f} out of range, dropping")
            lat = None
        if lon and (lon < 100 and lon > -170):
            print(f"      Warning: contact {contact_no} lon={lon:.2f} suspicious")
        
        contacts.append({
            'patrol': 1,
            'year': 1944,
            'contact_no': contact_no,
            'date': dates[i] if i < len(dates) else '',
            'time': times[i] if i < len(times) else '',
            'latitude': lat,
            'longitude': lon,
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
    
    with_pos = sum(1 for c in all_contacts if c['latitude'] and c['longitude'])
    print(f"Contacts with valid positions: {with_pos}/{len(all_contacts)}")
    print(f"{'='*70}")
    
    # Print summary table
    print(f"\n{'#':>3} {'Date':>12} {'Time':>5} {'Lat':>8} {'Lon':>8} {'Type':>8}")
    print("-" * 55)
    for c in all_contacts:
        lat_str = f"{c['latitude']:.1f}" if c['latitude'] else "-"
        lon_str = f"{c['longitude']:.1f}" if c['longitude'] else "-"
        print(f"{c['contact_no']:3d} {c['date']:>12} {c['time']:>5} {lat_str:>8} {lon_str:>8} {c['type']:>8}")
    
    # Save to CSV
    with open(f'{REPORTS_DIR}/patrol1_aircraft_contacts.csv', 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['patrol', 'year', 'contact_no', 'date', 'time', 
                                                'latitude', 'longitude', 'type', 'friendly'])
        writer.writeheader()
        writer.writerows(all_contacts)
    
    print(f"\nSaved to patrol1_aircraft_contacts.csv")

if __name__ == "__main__":
    main()
