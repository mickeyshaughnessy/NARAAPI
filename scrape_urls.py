from agency_config import api_urls
import requests
import string
import time
import re

# Function to scrape raw HTML and print URLs from lines with field--name-field-website
def scrape_agency_urls():
    base_url = "https://www.usa.gov/agency-index"
    
    # Iterate through A-Z
    for letter in string.ascii_lowercase:
        try:
            # Fetch page for each letter (e.g., /agency-index/a)
            if letter == "a":
                response = requests.get(f"{base_url}#A", timeout=10)
            else:
                response = requests.get(f"{base_url}/{letter}", timeout=10)
            response.raise_for_status()  # Raise exception for bad status codes
            
            # Split the raw HTML into lines
            html_lines = response.text.splitlines()
            
            # Process lines containing field--name-field-website
            for line in html_lines:
                if "field--name-field-website" in line:
                    # Extract URL using regex
                    match = re.search(r'href=["\'](.*?)["\']', line)
                    if match:
                        url = match.group(1)
                        print(url.strip())
                            
        except requests.RequestException as e:
            continue
        
        # Add a small delay to avoid overwhelming the server
        time.sleep(0.5)

# Run the scraper
scrape_agency_urls()
