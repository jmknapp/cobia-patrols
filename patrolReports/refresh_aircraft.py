#!/usr/bin/env python3
"""
Refresh the aircraft_contacts table from the Excel file.

Usage:
    python refresh_aircraft.py
"""

import mysql.connector
import pandas as pd
import os

EXCEL_FILE = os.path.join(os.path.dirname(__file__), 'Cobia_aircraft_contacts.xlsx')

def safe_int(val):
    if pd.isna(val) or val == '' or (isinstance(val, str) and val.strip() == ''):
        return None
    return int(float(val))

def safe_float(val):
    if pd.isna(val) or val == '' or (isinstance(val, str) and val.strip() == ''):
        return None
    return float(val)

def safe_str(val):
    if pd.isna(val) or val == '' or (isinstance(val, str) and val.strip() == ''):
        return None
    return str(val).strip()

def refresh_aircraft():
    # Read the Excel file
    if not os.path.exists(EXCEL_FILE):
        print(f"Error: Excel file not found: {EXCEL_FILE}")
        return False
    
    df = pd.read_excel(EXCEL_FILE)
    print(f"Read {df.shape[0]} rows from {os.path.basename(EXCEL_FILE)}")

    # Connect to MySQL
    from db_config import get_db_connection
    conn = get_db_connection()
    cursor = conn.cursor()

    # Clear and reload
    cursor.execute("DELETE FROM aircraft_contacts")

    insert_sql = """
        INSERT INTO aircraft_contacts 
        (patrol, contact_no, observation_time, timezone, observation_date, 
         latitude_deg, latitude_min, latitude_hemisphere,
         longitude_deg, longitude_min, longitude_hemisphere,
         latitude, longitude, aircraft_type, range_miles, course, speed, 
         method, elevation_angle, probable_mission)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    rows_inserted = 0
    for idx, row in df.iterrows():
        # Skip rows with missing patrol number (empty rows)
        if pd.isna(row['patrol']) or safe_int(row['patrol']) is None:
            continue
            
        lat_deg = safe_int(row['latitude deg'])
        lat_min = safe_float(row['latitude min'])
        lon_deg = safe_int(row['longitude deg'])
        lon_min = safe_float(row['longitude min'])
        
        # Get hemispheres
        lat_hem = safe_str(row.get('latitude hemisphere', 'N'))
        lon_hem = safe_str(row.get('longitude hemisphere', 'E'))
        if lat_hem:
            lat_hem = lat_hem.upper()[0]
        else:
            lat_hem = 'N'
        if lon_hem:
            lon_hem = lon_hem.upper()[0]
        else:
            lon_hem = 'E'
        
        # Calculate decimal lat/lon with hemisphere
        latitude = None
        longitude = None
        if lat_deg is not None and lat_min is not None:
            latitude = lat_deg + lat_min / 60.0
            if lat_hem == 'S':
                latitude = -latitude
        if lon_deg is not None and lon_min is not None:
            longitude = lon_deg + lon_min / 60.0
            if lon_hem == 'W':
                longitude = -longitude
        
        obs_time = None
        if pd.notna(row['observation time']):
            try:
                obs_time = str(int(float(row['observation time']))).zfill(4)
            except:
                obs_time = safe_str(row['observation time'])
        
        obs_date = row['observation date'].date() if pd.notna(row['observation date']) else None
        
        # Contact can be string like "26a", "26b"
        contact_val = row['contact']
        if pd.notna(contact_val):
            contact_str = str(contact_val).strip()
            # Remove ".0" if it's a float converted to string
            if contact_str.endswith('.0'):
                contact_str = contact_str[:-2]
        else:
            contact_str = None
        
        values = (
            safe_int(row['patrol']),
            contact_str,
            obs_time,
            safe_float(row['timezone']),
            obs_date,
            lat_deg, lat_min, lat_hem,
            lon_deg, lon_min, lon_hem,
            latitude, longitude,
            safe_str(row['type']),
            safe_int(row['miles range']),
            safe_int(row['course']),
            safe_float(row['speed']),
            safe_str(row['method']),
            safe_float(row['elevation angle']),
            safe_str(row.get('Probable mission') or row.get('probable mission'))
        )
        
        cursor.execute(insert_sql, values)
        rows_inserted += 1

    conn.commit()

    # Summary
    cursor.execute("SELECT patrol, COUNT(*) FROM aircraft_contacts GROUP BY patrol ORDER BY patrol")
    print(f"\nInserted {rows_inserted} total rows:")
    for row in cursor.fetchall():
        print(f"  Patrol {row[0]}: {row[1]} contacts")

    cursor.close()
    conn.close()
    print("\nDone!")
    return True

if __name__ == '__main__':
    refresh_aircraft()

