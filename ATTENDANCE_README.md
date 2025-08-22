# 📍 Location-Based Attendance System

An automated attendance system that uses GPS location verification to ensure students are physically present in the classroom when marking attendance.

## 🌟 Features

- **Location Verification**: Uses GPS coordinates to verify student presence in classroom
- **Automated Email Notifications**: Sends attendance links to students via email
- **Class Format Support**: Supports format like CSE-3B (Stream-Semester+Section)
- **Real-time Distance Calculation**: Calculates distance between student and classroom
- **Configurable Radius**: Set different proximity requirements for different rooms
- **Session Management**: Time-limited attendance sessions with automatic expiry
- **Faculty Dashboard**: Easy-to-use interface for teachers to create attendance sessions

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install flask sqlite3 smtplib
```

### 2. Setup Database and Sample Data
```bash
python setup_attendance.py
```

### 3. Configure Email Settings
Update `config/email_config.py` with your email credentials:

```python
EMAIL_CONFIG = {
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 587,
    'email': 'your-email@gmail.com',
    'password': 'your-app-password',  # Use App Password for Gmail
}
```

### 4. Update Room Coordinates
Replace sample coordinates in `config/email_config.py` with your actual classroom locations:

```python
ROOM_COORDINATES = {
    'Room 101': {'lat': 22.5726, 'lng': 88.3639, 'radius': 30},
    # Add your actual room coordinates
}
```

### 5. Run the Application
```bash
python app.py
```

## 📱 How It Works

### For Faculty:
1. Login to faculty dashboard
2. Click "Create Attendance Session"
3. Enter room number and class format (e.g., CSE-3B)
4. System automatically:
   - Creates attendance session
   - Finds students in the specified class
   - Sends email notifications to all students

### For Students:
1. Receive email notification with attendance link
2. Click the link to open attendance page
3. Allow location access when prompted
4. Click "Mark Attendance"
5. System verifies location and marks attendance accordingly

## 🎯 Class Format

The system uses a specific format for classes:
- **Format**: `STREAM-SEMESTERSECTION`
- **Examples**: 
  - `CSE-3B` → Computer Science, 3rd Semester, Section B
  - `ECE-2A` → Electronics, 2nd Semester, Section A
  - `MECH-4C` → Mechanical, 4th Semester, Section C

## 📧 Email Configuration

### Gmail Setup:
1. Enable 2-factor authentication
2. Go to Google Account → Security → 2-Step Verification → App passwords
3. Generate password for "Mail"
4. Use this password in configuration (not your regular Gmail password)

### Other Email Providers:
Update SMTP settings in `config/email_config.py` according to your provider's documentation.

## 🗄️ Database Schema

The system uses SQLite with the following tables:

### Students
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
    class_name TEXT NOT NULL,
    room TEXT NOT NULL,
    teacher_lat REAL NOT NULL,
    teacher_lng REAL NOT NULL,
    radius INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP,
    is_active BOOLEAN DEFAULT 1
);
```

### Attendance Records
```sql
CREATE TABLE attendance_records (
    id INTEGER PRIMARY KEY,
    session_id TEXT NOT NULL,
    student_id INTEGER NOT NULL,
    marked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    student_lat REAL,
    student_lng REAL,
    distance REAL,
    status TEXT DEFAULT 'present',
    FOREIGN KEY (session_id) REFERENCES attendance_sessions (id),
    FOREIGN KEY (student_id) REFERENCES students (id)
);
```

## ⚙️ Configuration Options

### Attendance Settings
```python
ATTENDANCE_SETTINGS = {
    'session_duration_minutes': 30,  # Session timeout
    'location_accuracy_threshold': 100,  # GPS accuracy requirement
    'default_radius': 50,  # Default classroom radius
    'max_radius': 100,  # Maximum allowed radius
    'min_radius': 10,   # Minimum allowed radius
}
```

### Room Coordinates
```python
ROOM_COORDINATES = {
    'Room 101': {'lat': 22.5726, 'lng': 88.3639, 'radius': 30},
    'Lab A': {'lat': 22.5732, 'lng': 88.3645, 'radius': 40},
    'Auditorium': {'lat': 22.5734, 'lng': 88.3647, 'radius': 50},
}
```

## 🔧 API Endpoints

### Create Attendance Session
```
POST /create-attendance
Content-Type: application/json

{
    "room": "Room 101",
    "class_format": "CSE-3B"
}
```

### Mark Attendance
```
POST /api/mark-attendance
Content-Type: application/json

{
    "session_id": "uuid-string",
    "latitude": 22.5726,
    "longitude": 88.3639
}
```

### Get Attendance Stats
```
GET /attendance-stats/<session_id>
```

### End Session
```
POST /end-session/<session_id>
```

## 🛡️ Security Features

- **Location Verification**: Prevents remote attendance marking
- **Session Timeout**: Automatic session expiry after 30 minutes
- **GPS Accuracy Check**: Requires minimum GPS accuracy
- **Distance Calculation**: Uses Haversine formula for accurate distance measurement
- **Duplicate Prevention**: Prevents multiple attendance marks for same session

## 🎨 User Interface

- **Responsive Design**: Works on desktop and mobile devices
- **Real-time Feedback**: Shows location accuracy and distance
- **Visual Status Indicators**: Clear success/error messages
- **Progressive Enhancement**: Graceful fallback for location services

## 🔍 Troubleshooting

### Common Issues:

1. **Location Not Working**
   - Ensure HTTPS is enabled (required for location services)
   - Check browser location permissions
   - Verify GPS is enabled on device

2. **Email Not Sending**
   - Verify SMTP credentials
   - Check firewall/network restrictions
   - Ensure App Password is used for Gmail

3. **Students Not Found**
   - Verify class format (e.g., CSE-3B)
   - Check student data in database
   - Ensure class_id matches in database

4. **Distance Calculation Issues**
   - Verify room coordinates are correct
   - Check GPS accuracy (should be <100m)
   - Ensure coordinates are in decimal degrees

## 📊 Sample Data

The setup script creates sample students for testing:
- CSE 3rd Semester Section B (5 students)
- CSE 5th Semester Section A (5 students)  
- ECE 2nd Semester Section A (4 students)
- CSE 1st Semester Section B (5 students)

## 🚀 Deployment

### Production Considerations:
1. Use environment variables for sensitive configuration
2. Enable HTTPS for location services
3. Set up proper email server (not Gmail for production)
4. Configure proper database backup
5. Set up monitoring and logging
6. Use proper secret key for Flask sessions

### Environment Variables:
```bash
export ATTENDANCE_EMAIL=your-email@domain.com
export ATTENDANCE_EMAIL_PASSWORD=your-app-password
export FLASK_SECRET_KEY=your-secret-key
export SMTP_SERVER=smtp.yourdomain.com
export SMTP_PORT=587
```

## 📝 License

This project is part of the Timely™ Automated Timetable Backend system.

## 🤝 Support

For issues and questions:
1. Check the troubleshooting section
2. Verify configuration settings
3. Test with sample data first
4. Check browser console for JavaScript errors

---

**Note**: This system requires HTTPS in production for location services to work properly. Browsers block location access on non-secure connections.