import sqlite3
import os

def check_rooms():
    db_paths = [
        'timetable.db',
        'Routine5_lab_advanced/timetable.db'
    ]
    
    for db_path in db_paths:
        if os.path.exists(db_path):
            print(f"\n=== ROOMS IN {db_path} ===")
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Check theory rooms
                cursor.execute('SELECT id, name FROM theory_rooms ORDER BY name')
                theory_rooms = cursor.fetchall()
                print(f"Theory Rooms ({len(theory_rooms)}):")
                for room_id, name in theory_rooms:
                    print(f"  ID: {room_id}, Name: {name}")
                
                # Check lab rooms
                cursor.execute('SELECT id, name FROM lab_rooms ORDER BY name')
                lab_rooms = cursor.fetchall()
                print(f"\nLab Rooms ({len(lab_rooms)}):")
                for room_id, name in lab_rooms:
                    print(f"  ID: {room_id}, Name: {name}")
                
                conn.close()
                
            except Exception as e:
                print(f"Error reading {db_path}: {e}")
        else:
            print(f"\n{db_path} not found")

if __name__ == "__main__":
    check_rooms()