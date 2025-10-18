"""Favicon caching system"""

import os
import hashlib
import json
from pathlib import Path
from PIL import Image
import io
import base64

class CacheManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self.cache_dir = Path.home() / '.ctmu' / 'cache'
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._initialized = True
    
    def get_cache_key(self, url):
        return hashlib.md5(url.encode()).hexdigest()
    
    def get_cached_favicon(self, url):
        cache_key = self.get_cache_key(url)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                    img_data = base64.b64decode(data['image'])
                    return Image.open(io.BytesIO(img_data))
            except (json.JSONDecodeError, KeyError, ValueError):
                pass
        return None
    
    def cache_favicon(self, url, favicon):
        cache_key = self.get_cache_key(url)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        try:
            img_bytes = io.BytesIO()
            favicon.save(img_bytes, format='PNG')
            img_data = base64.b64encode(img_bytes.getvalue()).decode('utf-8')
            
            with open(cache_file, 'w') as f:
                json.dump({'image': img_data}, f)
        except (OSError, ValueError):
            pass