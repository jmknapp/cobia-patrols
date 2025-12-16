#!/usr/bin/env python3
"""
Create an interactive map of USS Cobia patrol routes.
Color-coded by patrol with bathymetric ocean tiles.
"""

import csv
import folium
from folium import plugins

# Read positions
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
                    'type': row['type'],
                    'page': row['page']
                })
            except:
                pass

print(f"Loaded {len(positions)} positions")

# Group by patrol
patrols = {}
for p in positions:
    patrol_num = p['patrol']
    if patrol_num not in patrols:
        patrols[patrol_num] = []
    patrols[patrol_num].append(p)

# Sort each patrol's positions by page number (rough chronological order)
for patrol_num in patrols:
    patrols[patrol_num].sort(key=lambda x: int(x['page']))

# Patrol colors (distinct, easy to see)
COLORS = {
    1: '#e41a1c',  # Red
    2: '#377eb8',  # Blue
    3: '#4daf4a',  # Green
    4: '#984ea3',  # Purple
    5: '#ff7f00',  # Orange
    6: '#a65628',  # Brown
}

# Calculate map center (average of all positions)
all_lats = [p['lat'] for p in positions]
all_lons = [p['lon'] for p in positions]
center_lat = sum(all_lats) / len(all_lats)
center_lon = sum(all_lons) / len(all_lons)

print(f"Map center: ({center_lat:.2f}, {center_lon:.2f})")

# Create map with ocean/bathymetric tiles
# Using Esri Ocean Basemap which shows bathymetry
m = folium.Map(
    location=[center_lat, center_lon],
    zoom_start=4,
    tiles=None  # We'll add custom tiles
)

# Add Esri Ocean basemap (shows bathymetric contours)
folium.TileLayer(
    tiles='https://server.arcgisonline.com/ArcGIS/rest/services/Ocean/World_Ocean_Base/MapServer/tile/{z}/{y}/{x}',
    attr='Esri Ocean Basemap',
    name='Ocean Bathymetry',
    overlay=False
).add_to(m)

# Add standard map as alternative
folium.TileLayer(
    tiles='cartodbpositron',
    name='Light Map',
    overlay=False
).add_to(m)

# Add each patrol as a polyline with markers
for patrol_num in sorted(patrols.keys()):
    patrol_positions = patrols[patrol_num]
    color = COLORS.get(patrol_num, '#333333')
    
    # Create feature group for this patrol
    fg = folium.FeatureGroup(name=f'Patrol {patrol_num} ({len(patrol_positions)} pts)')
    
    # Draw route line
    if len(patrol_positions) >= 2:
        route_coords = [[p['lat'], p['lon']] for p in patrol_positions]
        folium.PolyLine(
            route_coords,
            color=color,
            weight=3,
            opacity=0.8,
            popup=f'Patrol {patrol_num}'
        ).add_to(fg)
    
    # Add markers for each position
    for i, p in enumerate(patrol_positions):
        # Determine marker icon
        if i == 0:
            icon = folium.Icon(color='green', icon='play', prefix='fa')
            label = f"Patrol {patrol_num} START"
        elif i == len(patrol_positions) - 1:
            icon = folium.Icon(color='red', icon='stop', prefix='fa')
            label = f"Patrol {patrol_num} END"
        else:
            # Use circle marker for intermediate points
            folium.CircleMarker(
                location=[p['lat'], p['lon']],
                radius=4,
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.7,
                popup=f"Patrol {patrol_num}<br>{p['date']}<br>{p['type']}<br>({p['lat']:.2f}, {p['lon']:.2f})"
            ).add_to(fg)
            continue
        
        folium.Marker(
            location=[p['lat'], p['lon']],
            popup=f"{label}<br>{p['date']}<br>({p['lat']:.2f}, {p['lon']:.2f})",
            icon=icon
        ).add_to(fg)
    
    fg.add_to(m)

# Add layer control
folium.LayerControl().add_to(m)

# Add legend
legend_html = '''
<div style="position: fixed; bottom: 50px; left: 50px; z-index: 1000;
            background-color: white; padding: 10px; border: 2px solid grey;
            border-radius: 5px; font-family: Arial;">
    <h4 style="margin: 0 0 10px 0;">USS Cobia Patrols</h4>
'''
for patrol_num in sorted(COLORS.keys()):
    color = COLORS[patrol_num]
    count = len(patrols.get(patrol_num, []))
    legend_html += f'<div><span style="background:{color}; width:20px; height:3px; display:inline-block; margin-right:5px;"></span> Patrol {patrol_num} ({count} pts)</div>'
legend_html += '</div>'

m.get_root().html.add_child(folium.Element(legend_html))

# Add title
title_html = '''
<div style="position: fixed; top: 10px; left: 50%; transform: translateX(-50%); z-index: 1000;
            background-color: rgba(255,255,255,0.9); padding: 10px 20px; border: 2px solid #333;
            border-radius: 5px; font-family: Arial;">
    <h2 style="margin: 0;">USS Cobia (SS-245) War Patrol Routes</h2>
    <p style="margin: 5px 0 0 0; font-size: 12px;">1944-1945 • Pacific Theater</p>
</div>
'''
m.get_root().html.add_child(folium.Element(title_html))

# Save map
output_path = '/home/jmknapp/cobia/patrolReports/static/patrol_map.html'
m.save(output_path)
print(f"\nMap saved to: {output_path}")
print(f"View at: http://localhost:5003/static/patrol_map.html")
