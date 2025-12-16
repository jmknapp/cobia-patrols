#!/usr/bin/env python3
"""
Create patrol tracks using ALL position data:
- Noon positions
- Ship contact positions (Cobia's position when contact made)
- Aircraft contact positions (Cobia's position when contact made)
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

def parse_date(date_str, year):
    """Parse date string like '27 June' or '7/12' to datetime."""
    if not date_str or pd.isna(date_str):
        return None
    
    date_str = str(date_str).strip()
    
    # Try "DD Month" format
    months = {'january':1, 'february':2, 'march':3, 'april':4, 'may':5, 'june':6,
              'july':7, 'august':8, 'september':9, 'october':10, 'november':11, 'december':12}
    
    for month_name, month_num in months.items():
        if month_name in date_str.lower():
            day_match = re.search(r'(\d{1,2})', date_str)
            if day_match:
                try:
                    return datetime(year, month_num, int(day_match.group(1)))
                except:
                    pass
    
    # Try "M/D" format
    if '/' in date_str:
        parts = date_str.split('/')
        if len(parts) == 2:
            try:
                return datetime(year, int(parts[0]), int(parts[1]))
            except:
                pass
    
    return None

def load_all_positions():
    """Load and combine all position data."""
    all_positions = []
    
    # 1. Noon positions
    noon = pd.read_csv(f'{REPORTS_DIR}/cobia_positions.csv')
    noon = noon.dropna(subset=['latitude', 'longitude'])
    for _, row in noon.iterrows():
        patrol = int(row['patrol'])
        dt = parse_date(row.get('date', ''), PATROL_YEARS.get(patrol, 1944))
        all_positions.append({
            'patrol': patrol,
            'datetime': dt,
            'latitude': row['latitude'],
            'longitude': row['longitude'],
            'type': 'noon',
            'label': f"Noon position - {row.get('date', '')}"
        })
    
    # 2. Ship contacts
    ships = pd.read_csv(f'{REPORTS_DIR}/all_ship_contacts.csv')
    ships = ships.dropna(subset=['latitude', 'longitude'])
    for _, row in ships.iterrows():
        patrol = int(row['patrol'])
        dt = parse_date(row.get('date', ''), int(row.get('year', PATROL_YEARS.get(patrol, 1944))))
        all_positions.append({
            'patrol': patrol,
            'datetime': dt,
            'latitude': row['latitude'],
            'longitude': row['longitude'],
            'type': 'ship',
            'label': f"Ship contact #{row['contact_no']} - {row.get('date', '')}"
        })
    
    # 3. Aircraft contacts (Patrol 1 improved)
    aircraft = pd.read_csv(f'{REPORTS_DIR}/patrol1_aircraft_contacts.csv')
    aircraft = aircraft.dropna(subset=['latitude', 'longitude'])
    for _, row in aircraft.iterrows():
        patrol = int(row['patrol'])
        dt = parse_date(row.get('date', ''), int(row.get('year', 1944)))
        all_positions.append({
            'patrol': patrol,
            'datetime': dt,
            'latitude': row['latitude'],
            'longitude': row['longitude'],
            'type': 'aircraft',
            'label': f"Aircraft contact #{row['contact_no']} - {row.get('date', '')}"
        })
    
    return all_positions

def main():
    positions = load_all_positions()
    print(f"Loaded {len(positions)} total position points")
    
    # Count by patrol
    for p in range(1, 7):
        count = sum(1 for pos in positions if pos['patrol'] == p)
        print(f"  Patrol {p}: {count} points")
    
    # Create map
    m = folium.Map(location=[20, 140], zoom_start=4,
                   tiles='https://server.arcgisonline.com/ArcGIS/rest/services/Ocean/World_Ocean_Base/MapServer/tile/{z}/{y}/{x}',
                   attr='Esri Ocean')
    
    # Create tracks for each patrol
    for patrol in range(1, 7):
        patrol_pos = [p for p in positions if p['patrol'] == patrol]
        
        # Sort by datetime (positions without dates go to end)
        patrol_pos.sort(key=lambda x: (x['datetime'] is None, x['datetime'] or datetime.max))
        
        if len(patrol_pos) < 2:
            continue
        
        coords = [(p['latitude'], p['longitude']) for p in patrol_pos]
        color = PATROL_COLORS[patrol]
        
        # Draw track line
        track_group = folium.FeatureGroup(name=f'Patrol {patrol} Track', show=True)
        folium.PolyLine(coords, weight=2, color=color, opacity=0.8).add_to(track_group)
        track_group.add_to(m)
        
        # Add markers for contacts
        for p in patrol_pos:
            if p['type'] == 'ship':
                icon_html = '<div style="font-size: 12px;">🚢</div>'
            elif p['type'] == 'aircraft':
                icon_html = '<div style="font-size: 10px;">✈️</div>'
            else:
                continue  # Skip noon position markers
            
            folium.Marker(
                [p['latitude'], p['longitude']],
                popup=p['label'],
                icon=folium.DivIcon(html=icon_html)
            ).add_to(m)
    
    # Add layer control
    folium.LayerControl().add_to(m)
    
    m.save(f'{REPORTS_DIR}/static/patrol_map.html')
    print(f"\nSaved patrol_map.html with complete tracks")

if __name__ == "__main__":
    main()
