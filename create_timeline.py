#!/usr/bin/env python3
"""
Create interactive timeline of USS Cobia contacts.
"""

import csv
import json
from collections import defaultdict
from datetime import datetime
import re

REPORTS_DIR = "/home/jmknapp/cobia/patrolReports"

# Patrol date ranges (approximate)
PATROL_DATES = {
    1: ("1944-06-25", "1944-08-20"),
    2: ("1944-09-05", "1944-11-10"),
    3: ("1945-01-01", "1945-02-15"),
    4: ("1945-03-10", "1945-05-15"),
    5: ("1945-05-10", "1945-07-10"),
    6: ("1945-07-15", "1945-08-15"),
}

COLORS = {
    1: '#e41a1c',
    2: '#377eb8',
    3: '#4daf4a',
    4: '#984ea3',
    5: '#ff7f00',
    6: '#a65628',
}

def parse_date(date_raw, year):
    """Parse date like '7/12' or '12 July' into datetime."""
    try:
        # Format: 7/12
        if '/' in date_raw:
            month, day = date_raw.split('/')
            return datetime(year, int(month), int(day))
        
        # Format: 12 July
        months = {
            'january': 1, 'february': 2, 'march': 3, 'april': 4,
            'may': 5, 'june': 6, 'july': 7, 'august': 8,
            'september': 9, 'october': 10, 'november': 11, 'december': 12
        }
        for month_name, month_num in months.items():
            if month_name in date_raw.lower():
                day_match = re.search(r'(\d{1,2})', date_raw)
                if day_match:
                    return datetime(year, month_num, int(day_match.group(1)))
    except:
        pass
    return None

def load_contacts():
    """Load all contacts and organize by date."""
    events = []
    
    # Load ship contacts
    try:
        with open(f'{REPORTS_DIR}/all_ship_contacts.csv', 'r') as f:
            for row in csv.DictReader(f):
                date = parse_date(row.get('date_raw', ''), int(row.get('year', 1944)))
                if date:
                    events.append({
                        'date': date,
                        'patrol': int(row['patrol']),
                        'type': 'ship',
                        'subtype': row.get('type', 'Unknown'),
                        'sunk': row.get('sunk', 'False').lower() == 'true',
                        'contact_no': row.get('contact_no', '')
                    })
    except Exception as e:
        print(f"Error loading ships: {e}")
    
    # Load aircraft contacts
    try:
        with open(f'{REPORTS_DIR}/all_aircraft_contacts.csv', 'r') as f:
            for row in csv.DictReader(f):
                date = parse_date(row.get('date', ''), int(row.get('year', 1944)))
                if date:
                    events.append({
                        'date': date,
                        'patrol': int(row['patrol']),
                        'type': 'aircraft',
                        'subtype': row.get('type', 'Unknown'),
                        'friendly': row.get('friendly', 'False').lower() == 'true',
                        'contact_no': row.get('contact_no', '')
                    })
    except Exception as e:
        print(f"Error loading aircraft: {e}")
    
    return sorted(events, key=lambda x: x['date'])

def create_timeline_html(events):
    """Create HTML timeline visualization."""
    
    # Group events by date
    by_date = defaultdict(list)
    for e in events:
        date_str = e['date'].strftime('%Y-%m-%d')
        by_date[date_str].append(e)
    
    # Create HTML
    html = '''<!DOCTYPE html>
<html>
<head>
    <title>USS Cobia Timeline</title>
    <style>
        * { box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', Arial, sans-serif; 
            margin: 0; 
            padding: 20px; 
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            color: #eee;
        }
        h1 { 
            text-align: center; 
            color: #f0d78c;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
            margin-bottom: 10px;
        }
        .subtitle {
            text-align: center;
            color: #aaa;
            margin-bottom: 30px;
        }
        .legend {
            display: flex;
            justify-content: center;
            gap: 20px;
            margin-bottom: 30px;
            flex-wrap: wrap;
        }
        .legend-item {
            display: flex;
            align-items: center;
            gap: 5px;
            padding: 5px 10px;
            background: rgba(255,255,255,0.1);
            border-radius: 5px;
        }
        .legend-color {
            width: 15px;
            height: 15px;
            border-radius: 3px;
        }
        .timeline-container {
            max-width: 1200px;
            margin: 0 auto;
            position: relative;
        }
        .timeline-line {
            position: absolute;
            left: 50%;
            transform: translateX(-50%);
            width: 4px;
            height: 100%;
            background: #444;
        }
        .timeline-event {
            display: flex;
            margin-bottom: 20px;
            position: relative;
        }
        .timeline-event:nth-child(odd) {
            flex-direction: row-reverse;
        }
        .event-date {
            width: 45%;
            text-align: right;
            padding-right: 30px;
            font-weight: bold;
            color: #f0d78c;
        }
        .timeline-event:nth-child(odd) .event-date {
            text-align: left;
            padding-left: 30px;
            padding-right: 0;
        }
        .event-content {
            width: 45%;
            padding-left: 30px;
            border-left: 3px solid #444;
        }
        .timeline-event:nth-child(odd) .event-content {
            padding-right: 30px;
            padding-left: 0;
            border-left: none;
            border-right: 3px solid #444;
            text-align: right;
        }
        .event-dot {
            position: absolute;
            left: 50%;
            transform: translateX(-50%);
            width: 16px;
            height: 16px;
            border-radius: 50%;
            border: 3px solid #1a1a2e;
            z-index: 1;
        }
        .event-card {
            background: rgba(255,255,255,0.1);
            padding: 10px 15px;
            border-radius: 8px;
            display: inline-block;
        }
        .ship { color: #4dabf7; }
        .aircraft { color: #ffd43b; }
        .sunk { color: #ff6b6b; font-weight: bold; }
        .patrol-tag {
            font-size: 11px;
            padding: 2px 6px;
            border-radius: 3px;
            margin-right: 5px;
        }
        .stats {
            display: flex;
            justify-content: center;
            gap: 30px;
            margin-bottom: 30px;
            flex-wrap: wrap;
        }
        .stat-box {
            background: rgba(255,255,255,0.1);
            padding: 15px 25px;
            border-radius: 10px;
            text-align: center;
        }
        .stat-number {
            font-size: 32px;
            font-weight: bold;
            color: #f0d78c;
        }
        .stat-label {
            font-size: 12px;
            color: #aaa;
        }
    </style>
</head>
<body>
    <h1>⚓ USS Cobia (SS-245) Contact Timeline</h1>
    <p class="subtitle">1944-1945 War Patrols</p>
    
    <div class="stats">
'''
    
    # Add stats
    ship_count = sum(1 for e in events if e['type'] == 'ship')
    aircraft_count = sum(1 for e in events if e['type'] == 'aircraft')
    sunk_count = sum(1 for e in events if e.get('sunk', False))
    
    html += f'''
        <div class="stat-box">
            <div class="stat-number">{len(events)}</div>
            <div class="stat-label">Total Contacts</div>
        </div>
        <div class="stat-box">
            <div class="stat-number">{ship_count}</div>
            <div class="stat-label">Ship Contacts</div>
        </div>
        <div class="stat-box">
            <div class="stat-number">{aircraft_count}</div>
            <div class="stat-label">Aircraft Contacts</div>
        </div>
        <div class="stat-box">
            <div class="stat-number">{sunk_count}</div>
            <div class="stat-label">Ships Sunk</div>
        </div>
    </div>
    
    <div class="legend">
'''
    
    for patrol_num, color in COLORS.items():
        html += f'<div class="legend-item"><div class="legend-color" style="background:{color}"></div>Patrol {patrol_num}</div>'
    
    html += '''
    </div>
    
    <div class="timeline-container">
        <div class="timeline-line"></div>
'''
    
    # Add events grouped by date
    for date_str in sorted(by_date.keys()):
        day_events = by_date[date_str]
        date_display = datetime.strptime(date_str, '%Y-%m-%d').strftime('%B %d, %Y')
        color = COLORS.get(day_events[0]['patrol'], '#888')
        
        html += f'''
        <div class="timeline-event">
            <div class="event-date">{date_display}</div>
            <div class="event-dot" style="background:{color}"></div>
            <div class="event-content">
                <div class="event-card">
'''
        
        for e in day_events:
            patrol_color = COLORS.get(e['patrol'], '#888')
            icon = '🚢' if e['type'] == 'ship' else '✈️'
            sunk_text = ' <span class="sunk">[SUNK]</span>' if e.get('sunk') else ''
            friendly = ' (friendly)' if e.get('friendly') else ''
            
            html += f'''
                    <div>
                        <span class="patrol-tag" style="background:{patrol_color}">P{e['patrol']}</span>
                        {icon} {e['subtype'] or e['type']}{friendly}{sunk_text}
                    </div>
'''
        
        html += '''
                </div>
            </div>
        </div>
'''
    
    html += '''
    </div>
</body>
</html>
'''
    
    return html

def main():
    events = load_contacts()
    print(f"Loaded {len(events)} contacts with valid dates")
    
    # Count by type
    ships = [e for e in events if e['type'] == 'ship']
    aircraft = [e for e in events if e['type'] == 'aircraft']
    print(f"  Ships: {len(ships)}")
    print(f"  Aircraft: {len(aircraft)}")
    
    # Create timeline
    html = create_timeline_html(events)
    
    output_path = f'{REPORTS_DIR}/static/timeline.html'
    with open(output_path, 'w') as f:
        f.write(html)
    
    print(f"\nTimeline saved: {output_path}")
    print(f"View at: http://localhost:5003/static/timeline.html")

if __name__ == "__main__":
    main()
