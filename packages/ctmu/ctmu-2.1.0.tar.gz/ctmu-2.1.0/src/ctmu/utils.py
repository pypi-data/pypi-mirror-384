"""Utility functions for CTMU Swiss Army Knife"""

import hashlib
import socket
import requests
import os
import platform
import subprocess
from pathlib import Path
from PIL import Image

# Hash Functions
def hash_text(text, algorithm='sha256'):
    """Hash text with specified algorithm"""
    hasher = getattr(hashlib, algorithm.lower())()
    hasher.update(text.encode())
    return hasher.hexdigest()

def hash_file(filepath, algorithm='sha256'):
    """Hash file contents"""
    hasher = getattr(hashlib, algorithm.lower())()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

# Network Functions
def check_port(host, port, timeout=3):
    """Check if port is open on host"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except:
        return False

def get_http_headers(url):
    """Get HTTP headers for URL"""
    try:
        response = requests.head(url, timeout=10)
        return dict(response.headers)
    except:
        return {}

# Nmap Functions
def nmap_scan(target, scan_type='basic', ports=None):
    """Perform nmap scan"""
    try:
        import subprocess
        
        cmd = ['nmap']
        
        if scan_type == 'fast':
            cmd.extend(['-F'])
        elif scan_type == 'stealth':
            cmd.extend(['-sS'])
        elif scan_type == 'udp':
            cmd.extend(['-sU'])
        elif scan_type == 'version':
            cmd.extend(['-sV'])
        elif scan_type == 'os':
            cmd.extend(['-O'])
        
        if ports:
            cmd.extend(['-p', ports])
        
        cmd.append(target)
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        return result.stdout if result.returncode == 0 else f"Error: {result.stderr}"
    except subprocess.TimeoutExpired:
        return "Error: Scan timeout"
    except FileNotFoundError:
        return "Error: nmap not installed. Install with: brew install nmap"
    except Exception as e:
        return f"Error: {e}"

def port_scan(host, start_port=1, end_port=1000):
    """Simple port scanner"""
    import socket
    from concurrent.futures import ThreadPoolExecutor
    
    open_ports = []
    
    def check_port(port):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((host, port))
            sock.close()
            if result == 0:
                return port
        except:
            pass
        return None
    
    with ThreadPoolExecutor(max_workers=100) as executor:
        futures = [executor.submit(check_port, port) for port in range(start_port, end_port + 1)]
        for future in futures:
            result = future.result()
            if result:
                open_ports.append(result)
    
    return sorted(open_ports)

# File Functions
def get_file_info(filepath):
    """Get detailed file information"""
    path = Path(filepath)
    stat = path.stat()
    return {
        'Size': f"{stat.st_size:,} bytes",
        'Modified': stat.st_mtime,
        'Permissions': oct(stat.st_mode)[-3:],
        'Type': 'Directory' if path.is_dir() else 'File'
    }

def generate_tree(directory, prefix="", max_depth=3, current_depth=0):
    """Generate directory tree structure"""
    if current_depth >= max_depth:
        return ""
    
    path = Path(directory)
    items = sorted(path.iterdir(), key=lambda x: (x.is_file(), x.name))
    tree = ""
    
    for i, item in enumerate(items[:20]):  # Limit to 20 items
        is_last = i == len(items) - 1
        current_prefix = "└── " if is_last else "├── "
        tree += f"{prefix}{current_prefix}{item.name}\n"
        
        if item.is_dir() and current_depth < max_depth - 1:
            next_prefix = prefix + ("    " if is_last else "│   ")
            tree += generate_tree(item, next_prefix, max_depth, current_depth + 1)
    
    return tree

# System Functions
def get_system_info():
    """Get macOS system information"""
    try:
        # Get macOS version
        version = platform.mac_ver()[0]
        # Get hardware info
        machine = platform.machine()
        processor = platform.processor()
        
        return {
            'OS': f"macOS {version}",
            'Architecture': machine,
            'Processor': processor or 'Unknown',
            'Python': platform.python_version()
        }
    except:
        return {'Error': 'Could not retrieve system info'}

def get_battery_status():
    """Get battery status on macOS"""
    try:
        result = subprocess.run(['pmset', '-g', 'batt'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            if len(lines) > 1:
                battery_line = lines[1]
                if '%' in battery_line:
                    return battery_line.split('\t')[1]
        return "Unknown"
    except:
        return "Not available"

# Image Functions
def resize_image(input_path, output_path, width=None, height=None):
    """Resize image maintaining aspect ratio"""
    with Image.open(input_path) as img:
        if width and height:
            img = img.resize((width, height), Image.Resampling.LANCZOS)
        elif width:
            ratio = width / img.width
            height = int(img.height * ratio)
            img = img.resize((width, height), Image.Resampling.LANCZOS)
        elif height:
            ratio = height / img.height
            width = int(img.width * ratio)
            img = img.resize((width, height), Image.Resampling.LANCZOS)
        
        img.save(output_path)

def convert_image(input_path, output_path, format='JPEG'):
    """Convert image to different format"""
    with Image.open(input_path) as img:
        if format.upper() == 'JPEG' and img.mode == 'RGBA':
            # Convert RGBA to RGB for JPEG
            rgb_img = Image.new('RGB', img.size, (255, 255, 255))
            rgb_img.paste(img, mask=img.split()[-1])
            rgb_img.save(output_path, format.upper())
        else:
            img.save(output_path, format.upper())

# Emacs Functions
def emacs_eval(expression):
    """Evaluate Emacs Lisp expression"""
    try:
        import subprocess
        result = subprocess.run(['emacs', '--batch', '--eval', expression], 
                              capture_output=True, text=True, timeout=30)
        return result.stdout.strip() if result.returncode == 0 else f"Error: {result.stderr}"
    except FileNotFoundError:
        return "Error: Emacs not installed"
    except Exception as e:
        return f"Error: {e}"

def emacs_open_file(filepath):
    """Open file in Emacs"""
    try:
        import subprocess
        subprocess.Popen(['emacs', filepath])
        return f"Opening {filepath} in Emacs"
    except FileNotFoundError:
        return "Error: Emacs not installed"
    except Exception as e:
        return f"Error: {e}"

def emacs_format_code(filepath, mode=None):
    """Format code file using Emacs"""
    try:
        import subprocess
        cmd = ['emacs', '--batch', filepath]
        if mode:
            cmd.extend(['--eval', f'({mode})'])
        cmd.extend(['--eval', '(indent-region (point-min) (point-max))', 
                   '--eval', '(save-buffer)'])
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return "Code formatted successfully" if result.returncode == 0 else f"Error: {result.stderr}"
    except FileNotFoundError:
        return "Error: Emacs not installed"
    except Exception as e:
        return f"Error: {e}"

# OpenSSH Functions
def ssh_keygen(key_type='rsa', bits=2048, comment=None, output_file=None):
    """Generate SSH key pair"""
    try:
        import subprocess
        cmd = ['ssh-keygen', '-t', key_type, '-b', str(bits)]
        if comment:
            cmd.extend(['-C', comment])
        if output_file:
            cmd.extend(['-f', output_file])
        else:
            cmd.extend(['-f', f'id_{key_type}'])
        cmd.append('-N')  # No passphrase
        cmd.append('')
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.stdout if result.returncode == 0 else f"Error: {result.stderr}"
    except Exception as e:
        return f"Error: {e}"

def ssh_copy_id(user, host, key_file=None):
    """Copy SSH public key to remote host"""
    try:
        import subprocess
        cmd = ['ssh-copy-id']
        if key_file:
            cmd.extend(['-i', key_file])
        cmd.append(f'{user}@{host}')
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        return "Key copied successfully" if result.returncode == 0 else f"Error: {result.stderr}"
    except Exception as e:
        return f"Error: {e}"

def ssh_connect(user, host, command=None, key_file=None):
    """SSH connect to remote host"""
    try:
        import subprocess
        cmd = ['ssh']
        if key_file:
            cmd.extend(['-i', key_file])
        cmd.append(f'{user}@{host}')
        if command:
            cmd.append(command)
        
        if command:
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.stdout if result.returncode == 0 else f"Error: {result.stderr}"
        else:
            subprocess.run(cmd)
            return "SSH session started"
    except Exception as e:
        return f"Error: {e}"

def ssh_tunnel(local_port, remote_host, remote_port, ssh_host, user):
    """Create SSH tunnel"""
    try:
        import subprocess
        cmd = ['ssh', '-L', f'{local_port}:{remote_host}:{remote_port}', f'{user}@{ssh_host}', '-N']
        
        process = subprocess.Popen(cmd)
        return f"Tunnel created: localhost:{local_port} -> {remote_host}:{remote_port}"
    except Exception as e:
        return f"Error: {e}"