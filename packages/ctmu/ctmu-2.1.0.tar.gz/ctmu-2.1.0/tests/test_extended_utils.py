"""Tests for extended utilities"""

import pytest
from src.ctmu.text_utils import count_words, extract_urls, json_format
from src.ctmu.math_utils import calculate, convert_base, statistics_calc
from src.ctmu.time_utils import timestamp_to_date, date_to_timestamp

class TestTextUtils:
    def test_count_words(self):
        assert count_words("hello world") == 2
        assert count_words("") == 0
    
    def test_extract_urls(self):
        text = "Visit https://github.com and http://example.com"
        urls = extract_urls(text)
        assert len(urls) == 2
        assert "https://github.com" in urls
    
    def test_json_format(self):
        result = json_format('{"name":"test"}')
        assert '"name": "test"' in result

class TestMathUtils:
    def test_calculate(self):
        assert calculate("2 + 3") == "5"
        assert calculate("10 / 2") == "5.0"
    
    def test_convert_base(self):
        assert convert_base("255", 10, 16) == "FF"
        assert convert_base("1010", 2, 10) == "10"
    
    def test_statistics_calc(self):
        result = statistics_calc("1,2,3,4,5")
        assert isinstance(result, dict)
        assert result['mean'] == 3.0

class TestTimeUtils:
    def test_timestamp_conversion(self):
        result = timestamp_to_date("1640995200")
        assert "2022" in result
    
    def test_date_conversion(self):
        result = date_to_timestamp("2022-01-01 00:00:00")
        assert isinstance(result, int)