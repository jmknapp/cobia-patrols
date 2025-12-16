#!/usr/bin/env python3
"""
Refresh the positions table from the Excel file.

Usage:
    python refresh_positions.py
"""

import mysql.connector
import pandas as pd
import os

EXCEL_FILE = os.path.join(os.path.dirname(__file__), 'Cobia_positions.xlsx')

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

def refresh_positions():
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
    cursor.execute("DELETE FROM positions")

    insert_sql = """
        INSERT INTO positions 
        (patrol, position_no, observation_time, timezone, observation_date, 
         latitude_deg, latitude_min, latitude_hemisphere,
         longitude_deg, longitude_min, longitude_hemisphere,
         latitude, longitude, position_type)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    rows_inserted = 0
    for idx, row in df.iterrows():
        # Skip rows with missing patrol number (empty rows)
        if pd.isna(row['patrol']) or safe_int(row['patrol']) is None:
            continue
            
        lat_deg = safe_int(row['latitude deg'])
        lat_min = safe_int(row['latitude min'])
        lon_deg = safe_int(row['longitude deg'])
        lon_min = safe_int(row['longitude min'])
        
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
        
        values = (
            safe_int(row['patrol']),
            safe_int(row['number']),
            obs_time,
            safe_int(row['timezone']),
            obs_date,
            lat_deg, lat_min, lat_hem,
            lon_deg, lon_min, lon_hem,
            latitude, longitude,
            safe_str(row['type'])
        )
        
        cursor.execute(insert_sql, values)
        rows_inserted += 1

    conn.commit()

    # Summary
    cursor.execute("""
        SELECT patrol, position_type, COUNT(*) 
        FROM positions 
        GROUP BY patrol, position_type 
        ORDER BY patrol, position_type
    """)
    print(f"\nInserted {rows_inserted} total rows:")
    current_patrol = None
    for row in cursor.fetchall():
        if row[0] != current_patrol:
            current_patrol = row[0]
            print(f"  Patrol {row[0]}:")
        print(f"    {row[1]}: {row[2]}")

    cursor.close()
    conn.close()
    print("\nDone!")
    return True

if __name__ == '__main__':
    refresh_positions()

