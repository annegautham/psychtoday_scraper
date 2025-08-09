# Psychology Today Therapist Scraper

A comprehensive web scraping system that extracts therapist information from Psychology Today by state and enables targeted email outreach campaigns.

## 🚀 Features

- **State-based extraction** - Extract all therapists from any US state
- **Email discovery** - Automatically finds personal email addresses from therapist websites
- **Web dashboard** - Complete Flask-based interface for management
- **Email campaigns** - Automated personalized email generation and sending
- **Real-time logging** - Comprehensive activity tracking and monitoring
- **Smart rate limiting** - Respectful scraping with anti-detection measures
- **VPN compatible** - Works with VPN services to bypass IP restrictions

## 🛠️ Quick Start

### 1. Setup
```bash
pip install -r requirements.txt
cp .env.template .env  # Configure your email settings
```

### 2. Start the Application
```bash
python app.py
```

### 3. Access Dashboard
Open http://localhost:5000 in your browser

### 4. Extract Therapists
- Use the web interface "Extract Data" page
- Or run: `python run_extraction.py`

### 5. Send Emails
- Review and approve emails in the "Email Queue"
- Or run: `python run_emails.py`

## 📊 Dashboard Features

- **📈 Dashboard** - Overview statistics and recent activity
- **🔍 Extract Data** - Start new therapist extraction jobs
- **👥 Therapists** - Browse extracted therapist database
- **📧 Email Queue** - Manage and send email campaigns
- **📝 System Logs** - Real-time activity monitoring

## 🔧 Configuration

### Email Setup
Edit `config.json`:
```json
{
  "email": {
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "email": "your-email@gmail.com",
    "password": "your-app-password"
  }
}
```

### Environment Variables
Create `.env` file:
```
FLASK_ENV=production
SECRET_KEY=your-secret-key
```

## 🚀 Deployment

### Option 1: Fly.io
```bash
fly deploy
```

### Option 2: Render
```bash
# Push to GitHub and connect to Render
```

### Option 3: Docker
```bash
docker build -t therapist-scraper .
docker run -p 5000:5000 therapist-scraper
```

## 📋 API Endpoints

- `GET /` - Dashboard
- `POST /extract` - Start extraction job
- `GET /job_status/<id>` - Check job status
- `GET /therapists` - View therapists
- `GET /emails` - Email queue management
- `GET /logs` - System logs
- `GET /api/logs` - Logs API

## ⚠️ Important Notes

- **VPN Required**: Psychology Today blocks many IPs. Use a VPN service like Hide.me, NordVPN, or ExpressVPN
- **Rate Limiting**: The system includes smart delays to respect website resources
- **Email Compliance**: All emails are sent to your configured address for compliance
- **Legal**: Review Psychology Today's Terms of Service before use

## 🔍 Troubleshooting

### "403 Forbidden" Errors
- Your IP is blocked by Psychology Today
- Solution: Connect to a VPN and try again

### No Therapists Found
- Check your VPN connection
- Verify the state name is correct
- Check system logs for detailed error messages

### Email Sending Issues
- Verify email configuration in `config.json`
- Use app-specific passwords for Gmail
- Check logs for SMTP errors

## 📁 Project Structure

```
psychtoday_scraper/
├── app.py                    # Main Flask application
├── state_therapist_extractor.py  # Core scraping logic
├── therapist_outreach.py     # Email functionality
├── run_extraction.py         # Standalone extraction script
├── run_emails.py            # Standalone email script
├── templates/               # HTML templates
├── config.json             # Email configuration
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is for educational and research purposes. Please respect website terms of service and applicable laws.

---

**Built with ❤️ for mental health accessibility**
