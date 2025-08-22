import sqlite3
import sys
import os

# Use EXACT same database as Routine5 folder
DB_PATH = 'Routine5_lab_advanced/timetable.db'

def setup_attendance_only():
    """Setup attendance with EXACT routine5 database - no changes"""
    
    # Setup attendance database separately
    att_conn = sqlite3.connect('attendance.db')
    att_cursor = att_conn.cursor()
    
    att_cursor.execute('DELETE FROM attendance_records')
    att_cursor.execute('DELETE FROM attendance_sessions')
    att_cursor.execute('DELETE FROM students')
    
    students = [
        (101, 'Chhanda', 'mchhandadgp@gmail.com', 'CIV101', 'cse-cse-b', 3),
        (102, 'Chhanda Mondal', 'chhanda.mondal.civil27@heritageit.edu.in', 'CIV102', 'cse-cse-b', 3),
    ]
    
    for student in students:
        att_cursor.execute('INSERT INTO students VALUES (?, ?, ?, ?, ?, ?)', student)
    
    att_cursor.execute('INSERT OR REPLACE INTO room_coordinates VALUES (?, ?, ?, ?)', 
                      ('Room 303', 22.5184833, 88.4168668, 5))
    
    att_conn.commit()
    att_conn.close()
    
    # Check routine5 database is untouched
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT name FROM theory_rooms')
    rooms = cursor.fetchall()
    cursor.execute('SELECT name FROM subjects LIMIT 3')
    subjects = cursor.fetchall()
    conn.close()
    
    print("ROUTINE5 DATABASE STATUS:")
    print(f"Theory rooms: {[r[0] for r in rooms]}")
    print(f"Sample subjects: {[s[0] for s in subjects]}")
    print("ATTENDANCE SETUP COMPLETE - ROUTINE5 UNTOUCHED")

if __name__ == "__main__":
    setup_attendance_only()