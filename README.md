# Psychology Today Scraper

A Python system to extract therapist information from Psychology Today and find their email addresses.

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure email settings:**
   - Copy `.env.template` to `.env`
   - Edit `config.json` with your email settings

3. **Run the main extractor:**
   ```bash
   python state_therapist_extractor.py
   ```

## Files

- **`state_therapist_extractor.py`** - Main extraction system with smart rate limiting
- **`fast_therapist_extractor.py`** - Ultra-fast parallel processing version
- **`therapist_outreach.py`** - Base classes for therapist info and email generation
- **`config.json`** - Email configuration settings

## Features

- Extract all therapists from any US state
- Find email addresses from personal websites
- Smart rate limiting with user-agent rotation
- Save results to CSV
- Send personalized demo emails
- Two modes: Normal (thorough) and Ultra-Fast (parallel)

## Usage

Choose your state and extraction speed. The system will:
1. Find all therapist profiles for the state
2. Extract detailed information
3. Follow website redirects to find emails
4. Save everything to CSV
5. Send demo emails to your configured address

All actual emails are sent to your demo address for safety.

