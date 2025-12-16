#!/usr/bin/env python3
"""
Create final interactive map with patrol routes and contacts.
"""

import csv
import folium
from folium import plugins

COLORS = {
    1: '#e41a1c', 2: '#377eb8', 3: '#4daf4a',
    4: '#984ea3', 5: '#ff7f00', 6: '#a65628',
}

def load_positions():
    positions = []
    with open('/home/jmknapp/cobia/patrolReports/cobia_positions.csv', 'r') as f:
        for row in csv.DictReader(f):
            try:
                positions.append({
                    'patrol': int(row['patrol']),
                    'lat': float(row['latitude']),
                    'lon': float(row['longitude']),
                    'date': row['date']
                })
            except:
                pass
    return positions

def load_ship_contacts():
    contacts = []
    with open('/home/jmknapp/cobia/patrolReports/all_ship_contacts.csv', 'r') as f:
        for row in csv.DictReader(f):
            try:
                lat = float(row['latitude']) if row['latitude'] else None
                lon = float(row['longitude']) if row['longitude'] else None
                if lat and lon and 100 <= lon <= 180:
                    contacts.append({
                        'patrol': int(row['patrol']),
                        'lat': lat,
                        'lon': lon,
                        'date': row['date'],
                        'type': row['type'],
                        'sunk': row['sunk'].lower() == 'true',
                        'contact_no': row['contact_no']
                    })
            except:
                pass
    return contacts

def load_aircraft_contacts():
    contacts = []
    with open('/home/jmknapp/cobia/patrolReports/all_aircraft_contacts.csv', 'r') as f:
        for row in csv.DictReader(f):
            try:
                lat = float(row['latitude']) if row['latitude'] else None
                lon = float(row['longitude']) if row['longitude'] else None
                if lat and lon and 100 <= lon <= 180:
                    contacts.append({
                        'patrol': int(row['patrol']),
                        'lat': lat,
                        'lon': lon,
                        'date': row['date'],
                        'type': row['type'],
                        'friendly': row['friendly'].lower() == 'true',
                        'contact_no': row['contact_no']
                    })
            except:
                pass
    return contacts

def main():
    positions = load_positions()
    ships = load_ship_contacts()
    aircraft = load_aircraft_contacts()
    
    print(f"Positions: {len(positions)}")
    print(f"Ship contacts with positions: {len(ships)}")
    print(f"Aircraft contacts with positions: {len(aircraft)}")
    
    # Center
    all_lats = [p['lat'] for p in positions]
    all_lons = [p['lon'] for p in positions]
    center = [sum(all_lats)/len(all_lats), sum(all_lons)/len(all_lons)]
    
    # Create map
    m = folium.Map(location=center, zoom_start=4, tiles=None)
    
    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/Ocean/World_Ocean_Base/MapServer/tile/{z}/{y}/{x}',
        attr='Esri', name='Ocean'
    ).add_to(m)
    folium.TileLayer('cartodbpositron', name='Light').add_to(m)
    
    # Patrol routes
    patrols = {}
    for p in positions:
        patrols.setdefault(p['patrol'], []).append(p)
    
    for pn in sorted(patrols.keys()):
        pts = patrols[pn]
        color = COLORS.get(pn, '#888')
        fg = folium.FeatureGroup(name=f'Patrol {pn} Route')
        
        if len(pts) >= 2:
            folium.PolyLine([[p['lat'], p['lon']] for p in pts], 
                           color=color, weight=3, opacity=0.7).add_to(fg)
        for p in pts:
            folium.CircleMarker([p['lat'], p['lon']], radius=3, color=color,
                               fill=True, fill_opacity=0.5).add_to(fg)
        fg.add_to(m)
    
    # Ship contacts
    ship_fg = folium.FeatureGroup(name=f'Ship Contacts ({len(ships)})')
    for s in ships:
        color = 'red' if s['sunk'] else 'darkblue'
        popup = f"Ship #{s['contact_no']}<br>Patrol {s['patrol']}<br>{s['date']}<br>{s['type']}"
        if s['sunk']:
            popup += "<br><b>SUNK</b>"
        folium.Marker([s['lat'], s['lon']], popup=popup,
                     icon=folium.Icon(color=color, icon='ship', prefix='fa')).add_to(ship_fg)
    ship_fg.add_to(m)
    
    # Aircraft contacts
    ac_fg = folium.FeatureGroup(name=f'Aircraft Contacts ({len(aircraft)})')
    for a in aircraft:
        color = 'green' if a['friendly'] else 'orange'
        popup = f"Aircraft #{a['contact_no']}<br>Patrol {a['patrol']}<br>{a['date']}<br>{a['type']}"
        folium.Marker([a['lat'], a['lon']], popup=popup,
                     icon=folium.Icon(color=color, icon='plane', prefix='fa')).add_to(ac_fg)
    ac_fg.add_to(m)
    
    folium.LayerControl().add_to(m)
    
    # Legend
    legend = '''
    <div style="position:fixed;bottom:50px;left:50px;z-index:1000;background:white;
                padding:15px;border:2px solid grey;border-radius:5px;font-family:Arial;">
        <h4 style="margin:0 0 10px 0;">USS Cobia Patrols</h4>
    '''
    for pn, c in COLORS.items():
        legend += f'<div><span style="background:{c};width:20px;height:3px;display:inline-block;margin-right:5px;"></span>Patrol {pn}</div>'
    legend += '''
        <hr style="margin:10px 0;">
        <div>🚢 Ship Contact</div>
        <div style="color:red;">🚢 Ship Sunk</div>
        <div style="color:orange;">✈️ Enemy Aircraft</div>
        <div style="color:green;">✈️ Friendly Aircraft</div>
    </div>'''
    m.get_root().html.add_child(folium.Element(legend))
    
    # Title
    title = '''
    <div style="position:fixed;top:10px;left:50%;transform:translateX(-50%);z-index:1000;
                background:rgba(255,255,255,0.95);padding:10px 20px;border:2px solid #333;
                border-radius:5px;text-align:center;font-family:Arial;">
        <h2 style="margin:0;">USS Cobia (SS-245) War Patrols</h2>
        <p style="margin:5px 0 0 0;font-size:12px;">1944-1945 • Routes & Contacts</p>
    </div>'''
    m.get_root().html.add_child(folium.Element(title))
    
    m.save('/home/jmknapp/cobia/patrolReports/static/patrol_map.html')
    print("Map saved!")

if __name__ == "__main__":
    main()
