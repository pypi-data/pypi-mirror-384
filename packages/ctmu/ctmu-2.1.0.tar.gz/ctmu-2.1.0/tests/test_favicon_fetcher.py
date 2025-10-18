"""Tests for favicon fetcher"""

import pytest
from unittest.mock import patch, Mock
from PIL import Image
import io
from src.ctmu.favicon_fetcher import FaviconFetcher

def test_favicon_fetcher_init():
    """Test favicon fetcher initialization"""
    fetcher = FaviconFetcher()
    assert fetcher.cache is not None

@patch('src.ctmu.favicon_fetcher.requests.get')
@patch('src.ctmu.favicon_fetcher.requests.head')
def test_fetch_favicon_success(mock_head, mock_get):
    """Test successful favicon fetch"""
    # Mock successful response
    mock_head.return_value.status_code = 200
    
    # Create fake image data
    img = Image.new('RGBA', (16, 16), (255, 0, 0, 255))
    try:
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        mock_get.return_value.content = img_bytes.getvalue()
        mock_get.return_value.raise_for_status.return_value = None
        
        fetcher = FaviconFetcher()
        result = fetcher.fetch('https://example.com')
        
        try:
            assert result.mode == 'RGBA'
            assert result.size == (16, 16)
        finally:
            result.close()
    finally:
        img.close()

def test_fetch_favicon_failure():
    """Test favicon fetch failure returns default"""
    with patch('src.ctmu.favicon_fetcher.requests.head', side_effect=Exception()):
        fetcher = FaviconFetcher()
        result = fetcher.fetch('https://example.com')

        try:
            assert result.mode == 'RGBA'
            assert result.size == (180, 180)
        finally:
            result.close()

def test_get_favicon_url():
    """Test favicon URL discovery"""
    fetcher = FaviconFetcher()
    url = fetcher._get_favicon_url('https://example.com')
    assert 'example.com' in url
    assert url.endswith('.ico') or url.endswith('.png')

def test_create_default_icon():
    """Test default icon creation"""
    fetcher = FaviconFetcher()
    icon = fetcher._create_default_icon()
    try:
        assert icon.mode == 'RGBA'
        assert icon.size == (180, 180)
    finally:
        icon.close()