#!/usr/bin/env python3
"""
Simple script to send emails via the Flask backend
"""

import requests
import json

def send_emails():
    print("📧 Starting Email Campaign via Backend...")
    print("=" * 50)
    
    try:
        # Get email queue status
        response = requests.get('http://localhost:5000/emails')
        
        if response.status_code == 200:
            print("✅ Connected to backend")
            
            # Check for draft emails
            api_response = requests.get('http://localhost:5000/api/logs')
            if api_response.status_code == 200:
                logs = api_response.json()['logs']
                draft_count = len([log for log in logs if 'Generated draft emails' in log])
                
                if draft_count > 0:
                    print(f"📝 Found draft emails ready for approval")
                    print("\\n🌐 Opening web interface for email management...")
                    print("👉 Go to: http://localhost:5000/emails")
                    print("\\n📋 Manual steps:")
                    print("   1. Review draft emails in the web interface")
                    print("   2. Approve emails you want to send")
                    print("   3. Use 'Send Emails' button to send approved emails")
                else:
                    print("❌ No draft emails found. Run extraction first.")
            else:
                print("⚠️ Could not check email status")
                
        else:
            print(f"❌ Could not connect to backend: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to Flask app. Make sure it's running on localhost:5000")
        print("   Run: python app.py")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    send_emails()
