#!/usr/bin/env python3
"""
Generate an interactive map showing USS Cobia patrol tracks.

Combines positions from:
- ship_contacts
- aircraft_contacts  
- positions (noon readings)
- inferred_positions

Sorts by date/time and plots piecewise linear paths for each patrol.
"""

import mysql.connector
import folium
from folium import Element, MacroElement
from jinja2 import Template
from datetime import datetime, timedelta
import math
import re

# CSS for animated surrender marker and torpedo attack marker
SURRENDER_MARKER_CSS = """
<style>
@keyframes pulse-gold {
    0% {
        transform: scale(1);
        box-shadow: 0 0 0 0 rgba(255, 215, 0, 0.7);
    }
    50% {
        transform: scale(1.1);
        box-shadow: 0 0 20px 10px rgba(255, 215, 0, 0.4);
    }
    100% {
        transform: scale(1);
        box-shadow: 0 0 0 0 rgba(255, 215, 0, 0);
    }
}
@keyframes pulse-red {
    0% {
        transform: scale(1);
        box-shadow: 0 0 0 0 rgba(220, 53, 69, 0.7);
    }
    50% {
        transform: scale(1.05);
        box-shadow: 0 0 12px 4px rgba(220, 53, 69, 0.4);
    }
    100% {
        transform: scale(1);
        box-shadow: 0 0 0 0 rgba(220, 53, 69, 0);
    }
}
.surrender-marker {
    animation: pulse-gold 2s ease-in-out infinite;
    background: linear-gradient(135deg, #ffd700 0%, #ffec8b 50%, #ffd700 100%);
    border: 3px solid #b8860b;
    border-radius: 50%;
    width: 30px;
    height: 30px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 16px;
    box-shadow: 0 0 15px 5px rgba(255, 215, 0, 0.6);
}
.torpedo-attack-marker {
    animation: pulse-red 1.5s ease-in-out infinite;
    background: linear-gradient(135deg, #dc3545 0%, #ff6b6b 50%, #dc3545 100%);
    border: 2px solid #a71d2a;
    border-radius: 4px;
    width: 24px;
    height: 24px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 12px;
    box-shadow: 0 0 8px 2px rgba(220, 53, 69, 0.5);
    color: white;
    font-weight: bold;
}
.gun-attack-marker {
    background: linear-gradient(135deg, #495057 0%, #6c757d 50%, #495057 100%);
    border: 2px solid #343a40;
    border-radius: 4px;
    width: 24px;
    height: 24px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 12px;
    box-shadow: 0 0 6px 2px rgba(73, 80, 87, 0.5);
    color: white;
    font-weight: bold;
}
.direction-arrow {
    font-size: 12px;
    color: white;
    text-shadow: 1px 1px 2px rgba(0,0,0,0.8), -1px -1px 2px rgba(0,0,0,0.8);
    font-weight: bold;
}
</style>
"""

# Aircraft type to local image mapping (images in static/aircraft_images/)
# Format: 'code': ('Full Name', 'image_path' or None)
AIRCRAFT_IMAGES = {
    # Japanese aircraft (Allied code names)
    'Betty': ('Mitsubishi G4M', '/static/aircraft_images/betty.jpg'),
    'Zero': ('Mitsubishi A6M Zero', '/static/aircraft_images/zero.jpg'),
    'Zeke': ('Mitsubishi A6M Zero', '/static/aircraft_images/zero.jpg'),
    'Lily': ('Kawasaki Ki-48', '/static/aircraft_images/lily.jpg'),
    'Val': ('Aichi D3A', '/static/aircraft_images/val.jpg'),
    'Nells': ('Mitsubishi G3M', '/static/aircraft_images/nell.jpg'),
    'Nell': ('Mitsubishi G3M', '/static/aircraft_images/nell.jpg'),
    'Dinah': ('Mitsubishi Ki-46', '/static/aircraft_images/dinah.jpg'),
    'Sally': ('Mitsubishi Ki-21', '/static/aircraft_images/sally.jpg'),
    'Two Sallys': ('Mitsubishi Ki-21', '/static/aircraft_images/sally.jpg'),
    'Mavis': ('Kawanishi H6K', '/static/aircraft_images/mavis.jpg'),
    'Emily': ('Kawanishi H8K', None),
    'Kate': ('Nakajima B5N', None),
    'Jake': ('Aichi E13A', '/static/aircraft_images/jake.jpg'),
    'Pete': ('Mitsubishi F1M', '/static/aircraft_images/pete.jpg'),
    'Dave': ('Nakajima E8N', '/static/aircraft_images/dave.jpg'),
    'Tojo': ('Nakajima Ki-44 Shoki', '/static/aircraft_images/tojo.jpg'),
    
    # US aircraft
    'PBY': ('Consolidated PBY Catalina', '/static/aircraft_images/pby.jpg'),
    'US PBY': ('Consolidated PBY Catalina', '/static/aircraft_images/pby.jpg'),
    'PBM': ('Martin PBM Mariner', '/static/aircraft_images/pbm.jpeg'),
    'US PBM': ('Martin PBM Mariner', '/static/aircraft_images/pbm.jpeg'),
    'SBD': ('Douglas SBD Dauntless', '/static/aircraft_images/sbd.jpg'),
    'Liberator': ('Consolidated B-24 Liberator', '/static/aircraft_images/liberator.jpg'),
    'US Liberator': ('Consolidated B-24 Liberator', '/static/aircraft_images/liberator.jpg'),
    'PB2Y': ('Consolidated PB2Y Coronado', '/static/aircraft_images/pb2y.jpg'),
    'US PB2Y': ('Consolidated PB2Y Coronado', '/static/aircraft_images/pb2y.jpg'),
    'B-26': ('Martin B-26 Marauder', '/static/aircraft_images/b26.jpg'),
    'Twin Engine Pat Bomber': ('Martin B-26 Marauder', '/static/aircraft_images/b26.jpg'),
    'Hellcat': ('Grumman F6F Hellcat', '/static/aircraft_images/hellcat.jpg'),
    'Hellcat Helldiver': ('Grumman F6F / Curtiss SB2C', '/static/aircraft_images/hellcat.jpg'),
    'Helldiver': ('Curtiss SB2C Helldiver', None),  # No image yet
}

def get_aircraft_popup(aircraft_type, patrol_num, date, time, position_str, observation_date, remarks='', contact_no='', view_link=''):
    """Generate popup HTML with aircraft image if available."""
    remarks_html = f'<br><i style="font-size:11px; color:#666;">{remarks}</i>' if remarks else ''
    contact_str = f' #{contact_no}' if contact_no else ''
    
    # Try to find a matching aircraft info
    aircraft_info = None
    if aircraft_type:
        # Check exact match first
        if aircraft_type in AIRCRAFT_IMAGES:
            aircraft_info = AIRCRAFT_IMAGES[aircraft_type]
        else:
            # Check if any key is contained in the type
            for key, info in AIRCRAFT_IMAGES.items():
                if key.lower() in aircraft_type.lower():
                    aircraft_info = info
                    break
    
    if aircraft_info:
        full_name, img_url = aircraft_info
        if img_url:
            return f'''<div style="width:320px">
                <b>P{patrol_num} Aircraft Contact{contact_str}</b><br>
                <b>{aircraft_type}</b> ({full_name})<br>
                {date} {time}<br>
                {position_str}{remarks_html}{view_link}<br>
                <img src="{img_url}" style="width:300px; margin-top:5px;">
            </div>'''
        else:
            return f'''<div style="width:280px">
                <b>P{patrol_num} Aircraft Contact{contact_str}</b><br>
                <b>{aircraft_type}</b> ({full_name})<br>
                {date} {time}<br>
                {position_str}{remarks_html}{view_link}
            </div>'''
    else:
        return f'''<div style="width:280px">
            <b>P{patrol_num} Aircraft Contact{contact_str}</b><br>
            <b>{aircraft_type or 'Unknown'}</b><br>
            {date} {time}<br>
            {position_str}{remarks_html}{view_link}
        </div>'''

# Colors for each patrol
PATROL_COLORS = {
    1: '#e41a1c',  # Red
    2: '#377eb8',  # Blue
    3: '#4daf4a',  # Green
    4: '#984ea3',  # Purple
    5: '#ff7f00',  # Orange
    6: '#a65628',  # Brown
}

def get_all_positions():
    """Fetch all positions from all tables including inferred positions."""
    from db_config import get_db_connection
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    all_positions = []
    
    # Ship contacts
    cursor.execute("""
        SELECT patrol, observation_date, observation_time, 
               latitude, longitude, 'ship' as source, ship_type as detail,
               latitude_deg, latitude_min, latitude_hemisphere,
               longitude_deg, longitude_min, longitude_hemisphere,
               remarks, contact_no
        FROM ship_contacts
        WHERE latitude IS NOT NULL AND longitude IS NOT NULL
    """)
    for row in cursor.fetchall():
        all_positions.append(row)
    
    # Aircraft contacts
    cursor.execute("""
        SELECT patrol, observation_date, observation_time,
               latitude, longitude, 'aircraft' as source, aircraft_type as detail,
               latitude_deg, latitude_min, latitude_hemisphere,
               longitude_deg, longitude_min, longitude_hemisphere,
               remarks, contact_no
        FROM aircraft_contacts
        WHERE latitude IS NOT NULL AND longitude IS NOT NULL
    """)
    for row in cursor.fetchall():
        all_positions.append(row)
    
    # Noon/other positions (no remarks column)
    cursor.execute("""
        SELECT patrol, observation_date, observation_time,
               latitude, longitude, 'position' as source, position_type as detail,
               latitude_deg, latitude_min, latitude_hemisphere,
               longitude_deg, longitude_min, longitude_hemisphere,
               NULL as remarks
        FROM positions
        WHERE latitude IS NOT NULL AND longitude IS NOT NULL
    """)
    for row in cursor.fetchall():
        all_positions.append(row)
    
    # Inferred positions (from narrative references, use tag field for both detail and remarks)
    cursor.execute("""
        SELECT patrol, observation_date, observation_time,
               latitude, longitude, 'inferred' as source, tag as detail,
               NULL as latitude_deg, NULL as latitude_min, NULL as latitude_hemisphere,
               NULL as longitude_deg, NULL as longitude_min, NULL as longitude_hemisphere,
               tag as remarks
        FROM inferred_positions
        WHERE latitude IS NOT NULL AND longitude IS NOT NULL
    """)
    for row in cursor.fetchall():
        all_positions.append(row)
    
    cursor.close()
    conn.close()
    
    return all_positions

def get_torpedo_attack_results():
    """Fetch torpedo attack results for popup display."""
    from db_config import get_db_connection
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT patrol, attack_number, result, target_name, target_type
        FROM torpedo_attacks
    """)
    
    # Create lookup dict: (patrol, attack_number) -> {result, target_name, target_type}
    results = {}
    for row in cursor.fetchall():
        key = (row['patrol'], row['attack_number'])
        results[key] = {
            'result': row['result'],
            'target_name': row['target_name'],
            'target_type': row['target_type']
        }
    
    cursor.close()
    conn.close()
    
    return results

def get_narrative_page_index():
    """Fetch narrative page index for linking popups to PDF pages."""
    from db_config import get_db_connection
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT patrol, page, observation_date, observation_time
        FROM narrative_page_index
        ORDER BY patrol, observation_date, observation_time
    """)
    
    # Group by patrol: patrol -> list of {page, date, time}
    index = {}
    for row in cursor.fetchall():
        patrol = row['patrol']
        if patrol not in index:
            index[patrol] = []
        index[patrol].append({
            'page': row['page'],
            'date': row['observation_date'],
            'time': row['observation_time']
        })
    
    cursor.close()
    conn.close()
    
    return index

def find_narrative_page(narrative_index, patrol, obs_date, obs_time):
    """
    Find the appropriate PDF page for a given patrol, date, and time.
    Returns the page number where the narrative starts at or before the given date/time.
    Falls back to page 1 if no match found.
    """
    if patrol not in narrative_index:
        return 1
    
    entries = narrative_index[patrol]
    
    # Convert obs_time to comparable format
    if obs_time:
        obs_time_str = str(obs_time).zfill(4)
    else:
        obs_time_str = "0000"
    
    # Find the latest entry that is at or before the given date/time
    best_page = 1
    for entry in entries:
        entry_date = entry['date']
        entry_time = entry['time'] or "0000"
        
        # Compare date first, then time
        if entry_date < obs_date:
            best_page = entry['page']
        elif entry_date == obs_date and entry_time <= obs_time_str:
            best_page = entry['page']
        elif entry_date > obs_date:
            break  # Entries are sorted, so we can stop
    
    return best_page

def get_pdf_filename(patrol):
    """Get the PDF filename for a given patrol number."""
    # Map patrol number to PDF filename
    patrol_pdfs = {
        1: 'USS_Cobia_P1.pdf',
        2: 'USS_Cobia_P2.pdf',
        3: 'USS_Cobia_P3.pdf',
        4: 'USS_Cobia_P4.pdf',
        5: 'USS_Cobia_P5.pdf',
        6: 'USS_Cobia_P6.pdf',
    }
    return patrol_pdfs.get(patrol, f'USS_Cobia_P{patrol}.pdf')

def format_position_str(p):
    """Format position as degrees/minutes string."""
    lat_d = p.get('latitude_deg')
    lat_m = p.get('latitude_min')
    lat_h = p.get('latitude_hemisphere')
    lon_d = p.get('longitude_deg')
    lon_m = p.get('longitude_min')
    lon_h = p.get('longitude_hemisphere')
    
    # If no deg/min data (e.g., inferred positions), format from decimal
    if lat_d is None or lon_d is None:
        lat = float(p.get('latitude', 0))
        lon = float(p.get('longitude', 0))
        lat_h = 'S' if lat < 0 else 'N'
        lon_h = 'W' if lon < 0 else 'E'
        lat = abs(lat)
        lon = abs(lon)
        lat_d = int(lat)
        lat_m = (lat - lat_d) * 60
        lon_d = int(lon)
        lon_m = (lon - lon_d) * 60
    
    lat_d = lat_d or 0
    lat_m = lat_m or 0
    lat_h = lat_h or 'N'
    lon_d = lon_d or 0
    lon_m = lon_m or 0
    lon_h = lon_h or 'E'
    
    # Handle decimal minutes
    if isinstance(lat_m, float):
        lat_str = f"{int(lat_d):02d}°{lat_m:04.1f}'{lat_h}"
    else:
        lat_str = f"{int(lat_d):02d}°{int(lat_m):02d}'{lat_h}"
    
    if isinstance(lon_m, float):
        lon_str = f"{int(lon_d):03d}°{lon_m:04.1f}'{lon_h}"
    else:
        lon_str = f"{int(lon_d):03d}°{int(lon_m):02d}'{lon_h}"
    
    return f"{lat_str} {lon_str}"

def time_to_minutes(time_str):
    """Convert time string to minutes for sorting."""
    if not time_str:
        return 0
    time_str = str(time_str).zfill(4)
    try:
        hours = int(time_str[:2])
        mins = int(time_str[2:])
        return hours * 60 + mins
    except:
        return 0

def sort_positions(positions):
    """Sort positions by patrol, date, time."""
    def sort_key(p):
        patrol = p['patrol'] or 0
        date = p['observation_date'] or datetime.min.date()
        time_mins = time_to_minutes(p['observation_time'])
        return (patrol, date, time_mins)
    
    return sorted(positions, key=sort_key)

def calculate_bearing(lat1, lon1, lat2, lon2):
    """Calculate bearing from point 1 to point 2 in degrees."""
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lon = math.radians(lon2 - lon1)
    
    x = math.sin(delta_lon) * math.cos(lat2_rad)
    y = math.cos(lat1_rad) * math.sin(lat2_rad) - math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(delta_lon)
    
    bearing = math.atan2(x, y)
    return (math.degrees(bearing) + 360) % 360

def get_midpoint(lat1, lon1, lat2, lon2):
    """Get midpoint between two coordinates."""
    return ((lat1 + lat2) / 2, (lon1 + lon2) / 2)

def normalize_longitudes_for_continuous_track(coords):
    """
    Normalize longitudes so a track crossing the antimeridian draws continuously.
    Converts western hemisphere longitudes to >180 values when needed.
    Returns normalized coordinates and segments that need splitting.
    """
    if len(coords) < 2:
        return [coords] if coords else []
    
    # Check if track crosses antimeridian by looking for large longitude jumps
    crosses_antimeridian = False
    for i in range(1, len(coords)):
        if abs(coords[i][1] - coords[i-1][1]) > 180:
            crosses_antimeridian = True
            break
    
    if not crosses_antimeridian:
        return [coords]
    
    # Normalize longitudes to be continuous
    # Strategy: convert negative longitudes to positive (add 360) when track goes westward
    normalized = []
    segments = []
    current_segment = []
    
    for i, (lat, lon) in enumerate(coords):
        if i == 0:
            # First point - check if we need to normalize
            # If most of the track is in positive longitudes, convert negative to positive
            pos_count = sum(1 for _, lo in coords if lo > 0)
            neg_count = len(coords) - pos_count
            if pos_count > neg_count and lon < 0:
                lon = lon + 360  # Convert -158 to 202
            current_segment.append((lat, lon))
        else:
            prev_lat, prev_lon = current_segment[-1]
            
            # Normalize current longitude relative to previous
            if lon < 0 and prev_lon > 100:
                # Crossing from positive to negative - convert to continuous
                lon = lon + 360
            elif lon > 100 and prev_lon > 200:
                # Continue in >180 range
                pass
            elif abs(lon - prev_lon) > 180:
                # Large jump - need to split segment here
                if current_segment:
                    segments.append(current_segment)
                current_segment = [(lat, lon)]
                continue
                
            current_segment.append((lat, lon))
    
    if current_segment:
        segments.append(current_segment)
    
    return segments


def split_at_antimeridian(coords):
    """
    Split a list of coordinates into segments that don't cross the antimeridian.
    Returns a list of coordinate lists.
    """
    # Use the new normalization function
    return normalize_longitudes_for_continuous_track(coords)

def create_map(positions):
    """Create a Folium map with patrol tracks."""
    
    # Get torpedo attack results for popup display
    torpedo_results = get_torpedo_attack_results()
    
    # Get narrative page index for PDF links
    narrative_index = get_narrative_page_index()
    
    # Group by patrol
    patrols = {}
    for p in positions:
        patrol_num = p['patrol']
        if patrol_num not in patrols:
            patrols[patrol_num] = []
        patrols[patrol_num].append(p)
    
    # Sort each patrol's positions
    for patrol_num in patrols:
        patrols[patrol_num] = sort_positions(patrols[patrol_num])
    
    # Calculate map center from all positions
    all_lats = [float(p['latitude']) for p in positions]
    all_lons = [float(p['longitude']) for p in positions]
    
    # Handle antimeridian for center calculation
    # Convert negative longitudes to 0-360 range for averaging
    adjusted_lons = [lon if lon >= 0 else lon + 360 for lon in all_lons]
    center_lat = sum(all_lats) / len(all_lats)
    center_lon = sum(adjusted_lons) / len(adjusted_lons)
    if center_lon > 180:
        center_lon -= 360
    
    # Create map with ESRI Ocean Basemap (bathymetric shading)
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=4,
        min_zoom=2,
        max_zoom=18,
        tiles=None  # Don't add default tiles
    )
    
    
    # Add ESRI World Imagery FIRST (underneath) as fallback for high zoom levels
    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri, Maxar, Earthstar Geographics',
        name='Satellite',
        control=False  # Don't show in layer control
    ).add_to(m)
    
    # Add ESRI Ocean Basemap SECOND (on top) - stops at zoom 13, satellite shows at higher zooms
    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/Ocean/World_Ocean_Base/MapServer/tile/{z}/{y}/{x}',
        attr='Esri, GEBCO, NOAA, National Geographic, DeLorme, HERE, Geonames.org, and other contributors',
        name='Ocean Basemap',
        max_zoom=9,  # Switch to satellite beyond this zoom
        control=False  # Don't show in layer control
    ).add_to(m)
    
    # Add CartoDB light labels for ocean basemap (zoom 2-9, black text)
    folium.TileLayer(
        tiles='https://{s}.basemaps.cartocdn.com/light_only_labels/{z}/{x}/{y}{r}.png',
        attr='CartoDB',
        name='Labels (Ocean)',
        overlay=True,
        control=False,  # Auto-switch, don't clutter layer control
        max_zoom=9,
        subdomains='abcd'
    ).add_to(m)
    
    # Add CartoDB dark labels for satellite (zoom 10+, white text)
    folium.TileLayer(
        tiles='https://{s}.basemaps.cartocdn.com/dark_only_labels/{z}/{x}/{y}{r}.png',
        attr='CartoDB',
        name='Labels (Satellite)',
        overlay=True,
        control=False,  # Auto-switch, don't clutter layer control
        min_zoom=10,
        subdomains='abcd'
    ).add_to(m)
    
    # Add custom CSS for animated surrender marker
    m.get_root().html.add_child(Element(SURRENDER_MARKER_CSS))
    
    # Create a FeatureGroup for each patrol (allows toggling)
    patrol_groups = {}
    
    # Add each patrol track
    for patrol_num in sorted(patrols.keys()):
        patrol_positions = patrols[patrol_num]
        color = PATROL_COLORS.get(patrol_num, '#333333')
        
        # Create a FeatureGroup for this patrol with color indicator in name
        # HTML span with colored line before patrol name
        patrol_label = f'<span style="display:inline-block; width:20px; height:4px; background:{color}; margin-right:6px; vertical-align:middle;"></span>Patrol {patrol_num}'
        fg = folium.FeatureGroup(name=patrol_label)
        patrol_groups[patrol_num] = fg
        
        # Build coordinate list
        coords = []
        for p in patrol_positions:
            lat = float(p['latitude'])
            lon = float(p['longitude'])
            coords.append((lat, lon))
        
        # Normalize and split at antimeridian crossings
        segments = split_at_antimeridian(coords)
        
        # Build a mapping of original coords to normalized coords for markers
        normalized_coords = {}
        for segment in segments:
            for lat, lon in segment:
                # Find the original coord that maps to this normalized one
                for orig_lat, orig_lon in coords:
                    if abs(orig_lat - lat) < 0.001:
                        # Check if this is a normalized longitude
                        if abs(orig_lon - lon) < 0.001 or abs(orig_lon + 360 - lon) < 0.001:
                            normalized_coords[(orig_lat, orig_lon)] = (lat, lon)
                            break
        
        # Draw each segment with direction arrows
        for segment in segments:
            if len(segment) >= 2:
                folium.PolyLine(
                    segment,
                    color=color,
                    weight=3,
                    opacity=0.8,
                    popup=f"Patrol {patrol_num}"
                ).add_to(fg)
                
                # Add direction arrows at midpoint of each line segment
                for i in range(len(segment) - 1):
                    lat1, lon1 = segment[i]
                    lat2, lon2 = segment[i + 1]
                    
                    # Skip very short segments
                    if abs(lat2 - lat1) < 0.1 and abs(lon2 - lon1) < 0.1:
                        continue
                    
                    # Calculate midpoint and bearing
                    mid_lat, mid_lon = get_midpoint(lat1, lon1, lat2, lon2)
                    bearing = calculate_bearing(lat1, lon1, lat2, lon2)
                    
                    # Create rotated arrow marker
                    arrow_html = f'''<div class="direction-arrow" style="transform: rotate({bearing}deg);">▲</div>'''
                    arrow_icon = folium.DivIcon(
                        html=arrow_html,
                        icon_size=(12, 12),
                        icon_anchor=(6, 6)
                    )
                    folium.Marker(
                        [mid_lat, mid_lon],
                        icon=arrow_icon
                    ).add_to(fg)
        
        # Add markers for each position
        for i, p in enumerate(patrol_positions):
            lat = float(p['latitude'])
            lon = float(p['longitude'])
            
            # Use normalized coordinates if available (for antimeridian crossing tracks)
            if (lat, lon) in normalized_coords:
                lat, lon = normalized_coords[(lat, lon)]
            
            source = p['source']
            detail = p['detail'] or ''
            date = p['observation_date']
            time = p['observation_time']
            
            # Format position as deg/min
            pos_str = format_position_str(p)
            
            remarks = p.get('remarks', '')
            contact_no = p.get('contact_no', '')
            
            # Get PDF page for this date/time
            pdf_page = find_narrative_page(narrative_index, patrol_num, date, time)
            pdf_file = get_pdf_filename(patrol_num)
            view_link = f'<br><a href="/view?file={pdf_file}&page={pdf_page}" target="_blank" style="font-size:11px; color:#2980b9;">View in Report →</a>'
            
            # Different marker styles for different sources
            if source == 'ship':
                remarks_html = f'<br><i style="font-size:11px; color:#666;">{remarks}</i>' if remarks else ''
                contact_str = f' #{contact_no}' if contact_no else ''
                popup_html = f'''<div style="width:280px">
                    <b>P{patrol_num} Ship Contact{contact_str}</b><br>
                    <b>{detail}</b><br>
                    {date} {time}<br>
                    {pos_str}{remarks_html}{view_link}
                </div>'''
                popup = folium.Popup(popup_html, max_width=350)
                # Smaller custom icon with ship graphic
                icon_html = '''<div style="
                    background-color: #c0392b;
                    border: 2px solid #922b21;
                    border-radius: 50% 50% 50% 0;
                    transform: rotate(-45deg);
                    width: 22px;
                    height: 22px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    box-shadow: 1px 1px 3px rgba(0,0,0,0.3);
                "><i class="fa fa-ship" style="transform: rotate(45deg); color: white; font-size: 10px;"></i></div>'''
                icon = folium.DivIcon(
                    html=icon_html,
                    icon_size=(22, 22),
                    icon_anchor=(11, 22)
                )
                folium.Marker([lat, lon], popup=popup, icon=icon).add_to(fg)
                continue
            elif source == 'aircraft':
                popup_html = get_aircraft_popup(detail, patrol_num, date, time, pos_str, date, remarks, contact_no, view_link)
                popup = folium.Popup(popup_html, max_width=350)
                # Smaller custom icon with plane graphic
                icon_html = '''<div style="
                    background-color: #2980b9;
                    border: 2px solid #1a5276;
                    border-radius: 50% 50% 50% 0;
                    transform: rotate(-45deg);
                    width: 22px;
                    height: 22px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    box-shadow: 1px 1px 3px rgba(0,0,0,0.3);
                "><i class="fa fa-plane" style="transform: rotate(45deg); color: white; font-size: 10px;"></i></div>'''
                icon = folium.DivIcon(
                    html=icon_html,
                    icon_size=(22, 22),
                    icon_anchor=(11, 22)
                )
                folium.Marker([lat, lon], popup=popup, icon=icon).add_to(fg)
                continue
            elif source == 'inferred':
                # Check if this is the surrender announcement (special animated marker)
                is_surrender = detail and 'Japan has accepted' in detail
                # Check if this is a torpedo attack
                is_torpedo_attack = detail and 'Torpedo Attack' in detail
                # Check if this is a gun attack
                is_gun_attack = detail and 'Gun Attack' in detail
                
                if is_surrender:
                    # Special animated surrender marker
                    popup_html = f'''<div style="width:320px; text-align:center;">
                        <h3 style="color:#b8860b; margin:0 0 10px 0;">🕊️ End of the War 🕊️</h3>
                        <b>August 14, 1945 - 2050</b><br><br>
                        <i style="font-size:14px;">"{detail}"</i><br><br>
                        {pos_str}<br>
                        <p style="font-size:11px; color:#666; margin-top:10px;">
                        USS Cobia was patrolling off Formosa when word came<br>
                        that Japan had accepted the terms of surrender.
                        </p>
                        {view_link}
                    </div>'''
                    popup = folium.Popup(popup_html, max_width=350)
                    
                    icon_html = '<div class="surrender-marker">⭐</div>'
                    icon = folium.DivIcon(
                        html=icon_html,
                        icon_size=(30, 30),
                        icon_anchor=(15, 15)
                    )
                    folium.Marker([lat, lon], popup=popup, icon=icon).add_to(fg)
                elif is_torpedo_attack:
                    # Special torpedo attack marker with explosion icon
                    # Extract attack number (handles "No. 1", "#1", etc.)
                    attack_match = re.search(r'(?:No\.?\s*|#)(\d+)', detail)
                    attack_num_int = int(attack_match.group(1)) if attack_match else None
                    attack_num_str = attack_match.group(1) if attack_match else '💥'
                    
                    # Look up result from torpedo_attacks table
                    result_info = torpedo_results.get((patrol_num, attack_num_int), {})
                    result = result_info.get('result', '')
                    target_name = result_info.get('target_name', '')
                    
                    # Build popup with result
                    result_line = ''
                    if result:
                        result_color = '#28a745' if result == 'Sunk' else '#dc3545' if result == 'Miss' else '#ffc107'
                        result_line = f'<br><b style="color:{result_color};">{result}</b>'
                        if target_name:
                            result_line += f' - {target_name}'
                    
                    remarks_line = f'<br><i style="font-size:11px; color:#666;">{remarks}</i>' if remarks and remarks != detail else ''
                    popup_html = f'''<div style="width:280px">
                        <b>P{patrol_num} {detail}</b>{result_line}<br>
                        {date} {time}<br>
                        {pos_str}{remarks_line}{view_link}
                    </div>'''
                    popup = folium.Popup(popup_html, max_width=350)
                    
                    icon_html = f'<div class="torpedo-attack-marker">{attack_num_str}</div>'
                    icon = folium.DivIcon(
                        html=icon_html,
                        icon_size=(24, 24),
                        icon_anchor=(12, 12)
                    )
                    folium.Marker([lat, lon], popup=popup, icon=icon).add_to(fg)
                elif is_gun_attack:
                    # Special gun attack marker
                    remarks_line = f'<br><i style="font-size:11px; color:#666;">{remarks}</i>' if remarks and remarks != detail else ''
                    popup_html = f'''<div style="width:280px">
                        <b>P{patrol_num} {detail}</b><br>
                        {date} {time}<br>
                        {pos_str}{remarks_line}{view_link}
                    </div>'''
                    popup = folium.Popup(popup_html, max_width=350)
                    
                    # Extract attack number for display
                    attack_match = re.search(r'#(\d+)', detail)
                    attack_num = attack_match.group(1) if attack_match else '🔫'
                    
                    icon_html = f'<div class="gun-attack-marker">{attack_num}</div>'
                    icon = folium.DivIcon(
                        html=icon_html,
                        icon_size=(24, 24),
                        icon_anchor=(12, 12)
                    )
                    folium.Marker([lat, lon], popup=popup, icon=icon).add_to(fg)
                else:
                    # Regular inferred positions - orange circle marker (smaller)
                    remarks_line = f'<br><i style="font-size:11px; color:#666;">{remarks}</i>' if remarks else ''
                    popup_html = f'''<div style="width:280px">
                        <b>P{patrol_num} Inferred Position</b><br>
                        {"<b>" + detail + "</b><br>" if detail else ""}
                        {date} {time}<br>
                        {pos_str}<br>
                        <i style="font-size:11px; color:#666;">Position derived from narrative</i>{remarks_line}{view_link}
                    </div>'''
                    popup = folium.Popup(popup_html, max_width=350)
                    folium.CircleMarker(
                        [lat, lon],
                        radius=6,
                        popup=popup,
                        color='#ff7f00',
                        fill=True,
                        fillColor='#ff7f00',
                        fillOpacity=0.8,
                        weight=2
                    ).add_to(fg)
                continue  # Skip the Marker below
            else:
                # Noon positions - green circle marker (smaller)
                remarks_html = f'<br><i style="font-size:11px; color:#666;">{remarks}</i>' if remarks else ''
                popup_html = f'''<div style="width:280px">
                    <b>P{patrol_num} Noon Position</b><br>
                    {date} {time}<br>
                    {pos_str}{remarks_html}{view_link}
                </div>'''
                popup = folium.Popup(popup_html, max_width=350)
                folium.CircleMarker(
                    [lat, lon],
                    radius=5,
                    popup=popup,
                    color='#4daf4a',
                    fill=True,
                    fillColor='#4daf4a',
                    fillOpacity=0.7,
                    weight=2
                ).add_to(fg)
        
        # Add the feature group to the map
        fg.add_to(m)
    
    # Add dynamic distance scale control
    class ScaleControl(MacroElement):
        _template = Template("""
            {% macro script(this, kwargs) %}
                L.control.scale({
                    metric: true,
                    imperial: true,
                    maxWidth: 200,
                    position: 'bottomright'
                }).addTo({{this._parent.get_name()}});
            {% endmacro %}
        """)
    
    ScaleControl().add_to(m)
    
    # Add click handler to show coordinates popup
    class ClickCoordinates(MacroElement):
        _template = Template("""
            {% macro script(this, kwargs) %}
                var clickPopup = null;
                {{this._parent.get_name()}}.on('click', function(e) {
                    var lat = e.latlng.lat;
                    var lng = e.latlng.lng;
                    
                    // Format as degrees and decimal minutes
                    var latHemi = lat >= 0 ? 'N' : 'S';
                    var lngHemi = lng >= 0 ? 'E' : 'W';
                    lat = Math.abs(lat);
                    lng = Math.abs(lng);
                    var latDeg = Math.floor(lat);
                    var latMin = ((lat - latDeg) * 60).toFixed(1);
                    var lngDeg = Math.floor(lng);
                    var lngMin = ((lng - lngDeg) * 60).toFixed(1);
                    
                    var content = '<div style="font-family: Arial; font-size: 13px;">' +
                        '<b>Position</b><br>' +
                        latDeg + '°' + latMin + "'" + latHemi + ' ' +
                        lngDeg + '°' + lngMin + "'" + lngHemi +
                        '<br><span style="font-size:11px; color:#666;">(' + 
                        e.latlng.lat.toFixed(5) + ', ' + e.latlng.lng.toFixed(5) + ')</span>' +
                        '</div>';
                    
                    if (clickPopup) {
                        {{this._parent.get_name()}}.closePopup(clickPopup);
                    }
                    clickPopup = L.popup()
                        .setLatLng(e.latlng)
                        .setContent(content)
                        .openOn({{this._parent.get_name()}});
                });
            {% endmacro %}
        """)
    
    ClickCoordinates().add_to(m)
    
    # Add layer control to toggle patrols
    folium.LayerControl(collapsed=False).add_to(m)
    
    # Add icon legend (contact types only, patrol colors are in layer control)
    legend_html = '''
    <div style="position: fixed; bottom: 50px; left: 50px; z-index: 1000;
                background-color: white; padding: 10px; border: 2px solid grey;
                border-radius: 5px; font-family: Arial;">
        <h4 style="margin: 0 0 10px 0;">Map Legend</h4>
        <div style="display:flex; align-items:center;"><span style="display:inline-block; width:14px; height:14px; border-radius:50% 50% 50% 0; background:#c0392b; margin-right:5px; transform:rotate(-45deg);"></span> Ship contact</div>
        <div style="display:flex; align-items:center;"><span style="display:inline-block; width:14px; height:14px; border-radius:50% 50% 50% 0; background:#2980b9; margin-right:5px; transform:rotate(-45deg);"></span> Aircraft contact</div>
        <div style="display:flex; align-items:center;"><span style="display:inline-block; width:10px; height:10px; border-radius:50%; background:#4daf4a; margin-right:5px;"></span> Noon position</div>
        <div style="display:flex; align-items:center;"><span style="display:inline-block; width:10px; height:10px; border-radius:50%; background:#ff7f00; margin-right:5px;"></span> Inferred position</div>
        <div style="display:flex; align-items:center;"><span style="display:inline-block; width:16px; height:16px; border-radius:3px; background:linear-gradient(135deg, #dc3545 0%, #ff6b6b 50%, #dc3545 100%); margin-right:5px; border:1px solid #a71d2a; font-size:9px; color:white; text-align:center; line-height:16px; font-weight:bold;">#</span> Torpedo attack</div>
        <div style="display:flex; align-items:center;"><span style="display:inline-block; width:16px; height:16px; border-radius:3px; background:linear-gradient(135deg, #495057 0%, #6c757d 50%, #495057 100%); margin-right:5px; border:1px solid #343a40; font-size:9px; color:white; text-align:center; line-height:16px; font-weight:bold;">#</span> Gun attack</div>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))
    
    return m

def main():
    print("Fetching positions from database...")
    positions = get_all_positions()
    print(f"  Found {len(positions)} total positions")
    
    # Count by patrol
    patrol_counts = {}
    for p in positions:
        patrol_num = p['patrol']
        patrol_counts[patrol_num] = patrol_counts.get(patrol_num, 0) + 1
    
    for patrol_num in sorted(patrol_counts.keys()):
        print(f"    Patrol {patrol_num}: {patrol_counts[patrol_num]} positions")
    
    print("\nGenerating map...")
    m = create_map(positions)
    
    output_file = 'static/patrol_tracks.html'
    m.save(output_file)
    
    # Inject SEO meta tags into the generated HTML
    with open(output_file, 'r') as f:
        html_content = f.read()
    
    seo_tags = '''
    <title>USS Cobia (SS-245) Patrol Track Maps | WWII Pacific Submarine Routes</title>
    <meta name="description" content="Interactive maps showing USS Cobia's six war patrols across the Pacific during WWII (1944-1945). View ship contacts, aircraft sightings, and patrol routes from Honolulu to the South China Sea.">
    <meta name="keywords" content="USS Cobia, SS-245, patrol map, submarine routes, WWII Pacific, war patrol tracks, interactive map">
    <meta name="robots" content="index, follow">
    <link rel="canonical" href="https://cobiapatrols.com/static/patrol_tracks.html">
    <meta property="og:type" content="website">
    <meta property="og:title" content="USS Cobia Patrol Track Maps - WWII Submarine Routes">
    <meta property="og:description" content="Interactive maps of USS Cobia's six war patrols in the Pacific (1944-1945).">
    <meta property="og:image" content="https://cobiapatrols.com/static/cobia.png">
    <meta property="og:url" content="https://cobiapatrols.com/static/patrol_tracks.html">
    <meta name="twitter:card" content="summary_large_image">
    <link rel="icon" type="image/svg+xml" href="/static/mapicon.svg">
    '''
    
    # Insert SEO tags after the opening <head> tag
    html_content = html_content.replace('<head>', '<head>' + seo_tags, 1)
    
    with open(output_file, 'w') as f:
        f.write(html_content)
    
    print(f"Map saved to {output_file}")

if __name__ == '__main__':
    main()

