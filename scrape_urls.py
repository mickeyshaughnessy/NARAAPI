from agency_config import api_urls
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import string

# Function to scrape agency URLs from USA.gov A-Z index
def scrape_agency_urls():
    base_url = "https://www.usa.gov/agency-index/"
    urls = []
    
    # Iterate through A-Z
    for letter in string.ascii_uppercase:
        try:
            # Fetch page for each letter (e.g., /agency-index/a)
            response = requests.get(f"{base_url}{letter}", timeout=10)
            response.raise_for_status()  # Raise exception for bad status codes
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Find all agency links (based on page structure)
            # Links are typically in <a> tags within <li> under <ul class="agency-list">
            agency_links = soup.select("ul.agency-list li a[href]")
            
            for link in agency_links:
                href = link["href"]
                # Ensure the link is an external .gov URL
                if href.startswith("http") and ".gov" in href:
                    # Extract root domain
                    domain = urlparse(href).netloc
                    if domain and domain not in urls:
                        urls.append(domain)
                        
        except requests.RequestException as e:
            print(f"Error scraping URLs for letter {letter}: {e}")
            continue
    
    return sorted(urls)  # Sort alphabetically

# Add scraped URLs to existing api_urls list
new_urls = scrape_agency_urls()
api_urls.extend(new_urls)

# Remove duplicates while preserving order
api_urls = list(dict.fromkeys(api_urls))

# Print the expanded list
for url in api_urls:
    print(url)
