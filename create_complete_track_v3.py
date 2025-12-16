#!/usr/bin/env python3
"""
Create patrol tracks with proper antimeridian (dateline) handling.
"""

import folium
import csv
import pandas as pd
from datetime import datetime
import re

REPORTS_DIR = "/home/jmknapp/cobia/patrolReports"

PATROL_COLORS = {
    1: '#e41a1c',  2: '#377eb8',  3: '#4daf4a',
    4: '#984ea3',  5: '#ff7f00',  6: '#a65628',
}

PATROL_YEARS = {1: 1944, 2: 1944, 3: 1944, 4: 1944, 5: 1945, 6: 1945}

def parse_datetime(date_str, time_str, year):
    if not date_str or pd.isna(date_str):
        return None
    
    date_str = str(date_str).strip()
    months = {'january':1, 'february':2, 'march':3, 'april':4, 'may':5, 'june':6,
              'july':7, 'august':8, 'september':9, 'october':10, 'november':11, 'december':12}
    
    month_num = None
    day = None
    
    for month_name, num in months.items():
        if month_name in date_str.lower():
            month_num = num
            day_match = re.search(r'(\d{1,2})', date_str)
            if day_match:
                day = int(day_match.group(1))
            break
    
    if not month_num or not day:
        return None
    
    hour, minute = 12, 0
    if time_str and not pd.isna(time_str):
        time_str = str(time_str).strip()
        if len(time_str) == 4 and time_str.isdigit():
            hour = int(time_str[:2])
            minute = int(time_str[2:])
    
    try:
        return datetime(year, month_num, day, hour, minute)
    except:
        return None

def load_all_positions():
    all_positions = []
    
    # Noon positions
    noon = pd.read_csv(f'{REPORTS_DIR}/cobia_positions.csv')
    noon = noon.dropna(subset=['latitude', 'longitude'])
    for _, row in noon.iterrows():
        patrol = int(row['patrol'])
        dt = parse_datetime(row.get('date', ''), '1200', PATROL_YEARS.get(patrol, 1944))
        all_positions.append({
            'patrol': patrol, 'datetime': dt,
            'latitude': row['latitude'], 'longitude': row['longitude'],
            'type': 'noon', 'label': f"Noon - {row.get('date', '')}"
        })
    
    # Ship contacts
    ships = pd.read_csv(f'{REPORTS_DIR}/all_ship_contacts.csv')
    ships = ships.dropna(subset=['latitude', 'longitude'])
    for _, row in ships.iterrows():
        patrol = int(row['patrol'])
        dt = parse_datetime(row.get('date', ''), row.get('time', ''), 
                           int(row.get('year', PATROL_YEARS.get(patrol, 1944))))
        all_positions.append({
            'patrol': patrol, 'datetime': dt,
            'latitude': row['latitude'], 'longitude': row['longitude'],
            'type': 'ship', 'label': f"Ship #{row['contact_no']} - {row.get('date', '')}"
        })
    
    # Aircraft contacts (Patrol 1)
    aircraft = pd.read_csv(f'{REPORTS_DIR}/patrol1_aircraft_contacts.csv')
    aircraft = aircraft.dropna(subset=['latitude', 'longitude'])
    for _, row in aircraft.iterrows():
        patrol = int(row['patrol'])
        dt = parse_datetime(row.get('date', ''), row.get('time', ''), 1944)
        all_positions.append({
            'patrol': patrol, 'datetime': dt,
            'latitude': row['latitude'], 'longitude': row['longitude'],
            'type': 'aircraft', 'label': f"Aircraft #{row['contact_no']} - {row.get('date', '')}"
        })
    
    return all_positions

def split_at_antimeridian(coords):
    """Split coordinate list at antimeridian crossings."""
    if len(coords) < 2:
        return [coords]
    
    segments = []
    current_segment = [coords[0]]
    
    for i in range(1, len(coords)):
        prev_lon = coords[i-1][1]
        curr_lon = coords[i][1]
        
        # Check for antimeridian crossing (large longitude jump)
        if abs(curr_lon - prev_lon) > 180:
            # End current segment and start new one
            segments.append(current_segment)
            current_segment = [coords[i]]
        else:
            current_segment.append(coords[i])
    
    segments.append(current_segment)
    return segments

def main():
    positions = load_all_positions()
    print(f"Loaded {len(positions)} total position points")
    
    # Create map centered on Pacific
    m = folium.Map(location=[20, 160], zoom_start=3,
                   tiles='https://server.arcgisonline.com/ArcGIS/rest/services/Ocean/World_Ocean_Base/MapServer/tile/{z}/{y}/{x}',
                   attr='Esri Ocean')
    
    for patrol in range(1, 7):
        patrol_pos = [p for p in positions if p['patrol'] == patrol]
        patrol_pos.sort(key=lambda x: (x['datetime'] is None, x['datetime'] or datetime.max))
        
        if len(patrol_pos) < 2:
            print(f"  Patrol {patrol}: only {len(patrol_pos)} points, skipping")
            continue
        
        coords = [(p['latitude'], p['longitude']) for p in patrol_pos]
        color = PATROL_COLORS[patrol]
        
        # Split at antimeridian crossings
        segments = split_at_antimeridian(coords)
        print(f"  Patrol {patrol}: {len(coords)} points, {len(segments)} segments")
        
        track_group = folium.FeatureGroup(name=f'Patrol {patrol} Track', show=True)
        for segment in segments:
            if len(segment) >= 2:
                folium.PolyLine(segment, weight=2, color=color, opacity=0.7).add_to(track_group)
        track_group.add_to(m)
    
    # Contact markers
    contact_group = folium.FeatureGroup(name='Contacts', show=True)
    for p in positions:
        if p['type'] == 'ship':
            folium.Marker([p['latitude'], p['longitude']], popup=p['label'],
                         icon=folium.DivIcon(html='<div style="font-size:12px;">🚢</div>')).add_to(contact_group)
        elif p['type'] == 'aircraft':
            folium.Marker([p['latitude'], p['longitude']], popup=p['label'],
                         icon=folium.DivIcon(html='<div style="font-size:10px;">✈️</div>')).add_to(contact_group)
    contact_group.add_to(m)
    
    folium.LayerControl().add_to(m)
    m.save(f'{REPORTS_DIR}/static/patrol_map.html')
    print(f"\nSaved patrol_map.html")

if __name__ == "__main__":
    main()
