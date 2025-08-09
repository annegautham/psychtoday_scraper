#!/usr/bin/env python3
"""
Simple script to extract Wyoming therapists using the integrated backend
"""

import requests
import json
import time

def start_extraction():
    print("🎯 Starting Wyoming Therapist Extraction via Backend...")
    print("=" * 50)
    
    # Start extraction job through Flask API
    data = {
        'state': 'wyoming',
        'mode': 'normal'
    }
    
    try:
        # Post extraction request
        response = requests.post('http://localhost:5000/extract', data=data)
        
        if response.status_code == 200:
            result = response.json()
            job_id = result['job_id']
            print(f"✅ Extraction job started! Job ID: {job_id}")
            print(f"📋 {result['message']}")
            
            # Monitor job progress
            print("\\n🔄 Monitoring extraction progress...")
            while True:
                time.sleep(5)
                
                # Check job status
                status_response = requests.get(f'http://localhost:5000/job_status/{job_id}')
                if status_response.status_code == 200:
                    status = status_response.json()
                    
                    if status['status'] == 'completed':
                        print(f"\\n🎉 Extraction completed!")
                        print(f"📊 Total therapists found: {status['total_found']}")
                        print(f"� Therapists with emails: {status['emails_found']}")
                        break
                    elif status['status'] == 'failed':
                        print(f"\\n❌ Extraction failed: {status.get('error_message', 'Unknown error')}")
                        break
                    elif status['status'] == 'running':
                        print("   ⏳ Still extracting...")
                    else:
                        print(f"   📋 Status: {status['status']}")
                else:
                    print("   ⚠️ Could not check status")
        else:
            print(f"❌ Failed to start extraction: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to Flask app. Make sure it's running on localhost:5000")
        print("   Run: python app.py")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    start_extraction()
