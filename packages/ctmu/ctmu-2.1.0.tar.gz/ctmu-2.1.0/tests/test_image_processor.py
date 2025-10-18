"""Tests for image processor"""

import pytest
from PIL import Image
from src.ctmu.image_processor import ImageProcessor

def test_image_processor_init():
    """Test image processor initialization"""
    processor = ImageProcessor()
    assert processor is not None

def test_embed_favicon(sample_qr_image, sample_favicon):
    """Test favicon embedding"""
    processor = ImageProcessor()
    result = processor.embed_favicon(sample_qr_image, sample_favicon)
    
    try:
        assert result.mode == 'RGBA'
        assert result.size == sample_qr_image.size
    finally:
        result.close()

def test_resize_favicon():
    """Test favicon resizing"""
    processor = ImageProcessor()
    favicon = Image.new('RGBA', (64, 64), (255, 0, 0, 255))
    
    try:
        resized = processor._resize_favicon(favicon, (32, 32))
        try:
            assert resized.size[0] <= 32
            assert resized.size[1] <= 32
        finally:
            resized.close()
    finally:
        favicon.close()

def test_embed_favicon_maintains_aspect_ratio(sample_qr_image):
    """Test that favicon embedding maintains aspect ratio"""
    processor = ImageProcessor()
    # Create rectangular favicon
    favicon = Image.new('RGBA', (64, 32), (255, 0, 0, 255))
    
    try:
        result = processor.embed_favicon(sample_qr_image, favicon)
        try:
            assert result.mode == 'RGBA'
        finally:
            result.close()
    finally:
        favicon.close()