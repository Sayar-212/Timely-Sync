from flask import Flask, render_template, request, jsonify
import sqlite3
import uuid
from datetime import datetime
import math

app = Flask(__name__)

def get_db():
    return sqlite3.connect('attendance.db')

@app.route('/')
def index():
    return render_template('landing.html')

@app.route('/start_session', methods=['POST'])
def start_session():
    data = request.json
    session_id = str(uuid.uuid4())[:8]
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO attendance_sessions 
        (id, class_id, class_name, room, teacher_lat, teacher_lng, radius)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (session_id, data['class_id'], data['class_name'], data['room'],
          data['lat'], data['lng'], data['radius']))
    conn.commit()
    conn.close()
    
    return jsonify({'session_id': session_id})

@app.route('/mark_attendance/<session_id>')
def mark_attendance(session_id):
    return render_template('mark_attendance.html', session_id=session_id)

@app.route('/submit_attendance', methods=['POST'])
def submit_attendance():
    data = request.json
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Get session details
    cursor.execute('SELECT teacher_lat, teacher_lng, radius FROM attendance_sessions WHERE id = ?', 
                  (data['session_id'],))
    session = cursor.fetchone()
    
    if not session:
        return jsonify({'success': False, 'error': 'Session not found'})
    
    teacher_lat, teacher_lng, radius = session
    
    # Calculate distance
    distance = math.sqrt((float(data['lat']) - teacher_lat)**2 + 
                        (float(data['lng']) - teacher_lng)**2) * 111000
    
    if distance <= radius:
        cursor.execute('''
            INSERT INTO attendance_records 
            (session_id, student_id, student_lat, student_lng, distance, client_ip)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (data['session_id'], data['student_id'], data['lat'], data['lng'], 
              distance, request.remote_addr))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    else:
        conn.close()
        return jsonify({'success': False, 'error': 'Too far from class location'})

if __name__ == '__main__':
    app.run(debug=True, port=5001)  # Different port from routine5