import sqlite3
import smtplib
import uuid
import math
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Tuple, Optional
from config.email_config import get_room_coordinates, get_attendance_settings, EMAIL_TEMPLATES

class LocationBasedAttendanceSystem:
    def __init__(self, db_path: str = "attendance.db"):
        self.db_path = db_path
        self.init_room_coordinates()
    
    def init_room_coordinates(self):
        """Initialize room coordinates in the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create room_coordinates table if not exists
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS room_coordinates (
                room_number TEXT PRIMARY KEY,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                radius INTEGER DEFAULT 50
            )
        ''')
        
        # Insert room coordinates from configuration
        room_coords = get_room_coordinates()
        sample_rooms = [
            (room, coords['lat'], coords['lng'], coords['radius'])
            for room, coords in room_coords.items()
        ]
        
        cursor.executemany('''
            INSERT OR IGNORE INTO room_coordinates (room_number, latitude, longitude, radius)
            VALUES (?, ?, ?, ?)
        ''', sample_rooms)
        
        conn.commit()
        conn.close()
    
    def calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two coordinates using Haversine formula"""
        R = 6371000  # Earth's radius in meters
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = (math.sin(delta_lat / 2) ** 2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * 
             math.sin(delta_lon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
    
    def create_attendance_session(self, class_id: str, class_name: str, room: str, 
                                teacher_lat: float, teacher_lng: float) -> str:
        """Create a new attendance session"""
        session_id = str(uuid.uuid4())
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get room radius
        cursor.execute('SELECT radius FROM room_coordinates WHERE room_number = ?', (room,))
        result = cursor.fetchone()
        radius = result[0] if result else 50  # Default 50m radius
        
        cursor.execute('''
            INSERT INTO attendance_sessions 
            (id, class_id, class_name, room, teacher_lat, teacher_lng, radius)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (session_id, class_id, class_name, room, teacher_lat, teacher_lng, radius))
        
        conn.commit()
        conn.close()
        
        return session_id
    
    def get_students_by_class(self, class_id: str) -> List[Dict]:
        """Get all students for a specific class"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, name, email, roll_number 
            FROM students 
            WHERE class_id = ?
        ''', (class_id,))
        
        students = []
        for row in cursor.fetchall():
            students.append({
                'id': row[0],
                'name': row[1],
                'email': row[2],
                'roll_number': row[3]
            })
        
        conn.close()
        return students
    
    def send_attendance_emails(self, students: List[Dict], session_id: str, 
                             class_name: str, room: str, smtp_config: Dict) -> int:
        """Send attendance notification emails to students"""
        try:
            print(f"Connecting to SMTP server: {smtp_config['smtp_server']}:{smtp_config['smtp_port']}")
            server = smtplib.SMTP(smtp_config['smtp_server'], smtp_config['smtp_port'])
            server.starttls()
            print(f"Logging in with email: {smtp_config['email']}")
            server.login(smtp_config['email'], smtp_config['password'])
            print("SMTP login successful")
            
            emails_sent = 0
            # Start ngrok tunnel for this attendance session
            from ngrok_manager import start_ngrok_for_attendance
            print("🚀 Starting ngrok tunnel for attendance session...")
            base_url = start_ngrok_for_attendance()
            
            if "localhost" in base_url:
                print("⚠️ Ngrok failed, using localhost - emails will contain local URLs")
            else:
                print(f"✅ Ngrok tunnel active: {base_url} (will auto-close in 5 minutes)")
            
            attendance_url = f"{base_url}/mark-attendance/{session_id}"
            
            for student in students:
                subject = f"Attendance Required - {class_name}"
                # Add email parameter to URL for student identification
                student_url = f"{attendance_url}?email={student['email']}"
                
                # Create HTML email template
                body = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
        .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }}
        .header {{ background: linear-gradient(135deg, #667eea, #764ba2); padding: 30px; text-align: center; color: white; }}
        .logo {{ display: flex; align-items: center; justify-content: center; gap: 15px; margin-bottom: 15px; }}
        .logo img {{ height: 50px; }}
        .content {{ padding: 30px; }}
        .attendance-card {{ background: #f8f9ff; border-left: 4px solid #667eea; padding: 20px; margin: 20px 0; border-radius: 8px; }}
        .btn {{ display: inline-block; background: linear-gradient(135deg, #38a169, #2f855a); color: white; padding: 15px 30px; text-decoration: none; border-radius: 25px; font-weight: bold; margin: 20px 0; }}
        .footer {{ background: #f7fafc; padding: 20px; text-align: center; color: #718096; font-size: 12px; }}
        .warning {{ background: #fff5f5; border: 1px solid #feb2b2; color: #742a2a; padding: 15px; border-radius: 8px; margin: 15px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">
                <img src="https://lh3.googleusercontent.com/d/1LBhx-x_Si1-cmGqsRAVmheoz0tXvJ3UN" alt="HITK Logo">
                <div>
                    <h1 style="margin: 0; font-size: 24px;">Timely™</h1>
                    <p style="margin: 5px 0 0 0; opacity: 0.9;">Smart Attendance System</p>
                </div>
                <img src="https://lh3.googleusercontent.com/d/1HfdfTfJKHXAsXbk06AroA-BLn8VcnqhA" alt="Timely Logo">
            </div>
        </div>
        
        <div class="content">
            <h2 style="color: #2d3748; margin-bottom: 10px;">📍 Attendance Required</h2>
            <p>Dear <strong>{student['name']}</strong>,</p>
            
            <div class="attendance-card">
                <h3 style="margin: 0 0 10px 0; color: #4a5568;">📚 {class_name}</h3>
                <p style="margin: 5px 0;"><strong>🏫 Location:</strong> {room}</p>
                <p style="margin: 5px 0;"><strong>⏰ Session:</strong> Active now (expires in 5 minutes)</p>
            </div>
            
            <p>Your attendance is required for the above class session. Please mark your attendance by clicking the button below:</p>
            
            <div style="text-align: center;">
                <a href="{student_url}" class="btn">📱 Mark My Attendance</a>
            </div>
            
            <div class="warning">
                <strong>⚠️ CRITICAL - READ CAREFULLY:</strong>
                <ul style="margin: 10px 0; padding-left: 20px;">
                    <li><strong>🚨 DISCONNECT FROM WIFI - Use Mobile Data Only</strong></li>
                    <li>Multiple students on same WiFi will be flagged as proxy</li>
                    <li>You must be physically present in the classroom</li>
                    <li>Location verification is automatic</li>
                    <li>Session expires in 5 minutes</li>
                    <li>Enable location services on your device</li>
                </ul>
            </div>
            
            <p style="color: #718096; font-size: 14px; margin-top: 20px;">
                If you're having trouble with the button, copy and paste this link:<br>
                <span style="background: #f7fafc; padding: 5px; border-radius: 4px; word-break: break-all;">{student_url}</span>
            </p>
        </div>
        
        <div class="footer">
            <p><strong>Heritage Institute of Technology, Kolkata</strong></p>
            <p>Automated by Timely™ Smart Attendance System</p>
            <p style="margin-top: 10px;">This is an automated message. Please do not reply to this email.</p>
        </div>
    </div>
</body>
</html>
"""
                
                msg = MIMEMultipart()
                msg['From'] = smtp_config['email']
                msg['To'] = student['email']
                msg['Subject'] = subject
                
                msg.attach(MIMEText(body, 'html'))
                print(f"Sending email to: {student['email']}")
                server.send_message(msg)
                emails_sent += 1
                print(f"Email sent successfully to: {student['email']}")
            
            server.quit()
            return emails_sent
            
        except Exception as e:
            print(f"Error sending emails: {e}")
            import traceback
            traceback.print_exc()
            return 0
    
    def mark_attendance(self, session_id: str, student_id: int, 
                       student_lat: float, student_lng: float, client_ip: str = None) -> Dict:
        """Mark attendance for a student with location verification"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get session details
        cursor.execute('''
            SELECT teacher_lat, teacher_lng, radius, is_active, room
            FROM attendance_sessions 
            WHERE id = ?
        ''', (session_id,))
        
        session = cursor.fetchone()
        if not session:
            conn.close()
            return {'success': False, 'message': 'Invalid session'}
        
        teacher_lat, teacher_lng, radius, is_active, room = session
        
        if not is_active:
            conn.close()
            return {'success': False, 'message': 'Session has ended'}
        
        # Calculate distance
        distance = self.calculate_distance(student_lat, student_lng, teacher_lat, teacher_lng)
        
        # Check if student is within range
        status = 'present' if distance <= radius else 'absent'
        
        # Check if already marked by this specific student
        cursor.execute('''
            SELECT id FROM attendance_records 
            WHERE session_id = ? AND student_id = ?
        ''', (session_id, student_id))
        
        if cursor.fetchone():
            conn.close()
            return {'success': False, 'message': 'Attendance already marked'}
        
        # Use provided client_ip or get from Flask request
        if not client_ip:
            from flask import request as flask_request
            client_ip = flask_request.environ.get('HTTP_X_FORWARDED_FOR', flask_request.environ.get('REMOTE_ADDR', 'unknown'))
            if ',' in client_ip:
                client_ip = client_ip.split(',')[0].strip()
        
        # Check for IP proxy detection
        cursor.execute('''
            SELECT student_id FROM attendance_records 
            WHERE session_id = ? AND client_ip = ?
        ''', (session_id, client_ip))
        
        existing_ip = cursor.fetchone()
        if existing_ip and existing_ip[0] != student_id:
            conn.close()
            return {
                'success': False, 
                'message': f'Proxy detected! This IP address was already used by another student. Use your own device.'
            }
        
        # Insert attendance record with IP tracking
        cursor.execute('''
            INSERT INTO attendance_records 
            (session_id, student_id, student_lat, student_lng, distance, status, marked_at, client_ip)
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?)
        ''', (session_id, student_id, student_lat, student_lng, distance, status, client_ip))
        
        conn.commit()
        conn.close()
        
        return {
            'success': True,
            'status': status,
            'distance': round(distance, 2),
            'required_distance': radius,
            'message': f'Attendance marked as {status}. Distance: {round(distance, 2)}m'
        }
    
    def get_attendance_stats(self, session_id: str) -> Dict:
        """Get attendance statistics for a session"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                COUNT(*) as total_marked,
                SUM(CASE WHEN status = 'present' THEN 1 ELSE 0 END) as present,
                SUM(CASE WHEN status = 'absent' THEN 1 ELSE 0 END) as absent
            FROM attendance_records 
            WHERE session_id = ?
        ''', (session_id,))
        
        stats = cursor.fetchone()
        conn.close()
        
        return {
            'total_marked': stats[0],
            'present': stats[1],
            'absent': stats[2]
        }
    
    def end_session(self, session_id: str) -> bool:
        """End an attendance session"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE attendance_sessions 
            SET is_active = 0, ended_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (session_id,))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return success