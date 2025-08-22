import sqlite3
import os

def show_rooms(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print(f"\n=== ROOMS IN {db_path} ===")
    
    cursor.execute('SELECT id, name FROM theory_rooms ORDER BY id')
    theory_rooms = cursor.fetchall()
    print(f"Theory Rooms:")
    for room_id, name in theory_rooms:
        print(f"  ID: {room_id}, Name: {name}")
    
    cursor.execute('SELECT id, name FROM lab_rooms ORDER BY id')
    lab_rooms = cursor.fetchall()
    print(f"Lab Rooms:")
    for room_id, name in lab_rooms:
        print(f"  ID: {room_id}, Name: {name}")
    
    conn.close()
    return theory_rooms, lab_rooms

def delete_rooms(db_path):
    theory_rooms, lab_rooms = show_rooms(db_path)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("\nEnter room IDs to delete (comma-separated) or 'q' to quit:")
    print("Format: theory:1,2,3 lab:4,5,6")
    
    user_input = input("Delete: ").strip()
    if user_input.lower() == 'q':
        conn.close()
        return
    
    try:
        parts = user_input.split()
        for part in parts:
            if ':' in part:
                room_type, ids = part.split(':', 1)
                id_list = [int(x.strip()) for x in ids.split(',') if x.strip()]
                
                if room_type.lower() == 'theory':
                    for room_id in id_list:
                        cursor.execute('DELETE FROM theory_rooms WHERE id = ?', (room_id,))
                        print(f"Deleted theory room ID {room_id}")
                
                elif room_type.lower() == 'lab':
                    for room_id in id_list:
                        cursor.execute('DELETE FROM lab_rooms WHERE id = ?', (room_id,))
                        print(f"Deleted lab room ID {room_id}")
        
        conn.commit()
        print("\nRooms deleted successfully!")
        show_rooms(db_path)
        
    except Exception as e:
        print(f"Error: {e}")
    
    conn.close()

if __name__ == "__main__":
    db_paths = ['timetable.db', 'Routine5_lab_advanced/timetable.db']
    
    for db_path in db_paths:
        if os.path.exists(db_path):
            print(f"\n{'='*50}")
            print(f"DATABASE: {db_path}")
            delete_rooms(db_path)