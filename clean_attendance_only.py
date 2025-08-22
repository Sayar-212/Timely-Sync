import sqlite3
import os

def clean_setup():
    """Complete fresh start - attendance only"""
    
    # Remove any altered files
    if os.path.exists('attendance.db'):
        os.remove('attendance.db')
    
    # Create fresh attendance database
    conn = sqlite3.connect('attendance.db')
    cursor = conn.cursor()
    
    # Create tables
    cursor.executescript('''
        CREATE TABLE students (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            roll_number TEXT UNIQUE NOT NULL,
            class_id TEXT NOT NULL,
            semester INTEGER NOT NULL
        );
        
        CREATE TABLE attendance_sessions (
            id TEXT PRIMARY KEY,
            class_id TEXT NOT NULL,
            class_name TEXT NOT NULL,
            room TEXT NOT NULL,
            teacher_lat REAL NOT NULL,
            teacher_lng REAL NOT NULL,
            radius INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ended_at TIMESTAMP,
            is_active BOOLEAN DEFAULT 1
        );
        
        CREATE TABLE attendance_records (
            id INTEGER PRIMARY KEY,
            session_id TEXT NOT NULL,
            student_id INTEGER NOT NULL,
            marked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            student_lat REAL,
            student_lng REAL,
            distance REAL,
            status TEXT DEFAULT 'present',
            client_ip TEXT,
            FOREIGN KEY (session_id) REFERENCES attendance_sessions (id),
            FOREIGN KEY (student_id) REFERENCES students (id)
        );
        
        CREATE TABLE room_coordinates (
            room_number TEXT PRIMARY KEY,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            radius INTEGER DEFAULT 50
        );
    ''')
    
    # Add students
    students = [
        (101, 'Chhanda', 'mchhandadgp@gmail.com', 'CIV101', 'cse-cse-b', 3),
        (102, 'Chhanda Mondal', 'chhanda.mondal.civil27@heritageit.edu.in', 'CIV102', 'cse-cse-b', 3),
    ]
    
    for student in students:
        cursor.execute('INSERT INTO students VALUES (?, ?, ?, ?, ?, ?)', student)
    
    cursor.execute('INSERT INTO room_coordinates VALUES (?, ?, ?, ?)', 
                  ('Room 303', 22.5184833, 88.4168668, 5))
    
    conn.commit()
    conn.close()
    print("FRESH ATTENDANCE DATABASE CREATED")
    print("ROUTINE5 FOLDER COMPLETELY UNTOUCHED")

if __name__ == "__main__":
    clean_setup()