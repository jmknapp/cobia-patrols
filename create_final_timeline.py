#!/usr/bin/env python3
"""Create timeline from parsed contact CSVs."""

import csv
from datetime import datetime
from collections import defaultdict
import re

REPORTS_DIR = "/home/jmknapp/cobia/patrolReports"

COLORS = {
    1: '#e41a1c', 2: '#377eb8', 3: '#4daf4a',
    4: '#984ea3', 5: '#ff7f00', 6: '#a65628',
}

def parse_date(date_str, year):
    """Parse date like '7/12' or '12 July'."""
    try:
        if '/' in str(date_str):
            month, day = str(date_str).split('/')
            return datetime(year, int(month), int(day))
        
        months = {'january':1,'february':2,'march':3,'april':4,'may':5,'june':6,
                  'july':7,'august':8,'september':9,'october':10,'november':11,'december':12}
        for name, num in months.items():
            if name in str(date_str).lower():
                day_match = re.search(r'(\d{1,2})', str(date_str))
                if day_match:
                    return datetime(year, num, int(day_match.group(1)))
    except:
        pass
    return None

def load_events():
    events = []
    
    # Ships
    with open(f'{REPORTS_DIR}/all_ship_contacts.csv') as f:
        for row in csv.DictReader(f):
            date = parse_date(row['date'], int(row['year']))
            if date:
                events.append({
                    'date': date,
                    'patrol': int(row['patrol']),
                    'type': 'ship',
                    'subtype': row['type'] or 'Ship',
                    'sunk': row['sunk'].lower() == 'true',
                    'contact_no': row['contact_no']
                })
    
    # Aircraft
    with open(f'{REPORTS_DIR}/all_aircraft_contacts.csv') as f:
        for row in csv.DictReader(f):
            date = parse_date(row['date'], int(row['year']))
            if date:
                events.append({
                    'date': date,
                    'patrol': int(row['patrol']),
                    'type': 'aircraft',
                    'subtype': row['type'] or 'Aircraft',
                    'friendly': row['friendly'].lower() == 'true',
                    'contact_no': row['contact_no']
                })
    
    return sorted(events, key=lambda x: x['date'])

def main():
    events = load_events()
    ships = [e for e in events if e['type'] == 'ship']
    aircraft = [e for e in events if e['type'] == 'aircraft']
    sunk = sum(1 for e in events if e.get('sunk'))
    
    print(f"Events: {len(events)} total, {len(ships)} ships, {len(aircraft)} aircraft, {sunk} sunk")
    
    # Group by date
    by_date = defaultdict(list)
    for e in events:
        by_date[e['date'].strftime('%Y-%m-%d')].append(e)
    
    html = f'''<!DOCTYPE html>
<html>
<head>
    <title>USS Cobia Timeline</title>
    <style>
        * {{ box-sizing: border-box; }}
        body {{ 
            font-family: 'Segoe UI', Arial, sans-serif; 
            margin: 0; padding: 20px; 
            background: linear-gradient(135deg, #1a1a2e, #16213e);
            min-height: 100vh; color: #eee;
        }}
        h1 {{ text-align: center; color: #f0d78c; margin-bottom: 5px; }}
        .subtitle {{ text-align: center; color: #aaa; margin-bottom: 20px; }}
        .stats {{ display: flex; justify-content: center; gap: 20px; margin-bottom: 20px; flex-wrap: wrap; }}
        .stat-box {{ background: rgba(255,255,255,0.1); padding: 15px 25px; border-radius: 10px; text-align: center; }}
        .stat-number {{ font-size: 28px; font-weight: bold; color: #f0d78c; }}
        .stat-label {{ font-size: 11px; color: #aaa; }}
        .legend {{ display: flex; justify-content: center; gap: 15px; margin-bottom: 25px; flex-wrap: wrap; }}
        .legend-item {{ display: flex; align-items: center; gap: 5px; padding: 4px 8px; 
                       background: rgba(255,255,255,0.1); border-radius: 4px; font-size: 12px; }}
        .timeline {{ max-width: 900px; margin: 0 auto; border-left: 3px solid #444; padding-left: 20px; }}
        .day {{ margin-bottom: 15px; }}
        .day-date {{ color: #f0d78c; font-weight: bold; margin-bottom: 5px; }}
        .event {{ background: rgba(255,255,255,0.08); padding: 8px 12px; border-radius: 5px; 
                 margin-bottom: 5px; display: flex; align-items: center; gap: 10px; }}
        .patrol-tag {{ font-size: 10px; padding: 2px 6px; border-radius: 3px; color: white; }}
        .ship {{ color: #4dabf7; }}
        .aircraft {{ color: #ffd43b; }}
        .sunk {{ color: #ff6b6b; font-weight: bold; }}
    </style>
</head>
<body>
    <h1>⚓ USS Cobia (SS-245) Contact Timeline</h1>
    <p class="subtitle">1944-1945 War Patrols</p>
    <div class="stats">
        <div class="stat-box"><div class="stat-number">{len(events)}</div><div class="stat-label">Total Contacts</div></div>
        <div class="stat-box"><div class="stat-number">{len(ships)}</div><div class="stat-label">Ship Contacts</div></div>
        <div class="stat-box"><div class="stat-number">{len(aircraft)}</div><div class="stat-label">Aircraft</div></div>
        <div class="stat-box"><div class="stat-number">{sunk}</div><div class="stat-label">Ships Sunk</div></div>
    </div>
    <div class="legend">
'''
    for pn, c in COLORS.items():
        html += f'<div class="legend-item"><div style="background:{c};width:12px;height:12px;border-radius:2px;"></div>Patrol {pn}</div>'
    
    html += '</div><div class="timeline">'
    
    for date_str in sorted(by_date.keys()):
        day_events = by_date[date_str]
        date_display = datetime.strptime(date_str, '%Y-%m-%d').strftime('%B %d, %Y')
        
        html += f'<div class="day"><div class="day-date">{date_display}</div>'
        for e in day_events:
            color = COLORS.get(e['patrol'], '#888')
            icon = '🚢' if e['type'] == 'ship' else '✈️'
            css_class = 'ship' if e['type'] == 'ship' else 'aircraft'
            extra = ' <span class="sunk">[SUNK]</span>' if e.get('sunk') else ''
            extra += ' (friendly)' if e.get('friendly') else ''
            
            html += f'''<div class="event">
                <span class="patrol-tag" style="background:{color}">P{e['patrol']}</span>
                <span class="{css_class}">{icon} {e['subtype']}{extra}</span>
            </div>'''
        html += '</div>'
    
    html += '</div></body></html>'
    
    with open(f'{REPORTS_DIR}/static/timeline.html', 'w') as f:
        f.write(html)
    print("Timeline saved!")

if __name__ == "__main__":
    main()
