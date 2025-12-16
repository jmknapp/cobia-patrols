#!/usr/bin/env python3
"""
Parse aircraft contact tables from Patrol 1 (pages 22-28).
The table has columns for each contact, read row by row.
"""

import json
import re

REPORTS_DIR = "/home/jmknapp/cobia/patrolReports"

def parse_patrol1_aircraft():
    with open(f'{REPORTS_DIR}/USS_Cobia_1st_Patrol_Report_gv_ocr.json') as f:
        ocr = json.load(f)
    
    contacts = []
    
    # Page 22: contacts 1-5
    # Page 23: contacts 6-10
    # Page 24: contacts 11-15
    # Page 25: contacts 16-20
    # Page 26: contacts 21-25
    # Page 27: contacts 26-30
    # Page 28: contacts 31-32
    
    page_contacts = {
        22: 5,
        23: 5,
        24: 5,
        25: 5,
        26: 5,
        27: 5,
        28: 2
    }
    
    contact_num = 0
    
    for page_num, num_contacts in page_contacts.items():
        text = ocr.get(str(page_num), '')
        lines = text.split('\n')
        
        # Find the CONTACT NUMBER line
        contact_line_idx = None
        for i, line in enumerate(lines):
            if 'CONTACT NUMBER' in line.upper():
                contact_line_idx = i
                break
        
        if contact_line_idx is None:
            continue
        
        # Extract data from subsequent lines
        # Skip header lines until we get to the contact numbers (single digits or double digits)
        data_start = None
        for i in range(contact_line_idx + 1, len(lines)):
            line = lines[i].strip()
            # Look for first contact number (should be a number matching expected sequence)
            if line.isdigit() and int(line) == contact_num + 1:
                data_start = i
                break
            # Also check for numbers with dots like "18."
            if re.match(r'^\d{1,2}\.?$', line):
                num = int(re.match(r'^(\d{1,2})', line).group(1))
                if num == contact_num + 1:
                    data_start = i
                    break
        
        if data_start is None:
            # Try finding by looking for sequence of small numbers
            for i in range(contact_line_idx + 1, min(contact_line_idx + 20, len(lines))):
                line = lines[i].strip()
                if re.match(r'^\d{1,2}$', line):
                    num = int(line)
                    if contact_num < num <= contact_num + 10:
                        data_start = i
                        break
        
        if data_start is None:
            print(f"  Page {page_num}: Could not find data start")
            continue
        
        # Now extract contact numbers, dates, times, positions
        # Contact numbers are on consecutive lines
        contact_numbers = []
        dates = []
        times = []
        latitudes = []
        longitudes = []
        
        # Read contact numbers
        idx = data_start
        while idx < len(lines) and len(contact_numbers) < num_contacts:
            line = lines[idx].strip()
            if re.match(r'^\d{1,2}\.?$', line):
                num = int(re.match(r'^(\d{1,2})', line).group(1))
                contact_numbers.append(num)
            elif line.isdigit():
                contact_numbers.append(int(line))
            idx += 1
        
        # Now look for dates (month names)
        months = ['January', 'February', 'March', 'April', 'May', 'June', 
                  'July', 'August', 'September', 'October', 'November', 'December']
        
        for i in range(data_start, min(len(lines), data_start + 30)):
            line = lines[i]
            for month in months:
                if month in line:
                    # Extract all dates from this line
                    date_matches = re.findall(r'(\d{1,2})\s*(' + '|'.join(months) + ')', line, re.IGNORECASE)
                    for dm in date_matches:
                        dates.append(f"{dm[0]} {dm[1]}")
        
        # Look for times (4-digit numbers that look like times)
        for i in range(data_start, min(len(lines), data_start + 30)):
            line = lines[i].strip()
            if re.match(r'^\d{4}$', line):
                time_val = int(line)
                if 0 <= time_val <= 2359:
                    times.append(line)
        
        # Look for latitudes (DD-MM.MN or DD-MMN patterns)
        lat_pattern = re.compile(r'(\d{1,2})-(\d{2})(?:\.(\d))?([NS])?')
        lon_pattern = re.compile(r'(\d{2,3})-(\d{2})(?:\.(\d))?([EW])?')
        
        for i in range(data_start, min(len(lines), data_start + 50)):
            line = lines[i]
            # Check for latitude
            for match in lat_pattern.finditer(line):
                deg = int(match.group(1))
                mins = int(match.group(2))
                dec = int(match.group(3)) if match.group(3) else 0
                direction = match.group(4) or 'N'
                if 0 <= deg <= 40:  # Valid lat range for Pacific
                    lat = deg + (mins + dec/10) / 60
                    if direction == 'S':
                        lat = -lat
                    latitudes.append(lat)
            
            # Check for longitude
            for match in lon_pattern.finditer(line):
                deg = int(match.group(1))
                mins = int(match.group(2))
                dec = int(match.group(3)) if match.group(3) else 0
                direction = match.group(4) or 'E'
                if 100 <= deg <= 180:  # Valid lon range for Pacific
                    lon = deg + (mins + dec/10) / 60
                    if direction == 'W':
                        lon = -lon
                    longitudes.append(lon)
        
        # Look for aircraft types
        ac_types = []
        for ac in ['PBM', 'PBY', 'Sally', 'Emily', 'Kate', 'Betty', 'Botty', 'Nell']:
            if ac.lower() in text.lower():
                count = len(re.findall(ac, text, re.IGNORECASE))
                ac_types.extend([ac] * count)
        
        print(f"  Page {page_num}: contacts={contact_numbers}, dates={len(dates)}, times={len(times)}, lats={len(latitudes)}, lons={len(longitudes)}")
        
        # Match up the data
        for i, cn in enumerate(contact_numbers):
            contact_num = cn
            date = dates[i] if i < len(dates) else ''
            time = times[i] if i < len(times) else ''
            lat = latitudes[i] if i < len(latitudes) else None
            lon = longitudes[i] if i < len(longitudes) else None
            ac_type = ac_types[i] if i < len(ac_types) else ''
            
            contacts.append({
                'contact_no': cn,
                'page': page_num,
                'date': date,
                'time': time,
                'latitude': lat,
                'longitude': lon,
                'type': ac_type,
                'friendly': ac_type in ['PBM', 'PBY']
            })
    
    return contacts

def main():
    print("Parsing Patrol 1 Aircraft Contacts...")
    print("=" * 70)
    
    contacts = parse_patrol1_aircraft()
    
    print(f"\n{'='*70}")
    print(f"Extracted {len(contacts)} aircraft contacts")
    print(f"{'='*70}")
    
    print(f"\n{'#':>3} {'Date':>12} {'Time':>5} {'Latitude':>10} {'Longitude':>12} {'Type':>8}")
    print("-" * 60)
    
    with_pos = 0
    for c in contacts:
        lat_str = f"{c['latitude']:.2f}" if c['latitude'] else "-"
        lon_str = f"{c['longitude']:.2f}" if c['longitude'] else "-"
        if c['latitude'] and c['longitude']:
            with_pos += 1
        print(f"{c['contact_no']:3d} {c['date']:>12} {c['time']:>5} {lat_str:>10} {lon_str:>12} {c['type']:>8}")
    
    print(f"\nContacts with positions: {with_pos}/{len(contacts)}")

if __name__ == "__main__":
    main()
