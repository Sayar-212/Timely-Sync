from flask import Flask, render_template, request, jsonify, send_file
import sqlite3
from datetime import datetime
import os
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch
import random
import requests
from io import BytesIO
from lab_scheduler import check_consecutive_lab_times

app = Flask(__name__)

def init_db():
    conn = sqlite3.connect('timetable_original.db')
    cursor = conn.cursor()
    
    # Drop existing tables if they exist
    cursor.execute('DROP TABLE IF EXISTS generated_schedules')
    cursor.execute('DROP TABLE IF EXISTS teacher_semester_assignments')
    cursor.execute('DROP TABLE IF EXISTS primary_assignments')
    cursor.execute('DROP TABLE IF EXISTS subject_teachers')
    cursor.execute('DROP TABLE IF EXISTS subjects')
    cursor.execute('DROP TABLE IF EXISTS semesters')
    cursor.execute('DROP TABLE IF EXISTS sections')
    cursor.execute('DROP TABLE IF EXISTS years')
    cursor.execute('DROP TABLE IF EXISTS departments')
    cursor.execute('DROP TABLE IF EXISTS theory_rooms')
    cursor.execute('DROP TABLE IF EXISTS lab_rooms')
    
    cursor.executescript('''
        CREATE TABLE departments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            code TEXT NOT NULL UNIQUE,
            program_duration INTEGER CHECK (program_duration BETWEEN 2 AND 4)
        );
        
        CREATE TABLE years (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            department_id INTEGER NOT NULL,
            year_number INTEGER CHECK (year_number BETWEEN 1 AND 4),
            section_count INTEGER CHECK (section_count >= 1),
            FOREIGN KEY (department_id) REFERENCES departments(id)
        );
        
        CREATE TABLE sections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            year_id INTEGER NOT NULL,
            section_label TEXT NOT NULL,
            FOREIGN KEY (year_id) REFERENCES years(id)
        );
        
        CREATE TABLE semesters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            year_id INTEGER NOT NULL,
            semester_number INTEGER NOT NULL,
            semester_type TEXT CHECK (semester_type IN ('odd', 'even')),
            is_active BOOLEAN DEFAULT FALSE,
            FOREIGN KEY (year_id) REFERENCES years(id)
        );
        
        CREATE TABLE theory_rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        );
        
        CREATE TABLE lab_rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        );
        
        CREATE TABLE subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            semester_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            type TEXT CHECK (type IN ('theory', 'practical')),
            credits INTEGER CHECK (credits BETWEEN 1 AND 4),
            lab_duration INTEGER DEFAULT NULL,
            FOREIGN KEY (semester_id) REFERENCES semesters(id)
        );
        
        CREATE TABLE subject_teachers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_id INTEGER NOT NULL,
            teacher_name TEXT NOT NULL,
            unavailable_day TEXT CHECK (unavailable_day IN ('monday', 'tuesday', 'wednesday', 'thursday', 'friday')),
            FOREIGN KEY (subject_id) REFERENCES subjects(id)
        );
        
        CREATE TABLE primary_assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_id INTEGER NOT NULL,
            section_id INTEGER NOT NULL,
            teacher_id INTEGER NOT NULL,
            assignment_type TEXT CHECK (assignment_type IN ('theory_primary', 'lab_primary')),
            is_matched_assignment BOOLEAN DEFAULT FALSE,
            FOREIGN KEY (subject_id) REFERENCES subjects(id),
            FOREIGN KEY (section_id) REFERENCES sections(id),
            FOREIGN KEY (teacher_id) REFERENCES subject_teachers(id)
        );
        
        CREATE TABLE teacher_semester_assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher_name TEXT NOT NULL,
            semester_id INTEGER NOT NULL,
            section_id INTEGER NOT NULL,
            subject_id INTEGER NOT NULL,
            subject_type TEXT CHECK (subject_type IN ('theory', 'practical')),
            is_matched_assignment BOOLEAN DEFAULT FALSE,
            FOREIGN KEY (semester_id) REFERENCES semesters(id),
            FOREIGN KEY (section_id) REFERENCES sections(id),
            FOREIGN KEY (subject_id) REFERENCES subjects(id),
            UNIQUE (teacher_name, semester_id, section_id)
        );
        
        CREATE TABLE generated_schedules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            section_id INTEGER NOT NULL,
            day TEXT,
            time_slot TEXT,
            subject_id INTEGER,
            teacher_id INTEGER,
            room_id INTEGER,
            room_type TEXT,
            FOREIGN KEY (section_id) REFERENCES sections(id)
        );
    ''')
    
    conn.commit()
    conn.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/get_departments')
def get_departments():
    if not os.path.exists('timetable.db'):
        return jsonify([])
    
    conn = sqlite3.connect('timetable.db', timeout=30)
    conn.execute('PRAGMA journal_mode=WAL')
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT id, name, code, program_duration FROM departments')
        departments = []
        for row in cursor.fetchall():
            departments.append({
                'id': row[0],
                'name': row[1],
                'code': row[2],
                'duration': row[3]
            })
        return jsonify(departments)
    except Exception as e:
        return jsonify([])
    finally:
        conn.close()

@app.route('/api/check_system_status')
def check_system_status():
    if not os.path.exists('timetable.db'):
        return jsonify({'configured': False})
    
    conn = sqlite3.connect('timetable.db', timeout=30)
    conn.execute('PRAGMA journal_mode=WAL')
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT COUNT(*) FROM departments')
        dept_count = cursor.fetchone()[0]
        
        if dept_count == 0:
            return jsonify({'configured': False})
        
        cursor.execute('SELECT id FROM departments LIMIT 1')
        dept_id = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM sections sec JOIN years y ON sec.year_id = y.id WHERE y.department_id = ?', (dept_id,))
        section_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM subjects s JOIN semesters sem ON s.semester_id = sem.id JOIN years y ON sem.year_id = y.id WHERE y.department_id = ?', (dept_id,))
        subject_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(DISTINCT teacher_name) FROM subject_teachers st JOIN subjects s ON st.subject_id = s.id JOIN semesters sem ON s.semester_id = sem.id JOIN years y ON sem.year_id = y.id WHERE y.department_id = ?', (dept_id,))
        teacher_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT (SELECT COUNT(*) FROM theory_rooms) + (SELECT COUNT(*) FROM lab_rooms)')
        room_count = cursor.fetchone()[0]
        
        return jsonify({
            'configured': True,
            'department_id': dept_id,
            'sections': section_count,
            'subjects': subject_count,
            'teachers': teacher_count,
            'rooms': room_count
        })
    except Exception as e:
        return jsonify({'configured': False})
    finally:
        conn.close()

@app.route('/setup')
def setup():
    # Initialize DB if it doesn't exist
    if not os.path.exists('timetable.db'):
        init_db()
    
    dept_id = request.args.get('dept_id')
    if dept_id:
        # Modify existing department - go directly to subjects
        return render_template('setup.html', modify_dept_id=dept_id)
    
    return render_template('setup.html')

@app.route('/api/save_department', methods=['POST'])
def save_department():
    data = request.json
    conn = sqlite3.connect('timetable.db', timeout=30)
    conn.execute('PRAGMA journal_mode=WAL')
    cursor = conn.cursor()
    
    try:
        # Check if exact same department exists
        cursor.execute('SELECT id FROM departments WHERE name = ? AND code = ? AND program_duration = ?',
                      (data['name'], data['code'], data['duration']))
        existing_dept = cursor.fetchone()
        
        if existing_dept:
            dept_id = existing_dept[0]
            # Check if years/sections match
            cursor.execute('SELECT year_number, section_count FROM years WHERE department_id = ? ORDER BY year_number',
                          (dept_id,))
            existing_years = cursor.fetchall()
            
            # Compare with new data
            new_years = [(i+1, count) for i, count in enumerate(data['sections']) if count > 0]
            
            if existing_years == new_years:
                return jsonify({'success': True, 'department_id': dept_id, 'skip_sections': True})
        
        # New department or different structure - clear and recreate
        cursor.execute('DELETE FROM departments WHERE name = ? OR code = ?', (data['name'], data['code']))
        
        cursor.execute('INSERT INTO departments (name, code, program_duration) VALUES (?, ?, ?)',
                      (data['name'], data['code'], data['duration']))
        dept_id = cursor.lastrowid
        
        for year_num, section_count in enumerate(data['sections'], 1):
            if section_count > 0:
                cursor.execute('INSERT INTO years (department_id, year_number, section_count) VALUES (?, ?, ?)',
                              (dept_id, year_num, section_count))
                year_id = cursor.lastrowid
                
                for i in range(section_count):
                    section_label = chr(65 + i)
                    cursor.execute('INSERT INTO sections (year_id, section_label) VALUES (?, ?)',
                                  (year_id, section_label))
        
        conn.commit()
        return jsonify({'success': True, 'department_id': dept_id, 'skip_sections': False})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
    finally:
        conn.close()

@app.route('/api/save_rooms', methods=['POST'])
def save_rooms():
    data = request.json
    conn = sqlite3.connect('timetable.db', timeout=30)
    conn.execute('PRAGMA journal_mode=WAL')
    cursor = conn.cursor()
    
    try:
        for room in data['theory_rooms']:
            cursor.execute('INSERT OR IGNORE INTO theory_rooms (name) VALUES (?)', (room,))
        
        for room in data['lab_rooms']:
            cursor.execute('INSERT OR IGNORE INTO lab_rooms (name) VALUES (?)', (room,))
        
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
    finally:
        conn.close()

@app.route('/api/setup_semester', methods=['POST'])
def setup_semester():
    data = request.json
    conn = sqlite3.connect('timetable.db', timeout=30)
    conn.execute('PRAGMA journal_mode=WAL')
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT id, year_number FROM years WHERE department_id = ?', (data['department_id'],))
        years = cursor.fetchall()
        
        for year_id, year_number in years:
            if data['semester_type'] == 'odd':
                semester_number = (year_number * 2) - 1
            else:
                semester_number = year_number * 2
            
            cursor.execute('INSERT OR REPLACE INTO semesters (year_id, semester_number, semester_type, is_active) VALUES (?, ?, ?, ?)',
                          (year_id, semester_number, data['semester_type'], True))
        
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
    finally:
        conn.close()

@app.route('/api/get_semesters/<int:dept_id>')
def get_semesters(dept_id):
    conn = sqlite3.connect('timetable.db', timeout=30)
    conn.execute('PRAGMA journal_mode=WAL')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT s.id, s.semester_number, y.year_number, y.section_count, s.semester_type
        FROM semesters s
        JOIN years y ON s.year_id = y.id
        WHERE y.department_id = ? AND s.is_active = 1
        ORDER BY s.semester_number
    ''', (dept_id,))
    
    semesters = []
    for row in cursor.fetchall():
        semesters.append({
            'id': row[0],
            'semester_number': row[1],
            'year_number': row[2],
            'section_count': row[3],
            'semester_type': row[4]
        })
    
    conn.close()
    return jsonify(semesters)

@app.route('/api/save_subject', methods=['POST'])
def save_subject():
    data = request.json
    conn = sqlite3.connect('timetable.db', timeout=30)
    conn.execute('PRAGMA journal_mode=WAL')
    cursor = conn.cursor()
    
    try:
        # Check if subject already exists
        cursor.execute('SELECT id FROM subjects WHERE semester_id = ? AND name = ? AND type = ?',
                      (data['semester_id'], data['name'], data['type']))
        existing = cursor.fetchone()
        
        if existing:
            # Re-assign teachers to ensure all sections get this subject
            auto_assign_teachers(existing[0], data['semester_id'])
            return jsonify({'success': True, 'message': 'Subject already exists, assignments updated'})
        
        cursor.execute('INSERT INTO subjects (semester_id, name, type, credits, lab_duration) VALUES (?, ?, ?, ?, ?)',
                      (data['semester_id'], data['name'], data['type'], data['credits'], data.get('lab_duration')))
        subject_id = cursor.lastrowid
        
        for teacher in data['teachers']:
            cursor.execute('INSERT OR IGNORE INTO subject_teachers (subject_id, teacher_name, unavailable_day) VALUES (?, ?, ?)',
                          (subject_id, teacher['name'], teacher['unavailable_day']))
        
        conn.commit()
        # CRITICAL: Assign this subject to ALL sections in the semester
        auto_assign_teachers(subject_id, data['semester_id'])
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
    finally:
        conn.close()

def auto_assign_teachers(subject_id, semester_id):
    conn = sqlite3.connect('timetable.db', timeout=30)
    conn.execute('PRAGMA journal_mode=WAL')
    cursor = conn.cursor()
    
    cursor.execute('SELECT name, type FROM subjects WHERE id = ?', (subject_id,))
    result = cursor.fetchone()
    if not result:
        conn.close()
        return
    subject_name, subject_type = result
    
    cursor.execute('''
        SELECT sec.id FROM sections sec
        JOIN years y ON sec.year_id = y.id
        JOIN semesters s ON s.year_id = y.id
        WHERE s.id = ?
    ''', (semester_id,))
    sections = cursor.fetchall()
    
    cursor.execute('SELECT id, teacher_name FROM subject_teachers WHERE subject_id = ?', (subject_id,))
    teachers = cursor.fetchall()
    
    if not teachers:
        conn.close()
        return
    
    # Theory-Lab matching logic
    if subject_type == 'practical' and subject_name.endswith(' Lab'):
        theory_name = subject_name.replace(' Lab', '')
        
        cursor.execute('''
            SELECT s.id FROM subjects s
            JOIN semesters sem ON s.semester_id = sem.id
            WHERE s.name = ? AND s.type = 'theory' AND sem.id = ?
        ''', (theory_name, semester_id))
        theory_subject = cursor.fetchone()
        
        if theory_subject:
            cursor.execute('''
                SELECT pa.section_id, st.teacher_name, st.id
                FROM primary_assignments pa
                JOIN subject_teachers st ON pa.teacher_id = st.id
                WHERE pa.subject_id = ?
            ''', (theory_subject[0],))
            theory_assignments = cursor.fetchall() or []
            
            # Ensure ALL sections get the lab, even if no theory assignment exists
            assigned_sections = set()
            for section_id, teacher_name, teacher_id in theory_assignments:
                cursor.execute('SELECT id FROM subject_teachers WHERE subject_id = ? AND teacher_name = ?',
                              (subject_id, teacher_name))
                lab_teacher = cursor.fetchone()
                
                if lab_teacher:
                    cursor.execute('INSERT OR REPLACE INTO primary_assignments (subject_id, section_id, teacher_id, assignment_type, is_matched_assignment) VALUES (?, ?, ?, ?, ?)',
                                  (subject_id, section_id, lab_teacher[0], 'lab_primary', True))
                    
                    cursor.execute('INSERT OR IGNORE INTO teacher_semester_assignments (teacher_name, semester_id, section_id, subject_id, subject_type, is_matched_assignment) VALUES (?, ?, ?, ?, ?, ?)',
                                  (teacher_name, semester_id, section_id, subject_id, 'practical', True))
                    assigned_sections.add(section_id)
            
            # Assign remaining sections that didn't get matched assignments
            remaining_sections = [(s[0],) for s in sections if s[0] not in assigned_sections]
            for i, (section_id,) in enumerate(remaining_sections):
                teacher_idx = i % len(teachers)
                teacher_id, teacher_name = teachers[teacher_idx]
                
                cursor.execute('INSERT OR REPLACE INTO primary_assignments (subject_id, section_id, teacher_id, assignment_type, is_matched_assignment) VALUES (?, ?, ?, ?, ?)',
                              (subject_id, section_id, teacher_id, 'lab_primary', False))
                
                cursor.execute('INSERT OR IGNORE INTO teacher_semester_assignments (teacher_name, semester_id, section_id, subject_id, subject_type, is_matched_assignment) VALUES (?, ?, ?, ?, ?, ?)',
                              (teacher_name, semester_id, section_id, subject_id, subject_type, False))
            
            conn.commit()
            conn.close()
            return
    
    # Regular assignment - ENSURE ALL SECTIONS GET THIS SUBJECT
    for i, (section_id,) in enumerate(sections):
        teacher_idx = i % len(teachers)  # Round-robin assignment
        teacher_id, teacher_name = teachers[teacher_idx]
        assignment_type = 'theory_primary' if subject_type == 'theory' else 'lab_primary'
        
        cursor.execute('INSERT OR REPLACE INTO primary_assignments (subject_id, section_id, teacher_id, assignment_type, is_matched_assignment) VALUES (?, ?, ?, ?, ?)',
                      (subject_id, section_id, teacher_id, assignment_type, False))
        
        cursor.execute('INSERT OR IGNORE INTO teacher_semester_assignments (teacher_name, semester_id, section_id, subject_id, subject_type, is_matched_assignment) VALUES (?, ?, ?, ?, ?, ?)',
                      (teacher_name, semester_id, section_id, subject_id, subject_type, False))
    
    conn.commit()
    conn.close()

@app.route('/api/get_subject/<int:subject_id>')
def get_subject(subject_id):
    conn = sqlite3.connect('timetable.db', timeout=30)
    conn.execute('PRAGMA journal_mode=WAL')
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT name, type, credits, lab_duration, semester_id FROM subjects WHERE id = ?', (subject_id,))
        subject = cursor.fetchone()
        
        if not subject:
            return jsonify({'success': False, 'error': 'Subject not found'})
        
        cursor.execute('SELECT teacher_name, unavailable_day FROM subject_teachers WHERE subject_id = ?', (subject_id,))
        teachers = cursor.fetchall()
        
        return jsonify({
            'success': True,
            'subject': {
                'id': subject_id,
                'name': subject[0],
                'type': subject[1],
                'credits': subject[2],
                'lab_duration': subject[3],
                'semester_id': subject[4],
                'teachers': [{'name': t[0], 'unavailable_day': t[1]} for t in teachers]
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
    finally:
        conn.close()

@app.route('/api/update_subject/<int:subject_id>', methods=['PUT'])
def update_subject(subject_id):
    data = request.json
    conn = sqlite3.connect('timetable.db', timeout=30)
    conn.execute('PRAGMA journal_mode=WAL')
    cursor = conn.cursor()
    
    try:
        # Update subject
        cursor.execute('UPDATE subjects SET name = ?, type = ?, credits = ?, lab_duration = ? WHERE id = ?',
                      (data['name'], data['type'], data['credits'], data.get('lab_duration'), subject_id))
        
        # Remove old teachers and assignments
        cursor.execute('DELETE FROM primary_assignments WHERE subject_id = ?', (subject_id,))
        cursor.execute('DELETE FROM teacher_semester_assignments WHERE subject_id = ?', (subject_id,))
        cursor.execute('DELETE FROM subject_teachers WHERE subject_id = ?', (subject_id,))
        
        # Add new teachers
        for teacher in data['teachers']:
            cursor.execute('INSERT INTO subject_teachers (subject_id, teacher_name, unavailable_day) VALUES (?, ?, ?)',
                          (subject_id, teacher['name'], teacher['unavailable_day']))
        
        conn.commit()
        auto_assign_teachers(subject_id, data['semester_id'])
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
    finally:
        conn.close()

@app.route('/api/remove_subject/<int:subject_id>', methods=['DELETE'])
def remove_subject(subject_id):
    conn = sqlite3.connect('timetable.db', timeout=30)
    conn.execute('PRAGMA journal_mode=WAL')
    cursor = conn.cursor()
    
    try:
        # Remove related data first
        cursor.execute('DELETE FROM primary_assignments WHERE subject_id = ?', (subject_id,))
        cursor.execute('DELETE FROM teacher_semester_assignments WHERE subject_id = ?', (subject_id,))
        cursor.execute('DELETE FROM subject_teachers WHERE subject_id = ?', (subject_id,))
        cursor.execute('DELETE FROM subjects WHERE id = ?', (subject_id,))
        
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
    finally:
        conn.close()

@app.route('/api/get_subjects/<int:semester_id>')
def get_subjects(semester_id):
    conn = sqlite3.connect('timetable.db', timeout=30)
    conn.execute('PRAGMA journal_mode=WAL')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT s.id, s.name, s.type, s.credits, s.lab_duration,
               COUNT(st.id) as teacher_count,
               (SELECT COUNT(*) FROM sections sec
                JOIN years y ON sec.year_id = y.id
                JOIN semesters sem ON sem.year_id = y.id
                WHERE sem.id = ?) as section_count
        FROM subjects s
        LEFT JOIN subject_teachers st ON s.id = st.subject_id
        WHERE s.semester_id = ?
        GROUP BY s.id
    ''', (semester_id, semester_id))
    
    subjects = []
    for row in cursor.fetchall():
        subjects.append({
            'id': row[0],
            'name': row[1],
            'type': row[2],
            'credits': row[3],
            'lab_duration': row[4],
            'teacher_count': row[5],
            'section_count': row[6],
            'status': 'complete' if row[5] >= row[6] else 'incomplete'
        })
    
    conn.close()
    return jsonify(subjects)

@app.route('/api/generate_timetable', methods=['POST'])
def generate_timetable():
    data = request.json
    dept_id = data['department_id']
    
    conn = None
    try:
        conn = sqlite3.connect('timetable.db', timeout=60)
        conn.execute('PRAGMA journal_mode=DELETE')
        conn.execute('PRAGMA synchronous=NORMAL')
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM generated_schedules')
        conn.commit()
        
        cursor.execute('''
            SELECT s.id, s.semester_number, y.year_number
            FROM semesters s
            JOIN years y ON s.year_id = y.id
            WHERE y.department_id = ? AND s.is_active = 1
        ''', (dept_id,))
        semesters = cursor.fetchall()
        
        total_sections = 0
        
        # Initialize GLOBAL room schedule for ALL sections
        cursor.execute('SELECT id, name FROM theory_rooms')
        theory_rooms = cursor.fetchall()
        cursor.execute('SELECT id, name FROM lab_rooms')
        lab_rooms = cursor.fetchall()
        
        time_slots = ['09:00-10:00', '10:00-11:00', '11:00-12:00', '12:00-13:00', '13:00-14:00', '14:00-15:00', '15:00-16:00', '16:00-17:00']
        days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']
        
        global_room_schedule = {}
        for room_id, room_name in theory_rooms + lab_rooms:
            global_room_schedule[room_id] = {day: {slot: None for slot in time_slots} for day in days}
        
        # Room rotation counters for even distribution
        theory_room_counter = 0
        lab_room_counter = 0
        
        for semester_id, semester_number, year_number in semesters:
            cursor.execute('''
                SELECT sec.id, sec.section_label
                FROM sections sec
                JOIN years y ON sec.year_id = y.id
                JOIN semesters s ON s.year_id = y.id
                WHERE s.id = ?
            ''', (semester_id,))
            sections = cursor.fetchall()
            
            total_sections += len(sections)
            
            for section_id, section_label in sections:
                theory_room_counter, lab_room_counter = generate_section_schedule_inline(conn, section_id, semester_id, global_room_schedule, theory_room_counter, lab_room_counter, theory_rooms, lab_rooms)
        
        conn.commit()
        conn.close()
        conn = None
        
        pdf_files = generate_pdf_schedules(dept_id)
        
        return jsonify({
            'success': True,
            'total_sections': total_sections,
            'pdf_count': len(pdf_files)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
    finally:
        if conn:
            try:
                conn.close()
            except:
                pass

def generate_section_schedule_inline(conn, section_id, semester_id, global_room_schedule=None, theory_room_counter=0, lab_room_counter=0, theory_rooms=None, lab_rooms=None):
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT s.id, s.name, s.type, s.credits, s.lab_duration,
               pa.teacher_id, st.teacher_name, st.unavailable_day
        FROM subjects s
        JOIN primary_assignments pa ON s.id = pa.subject_id
        JOIN subject_teachers st ON pa.teacher_id = st.id
        WHERE s.semester_id = ? AND pa.section_id = ?
    ''', (semester_id, section_id))
    
    subjects = cursor.fetchall()
    
    cursor.execute('SELECT id, name FROM theory_rooms')
    theory_rooms = cursor.fetchall()
    cursor.execute('SELECT id, name FROM lab_rooms')
    lab_rooms = cursor.fetchall()
    
    time_slots = ['09:00-10:00', '10:00-11:00', '11:00-12:00', '12:00-13:00', '13:00-14:00', '14:00-15:00', '15:00-16:00', '16:00-17:00']
    days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']
    
    # Initialize tracking structures
    schedule = {day: {slot: None for slot in time_slots} for day in days}
    teacher_schedule = {}
    teacher_weekly_count = {}
    teacher_lab_sessions = {}
    section_has_double = False  # Track if section already has a double lecture this week
    daily_lab_count = {day: 0 for day in days}  # Track labs per day per section
    section_lab_times = {}  # Track lab time slots used by this section
    
    # Use global room schedule if provided, otherwise initialize local one
    if global_room_schedule is None:
        all_room_schedule = {}
        for room_id, room_name in theory_rooms + lab_rooms:
            all_room_schedule[room_id] = {day: {slot: None for slot in time_slots} for day in days}
    else:
        all_room_schedule = global_room_schedule
    
    # Get lab schedule for SAME SEMESTER SAME SUBJECT to avoid conflicts within semester
    cursor.execute('''
        SELECT gs.subject_id, gs.day 
        FROM generated_schedules gs
        JOIN subjects s ON gs.subject_id = s.id
        WHERE s.type = "practical" AND s.semester_id = ?
    ''', (semester_id,))
    existing_lab_schedule = {}
    for subj_id, day in cursor.fetchall():
        if subj_id not in existing_lab_schedule:
            existing_lab_schedule[subj_id] = set()
        existing_lab_schedule[subj_id].add(day)
    
    # Get GLOBAL teacher schedule to prevent teacher conflicts across ALL sections/semesters
    cursor.execute('''
        SELECT st.teacher_name, gs.day, gs.time_slot
        FROM generated_schedules gs
        JOIN subject_teachers st ON gs.teacher_id = st.id
    ''')
    global_teacher_schedule = {}
    for teacher_name, day, time_slot in cursor.fetchall():
        if teacher_name not in global_teacher_schedule:
            global_teacher_schedule[teacher_name] = {}
        if day not in global_teacher_schedule[teacher_name]:
            global_teacher_schedule[teacher_name][day] = set()
        global_teacher_schedule[teacher_name][day].add(time_slot)
    
    # Sort subjects: labs first, then theory by credits (distribute evenly)
    theory_subjects = [s for s in subjects if s[2] == 'theory']
    lab_subjects = [s for s in subjects if s[2] == 'practical']
    
    # Schedule labs first (higher priority)
    for subject_id, name, subject_type, credits, lab_duration, teacher_id, teacher_name, unavailable_day in lab_subjects:
        lab_hours = lab_duration or 2
        scheduled = False
        
        # Sort days to enforce morning/afternoon alternation for labs
        available_days = [d for d in days if d != unavailable_day and daily_lab_count[d] < 1]
        
        # Check if we need morning or afternoon based on adjacent days
        morning_slots = ['09:00-10:00', '10:00-11:00', '11:00-12:00']
        afternoon_slots = ['13:00-14:00', '14:00-15:00', '15:00-16:00', '16:00-17:00']
        
        prefer_morning = True
        for day in available_days:
            day_idx = days.index(day)
            # Check previous day
            if day_idx > 0:
                prev_day = days[day_idx - 1]
                if prev_day in section_lab_times:
                    prev_is_morning = any(slot in morning_slots for slot in section_lab_times[prev_day])
                    prefer_morning = not prev_is_morning
                    break
            # Check next day
            if day_idx < len(days) - 1:
                next_day = days[day_idx + 1]
                if next_day in section_lab_times:
                    next_is_morning = any(slot in morning_slots for slot in section_lab_times[next_day])
                    prefer_morning = not next_is_morning
                    break
        
        # Remove days where this subject already has labs (other sections)
        if subject_id in existing_lab_schedule:
            available_days = [d for d in available_days if d not in existing_lab_schedule[subject_id]]
        
        # If no unique days available, use any available day
        if not available_days:
            available_days = [d for d in days if d != unavailable_day and daily_lab_count[d] < 1]
        
        for day in available_days:
            if scheduled:
                break
                
            # Find CONSECUTIVE slots for lab based on morning/afternoon preference
            start_range = range(len(time_slots) - lab_hours + 1) if not prefer_morning else range(3 - lab_hours + 1)
            if not prefer_morning:
                start_range = range(4, len(time_slots) - lab_hours + 1)  # Start from 13:00
            
            for i in start_range:
                if time_slots[i] == '12:00-13:00':
                    continue
                    
                slots_available = True
                temp_slots = []
                
                # Check consecutive slots
                for j in range(lab_hours):
                    slot = time_slots[i + j]
                    if (slot == '12:00-13:00' or 
                        schedule[day][slot] is not None or
                        teacher_schedule.get(teacher_name, {}).get(day, {}).get(slot) or
                        slot in global_teacher_schedule.get(teacher_name, {}).get(day, set())):
                        slots_available = False
                        break
                    temp_slots.append(slot)
                
                # Ensure we have exactly the required consecutive slots
                if not (slots_available and len(temp_slots) == lab_hours):
                    continue
                
                # Check for consecutive lab times on adjacent days and implement smart scheduling
                consecutive_conflict = check_consecutive_lab_times(day, temp_slots, section_lab_times, days)
                
                # If conflict exists, try to schedule in opposite time slot (morning->afternoon, afternoon->morning)
                if consecutive_conflict:
                    # Check if we can schedule in opposite time slot
                    current_is_morning = any(slot in ['09:00-10:00', '10:00-11:00', '11:00-12:00'] for slot in temp_slots)
                    
                    if current_is_morning:
                        # Try afternoon slots (13:00 onwards)
                        afternoon_start = next((i for i, slot in enumerate(time_slots) if slot == '13:00-14:00'), -1)
                        if afternoon_start != -1 and afternoon_start + lab_hours - 1 < len(time_slots):
                            afternoon_slots = []
                            slots_available = True
                            for j in range(lab_hours):
                                slot = time_slots[afternoon_start + j]
                                if (schedule[day][slot] is not None or
                                    teacher_schedule.get(teacher_name, {}).get(day, {}).get(slot) or
                                    slot in global_teacher_schedule.get(teacher_name, {}).get(day, set())):
                                    slots_available = False
                                    break
                                afternoon_slots.append(slot)
                            
                            if slots_available and len(afternoon_slots) == lab_hours:
                                temp_slots = afternoon_slots
                            else:
                                continue  # Skip this day if can't find afternoon slot
                    else:
                        # Try morning slots (before 12:00)
                        morning_slots = []
                        slots_available = True
                        for j in range(lab_hours):
                            if j >= 3:  # Only 3 morning slots available
                                slots_available = False
                                break
                            slot = time_slots[j]
                            if (schedule[day][slot] is not None or
                                teacher_schedule.get(teacher_name, {}).get(day, {}).get(slot) or
                                slot in global_teacher_schedule.get(teacher_name, {}).get(day, set())):
                                slots_available = False
                                break
                            morning_slots.append(slot)
                        
                        if slots_available and len(morning_slots) == lab_hours:
                            temp_slots = morning_slots
                        else:
                            continue  # Skip this day if can't find morning slot
                
                if slots_available and len(temp_slots) == lab_hours:
                    # Allocate lab room dynamically (prefer lab rooms, fallback to theory)
                    room_id = None
                    room_type = None
                    
                    # Use lab rooms only - random selection
                    room_id = None
                    room_type = 'lab'
                    
                    # Shuffle lab rooms for random selection
                    shuffled_labs = lab_rooms.copy()
                    random.shuffle(shuffled_labs)
                    
                    for room in shuffled_labs:
                        room_available = True
                        for slot in temp_slots:
                            if all_room_schedule[room[0]][day][slot] is not None:
                                room_available = False
                                break
                        if room_available:
                            room_id = room[0]
                            break
                    
                    if room_id:
                        # Schedule lab
                        for slot in temp_slots:
                            schedule[day][slot] = {
                                'subject_id': subject_id, 'subject_name': name,
                                'teacher_id': teacher_id, 'teacher_name': teacher_name,
                                'room_id': room_id, 'type': 'lab'
                            }
                            
                            # Update tracking
                            if teacher_name not in teacher_schedule:
                                teacher_schedule[teacher_name] = {}
                            if day not in teacher_schedule[teacher_name]:
                                teacher_schedule[teacher_name][day] = {}
                            teacher_schedule[teacher_name][day][slot] = True
                            
                            # Update room schedule
                            all_room_schedule[room_id][day][slot] = f'{name}_{section_id}'
                            
                            cursor.execute('''
                                INSERT INTO generated_schedules 
                                (section_id, day, time_slot, subject_id, teacher_id, room_id, room_type)
                                VALUES (?, ?, ?, ?, ?, ?, ?)
                            ''', (section_id, day, slot, subject_id, teacher_id, room_id, room_type))
                        
                        # Mark teacher lab session and mandatory break
                        if teacher_name not in teacher_lab_sessions:
                            teacher_lab_sessions[teacher_name] = {}
                        teacher_lab_sessions[teacher_name][day] = temp_slots[-1]
                        
                        # Block next hour for mandatory break
                        next_slot_idx = time_slots.index(temp_slots[-1]) + 1
                        if next_slot_idx < len(time_slots) and time_slots[next_slot_idx] != '12:00-13:00':
                            if day not in teacher_schedule[teacher_name]:
                                teacher_schedule[teacher_name][day] = {}
                            teacher_schedule[teacher_name][day][time_slots[next_slot_idx]] = 'BREAK'
                        
                        # Update section lab times tracking
                        if day not in section_lab_times:
                            section_lab_times[day] = set()
                        section_lab_times[day].update(temp_slots)
                        
                        # Update global lab tracking
                        if subject_id not in existing_lab_schedule:
                            existing_lab_schedule[subject_id] = set()
                        existing_lab_schedule[subject_id].add(day)
                        
                        daily_lab_count[day] += 1
                        scheduled = True
                        break
                
                if scheduled:
                    break
        
        # If lab still not scheduled, try again without consecutive time restriction
        if not scheduled:
            for day in available_days:
                if scheduled:
                    break
                    
                for i in range(len(time_slots) - lab_hours + 1):
                    if time_slots[i] == '12:00-13:00':
                        continue
                        
                    slots_available = True
                    temp_slots = []
                    
                    for j in range(lab_hours):
                        slot = time_slots[i + j]
                        if (slot == '12:00-13:00' or 
                            schedule[day][slot] is not None or
                            teacher_schedule.get(teacher_name, {}).get(day, {}).get(slot) or
                            slot in global_teacher_schedule.get(teacher_name, {}).get(day, set())):
                            slots_available = False
                            break
                        temp_slots.append(slot)
                    
                    if slots_available and len(temp_slots) == lab_hours:
                        room_id = None
                        room_type = 'lab'
                        
                        shuffled_labs = lab_rooms.copy()
                        random.shuffle(shuffled_labs)
                        
                        for room in shuffled_labs:
                            room_available = True
                            for slot in temp_slots:
                                if all_room_schedule[room[0]][day][slot] is not None:
                                    room_available = False
                                    break
                            if room_available:
                                room_id = room[0]
                                break
                        
                        if room_id:
                            for slot in temp_slots:
                                schedule[day][slot] = {
                                    'subject_id': subject_id, 'subject_name': name,
                                    'teacher_id': teacher_id, 'teacher_name': teacher_name,
                                    'room_id': room_id, 'type': 'lab'
                                }
                                
                                if teacher_name not in teacher_schedule:
                                    teacher_schedule[teacher_name] = {}
                                if day not in teacher_schedule[teacher_name]:
                                    teacher_schedule[teacher_name][day] = {}
                                teacher_schedule[teacher_name][day][slot] = True
                                
                                all_room_schedule[room_id][day][slot] = f'{name}_{section_id}'
                                
                                cursor.execute('''
                                    INSERT INTO generated_schedules 
                                    (section_id, day, time_slot, subject_id, teacher_id, room_id, room_type)
                                    VALUES (?, ?, ?, ?, ?, ?, ?)
                                ''', (section_id, day, slot, subject_id, teacher_id, room_id, room_type))
                            
                            if teacher_name not in teacher_lab_sessions:
                                teacher_lab_sessions[teacher_name] = {}
                            teacher_lab_sessions[teacher_name][day] = temp_slots[-1]
                            
                            next_slot_idx = time_slots.index(temp_slots[-1]) + 1
                            if next_slot_idx < len(time_slots) and time_slots[next_slot_idx] != '12:00-13:00':
                                if day not in teacher_schedule[teacher_name]:
                                    teacher_schedule[teacher_name][day] = {}
                                teacher_schedule[teacher_name][day][time_slots[next_slot_idx]] = 'BREAK'
                            
                            if day not in section_lab_times:
                                section_lab_times[day] = set()
                            section_lab_times[day].update(temp_slots)
                            
                            if subject_id not in existing_lab_schedule:
                                existing_lab_schedule[subject_id] = set()
                            existing_lab_schedule[subject_id].add(day)
                            
                            daily_lab_count[day] += 1
                            scheduled = True
                            break
                    
                    if scheduled:
                        break
    
    # Schedule theory subjects with proper credit distribution
    for subject_id, name, subject_type, credits, lab_duration, teacher_id, teacher_name, unavailable_day in theory_subjects:
        classes_scheduled = 0
        
        # Theory subject MUST be taught exactly 'credits' hours per week
        required_classes = credits  # Always use full credits, no reduction
        
        # Only allow double lectures as last resort when absolutely necessary
        double_scheduled = False
        # First try to schedule all classes as singles, only use doubles if can't complete required classes
        
        # Schedule single classes distributed across the week for better mixing
        daily_subject_count = {day: 0 for day in days}
        subject_time_slots = []  # Track which time slots this subject has used
        
        while classes_scheduled < required_classes:
            scheduled_this_round = False
            
            # Sort days by daily load for balanced distribution across week
            sorted_days = sorted(days, key=lambda d: (
                sum(1 for slot in time_slots if schedule[d].get(slot) and slot != '12:00-13:00'),  # Total classes per day (primary)
                daily_subject_count[d]  # Prefer days with fewer subjects for this subject
            ))
            
            for day in sorted_days:
                if day == unavailable_day or classes_scheduled >= required_classes:
                    continue
                    
                # Check if this subject already has a class on this day
                subject_on_day = any(schedule[day].get(slot) and schedule[day][slot].get('subject_name') == name 
                                   for slot in time_slots)
                
                # Strictly avoid same subject same day
                if subject_on_day:
                    continue
                
                # Sort time slots for variety - prefer unused time slots for this subject
                available_slots = [slot for slot in time_slots if slot != '12:00-13:00']
                sorted_slots = sorted(available_slots, key=lambda s: (
                    s in subject_time_slots,  # Prefer new time slots
                    time_slots.index(s)  # Then by time order
                ))
                    
                for slot in sorted_slots:
                    if (schedule[day][slot] is not None or
                        teacher_schedule.get(teacher_name, {}).get(day, {}).get(slot) or
                        slot in global_teacher_schedule.get(teacher_name, {}).get(day, set()) or
                        classes_scheduled >= required_classes):
                        continue
                    
                    # Check for mandatory break after lab
                    if (teacher_name in teacher_lab_sessions and 
                        day in teacher_lab_sessions[teacher_name]):
                        lab_end_slot = teacher_lab_sessions[teacher_name][day]
                        lab_end_idx = time_slots.index(lab_end_slot)
                        current_idx = time_slots.index(slot)
                        if current_idx == lab_end_idx + 1:
                            continue
                    
                    # PREVENT CONSECUTIVE CLASSES for same subject
                    current_idx = time_slots.index(slot)
                    
                    # Check previous slot
                    if current_idx > 0:
                        prev_slot = time_slots[current_idx - 1]
                        if (schedule[day].get(prev_slot) and 
                            schedule[day][prev_slot].get('subject_name') == name):
                            continue
                    
                    # Check next slot
                    if current_idx < len(time_slots) - 1:
                        next_slot = time_slots[current_idx + 1]
                        if (schedule[day].get(next_slot) and 
                            schedule[day][next_slot].get('subject_name') == name):
                            continue
                    
                    # Use theory rooms - random selection
                    room_id = None
                    
                    # Shuffle theory rooms for random selection
                    shuffled_theory = theory_rooms.copy()
                    random.shuffle(shuffled_theory)
                    
                    for room in shuffled_theory:
                        if all_room_schedule[room[0]][day][slot] is None:
                            room_id = room[0]
                            break
                    
                    if room_id:
                        schedule[day][slot] = {
                            'subject_id': subject_id, 'subject_name': name,
                            'teacher_id': teacher_id, 'teacher_name': teacher_name,
                            'room_id': room_id, 'type': 'theory'
                        }
                        
                        # Update tracking
                        if teacher_name not in teacher_schedule:
                            teacher_schedule[teacher_name] = {}
                        if day not in teacher_schedule[teacher_name]:
                            teacher_schedule[teacher_name][day] = {}
                        teacher_schedule[teacher_name][day][slot] = True
                        
                        # Update room schedule
                        all_room_schedule[room_id][day][slot] = f'{name}_{section_id}'
                        
                        classes_scheduled += 1
                        daily_subject_count[day] += 1
                        subject_time_slots.append(slot)  # Track time slot usage
                        scheduled_this_round = True
                        
                        cursor.execute('''
                            INSERT INTO generated_schedules 
                            (section_id, day, time_slot, subject_id, teacher_id, room_id, room_type)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        ''', (section_id, day, slot, subject_id, teacher_id, room_id, 'theory'))
                        
                        break
                
                if scheduled_this_round:
                    break
            
            # If can't schedule more, try relaxing constraints
            if not scheduled_this_round:
                # Try scheduling without subject-on-day restriction
                for day in sorted_days:
                    if day == unavailable_day or classes_scheduled >= required_classes:
                        continue
                        
                    for slot in time_slots:
                        if (slot == '12:00-13:00' or
                            schedule[day][slot] is not None or
                            teacher_schedule.get(teacher_name, {}).get(day, {}).get(slot) or
                            slot in global_teacher_schedule.get(teacher_name, {}).get(day, set()) or
                            classes_scheduled >= required_classes):
                            continue
                        
                        # Find any available room
                        room_id = None
                        for room in theory_rooms:
                            if all_room_schedule[room[0]][day][slot] is None:
                                room_id = room[0]
                                break
                        
                        if room_id:
                            schedule[day][slot] = {
                                'subject_id': subject_id, 'subject_name': name,
                                'teacher_id': teacher_id, 'teacher_name': teacher_name,
                                'room_id': room_id, 'type': 'theory'
                            }
                            
                            if teacher_name not in teacher_schedule:
                                teacher_schedule[teacher_name] = {}
                            if day not in teacher_schedule[teacher_name]:
                                teacher_schedule[teacher_name][day] = {}
                            teacher_schedule[teacher_name][day][slot] = True
                            
                            all_room_schedule[room_id][day][slot] = f'{name}_{section_id}'
                            
                            classes_scheduled += 1
                            scheduled_this_round = True
                            
                            cursor.execute('''
                                INSERT INTO generated_schedules 
                                (section_id, day, time_slot, subject_id, teacher_id, room_id, room_type)
                                VALUES (?, ?, ?, ?, ?, ?, ?)
                            ''', (section_id, day, slot, subject_id, teacher_id, room_id, 'theory'))
                            
                            break
                    
                    if scheduled_this_round:
                        break
                
                # Only allow double periods if absolutely no other option exists
                if not scheduled_this_round and classes_scheduled < required_classes and classes_scheduled == 0:
                    # Only create double period if no single periods were scheduled at all
                    pass  # Remove double period scheduling entirely
                
                # Final break if still can't schedule
                if not scheduled_this_round:
                    break
    
    return theory_room_counter, lab_room_counter

def generate_section_schedule(section_id, semester_id):
    conn = sqlite3.connect('timetable.db', timeout=30)
    conn.execute('PRAGMA journal_mode=WAL')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT s.id, s.name, s.type, s.credits, s.lab_duration,
               pa.teacher_id, st.teacher_name, st.unavailable_day
        FROM subjects s
        JOIN primary_assignments pa ON s.id = pa.subject_id
        JOIN subject_teachers st ON pa.teacher_id = st.id
        WHERE s.semester_id = ? AND pa.section_id = ?
    ''', (semester_id, section_id))
    
    subjects = cursor.fetchall()
    
    cursor.execute('SELECT id, name FROM theory_rooms')
    theory_rooms = cursor.fetchall()
    cursor.execute('SELECT id, name FROM lab_rooms')
    lab_rooms = cursor.fetchall()
    
    time_slots = ['09:00-10:00', '10:00-11:00', '11:00-12:00', '12:00-13:00', '13:00-14:00', '14:00-15:00', '15:00-16:00', '16:00-17:00']
    days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']
    
    schedule = {}
    teacher_schedule = {}
    
    for day in days:
        schedule[day] = {}
        for slot in time_slots:
            schedule[day][slot] = None
    
    for subject_id, name, subject_type, credits, lab_duration, teacher_id, teacher_name, unavailable_day in subjects:
        
        if subject_type == 'theory':
            classes_scheduled = 0
            for day in days:
                if day == unavailable_day or classes_scheduled >= credits:
                    continue
                
                daily_theory_count = sum(1 for slot in time_slots 
                                       if schedule[day].get(slot) and 
                                       schedule[day][slot].get('type') == 'theory')
                
                if daily_theory_count >= 2:
                    continue
                
                for slot in time_slots:
                    if slot == '12:00-13:00':
                        continue
                    
                    if (schedule[day][slot] is None and 
                        teacher_schedule.get(teacher_name, {}).get(day, {}).get(slot) is None and
                        classes_scheduled < credits):
                        
                        room_id = theory_rooms[0][0] if theory_rooms else 1
                        
                        schedule[day][slot] = {
                            'subject_id': subject_id,
                            'subject_name': name,
                            'teacher_id': teacher_id,
                            'teacher_name': teacher_name,
                            'room_id': room_id,
                            'type': 'theory'
                        }
                        
                        if teacher_name not in teacher_schedule:
                            teacher_schedule[teacher_name] = {}
                        if day not in teacher_schedule[teacher_name]:
                            teacher_schedule[teacher_name][day] = {}
                        teacher_schedule[teacher_name][day][slot] = True
                        
                        classes_scheduled += 1
                        
                        cursor.execute('''
                            INSERT INTO generated_schedules 
                            (section_id, day, time_slot, subject_id, teacher_id, room_id, room_type)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        ''', (section_id, day, slot, subject_id, teacher_id, room_id, 'theory'))
        
        elif subject_type == 'practical':
            lab_hours = lab_duration or 2
            
            for day in days:
                if day == unavailable_day:
                    continue
                
                continuous_slots = []
                for i in range(len(time_slots) - lab_hours + 1):
                    if time_slots[i] == '12:00-13:00':
                        continue
                    
                    slots_available = True
                    temp_slots = []
                    
                    for j in range(lab_hours):
                        slot = time_slots[i + j]
                        if (slot == '12:00-13:00' or 
                            schedule[day].get(slot) is not None or
                            teacher_schedule.get(teacher_name, {}).get(day, {}).get(slot) is not None):
                            slots_available = False
                            break
                        temp_slots.append(slot)
                    
                    if slots_available:
                        continuous_slots = temp_slots
                        break
                
                if continuous_slots:
                    room_id = lab_rooms[0][0] if lab_rooms else theory_rooms[0][0] if theory_rooms else 1
                    
                    for slot in continuous_slots:
                        schedule[day][slot] = {
                            'subject_id': subject_id,
                            'subject_name': name,
                            'teacher_id': teacher_id,
                            'teacher_name': teacher_name,
                            'room_id': room_id,
                            'type': 'lab'
                        }
                        
                        if teacher_name not in teacher_schedule:
                            teacher_schedule[teacher_name] = {}
                        if day not in teacher_schedule[teacher_name]:
                            teacher_schedule[teacher_name][day] = {}
                        teacher_schedule[teacher_name][day][slot] = True
                        
                        cursor.execute('''
                            INSERT INTO generated_schedules 
                            (section_id, day, time_slot, subject_id, teacher_id, room_id, room_type)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        ''', (section_id, day, slot, subject_id, teacher_id, room_id, 'lab'))
                    
                    break
    
    conn.commit()
    conn.close()

def generate_pdf_schedules(dept_id):
    print("=== GENERATING PDF SCHEDULES ===")
    conn = sqlite3.connect('timetable.db', timeout=30)
    conn.execute('PRAGMA journal_mode=WAL')
    cursor = conn.cursor()
    
    cursor.execute('SELECT name, code FROM departments WHERE id = ?', (dept_id,))
    result = cursor.fetchone()
    if not result:
        conn.close()
        return []
    dept_name, dept_code = result
    
    cursor.execute('''
        SELECT sec.id, sec.section_label, y.year_number, s.semester_number
        FROM sections sec
        JOIN years y ON sec.year_id = y.id
        JOIN semesters s ON s.year_id = y.id
        WHERE y.department_id = ? AND s.is_active = 1
        ORDER BY y.year_number, s.semester_number, sec.section_label
    ''', (dept_id,))
    sections = cursor.fetchall()
    
    os.makedirs('output', exist_ok=True)
    filename = f'output/All_Timetables_{dept_code}.pdf'
    
    doc = SimpleDocTemplate(filename, pagesize=landscape(A4))
    elements = []
    styles = getSampleStyleSheet()
    
    for i, (section_id, section_label, year_number, semester_number) in enumerate(sections):
        # Add page break for subsequent sections
        if i > 0:
            from reportlab.platypus import PageBreak
            elements.append(PageBreak())
        
        # Header with HITK logo
        try:
            logo_url = "https://lh3.googleusercontent.com/d/1LBhx-x_Si1-cmGqsRAVmheoz0tXvJ3UN"
            response = requests.get(logo_url, timeout=10)
            if response.status_code == 200:
                logo_img = Image(BytesIO(response.content), width=60, height=60)
                logo_img.hAlign = 'CENTER'
                elements.append(logo_img)
                elements.append(Spacer(1, 10))
        except:
            pass  # Continue without logo if download fails
        
        section_info = Paragraph(f'<para align="center"><font size="12">{dept_name} ({dept_code}) - Year {year_number}, Section {section_label}</font></para>', styles['Normal'])
        elements.extend([section_info, Spacer(1, 20)])
        
        cursor.execute('''
            SELECT gs.day, gs.time_slot, s.name, st.teacher_name, 
                   CASE WHEN tr.name IS NOT NULL THEN tr.name ELSE lr.name END as room_name
            FROM generated_schedules gs
            JOIN subjects s ON gs.subject_id = s.id
            JOIN subject_teachers st ON gs.teacher_id = st.id
            LEFT JOIN theory_rooms tr ON gs.room_id = tr.id AND gs.room_type = 'theory'
            LEFT JOIN lab_rooms lr ON gs.room_id = lr.id AND gs.room_type = 'lab'
            WHERE gs.section_id = ?
            ORDER BY 
                CASE gs.day 
                    WHEN 'monday' THEN 1 
                    WHEN 'tuesday' THEN 2 
                    WHEN 'wednesday' THEN 3 
                    WHEN 'thursday' THEN 4 
                    WHEN 'friday' THEN 5 
                END, gs.time_slot
        ''', (section_id,))
        
        schedule_data = cursor.fetchall()
        
        time_slots = ['09:00-10:00', '10:00-11:00', '11:00-12:00', '12:00-13:00', '13:00-14:00', '14:00-15:00', '15:00-16:00', '16:00-17:00']
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        
        schedule_grid = {}
        for day, time_slot, subject, teacher, room in schedule_data:
            if day not in schedule_grid:
                schedule_grid[day] = {}
            schedule_grid[day][time_slot] = f'{subject}\n{teacher}\n{room}'
        
        table_data = [['Day'] + time_slots]
        
        for day_name, day_key in zip(days, ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']):
            row = [day_name]
            for slot in time_slots:
                if slot == '12:00-13:00':
                    cell_content = 'LUNCH BREAK'
                else:
                    cell_content = schedule_grid.get(day_key, {}).get(slot, 'Free Period')
                row.append(cell_content)
            table_data.append(row)
        
        table = Table(table_data, colWidths=[0.8*inch, 1.1*inch, 1.1*inch, 1.1*inch, 1.1*inch, 1.1*inch, 1.1*inch, 1.1*inch, 1.1*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 7),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 20))
        
        # Add footer
        footer_text = "Generated by Timely™ - AI-Powered Timetable Management System"
        elements.append(Spacer(1, 20))
        elements.append(Paragraph(f"<i>{footer_text}</i>", styles["Normal"]))
        elements.append(Spacer(1, 12))
    
    doc.build(elements)
    
    conn.close()
    return [filename]

@app.route('/download_schedules')
def download_schedules():
    # Find the generated PDF file
    for filename in os.listdir('output'):
        if filename.endswith('.pdf'):
            filepath = os.path.join('output', filename)
            return send_file(
                filepath,
                mimetype='application/pdf',
                as_attachment=True,
                download_name=filename
            )
    
    return jsonify({'error': 'No PDF found'}), 404

if __name__ == '__main__':
    if not os.path.exists('timetable.db'):
        init_db()
    app.run(debug=False, port=7777)