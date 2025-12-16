#!/usr/bin/env python3
"""
Refresh the inferred_positions table from Cobia_inferred_positions.xlsx
"""

import pandas as pd
import mysql.connector
from datetime import datetime

def refresh_inferred_positions():
    # Read Excel file
    df = pd.read_excel('Cobia_inferred_positions.xlsx')
    print(f"Read {len(df)} rows from Cobia_inferred_positions.xlsx")
    
    # Connect to database
    from db_config import get_db_connection
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Drop and recreate table
    cursor.execute("DROP TABLE IF EXISTS inferred_positions")
    
    cursor.execute("""
        CREATE TABLE inferred_positions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            patrol INT NOT NULL,
            number INT,
            observation_time VARCHAR(10),
            timezone INT,
            observation_date DATE,
            latitude DECIMAL(10, 6),
            longitude DECIMAL(10, 6),
            tag VARCHAR(255),
            INDEX idx_patrol (patrol),
            INDEX idx_date (observation_date)
        )
    """)
    print("Created inferred_positions table")
    
    # Insert data
    insert_sql = """
        INSERT INTO inferred_positions 
        (patrol, number, observation_time, timezone, observation_date, 
         latitude, longitude, tag)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    
    inserted = 0
    for _, row in df.iterrows():
        # Skip rows where patrol is null
        if pd.isna(row['patrol']):
            continue
            
        # Format observation time as string (e.g., "0830")
        obs_time = str(int(row['observation time'])).zfill(4) if pd.notna(row['observation time']) else None
        
        # Format date
        obs_date = row['observation date'].date() if pd.notna(row['observation date']) else None
        
        values = (
            int(row['patrol']),
            int(row['number']) if pd.notna(row['number']) else None,
            obs_time,
            int(row['timezone']) if pd.notna(row['timezone']) else None,
            obs_date,
            float(row['latitude']) if pd.notna(row['latitude']) else None,
            float(row['longitude']) if pd.notna(row['longitude']) else None,
            row['tag'] if pd.notna(row['tag']) else None
        )
        
        cursor.execute(insert_sql, values)
        inserted += 1
    
    conn.commit()
    print(f"Inserted {inserted} rows")
    
    # Verify
    cursor.execute("SELECT COUNT(*) FROM inferred_positions")
    count = cursor.fetchone()[0]
    print(f"Table now has {count} rows")
    
    # Show sample
    cursor.execute("""
        SELECT patrol, number, observation_date, observation_time, 
               latitude, longitude, tag 
        FROM inferred_positions 
        ORDER BY patrol, number
        LIMIT 10
    """)
    print("\nSample data:")
    for row in cursor.fetchall():
        print(f"  P{row[0]} #{row[1]}: {row[2]} {row[3]} - {row[4]:.4f}, {row[5]:.4f} - {row[6]}")
    
    cursor.close()
    conn.close()

if __name__ == '__main__':
    refresh_inferred_positions()


