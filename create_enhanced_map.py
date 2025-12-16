#!/usr/bin/env python3
"""
Create enhanced interactive map with patrol routes AND contacts.
"""

import csv
import folium
from folium import plugins
import re

# Patrol colors
COLORS = {
    1: '#e41a1c',  # Red
    2: '#377eb8',  # Blue
    3: '#4daf4a',  # Green
    4: '#984ea3',  # Purple
    5: '#ff7f00',  # Orange
    6: '#a65628',  # Brown
}

def parse_position(lat_str, lon_str):
    """Convert position strings like '28-24N' '141-18E' to decimal degrees."""
    if not lat_str or not lon_str:
        return None, None
    
    try:
        # Parse latitude
        lat_match = re.match(r'(\d+)-(\d+)(?:\.(\d))?([NS])?', lat_str)
        if lat_match:
            deg = int(lat_match.group(1))
            mins = int(lat_match.group(2))
            dec = int(lat_match.group(3)) if lat_match.group(3) else 0
            direction = lat_match.group(4) or 'N'
            lat = deg + (mins + dec/10) / 60
            if direction == 'S':
                lat = -lat
        else:
            return None, None
        
        # Parse longitude
        lon_match = re.match(r'(\d+)-(\d+)(?:\.(\d))?([EW])?', lon_str)
        if lon_match:
            deg = int(lon_match.group(1))
            mins = int(lon_match.group(2))
            dec = int(lon_match.group(3)) if lon_match.group(3) else 0
            direction = lon_match.group(4) or 'E'
            lon = deg + (mins + dec/10) / 60
            if direction == 'W':
                lon = -lon
        else:
            return None, None
        
        # Validate
        if abs(lat) > 60 or lon < 100 or lon > 180:
            return None, None
            
        return lat, lon
    except:
        return None, None

def load_positions():
    """Load patrol positions."""
    positions = []
    with open('/home/jmknapp/cobia/patrolReports/cobia_positions.csv', 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['latitude'] and row['longitude']:
                try:
                    positions.append({
                        'patrol': int(row['patrol']),
                        'lat': float(row['latitude']),
                        'lon': float(row['longitude']),
                        'date': row['date'],
                        'type': row['type']
                    })
                except:
                    pass
    return positions

def load_ship_contacts():
    """Load ship contacts."""
    contacts = []
    try:
        with open('/home/jmknapp/cobia/patrolReports/all_ship_contacts.csv', 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                lat, lon = parse_position(row.get('latitude', ''), row.get('longitude', ''))
                if lat and lon:
                    contacts.append({
                        'patrol': int(row['patrol']),
                        'lat': lat,
                        'lon': lon,
                        'date': row.get('date_raw', ''),
                        'type': row.get('type', ''),
                        'sunk': row.get('sunk', '').lower() == 'true',
                        'contact_no': row.get('contact_no', '')
                    })
    except Exception as e:
        print(f"Error loading ship contacts: {e}")
    return contacts

def load_aircraft_contacts():
    """Load aircraft contacts."""
    contacts = []
    try:
        with open('/home/jmknapp/cobia/patrolReports/all_aircraft_contacts.csv', 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                lat, lon = parse_position(row.get('latitude', ''), row.get('longitude', ''))
                if lat and lon:
                    contacts.append({
                        'patrol': int(row['patrol']),
                        'lat': lat,
                        'lon': lon,
                        'date': row.get('date', ''),
                        'type': row.get('type', ''),
                        'friendly': row.get('friendly', '').lower() == 'true',
                        'contact_no': row.get('contact_no', '')
                    })
    except Exception as e:
        print(f"Error loading aircraft contacts: {e}")
    return contacts

def main():
    positions = load_positions()
    ship_contacts = load_ship_contacts()
    aircraft_contacts = load_aircraft_contacts()
    
    print(f"Loaded {len(positions)} patrol positions")
    print(f"Loaded {len(ship_contacts)} ship contacts with valid positions")
    print(f"Loaded {len(aircraft_contacts)} aircraft contacts with valid positions")
    
    # Calculate map center
    all_lats = [p['lat'] for p in positions]
    all_lons = [p['lon'] for p in positions]
    center_lat = sum(all_lats) / len(all_lats)
    center_lon = sum(all_lons) / len(all_lons)
    
    # Create map
    m = folium.Map(location=[center_lat, center_lon], zoom_start=4, tiles=None)
    
    # Add tile layers
    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/Ocean/World_Ocean_Base/MapServer/tile/{z}/{y}/{x}',
        attr='Esri Ocean Basemap',
        name='Ocean Bathymetry'
    ).add_to(m)
    
    folium.TileLayer('cartodbpositron', name='Light Map').add_to(m)
    
    # Group positions by patrol
    patrols = {}
    for p in positions:
        if p['patrol'] not in patrols:
            patrols[p['patrol']] = []
        patrols[p['patrol']].append(p)
    
    # Add patrol routes
    for patrol_num in sorted(patrols.keys()):
        patrol_positions = patrols[patrol_num]
        color = COLORS.get(patrol_num, '#333333')
        
        fg = folium.FeatureGroup(name=f'Patrol {patrol_num} Route')
        
        if len(patrol_positions) >= 2:
            route_coords = [[p['lat'], p['lon']] for p in patrol_positions]
            folium.PolyLine(route_coords, color=color, weight=3, opacity=0.7).add_to(fg)
        
        for p in patrol_positions:
            folium.CircleMarker(
                location=[p['lat'], p['lon']],
                radius=3,
                color=color,
                fill=True,
                fill_opacity=0.5,
                popup=f"Patrol {patrol_num}<br>{p['date']}"
            ).add_to(fg)
        
        fg.add_to(m)
    
    # Add ship contacts
    ship_fg = folium.FeatureGroup(name=f'Ship Contacts ({len(ship_contacts)})')
    for c in ship_contacts:
        color = COLORS.get(c['patrol'], '#333333')
        icon_color = 'red' if c['sunk'] else 'blue'
        
        folium.Marker(
            location=[c['lat'], c['lon']],
            popup=f"Ship Contact #{c['contact_no']}<br>Patrol {c['patrol']}<br>{c['date']}<br>Type: {c['type']}<br>{'SUNK' if c['sunk'] else ''}",
            icon=folium.Icon(color=icon_color, icon='ship', prefix='fa')
        ).add_to(ship_fg)
    ship_fg.add_to(m)
    
    # Add aircraft contacts
    ac_fg = folium.FeatureGroup(name=f'Aircraft Contacts ({len(aircraft_contacts)})')
    for c in aircraft_contacts:
        color = 'green' if c['friendly'] else 'orange'
        
        folium.Marker(
            location=[c['lat'], c['lon']],
            popup=f"Aircraft Contact #{c['contact_no']}<br>Patrol {c['patrol']}<br>{c['date']}<br>Type: {c['type']}<br>{'Friendly' if c['friendly'] else 'Enemy'}",
            icon=folium.Icon(color=color, icon='plane', prefix='fa')
        ).add_to(ac_fg)
    ac_fg.add_to(m)
    
    # Add layer control
    folium.LayerControl().add_to(m)
    
    # Add legend
    legend_html = '''
    <div style="position: fixed; bottom: 50px; left: 50px; z-index: 1000;
                background-color: white; padding: 15px; border: 2px solid grey;
                border-radius: 5px; font-family: Arial; max-width: 250px;">
        <h4 style="margin: 0 0 10px 0;">USS Cobia Patrols</h4>
        <div style="margin-bottom: 10px;">
    '''
    for patrol_num in sorted(COLORS.keys()):
        color = COLORS[patrol_num]
        legend_html += f'<div><span style="background:{color}; width:20px; height:3px; display:inline-block; margin-right:5px;"></span> Patrol {patrol_num}</div>'
    
    legend_html += '''
        </div>
        <div style="border-top: 1px solid #ccc; padding-top: 10px; margin-top: 10px;">
            <div>🚢 <span style="color:blue">●</span> Ship Contact</div>
            <div>🚢 <span style="color:red">●</span> Ship Sunk</div>
            <div>✈️ <span style="color:orange">●</span> Enemy Aircraft</div>
            <div>✈️ <span style="color:green">●</span> Friendly Aircraft</div>
        </div>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))
    
    # Add title
    title_html = '''
    <div style="position: fixed; top: 10px; left: 50%; transform: translateX(-50%); z-index: 1000;
                background-color: rgba(255,255,255,0.95); padding: 10px 20px; border: 2px solid #333;
                border-radius: 5px; font-family: Arial; text-align: center;">
        <h2 style="margin: 0;">USS Cobia (SS-245) War Patrols</h2>
        <p style="margin: 5px 0 0 0; font-size: 12px;">Routes, Ship Contacts & Aircraft Contacts • 1944-1945</p>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(title_html))
    
    # Save
    output_path = '/home/jmknapp/cobia/patrolReports/static/patrol_map.html'
    m.save(output_path)
    print(f"\nMap saved: {output_path}")

if __name__ == "__main__":
    main()
