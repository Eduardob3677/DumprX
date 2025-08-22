<div align="center">

  <h1>DumprX</h1>

  <h4>Modern Python Firmware Dumping and Extraction Toolkit v2.0</h4>

</div>


## What this really is

DumprX is a completely refactored and modernized firmware extraction toolkit, migrated from bash to Python with a professional CLI interface. This toolkit provides comprehensive firmware dumping capabilities with Rich console output, progress bars, and intelligent device detection.

## The improvements in v2.0

- [x] **Complete Python migration** - All bash scripts converted to modern Python with Click CLI
- [x] **Rich console interface** - Beautiful CLI with colors, emojis, progress bars and panels
- [x] **Intelligent device detection** - Automatic detection of device information, partitions, and configurations
- [x] **Modern downloaders** - Support for MEGA, MediaFire, Google Drive, AndroidFileHost with progress tracking
- [x] **Comprehensive extractors** - Support for all major firmware formats with improved error handling
- [x] **Git integration** - Automatic repository setup and firmware dump uploads
- [x] **External tool management** - Automatic cloning and updating of required tools
- [x] **Modular architecture** - Clean separation into core, downloaders, extractors, modules, and utils

## Requirements

- Python 3.8 or newer
- Git and Git LFS
- Standard extraction tools (7z, unrar, etc.)

## Installation

1. **Clone the repository**:
```bash
git clone https://github.com/Eduardob3677/DumprX.git
cd DumprX
```

2. **Run the setup script**:
```bash
./setup.sh
```

3. **Activate the virtual environment**:
```bash
source .venv/bin/activate
```

## Usage

### Command Line Interface

```bash
dumprx <firmware_file_or_url> [OPTIONS]
```

### Options

- `-u, --url TEXT` - 🌐 Firmware download URL
- `-c, --config TEXT` - ⚙️ Configuration file path  
- `-o, --output TEXT` - 📤 Output directory
- `-v, --verbose` - 🔍 Verbose output
- `--github-token TEXT` - 🔐 GitHub token for uploads
- `--telegram-token TEXT` - 📱 Telegram bot token
- `--chat-id TEXT` - 💬 Telegram chat ID

### Examples

```bash
# Extract local firmware file
dumprx firmware.zip

# Download and extract from URL
dumprx 'https://example.com/firmware.zip'

# Extract with custom output directory
dumprx firmware.zip -o /path/to/output

# Verbose extraction with GitHub upload
dumprx firmware.zip --verbose --github-token ghp_xxxx
```

## Supported File Formats

- **Archives**: *.zip | *.rar | *.7z | *.tar | *.tar.gz | *.tgz | *.tar.md5
- **Vendor specific**: *.ozip | *.ofp | *.ops | *.kdz | ruu_*.exe
- **Android images**: system.new.dat | system.new.dat.br | system.new.dat.xz
- **System images**: system.new.img | system.img | system-sign.img | UPDATE.APP
- **Other formats**: *.emmc.img | *.img.ext4 | system.bin | system-p | payload.bin
- **Special formats**: *.nb0 | .*chunk* | *.pac | *super*.img | *system*.sin

## Supported Download Sources

- **Direct links** from any website
- **MEGA** (mega.nz)
- **MediaFire** (mediafire.com)
- **Google Drive** (drive.google.com)
- **AndroidFileHost** (androidfilehost.com)

## Project Structure

```
dumprx/
├── core/               # Core firmware processing logic
├── downloaders/        # Download managers for different sources
├── extractors/         # Firmware format extractors
├── modules/            # Device detection and Git management  
├── utils/              # Utilities and external tool management
├── cli.py             # Main CLI interface
└── __init__.py        # Package initialization

bin/                   # Binary tools and utilities
utils/                 # Legacy tools and scripts
setup.sh              # Installation and setup script
```

## GitHub Actions Workflow Usage

You can use the automated GitHub Actions workflow to dump firmware in the cloud. The workflow supports the new Python CLI and provides the same functionality with improved error handling and progress reporting.

## Credits

### Main Scripture Credit
This toolkit improves upon the original [Dumpyara](https://github.com/AndroidDumps/) and [Phoenix Firmware Dumper](https://github.com/DroidDumps) projects.

### Python Migration
- **DumprX v2.0** - Complete Python migration with modern CLI by DumprX Team

### External Tools
All external tools are automatically managed and include:
- sdat2img.py, unsin, extract-dtb.py, dtc, vmlinux-to-elf
- ozipdecrypt, ofp extractors, lpunpack, splituapp
- kdztools, RUU_Decrypt_Tool, pacextractor, and more

### Download Utilities  
- AFH downloader, MEGA/MediaFire/GDrive scripts
- Integrated aria2c and direct download support
