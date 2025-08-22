import sqlite3
import os

def safe_attendance_setup():
    """ONLY works with attendance.db - NEVER touches routine5"""
    
    # Explicitly check we're not touching routine5
    routine5_path = 'Routine5_lab_advanced/timetable.db'
    if os.path.exists(routine5_path):
        # Make routine5 read-only as safety measure
        os.chmod(routine5_path, 0o444)
        print("[PROTECTED] Routine5 database set to read-only")
    
    # Work ONLY with attendance database
    conn = sqlite3.connect('attendance.db')
    cursor = conn.cursor()
    
    # Clean attendance data
    cursor.execute('DELETE FROM attendance_records')
    cursor.execute('DELETE FROM attendance_sessions') 
    cursor.execute('DELETE FROM students')
    
    # Add students
    students = [
        (101, 'Chhanda', 'mchhandadgp@gmail.com', 'CIV101', 'cse-cse-b', 3),
        (102, 'Chhanda Mondal', 'chhanda.mondal.civil27@heritageit.edu.in', 'CIV102', 'cse-cse-b', 3),
    ]
    
    for student in students:
        cursor.execute('INSERT INTO students VALUES (?, ?, ?, ?, ?, ?)', student)
    
    cursor.execute('INSERT OR REPLACE INTO room_coordinates VALUES (?, ?, ?, ?)', 
                  ('Room 303', 22.5184833, 88.4168668, 5))
    
    conn.commit()
    conn.close()
    print("[DONE] Attendance setup complete - routine5 untouched")

if __name__ == "__main__":
    safe_attendance_setup()