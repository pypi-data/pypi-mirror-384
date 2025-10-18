"""Tests for QR generator"""

import pytest
from src.ctmu.qr_generator import QRGenerator

@pytest.fixture
def qr_generator():
    """Shared QR generator instance for tests"""
    return QRGenerator()

def test_qr_generator_init(qr_generator):
    """Test QR generator initialization"""
    assert 'bauhaus' in qr_generator.stylers
    assert 'classic' in qr_generator.stylers
    assert 'hacker' in qr_generator.stylers

def test_generate_bauhaus_qr(qr_generator):
    """Test Bauhaus QR generation"""
    result = qr_generator.generate('https://example.com', 'bauhaus')
    assert result.mode == 'RGBA'
    assert result.size[0] > 0
    assert result.size[1] > 0

def test_generate_classic_qr(qr_generator):
    """Test Classic QR generation"""
    result = qr_generator.generate('https://example.com', 'classic')
    assert result.mode == 'RGBA'

def test_generate_hacker_qr(qr_generator):
    """Test Hacker QR generation"""
    result = qr_generator.generate('https://example.com', 'hacker')
    assert result.mode == 'RGBA'

def test_generate_invalid_style(qr_generator):
    """Test QR generation with invalid style defaults to bauhaus"""
    result = qr_generator.generate('https://example.com', 'invalid')
    assert result.mode == 'RGBA'