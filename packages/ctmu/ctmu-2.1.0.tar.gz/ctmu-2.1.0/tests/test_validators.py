"""Tests for URL validation"""

import pytest
from src.ctmu.validators import URLValidator

def test_valid_url():
    assert URLValidator.validate("https://example.com") == "https://example.com"

def test_url_without_protocol():
    assert URLValidator.validate("example.com") == "https://example.com"

def test_invalid_url():
    with pytest.raises(ValueError):
        URLValidator.validate("")
    
    with pytest.raises(ValueError):
        URLValidator.validate("invalid")