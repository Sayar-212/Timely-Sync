#!/usr/bin/env python3
"""
Setup script for Location-Based Attendance System

This script helps set up the attendance system by:
1. Creating necessary database tables
2. Populating sample data
3. Configuring email settings
4. Testing the system
"""

import sqlite3
import os
import sys
from attendance_system import LocationBasedAttendanceSystem

def create_sample_students():
    """Create sample student data for testing"""
    conn = sqlite3.connect('attendance.db')
    cursor = conn.cursor()
    
    # Sample students for different classes
    sample_students = [
        # CSE 3rd Semester Section B
        (1, 'Rahul Kumar', 'rahul.kumar@student.edu', 'CSE001', 'math-cse-b', 3),
        (2, 'Priya Sharma', 'priya.sharma@student.edu', 'CSE002', 'math-cse-b', 3),
        (3, 'Amit Singh', 'amit.singh@student.edu', 'CSE003', 'math-cse-b', 3),
        (4, 'Sneha Patel', 'sneha.patel@student.edu', 'CSE004', 'math-cse-b', 3),
        (5, 'Vikram Gupta', 'vikram.gupta@student.edu', 'CSE005', 'math-cse-b', 3),
        
        # CSE 5th Semester Section A
        (11, 'Arjun Mehta', 'arjun.mehta@student.edu', 'CSE011', 'stats-cse-a', 5),
        (12, 'Pooja Agarwal', 'pooja.agarwal@student.edu', 'CSE012', 'stats-cse-a', 5),
        (13, 'Kiran Kumar', 'kiran.kumar@student.edu', 'CSE013', 'stats-cse-a', 5),
        (14, 'Neha Gupta', 'neha.gupta@student.edu', 'CSE014', 'stats-cse-a', 5),
        (15, 'Rohit Sharma', 'rohit.sharma@student.edu', 'CSE015', 'stats-cse-a', 5),
        
        # ECE 2nd Semester Section A
        (21, 'Sanjay Patel', 'sanjay.patel@student.edu', 'ECE001', 'calc-ece-a', 2),
        (22, 'Meera Singh', 'meera.singh@student.edu', 'ECE002', 'calc-ece-a', 2),
        (23, 'Ajay Kumar', 'ajay.kumar@student.edu', 'ECE003', 'calc-ece-a', 2),
        (24, 'Divya Reddy', 'divya.reddy@student.edu', 'ECE004', 'calc-ece-a', 2),
        
        # CSE 1st Semester Section B (for algebra)
        (31, 'Manish Jain', 'manish.jain@student.edu', 'CSE016', 'algebra-cse-b', 1),
        (32, 'Swati Verma', 'swati.verma@student.edu', 'CSE017', 'algebra-cse-b', 1),
        (33, 'Rajesh Kumar', 'rajesh.kumar@student.edu', 'CSE018', 'algebra-cse-b', 1),
        (34, 'Priyanka Singh', 'priyanka.singh@student.edu', 'CSE019', 'algebra-cse-b', 1),
        (35, 'Anil Sharma', 'anil.sharma@student.edu', 'CSE020', 'algebra-cse-b', 1),
    ]
    
    # Insert students (ignore if already exists)
    for student in sample_students:
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO students (id, name, email, roll_number, class_id, semester)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', student)
        except sqlite3.Error as e:
            print(f"Error inserting student {student[1]}: {e}")
    
    conn.commit()
    conn.close()
    print(f"✅ Created {len(sample_students)} sample students")

def test_system():
    """Test the attendance system"""
    print("\n🧪 Testing Attendance System...")
    
    try:
        # Initialize system
        attendance_system = LocationBasedAttendanceSystem()
        
        # Test creating a session
        session_id = attendance_system.create_attendance_session(
            'math-cse-b', 'CSE Semester 3 - Section B', 'Room 101', 22.5185485, 88.4167369
        )
        print(f"✅ Created test session: {session_id}")
        
        # Test getting students
        students = attendance_system.get_students_by_class('math-cse-b')
        print(f"✅ Found {len(students)} students for class math-cse-b")
        
        # Test marking attendance (simulate student in range)
        if students:
            result = attendance_system.mark_attendance(
                session_id, students[0]['id'], 22.5185485, 88.4167369  # Same location as teacher
            )
            print(f"✅ Test attendance marking: {result['message']}")
        
        # Test getting stats
        stats = attendance_system.get_attendance_stats(session_id)
        print(f"✅ Attendance stats: {stats}")
        
        # End session
        attendance_system.end_session(session_id)
        print("✅ Test session ended")
        
        print("\n🎉 All tests passed! System is ready to use.")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    
    return True

def setup_email_config():
    """Guide user through email configuration"""
    print("\n📧 Email Configuration Setup")
    print("=" * 50)
    
    print("""
To enable email notifications, you need to configure SMTP settings.

For Gmail:
1. Enable 2-factor authentication on your Gmail account
2. Generate an App Password:
   - Go to Google Account settings → Security → 2-Step Verification → App passwords
   - Generate password for "Mail"
3. Use the generated password (not your regular Gmail password)

For other email providers, you'll need their SMTP settings.
    """)
    
    email = input("Enter your email address: ").strip()
    if email:
        print(f"\n📝 To complete setup, set these environment variables:")
        print(f"   ATTENDANCE_EMAIL={email}")
        print(f"   ATTENDANCE_EMAIL_PASSWORD=your-app-password")
        print(f"\nOr update config/email_config.py directly")
    
    return email

def main():
    """Main setup function"""
    print("🚀 Setting up Location-Based Attendance System")
    print("=" * 60)
    
    # Check if database exists
    if not os.path.exists('attendance.db'):
        print("❌ Database not found. Please run the main app first to create tables.")
        return
    
    # Create sample students
    create_sample_students()
    
    # Setup email configuration
    setup_email_config()
    
    # Test the system
    if test_system():
        print("\n✅ Setup completed successfully!")
        print("\nNext steps:")
        print("1. Update email configuration in config/email_config.py")
        print("2. Update room coordinates with your actual locations")
        print("3. Run the Flask app: python app.py")
        print("4. Login as faculty and test creating attendance sessions")
    else:
        print("\n❌ Setup encountered issues. Please check the error messages above.")

if __name__ == "__main__":
    main()