import subprocess
import time
import json
import threading
import os
from pyngrok import ngrok

class NgrokManager:
    def __init__(self, auth_token="31K71sh060wpPhNFWWwQAB81wRp_4hNr7sY5NpC9Za5zDoCm4"):
        self.auth_token = auth_token
        self.ngrok_process = None
        self.public_url = None
        
    def start_ngrok(self, port=5000):
        """Start ngrok tunnel using pyngrok"""
        try:
            # Kill any existing sessions first
            ngrok.kill()
            
            # Set auth token
            ngrok.set_auth_token(self.auth_token)
            
            # Start tunnel
            tunnel = ngrok.connect(port)
            self.public_url = tunnel.public_url
            
            print(f"✅ Ngrok tunnel started: {self.public_url}")
            return self.public_url
            
        except Exception as e:
            print(f"❌ Failed to start ngrok: {e}")
            # Force cleanup
            import subprocess
            try:
                subprocess.run(['taskkill', '/f', '/im', 'ngrok.exe'], capture_output=True)
            except:
                pass
            return None
    
    def get_public_url(self):
        """Get the public URL"""
        return self.public_url
    
    def stop_ngrok(self):
        """Stop ngrok tunnel"""
        try:
            if self.public_url:
                ngrok.disconnect(self.public_url)
            ngrok.kill()
            self.public_url = None
            print("🛑 Ngrok tunnel stopped")
        except Exception as e:
            print(f"Error stopping ngrok: {e}")
            # Force kill any remaining processes
            import subprocess
            try:
                subprocess.run(['taskkill', '/f', '/im', 'ngrok.exe'], capture_output=True)
            except:
                pass
            self.public_url = None

# Global ngrok manager instance
ngrok_manager = NgrokManager()

def start_ngrok_for_attendance():
    """Start ngrok for attendance session and auto-close after 5 minutes"""
    import threading
    import time
    
    # Start ngrok
    ngrok_manager.start_ngrok()
    
    # Schedule auto-close after 5 minutes
    def auto_close():
        time.sleep(300)  # 5 minutes
        print("⏰ Auto-closing ngrok tunnel after 5 minutes")
        ngrok_manager.stop_ngrok()
    
    threading.Thread(target=auto_close, daemon=True).start()
    
    return ngrok_manager.public_url or "http://localhost:5000"

def ensure_ngrok_running():
    """Get current ngrok URL or localhost"""
    return ngrok_manager.public_url or "http://localhost:5000"