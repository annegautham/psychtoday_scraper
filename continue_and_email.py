#!/usr/bin/env python3
"""
Continue extraction and then send emails
"""

import pandas as pd
import os
from therapist_outreach import TherapistInfo, EmailTemplateGenerator, EmailSender

def continue_and_email():
    print("📧 Checking for existing therapist data...")
    
    # Check if we have a progress file
    progress_file = "wyoming_progress.csv"
    
    if os.path.exists(progress_file):
        df = pd.read_csv(progress_file)
        print(f"✅ Found {len(df)} therapists in progress file")
        
        # Filter those with emails
        with_emails = df[df['email'].notna() & (df['email'] != '')]
        print(f"📧 Found {len(with_emails)} therapists with emails:")
        
        for _, row in with_emails.iterrows():
            print(f"  • {row['name']} - {row['email']}")
        
        if len(with_emails) > 0:
            print(f"\\n🚀 Sending emails to {len(with_emails)} therapists...")
            
            # Set up email system
            sender = EmailSender()
            generator = EmailTemplateGenerator()
            
            sent_count = 0
            for _, row in with_emails.iterrows():
                therapist = TherapistInfo(
                    name=row['name'],
                    email=row['email'],
                    location=row['location'],
                    specialties=row.get('specialties', ''),
                    website=row.get('website', '')
                )
                
                try:
                    print(f"📤 Sending to {therapist.name}...")
                    success = sender.send_email(therapist, generator)
                    if success:
                        sent_count += 1
                        print(f"  ✅ Email sent!")
                    else:
                        print(f"  ❌ Failed to send")
                except Exception as e:
                    print(f"  💥 Error: {e}")
            
            print(f"\\n🎉 Email campaign complete! Sent {sent_count}/{len(with_emails)} emails.")
        else:
            print("❌ No therapists with emails found yet.")
    else:
        print("❌ No progress file found. Run extraction first.")

if __name__ == "__main__":
    continue_and_email()
