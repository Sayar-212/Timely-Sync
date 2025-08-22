import sqlite3

def setup_your_students():
    """Clean database and add your specific students"""
    conn = sqlite3.connect('attendance.db')
    cursor = conn.cursor()
    
    # Clean existing data
    cursor.execute('DELETE FROM attendance_records')
    cursor.execute('DELETE FROM attendance_sessions')
    cursor.execute('DELETE FROM students')
    print("🧹 Cleaned existing attendance data")
    
    # Your students for CSE-B class
    students = [
        (101, 'Anurima niggs', 'anurima.das.iotcs27@heritageit.edu.in', 'CSE101', 'cse-cse-b', 3),
        (102, 'Sayar Basu', 'sayar.basu.cse26@heritageit.edu.in', 'CSE102', 'cse-cse-b', 3),
        (103, 'Pradip Maity', 'pradip.maity.cse26@heritageit.edu.in', 'CSE103', 'cse-cse-b', 3),
        (104, 'Dedipta Saha', 'dedipta.saha.mba26@hbs.edu.in', 'CSE104', 'cse-cse-b', 3),
    ]
    
    for student in students:
        cursor.execute('''
            INSERT OR REPLACE INTO students (id, name, email, roll_number, class_id, semester)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', student)
    
    # Add room coordinates
    rooms = [
        ('303', 22.5184833, 88.4168668, 5),
        ('304', 22.5185000, 88.4169000, 5),
        ('305', 22.5185200, 88.4169300, 5),
        ('306', 22.5185400, 88.4169600, 5)
    ]
    
    # Create rooms table if not exists
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_number TEXT UNIQUE NOT NULL,
            latitude REAL,
            longitude REAL,
            radius INTEGER DEFAULT 5
        )
    ''')
    
    for room in rooms:
        cursor.execute('''
            INSERT OR REPLACE INTO rooms (room_number, latitude, longitude, radius)
            VALUES (?, ?, ?, ?)
        ''', room)
    
    conn.commit()
    conn.close()
    print("✅ Database cleaned and students added")
    print("📧 Fresh student list:")
    for student in students:
        print(f"   - {student[1]} ({student[2]})")
    print("\n🔄 Ready for new attendance sessions!")

if __name__ == "__main__":
    setup_your_students()