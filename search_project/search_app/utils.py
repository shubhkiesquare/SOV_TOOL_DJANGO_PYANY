# search_app/utils.py
import urllib.request
import urllib.parse
from bs4 import BeautifulSoup
from django.conf import settings

def process_search_query(search_query):
    username = settings.BRIGHT_DATA_USERNAME
    password = settings.BRIGHT_DATA_PASSWORD
    proxy = settings.BRIGHT_DATA_HOST
    
    proxy_url = f'http://{username}:{password}@{proxy}'
    
    base_url = "https://www.google.com/search"
    keywords = search_query.keywords.split(',')
    results = []

    for keyword in keywords:
        params = {
            'q': keyword.strip(),
            'num': search_query.pagination or '10',
            'hl': search_query.country,
            'gl': search_query.country,
            'device': search_query.device,
        }
        
        if search_query.city:
            city_parts = search_query.city.split(',')
            if len(city_parts) >= 1:
                city_name = city_parts[0].strip()
                params['uule'] = create_uule(city_name)
        
        url = f"{base_url}?{urllib.parse.urlencode(params)}"
        
        try:
            opener = urllib.request.build_opener(
                urllib.request.ProxyHandler({
                    'http': proxy_url,
                    'https': proxy_url
                })
            )
            with opener.open(url, timeout=30) as response:
                html_content = response.read().decode('utf-8')
            
            keyword_results = parse_search_results(html_content, keyword)
            results.extend(keyword_results)
        except Exception as e:
            results.append({'error': f"An error occurred for keyword '{keyword}': {str(e)}"})
    
    return results

def parse_search_results(html_content, keyword):
    soup = BeautifulSoup(html_content, 'html.parser')
    search_results = []
    rank = 0

    for result in soup.select('div.g'):
        rank += 1
        title_element = result.select_one('h3')
        link_element = result.select_one('a')
        snippet_element = result.select_one('div.VwiC3b')

        if title_element and link_element and snippet_element:
            search_results.append({
                'keyword': keyword,
                'rank': rank,
                'title': title_element.get_text(strip=True),
                'link': link_element['href'],
                'description': snippet_element.get_text(strip=True)
            })

    return search_results

def create_uule(city):
    import base64
    canonical_name_length = len(city) + 2
    canonical_name_length_hex = format(canonical_name_length, '02x')
    encoded_city = base64.b64encode(city.encode('utf-8')).decode('ascii')
    uule = f"w+CAIQICI{canonical_name_length_hex}{encoded_city}"
    return uule