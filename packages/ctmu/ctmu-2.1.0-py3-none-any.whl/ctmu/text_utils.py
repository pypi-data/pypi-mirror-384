"""Text processing utilities"""

import re
import json
import csv
from io import StringIO

def count_words(text):
    """Count words in text"""
    return len(text.split())

def count_lines(text):
    """Count lines in text"""
    return len(text.splitlines())

def count_chars(text, include_spaces=True):
    """Count characters in text"""
    return len(text) if include_spaces else len(text.replace(' ', ''))

def extract_urls(text):
    """Extract URLs from text"""
    url_pattern = r'https?://[^\s<>"{}|\\^`[\]]+'
    return re.findall(url_pattern, text)

def extract_emails(text):
    """Extract email addresses from text"""
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    return re.findall(email_pattern, text)

def json_format(text):
    """Format JSON text"""
    try:
        parsed = json.loads(text)
        return json.dumps(parsed, indent=2)
    except json.JSONDecodeError as e:
        return f"Error: Invalid JSON - {e}"

def csv_to_json(csv_text):
    """Convert CSV to JSON"""
    try:
        reader = csv.DictReader(StringIO(csv_text))
        return json.dumps(list(reader), indent=2)
    except Exception as e:
        return f"Error: {e}"

def remove_duplicates(text):
    """Remove duplicate lines"""
    lines = text.splitlines()
    return '\n'.join(dict.fromkeys(lines))

def sort_lines(text, reverse=False):
    """Sort lines alphabetically"""
    lines = text.splitlines()
    return '\n'.join(sorted(lines, reverse=reverse))