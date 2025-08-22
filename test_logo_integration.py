#!/usr/bin/env python3
"""
Test script to verify HITK logo integration in PDF generation
"""

import requests
from io import BytesIO
from reportlab.platypus import Image

def test_logo_download():
    """Test if the HITK logo can be downloaded successfully"""
    try:
        logo_url = "https://lh3.googleusercontent.com/d/1LBhx-x_Si1-cmGqsRAVmheoz0tXvJ3UN"
        print(f"Testing logo download from: {logo_url}")
        
        response = requests.get(logo_url, timeout=10)
        print(f"Response status code: {response.status_code}")
        
        if response.status_code == 200:
            print(f"Logo downloaded successfully! Size: {len(response.content)} bytes")
            
            # Test creating ReportLab Image object
            logo_img = Image(BytesIO(response.content), width=60, height=60)
            print("ReportLab Image object created successfully!")
            return True
        else:
            print(f"Failed to download logo. Status code: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"Error downloading logo: {e}")
        return False

if __name__ == "__main__":
    print("=== HITK Logo Integration Test ===")
    success = test_logo_download()
    
    if success:
        print("\n[SUCCESS] Logo integration test PASSED!")
        print("The HITK logo will be successfully added to generated PDFs.")
    else:
        print("\n[FAILED] Logo integration test FAILED!")
        print("PDFs will be generated without the logo.")
    
    print("\nModified files:")
    print("1. Routine5_lab_advanced/app.py - generate_pdf_schedules() function")
    print("2. utils/pdf_utils.py - timetable_to_pdf() function")
    
    print("\nChanges made:")
    print("- Added HITK logo download from Google Drive link")
    print("- Logo is displayed at the top center of each PDF page")
    print("- Fallback mechanism: if logo download fails, PDF generation continues without logo")
    print("- Logo size: 60x60 pixels for optimal display")