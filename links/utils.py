import requests
from bs4 import BeautifulSoup

def fetch_og_metadata(url):
    result = {'title': '', 'description': '', 'image': ''}
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        og_title = soup.find('meta', property='og:title')
        og_desc = soup.find('meta', property='og:description')
        og_image = soup.find('meta', property='og:image')
        if og_title and og_title.get('content'):
            result['title'] = og_title['content']
        if og_desc and og_desc.get('content'):
            result['description'] = og_desc['content']
        if og_image and og_image.get('content'):
            result['image'] = og_image['content']
        if not result['title']:
            title_tag = soup.find('title')
            if title_tag and title_tag.string:
                result['title'] = title_tag.string.strip()
        if not result['description']:
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc and meta_desc.get('content'):
                result['description'] = meta_desc['content']
    except (requests.RequestException, Exception):
        pass
    return result