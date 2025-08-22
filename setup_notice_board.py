#!/usr/bin/env python3
"""
Setup script for Notice Board functionality
"""

import sqlite3
import json
from datetime import datetime

def setup_notice_board_tables():
    """Create notice board and room tables"""
    conn = sqlite3.connect('attendance.db')
    cursor = conn.cursor()
    
    # Create notice board table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notice_board (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            type TEXT DEFAULT 'timetable',
            published_by TEXT NOT NULL,
            published_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT 1,
            timetable_data TEXT
        )
    ''')
    
    # Create rooms table with coordinates
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_number TEXT UNIQUE NOT NULL,
            latitude REAL,
            longitude REAL,
            radius INTEGER DEFAULT 5
        )
    ''')
    
    # Insert default rooms
    rooms = [
        ('303', 22.5184833, 88.4168668, 5),
        ('304', 22.5185000, 88.4169000, 5),
        ('305', 22.5185200, 88.4169300, 5),
        ('306', 22.5185400, 88.4169600, 5),
        ('307', 22.5185600, 88.4169900, 5)
    ]
    
    for room in rooms:
        cursor.execute('''
            INSERT OR REPLACE INTO rooms (room_number, latitude, longitude, radius)
            VALUES (?, ?, ?, ?)
        ''', room)
    
    conn.commit()
    conn.close()
    print("Notice board and rooms tables created successfully")

if __name__ == "__main__":
    setup_notice_board_tables()