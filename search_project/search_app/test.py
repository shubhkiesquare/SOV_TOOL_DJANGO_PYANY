import urllib.request
import ssl

# Disable SSL certificate verification
ssl._create_default_https_context = ssl._create_unverified_context

# Bright Data credentials
username = 'brd-customer-hl_73244dc3-zone-serp_api1'
password = '7cfjb44xbl05'
proxy = 'brd.superproxy.io:22225'

# Set up the proxy
proxy_url = f'http://{username}:{password}@{proxy}'
proxy_handler = urllib.request.ProxyHandler({
    'http': proxy_url,
    'https': proxy_url
})
opener = urllib.request.build_opener(proxy_handler)

# Make a request
url = 'https://www.google.com/search?q=pizza&location=United+States'
try:
    with opener.open(url, timeout=30) as response:
        html_content = response.read().decode('utf-8')
    print("Request successful. First 500 characters of response:")
    print(html_content[:500])
except Exception as e:
    print(f"An error occurred: {str(e)}")