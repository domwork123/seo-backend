# ScrapingBee Configuration
import os

# ScrapingBee API Configuration
SCRAPINGBEE_API_KEY = os.getenv("SCRAPINGBEE_API_KEY")
SCRAPINGBEE_BASE_URL = "https://app.scrapingbee.com/api/v1/"

def get_scrapingbee_config():
    """Get ScrapingBee configuration"""
    if not SCRAPINGBEE_API_KEY:
        raise ValueError("SCRAPINGBEE_API_KEY environment variable is not set")
    
    return {
        "api_key": SCRAPINGBEE_API_KEY,
        "base_url": SCRAPINGBEE_BASE_URL
    }
