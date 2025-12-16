#!/usr/bin/env python3
"""Update patrol map with improved Patrol 1 aircraft contacts."""

import folium
import csv
import pandas as pd

REPORTS_DIR = "/home/jmknapp/cobia/patrolReports"

PATROL_COLORS = {
    1: '#e41a1c',  2: '#377eb8',  3: '#4daf4a',
    4: '#984ea3',  5: '#ff7f00',  6: '#a65628',
}

def main():
    # Load positions
    positions = pd.read_csv(f'{REPORTS_DIR}/cobia_positions.csv')
    positions = positions.dropna(subset=['latitude', 'longitude'])
    print(f"Loaded {len(positions)} noon positions")
    
    # Load ship contacts
    ships = pd.read_csv(f'{REPORTS_DIR}/all_ship_contacts.csv')
    ships = ships.dropna(subset=['latitude', 'longitude'])
    print(f"Loaded {len(ships)} ship contacts with positions")
    
    # Load Patrol 1 aircraft (improved)
    p1_aircraft = pd.read_csv(f'{REPORTS_DIR}/patrol1_aircraft_contacts.csv')
    p1_aircraft = p1_aircraft.dropna(subset=['latitude', 'longitude'])
    
    # Load other patrols' aircraft from old file
    all_aircraft = pd.read_csv(f'{REPORTS_DIR}/all_aircraft_contacts.csv')
    other_aircraft = all_aircraft[all_aircraft['patrol'] != 1]
    other_aircraft = other_aircraft.dropna(subset=['latitude', 'longitude'])
    
    # Combine aircraft
    aircraft = pd.concat([p1_aircraft, other_aircraft], ignore_index=True)
    print(f"Loaded {len(aircraft)} aircraft contacts ({len(p1_aircraft)} from P1)")
    
    # Create map
    m = folium.Map(location=[20, 140], zoom_start=4, 
                   tiles='https://server.arcgisonline.com/ArcGIS/rest/services/Ocean/World_Ocean_Base/MapServer/tile/{z}/{y}/{x}',
                   attr='Esri Ocean')
    
    # Add patrol routes
    route_group = folium.FeatureGroup(name='Patrol Routes', show=True)
    for patrol in range(1, 7):
        patrol_data = positions[positions['patrol'] == patrol]
        if len(patrol_data) < 2:
            continue
        coords = list(zip(patrol_data['latitude'], patrol_data['longitude']))
        color = PATROL_COLORS[patrol]
        folium.PolyLine(coords, weight=3, color=color, opacity=0.8,
                       popup=f'Patrol {patrol}').add_to(route_group)
    route_group.add_to(m)
    
    # Add ship contacts
    ship_group = folium.FeatureGroup(name='Ship Contacts', show=True)
    for _, row in ships.iterrows():
        color = PATROL_COLORS.get(int(row['patrol']), 'gray')
        sunk = str(row.get('sunk', '')).lower() == 'true'
        icon = '🔥' if sunk else '🚢'
        popup = f"P{int(row['patrol'])} Ship #{row['contact_no']}<br>{row.get('type', '')}<br>{row.get('date', '')}"
        folium.Marker(
            [row['latitude'], row['longitude']],
            popup=popup,
            icon=folium.DivIcon(html=f'<div style="font-size: 14px;">{icon}</div>')
        ).add_to(ship_group)
    ship_group.add_to(m)
    
    # Add aircraft contacts
    aircraft_group = folium.FeatureGroup(name='Aircraft Contacts', show=True)
    for _, row in aircraft.iterrows():
        friendly = str(row.get('friendly', '')).lower() == 'true'
        icon = '✈️' if friendly else '🔴'
        popup = f"P{int(row['patrol'])} Aircraft #{row['contact_no']}<br>{row.get('type', '')}<br>{row.get('date', '')}"
        folium.Marker(
            [row['latitude'], row['longitude']],
            popup=popup,
            icon=folium.DivIcon(html=f'<div style="font-size: 12px;">{icon}</div>')
        ).add_to(aircraft_group)
    aircraft_group.add_to(m)
    
    # Add layer control
    folium.LayerControl().add_to(m)
    
    # Save
    m.save(f'{REPORTS_DIR}/static/patrol_map.html')
    print(f"\nSaved patrol_map.html")
    print(f"  Routes: {len(positions)} points")
    print(f"  Ships: {len(ships)} markers")  
    print(f"  Aircraft: {len(aircraft)} markers")

if __name__ == "__main__":
    main()
