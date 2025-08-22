import requests
import os

def download_logo():
    """Download HITK logo and save locally"""
    logo_url = "https://lh3.googleusercontent.com/d/1LBhx-x_Si1-cmGqsRAVmheoz0tXvJ3UN"
    
    try:
        response = requests.get(logo_url, timeout=10)
        if response.status_code == 200:
            os.makedirs('assets', exist_ok=True)
            with open('assets/hitk_logo.png', 'wb') as f:
                f.write(response.content)
            print("Logo downloaded successfully!")
            return True
    except Exception as e:
        print(f"Failed to download logo: {e}")
    
    return False

if __name__ == "__main__":
    download_logo()