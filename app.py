from flask import Flask, render_template, request, jsonify, redirect, url_for
import sqlite3
import json
from datetime import datetime
import threading
import os
from state_therapist_extractor import StateTherapistExtractor
from therapist_outreach import EmailSender, EmailTemplateGenerator, TherapistInfo
import pandas as pd

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'

# Database setup
def init_db():
    conn = sqlite3.connect('therapist_data.db')
    cursor = conn.cursor()
    
    # Therapists table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS therapists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            title TEXT,
            location TEXT,
            phone TEXT,
            website TEXT,
            email TEXT,
            specialties TEXT,
            insurance TEXT,
            profile_url TEXT,
            state TEXT,
            extracted_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            email_status TEXT DEFAULT 'pending'  -- pending, approved, sent, rejected
        )
    ''')
    
    # Email queue table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS email_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            therapist_id INTEGER,
            subject TEXT,
            body TEXT,
            recipient_email TEXT,
            status TEXT DEFAULT 'draft',  -- draft, approved, sent, failed
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            sent_date TIMESTAMP,
            FOREIGN KEY (therapist_id) REFERENCES therapists (id)
        )
    ''')
    
    # Extraction jobs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS extraction_jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            state TEXT,
            status TEXT DEFAULT 'pending',  -- pending, running, completed, failed
            total_found INTEGER DEFAULT 0,
            emails_found INTEGER DEFAULT 0,
            start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            end_time TIMESTAMP,
            error_message TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

# Database helper functions
def get_db_connection():
    conn = sqlite3.connect('therapist_data.db')
    conn.row_factory = sqlite3.Row
    return conn

def save_therapists_to_db(therapists_data, state, job_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    emails_found = 0
    for therapist in therapists_data:
        cursor.execute('''
            INSERT INTO therapists (name, title, location, phone, website, email, 
                                  specialties, insurance, profile_url, state)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            therapist.get('name', ''),
            therapist.get('title', ''),
            therapist.get('location', ''),
            therapist.get('phone', ''),
            therapist.get('website', ''),
            therapist.get('email', ''),
            therapist.get('specialties', ''),
            therapist.get('insurance', ''),
            therapist.get('profile_url', ''),
            state
        ))
        
        if therapist.get('email'):
            emails_found += 1
    
    # Update job status
    cursor.execute('''
        UPDATE extraction_jobs 
        SET status = 'completed', total_found = ?, emails_found = ?, end_time = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (len(therapists_data), emails_found, job_id))
    
    conn.commit()
    conn.close()
    return emails_found

# Background extraction task
def run_extraction_task(state, job_id, mode='normal'):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE extraction_jobs SET status = "running" WHERE id = ?', (job_id,))
        conn.commit()
        conn.close()
        
        # Run the extraction
        extractor = StateTherapistExtractor()
        therapists_data = extractor.extract_state_therapists(state)
        
        # Save to database
        emails_found = save_therapists_to_db(therapists_data, state, job_id)
        
        # Generate draft emails for therapists with email addresses
        generate_draft_emails(state)
        
    except Exception as e:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE extraction_jobs 
            SET status = "failed", error_message = ?, end_time = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (str(e), job_id))
        conn.commit()
        conn.close()

def generate_draft_emails(state):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get therapists with emails from this state
    cursor.execute('''
        SELECT * FROM therapists 
        WHERE state = ? AND email IS NOT NULL AND email != ""
    ''', (state,))
    
    therapists = cursor.fetchall()
    
    for therapist in therapists:
        # Convert to TherapistInfo object
        therapist_info = TherapistInfo(
            name=therapist['name'] or '',
            credentials=therapist['title'] or '',
            email=therapist['email'] or '',
            practice_name='',
            location=therapist['location'] or '',
            website=therapist['website'] or '',
            specialties=therapist['specialties'].split(',') if therapist['specialties'] else []
        )
        
        # Generate personalized email
        subject, body = EmailTemplateGenerator.generate_email(therapist_info)
        
        # Save draft email
        cursor.execute('''
            INSERT INTO email_queue (therapist_id, subject, body, recipient_email, status)
            VALUES (?, ?, ?, ?, 'draft')
        ''', (therapist['id'], subject, body, therapist['email']))
    
    conn.commit()
    conn.close()

# Routes
@app.route('/')
def dashboard():
    conn = get_db_connection()
    
    # Get summary stats
    total_therapists = conn.execute('SELECT COUNT(*) as count FROM therapists').fetchone()['count']
    therapists_with_emails = conn.execute('SELECT COUNT(*) as count FROM therapists WHERE email IS NOT NULL AND email != ""').fetchone()['count']
    pending_emails = conn.execute('SELECT COUNT(*) as count FROM email_queue WHERE status = "draft"').fetchone()['count']
    sent_emails = conn.execute('SELECT COUNT(*) as count FROM email_queue WHERE status = "sent"').fetchone()['count']
    
    # Get recent extraction jobs
    recent_jobs = conn.execute('''
        SELECT * FROM extraction_jobs 
        ORDER BY start_time DESC 
        LIMIT 5
    ''').fetchall()
    
    conn.close()
    
    return render_template('dashboard.html', 
                         total_therapists=total_therapists,
                         therapists_with_emails=therapists_with_emails,
                         pending_emails=pending_emails,
                         sent_emails=sent_emails,
                         recent_jobs=recent_jobs)

@app.route('/extract', methods=['GET', 'POST'])
def extract_data():
    if request.method == 'POST':
        state = request.form['state']
        mode = request.form.get('mode', 'normal')
        
        # Create extraction job
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO extraction_jobs (state, status) VALUES (?, "pending")', (state,))
        job_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Start background task
        thread = threading.Thread(target=run_extraction_task, args=(state, job_id, mode))
        thread.daemon = True
        thread.start()
        
        return jsonify({'success': True, 'job_id': job_id, 'message': f'Extraction started for {state}'})
    
    return render_template('extract.html')

@app.route('/therapists')
def therapists():
    conn = get_db_connection()
    page = request.args.get('page', 1, type=int)
    per_page = 50
    offset = (page - 1) * per_page
    
    # Get therapists with pagination
    therapists = conn.execute('''
        SELECT * FROM therapists 
        ORDER BY extracted_date DESC 
        LIMIT ? OFFSET ?
    ''', (per_page, offset)).fetchall()
    
    total = conn.execute('SELECT COUNT(*) as count FROM therapists').fetchone()['count']
    conn.close()
    
    return render_template('therapists.html', 
                         therapists=therapists, 
                         page=page, 
                         total=total, 
                         per_page=per_page)

@app.route('/emails')
def emails():
    conn = get_db_connection()
    
    # Get email queue with therapist info
    emails = conn.execute('''
        SELECT eq.*, t.name, t.email as therapist_email
        FROM email_queue eq
        JOIN therapists t ON eq.therapist_id = t.id
        ORDER BY eq.created_date DESC
    ''').fetchall()
    
    conn.close()
    
    return render_template('emails.html', emails=emails)

@app.route('/email/<int:email_id>')
def email_detail(email_id):
    conn = get_db_connection()
    
    email = conn.execute('''
        SELECT eq.*, t.name, t.email as therapist_email, t.website, t.specialties
        FROM email_queue eq
        JOIN therapists t ON eq.therapist_id = t.id
        WHERE eq.id = ?
    ''', (email_id,)).fetchone()
    
    conn.close()
    
    if not email:
        return "Email not found", 404
    
    return render_template('email_detail.html', email=email)

@app.route('/approve_email/<int:email_id>', methods=['POST'])
def approve_email(email_id):
    data = request.get_json()
    subject = data.get('subject')
    body = data.get('body')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE email_queue 
        SET subject = ?, body = ?, status = 'approved'
        WHERE id = ?
    ''', (subject, body, email_id))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Email approved'})

@app.route('/send_emails', methods=['POST'])
def send_emails():
    conn = get_db_connection()
    
    # Get approved emails
    approved_emails = conn.execute('''
        SELECT eq.*, t.email as therapist_email
        FROM email_queue eq
        JOIN therapists t ON eq.therapist_id = t.id
        WHERE eq.status = 'approved'
    ''').fetchall()
    
    # Load email config
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
        email_config = config.get('email', {})
    except:
        email_config = {}
    
    # Send emails
    if email_config:
        email_sender = EmailSender(
            smtp_server=email_config.get('smtp_server', 'smtp.gmail.com'),
            smtp_port=email_config.get('smtp_port', 587),
            email=email_config.get('email', ''),
            password=email_config.get('password', '')
        )
    else:
        return jsonify({'success': False, 'message': 'Email not configured'})
    
    sent_count = 0
    
    for email in approved_emails:
        try:
            success = email_sender.send_email(
                email['therapist_email'], 
                email['subject'], 
                email['body']
            )
            
            if success:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE email_queue 
                    SET status = 'sent', sent_date = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (email['id'],))
                sent_count += 1
            else:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE email_queue 
                    SET status = 'failed'
                    WHERE id = ?
                ''', (email['id'],))
                
        except Exception as e:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE email_queue 
                SET status = 'failed'
                WHERE id = ?
            ''', (email['id'],))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': f'Sent {sent_count} emails'})

@app.route('/job_status/<int:job_id>')
def job_status(job_id):
    conn = get_db_connection()
    job = conn.execute('SELECT * FROM extraction_jobs WHERE id = ?', (job_id,)).fetchone()
    conn.close()
    
    if not job:
        return jsonify({'error': 'Job not found'}), 404
    
    return jsonify(dict(job))

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
