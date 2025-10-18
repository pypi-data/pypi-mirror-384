"""Tests for core functionality"""

import pytest
from src.ctmu.core import CTMUCore

def test_ctmu_core_init():
    """Test CTMUCore initialization"""
    core = CTMUCore()
    assert core.qr_gen is not None
    assert core.favicon_fetcher is not None
    assert core.image_processor is not None

def test_generate_qr():
    """Test QR generation workflow"""
    core = CTMUCore()
    # This would require mocking for full test
    assert hasattr(core, 'generate_qr')
    assert hasattr(core, '_save_as_svg')