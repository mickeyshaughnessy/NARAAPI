# This script crawls the various US federal agency web endpoints.

from agency_config import api_urls

for url in api_urls:
    endpoint = url + '/ping'
    resp = requests.get(endpoint)
    print(resp)
