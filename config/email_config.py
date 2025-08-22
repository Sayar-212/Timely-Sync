"""
Email Configuration for Attendance System

To use Gmail SMTP:
1. Enable 2-factor authentication on your Gmail account
2. Generate an App Password:
   - Go to Google Account settings
   - Security > 2-Step Verification > App passwords
   - Generate password for "Mail"
3. Use the generated password below

For other email providers, update SMTP settings accordingly.
"""

import os

# Email Configuration
EMAIL_CONFIG = {
    'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
    'smtp_port': int(os.getenv('SMTP_PORT', 587)),
    'email': os.getenv('ATTENDANCE_EMAIL', 'your-email@gmail.com'),
    'password': os.getenv('ATTENDANCE_EMAIL_PASSWORD', 'your-app-password'),
    'use_tls': True
}

# Room Coordinates (Replace with actual coordinates of your institution)
ROOM_COORDINATES = {
    'Room 101': {'lat': 22.5185485, 'lng': 88.4167369, 'radius': 30},
    'Room 102': {'lat': 22.5185585, 'lng': 88.4167469, 'radius': 30},
    'Room 103': {'lat': 22.5185685, 'lng': 88.4167569, 'radius': 30},
    'Room 201': {'lat': 22.5185785, 'lng': 88.4167669, 'radius': 30},
    'Room 202': {'lat': 22.5185885, 'lng': 88.4167769, 'radius': 30},
    'Room 205': {'lat': 22.5185985, 'lng': 88.4167869, 'radius': 30},
    'Lab A': {'lat': 22.5186085, 'lng': 88.4167969, 'radius': 40},
    'Lab B': {'lat': 22.5186185, 'lng': 88.4168069, 'radius': 40},
    'Auditorium': {'lat': 22.5186285, 'lng': 88.4168169, 'radius': 50},
    'Library': {'lat': 22.5186385, 'lng': 88.4168269, 'radius': 35},
}

# Attendance Settings
ATTENDANCE_SETTINGS = {
    'session_duration_minutes': 30,  # How long attendance session stays active
    'location_accuracy_threshold': 100,  # Minimum GPS accuracy required (meters)
    'default_radius': 50,  # Default classroom radius in meters
    'max_radius': 100,  # Maximum allowed radius
    'min_radius': 10,   # Minimum allowed radius
}

# Class Format Validation
CLASS_FORMAT_REGEX = r'^[A-Z]{2,4}-\d[A-Z]$'  # e.g., CSE-3B, ECE-2A, MECH-4C

# Email Templates
EMAIL_TEMPLATES = {
    'attendance_notification': {
        'subject': 'Attendance Required - {class_name}',
        'body': '''
Dear {student_name},

Your attendance is required for {class_name} in {room}.

Please click the link below to mark your attendance:
{attendance_url}

Important Notes:
• You must be physically present in the classroom to mark attendance
• The system will verify your location automatically
• Session will expire in {duration} minutes
• Ensure your device's location services are enabled

If you have any issues, please contact your instructor.

Best regards,
Academic System - Timely™
        '''
    }
}

def get_email_config():
    """Get email configuration with environment variable support"""
    return EMAIL_CONFIG.copy()

def get_room_coordinates():
    """Get room coordinates configuration"""
    return ROOM_COORDINATES.copy()

def get_attendance_settings():
    """Get attendance system settings"""
    return ATTENDANCE_SETTINGS.copy()