import requests

urls = []
successful_pings = 0
failed_pings = 0

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
        resp = requests.get(endpoint, timeout=5)
        print(f"{resp.status_code} {endpoint}")
        if resp.status_code == 200:
            successful_pings += 1
        else:
            failed_pings += 1
    except requests.exceptions.RequestException:
        print(f"Failed {endpoint}")
        failed_pings += 1

# Summary statistics
total_urls = len(urls)
success_rate = (successful_pings / total_urls * 100) if total_urls > 0 else 0
print("\nSummary Statistics:")
print(f"Total URLs processed: {total_urls}")
print(f"Successful pings: {successful_pings}")
print(f"Failed pings: {failed_pings}")
print(f"Success rate: {success_rate:.2f}%")