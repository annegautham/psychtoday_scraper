"""
Therapist Outreach Script
========================

This script scrapes therapist information from public directories and sends personalized
outreach emails for Nexus Care platform recruitment.

Features:
- Scrapes from Psychology Today, TherapyDen, and university counseling centers
- Determines doctoral degrees for proper addressing
- Finds email addresses through multiple methods
- Sends personalized emails with anti-spam measures
- Comprehensive logging and error handling

Author: AI Assistant
Date: August 7, 2025
"""

import requests
from bs4 import BeautifulSoup
import smtplib
import time
import random
import re
import csv
import json
import logging
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from urllib.parse import urljoin, urlparse
from typing import Dict, List, Optional, Tuple
import os
from dataclasses import dataclass
import ssl
from email.utils import formataddr


@dataclass
class TherapistInfo:
    """Data class to store therapist information"""
    name: str
    credentials: str = ""
    email: str = ""
    practice_name: str = ""
    location: str = ""
    website: str = ""
    specialties: List[str] = None
    is_doctoral: bool = False
    
    def __post_init__(self):
        if self.specialties is None:
            self.specialties = []
        self.is_doctoral = self._check_doctoral_degree()
    
    def _check_doctoral_degree(self) -> bool:
        """Check if therapist has a doctoral degree"""
        doctoral_degrees = ['PHD', 'PSYD', 'EDD', 'MD', 'DMH', 'DRPH']
        credentials_upper = self.credentials.upper()
        return any(degree in credentials_upper for degree in doctoral_degrees)
    
    def get_proper_name(self) -> str:
        """Get properly formatted name for email addressing"""
        if self.is_doctoral:
            # Extract last name for Dr. title
            name_parts = self.name.strip().split()
            if len(name_parts) >= 2:
                return f"Dr. {name_parts[-1]}"
            return f"Dr. {self.name}"
        return self.name


class EmailSender:
    """Handles email sending with anti-spam measures"""
    
    def __init__(self, smtp_server: str, smtp_port: int, email: str, password: str):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.email = email
        self.password = password
        self.logger = logging.getLogger(__name__)
    
    def send_email(self, recipient: str, subject: str, body: str, sender_name: str = "Gautham Anne") -> bool:
        """Send an email with error handling"""
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = formataddr((sender_name, self.email))
            msg['To'] = recipient
            
            # Add body
            html_body = body.replace('\n', '<br>')
            text_part = MIMEText(body, 'plain')
            html_part = MIMEText(html_body, 'html')
            
            msg.attach(text_part)
            msg.attach(html_part)
            
            # Connect and send
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, context=context) as server:
                server.login(self.email, self.password)
                server.send_message(msg)
            
            self.logger.info(f"Email sent successfully to {recipient}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send email to {recipient}: {str(e)}")
            return False


class TherapistScraper:
    """Main scraper class for therapist information"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.logger = logging.getLogger(__name__)
        self.scraped_data = []
    
    def scrape_psychology_today(self, state: str, city: str = "", max_pages: int = 5) -> List[TherapistInfo]:
        """Scrape therapists from Psychology Today"""
        therapists = []
        base_url = "https://www.psychologytoday.com"
        
        try:
            # Build search URL - try different URL patterns for Psychology Today
            search_urls = [
                f"{base_url}/us/{state.lower()}/therapy",
                f"{base_url}/us/{state.upper()}/therapy", 
                f"{base_url}/therapists/{state.lower()}",
                f"{base_url}/therapists/{state.upper()}"
            ]
            
            # Try each URL pattern
            working_url = None
            for test_url in search_urls:
                self.logger.info(f"Trying Psychology Today URL: {test_url}")
                response = self.session.get(test_url, timeout=10)
                if response.status_code == 200:
                    working_url = test_url
                    self.logger.info(f"Found working URL: {working_url}")
                    break
                else:
                    self.logger.warning(f"URL failed with status {response.status_code}: {test_url}")
            
            if not working_url:
                self.logger.error(f"Could not find working Psychology Today URL for {state}")
                return therapists
            
            self.logger.info(f"Scraping Psychology Today for {state} using {working_url}")
            
            for page in range(1, max_pages + 1):
                page_url = f"{working_url}?page={page}"
                response = self.session.get(page_url, timeout=10)
                
                if response.status_code != 200:
                    self.logger.warning(f"Failed to fetch page {page}: {response.status_code}")
                    continue
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Try multiple patterns to find therapist profile links
                profile_patterns = [
                    r'/us/.*/therapy/.*',
                    r'/therapist/.*',
                    r'/profile/.*'
                ]
                
                found_profiles = False
                for pattern in profile_patterns:
                    profile_links = soup.find_all('a', href=re.compile(pattern))
                    if profile_links:
                        self.logger.info(f"Found {len(profile_links)} profile links using pattern: {pattern}")
                        found_profiles = True
                        
                        for link in profile_links[:10]:  # Limit per page
                            profile_url = urljoin(base_url, link.get('href'))
                            therapist = self._scrape_psychology_today_profile(profile_url)
                            if therapist:  # Keep even without email for now
                                therapists.append(therapist)
                                self.logger.info(f"Found therapist: {therapist.name} (Email: {therapist.email or 'None'})")
                        break
                
                if not found_profiles:
                    # Try to find any therapist-related content
                    all_links = soup.find_all('a', href=True)
                    therapist_links = [link for link in all_links if 'therapist' in link.get('href', '').lower()]
                    if therapist_links:
                        self.logger.info(f"Found {len(therapist_links)} potential therapist links")
                        for link in therapist_links[:5]:
                            profile_url = urljoin(base_url, link.get('href'))
                            therapist = self._scrape_psychology_today_profile(profile_url)
                            if therapist:
                                therapists.append(therapist)
                                self.logger.info(f"Found therapist: {therapist.name}")
                
                # Random delay between pages
                time.sleep(random.uniform(2, 5))
        
        except Exception as e:
            self.logger.error(f"Error scraping Psychology Today: {str(e)}")
        
        return therapists
    
    def _scrape_psychology_today_profile(self, url: str) -> Optional[TherapistInfo]:
        """Scrape individual therapist profile from Psychology Today"""
        try:
            response = self.session.get(url, timeout=10)
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract name - try multiple selectors
            name = ""
            name_selectors = [
                'h1.profile-title',
                'h1[data-cy="profile-name"]',
                'h1',
                '.profile-title',
                '[data-cy="profile-name"]'
            ]
            
            for selector in name_selectors:
                name_elem = soup.select_one(selector)
                if name_elem:
                    name = name_elem.get_text().strip()
                    break
            
            if not name:
                self.logger.warning(f"Could not find name in profile: {url}")
                return None
            
            # Extract credentials - try multiple selectors
            credentials = ""
            cred_selectors = [
                'span.profile-title-credentials',
                '.profile-credentials',
                '[data-cy="profile-credentials"]'
            ]
            
            for selector in cred_selectors:
                cred_elem = soup.select_one(selector)
                if cred_elem:
                    credentials = cred_elem.get_text().strip()
                    break
            
            # Extract practice information
            practice_name = ""
            practice_selectors = [
                'div.profile-practice-name',
                '.practice-name',
                '[data-cy="practice-name"]'
            ]
            
            for selector in practice_selectors:
                practice_elem = soup.select_one(selector)
                if practice_elem:
                    practice_name = practice_elem.get_text().strip()
                    break
            
            # Extract location
            location = ""
            location_selectors = [
                'span.profile-location',
                '.location',
                '[data-cy="location"]'
            ]
            
            for selector in location_selectors:
                location_elem = soup.select_one(selector)
                if location_elem:
                    location = location_elem.get_text().strip()
                    break
            
            # Extract specialties
            specialties = []
            specialty_selectors = [
                'span.profile-specialties',
                '.specialties',
                '[data-cy="specialties"]'
            ]
            
            for selector in specialty_selectors:
                specialty_elems = soup.select(selector)
                for elem in specialty_elems:
                    specialties.extend([s.strip() for s in elem.get_text().split(',')])
                if specialties:
                    break
            
            # Try to find email or website - more comprehensive search
            email = ""
            website = ""
            
            # Look for contact information in multiple places
            contact_selectors = [
                'div.profile-contact',
                '.contact-info',
                '.contact',
                '[data-cy="contact"]'
            ]
            
            for selector in contact_selectors:
                contact_section = soup.select_one(selector)
                if contact_section:
                    # Look for email links
                    email_links = contact_section.find_all('a', href=re.compile(r'mailto:'))
                    if email_links:
                        email = email_links[0].get('href').replace('mailto:', '')
                    
                    # Look for website links
                    website_links = contact_section.find_all('a', href=re.compile(r'http'))
                    if website_links:
                        website = website_links[0].get('href')
                    break
            
            # If no contact section found, search entire page
            if not email:
                all_email_links = soup.find_all('a', href=re.compile(r'mailto:'))
                if all_email_links:
                    email = all_email_links[0].get('href').replace('mailto:', '')
            
            if not website:
                all_website_links = soup.find_all('a', href=re.compile(r'http'))
                for link in all_website_links:
                    href = link.get('href', '')
                    # Skip social media and psychology today links
                    if not any(social in href.lower() for social in ['facebook', 'twitter', 'instagram', 'psychologytoday']):
                        website = href
                        break
            
            # If no email found, try to extract from website
            if not email and website:
                email = self._extract_email_from_website(website)
            
            # Create therapist info even without email (for testing)
            therapist = TherapistInfo(
                name=name,
                credentials=credentials,
                email=email,
                practice_name=practice_name,
                location=location,
                website=website,
                specialties=specialties
            )
            
            return therapist
            
        except Exception as e:
            self.logger.error(f"Error scraping profile {url}: {str(e)}")
            return None
    
    def scrape_therapyden(self, state: str, max_results: int = 50) -> List[TherapistInfo]:
        """Scrape therapists from TherapyDen"""
        therapists = []
        base_url = "https://www.therapyden.com"
        
        try:
            search_url = f"{base_url}/therapists/{state.lower()}"
            self.logger.info(f"Scraping TherapyDen for {state}")
            
            response = self.session.get(search_url, timeout=10)
            if response.status_code != 200:
                self.logger.warning(f"Failed to fetch TherapyDen: {response.status_code}")
                return therapists
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find therapist cards/links
            therapist_links = soup.find_all('a', href=re.compile(r'/therapist/'))
            
            for i, link in enumerate(therapist_links[:max_results]):
                if i >= max_results:
                    break
                
                profile_url = urljoin(base_url, link.get('href'))
                therapist = self._scrape_therapyden_profile(profile_url)
                if therapist and therapist.email:
                    therapists.append(therapist)
                    self.logger.info(f"Found TherapyDen therapist: {therapist.name}")
                
                # Delay between requests
                time.sleep(random.uniform(1, 3))
        
        except Exception as e:
            self.logger.error(f"Error scraping TherapyDen: {str(e)}")
        
        return therapists
    
    def _scrape_therapyden_profile(self, url: str) -> Optional[TherapistInfo]:
        """Scrape individual therapist profile from TherapyDen"""
        try:
            response = self.session.get(url, timeout=10)
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract name and credentials
            name = ""
            credentials = ""
            title_elem = soup.find('h1')
            if title_elem:
                title_text = title_elem.get_text().strip()
                # Split name and credentials
                if ',' in title_text:
                    name, credentials = title_text.split(',', 1)
                    name = name.strip()
                    credentials = credentials.strip()
                else:
                    name = title_text
            
            # Extract other information similar to Psychology Today
            # This would need to be customized based on TherapyDen's actual structure
            
            therapist = TherapistInfo(
                name=name,
                credentials=credentials,
                email="",  # Would need to implement email extraction
                practice_name="",
                location="",
                website=url
            )
            
            return therapist
            
        except Exception as e:
            self.logger.error(f"Error scraping TherapyDen profile {url}: {str(e)}")
            return None
    
    def scrape_university_caps(self, university_urls: List[str]) -> List[TherapistInfo]:
        """Scrape counseling center staff from university websites"""
        therapists = []
        
        for url in university_urls:
            try:
                self.logger.info(f"Scraping university CAPS: {url}")
                response = self.session.get(url, timeout=15)
                
                if response.status_code != 200:
                    continue
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Look for staff listings - this is very site-specific
                # Common patterns for staff pages
                staff_patterns = [
                    'div[class*="staff"]',
                    'div[class*="faculty"]',
                    'div[class*="therapist"]',
                    'div[class*="counselor"]',
                    '.staff-member',
                    '.faculty-member'
                ]
                
                for pattern in staff_patterns:
                    staff_elements = soup.select(pattern)
                    if staff_elements:
                        for elem in staff_elements:
                            therapist = self._extract_university_staff_info(elem, url)
                            if therapist and therapist.email:
                                therapists.append(therapist)
                        break
                
                time.sleep(random.uniform(2, 4))
                
            except Exception as e:
                self.logger.error(f"Error scraping university {url}: {str(e)}")
        
        return therapists
    
    def _extract_university_staff_info(self, element, base_url: str) -> Optional[TherapistInfo]:
        """Extract staff information from university page element"""
        try:
            # Extract name
            name_elem = element.find(['h1', 'h2', 'h3', 'h4', 'strong'])
            if not name_elem:
                return None
            name = name_elem.get_text().strip()
            
            # Extract credentials (often in parentheses or after comma)
            credentials = ""
            text = element.get_text()
            cred_match = re.search(r'([A-Z]{2,4}(?:\s*,\s*[A-Z]{2,4})*)', text)
            if cred_match:
                credentials = cred_match.group(1)
            
            # Look for email
            email = ""
            email_links = element.find_all('a', href=re.compile(r'mailto:'))
            if email_links:
                email = email_links[0].get('href').replace('mailto:', '')
            
            # Extract university name from URL
            parsed_url = urlparse(base_url)
            university_name = parsed_url.netloc.replace('www.', '').split('.')[0].title()
            
            therapist = TherapistInfo(
                name=name,
                credentials=credentials,
                email=email,
                practice_name=f"{university_name} Counseling Center",
                location=university_name,
                website=base_url
            )
            
            return therapist
            
        except Exception as e:
            self.logger.error(f"Error extracting university staff info: {str(e)}")
            return None
    
    def _extract_email_from_website(self, website_url: str) -> str:
        """Try to extract email from therapist's website"""
        try:
            response = self.session.get(website_url, timeout=10)
            if response.status_code != 200:
                return ""
            
            # Look for email patterns in the page content
            content = response.text
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            emails = re.findall(email_pattern, content)
            
            # Filter out common non-personal emails
            excluded_patterns = ['admin@', 'info@', 'contact@', 'support@', 'noreply@']
            for email in emails:
                if not any(pattern in email.lower() for pattern in excluded_patterns):
                    return email
            
            return ""
            
        except Exception as e:
            self.logger.error(f"Error extracting email from {website_url}: {str(e)}")
            return ""


class EmailTemplateGenerator:
    """Generates personalized email content"""
    
    @staticmethod
    def generate_email(therapist: TherapistInfo) -> Tuple[str, str]:
        """Generate personalized email subject and body"""
        
        # Get therapist details
        therapist_name = therapist.get_proper_name()
        
        # Determine specific specialty for subject line
        specific_specialty = "Mental Health"  # Default
        if therapist.specialties:
            if len(therapist.specialties) > 0:
                main_specialty = therapist.specialties[0].strip()
                # Clean up the specialty name for subject
                if "therapy" in main_specialty.lower():
                    specific_specialty = main_specialty
                elif "counseling" in main_specialty.lower():
                    specific_specialty = main_specialty
                else:
                    specific_specialty = f"{main_specialty} Therapy"
        elif therapist.is_doctoral:
            specific_specialty = "Clinical Psychology"
        
        # Generate subject
        subject = f"Exclusive Platform Launch for Licensed {specific_specialty} Therapists"
        
        # Generate personalized specialty details
        specialty_work = "mental health care"
        specific_detail = "evidence-based treatment methods"
        unique_approach = "client-centered therapeutic approach"
        
        if therapist.specialties and len(therapist.specialties) > 0:
            main_specialty = therapist.specialties[0].strip()
            
            # Personalize based on specialty
            if "trauma" in main_specialty.lower():
                specialty_work = f"trauma-informed therapy"
                specific_detail = "comprehensive approach to trauma recovery"
                unique_approach = "trauma-informed care methodology"
            elif "anxiety" in main_specialty.lower():
                specialty_work = f"anxiety treatment"
                specific_detail = "specialized anxiety intervention techniques"
                unique_approach = "evidence-based anxiety management strategies"
            elif "depression" in main_specialty.lower():
                specialty_work = f"depression treatment"
                specific_detail = "holistic approach to depression therapy"
                unique_approach = "comprehensive depression treatment methods"
            elif "couples" in main_specialty.lower() or "marriage" in main_specialty.lower():
                specialty_work = f"couples counseling"
                specific_detail = "relationship-focused therapeutic methods"
                unique_approach = "evidence-based couples therapy techniques"
            elif "family" in main_specialty.lower():
                specialty_work = f"family therapy"
                specific_detail = "systemic family intervention approaches"
                unique_approach = "family-centered therapeutic methods"
            elif "child" in main_specialty.lower() or "adolescent" in main_specialty.lower():
                specialty_work = f"adolescent therapy"
                specific_detail = "developmental-focused treatment approaches"
                unique_approach = "age-appropriate therapeutic interventions"
            elif "addiction" in main_specialty.lower():
                specialty_work = f"addiction recovery therapy"
                specific_detail = "comprehensive addiction treatment methods"
                unique_approach = "evidence-based recovery approaches"
            elif "cognitive" in main_specialty.lower() or "cbt" in main_specialty.lower():
                specialty_work = f"cognitive behavioral therapy"
                specific_detail = "structured CBT intervention techniques"
                unique_approach = "cognitive-behavioral therapeutic framework"
            elif "emdr" in main_specialty.lower():
                specialty_work = f"EMDR therapy"
                specific_detail = "specialized EMDR treatment protocols"
                unique_approach = "trauma-focused EMDR methodology"
            else:
                specialty_work = f"{main_specialty.lower()}"
                specific_detail = f"specialized {main_specialty.lower()} treatment approach"
                unique_approach = f"evidence-based {main_specialty.lower()} methods"
        
        # Additional personalization based on credentials
        if therapist.is_doctoral:
            if "phd" in therapist.credentials.lower():
                specific_detail = f"doctoral-level clinical expertise and {specific_detail}"
            elif "psyd" in therapist.credentials.lower():
                specific_detail = f"doctoral training in clinical psychology and {specific_detail}"
            elif "md" in therapist.credentials.lower():
                specific_detail = f"medical background and {specific_detail}"
        
        # Build email body
        body = f"""Dear {therapist_name},

I hope this email finds you well. My name is Gautham, and I'm the founder of Koamigo, a platform that's revolutionizing how people connect with mental health professionals.

I discovered your work with {specialty_work} and was truly impressed by your {specific_detail}. Your focus on {unique_approach} resonates deeply with what we're building at Koamigo.

Working alongside Licensed Psychologists at Stanford Medicine, we've designed a platform that truly supports therapists in their practice while offering the compensation and autonomy you deserve.

Our platform offers:

• Higher compensation than other online platforms
• AI-powered matching that considers therapeutic approach, personality compatibility, and specific expertise areas
• Comprehensive patient summaries from ongoing AI interactions that give you deeper insight before sessions
• Complete autonomy over your schedule and client selection - you choose which matched patients to accept

We're onboarding therapists soon and opening early access to the platform - you can secure your spot at https://koamigo.com/

Happy to set up a brief call if you're interested to discuss how we can support your practice.

Warm wishes,
Gautham Anne

Founder, Koamigo"""
        
        return subject, body


class TherapistOutreachBot:
    """Main orchestrator for the therapist outreach process"""
    
    def __init__(self, config_file: str = "config.json"):
        self.config = self._load_config(config_file)
        self._setup_logging()
        
        # Initialize components
        self.scraper = TherapistScraper()
        self.email_sender = EmailSender(
            smtp_server=self.config['email']['smtp_server'],
            smtp_port=self.config['email']['smtp_port'],
            email=self.config['email']['address'],
            password=self.config['email']['password']
        )
        self.template_generator = EmailTemplateGenerator()
        
        # Data storage
        self.all_therapists = []
        self.sent_emails = set()
        
        self.logger = logging.getLogger(__name__)
    
    def _load_config(self, config_file: str) -> dict:
        """Load configuration from JSON file"""
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            # Return default config if file doesn't exist
            return {
                "email": {
                    "smtp_server": "mail.privateemail.com",
                    "smtp_port": 465,
                    "address": "outreach@koamigo.com",
                    "password": "YOUR_PASSWORD_HERE"
                },
                "scraping": {
                    "states": ["CA", "NY", "TX", "FL"],
                    "max_therapists_per_state": 50,
                    "delay_between_emails": [30, 120],
                    "max_emails_per_day": 100
                },
                "university_caps_urls": [
                    "https://caps.northwestern.edu/staff/",
                    "https://vaden.stanford.edu/caps-and-bridge/caps/staff",
                    "https://counseling.uchicago.edu/about/staff/",
                    "https://www.berkeley.edu/counseling/staff/"
                ]
            }
    
    def _setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('therapist_outreach.log'),
                logging.StreamHandler()
            ]
        )
    
    def scrape_all_therapists(self):
        """Scrape therapists from all configured sources"""
        self.logger.info("Starting therapist scraping process...")
        
        # Scrape from Psychology Today
        for state in self.config['scraping']['states']:
            therapists = self.scraper.scrape_psychology_today(
                state=state,
                max_pages=3
            )
            self.all_therapists.extend(therapists)
            self.logger.info(f"Found {len(therapists)} therapists from Psychology Today in {state}")
            
            # Delay between states
            time.sleep(random.uniform(5, 10))
        
        # Scrape from TherapyDen
        for state in self.config['scraping']['states']:
            therapists = self.scraper.scrape_therapyden(
                state=state,
                max_results=20
            )
            self.all_therapists.extend(therapists)
            self.logger.info(f"Found {len(therapists)} therapists from TherapyDen in {state}")
            
            time.sleep(random.uniform(5, 10))
        
        # Scrape university CAPS
        university_therapists = self.scraper.scrape_university_caps(
            self.config['university_caps_urls']
        )
        self.all_therapists.extend(university_therapists)
        self.logger.info(f"Found {len(university_therapists)} therapists from university CAPS")
        
        # Remove duplicates based on email
        unique_therapists = []
        seen_emails = set()
        for therapist in self.all_therapists:
            if therapist.email and therapist.email not in seen_emails:
                unique_therapists.append(therapist)
                seen_emails.add(therapist.email)
        
        self.all_therapists = unique_therapists
        self.logger.info(f"Total unique therapists with emails: {len(self.all_therapists)}")
    
    def send_outreach_emails(self):
        """Send personalized emails to all scraped therapists"""
        self.logger.info("Starting email outreach process...")
        
        emails_sent_today = 0
        max_daily_emails = self.config['scraping']['max_emails_per_day']
        
        for i, therapist in enumerate(self.all_therapists):
            if emails_sent_today >= max_daily_emails:
                self.logger.info(f"Reached daily email limit ({max_daily_emails})")
                break
            
            if therapist.email in self.sent_emails:
                continue
            
            try:
                # Generate personalized email
                subject, body = self.template_generator.generate_email(therapist)
                
                # Send email
                success = self.email_sender.send_email(
                    recipient=therapist.email,
                    subject=subject,
                    body=body
                )
                
                if success:
                    self.sent_emails.add(therapist.email)
                    emails_sent_today += 1
                    self.logger.info(f"Email sent to {therapist.name} ({therapist.email})")
                    
                    # Save progress
                    self._save_progress()
                
                # Anti-spam delay
                delay_range = self.config['scraping']['delay_between_emails']
                delay = random.uniform(delay_range[0], delay_range[1])
                self.logger.info(f"Waiting {delay:.1f} seconds before next email...")
                time.sleep(delay)
                
            except Exception as e:
                self.logger.error(f"Error sending email to {therapist.name}: {str(e)}")
        
        self.logger.info(f"Email outreach completed. Sent {emails_sent_today} emails.")
    
    def _save_progress(self):
        """Save progress to CSV file"""
        filename = f"therapist_outreach_{datetime.now().strftime('%Y%m%d')}.csv"
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['name', 'credentials', 'email', 'practice_name', 'location', 'website', 'is_doctoral', 'email_sent']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for therapist in self.all_therapists:
                writer.writerow({
                    'name': therapist.name,
                    'credentials': therapist.credentials,
                    'email': therapist.email,
                    'practice_name': therapist.practice_name,
                    'location': therapist.location,
                    'website': therapist.website,
                    'is_doctoral': therapist.is_doctoral,
                    'email_sent': therapist.email in self.sent_emails
                })
    
    def run_full_outreach(self):
        """Run the complete outreach process"""
        self.logger.info("Starting complete therapist outreach process...")
        
        # Step 1: Scrape therapists
        self.scrape_all_therapists()
        
        # Step 2: Send emails
        self.send_outreach_emails()
        
        # Step 3: Final save
        self._save_progress()
        
        self.logger.info("Outreach process completed!")


def main():
    """Main execution function"""
    # Create and run the outreach bot
    bot = TherapistOutreachBot()
    bot.run_full_outreach()


if __name__ == "__main__":
    main()
