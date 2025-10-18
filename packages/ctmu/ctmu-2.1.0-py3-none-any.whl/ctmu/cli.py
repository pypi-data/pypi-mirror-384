#!/usr/bin/env python3
"""CTMU - Swiss Army Knife CLI Tool for macOS"""

import click
import os
import sys
import json
import hashlib
import base64
import subprocess
import tempfile
from pathlib import Path
from .core import CTMUCore
from .utils import *
from .storage import *
from .gpg_utils import *
from .text_utils import *
from .web_utils import *
from .time_utils import *
from .math_utils import *
from .media_utils import *
from .dev_utils import *
from .monitor_utils import *
from .backup_utils import *

@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    """CTMU - Swiss Army Knife CLI Tool for macOS"""
    if ctx.invoked_subcommand is None:
        click.echo("CTMU - Swiss Army Knife CLI Tool")
        click.echo("\nAvailable commands:")
        click.echo("  qr        Generate QR codes with favicons")
        click.echo("  hash      Hash files and text")
        click.echo("  encode    Base64 encode/decode")
        click.echo("  net       Network utilities (ping, nmap, scan)")
        click.echo("  file      File operations")
        click.echo("  sys       System information")
        click.echo("  img       Image processing")
        click.echo("  emacs     GNU Emacs utilities")
        click.echo("  ssh       OpenSSH utilities")
        click.echo("  s3        AWS S3 storage")
        click.echo("  nextcloud Nextcloud storage")
        click.echo("  gpg       GPG encryption")
        click.echo("  text      Text processing")
        click.echo("  web       Web utilities")
        click.echo("  time      Time utilities")
        click.echo("  math      Math utilities")
        click.echo("  media     Media processing")
        click.echo("  dev       Development tools")
        click.echo("  monitor   System monitoring")
        click.echo("  backup    Backup utilities")
        click.echo("\nUse 'ctmu <command> --help' for more info")

# QR Code Generation
@cli.command()
@click.argument('url', required=False)
@click.option('--style', default='bauhaus', help='QR code style (bauhaus, classic, hacker)')
@click.option('--output', '-o', default='.', help='Output directory')
def qr(url, style, output):
    """Generate QR codes with website favicons"""
    core = CTMUCore()
    
    if not url:
        url = click.prompt('Enter website URL')
    
    os.makedirs(output, exist_ok=True)
    
    try:
        files_created = core.generate_qr(url, style, output)
        click.echo(f"QR code generated!")
        for file_path in files_created:
            click.echo(f"   {file_path}")
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)

# Hash Utilities
@cli.group()
def hash():
    """Hash files and text"""
    pass

@hash.command()
@click.argument('text')
@click.option('--algo', default='sha256', help='Hash algorithm')
def text(text, algo):
    """Hash text string"""
    result = hash_text(text, algo)
    click.echo(f"{algo.upper()}: {result}")

@hash.command()
@click.argument('filepath', type=click.Path(exists=True))
@click.option('--algo', default='sha256', help='Hash algorithm')
def file(filepath, algo):
    """Hash file contents"""
    result = hash_file(filepath, algo)
    click.echo(f"{algo.upper()}: {result}")

# Encoding Utilities
@cli.group()
def encode():
    """Base64 encode/decode operations"""
    pass

@encode.command()
@click.argument('text')
def b64(text):
    """Base64 encode text"""
    result = base64.b64encode(text.encode()).decode()
    click.echo(result)

@encode.command()
@click.argument('encoded')
def b64d(encoded):
    """Base64 decode text"""
    try:
        result = base64.b64decode(encoded).decode()
        click.echo(result)
    except Exception:
        click.echo("Invalid base64 string", err=True)

# Network Utilities
@cli.group()
def net():
    """Network utilities"""
    pass

@net.command()
@click.argument('host')
@click.option('--port', '-p', default=80, help='Port to check')
def ping(host, port):
    """Check if host:port is reachable"""
    result = check_port(host, port)
    status = "Open" if result else "Closed"
    click.echo(f"{host}:{port} - {status}")

@net.command()
@click.argument('url')
def headers(url):
    """Get HTTP headers for URL"""
    headers = get_http_headers(url)
    for key, value in headers.items():
        click.echo(f"{key}: {value}")

@net.command()
@click.argument('target')
@click.option('--type', '-t', default='basic', help='Scan type: basic, fast, stealth, udp, version, os')
@click.option('--ports', '-p', help='Port range (e.g., 1-1000, 80,443)')
def nmap(target, type, ports):
    """Perform nmap network scan"""
    result = nmap_scan(target, type, ports)
    click.echo(result)

@net.command()
@click.argument('host')
@click.option('--start', default=1, help='Start port')
@click.option('--end', default=1000, help='End port')
def scan(host, start, end):
    """Simple port scanner"""
    click.echo(f"Scanning {host} ports {start}-{end}...")
    open_ports = port_scan(host, start, end)
    if open_ports:
        click.echo(f"Open ports: {', '.join(map(str, open_ports))}")
    else:
        click.echo("No open ports found")

# File Operations
@cli.group()
def file():
    """File operations"""
    pass

@file.command()
@click.argument('filepath', type=click.Path(exists=True))
def info(filepath):
    """Get file information"""
    info = get_file_info(filepath)
    for key, value in info.items():
        click.echo(f"{key}: {value}")

@file.command()
@click.argument('directory', type=click.Path(exists=True))
def tree(directory):
    """Display directory tree"""
    tree_output = generate_tree(directory)
    click.echo(tree_output)

# System Information
@cli.group()
def sys():
    """System information"""
    pass

@sys.command()
def info():
    """Display system information"""
    info = get_system_info()
    for key, value in info.items():
        click.echo(f"{key}: {value}")

@sys.command()
def battery():
    """Show battery status (macOS)"""
    status = get_battery_status()
    click.echo(f"Battery: {status}")

# Image Processing
@cli.group()
def img():
    """Image processing utilities"""
    pass

@img.command()
@click.argument('input_path', type=click.Path(exists=True))
@click.argument('output_path')
@click.option('--width', type=int, help='Target width')
@click.option('--height', type=int, help='Target height')
def resize(input_path, output_path, width, height):
    """Resize image"""
    try:
        resize_image(input_path, output_path, width, height)
        click.echo(f"Image resized: {output_path}")
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)

@img.command()
@click.argument('input_path', type=click.Path(exists=True))
@click.argument('output_path')
@click.option('--format', default='JPEG', help='Output format')
def convert(input_path, output_path, format):
    """Convert image format"""
    try:
        convert_image(input_path, output_path, format)
        click.echo(f"Image converted: {output_path}")
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)

# Emacs Utilities
@cli.group()
def emacs():
    """GNU Emacs utilities"""
    pass

@emacs.command()
@click.argument('expression')
def eval(expression):
    """Evaluate Emacs Lisp expression"""
    result = emacs_eval(expression)
    click.echo(result)

@emacs.command()
@click.argument('filepath', type=click.Path(exists=True))
def open(filepath):
    """Open file in Emacs"""
    result = emacs_open_file(filepath)
    click.echo(result)

@emacs.command()
@click.argument('filepath', type=click.Path(exists=True))
@click.option('--mode', help='Emacs mode (e.g., python-mode, js-mode)')
def format(filepath, mode):
    """Format code file using Emacs"""
    result = emacs_format_code(filepath, mode)
    click.echo(result)

# OpenSSH Utilities
@cli.group()
def ssh():
    """OpenSSH utilities"""
    pass

@ssh.command()
@click.option('--type', '-t', default='rsa', help='Key type (rsa, ed25519, ecdsa)')
@click.option('--bits', '-b', default=2048, help='Key size in bits')
@click.option('--comment', '-C', help='Key comment')
@click.option('--output', '-f', help='Output filename')
def keygen(type, bits, comment, output):
    """Generate SSH key pair"""
    result = ssh_keygen(type, bits, comment, output)
    click.echo(result)

@ssh.command()
@click.argument('user')
@click.argument('host')
@click.option('--key', '-i', help='Identity file')
def copyid(user, host, key):
    """Copy SSH public key to remote host"""
    result = ssh_copy_id(user, host, key)
    click.echo(result)

@ssh.command()
@click.argument('user')
@click.argument('host')
@click.option('--command', '-c', help='Command to execute')
@click.option('--key', '-i', help='Identity file')
def connect(user, host, command, key):
    """SSH connect to remote host"""
    result = ssh_connect(user, host, command, key)
    click.echo(result)

@ssh.command()
@click.argument('local_port', type=int)
@click.argument('remote_host')
@click.argument('remote_port', type=int)
@click.argument('ssh_host')
@click.argument('user')
def tunnel(local_port, remote_host, remote_port, ssh_host, user):
    """Create SSH tunnel"""
    result = ssh_tunnel(local_port, remote_host, remote_port, ssh_host, user)
    click.echo(result)

# S3 Storage
@cli.group()
def s3():
    """AWS S3 storage utilities"""
    pass

@s3.command()
@click.argument('file_path', type=click.Path(exists=True))
@click.argument('bucket')
@click.option('--key', '-k', help='S3 object key')
@click.option('--profile', '-p', help='AWS profile')
def upload(file_path, bucket, key, profile):
    """Upload file to S3"""
    result = s3_upload(file_path, bucket, key, profile)
    click.echo(result)

@s3.command()
@click.argument('bucket')
@click.argument('key')
@click.option('--output', '-o', help='Local output path')
@click.option('--profile', '-p', help='AWS profile')
def download(bucket, key, output, profile):
    """Download file from S3"""
    result = s3_download(bucket, key, output, profile)
    click.echo(result)

@s3.command()
@click.argument('bucket')
@click.option('--prefix', help='Object prefix filter')
@click.option('--profile', '-p', help='AWS profile')
def list(bucket, prefix, profile):
    """List S3 bucket contents"""
    result = s3_list(bucket, prefix or "", profile)
    if isinstance(result, list):
        for obj in result:
            click.echo(f"{obj['Key']} ({obj['Size']} bytes) - {obj['Modified']}")
    else:
        click.echo(result)

@s3.command()
@click.argument('bucket')
@click.argument('key')
@click.option('--profile', '-p', help='AWS profile')
def delete(bucket, key, profile):
    """Delete file from S3"""
    result = s3_delete(bucket, key, profile)
    click.echo(result)

# Nextcloud Storage
@cli.group()
def nextcloud():
    """Nextcloud storage utilities"""
    pass

@nextcloud.command()
@click.argument('file_path', type=click.Path(exists=True))
@click.argument('remote_path')
@click.option('--url', '-u', required=True, help='Nextcloud WebDAV URL')
@click.option('--username', required=True, help='Username')
@click.option('--password', required=True, help='Password')
def upload(file_path, remote_path, url, username, password):
    """Upload file to Nextcloud"""
    result = nextcloud_upload(file_path, remote_path, url, username, password)
    click.echo(result)

@nextcloud.command()
@click.argument('remote_path')
@click.argument('local_path')
@click.option('--url', '-u', required=True, help='Nextcloud WebDAV URL')
@click.option('--username', required=True, help='Username')
@click.option('--password', required=True, help='Password')
def download(remote_path, local_path, url, username, password):
    """Download file from Nextcloud"""
    result = nextcloud_download(remote_path, local_path, url, username, password)
    click.echo(result)

@nextcloud.command()
@click.argument('remote_path')
@click.option('--url', '-u', required=True, help='Nextcloud WebDAV URL')
@click.option('--username', required=True, help='Username')
@click.option('--password', required=True, help='Password')
def list(remote_path, url, username, password):
    """List Nextcloud directory contents"""
    result = nextcloud_list(remote_path, url, username, password)
    if isinstance(result, list):
        for item in result:
            size_info = f" ({item['Size']} bytes)" if item['Type'] == 'File' else ""
            click.echo(f"{item['Name']} [{item['Type']}]{size_info}")
    else:
        click.echo(result)

@nextcloud.command()
@click.argument('remote_path')
@click.option('--url', '-u', required=True, help='Nextcloud WebDAV URL')
@click.option('--username', required=True, help='Username')
@click.option('--password', required=True, help='Password')
def delete(remote_path, url, username, password):
    """Delete file from Nextcloud"""
    result = nextcloud_delete(remote_path, url, username, password)
    click.echo(result)

@nextcloud.command()
@click.argument('remote_path')
@click.option('--url', '-u', required=True, help='Nextcloud WebDAV URL')
@click.option('--username', required=True, help='Username')
@click.option('--password', required=True, help='Password')
def mkdir(remote_path, url, username, password):
    """Create directory in Nextcloud"""
    result = nextcloud_mkdir(remote_path, url, username, password)
    click.echo(result)

# GPG Utilities
@cli.group()
def gpg():
    """GPG encryption and key management"""
    pass

@gpg.command()
@click.argument('file_path', type=click.Path(exists=True))
@click.argument('recipient')
@click.option('--output', '-o', help='Output file path')
def encrypt(file_path, recipient, output):
    """Encrypt file with GPG"""
    result = gpg_encrypt_file(file_path, recipient, output)
    click.echo(result)

@gpg.command()
@click.argument('file_path', type=click.Path(exists=True))
@click.option('--output', '-o', help='Output file path')
def decrypt(file_path, output):
    """Decrypt file with GPG"""
    result = gpg_decrypt_file(file_path, output)
    click.echo(result)

@gpg.command()
@click.argument('file_path', type=click.Path(exists=True))
@click.option('--output', '-o', help='Signature file path')
def sign(file_path, output):
    """Sign file with GPG"""
    result = gpg_sign_file(file_path, output)
    click.echo(result)

@gpg.command()
@click.argument('file_path', type=click.Path(exists=True))
@click.option('--signature', '-s', help='Signature file path')
def verify(file_path, signature):
    """Verify file signature"""
    result = gpg_verify_file(file_path, signature)
    click.echo(result)

@gpg.command()
def listkeys():
    """List GPG keys"""
    result = gpg_list_keys()
    if isinstance(result, list):
        for key in result:
            click.echo(f"{key.get('keyid', 'N/A')} - {key.get('uid', 'N/A')}")
    else:
        click.echo(result)

@gpg.command()
@click.argument('name')
@click.argument('email')
@click.option('--passphrase', default='', help='Key passphrase')
def keygen(name, email, passphrase):
    """Generate GPG key pair"""
    result = gpg_generate_key(name, email, passphrase)
    click.echo(result)

@gpg.command()
@click.argument('keyid')
@click.option('--output', '-o', help='Output file path')
@click.option('--binary', is_flag=True, help='Export in binary format')
def export(keyid, output, binary):
    """Export GPG public key"""
    result = gpg_export_key(keyid, output, not binary)
    click.echo(result)

@gpg.command()
@click.argument('key_file', type=click.Path(exists=True))
def import_key(key_file):
    """Import GPG key"""
    result = gpg_import_key(key_file)
    click.echo(result)

# Text Utilities
@cli.group()
def text():
    """Text processing utilities"""
    pass

@text.command()
@click.argument('text')
def count(text):
    """Count words, lines, and characters"""
    words = count_words(text)
    lines = count_lines(text)
    chars = count_chars(text)
    click.echo(f"Words: {words}, Lines: {lines}, Characters: {chars}")

@text.command()
@click.argument('text')
def urls(text):
    """Extract URLs from text"""
    urls = extract_urls(text)
    for url in urls:
        click.echo(url)

@text.command()
@click.argument('text')
def emails(text):
    """Extract email addresses from text"""
    emails = extract_emails(text)
    for email in emails:
        click.echo(email)

@text.command()
@click.argument('json_text')
def format_json(json_text):
    """Format JSON text"""
    result = json_format(json_text)
    click.echo(result)

@text.command()
@click.argument('text')
@click.option('--reverse', is_flag=True, help='Sort in reverse order')
def sort(text, reverse):
    """Sort lines alphabetically"""
    result = sort_lines(text, reverse)
    click.echo(result)

# Web Utilities
@cli.group()
def web():
    """Web utilities"""
    pass

@web.command()
@click.argument('url')
@click.option('--output', '-o', help='Output file path')
def download(url, output):
    """Download file from URL"""
    result = download_file(url, output)
    click.echo(result)

@web.command()
@click.argument('url')
def check(url):
    """Check website status"""
    result = check_website(url)
    if isinstance(result, dict):
        for key, value in result.items():
            if key != 'headers':
                click.echo(f"{key}: {value}")
    else:
        click.echo(result)

@web.command()
@click.argument('url')
def title(url):
    """Get page title"""
    result = get_page_title(url)
    click.echo(result)

@web.command()
@click.argument('url')
def shorten(url):
    """Shorten URL"""
    result = shorten_url(url)
    click.echo(result)

@web.command()
@click.argument('url')
@click.option('--method', '-m', default='GET', help='HTTP method')
@click.option('--data', '-d', help='JSON data')
def api(url, method, data):
    """Test API endpoint"""
    result = test_api(url, method, data=data)
    if isinstance(result, dict):
        for key, value in result.items():
            click.echo(f"{key}: {value}")
    else:
        click.echo(result)

# Time Utilities
@cli.group()
def time():
    """Time and date utilities"""
    pass

@time.command()
@click.argument('timestamp')
@click.option('--format', '-f', default='%Y-%m-%d %H:%M:%S', help='Date format')
def from_timestamp(timestamp, format):
    """Convert timestamp to date"""
    result = timestamp_to_date(timestamp, format)
    click.echo(result)

@time.command()
@click.argument('date_str')
@click.option('--format', '-f', default='%Y-%m-%d %H:%M:%S', help='Date format')
def to_timestamp(date_str, format):
    """Convert date to timestamp"""
    result = date_to_timestamp(date_str, format)
    click.echo(result)

@time.command()
@click.option('--format', '-f', default='%Y-%m-%d %H:%M:%S', help='Date format')
def now(format):
    """Get current time"""
    result = current_time(format=format)
    click.echo(result)

@time.command()
@click.argument('seconds', type=int)
def countdown(seconds):
    """Countdown timer"""
    result = countdown(seconds)
    click.echo(result)

# Math Utilities
@cli.group()
def math():
    """Math and calculation utilities"""
    pass

@math.command()
@click.argument('expression')
def calc(expression):
    """Calculate expression"""
    result = calculate(expression)
    click.echo(result)

@math.command()
@click.argument('number')
@click.argument('from_base', type=int)
@click.argument('to_base', type=int)
def base(number, from_base, to_base):
    """Convert number between bases"""
    result = convert_base(number, from_base, to_base)
    click.echo(result)

@math.command()
@click.argument('numbers')
def stats(numbers):
    """Calculate statistics"""
    result = statistics_calc(numbers)
    if isinstance(result, dict):
        for key, value in result.items():
            click.echo(f"{key}: {value}")
    else:
        click.echo(result)

@math.command()
@click.option('--type', '-t', default='int', help='Number type (int/float)')
@click.option('--min', default=1, help='Minimum value')
@click.option('--max', default=100, help='Maximum value')
@click.option('--count', '-c', default=1, help='Count of numbers')
def random(type, min, max, count):
    """Generate random numbers"""
    result = generate_random(type, min, max, count)
    click.echo(result)

@math.command()
@click.argument('value')
@click.argument('from_unit')
@click.argument('to_unit')
def convert(value, from_unit, to_unit):
    """Convert between units"""
    result = unit_convert(value, from_unit, to_unit)
    click.echo(result)

# Media Utilities
@cli.group()
def media():
    """Media processing utilities"""
    pass

@media.command()
@click.argument('file_path', type=click.Path(exists=True))
def info(file_path):
    """Get media file information"""
    result = get_media_info(file_path)
    if isinstance(result, dict):
        for key, value in result.items():
            click.echo(f"{key}: {value}")
    else:
        click.echo(result)

@media.command()
@click.argument('input_path', type=click.Path(exists=True))
@click.argument('output_path')
@click.option('--format', '-f', default='mp3', help='Output format')
@click.option('--bitrate', '-b', default='192k', help='Audio bitrate')
def convert_audio(input_path, output_path, format, bitrate):
    """Convert audio file format"""
    result = convert_audio(input_path, output_path, format, bitrate)
    click.echo(result)

@media.command()
@click.argument('video_path', type=click.Path(exists=True))
@click.option('--output', '-o', help='Output audio file')
def extract_audio(video_path, output):
    """Extract audio from video"""
    result = extract_audio(video_path, output)
    click.echo(result)

@media.command()
@click.argument('input_path', type=click.Path(exists=True))
@click.option('--output', '-o', help='Output PDF file')
@click.option('--quality', '-q', default='ebook', help='Compression quality')
def compress_pdf(input_path, output, quality):
    """Compress PDF file"""
    result = compress_pdf(input_path, output, quality)
    click.echo(result)

# Development Utilities
@cli.group()
def dev():
    """Development utilities"""
    pass

@dev.command()
@click.option('--version', '-v', default=4, help='UUID version')
@click.option('--count', '-c', default=1, help='Number of UUIDs')
def uuid(version, count):
    """Generate UUID"""
    result = generate_uuid(version, count)
    if count > 1:
        for uuid_str in result:
            click.echo(uuid_str)
    else:
        click.echo(result)

@dev.command()
@click.option('--length', '-l', default=16, help='Password length')
@click.option('--no-symbols', is_flag=True, help='Exclude symbols')
def password(length, no_symbols):
    """Generate secure password"""
    result = generate_password(length, not no_symbols)
    click.echo(result)

@dev.command()
@click.option('--length', '-l', default=32, help='API key length')
def apikey(length):
    """Generate API key"""
    result = generate_api_key(length)
    click.echo(result)

@dev.command()
@click.argument('json_str')
def minify(json_str):
    """Minify JSON"""
    result = minify_json(json_str)
    click.echo(result)

@dev.command()
def git():
    """Get git repository status"""
    result = git_status()
    if isinstance(result, dict):
        for key, value in result.items():
            click.echo(f"{key}: {value}")
    else:
        click.echo(result)

@dev.command()
def docker():
    """List Docker containers"""
    result = docker_ps()
    if isinstance(result, list):
        for container in result:
            click.echo(f"{container.get('Names', 'N/A')} - {container.get('Status', 'N/A')}")
    else:
        click.echo(result)

# System Monitor
@cli.group()
def monitor():
    """System monitoring utilities"""
    pass

@monitor.command()
def cpu():
    """Get CPU usage"""
    result = cpu_usage()
    click.echo(f"CPU Usage: {result}%")

@monitor.command()
def memory():
    """Get memory usage"""
    result = memory_usage()
    for key, value in result.items():
        click.echo(f"{key}: {value}")

@monitor.command()
@click.option('--path', '-p', default='/', help='Path to check')
def disk(path):
    """Get disk usage"""
    result = disk_usage(path)
    for key, value in result.items():
        click.echo(f"{key}: {value}")

@monitor.command()
def network():
    """Get network statistics"""
    result = network_stats()
    for key, value in result.items():
        click.echo(f"{key}: {value}")

@monitor.command()
@click.option('--count', '-c', default=10, help='Number of processes')
def top(count):
    """Get top processes"""
    result = top_processes(count)
    for proc in result:
        click.echo(f"{proc['pid']} {proc['name']} - CPU: {proc['cpu_percent']}%")

@monitor.command()
def ports():
    """Get port listeners"""
    result = port_listeners()
    for listener in result:
        click.echo(f"Port {listener['port']}: {listener['process']} (PID: {listener['pid']})")

@monitor.command()
def uptime():
    """Get system uptime"""
    result = system_uptime()
    click.echo(f"Uptime: {result}")

# Backup Utilities
@cli.group()
def backup():
    """Backup and archive utilities"""
    pass

@backup.command()
@click.argument('source_path', type=click.Path(exists=True))
@click.option('--output', '-o', help='Output ZIP file')
def zip(source_path, output):
    """Create ZIP archive"""
    result = create_zip(source_path, output)
    click.echo(result)

@backup.command()
@click.argument('zip_path', type=click.Path(exists=True))
@click.option('--extract-to', '-e', help='Extract destination')
def unzip(zip_path, extract_to):
    """Extract ZIP archive"""
    result = extract_zip(zip_path, extract_to)
    click.echo(result)

@backup.command()
@click.argument('source_path', type=click.Path(exists=True))
@click.option('--output', '-o', help='Output TAR file')
@click.option('--compression', '-c', default='gz', help='Compression type')
def tar(source_path, output, compression):
    """Create TAR archive"""
    result = create_tar(source_path, output, compression)
    click.echo(result)

@backup.command()
@click.argument('source')
@click.argument('destination')
@click.option('--delete', is_flag=True, help='Delete extraneous files')
def sync(source, destination, delete):
    """Sync directories"""
    result = sync_directories(source, destination, delete)
    click.echo(result)

def main():
    cli()

if __name__ == '__main__':
    main()