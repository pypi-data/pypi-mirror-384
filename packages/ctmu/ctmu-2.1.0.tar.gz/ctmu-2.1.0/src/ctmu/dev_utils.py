"""Development utilities"""

import subprocess
import json
import os
import uuid
import secrets
import string

def generate_uuid(version=4, count=1):
    """Generate UUID"""
    uuids = []
    for _ in range(count):
        if version == 1:
            uuids.append(str(uuid.uuid1()))
        elif version == 4:
            uuids.append(str(uuid.uuid4()))
    return uuids if count > 1 else uuids[0]

def generate_password(length=16, include_symbols=True):
    """Generate secure password"""
    chars = string.ascii_letters + string.digits
    if include_symbols:
        chars += "!@#$%^&*"
    return ''.join(secrets.choice(chars) for _ in range(length))

def generate_api_key(length=32):
    """Generate API key"""
    return secrets.token_hex(length // 2)

def minify_json(json_str):
    """Minify JSON string"""
    try:
        parsed = json.loads(json_str)
        return json.dumps(parsed, separators=(',', ':'))
    except json.JSONDecodeError as e:
        return f"Error: Invalid JSON - {e}"

def prettify_json(json_str, indent=2):
    """Prettify JSON string"""
    try:
        parsed = json.loads(json_str)
        return json.dumps(parsed, indent=indent, sort_keys=True)
    except json.JSONDecodeError as e:
        return f"Error: Invalid JSON - {e}"

def validate_json(json_str):
    """Validate JSON syntax"""
    try:
        json.loads(json_str)
        return "Valid JSON"
    except json.JSONDecodeError as e:
        return f"Invalid JSON: {e}"

def git_status():
    """Get git repository status"""
    try:
        result = subprocess.run(['git', 'status', '--porcelain'], capture_output=True, text=True, cwd='.')
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n') if result.stdout.strip() else []
            return {
                'modified': len([l for l in lines if l.startswith(' M')]),
                'added': len([l for l in lines if l.startswith('A')]),
                'deleted': len([l for l in lines if l.startswith(' D')]),
                'untracked': len([l for l in lines if l.startswith('??')]),
                'total_changes': len(lines)
            }
        return f"Error: {result.stderr}"
    except FileNotFoundError:
        return "Error: Git not installed"
    except Exception as e:
        return f"Error: {e}"

def docker_ps():
    """List Docker containers"""
    try:
        result = subprocess.run(['docker', 'ps', '--format', 'json'], capture_output=True, text=True)
        if result.returncode == 0:
            containers = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    containers.append(json.loads(line))
            return containers
        return f"Error: {result.stderr}"
    except FileNotFoundError:
        return "Error: Docker not installed"
    except Exception as e:
        return f"Error: {e}"