from app import app

if __name__ == '__main__':
    print("Starting College Timetable Management System...")
    print("Access the application at: http://localhost:5000")
    print("\nSystem Features:")
    print("- Cross-Semester Teacher Assignment")
    print("- Theory-Lab Matching Logic")
    print("- Constraint-Based Scheduling")
    print("- PDF Generation for All Sections")
    print("\nPress Ctrl+C to stop the server")
    
    app.run(debug=True, host='0.0.0.0', port=5000)