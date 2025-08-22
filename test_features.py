#!/usr/bin/env python3
"""
Test script for new features
"""

import sqlite3
import json
from datetime import datetime

def test_notice_board():
    """Test notice board functionality"""
    print("Testing notice board...")
    
    conn = sqlite3.connect('attendance.db')
    cursor = conn.cursor()
    
    # Insert a test notice
    cursor.execute('''
        INSERT INTO notice_board (title, content, type, published_by, timetable_data)
        VALUES (?, ?, ?, ?, ?)
    ''', (
        'Test Timetable Published',
        'This is a test notice for the new timetable system.',
        'timetable',
        'Test HOD',
        json.dumps({'test': True})
    ))
    
    # Fetch notices
    cursor.execute('''
        SELECT title, content, published_by, published_at, type
        FROM notice_board 
        WHERE is_active = 1 
        ORDER BY published_at DESC
    ''')
    
    notices = cursor.fetchall()
    print(f"Found {len(notices)} notices")
    for notice in notices:
        print(f"  - {notice[0]} by {notice[2]}")
    
    conn.commit()
    conn.close()

def test_rooms():
    """Test rooms functionality"""
    print("Testing rooms...")
    
    conn = sqlite3.connect('attendance.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT room_number, latitude, longitude FROM rooms ORDER BY room_number')
    rooms = cursor.fetchall()
    
    print(f"Found {len(rooms)} rooms:")
    for room in rooms:
        print(f"  - Room {room[0]}: ({room[1]}, {room[2]})")
    
    conn.close()

if __name__ == "__main__":
    print("Testing new features...")
    test_notice_board()
    test_rooms()
    print("Tests completed!")