"""
State-Based Therapist Extraction System
======================================

Comprehensive system to extract all therapist information by state,
save to CSV, and send emails to those with personal website emails.
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
import pandas as pd
import re
import time
import json
import random
import csv
from datetime import datetime
from therapist_outreach import TherapistInfo, EmailTemplateGenerator, EmailSender

class StateTherapistExtractor:
    def __init__(self):
        self.session = requests.Session()
        
        # Rotating User Agents for better anti-detection
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:122.0) Gecko/20100101 Firefox/122.0',
            'Mozilla/5.0 (X11; Linux x86_64; rv:122.0) Gecko/20100101 Firefox/122.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/121.0.0.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2.1 Safari/605.1.15'
        ]
        
        # Enhanced headers for better stealth
        self.base_headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        }
        
        # Rate limiting tracking
        self.request_count = 0
        self.last_request_time = 0
        self.rate_limit_hit = False
        self.consecutive_errors = 0
        
        # Initialize session with random user agent
        self.rotate_session()
        
        # Connection pooling with retry strategy
        retry_strategy = Retry(
            total=5,
            status_forcelist=[403, 429, 500, 502, 503, 504],
            backoff_factor=2,
            respect_retry_after_header=True
        )
        
        adapter = HTTPAdapter(
            pool_connections=5, 
            pool_maxsize=10,
            max_retries=retry_strategy
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
        self.driver = None
        self.cache = {}  # Simple cache for parsed data
        
    def rotate_session(self):
        """Rotate user agent and clear session cookies for stealth"""
        user_agent = random.choice(self.user_agents)
        headers = self.base_headers.copy()
        headers['User-Agent'] = user_agent
        
        self.session.headers.clear()
        self.session.headers.update(headers)
        self.session.cookies.clear()
        
        print(f"Rotated to: {user_agent[:50]}...")
    
    def smart_delay(self, base_delay=3, is_error=False):
        """Implement smart delays with exponential backoff on errors"""
        current_time = time.time()
        
        # Calculate delay based on request frequency
        if self.last_request_time > 0:
            time_since_last = current_time - self.last_request_time
            if time_since_last < 1:  # Too fast
                base_delay *= 2
        
        # Exponential backoff on consecutive errors
        if is_error:
            self.consecutive_errors += 1
            delay = base_delay * (2 ** min(self.consecutive_errors, 4))  # Cap at 16x
            print(f"Error delay: {delay:.1f}s (error #{self.consecutive_errors})")
        else:
            self.consecutive_errors = 0  # Reset on success
            delay = base_delay
        
        # Add randomization to avoid pattern detection
        actual_delay = random.uniform(delay * 0.8, delay * 1.5)
        
        # Rate limit recovery
        if self.rate_limit_hit:
            actual_delay = max(actual_delay, 30)  # Minimum 30s after rate limit
            print(f"Rate limit recovery delay: {actual_delay:.1f}s")
        
        if actual_delay > 1:
            print(f"Waiting {actual_delay:.1f} seconds...")
            time.sleep(actual_delay)
        
        self.last_request_time = time.time()
        self.request_count += 1
        
        # Rotate session every 20 requests
        if self.request_count % 20 == 0:
            self.rotate_session()
    
    def make_request(self, url, timeout=20, max_retries=3):
        """Make HTTP request with smart retry logic and rate limit detection"""
        
        for attempt in range(max_retries):
            try:
                # Smart delay before request
                is_retry = attempt > 0
                self.smart_delay(base_delay=5 if is_retry else 3, is_error=is_retry)
                
                response = self.session.get(url, timeout=timeout)
                
                # Check for rate limiting
                if response.status_code == 403:
                    self.rate_limit_hit = True
                    print(f"Rate limited on attempt {attempt + 1}")
                    
                    if attempt < max_retries - 1:
                        wait_time = 60 * (2 ** attempt)  # 1min, 2min, 4min
                        print(f"Waiting {wait_time/60:.1f} minutes before retry...")
                        time.sleep(wait_time)
                        self.rotate_session()  # New session for retry
                        continue
                    else:
                        raise requests.exceptions.RequestException(f"Rate limited after {max_retries} attempts")
                
                elif response.status_code == 429:  # Too Many Requests
                    retry_after = response.headers.get('Retry-After', 60)
                    print(f"Server says retry after {retry_after} seconds")
                    time.sleep(int(retry_after) + 10)
                    continue
                
                elif response.status_code == 200:
                    self.rate_limit_hit = False  # Reset rate limit flag on success
                    return response
                
                else:
                    print(f"HTTP {response.status_code} on attempt {attempt + 1}")
                    if attempt < max_retries - 1:
                        continue
                    else:
                        response.raise_for_status()
                        
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                print(f"Network error on attempt {attempt + 1}: {type(e).__name__}")
                if attempt < max_retries - 1:
                    continue
                else:
                    raise
        
        return None
        
    def setup_chrome_driver(self):
        """Setup Chrome driver for website redirects - optimized for stealth"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-logging')
        chrome_options.add_argument('--log-level=3')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-plugins')
        
        # Use random user agent for Chrome too
        user_agent = random.choice(self.user_agents)
        chrome_options.add_argument(f'--user-agent={user_agent}')
        
        # Additional stealth options
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--disable-features=VizDisplayCompositor')
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
        
        # Randomize window size slightly
        width = random.randint(1366, 1920)
        height = random.randint(768, 1080)
        chrome_options.add_argument(f'--window-size={width},{height}')
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.set_page_load_timeout(15)
            
            # Hide automation indicators
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            return True
        except WebDriverException as e:
            print(f"Chrome WebDriver error: {e}")
            return False
    
    def extract_state_therapists(self, state_name):
        """Main function to extract all therapists from a state"""
        
        print(f"="*80)
        print(f"EXTRACTING THERAPISTS FROM {state_name.upper()}")
        print("="*80)
        
        # Get profile URLs
        profile_urls = self.get_state_profile_urls(state_name)
        if not profile_urls:
            print(f"No profiles found for {state_name}")
            return []
        
        print(f"Found {len(profile_urls)} therapist profiles")
        
        # Setup Selenium for website redirects
        if not self.setup_chrome_driver():
            print("Cannot proceed without Chrome driver")
            return []
        
        try:
            # Extract detailed information for each therapist
            therapists_data = []
            
            for i, profile_url in enumerate(profile_urls, 1):
                print(f"\\n--- Processing {i}/{len(profile_urls)} ---")
                print(f"Profile: {profile_url.split('/')[-2]}")
                
                therapist_data = self.extract_single_therapist(profile_url)
                if therapist_data:
                    therapists_data.append(therapist_data)
                    status = "WITH EMAIL" if therapist_data['email'] else "NO EMAIL"
                    print(f"{status}: {therapist_data['name']}")
                else:
                    print("Failed to extract")
                
                # Save progress every 25 therapists
                if i % 25 == 0:
                    temp_filename = f"{state_name.lower()}_progress.csv"
                    try:
                        df = pd.DataFrame(therapists_data)
                        df.to_csv(temp_filename, index=False, encoding='utf-8')
                        print(f"\\nProgress saved: {len(therapists_data)} therapists to {temp_filename}")
                    except Exception as e:
                        print(f"Error saving progress: {e}")
                
                # Smart rate limiting between therapists (handled in make_request)
                # But add a small additional delay for Selenium operations
                if i < len(profile_urls):
                    additional_delay = random.uniform(1, 3)
                    time.sleep(additional_delay)
            
            return therapists_data
            
        finally:
            if self.driver:
                self.driver.quit()
    
    def get_state_profile_urls(self, state_name):
        """Get all therapist profile URLs for a state (handles pagination with smart rate limiting)"""
        
        profile_urls = []
        page = 1
        max_pages = 25  # Safety limit to prevent infinite loops
        
        print(f"🔍 Starting URL extraction for {state_name} with smart rate limiting...")
        
        while page <= max_pages:
            if page == 1:
                state_url = f"https://www.psychologytoday.com/us/therapists/{state_name.lower()}"
            else:
                state_url = f"https://www.psychologytoday.com/us/therapists/{state_name.lower()}?page={page}"
            
            print(f"� Fetching page {page}: {state_url}")
            
            try:
                # Use smart request method
                response = self.make_request(state_url)
                
                if not response or response.status_code != 200:
                    print(f"❌ Failed to load page {page}: {response.status_code if response else 'No response'}")
                    break
                
                soup = BeautifulSoup(response.content, 'html.parser')
                results_rows = soup.select('.results-row')
                
                if not results_rows:
                    print(f"✅ No more results on page {page}, stopping")
                    break
                
                page_urls = []
                for row in results_rows:
                    links = row.find_all('a', href=True)
                    for link in links:
                        href = link.get('href', '')
                        if '/us/therapists/' in href and not any(skip in href for skip in ['?', '#']):
                            if href.startswith('/'):
                                full_url = 'https://www.psychologytoday.com' + href
                            else:
                                full_url = href
                            
                            if full_url not in profile_urls and full_url not in page_urls:
                                page_urls.append(full_url)
                
                if not page_urls:
                    print(f"✅ No new profiles on page {page}, stopping")
                    break
                
                profile_urls.extend(page_urls)
                print(f"   📄 Found {len(page_urls)} profiles on page {page} (total: {len(profile_urls)})")
                
                # Check for pagination - look for page links with higher numbers
                pagination_links = soup.find_all('a', href=re.compile(r'page=\d+'))
                max_page = 1
                
                if pagination_links:
                    for link in pagination_links:
                        href = link.get('href', '')
                        page_match = re.search(r'page=(\d+)', href)
                        if page_match:
                            page_num = int(page_match.group(1))
                            max_page = max(max_page, page_num)
                
                # Also check for "Next" button
                next_page = soup.find('a', {'aria-label': 'Next page'}) or soup.find('a', string='Next')
                
                # Continue if we haven't reached the last page or there's a next button
                if page < max_page or next_page:
                    page += 1
                    print(f"   ➡️ Going to page {page} (max detected: {max_page})")
                else:
                    print(f"✅ Reached final page {page} (max: {max_page}), stopping")
                    break
                
                # Additional delay between pages (handled by smart_delay in make_request)
                
            except Exception as e:
                print(f"❌ Error fetching page {page}: {e}")
                # Try to continue with next page after error delay
                self.smart_delay(base_delay=10, is_error=True)
                page += 1
                if page > max_pages:
                    break
                continue
        
        print(f"🎯 Total profiles found across all pages: {len(profile_urls)}")
        return profile_urls
    
    def extract_single_therapist(self, profile_url):
        """Extract complete information for a single therapist with smart rate limiting"""
        
        try:
            # Load profile with smart request handling
            response = self.make_request(profile_url)
            
            if not response or response.status_code != 200:
                print(f"   ❌ Failed to load profile: {response.status_code if response else 'No response'}")
                return None
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract basic information
            therapist_data = {
                'profile_url': profile_url,
                'name': self.extract_name(soup),
                'credentials': self.extract_credentials(soup),
                'location': self.extract_location(soup),
                'phone': self.extract_phone(soup),
                'practice_name': self.extract_practice_name(soup),
                'specialties': ', '.join(self.extract_specialties(soup)),
                'insurance': ', '.join(self.extract_insurance(soup)),
                'session_fee': self.extract_session_fee(soup),
                'languages': ', '.join(self.extract_languages(soup)),
                'therapy_types': ', '.join(self.extract_therapy_types(soup)),
                'website': '',
                'email': '',
                'extraction_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'has_doctoral_degree': False
            }
            
            # Check for doctoral degrees
            therapist_data['has_doctoral_degree'] = any(
                cred in therapist_data['credentials'].upper() 
                for cred in ['PHD', 'PSYD', 'EDD', 'MD']
            )
            
            print(f"   Name: {therapist_data['name']}")
            print(f"   Credentials: {therapist_data['credentials']}")
            print(f"   Location: {therapist_data['location']}")
            
            # Check for direct email on Psychology Today
            direct_email = self.extract_direct_email(soup)
            if direct_email:
                therapist_data['email'] = direct_email
                print(f"   Direct email: {direct_email}")
            
            # Look for website and extract email if available
            website_links = soup.find_all('a', href=re.compile(r'/us/profile/\d+/website'))
            
            if website_links:
                print(f"   Following website redirect...")
                website_url, website_email = self.follow_website_redirect(profile_url, website_links[0])
                
                if website_url:
                    therapist_data['website'] = website_url
                    print(f"   Website: {website_url}")
                
                if website_email:
                    therapist_data['email'] = website_email
                    print(f"   Website email: {website_email}")
                else:
                    print(f"   No email found on website")
            else:
                print(f"   No website link found")
            
            return therapist_data
            
        except Exception as e:
            print(f"   Error extracting therapist: {e}")
            return None
    
    def follow_website_redirect(self, profile_url, website_link):
        """Use Selenium to follow website redirect and extract email with smart delays"""
        
        website_redirect = website_link.get('href')
        if website_redirect.startswith('/'):
            website_redirect = 'https://www.psychologytoday.com' + website_redirect
        
        try:
            self.driver.get(website_redirect)
            
            # Smart wait for page to load
            wait_time = random.uniform(3, 7)
            time.sleep(wait_time)
            
            final_url = self.driver.current_url
            
            if ('psychologytoday.com' not in final_url and 
                final_url != website_redirect):
                
                # Extract email from external website
                page_source = self.driver.page_source
                soup = BeautifulSoup(page_source, 'html.parser')
                email = self.extract_emails_from_website(soup)
                
                return final_url, email
            
            return "", ""
            
        except (TimeoutException, WebDriverException, ConnectionResetError, Exception) as e:
            print(f"     Redirect error: {type(e).__name__}: {e}")
            return "", ""
    
    def extract_name(self, soup):
        """Extract therapist name"""
        name_elem = soup.select_one('h1')
        if name_elem:
            name = name_elem.get_text(strip=True)
            name = re.sub(r'\(.*?\)', '', name)
            name = re.sub(r'Verified.*', '', name, re.IGNORECASE)
            return name.strip()
        return ""
    
    def extract_credentials(self, soup):
        """Extract credentials"""
        text = soup.get_text()
        patterns = [r'\b(PhD|PsyD|EdD|MD|LCSW|LMFT|LPC|LMHC|LPCC|LCPC|LMHP)\b']
        
        all_creds = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            all_creds.extend(matches)
        
        unique_creds = list(set(all_creds))
        return ', '.join(unique_creds[:5])
    
    def extract_location(self, soup):
        """Extract location"""
        text = soup.get_text()
        # Look for city, state patterns
        location_patterns = [
            r'([A-Za-z\s]+),\s*([A-Z]{2})\b',
            r'([A-Za-z\s]+)\s+([A-Z]{2})\s+\d{5}'
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, text)
            if match:
                return f"{match.group(1).strip()}, {match.group(2)}"
        
        return ""
    
    def extract_phone(self, soup):
        """Extract phone number"""
        text = soup.get_text()
        phone_patterns = [
            r'\(?\d{3}\)?[-\s]?\d{3}[-\s]?\d{4}',
            r'\d{3}\.\d{3}\.\d{4}'
        ]
        
        for pattern in phone_patterns:
            match = re.search(pattern, text)
            if match:
                # Clean and format phone number
                clean_phone = re.sub(r'[^\d]', '', match.group())
                if len(clean_phone) == 10:
                    return f"({clean_phone[:3]}) {clean_phone[3:6]}-{clean_phone[6:]}"
        
        return ""
    
    def extract_practice_name(self, soup):
        """Extract practice name"""
        selectors = ['.practice-name', '.organization-name', '[data-cy="practice-name"]']
        
        for selector in selectors:
            elem = soup.select_one(selector)
            if elem:
                return elem.get_text(strip=True)
        
        return ""
    
    def extract_specialties(self, soup):
        """Extract specialties/issues treated"""
        text = soup.get_text().lower()
        
        # Common therapy specialties
        specialties = [
            'anxiety', 'depression', 'trauma', 'ptsd', 'adhd', 'addiction',
            'couples therapy', 'family therapy', 'grief', 'bipolar',
            'eating disorders', 'ocd', 'panic attacks', 'phobias',
            'relationship issues', 'stress', 'anger management'
        ]
        
        found = []
        for specialty in specialties:
            if specialty in text:
                found.append(specialty.title())
        
        return found[:8]  # Limit to top 8
    
    def extract_insurance(self, soup):
        """Extract accepted insurance"""
        text = soup.get_text()
        
        insurance_companies = [
            'Aetna', 'Anthem', 'Blue Cross', 'Cigna', 'Humana',
            'Kaiser', 'Medicare', 'Medicaid', 'UnitedHealth',
            'Tricare', 'BCBS'
        ]
        
        found = []
        for insurance in insurance_companies:
            if insurance.lower() in text.lower():
                found.append(insurance)
        
        return found[:5]
    
    def extract_session_fee(self, soup):
        """Extract session fee information"""
        text = soup.get_text()
        
        # Look for fee patterns
        fee_patterns = [
            r'\$\d{2,3}(?:-\$?\d{2,3})?',
            r'\d{2,3}\s*-\s*\d{2,3}\s*(?:per|/)?\s*session'
        ]
        
        for pattern in fee_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group()
        
        return ""
    
    def extract_languages(self, soup):
        """Extract languages spoken"""
        text = soup.get_text()
        
        languages = [
            'Spanish', 'French', 'German', 'Italian', 'Portuguese',
            'Chinese', 'Japanese', 'Korean', 'Arabic', 'Russian',
            'Hindi', 'Vietnamese', 'Tagalog'
        ]
        
        found = []
        for language in languages:
            if language.lower() in text.lower():
                found.append(language)
        
        return found
    
    def extract_therapy_types(self, soup):
        """Extract therapy modalities/types"""
        text = soup.get_text().lower()
        
        modalities = [
            'cognitive behavioral', 'cbt', 'dbt', 'emdr', 'psychodynamic',
            'humanistic', 'solution focused', 'gestalt', 'mindfulness',
            'narrative therapy', 'family systems', 'acceptance commitment'
        ]
        
        found = []
        for modality in modalities:
            if modality in text:
                found.append(modality.title())
        
        return found[:5]
    
    def extract_direct_email(self, soup):
        """Extract email from Psychology Today profile"""
        # Look for mailto links
        mailto_links = soup.find_all('a', href=re.compile(r'^mailto:', re.I))
        for link in mailto_links:
            email = link.get('href', '').replace('mailto:', '').strip()
            if self.is_valid_email(email):
                return email
        
        # Look for email patterns in text
        text = soup.get_text()
        emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
        
        for email in emails:
            if self.is_valid_email(email):
                return email
        
        return ""
    
    def extract_emails_from_website(self, soup):
        """Extract email from external website"""
        emails = []
        
        # Look for mailto links first
        mailto_links = soup.find_all('a', href=re.compile(r'^mailto:', re.I))
        for link in mailto_links:
            email = link.get('href', '').replace('mailto:', '').strip()
            if '?' in email:
                email = email.split('?')[0]
            if self.is_valid_email(email):
                emails.append(email)
        
        # Look for email patterns in text
        text = soup.get_text()
        email_patterns = re.findall(r'(?<!\w)[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}(?!\w)', text)
        
        for email in email_patterns:
            email = email.strip()
            # Clean email of any extra characters
            email = re.sub(r'[^A-Za-z0-9._%+-@]', '', email)
            if self.is_valid_email(email):
                emails.append(email)
        
        # Return first valid email
        unique_emails = list(set(emails))
        return unique_emails[0] if unique_emails else ""
    
    def is_valid_email(self, email):
        """Check if email is valid"""
        if not email or '@' not in email:
            return False
        
        # Filter out generic emails
        generic = [
            'noreply', 'admin', 'support', 'webmaster', 'postmaster',
            'example.com', 'test@', 'no-reply', 'info@'
        ]
        
        email_lower = email.lower()
        for pattern in generic:
            if pattern in email_lower:
                return False
        
        # Basic email validation
        parts = email.split('@')
        if len(parts) != 2:
            return False
        
        domain = parts[1]
        if '.' not in domain or len(domain.split('.')[-1]) < 2:
            return False
        
        return True
    
    def save_to_csv(self, therapists_data, state_name):
        """Save therapist data to CSV file"""
        
        if not therapists_data:
            print("No data to save")
            return None
        
        filename = f"{state_name.lower()}.csv"
        
        # Define CSV columns
        columns = [
            'name', 'credentials', 'has_doctoral_degree', 'email', 'phone',
            'practice_name', 'location', 'website', 'specialties',
            'insurance', 'session_fee', 'languages', 'therapy_types',
            'profile_url', 'extraction_date'
        ]
        
        try:
            df = pd.DataFrame(therapists_data)
            df = df.reindex(columns=columns, fill_value='')
            df.to_csv(filename, index=False, encoding='utf-8')
            
            print(f"\\nData saved to: {filename}")
            print(f"Total therapists: {len(therapists_data)}")
            
            email_count = len([t for t in therapists_data if t.get('email')])
            print(f"Therapists with emails: {email_count}")
            
            doctoral_count = len([t for t in therapists_data if t.get('has_doctoral_degree')])
            print(f"Therapists with doctoral degrees: {doctoral_count}")
            
            return filename
            
        except Exception as e:
            print(f"Error saving CSV: {e}")
            return None
    
    def send_emails_to_therapists(self, therapists_data, state_name):
        """Send emails to therapists who have email addresses"""
        
        # Filter for therapists with emails
        email_therapists = [t for t in therapists_data if t.get('email')]
        
        if not email_therapists:
            print("No therapists with emails found")
            return
        
        print(f"\\nSENDING EMAILS TO {len(email_therapists)} THERAPISTS")
        print("="*60)
        
        # Load email configuration
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
        except Exception as e:
            print(f"Error loading email config: {e}")
            return
        
        email_sender = EmailSender(
            smtp_server=config['email']['smtp_server'],
            smtp_port=config['email']['smtp_port'],
            email=config['email']['address'],
            password=config['email']['password']
        )
        
        template_generator = EmailTemplateGenerator()
        demo_recipient = "annegautham@gmail.com"
        
        for i, therapist_data in enumerate(email_therapists, 1):
            print(f"\\nEmail {i}/{len(email_therapists)}: {therapist_data['name']}")
            
            # Create TherapistInfo object
            therapist = TherapistInfo(
                name=therapist_data['name'],
                credentials=therapist_data['credentials'],
                email=therapist_data['email'],
                practice_name=therapist_data['practice_name'] or 'Private Practice',
                location=therapist_data['location'],
                website=therapist_data['website'] or therapist_data['profile_url'],
                specialties=therapist_data['specialties'].split(', ') if therapist_data['specialties'] else []
            )
            
            # Generate email content
            subject, body = template_generator.generate_email(therapist)
            
            # Create demo email
            demo_subject = f"[{state_name.upper()} THERAPIST DEMO {i}] {subject}"
            demo_body = f"""
=== {state_name.upper()} THERAPIST OUTREACH DEMO #{i} ===
Source: Psychology Today + Selenium Website Scraping

Therapist Details:
- Name: {therapist_data['name']}
- Credentials: {therapist_data['credentials']}
- Has Doctoral Degree: {therapist_data['has_doctoral_degree']}
- Location: {therapist_data['location']}
- Practice: {therapist_data['practice_name']}
- Phone: {therapist_data['phone']}
- Personal Website: {therapist_data['website']}
- Email Found: {therapist_data['email']}
- Specialties: {therapist_data['specialties']}
- Insurance: {therapist_data['insurance']}
- Session Fee: {therapist_data['session_fee']}
- Languages: {therapist_data['languages']}
- Therapy Types: {therapist_data['therapy_types']}

=== PERSONALIZED EMAIL CONTENT ===

{body}

=== END DEMO EMAIL ===

🎯 This would be sent to: {therapist_data['email']}
✅ Real {state_name} therapist with extracted email from personal website
"""
            
            # Send email
            success = email_sender.send_email(
                recipient=demo_recipient,
                subject=demo_subject,
                body=demo_body
            )
            
            if success:
                print(f"Demo email {i} sent successfully!")
            else:
                print(f"Failed to send demo email {i}")
            
            # Rate limiting
            if i < len(email_therapists):
                delay = random.uniform(15, 25)
                print(f"Waiting {delay:.1f} seconds...")
                time.sleep(delay)

def main():
    """Main function to run state-based extraction"""
    
    print("="*80)
    print("STATE-BASED THERAPIST EXTRACTION SYSTEM")
    print("="*80)
    print()
    print("This system will:")
    print("Extract ALL therapist information from Psychology Today by state")
    print("Save complete data to CSV file (state_name.csv)")
    print("Follow website redirects to find personal emails")
    print("Send personalized emails ONLY to therapists with extracted emails")
    print("All emails are sent to annegautham@gmail.com for demonstration")
    print()
    
    state_name = input("Enter state name (e.g., Wyoming, Colorado, Utah): ").strip()
    
    if not state_name:
        print("State name is required")
        return
    
    print(f"\\nStarting thorough extraction for {state_name}...")
    
    # Create extractor instance
    extractor = StateTherapistExtractor()
    
    # Extract all therapist data
    print(f"\\nExtracting therapists from {state_name}...")
    therapists_data = extractor.extract_state_therapists(state_name)
    
    if not therapists_data:
        print(f"No therapist data extracted for {state_name}")
        return
    
    # Save to CSV
    csv_file = extractor.save_to_csv(therapists_data, state_name)
    
    if csv_file:
        print(f"\\nSuccessfully saved {len(therapists_data)} therapists to {csv_file}")
        
        # Ask about sending emails
        email_therapists = [t for t in therapists_data if t.get('email')]
        
        if email_therapists:
            print(f"\\nFound {len(email_therapists)} therapists with emails:")
            for i, t in enumerate(email_therapists, 1):
                print(f"  {i}. {t['name']} - {t['email']}")
            
            send_emails = input(f"\\nSend demo emails for these {len(email_therapists)} therapists? (y/n): ").lower()
            
            if send_emails == 'y':
                extractor.send_emails_to_therapists(therapists_data, state_name)
        else:
            print(f"\\nNo therapists with emails found in {state_name}")
    
    print(f"\\n{'='*80}")
    print(f"{state_name.upper()} EXTRACTION COMPLETED!")
    print('='*80)

if __name__ == "__main__":
    main()
