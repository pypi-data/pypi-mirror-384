"""Integration tests for CTMU"""

import pytest
import tempfile
import os
from unittest.mock import patch, Mock
from PIL import Image
import io
from src.ctmu.core import CTMUCore

@patch('src.ctmu.favicon_fetcher.requests.get')
@patch('src.ctmu.favicon_fetcher.requests.head')
def test_end_to_end_qr_generation(mock_head, mock_get):
    """Test complete QR generation workflow"""
    # Mock successful favicon fetch
    mock_head.return_value.status_code = 200
    
    # Create fake favicon
    img = Image.new('RGBA', (16, 16), (255, 0, 0, 255))
    try:
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        mock_get.return_value.content = img_bytes.getvalue()
        mock_get.return_value.raise_for_status.return_value = None
        
        # Test core functionality with temp directory
        with tempfile.TemporaryDirectory() as temp_dir:
            core = CTMUCore()
            files = core.generate_qr('example.com', 'bauhaus', temp_dir)
            
            # Verify files were created
            assert len(files) == 3
            assert all(os.path.exists(f) for f in files)
            assert any(f.endswith('.png') for f in files)
            assert any(f.endswith('.jpg') for f in files)
            assert any(f.endswith('.svg') for f in files)
            
        # Verify HTTP error handling was invoked
        mock_get.return_value.raise_for_status.assert_called_once()
    finally:
        img.close()

def test_invalid_url_handling():
    """Test handling of invalid URLs"""
    core = CTMUCore()
    
    with pytest.raises(ValueError):
        core.generate_qr('', 'bauhaus')

@patch('src.ctmu.favicon_fetcher.requests.head', side_effect=Exception())
def test_favicon_fetch_failure_fallback(mock_head):
    """Test fallback when favicon fetch fails"""
    with tempfile.TemporaryDirectory() as temp_dir:
        core = CTMUCore()
        files = core.generate_qr('example.com', 'bauhaus', temp_dir)
        
        # Should still generate QR files with default icon
        assert len(files) == 3
        assert all(os.path.exists(f) for f in files)

def test_different_styles():
    """Test QR generation with different styles"""
    core = CTMUCore()
    
    test_image = Image.new('RGBA', (16, 16), (255, 0, 0, 255))
    try:
        with patch('src.ctmu.favicon_fetcher.FaviconFetcher.fetch') as mock_fetch:
            mock_fetch.return_value = test_image
            
            # Test all styles with temp directory
            with tempfile.TemporaryDirectory() as temp_dir:
                for style in ['bauhaus', 'classic', 'hacker']:
                    files = core.generate_qr('example.com', style, temp_dir)
                    assert len(files) == 3
                    assert all(os.path.exists(f) for f in files)
    finally:
        test_image.close()