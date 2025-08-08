# Psychology Today Scraper

A comprehensive Python system to extract therapist information from Psychology Today and manage email outreach campaigns.

## Features

- **Web-based Dashboard**: Modern Flask interface for managing extractions and emails
- **Smart Rate Limiting**: Respectful scraping with user-agent rotation and exponential backoff
- **Two Extraction Modes**: Normal (thorough) and Ultra-Fast (parallel processing)
- **Email Management**: Review, edit, and approve emails before sending
- **Database Storage**: SQLite database for persistent data storage
- **Background Processing**: Non-blocking extraction jobs

## Quick Start

1. **Set up virtual environment:**
   ```bash
   python -m venv venv
   .\venv\Scripts\Activate.ps1  # Windows
   # or: source venv/bin/activate  # Linux/Mac
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure email settings:**
   - Edit `config.json` with your email settings

4. **Start the web application:**
   ```bash
   python app.py
   ```

5. **Open your browser:**
   ```
   http://localhost:5000
   ```

## Web Interface

### Dashboard
- View extraction statistics
- Monitor recent jobs
- Quick access to all features

### Extract Data
- Select any US state
- Choose extraction speed (Normal vs Ultra-Fast)
- Monitor progress in real-time

### Email Management
- Review all extracted emails
- Edit subject lines and content
- Approve emails individually
- Send emails in batches

### Therapist Database
- Browse all extracted therapist data
- Search and filter results
- Export to CSV

## Command Line Usage

You can still use the original command-line scripts:

```bash
# Main extraction system
python state_therapist_extractor.py

# Ultra-fast parallel version  
python fast_therapist_extractor.py
```

## Files

- **`app.py`** - Flask web application with dashboard
- **`state_therapist_extractor.py`** - Main extraction system with smart rate limiting
- **`fast_therapist_extractor.py`** - Ultra-fast parallel processing version
- **`therapist_outreach.py`** - Base classes for therapist info and email generation
- **`config.json`** - Email configuration settings
- **`templates/`** - HTML templates for web interface

## Database

The system uses SQLite to store:
- **Therapists**: All extracted therapist information
- **Email Queue**: Draft, approved, and sent emails
- **Extraction Jobs**: Status and progress of extraction tasks

## Email Workflow

1. **Extract**: Run extraction job for any state
2. **Review**: Browse generated draft emails  
3. **Edit**: Modify subject lines and content as needed
4. **Approve**: Mark emails ready for sending
5. **Send**: Batch send all approved emails

All emails are sent to your configured demo address for safety.

## Rate Limiting Features

- 8 rotating user agents
- Smart delay system (2s → 20s → 40s → 80s)
- Session rotation every 20 requests  
- 403/429 error detection and recovery
- Exponential backoff on failures

## Safety Features

- All actual emails redirected to demo address
- Manual approval required before sending
- Comprehensive error handling and logging
- Respectful of Psychology Today's servers

