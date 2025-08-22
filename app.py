from flask import Flask, render_template, request, jsonify, send_file, session, redirect, url_for
import os
import json
import sqlite3
from datetime import datetime
from orchestrator.orchestrator import Orchestrator
from utils.logging_utils import get_logger
from attendance_system import LocationBasedAttendanceSystem
from config.email_config import get_email_config
from ngrok_manager import ensure_ngrok_running
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
import requests
import io

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-in-production'
logger = get_logger("WebApp")

# Initialize attendance system
attendance_system = LocationBasedAttendanceSystem()

# Ngrok will start on-demand when creating attendance

# Mock user database for demo
USERS = {
    'admin': {'password': 'admin123', 'role': 'admin', 'name': 'System Administrator'},
    'hod': {'password': 'hod123', 'role': 'hod', 'name': 'Dr. Sarah Johnson'},
    'faculty': {'password': 'faculty123', 'role': 'faculty', 'name': 'Prof. Michael Smith'},
    'student': {'password': 'student123', 'role': 'student', 'name': 'Alex Kumar'},
    'fac': {'password': 'fac123', 'role': 'pending', 'name': 'Faculty Member'}
}

# Configure codes for role determination
CONFIGURE_CODES = {
    '000': 'admin',
    '001': 'hod', 
    '069': 'faculty'
}

@app.route('/')
def landing():
    return render_template('landing.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username in USERS and USERS[username]['password'] == password:
            session['user'] = username
            session['role'] = USERS[username]['role']
            session['name'] = USERS[username]['name']
            
            # Redirect to configure page for fac users
            if username == 'fac':
                return redirect(url_for('configure'))
            
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error='Invalid credentials')
    
    return render_template('login.html')

@app.route('/auth/callback', methods=['POST'])
def auth_callback():
    # Supabase authentication callback endpoint
    try:
        data = request.get_json()
        user_data = data.get('user')
        
        if user_data:
            email = user_data.get('email')
            name = user_data.get('user_metadata', {}).get('full_name') or email.split('@')[0]
            avatar_url = user_data.get('user_metadata', {}).get('avatar_url')
            
            # Verify email domain
            if not (email.endswith('@heritageit.edu.in') or email.endswith('@heritageit.edu')):
                return jsonify({'success': False, 'error': 'Access denied. Only @heritageit.edu or @heritageit.edu.in emails are allowed.'}), 403
            
            session['user'] = email
            session['name'] = name
            session['avatar_url'] = avatar_url
            session['auth_method'] = 'supabase'
            
            # .edu emails need configure code
            if email.endswith('@heritageit.edu'):
                session['role'] = 'pending'
                return jsonify({'success': True, 'redirect': '/configure'})
            elif email.endswith('@heritageit.edu.in'):
                session['role'] = 'student'
                return jsonify({'success': True, 'redirect': '/dashboard'})
            
        return jsonify({'success': False, 'error': 'No user data'}), 400
        
    except Exception as e:
        logger.error(f"Auth callback error: {e}")
        return jsonify({'success': False, 'error': 'Authentication failed'}), 500

@app.route('/configure', methods=['GET', 'POST'])
def configure():
    # Allow direct access for fac user or users with pending role
    if 'user' not in session:
        # Handle fac user direct access
        session['user'] = 'fac'
        session['role'] = 'pending'
        session['name'] = 'Faculty Member'
    
    if session.get('role') != 'pending':
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        configure_code = request.form['configure_code']
        
        if configure_code in CONFIGURE_CODES:
            session['role'] = CONFIGURE_CODES[configure_code]
            return redirect(url_for('dashboard'))
        else:
            return render_template('configure.html', error='Invalid configure code')
    
    return render_template('configure.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('landing'))

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    # Redirect to configure if role is pending
    if session.get('role') == 'pending':
        return redirect(url_for('configure'))
    
    role = session['role']
    if role == 'admin':
        return render_template('admin_dashboard.html')
    elif role == 'hod':
        return render_template('hod_dashboard.html')
    elif role == 'faculty':
        return render_template('faculty_dashboard.html')
    elif role == 'student':
        return render_template('student_dashboard.html')
    
    return redirect(url_for('login'))

@app.route('/generator')
def generator():
    if 'user' not in session or session['role'] != 'hod':
        return redirect(url_for('login'))
    return render_template('generator.html')

@app.route('/api/check_db_status')
def check_db_status():
    if 'user' not in session or session['role'] != 'hod':
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        from routine5_integration import Routine5Integration
        routine5 = Routine5Integration()
        status = routine5.check_database_status()
        return jsonify(status)
    except Exception as e:
        return jsonify({'configured': False, 'error': str(e)})

@app.route('/generate', methods=['POST'])
def generate_timetable():
    if 'user' not in session or session['role'] != 'hod':
        return jsonify({'error': 'Unauthorized'}), 403
        
    try:
        data = request.get_json()
        constraints = data.get('constraints', [])
        
        if not constraints:
            return jsonify({'error': 'No constraints provided'}), 400
        
        # Split constraints by newlines and filter empty lines
        nl_constraints = [c.strip() for c in constraints.split('\n') if c.strip()]
        
        logger.info(f"Processing {len(nl_constraints)} constraints")
        
        orch = Orchestrator()
        result = orch.run(nl_constraints)
        
        return jsonify({
            'success': True,
            'outputs': result['outputs'],
            'verification': result['verification']
        })
        
    except Exception as e:
        logger.error(f"Error generating timetable: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/generate_from_db', methods=['POST'])
def generate_from_db():
    if 'user' not in session or session['role'] != 'hod':
        return jsonify({'error': 'Unauthorized'}), 403
        
    try:
        from routine5_integration import Routine5Integration
        
        # Initialize Routine5 integration
        routine5 = Routine5Integration()
        
        # Check database status
        status = routine5.check_database_status()
        if not status['configured']:
            return jsonify({'error': f"Database not configured: {status['error']}"}), 400
        
        logger.info(f"Generating timetables for {status['sections']} sections with {status['subjects']} subjects")
        
        # Generate timetables using Routine5 exact logic
        result = routine5.generate_timetables()
        
        if result.get('success'):
            output_files = routine5.get_output_files()
            return jsonify({
                'success': True,
                'total_sections': result.get('total_sections', status['sections']),
                'pdf_count': len(output_files),
                'files': [f['name'] for f in output_files]
            })
        else:
            return jsonify({'error': result.get('error', 'Unknown error occurred')}), 500
        
    except Exception as e:
        logger.error(f"Error generating from database: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/download/<filename>')
def download_file(filename):
    try:
        file_path = os.path.join('outputs', filename)
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True)
        else:
            return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download_routine5_schedules')
def download_routine5_schedules():
    try:
        # Find the generated PDF file from Routine5
        output_dir = 'Routine5_lab_advanced/output'
        if os.path.exists(output_dir):
            for filename in os.listdir(output_dir):
                if filename.endswith('.pdf') and 'All_Timetables' in filename:
                    filepath = os.path.join(output_dir, filename)
                    return send_file(
                        filepath,
                        mimetype='application/pdf',
                        as_attachment=True,
                        download_name=filename
                    )
        
        return jsonify({'error': 'No PDF found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/publish_timetable', methods=['POST'])
def publish_timetable():
    if 'user' not in session or session['role'] != 'hod':
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        data = request.get_json()
        title = data.get('title', 'New Timetable Published')
        
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        
        # Create notice board table if not exists
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
        
        # Insert notice
        cursor.execute('''
            INSERT INTO notice_board (title, content, type, published_by, timetable_data)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            title,
            'New class timetables have been published and are now available.',
            'timetable',
            session['name'],
            json.dumps({'published_at': datetime.now().isoformat()})
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Timetable published to notice board'})
        
    except Exception as e:
        logger.error(f"Error publishing timetable: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/notices')
def get_notices():
    try:
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT title, content, published_by, published_at, type
            FROM notice_board 
            WHERE is_active = 1 
            ORDER BY published_at DESC 
            LIMIT 10
        ''')
        
        notices = []
        for row in cursor.fetchall():
            notices.append({
                'title': row[0],
                'content': row[1],
                'published_by': row[2],
                'published_at': row[3],
                'type': row[4]
            })
        
        conn.close()
        return jsonify(notices)
        
    except Exception as e:
        logger.error(f"Error fetching notices: {e}")
        return jsonify([])

@app.route('/api/rooms')
def get_rooms():
    try:
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        
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
        
        # Insert default rooms if table is empty
        cursor.execute('SELECT COUNT(*) FROM rooms')
        if cursor.fetchone()[0] == 0:
            rooms = [('303', 22.5184833, 88.4168668, 5), ('304', 22.5185000, 88.4169000, 5), 
                    ('305', 22.5185200, 88.4169300, 5), ('306', 22.5185400, 88.4169600, 5)]
            for room in rooms:
                cursor.execute('INSERT INTO rooms (room_number, latitude, longitude, radius) VALUES (?, ?, ?, ?)', room)
        
        cursor.execute('SELECT room_number FROM rooms ORDER BY room_number')
        rooms = [row[0] for row in cursor.fetchall()]
        
        conn.commit()
        conn.close()
        return jsonify(rooms)
        
    except Exception as e:
        logger.error(f"Error fetching rooms: {e}")
        return jsonify(['303', '304', '305', '306'])  # Fallback

@app.route('/api/student-timetable')
def get_student_timetable():
    if 'user' not in session or session['role'] != 'student':
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        routine5_db = 'Routine5_lab_advanced/timetable.db'
        if os.path.exists(routine5_db):
            conn = sqlite3.connect(routine5_db)
            cursor = conn.cursor()
            
            # Get all sections with their schedules
            cursor.execute('''
                SELECT sec.id, sec.section_label, y.year_number, s.semester_number, d.name, d.code
                FROM sections sec
                JOIN years y ON sec.year_id = y.id
                JOIN semesters s ON s.year_id = y.id
                JOIN departments d ON y.department_id = d.id
                WHERE s.is_active = 1
                ORDER BY y.year_number, s.semester_number, sec.section_label
            ''')
            sections = cursor.fetchall()
            
            all_sections = []
            for section_id, section_label, year_number, semester_number, dept_name, dept_code in sections:
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
                schedule_grid = {}
                for day, time_slot, subject, teacher, room in schedule_data:
                    if day not in schedule_grid:
                        schedule_grid[day] = {}
                    schedule_grid[day][time_slot] = {
                        'subject': subject,
                        'teacher': teacher,
                        'room': room
                    }
                
                all_sections.append({
                    'section_label': section_label,
                    'year_number': year_number,
                    'semester_number': semester_number,
                    'dept_name': dept_name,
                    'dept_code': dept_code,
                    'schedule': schedule_grid
                })
            
            conn.close()
            return jsonify({'success': True, 'sections': all_sections})
        
        return jsonify({'success': False, 'message': 'No generated timetable found'})
        
    except Exception as e:
        logger.error(f"Error fetching student timetable: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/download-timetable')
def download_student_timetable():
    if 'user' not in session or session['role'] != 'student':
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        # Find the generated PDF file from Routine5
        output_dir = 'Routine5_lab_advanced/output'
        if os.path.exists(output_dir):
            for filename in os.listdir(output_dir):
                if filename.endswith('.pdf') and 'All_Timetables' in filename:
                    filepath = os.path.join(output_dir, filename)
                    return send_file(
                        filepath,
                        mimetype='application/pdf',
                        as_attachment=True,
                        download_name=filename
                    )
        
        return jsonify({'error': 'No PDF found'}), 404
        
    except Exception as e:
        logger.error(f"Error downloading PDF: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/routine5_setup')
def routine5_setup():
    if 'user' not in session or session['role'] != 'hod':
        return redirect(url_for('login'))
    
    # Redirect to Routine5 setup page
    return redirect('/static/routine5_setup.html')

# Attendance System Routes
@app.route('/create-attendance', methods=['POST'])
def create_attendance():
    if 'user' not in session or session['role'] != 'faculty':
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        data = request.get_json()
        room = data.get('room', 'Room 101')
        
        # Parse class format: CSE-3B -> stream: CSE, semester: 3, section: B
        class_format = data.get('class_format', 'CSE-3B')
        parts = class_format.split('-')
        if len(parts) != 2:
            return jsonify({'error': 'Invalid class format. Use format: CSE-3B'}), 400
        
        stream = parts[0].upper()
        sem_section = parts[1]
        
        # Extract semester and section
        semester = ''.join(filter(str.isdigit, sem_section))
        section = ''.join(filter(str.isalpha, sem_section)).upper()
        
        if not semester or not section:
            return jsonify({'error': 'Invalid format. Use: STREAM-SEMESTERSECTION (e.g., CSE-3B)'}), 400
        
        class_id = f"{stream.lower()}-{stream.lower()}-{section.lower()}"
        class_name = f"{stream} Semester {semester} - Section {section}"
        
        # Get room coordinates from database
        conn_room = sqlite3.connect('attendance.db')
        cursor_room = conn_room.cursor()
        cursor_room.execute('SELECT latitude, longitude FROM rooms WHERE room_number = ?', (room,))
        room_data = cursor_room.fetchone()
        conn_room.close()
        
        if room_data:
            teacher_lat, teacher_lng = room_data
        else:
            # Default coordinates for Room 303
            teacher_lat = 22.5184833
            teacher_lng = 88.4168668
        
        # Create attendance session
        session_id = attendance_system.create_attendance_session(
            class_id, class_name, room, teacher_lat, teacher_lng
        )
        
        # Get students for this class
        students = attendance_system.get_students_by_class(class_id)
        
        if not students:
            return jsonify({
                'success': False,
                'message': f'No students found for class {class_format}'
            })
        
        # Email configuration - UPDATE THESE VALUES
        smtp_config = {
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': 587,
            'email': 'sync.timely@gmail.com',
            'password': 'zrtw pmwx dlsp jkcf',
            'use_tls': True
        }
        
        # Send emails to students
        emails_sent = attendance_system.send_attendance_emails(
            students, session_id, class_name, room, smtp_config
        )
        
        return jsonify({
            'success': True,
            'sessionId': session_id,
            'emailsSent': emails_sent,
            'studentsFound': len(students),
            'classFormat': class_format
        })
        
    except Exception as e:
        logger.error(f"Error creating attendance: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/mark-attendance/<session_id>')
def mark_attendance_page(session_id):
    try:
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT class_name, room, created_at, radius, is_active
            FROM attendance_sessions 
            WHERE id = ?
        ''', (session_id,))
        
        session_data = cursor.fetchone()
        conn.close()
        
        if not session_data:
            return render_template('error.html', message='Invalid attendance session')
        
        if not session_data[4]:  # is_active
            return render_template('error.html', message='Attendance session has ended')
        
        session_info = {
            'class_name': session_data[0],
            'room': session_data[1],
            'created_at': session_data[2],
            'radius': session_data[3]
        }
        
        return render_template('mark_attendance.html', 
                             session=session_info, 
                             session_id=session_id)
        
    except Exception as e:
        logger.error(f"Error loading attendance page: {e}")
        return render_template('error.html', message='Error loading attendance page')

@app.route('/api/mark-attendance', methods=['POST'])
def api_mark_attendance():
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        
        if not all([session_id, latitude, longitude]):
            return jsonify({'error': 'Missing required data'}), 400
        
        # Get student ID from email in request body
        email = data.get('email')
        print(f"DEBUG: Email from request: {email}")
        
        if email:
            # Find student by email
            conn = sqlite3.connect('attendance.db')
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM students WHERE email = ?', (email,))
            result = cursor.fetchone()
            conn.close()
            student_id = result[0] if result else 1
            print(f"DEBUG: Student ID found: {student_id}")
        else:
            student_id = 1  # Default fallback
            print("DEBUG: No email provided, using default student_id = 1")
        
        # Get client IP
        client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR', 'unknown'))
        if ',' in client_ip:
            client_ip = client_ip.split(',')[0].strip()
        
        result = attendance_system.mark_attendance(
            session_id, student_id, latitude, longitude, client_ip
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error marking attendance: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/attendance-stats/<session_id>')
def attendance_stats(session_id):
    if 'user' not in session or session['role'] != 'faculty':
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        stats = attendance_system.get_attendance_stats(session_id)
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error getting attendance stats: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/end-session/<session_id>', methods=['POST'])
def end_session(session_id):
    if 'user' not in session or session['role'] != 'faculty':
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        success = attendance_system.end_session(session_id)
        return jsonify({'success': success})
    except Exception as e:
        logger.error(f"Error ending session: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/attendance-report/<session_id>')
def attendance_report(session_id):
    if 'user' not in session or session['role'] != 'faculty':
        return redirect(url_for('login'))
    
    try:
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        
        # Get session info
        cursor.execute('''
            SELECT class_name, room, created_at, class_id
            FROM attendance_sessions WHERE id = ?
        ''', (session_id,))
        session_data = cursor.fetchone()
        
        if not session_data:
            return render_template('error.html', message='Session not found')
        
        # Get all students for this class
        cursor.execute('''
            SELECT s.id, s.name, s.email, s.roll_number
            FROM students s WHERE s.class_id = ?
        ''', (session_data[3],))
        all_students = cursor.fetchall()
        
        # Get attendance records
        cursor.execute('''
            SELECT student_id, status, marked_at, distance
            FROM attendance_records WHERE session_id = ?
        ''', (session_id,))
        attendance_records = {row[0]: row for row in cursor.fetchall()}
        
        conn.close()
        
        # Build student list with status
        students = []
        present_count = absent_count = not_clicked_count = 0
        
        for student in all_students:
            student_id = student[0]
            if student_id in attendance_records:
                record = attendance_records[student_id]
                status = record[1]  # present/absent
                marked_at = record[2]
                distance = record[3]
                if status == 'present':
                    present_count += 1
                else:
                    absent_count += 1
            else:
                status = 'not-clicked'
                marked_at = None
                distance = None
                not_clicked_count += 1
            
            students.append({
                'name': student[1],
                'email': student[2],
                'roll_number': student[3],
                'status': status,
                'marked_at': marked_at,
                'distance': distance
            })
        
        session_info = {
            'class_name': session_data[0],
            'room': session_data[1],
            'created_at': session_data[2]
        }
        
        stats = {
            'present': present_count,
            'absent': absent_count,
            'not_clicked': not_clicked_count,
            'total': len(all_students)
        }
        
        return render_template('attendance_report.html', 
                             session=session_info, 
                             students=students, 
                             stats=stats,
                             session_id=session_id)
        
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        return render_template('error.html', message='Error generating report')

@app.route('/start_routine5_app', methods=['POST'])
def start_routine5_app():
    if 'user' not in session or session['role'] != 'hod':
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        import subprocess
        import os
        import time
        import requests
        
        # Check if already running
        try:
            response = requests.get('http://127.0.0.1:7777', timeout=2)
            if response.status_code == 200:
                return jsonify({'success': True, 'message': 'Routine5 app already running'})
        except:
            pass
        
        # Start the Routine5 app in background
        routine5_path = os.path.join(os.getcwd(), 'Routine5_lab_advanced')
        process = subprocess.Popen(['python', 'app.py'], cwd=routine5_path, shell=True, 
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait and verify it started
        for i in range(10):  # Try for 10 seconds
            time.sleep(1)
            try:
                response = requests.get('http://127.0.0.1:7777', timeout=1)
                if response.status_code == 200:
                    return jsonify({'success': True, 'message': 'Routine5 app started successfully'})
            except:
                continue
        
        return jsonify({'success': False, 'message': 'Routine5 app started but not responding'})
    except Exception as e:
        logger.error(f"Error starting Routine5 app: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/export-pdf/<session_id>')
def export_pdf(session_id):
    if 'user' not in session or session['role'] != 'faculty':
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        
        # Get session info
        cursor.execute('''
            SELECT class_name, room, created_at, class_id
            FROM attendance_sessions WHERE id = ?
        ''', (session_id,))
        session_data = cursor.fetchone()
        
        if not session_data:
            return jsonify({'error': 'Session not found'}), 404
        
        # Get all students for this class
        cursor.execute('''
            SELECT s.id, s.name, s.email, s.roll_number
            FROM students s WHERE s.class_id = ?
        ''', (session_data[3],))
        all_students = cursor.fetchall()
        
        # Get attendance records
        cursor.execute('''
            SELECT student_id, status, marked_at, distance
            FROM attendance_records WHERE session_id = ?
        ''', (session_id,))
        attendance_records = {row[0]: row for row in cursor.fetchall()}
        
        conn.close()
        
        # Create PDF
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch)
        styles = getSampleStyleSheet()
        story = []
        
        # Header with logos
        try:
            from reportlab.platypus import Image
            hitk_logo = Image('https://lh3.googleusercontent.com/d/1LBhx-x_Si1-cmGqsRAVmheoz0tXvJ3UN', width=1*inch, height=1*inch)
            timely_logo = Image('https://lh3.googleusercontent.com/d/16SCBMg4I5snTZjuQ1XrsfDPkRMvPfwGs', width=1*inch, height=1*inch)
            
            logo_data = [[
                hitk_logo,
                Paragraph('<b>Heritage Institute of Technology</b><br/>Attendance Management System<br/>Powered by Timely™', 
                          ParagraphStyle('LogoText', parent=styles['Normal'], fontSize=12, alignment=1)),
                timely_logo
            ]]
            
            logo_table = Table(logo_data, colWidths=[1.5*inch, 4*inch, 1.5*inch])
            logo_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 20)
            ]))
            story.append(logo_table)
        except:
            header_style = ParagraphStyle('Header', parent=styles['Normal'], fontSize=14, alignment=1, spaceAfter=20)
            story.append(Paragraph('<b>Heritage Institute of Technology</b><br/>Attendance Management System<br/>Powered by Timely™', header_style))
        
        # Title
        title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], 
                                   fontSize=18, spaceAfter=20, alignment=1)
        story.append(Paragraph('Attendance Report', title_style))
        
        # Session info
        info_style = ParagraphStyle('Info', parent=styles['Normal'], fontSize=12, spaceAfter=10)
        story.append(Paragraph(f'<b>Class:</b> {session_data[0]}', info_style))
        story.append(Paragraph(f'<b>Room:</b> {session_data[1]}', info_style))
        story.append(Paragraph(f'<b>Date:</b> {session_data[2]}', info_style))
        story.append(Spacer(1, 20))
        
        # Build table data
        table_data = [['Name', 'Roll Number', 'Email', 'Status', 'Time']]
        present_count = absent_count = not_clicked_count = 0
        
        for student in all_students:
            student_id = student[0]
            if student_id in attendance_records:
                record = attendance_records[student_id]
                status = record[1].title()
                marked_at = record[2] if record[2] else 'N/A'
                if record[1] == 'present':
                    present_count += 1
                else:
                    absent_count += 1
            else:
                status = 'Not Clicked'
                marked_at = 'N/A'
                not_clicked_count += 1
            
            table_data.append([student[1], student[3], student[2], status, marked_at])
        
        # Create table
        table = Table(table_data, colWidths=[2*inch, 1*inch, 2.5*inch, 1*inch, 1.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        # Color code status
        for i, row in enumerate(table_data[1:], 1):
            if row[3] == 'Present':
                table.setStyle(TableStyle([('BACKGROUND', (3, i), (3, i), colors.lightgreen)]))
            elif row[3] == 'Absent':
                table.setStyle(TableStyle([('BACKGROUND', (3, i), (3, i), colors.lightcoral)]))
            else:
                table.setStyle(TableStyle([('BACKGROUND', (3, i), (3, i), colors.lightyellow)]))
        
        story.append(table)
        story.append(Spacer(1, 20))
        
        # Summary
        summary_data = [
            ['Total Students', str(len(all_students))],
            ['Present', str(present_count)],
            ['Absent', str(absent_count)],
            ['Not Clicked', str(not_clicked_count)]
        ]
        
        summary_table = Table(summary_data, colWidths=[2*inch, 1*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.lightblue),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(Paragraph('<b>Summary</b>', styles['Heading2']))
        story.append(summary_table)
        
        doc.build(story)
        buffer.seek(0)
        
        return send_file(
            buffer,
            as_attachment=True,
            download_name=f'attendance_report_{session_id}.pdf',
            mimetype='application/pdf'
        )
        
    except Exception as e:
        logger.error(f"Error exporting PDF: {e}")
        return jsonify({'error': str(e)}), 500



def start_routine5_app():
    """Start the Routine5 app in background"""
    import subprocess
    import os
    import time
    
    time.sleep(2)  # Wait for main app to start
    routine5_path = os.path.join(os.getcwd(), 'Routine5_lab_advanced')
    subprocess.Popen(['python', 'app.py'], cwd=routine5_path, shell=True)

if __name__ == '__main__':
    import threading
    
    # Start Routine5 app in background thread
    routine5_thread = threading.Thread(target=start_routine5_app, daemon=True)
    routine5_thread.start()
    
    app.run(debug=False, host='0.0.0.0', port=5000)