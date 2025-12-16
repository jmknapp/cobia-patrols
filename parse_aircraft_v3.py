#!/usr/bin/env python3
"""
Parse aircraft contact tables from Patrol 1 (pages 22-28).
Handles missing E/W suffixes on longitudes.
"""

import json
import re

REPORTS_DIR = "/home/jmknapp/cobia/patrolReports"

def extract_positions(text):
    """Extract lat/lon from OCR text. Handles missing direction suffixes."""
    lines = text.split('\n')
    
    lats = []
    lons = []
    
    # Find the "Long." line to separate lat/lon sections
    long_line_idx = None
    for i, line in enumerate(lines):
        if 'Long.' in line or 'Long' in line:
            long_line_idx = i
            break
    
    # Latitude pattern - usually has N/S but sometimes not
    lat_pattern = r'(\d{1,2})-(\d{2})(?:\.(\d))?([NS])?'
    # Longitude pattern - often missing E/W
    lon_pattern = r'(\d{2,3})-(\d{2})(?:\.(\d))?([EW])?'
    
    for i, line in enumerate(lines):
        # Skip if line has "Long" - this is the header
        if 'Long' in line:
            continue
        
        # Check for coordinates based on position
        matches = list(re.finditer(r'(\d{1,3})-(\d{2})(?:\.(\d))?([NSEW])?', line))
        
        for m in matches:
            deg = int(m.group(1))
            mins = int(m.group(2))
            dec = int(m.group(3)) if m.group(3) else 0
            direction = m.group(4)
            
            value = deg + (mins + dec/10) / 60
            
            # Determine if lat or lon based on degree value and position
            if long_line_idx and i > long_line_idx:
                # After "Long." line = these are longitudes
                if deg >= 100 and deg <= 180:
                    if direction == 'W':
                        value = -value
                    lons.append(value)
            elif deg <= 40:
                # Likely latitude (Pacific theater)
                if direction == 'S':
                    value = -value
                lats.append(value)
            elif deg >= 100 and deg <= 180:
                # Likely longitude
                if direction == 'W':
                    value = -value
                lons.append(value)
    
    return lats, lons

def extract_dates(text):
    """Extract dates like '27 June' or '13 August'."""
    months = ['January', 'February', 'March', 'April', 'May', 'June', 
              'July', 'August', 'September', 'October', 'November', 'December']
    pattern = r'(\d{1,2})\s+(' + '|'.join(months) + ')'
    matches = re.findall(pattern, text, re.IGNORECASE)
    return [f"{m[0]} {m[1]}" for m in matches]

def extract_times(text):
    """Extract 4-digit times from lines."""
    times = []
    for line in text.split('\n'):
        line = line.strip()
        if re.match(r'^\d{4}$', line):
            val = int(line)
            if 0 <= val <= 2359:
                times.append(line)
        m = re.match(r'^(\d{4})\s', line)
        if m:
            val = int(m.group(1))
            if 0 <= val <= 2359:
                times.append(m.group(1))
    return times

def extract_types(text):
    """Extract aircraft types in order of appearance."""
    types = []
    text_lower = text.lower()
    
    # Find all type mentions with their positions
    type_patterns = [
        (r'US\s*PBM|PBM', 'PBM', True),
        (r'PBY', 'PBY', True),
        (r'Sally', 'Sally', False),
        (r'Emily', 'Emily', False),
        (r'Kate', 'Kate', False),
        (r'Bett?y', 'Betty', False),
        (r'Nell', 'Nell', False),
    ]
    
    all_matches = []
    for pattern, name, friendly in type_patterns:
        for m in re.finditer(pattern, text, re.IGNORECASE):
            all_matches.append((m.start(), name, friendly))
    
    # Sort by position
    all_matches.sort(key=lambda x: x[0])
    return [(m[1], m[2]) for m in all_matches]

def parse_page(page_num, text, start_contact, num_contacts):
    """Parse a single page of the aircraft contact table."""
    contacts = []
    
    dates = extract_dates(text)
    times = extract_times(text)
    lats, lons = extract_positions(text)
    types = extract_types(text)
    
    print(f"  Page {page_num}: {num_contacts} contacts, dates={len(dates)}, times={len(times)}, lats={len(lats)}, lons={len(lons)}, types={len(types)}")
    
    for i in range(num_contacts):
        contact_no = start_contact + i
        
        date = dates[i] if i < len(dates) else ''
        time = times[i] if i < len(times) else ''
        lat = lats[i] if i < len(lats) else None
        lon = lons[i] if i < len(lons) else None
        ac_type = types[i][0] if i < len(types) else ''
        friendly = types[i][1] if i < len(types) else False
        
        contacts.append({
            'contact_no': contact_no,
            'page': page_num,
            'date': date,
            'time': time,
            'latitude': lat,
            'longitude': lon,
            'type': ac_type,
            'friendly': friendly
        })
    
    return contacts

def main():
    with open(f'{REPORTS_DIR}/USS_Cobia_1st_Patrol_Report_gv_ocr.json') as f:
        ocr = json.load(f)
    
    print("Parsing Patrol 1 Aircraft Contacts (v3)")
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
    
    print(f"\n{'#':>3} {'Date':>12} {'Time':>5} {'Latitude':>10} {'Longitude':>12} {'Type':>8}")
    print("-" * 60)
    
    with_pos = 0
    for c in all_contacts:
        lat_str = f"{c['latitude']:.2f}" if c['latitude'] else "-"
        lon_str = f"{c['longitude']:.2f}" if c['longitude'] else "-"
        if c['latitude'] and c['longitude']:
            with_pos += 1
        print(f"{c['contact_no']:3d} {c['date']:>12} {c['time']:>5} {lat_str:>10} {lon_str:>12} {c['type']:>8}")
    
    print(f"\nContacts with positions: {with_pos}/{len(all_contacts)}")

if __name__ == "__main__":
    main()
