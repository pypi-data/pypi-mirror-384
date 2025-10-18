"""Tests for cache manager"""

import pytest
import tempfile
import shutil
from pathlib import Path
from PIL import Image
from src.ctmu.cache_manager import CacheManager

def test_cache_manager_singleton():
    """Test cache manager singleton pattern"""
    cache1 = CacheManager()
    cache2 = CacheManager()
    assert cache1 is cache2

def test_get_cache_key():
    """Test cache key generation"""
    cache = CacheManager()
    key1 = cache.get_cache_key('https://example.com')
    key2 = cache.get_cache_key('https://example.com')
    key3 = cache.get_cache_key('https://different.com')
    
    assert key1 == key2
    assert key1 != key3
    assert len(key1) == 32  # MD5 hash length

def test_cache_and_retrieve_favicon():
    """Test caching and retrieving favicon"""
    # Use temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        cache = CacheManager()
        cache.cache_dir = Path(temp_dir)
        
        # Create test favicon
        favicon = Image.new('RGBA', (16, 16), (255, 0, 0, 255))
        url = 'https://test.com'
        
        try:
            # Cache favicon
            cache.cache_favicon(url, favicon)
            
            # Retrieve favicon
            retrieved = cache.get_cached_favicon(url)
            
            try:
                assert retrieved is not None
                assert retrieved.mode == 'RGBA'
                assert retrieved.size == (16, 16)
            finally:
                if retrieved:
                    retrieved.close()
        finally:
            favicon.close()

def test_cache_miss():
    """Test cache miss returns None"""
    cache = CacheManager()
    result = cache.get_cached_favicon('https://nonexistent.com')
    assert result is None