"""Web utilities"""

import requests
import json
from urllib.parse import urlparse, urljoin
import time

def download_file(url, output_path=None, timeout=30):
    """Download file from URL"""
    try:
        response = requests.get(url, timeout=timeout, stream=True)
        response.raise_for_status()
        
        if not output_path:
            output_path = urlparse(url).path.split('/')[-1] or 'download'
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        return f"Downloaded {url} to {output_path}"
    except Exception as e:
        return f"Error: {e}"

def check_website(url, timeout=10):
    """Check website status"""
    try:
        start_time = time.time()
        response = requests.get(url, timeout=timeout)
        response_time = round((time.time() - start_time) * 1000, 2)
        
        return {
            'url': url,
            'status': response.status_code,
            'response_time': f"{response_time}ms",
            'size': len(response.content),
            'headers': dict(response.headers)
        }
    except Exception as e:
        return f"Error: {e}"

def get_page_title(url):
    """Extract page title from URL"""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        import re
        title_match = re.search(r'<title[^>]*>([^<]+)</title>', response.text, re.IGNORECASE)
        return title_match.group(1).strip() if title_match else "No title found"
    except Exception as e:
        return f"Error: {e}"

def shorten_url(url, service='tinyurl'):
    """Shorten URL using service"""
    try:
        if service == 'tinyurl':
            api_url = f"http://tinyurl.com/api-create.php?url={url}"
            response = requests.get(api_url, timeout=10)
            return response.text if response.status_code == 200 else f"Error: {response.status_code}"
        else:
            return "Error: Unsupported service"
    except Exception as e:
        return f"Error: {e}"

def test_api(url, method='GET', headers=None, data=None):
    """Test API endpoint"""
    try:
        kwargs = {'timeout': 30}
        if headers:
            kwargs['headers'] = headers
        if data:
            kwargs['json'] = json.loads(data) if isinstance(data, str) else data
        
        response = requests.request(method, url, **kwargs)
        
        return {
            'status': response.status_code,
            'headers': dict(response.headers),
            'body': response.text[:1000] + '...' if len(response.text) > 1000 else response.text
        }
    except Exception as e:
        return f"Error: {e}"