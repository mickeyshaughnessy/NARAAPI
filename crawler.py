# This script crawls the various US federal agency web endpoints.
import requests

urls = []
with open("all_urls.dat") as fin:
    for line in fin:
        line = line.rstrip()
        urls.append(line)

for url in urls:
    if url[-1] == "/":
        endpoint = url + 'ping'
    else:
        endpoint = url + '/ping'
    try:
        resp = requests.get(endpoint)
        print(resp, endpoint)
    except:
        pass
