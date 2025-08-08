"""
Enhanced Configuration Loader with Environment Variable Support
==============================================================

This module extends the main script to support environment variables
for sensitive configuration data like passwords.
"""

import os
import json
from typing import Dict, Any

def load_config_with_env(config_file: str = "config.json") -> Dict[str, Any]:
    """
    Load configuration from JSON file and override with environment variables
    """
    # Load base config
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        # Create default config if file doesn't exist
        config = {
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
            }
        }
    
    # Override with environment variables if they exist
    config["email"]["address"] = os.getenv("EMAIL_ADDRESS", config["email"]["address"])
    config["email"]["password"] = os.getenv("EMAIL_PASSWORD", config["email"]["password"])
    config["email"]["smtp_server"] = os.getenv("SMTP_SERVER", config["email"]["smtp_server"])
    config["email"]["smtp_port"] = int(os.getenv("SMTP_PORT", config["email"]["smtp_port"]))
    
    # Scraping overrides
    config["scraping"]["max_emails_per_day"] = int(os.getenv("MAX_EMAILS_PER_DAY", config["scraping"]["max_emails_per_day"]))
    config["scraping"]["max_therapists_per_state"] = int(os.getenv("MAX_THERAPISTS_PER_STATE", config["scraping"]["max_therapists_per_state"]))
    
    # Delay overrides
    delay_min = int(os.getenv("DELAY_BETWEEN_EMAILS_MIN", config["scraping"]["delay_between_emails"][0]))
    delay_max = int(os.getenv("DELAY_BETWEEN_EMAILS_MAX", config["scraping"]["delay_between_emails"][1]))
    config["scraping"]["delay_between_emails"] = [delay_min, delay_max]
    
    # Hunter.io API key (optional)
    hunter_api_key = os.getenv("HUNTER_IO_API_KEY")
    if hunter_api_key:
        config["hunter_io"] = {
            "api_key": hunter_api_key,
            "enabled": True
        }
    
    return config

def load_env_file(env_file: str = ".env"):
    """
    Load environment variables from a .env file
    """
    if not os.path.exists(env_file):
        return
    
    with open(env_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()

# Usage example:
if __name__ == "__main__":
    # Load .env file first
    load_env_file()
    
    # Then load config with environment overrides
    config = load_config_with_env()
    
    print("Configuration loaded:")
    print(f"Email: {config['email']['address']}")
    print(f"SMTP Server: {config['email']['smtp_server']}")
    print(f"Max emails per day: {config['scraping']['max_emails_per_day']}")
    
    # Don't print password for security
    if config['email']['password'] != "YOUR_PASSWORD_HERE":
        print("✅ Email password is configured")
    else:
        print("⚠️  Email password needs to be set")
