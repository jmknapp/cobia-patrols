#!/usr/bin/env python3
"""
Parse aircraft contact tables from Patrol 1 (pages 22-28).
Uses known table structure: 32 contacts, ~5 per page.
"""

import json
import re

REPORTS_DIR = "/home/jmknapp/cobia/patrolReports"

def extract_positions(text):
    """Extract lat/lon pairs from OCR text."""
    positions = []
    
    # Pattern for coordinates like 12-41N, 170-30E
    lat_pattern = r'(\d{1,2})-(\d{2})(?:\.(\d))?([NS])'
    lon_pattern = r'(\d{2,3})-(\d{2})(?:\.(\d))?([EW])'
    
    lat_matches = list(re.finditer(lat_pattern, text))
    lon_matches = list(re.finditer(lon_pattern, text))
    
    lats = []
    for m in lat_matches:
        deg = int(m.group(1))
        mins = int(m.group(2))
        dec = int(m.group(3)) if m.group(3) else 0
        lat = deg + (mins + dec/10) / 60
        if m.group(4) == 'S':
            lat = -lat
        lats.append(lat)
    
    lons = []
    for m in lon_matches:
        deg = int(m.group(1))
        mins = int(m.group(2))  
        dec = int(m.group(3)) if m.group(3) else 0
        lon = deg + (mins + dec/10) / 60
        if m.group(4) == 'W':
            lon = -lon
        lons.append(lon)
    
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
        # Must be exactly 4 digits and a valid time
        if re.match(r'^\d{4}$', line):
            val = int(line)
            if 0 <= val <= 2359:
                times.append(line)
        # Also check for times at start of line
        m = re.match(r'^(\d{4})\s', line)
        if m:
            val = int(m.group(1))
            if 0 <= val <= 2359:
                times.append(m.group(1))
    return times

def extract_types(text):
    """Extract aircraft types."""
    types = []
    # Check for US PBM, PBY (friendlies)
    text_lower = text.lower()
    
    type_patterns = [
        (r'US\s+PBM', 'PBM', True),
        (r'\bPBM\b', 'PBM', True),
        (r'\bPBY\b', 'PBY', True),
        (r'\bSally\b', 'Sally', False),
        (r'\bEmily\b', 'Emily', False),
        (r'\bKate\b', 'Kate', False),
        (r'\bBetty\b', 'Betty', False),
        (r'\bBotty\b', 'Betty', False),  # OCR error
        (r'\bNell\b', 'Nell', False),
    ]
    
    for pattern, name, friendly in type_patterns:
        for _ in re.finditer(pattern, text, re.IGNORECASE):
            types.append((name, friendly))
    
    return types

def parse_page(page_num, text, start_contact, num_contacts):
    """Parse a single page of the aircraft contact table."""
    contacts = []
    
    dates = extract_dates(text)
    times = extract_times(text)
    lats, lons = extract_positions(text)
    types = extract_types(text)
    
    print(f"  Page {page_num}: dates={dates[:num_contacts]}, times={times[:num_contacts]}")
    print(f"           lats={[f'{l:.2f}' for l in lats[:num_contacts]]}, lons={[f'{l:.2f}' for l in lons[:num_contacts]]}")
    
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
    
    print("Parsing Patrol 1 Aircraft Contacts...")
    print("=" * 70)
    
    # Known structure: contacts 1-32 across pages 22-28
    page_map = [
        (22, 1, 5),   # page, start_contact, num_contacts
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
    
    print(f"\n{'#':>3} {'Date':>12} {'Time':>5} {'Latitude':>10} {'Longitude':>12} {'Type':>8} {'Fnd'}")
    print("-" * 70)
    
    with_pos = 0
    for c in all_contacts:
        lat_str = f"{c['latitude']:.2f}" if c['latitude'] else "-"
        lon_str = f"{c['longitude']:.2f}" if c['longitude'] else "-"
        if c['latitude'] and c['longitude']:
            with_pos += 1
        fnd = "Y" if c['friendly'] else ""
        print(f"{c['contact_no']:3d} {c['date']:>12} {c['time']:>5} {lat_str:>10} {lon_str:>12} {c['type']:>8} {fnd}")
    
    print(f"\nContacts with positions: {with_pos}/{len(all_contacts)}")

if __name__ == "__main__":
    main()
