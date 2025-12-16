#!/usr/bin/env python3
"""
Validate aircraft contacts data for plausibility.

Checks:
1. Distance/time validation: Could Cobia have traveled between consecutive contacts?
   - USS Cobia max speed: ~20 knots surfaced, ~9 knots submerged
   - Flag if required speed > 25 knots (generous margin)
   
2. Position sanity checks:
   - Latitude should be reasonable for Pacific theater
   - Longitude should be reasonable for Pacific theater
   
3. Date/time sequence: Contacts should be in chronological order within a patrol
"""

import mysql.connector
from datetime import datetime, timedelta
from math import radians, sin, cos, sqrt, atan2

# Haversine formula to calculate distance between two lat/lon points
def haversine_nm(lat1, lon1, lat2, lon2):
    """Calculate distance in nautical miles between two points."""
    if any(v is None for v in [lat1, lon1, lat2, lon2]):
        return None
    
    R = 3440.065  # Earth's radius in nautical miles
    
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    
    return R * c

def time_to_minutes(time_str):
    """Convert HHMM string to minutes since midnight."""
    if not time_str:
        return None
    time_str = str(time_str).zfill(4)
    hours = int(time_str[:2])
    mins = int(time_str[2:])
    return hours * 60 + mins

def format_position(contact):
    """Format position as degrees and minutes with hemisphere."""
    lat_deg = contact.get('latitude_deg')
    lat_min = contact.get('latitude_min')
    lat_hem = contact.get('latitude_hemisphere', 'N')
    lon_deg = contact.get('longitude_deg')
    lon_min = contact.get('longitude_min')
    lon_hem = contact.get('longitude_hemisphere', 'E')
    
    if lat_deg is not None and lat_min is not None:
        lat_str = f"{lat_deg:02d}°{float(lat_min):04.1f}'{lat_hem}"
    else:
        lat_str = "??°??'"
    
    if lon_deg is not None and lon_min is not None:
        lon_str = f"{lon_deg:03d}°{float(lon_min):04.1f}'{lon_hem}"
    else:
        lon_str = "???°??'"
    
    return f"{lat_str} {lon_str}"

def validate_aircraft():
    from db_config import get_db_connection
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Get all contacts ordered by patrol, date, time
    cursor.execute("""
        SELECT id, patrol, contact_no, observation_time, timezone, observation_date,
               latitude_deg, latitude_min, latitude_hemisphere,
               longitude_deg, longitude_min, longitude_hemisphere,
               latitude, longitude, aircraft_type
        FROM aircraft_contacts
        ORDER BY patrol, observation_date, observation_time
    """)
    
    contacts = cursor.fetchall()
    cursor.close()
    conn.close()
    
    if not contacts:
        print("No aircraft contacts found in database.")
        return
    
    # Group by patrol
    patrols = {}
    for c in contacts:
        p = c['patrol']
        if p not in patrols:
            patrols[p] = []
        patrols[p].append(c)
    
    print("=" * 80)
    print("AIRCRAFT CONTACTS VALIDATION REPORT")
    print("=" * 80)
    
    # Check 1: Position sanity
    print("\n[1] POSITION SANITY CHECKS")
    print("-" * 40)
    position_issues = []
    
    for c in contacts:
        lat = c['latitude']
        lon = c['longitude']
        
        # Check for missing positions
        if lat is None or lon is None:
            position_issues.append({
                'contact': c,
                'issue': 'Missing latitude/longitude'
            })
            continue
        
        # Pacific/Indian Ocean theater bounds (generous)
        # Latitude: -35 to 50 (covers Java Sea/Australia to Aleutians)
        # Longitude: 95E to 160W (95 to 180, then -180 to -150) - includes Malacca Strait
        
        lat_ok = -35 <= float(lat) <= 50
        
        # Longitude check - Pacific spans the antimeridian
        lon_val = float(lon)
        lon_ok = (95 <= lon_val <= 180) or (-180 <= lon_val <= -150)
        
        if not lat_ok:
            position_issues.append({
                'contact': c,
                'issue': f'Latitude outside expected range (-35° to 50°)'
            })
        
        if not lon_ok:
            position_issues.append({
                'contact': c,
                'issue': f'Longitude outside expected Pacific range'
            })
    
    if position_issues:
        for pi in position_issues:
            c = pi['contact']
            print(f"  P{c['patrol']} #{c['contact_no']}: {pi['issue']} - {format_position(c)}")
    else:
        print("  All positions within expected bounds.")
    
    # Check 2: Distance/time validation
    print("\n[2] DISTANCE/TIME VALIDATION (max 25 knots)")
    print("-" * 40)
    speed_issues = []
    
    for patrol_num in sorted(patrols.keys()):
        patrol_contacts = patrols[patrol_num]
        
        for i in range(1, len(patrol_contacts)):
            prev = patrol_contacts[i-1]
            curr = patrol_contacts[i]
            
            # Skip if missing position data
            if None in [prev['latitude'], prev['longitude'], 
                       curr['latitude'], curr['longitude']]:
                continue
            
            # Calculate distance
            dist_nm = haversine_nm(
                float(prev['latitude']), float(prev['longitude']),
                float(curr['latitude']), float(curr['longitude'])
            )
            
            # Calculate time difference
            if prev['observation_date'] and curr['observation_date'] and \
               prev['observation_time'] and curr['observation_time']:
                
                prev_mins = time_to_minutes(prev['observation_time'])
                curr_mins = time_to_minutes(curr['observation_time'])
                
                # Days difference
                days_diff = (curr['observation_date'] - prev['observation_date']).days
                
                # Total minutes difference
                time_diff_mins = days_diff * 24 * 60 + (curr_mins - prev_mins)
                
                if time_diff_mins <= 0:
                    speed_issues.append({
                        'prev': prev,
                        'curr': curr,
                        'issue': f'Time not advancing (diff: {time_diff_mins} mins)',
                        'distance': dist_nm,
                        'time_hrs': None,
                        'speed': None
                    })
                    continue
                
                time_diff_hrs = time_diff_mins / 60.0
                
                # Calculate required speed
                if time_diff_hrs > 0:
                    speed_knots = dist_nm / time_diff_hrs
                    
                    if speed_knots > 25:
                        speed_issues.append({
                            'prev': prev,
                            'curr': curr,
                            'issue': f'Required speed {speed_knots:.1f} knots exceeds 25 kt max',
                            'distance': dist_nm,
                            'time_hrs': time_diff_hrs,
                            'speed': speed_knots
                        })
    
    if speed_issues:
        for si in speed_issues:
            prev = si['prev']
            curr = si['curr']
            print(f"\n  P{curr['patrol']} #{prev['contact_no']} → #{curr['contact_no']}: {si['issue']}")
            print(f"    From: {prev['observation_date']} {prev['observation_time']} {format_position(prev)}")
            print(f"    To:   {curr['observation_date']} {curr['observation_time']} {format_position(curr)}")
            if si['distance']:
                print(f"    Distance: {si['distance']:.1f} nm", end="")
                if si['time_hrs']:
                    print(f", Time: {si['time_hrs']:.1f} hrs", end="")
                if si['speed']:
                    print(f", Speed needed: {si['speed']:.1f} kt")
                else:
                    print()
    else:
        print("  All contact transitions are within speed limits.")
    
    # Check 3: Chronological order within patrol
    print("\n[3] CHRONOLOGICAL ORDER CHECK")
    print("-" * 40)
    order_issues = []
    
    for patrol_num in sorted(patrols.keys()):
        patrol_contacts = patrols[patrol_num]
        
        for i in range(1, len(patrol_contacts)):
            prev = patrol_contacts[i-1]
            curr = patrol_contacts[i]
            
            # Check datetime ordering
            if prev['observation_date'] and curr['observation_date']:
                if curr['observation_date'] < prev['observation_date']:
                    order_issues.append({
                        'prev': prev,
                        'curr': curr,
                        'issue': 'Date goes backwards'
                    })
                elif curr['observation_date'] == prev['observation_date']:
                    # Same date - check time
                    prev_mins = time_to_minutes(prev['observation_time'])
                    curr_mins = time_to_minutes(curr['observation_time'])
                    if prev_mins and curr_mins and curr_mins < prev_mins:
                        order_issues.append({
                            'prev': prev,
                            'curr': curr,
                            'issue': f'Time goes backwards (same date)'
                        })
    
    if order_issues:
        for oi in order_issues:
            prev = oi['prev']
            curr = oi['curr']
            print(f"  P{curr['patrol']} #{prev['contact_no']} → #{curr['contact_no']}: {oi['issue']}")
            print(f"    {prev['observation_date']} {prev['observation_time']} → "
                  f"{curr['observation_date']} {curr['observation_time']}")
    else:
        print("  All contacts in chronological order.")
    
    # Check 4: Duplicate positions
    print("\n[4] DUPLICATE/VERY CLOSE POSITIONS")
    print("-" * 40)
    dup_found = False
    
    for patrol_num in sorted(patrols.keys()):
        patrol_contacts = patrols[patrol_num]
        
        for i in range(1, len(patrol_contacts)):
            prev = patrol_contacts[i-1]
            curr = patrol_contacts[i]
            
            if None in [prev['latitude'], prev['longitude'], 
                       curr['latitude'], curr['longitude']]:
                continue
            
            dist = haversine_nm(
                float(prev['latitude']), float(prev['longitude']),
                float(curr['latitude']), float(curr['longitude'])
            )
            
            if dist is not None and dist < 0.5:  # Less than half a nautical mile
                print(f"  P{curr['patrol']} #{prev['contact_no']} & #{curr['contact_no']}: "
                      f"Only {dist:.2f} nm apart at {format_position(curr)}")
                dup_found = True
    
    if not dup_found:
        print("  No duplicate positions found.")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total aircraft contacts analyzed: {len(contacts)}")
    print(f"Position issues: {len(position_issues)}")
    print(f"Speed/distance issues: {len(speed_issues)}")
    print(f"Chronological issues: {len(order_issues)}")
    
    total_issues = len(position_issues) + len(speed_issues) + len(order_issues)
    if total_issues == 0:
        print("\n✓ No issues found!")
    else:
        print(f"\n⚠ {total_issues} potential issues found - review above")

if __name__ == '__main__':
    validate_aircraft()

