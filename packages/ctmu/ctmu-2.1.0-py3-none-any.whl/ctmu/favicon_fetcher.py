"""Favicon fetching and processing"""

import requests
from PIL import Image, ImageDraw
from urllib.parse import urljoin, urlparse
import io
import ipaddress
from .cache_manager import CacheManager

class FaviconFetcher:
    def __init__(self):
        self.cache = CacheManager()
    
    def fetch(self, url):
        """Fetch favicon for given URL"""
        # Validate URL for SSRF protection
        if not self._is_safe_url(url):
            return self._create_default_icon()
            
        # Check cache first
        cached = self.cache.get_cached_favicon(url)
        if cached:
            return cached
        
        try:
            favicon_url = self._get_favicon_url(url)
            if not self._is_safe_url(favicon_url):
                return self._create_default_icon()
            favicon = self._download_favicon(favicon_url)
            self.cache.cache_favicon(url, favicon)
            return favicon
        except Exception:
            # Return default icon if fetch fails
            return self._create_default_icon()
    
    def _get_favicon_url(self, url):
        """Get favicon URL from website"""
        parsed = urlparse(url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        
        # Try high-resolution favicon locations first
        favicon_paths = [
            '/apple-touch-icon-180x180.png',
            '/apple-touch-icon-152x152.png',
            '/apple-touch-icon-120x120.png',
            '/apple-touch-icon.png',
            '/favicon-32x32.png',
            '/favicon-16x16.png',
            '/favicon.png',
            '/favicon.ico'
        ]
        
        for path in favicon_paths:
            favicon_url = urljoin(base_url, path)
            try:
                response = requests.head(favicon_url, timeout=5)
                if response.status_code == 200:
                    return favicon_url
            except:
                continue
        
        return urljoin(base_url, '/favicon.ico')
    
    def _download_favicon(self, favicon_url):
        """Download and process favicon"""
        response = requests.get(favicon_url, timeout=10)
        response.raise_for_status()
        
        image = Image.open(io.BytesIO(response.content))
        return image.convert('RGBA')
    
    def _is_safe_url(self, url):
        """Validate URL to prevent SSRF attacks"""
        try:
            parsed = urlparse(url)
            
            # Only allow HTTP/HTTPS
            if parsed.scheme not in ('http', 'https'):
                return False
                
            # Block localhost and private IPs
            hostname = parsed.hostname
            if not hostname:
                return False
                
            # Check for localhost
            if hostname.lower() in ('localhost', '127.0.0.1', '::1'):
                return False
                
            # Check for private IP ranges
            try:
                ip = ipaddress.ip_address(hostname)
                return ip.is_global
            except ValueError:
                # Not an IP address, check for private domains
                if hostname.endswith('.local') or hostname.startswith('192.168.') or hostname.startswith('10.') or hostname.startswith('172.'):
                    return False
                    
            return True
        except Exception:
            return False
    
    def _create_default_icon(self):
        """Create attractive default icon when favicon unavailable"""
        size = 180
        img = Image.new('RGBA', (size, size), (255, 255, 255, 0))
        draw = ImageDraw.Draw(img)
        
        # Draw a simple web/globe icon
        center = size // 2
        radius = size // 3
        
        # Circle background
        draw.ellipse([center-radius, center-radius, center+radius, center+radius], 
                    fill=(70, 130, 180, 255), outline=(50, 100, 150, 255), width=3)
        
        # Grid lines for web/globe effect
        draw.ellipse([center-radius//2, center-radius, center+radius//2, center+radius], 
                    outline=(255, 255, 255, 180), width=2)
        draw.line([center-radius, center, center+radius, center], 
                  fill=(255, 255, 255, 180), width=2)
        
        return img