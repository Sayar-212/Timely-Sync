# Timely-Sync: Comprehensive Automated Timetable & Attendance System

A complete educational management system featuring **multi-agent timetable generation**, **location-based attendance tracking**, and **integrated notice board** with professional PDF exports and institutional branding.

## 🚀 Quick Start

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
export GEMINI_API_KEY=YOUR_KEY   # optional
python main.py
```

## 🏗️ System Architecture

### Multi-Agent Timetable Backend
- **Google OR-Tools CP-SAT** for constraint satisfaction
- **Gemini API** for natural language parsing (offline fallback included)
- **Multi-agent architecture** with specialized agents for parsing, verification, solving, and formatting
- **Dual generation modes**: Database-driven (Routine5) and natural language constraints

### Location-Based Attendance System
- **GPS verification** ensures physical presence in classroom
- **Automated email notifications** with branded templates
- **Real-time distance calculation** using Haversine formula
- **Session management** with automatic expiry

### Notice Board & Room Management
- **HOD dashboard** for publishing timetables
- **Student dashboard** with real-time updates
- **Room management** with GPS coordinates
- **Professional PDF exports** with institutional branding

## 📊 Features Overview

### 🎯 Timetable Generation
- **Two Generation Methods**:
  - Database-driven using Routine5 logic (6 sections, 14 subjects)
  - Natural language constraint parsing with multi-agent system
- **Professional PDF Output** with HITK logo integration
- **Constraint Verification** and optimization
- **JSON + PDF exports** in `outputs/` directory

### 📍 Attendance System
- **Location Verification**: GPS-based presence confirmation
- **Class Format Support**: CSE-3B (Stream-Semester+Section)
- **Email Integration**: Automated notifications to students
- **Faculty Dashboard**: Easy session creation and management
- **Real-time Reporting**: Attendance statistics and PDF exports

### 📢 Notice Board
- **HOD Publishing**: Publish timetables with custom titles
- **Student Dashboard**: Real-time notice updates every 30 seconds
- **Visual Indicators**: "NEW" badges for fresh notices
- **Time Stamps**: Publication date and author tracking

### 🏢 Room Management
- **Pre-configured Rooms**: 303, 304, 305, 306 with GPS coordinates
- **Dropdown Selection**: Faculty room selection interface
- **Location Integration**: Automatic coordinate mapping for attendance

## 🔧 Installation & Setup

### 1. Core Dependencies
```bash
pip install flask sqlite3 reportlab requests google-ortools
```

### 2. Database Setup
```bash
python setup_attendance.py      # Attendance system
python setup_notice_board.py    # Notice board system
python setup_your_data.py       # Sample data
```

### 3. Email Configuration
Update `config/email_config.py`:
```python
EMAIL_CONFIG = {
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 587,
    'email': 'your-email@gmail.com',
    'password': 'your-app-password',
}
```

### 4. Room Coordinates
Configure actual classroom locations in `config/email_config.py`:
```python
ROOM_COORDINATES = {
    'Room 303': {'lat': 22.5184833, 'lng': 88.4168668, 'radius': 30},
    'Room 304': {'lat': 22.5185000, 'lng': 88.4169000, 'radius': 30},
}
```

## 🎮 Usage Guide

### For HOD (Head of Department)
1. **Login**: `hod` / `hod123`
2. **Generate Timetables**: Choose database or custom constraints
3. **Publish to Notice Board**: Share with students instantly
4. **View Reports**: Access attendance and system statistics

### For Faculty
1. **Login**: `faculty` / `faculty123`
2. **Create Attendance Session**: Select room and class format
3. **Monitor Attendance**: Real-time student check-ins
4. **Export Reports**: Professional PDF attendance reports

### For Students
1. **Receive Email**: Attendance notification with location link
2. **Mark Attendance**: GPS-verified presence confirmation
3. **View Dashboard**: Scrollable routine and notice board
4. **Real-time Updates**: Automatic notice refresh every 30 seconds

## 📱 System Interfaces

### Web Application Routes
- `/` - Landing page with system overview
- `/hod-dashboard` - HOD management interface
- `/faculty-dashboard` - Faculty attendance management
- `/student-dashboard` - Student routine and notices
- `/generator` - Timetable generation interface
- `/attendance-report/<session_id>` - PDF export interface

### API Endpoints
- `POST /create-attendance` - Create new attendance session
- `POST /api/mark-attendance` - Student attendance marking
- `GET /api/rooms` - Available rooms list
- `POST /publish-notice` - HOD notice publishing
- `GET /api/check_db_status` - Database status check

## 🗄️ Database Schema

### Students Table
```sql
CREATE TABLE students (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    roll_number TEXT UNIQUE NOT NULL,
    class_id TEXT NOT NULL,
    semester INTEGER NOT NULL
);
```

### Attendance Sessions
```sql
CREATE TABLE attendance_sessions (
    id TEXT PRIMARY KEY,
    class_id TEXT NOT NULL,
    room TEXT NOT NULL,
    teacher_lat REAL NOT NULL,
    teacher_lng REAL NOT NULL,
    radius INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT 1
);
```

### Notice Board
```sql
CREATE TABLE notice_board (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    published_by TEXT NOT NULL,
    published_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Rooms
```sql
CREATE TABLE rooms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    room_number TEXT UNIQUE NOT NULL,
    latitude REAL,
    longitude REAL,
    radius INTEGER DEFAULT 5
);
```

## 🎨 Professional Features

### PDF Export System
- **Dual Branding**: HITK + Timely™ logos
- **Professional Layout**: Clean, institutional formatting
- **Color-Coded Status**: Present (Green), Absent (Red), Not Clicked (Yellow)
- **Summary Statistics**: Complete attendance overview
- **Automatic Download**: Descriptive filenames with session IDs

### Email Templates
- **Branded Headers**: Institutional logos and styling
- **Mobile Responsive**: Perfect display on all devices
- **Clear Instructions**: Step-by-step attendance process
- **Professional Tone**: Suitable for academic environment

### User Interface
- **Responsive Design**: Desktop and mobile optimized
- **Real-time Feedback**: Location accuracy and distance display
- **Visual Status Indicators**: Clear success/error messages
- **Progressive Enhancement**: Graceful fallback for location services

## 🧪 Testing

### Run Test Suite
```bash
pytest -q                        # Core system tests
python test_integration.py       # Integration tests
python test_logo_integration.py  # PDF branding tests
python test_features.py          # Feature validation
```

### Manual Testing
```bash
python app.py                    # Start web application
# Visit: http://localhost:5000
# Test with sample data and coordinates
```

## 🔒 Security Features

- **Location Verification**: Prevents remote attendance marking
- **Session Timeout**: Automatic expiry after 30 minutes
- **GPS Accuracy Check**: Minimum accuracy requirements
- **Role-Based Access**: HOD, Faculty, Student permissions
- **Duplicate Prevention**: Single attendance per session
- **HTTPS Required**: Location services security requirement

## 🚀 Production Deployment

### Environment Variables
```bash
export ATTENDANCE_EMAIL=your-email@domain.com
export ATTENDANCE_EMAIL_PASSWORD=your-app-password
export FLASK_SECRET_KEY=your-secret-key
export GEMINI_API_KEY=your-gemini-key
export SMTP_SERVER=smtp.yourdomain.com
```

### Production Checklist
- [ ] Enable HTTPS for location services
- [ ] Configure production email server
- [ ] Set up database backups
- [ ] Configure monitoring and logging
- [ ] Update room coordinates for actual locations
- [ ] Test all user workflows
- [ ] Verify PDF generation and branding

## 📁 Project Structure

```
Timely-Sync/
├── agents/                 # Multi-agent timetable system
├── config/                 # Configuration files
├── core/                   # Core constraint and scoring logic
├── orchestrator/           # Agent coordination
├── templates/              # Web interface templates
├── utils/                  # Utility functions
├── tests/                  # Test suite
├── outputs/                # Generated timetables and reports
├── app.py                  # Main web application
├── main.py                 # Timetable backend entry point
├── attendance_system.py    # Attendance functionality
└── requirements.txt        # Dependencies
```

## 🤝 Support & Troubleshooting

### Common Issues

1. **Location Not Working**: Enable HTTPS, check browser permissions
2. **Email Not Sending**: Verify SMTP credentials and App Password
3. **Students Not Found**: Check class format and database entries
4. **PDF Generation Fails**: Verify logo URL and network connectivity

### Configuration Files
- `config/settings.py` - Environment variables and system settings
- `config/email_config.py` - Email and room coordinate configuration

## 📄 License

This project is part of the Heritage Institute of Technology, Kolkata educational management system.

---

**Timely-Sync** - Complete educational management solution with automated timetabling, location-based attendance, and integrated communication systems. Built for modern educational institutions requiring professional, reliable, and secure academic management tools.