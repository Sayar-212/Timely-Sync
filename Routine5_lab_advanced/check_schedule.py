import sqlite3

conn = sqlite3.connect('timetable.db')
cursor = conn.cursor()

# Check existing schedules
cursor.execute('''
    SELECT gs.section_id, gs.day, gs.time_slot, s.name, 
           CASE WHEN tr.name IS NOT NULL THEN tr.name ELSE lr.name END as room_name,
           gs.room_type
    FROM generated_schedules gs
    JOIN subjects s ON gs.subject_id = s.id
    LEFT JOIN theory_rooms tr ON gs.room_id = tr.id AND gs.room_type = 'theory'
    LEFT JOIN lab_rooms lr ON gs.room_id = lr.id AND gs.room_type = 'lab'
    ORDER BY gs.section_id, gs.day, gs.time_slot
''')

schedules = cursor.fetchall()
print(f"Total scheduled classes: {len(schedules)}")

# Group by room to see distribution
room_usage = {}
for section_id, day, time_slot, subject, room_name, room_type in schedules:
    if room_name not in room_usage:
        room_usage[room_name] = 0
    room_usage[room_name] += 1

print("\nRoom usage distribution:")
for room, count in sorted(room_usage.items()):
    print(f"  {room}: {count} classes")

conn.close()