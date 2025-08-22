import sqlite3
import os
import sys
import shutil
from datetime import datetime

class Routine5Integration:
    def __init__(self):
        self.routine5_path = 'Routine5_lab_advanced'
        self.db_path = os.path.join(self.routine5_path, 'timetable.db')
        
    def check_database_status(self):
        """Check if Routine5 database is configured"""
        if not os.path.exists(self.db_path):
            return {'configured': False, 'error': 'Database not found'}
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if departments exist
            cursor.execute('SELECT COUNT(*) FROM departments')
            dept_count = cursor.fetchone()[0]
            
            if dept_count == 0:
                conn.close()
                return {'configured': False, 'error': 'No departments configured'}
            
            # Get basic stats
            cursor.execute('SELECT id FROM departments LIMIT 1')
            dept_id = cursor.fetchone()[0]
            
            cursor.execute('''
                SELECT COUNT(*) FROM sections sec 
                JOIN years y ON sec.year_id = y.id 
                WHERE y.department_id = ?
            ''', (dept_id,))
            section_count = cursor.fetchone()[0]
            
            cursor.execute('''
                SELECT COUNT(*) FROM subjects s 
                JOIN semesters sem ON s.semester_id = sem.id 
                JOIN years y ON sem.year_id = y.id 
                WHERE y.department_id = ?
            ''', (dept_id,))
            subject_count = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'configured': True,
                'department_id': dept_id,
                'sections': section_count,
                'subjects': subject_count
            }
            
        except Exception as e:
            return {'configured': False, 'error': str(e)}
    
    def generate_timetables(self):
        """Generate timetables using Routine5 exact logic"""
        try:
            # Add Routine5 path to sys.path temporarily
            if self.routine5_path not in sys.path:
                sys.path.insert(0, self.routine5_path)
            
            # Import Routine5 modules
            from app import generate_timetable, app
            
            # Check database status
            status = self.check_database_status()
            if not status['configured']:
                return {'success': False, 'error': status['error']}
            
            dept_id = status['department_id']
            
            # Call Routine5 generation function
            # Monkey patch the request to simulate POST data
            import flask
            with app.test_request_context('/api/generate_timetable', method='POST', json={'department_id': dept_id}):
                response = generate_timetable()
                result = response.get_json()
            
            # Clean up sys.path
            if self.routine5_path in sys.path:
                sys.path.remove(self.routine5_path)
            
            return result
            
        except Exception as e:
            # Clean up sys.path on error
            if self.routine5_path in sys.path:
                sys.path.remove(self.routine5_path)
            return {'success': False, 'error': str(e)}
    
    def get_output_files(self):
        """Get list of generated output files"""
        output_dir = os.path.join(self.routine5_path, 'output')
        if not os.path.exists(output_dir):
            return []
        
        files = []
        for filename in os.listdir(output_dir):
            if filename.endswith('.pdf'):
                files.append({
                    'name': filename,
                    'path': os.path.join(output_dir, filename),
                    'size': os.path.getsize(os.path.join(output_dir, filename))
                })
        
        return files
    
    def copy_sample_database(self):
        """Copy sample database if needed"""
        try:
            # Check if we have a sample database
            sample_db = os.path.join(self.routine5_path, 'timetable_sample.db')
            if os.path.exists(sample_db) and not os.path.exists(self.db_path):
                shutil.copy2(sample_db, self.db_path)
                return True
            return False
        except Exception:
            return False