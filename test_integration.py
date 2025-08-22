#!/usr/bin/env python3

import sys
import os

# Test the Routine5 integration
def test_routine5_integration():
    print("Testing Routine5 Integration...")
    
    try:
        from routine5_integration import Routine5Integration
        
        # Initialize integration
        routine5 = Routine5Integration()
        print("OK Routine5Integration initialized")
        
        # Check database status
        status = routine5.check_database_status()
        print(f"OK Database status: {status}")
        
        if status['configured']:
            print(f"  - Sections: {status['sections']}")
            print(f"  - Subjects: {status['subjects']}")
            
            # Get output files
            files = routine5.get_output_files()
            print(f"OK Found {len(files)} output files:")
            for file in files:
                print(f"  - {file['name']} ({file['size']} bytes)")
        else:
            print(f"  - Error: {status['error']}")
        
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        return False

def test_database_direct():
    print("\nTesting direct database access...")
    
    try:
        import sqlite3
        db_path = 'Routine5_lab_advanced/timetable.db'
        
        if not os.path.exists(db_path):
            print(f"ERROR Database not found: {db_path}")
            return False
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Test basic queries
        cursor.execute('SELECT COUNT(*) FROM departments')
        dept_count = cursor.fetchone()[0]
        print(f"OK Departments: {dept_count}")
        
        cursor.execute('SELECT COUNT(*) FROM subjects')
        subject_count = cursor.fetchone()[0]
        print(f"OK Subjects: {subject_count}")
        
        cursor.execute('SELECT COUNT(*) FROM sections')
        section_count = cursor.fetchone()[0]
        print(f"OK Sections: {section_count}")
        
        cursor.execute('SELECT COUNT(*) FROM theory_rooms')
        theory_rooms = cursor.fetchone()[0]
        print(f"OK Theory rooms: {theory_rooms}")
        
        cursor.execute('SELECT COUNT(*) FROM lab_rooms')
        lab_rooms = cursor.fetchone()[0]
        print(f"OK Lab rooms: {lab_rooms}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"ERROR Database error: {e}")
        return False

if __name__ == "__main__":
    print("=== Routine5 Integration Test ===")
    
    # Test database directly
    db_ok = test_database_direct()
    
    # Test integration wrapper
    integration_ok = test_routine5_integration()
    
    print(f"\n=== Results ===")
    print(f"Database: {'OK' if db_ok else 'FAILED'}")
    print(f"Integration: {'OK' if integration_ok else 'FAILED'}")
    
    if db_ok and integration_ok:
        print("\nAll tests passed! Integration is ready.")
    else:
        print("\nSome tests failed. Check the errors above.")