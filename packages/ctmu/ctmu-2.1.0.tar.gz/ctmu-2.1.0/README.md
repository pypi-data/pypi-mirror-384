# CTMU for macOS

**Swiss Army Knife CLI Tool** - QR codes, hashing, networking, file operations, and more!

[![Tests](https://github.com/JohnThre/CTMU-for-macOS/actions/workflows/test.yml/badge.svg)](https://github.com/JohnThre/CTMU-for-macOS/actions/workflows/test.yml)
[![Release](https://github.com/JohnThre/CTMU-for-macOS/actions/workflows/release.yml/badge.svg)](https://github.com/JohnThre/CTMU-for-macOS/actions/workflows/release.yml)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![codecov](https://codecov.io/gh/JohnThre/CTMU-for-macOS/branch/main/graph/badge.svg)](https://codecov.io/gh/JohnThre/CTMU-for-macOS)

```
┌─────────────────────────────────────────────────────────────┐
│                    CTMU Architecture                        │
├─────────────────────────────────────────────────────────────┤
│  QR Codes    Security    Network    Files    Images        │
│  System      Text        Web        Time     Math           │
│  Media       Dev Tools   Monitor    Backup   Storage       │
│  Emacs       SSH         GPG        S3/Cloud               │
└─────────────────────────────────────────────────────────────┘
```

## Overview

CTMU (Custom Terminal Multi Utility) is a comprehensive command-line Swiss Army knife for macOS developers and power users. Originally designed for QR code generation, it now includes 60+ essential utilities across 15 categories for daily development tasks.

**One Tool, Multiple Solutions** - Replace dozens of separate utilities with a single, powerful CLI.

## Features

### QR Code Generation
- Professional QR codes with website favicons
- Three elegant styles: Bauhaus, Classic, Hacker
- High-resolution output (PNG, JPEG, SVG)

### Security & Hashing
- Hash files and text (SHA256, MD5, SHA1, SHA512)
- Base64 encoding/decoding
- File integrity verification

### Network Utilities
- Port connectivity testing
- HTTP header inspection
- Built-in port scanner
- nmap integration

### File Operations
- File information and metadata
- Directory tree visualization
- Batch file operations

### System Information
- macOS system details
- Battery status monitoring
- Hardware information

### Image Processing
- Image resizing and conversion
- Format transformation
- Batch image operations

### GNU Emacs Integration
- Evaluate Emacs Lisp expressions
- Open files in Emacs editor
- Format code using Emacs modes

### OpenSSH Integration
- Generate SSH key pairs
- Copy keys to remote hosts
- SSH connections and tunnels
- Remote command execution

### Cloud Storage
- AWS S3 file operations
- Nextcloud WebDAV integration
- Upload, download, list, delete files
- Directory management

### GPG Encryption
- File encryption and decryption
- Digital signatures and verification
- Key generation and management
- Import/export keys

### Text Processing
- Word, line, character counting
- URL and email extraction
- JSON formatting and CSV conversion
- Line sorting and deduplication

### Web Utilities
- File downloading from URLs
- Website status checking
- Page title extraction
- URL shortening and API testing

### Time & Date
- Timestamp conversions
- Current time in multiple formats
- Time difference calculations
- Countdown timers

### Math & Calculations
- Safe expression calculator
- Number base conversions
- Statistical calculations
- Unit conversions and random numbers

### Media Processing
- Audio/video file information
- Audio format conversion
- Audio extraction from video
- PDF compression

### Development Tools
- UUID and password generation
- JSON minification and validation
- Git repository status
- Docker container management

### System Monitoring
- CPU, memory, disk usage
- Network statistics
- Process monitoring
- Port listeners and uptime

### Backup & Archives
- ZIP and TAR archive creation
- Directory synchronization
- Database backups
- File compression utilities

## Requirements

- **Platform:** macOS 10.14+
- **Python:** 3.8+
- **Optional:** nmap (for advanced network scanning)
- **Optional:** GNU Emacs (for Emacs integration)
- **Optional:** AWS CLI configured (for S3 operations)
- **Optional:** Nextcloud server access (for WebDAV operations)
- **Optional:** GPG (for encryption operations)

## Installation

### Quick Install
```bash
# Clone and install
git clone <repository-url>
cd "CTMU for macOS"
./install.sh
```

### Manual Install
```bash
pip install -r requirements.txt
pip install -e .
```

### Verify Installation
```bash
ctmu --help
```

## Command Reference

### QR Code Generation
```bash
ctmu qr <url> [--style bauhaus|classic|hacker] [--output dir]

# Examples
ctmu qr https://github.com
ctmu qr https://apple.com --style classic --output ~/Desktop
```

### Security & Hashing
```bash
ctmu hash text "message"              # Hash text
ctmu hash file document.pdf --algo md5 # Hash file
ctmu encode b64 "secret"               # Base64 encode
ctmu encode b64d "encoded_string"      # Base64 decode
```

### Network Utilities
```bash
ctmu net ping host --port 80           # Check connectivity
ctmu net scan localhost --start 1 --end 1000  # Port scan
ctmu net headers https://api.com       # HTTP headers
ctmu net nmap target --type fast       # Nmap scan
```

### File Operations
```bash
ctmu file info document.pdf           # File details
ctmu file tree /path/to/dir           # Directory tree
```

### System Information
```bash
ctmu sys info                         # System details
ctmu sys battery                      # Battery status
```

### Image Processing
```bash
ctmu img resize input.jpg output.jpg --width 800
ctmu img convert image.png image.jpg --format JPEG
```

### GNU Emacs
```bash
ctmu emacs eval "(+ 2 3)"              # Evaluate Lisp
ctmu emacs open file.py                # Open in Emacs
ctmu emacs format code.py --mode python-mode  # Format code
```

### OpenSSH
```bash
ctmu ssh keygen --type ed25519         # Generate SSH key
ctmu ssh copyid user host              # Copy key to host
ctmu ssh connect user host --command "ls -la"  # Execute command
ctmu ssh tunnel 8080 localhost 80 server user  # Create tunnel
```

### Cloud Storage
```bash
# AWS S3
ctmu s3 upload file.txt my-bucket --key path/file.txt
ctmu s3 download my-bucket path/file.txt --output local.txt
ctmu s3 list my-bucket --prefix docs/
ctmu s3 delete my-bucket path/file.txt

# Nextcloud
ctmu nextcloud upload file.txt /remote/file.txt -u https://cloud.example.com/remote.php/dav/files/username/ --username user --password pass
ctmu nextcloud download /remote/file.txt local.txt -u https://cloud.example.com/remote.php/dav/files/username/ --username user --password pass
ctmu nextcloud list /remote/ -u https://cloud.example.com/remote.php/dav/files/username/ --username user --password pass
ctmu nextcloud mkdir /remote/newfolder -u https://cloud.example.com/remote.php/dav/files/username/ --username user --password pass
```

### GPG Encryption
```bash
ctmu gpg encrypt document.txt user@example.com
ctmu gpg decrypt document.txt.gpg
ctmu gpg sign document.txt
ctmu gpg verify document.txt --signature document.txt.sig
ctmu gpg keygen "John Doe" john@example.com
ctmu gpg listkeys
ctmu gpg export KEYID --output public.asc
ctmu gpg import-key public.asc
```

### Text Processing
```bash
ctmu text count "Hello world from CTMU"
ctmu text urls "Visit https://github.com and https://apple.com"
ctmu text emails "Contact john@example.com or jane@company.org"
ctmu text format-json '{"name":"CTMU","type":"CLI"}'
ctmu text sort "zebra\napple\nbanana" --reverse
```

### Web Utilities
```bash
ctmu web download https://example.com/file.zip
ctmu web check https://github.com
ctmu web title https://apple.com
ctmu web shorten https://very-long-url.com/path/to/resource
ctmu web api https://api.github.com/users/octocat --method GET
```

### Time & Date
```bash
ctmu time from-timestamp 1640995200
ctmu time to-timestamp "2022-01-01 00:00:00"
ctmu time now --format "%Y-%m-%d %H:%M:%S"
ctmu time countdown 60
```

### Math & Calculations
```bash
ctmu math calc "2 + 3 * 4"
ctmu math base 255 10 16
ctmu math stats "1,2,3,4,5,6,7,8,9,10"
ctmu math random --type int --min 1 --max 100 --count 5
ctmu math convert 100 cm m
```

### Media Processing
```bash
ctmu media info video.mp4
ctmu media convert-audio input.wav output.mp3 --bitrate 320k
ctmu media extract-audio video.mp4 --output audio.mp3
ctmu media compress-pdf large.pdf --quality ebook
```

### Development Tools
```bash
ctmu dev uuid --count 5
ctmu dev password --length 20
ctmu dev apikey --length 64
ctmu dev minify '{"key": "value", "array": [1, 2, 3]}'
ctmu dev git
ctmu dev docker
```

### System Monitoring
```bash
ctmu monitor cpu
ctmu monitor memory
ctmu monitor disk --path /home
ctmu monitor network
ctmu monitor top --count 5
ctmu monitor ports
ctmu monitor uptime
```

### Backup & Archives
```bash
ctmu backup zip project/ --output project_backup.zip
ctmu backup unzip backup.zip --extract-to ./restored/
ctmu backup tar documents/ --compression gz
ctmu backup sync source/ destination/ --delete
```

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                      CTMU Core                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ QR Generator│  │   Network   │  │   Security  │        │
│  │             │  │   Scanner   │  │   Hasher    │        │
│  │ • Bauhaus   │  │ • Port Scan │  │ • SHA256    │        │
│  │ • Classic   │  │ • nmap      │  │ • MD5       │        │
│  │ • Hacker    │  │ • Headers   │  │ • Base64    │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │    File     │  │   System    │  │    Image    │        │
│  │  Operations │  │    Info     │  │ Processing  │        │
│  │             │  │             │  │             │        │
│  │ • Info      │  │ • macOS     │  │ • Resize    │        │
│  │ • Tree      │  │ • Battery   │  │ • Convert   │        │
│  │ • Metadata  │  │ • Hardware  │  │ • Optimize  │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │    Text     │  │     Web     │  │    Time     │        │
│  │ Processing  │  │  Utilities  │  │   & Date    │        │
│  │             │  │             │  │             │        │
│  │ • Count     │  │ • Download  │  │ • Convert   │        │
│  │ • Extract   │  │ • Check     │  │ • Format    │        │
│  │ • Format    │  │ • API Test  │  │ • Timer     │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │    Math     │  │    Media    │  │ Development │        │
│  │ Calculator  │  │ Processing  │  │    Tools    │        │
│  │             │  │             │  │             │        │
│  │ • Calculate │  │ • Audio     │  │ • UUID      │        │
│  │ • Convert   │  │ • Video     │  │ • Password  │        │
│  │ • Stats     │  │ • PDF       │  │ • JSON      │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   System    │  │   Backup    │  │   Storage   │        │
│  │ Monitoring  │  │  & Archive  │  │   Cloud     │        │
│  │             │  │             │  │             │        │
│  │ • CPU       │  │ • ZIP/TAR   │  │ • S3        │        │
│  │ • Memory    │  │ • Sync      │  │ • Nextcloud │        │
│  │ • Process   │  │ • Database  │  │ • WebDAV    │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐                         │
│  │ GNU Emacs   │  │     GPG     │                         │
│  │ Integration │  │ Encryption  │                         │
│  │             │  │             │                         │
│  │ • Eval      │  │ • Encrypt   │                         │
│  │ • Open      │  │ • Sign      │                         │
│  │ • Format    │  │ • Keys      │                         │
│  └─────────────┘  └─────────────┘                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Professional Applications

| Use Case | Commands | Benefits |
|----------|----------|----------|
| **DevOps** | `hash`, `net nmap`, `sys info` | Deployment verification, security scanning |
| **Development** | `qr`, `net ping`, `img resize` | Portfolio QRs, service checks, asset optimization |
| **Security** | `hash file`, `encode b64`, `net scan` | File integrity, secret encoding, reconnaissance |
| **Content** | `qr`, `img convert`, `file tree` | Social QRs, format conversion, organization |
| **Emacs Users** | `emacs eval`, `emacs format` | Lisp evaluation, code formatting |
| **SSH/Remote** | `ssh keygen`, `ssh tunnel` | Key management, secure connections |
| **Cloud Storage** | `s3 upload`, `nextcloud sync` | File backup, cloud synchronization |
| **Security** | `gpg encrypt`, `gpg sign` | File encryption, digital signatures |
| **Text Processing** | `text count`, `text urls` | Text analysis, data extraction |
| **Web Operations** | `web download`, `web check` | File downloads, site monitoring |
| **Time Management** | `time now`, `time countdown` | Time tracking, scheduling |
| **Calculations** | `math calc`, `math convert` | Quick calculations, unit conversions |
| **Media Processing** | `media info`, `media convert-audio` | Audio/video processing, PDF compression |
| **Development** | `dev uuid`, `dev password` | Code generation, project management |
| **System Monitor** | `monitor cpu`, `monitor top` | Performance monitoring, diagnostics |
| **Backup/Archive** | `backup zip`, `backup sync` | Data backup, file archiving |

## Command Categories

### Core Commands (15 categories, 60+ commands)

1. **QR Code Generation** - 1 command
2. **Security & Hashing** - 4 commands  
3. **Network Utilities** - 4 commands
4. **File Operations** - 2 commands
5. **System Information** - 2 commands
6. **Image Processing** - 2 commands
7. **GNU Emacs Integration** - 3 commands
8. **OpenSSH Integration** - 4 commands
9. **Cloud Storage** - 8 commands (S3 + Nextcloud)
10. **GPG Encryption** - 8 commands
11. **Text Processing** - 5 commands
12. **Web Utilities** - 5 commands
13. **Time & Date** - 4 commands
14. **Math & Calculations** - 5 commands
15. **Media Processing** - 4 commands
16. **Development Tools** - 6 commands
17. **System Monitoring** - 7 commands
18. **Backup & Archives** - 4 commands

## Performance & Features

### Performance
- **Fast Execution**: < 1 second response time
- **Concurrent Scanning**: 100 threads for port scanning
- **Memory Efficient**: Minimal resource usage
- **Batch Processing**: Handle multiple files/operations

### Technical Features
- **Modular Architecture**: Easy to extend
- **Error Handling**: Graceful failure management
- **Cross-Format Support**: Multiple output formats
- **macOS Integration**: Native system APIs

### Security
- **Multiple Hash Algorithms**: SHA256, MD5, SHA1, SHA512
- **Secure Encoding**: Base64 utilities
- **Network Security**: Port scanning and reconnaissance
- **File Integrity**: Checksum verification

## Troubleshooting

### Common Issues
- **nmap not found**: Install with `brew install nmap`
- **Emacs not found**: Install with `brew install emacs`
- **Permission denied**: Use `sudo` for system-level operations
- **Image processing errors**: Ensure PIL/Pillow is installed
- **Network timeouts**: Check firewall settings
- **S3 access denied**: Configure AWS credentials with `aws configure`
- **Nextcloud connection failed**: Verify WebDAV URL and credentials
- **GPG not found**: Install with `brew install gnupg`

### Getting Help
```bash
ctmu --help                    # Main help
ctmu <command> --help          # Command help
```

## License

GPL v3 License - See [LICENSE](LICENSE) file for details.

---

**CTMU** - One tool, endless possibilities. Transform your macOS terminal into a Swiss Army knife of utilities.