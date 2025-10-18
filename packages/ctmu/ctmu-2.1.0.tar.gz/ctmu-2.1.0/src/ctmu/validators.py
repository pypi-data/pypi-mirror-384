"""URL validation utilities"""

import re
from urllib.parse import urlparse

class URLValidator:
    DOMAIN_PATTERN = re.compile(r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$')
    
    @staticmethod
    def validate(url):
        """Validate and normalize URL"""
        if not url:
            raise ValueError("URL cannot be empty")
        
        # Add protocol if missing
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        # Parse and validate
        parsed = urlparse(url)
        if not parsed.netloc:
            raise ValueError("Invalid URL format")
        
        # Basic domain validation - require at least one dot for valid domain
        domain = parsed.netloc.split(':')[0]
        if not URLValidator.DOMAIN_PATTERN.match(domain) or '.' not in domain:
            raise ValueError("Invalid domain name")
        
        return url