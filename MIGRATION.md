# DumprX v2.0 - Migration Guide

## Overview

DumprX v2.0 represents a complete migration from the original bash-based tool to a modern Python application with a rich CLI interface. This migration provides better maintainability, extensibility, and user experience while preserving all existing functionality.

## What's New

### Modern Python Architecture
- **Click-based CLI** with comprehensive help and command structure
- **Rich console output** with progress bars, colors, and formatted displays
- **Modular design** with clear separation of concerns
- **YAML configuration** with backward compatibility for legacy token files
- **Type hints and modern Python practices**

### Enhanced Features
- **Improved error handling** with better error messages and recovery
- **Progress tracking** for downloads and extractions
- **Telegram notifications** with rich status updates
- **Git integration** with automated repository creation and management
- **Configuration management** with easy show/set commands
- **Dependency testing** and setup automation

### Maintained Compatibility
- **All existing functionality** preserved from the original bash version
- **Same output structure** and file organization
- **Legacy token support** for existing workflows
- **CI/CD compatibility** with same input/output behavior

## Installation

### Requirements
- Python 3.8 or later
- Git
- Standard Unix tools (7zz, aria2c, wget, etc.)

### Quick Setup
```bash
# Clone the repository
git clone https://github.com/Eduardob3677/DumprX.git
cd DumprX

# Install dependencies
python3 dumprx.py setup

# Or install manually
pip install -r requirements.txt
```

## Usage

### Command Line Interface

The new CLI provides a comprehensive command structure:

```bash
# Show help
python3 dumprx.py --help

# Extract firmware (main functionality)
python3 dumprx.py extract firmware.zip
python3 dumprx.py extract "https://mega.nz/file/..."

# Download only
python3 dumprx.py download "https://example.com/firmware.zip"

# Configuration management
python3 dumprx.py config show
python3 dumprx.py config set git.provider github
python3 dumprx.py config set telegram.enabled true

# Setup and testing
python3 dumprx.py setup
python3 dumprx.py test

# Version information
python3 dumprx.py version
```

### Configuration

DumprX v2.0 uses YAML configuration stored in `~/.dumprx/config.yaml`:

```yaml
output_dir: out
input_dir: input
temp_dir: tmp

git:
  enabled: true
  provider: github  # or gitlab
  auto_push: true

telegram:
  enabled: false
  token: ""
  chat_id: ""

download:
  max_retries: 3
  chunk_size: 8192
  timeout: 30
```

### Backward Compatibility

Legacy token files are still supported:
- `.github_token` - GitHub access token
- `.gitlab_token` - GitLab access token  
- `.tg_token` - Telegram bot token
- `.tg_chat` - Telegram chat ID

## Migration from Bash Version

### For End Users

1. **Continue using the bash version** if you prefer:
   ```bash
   ./dumper.sh firmware.zip
   ```

2. **Try the Python version** for new features:
   ```bash
   python3 dumprx.py extract firmware.zip
   ```

3. **Gradually migrate** by testing the Python version alongside the bash version

### For CI/CD Workflows

The Python version maintains the same interface for automation:

```bash
# Old way (still works)
./dumper.sh "$FIRMWARE_URL"

# New way (equivalent functionality)
python3 dumprx.py extract "$FIRMWARE_URL"
```

### For Developers

The modular Python architecture makes it easier to:
- Add new firmware formats in `dumprx/extractors/`
- Add new download sources in `dumprx/downloaders/`
- Customize output formatting in `dumprx/modules/formatters.py`
- Integrate with external services

## Supported Formats

All formats from the original version are supported:

### Archive Formats
- ZIP, RAR, 7Z, TAR, TAR.GZ, TGZ, TAR.MD5

### Vendor-Specific Formats
- **LG**: KDZ, DZ files
- **Oppo/OnePlus**: OZIP, OFP, OPS files
- **HTC**: RUU files
- **Huawei**: UPDATE.APP files
- **Nokia**: NB0 files
- **SpreadTrum**: PAC files

### Android Formats
- System images (system.img, system.new.dat, system.new.dat.br)
- Payload files (payload.bin)
- Super images (super.img)
- Sparse images with automatic conversion
- EXT4 and EROFS filesystems

### Download Sources
- Direct HTTP/HTTPS links
- Mega.nz
- MediaFire
- Google Drive
- OneDrive
- AndroidFileHost

## Troubleshooting

### Common Issues

1. **Missing dependencies**:
   ```bash
   python3 dumprx.py setup
   ```

2. **Import errors**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Binary tool errors**:
   ```bash
   python3 dumprx.py test
   ```

### Getting Help

- Run `python3 dumprx.py --help` for command help
- Run `python3 dumprx.py test` to check your setup
- Check the GitHub issues for known problems
- Use `python3 dumprx.py config show` to verify configuration

## Development

### Project Structure

```
dumprx/
├── cli.py              # Main CLI interface
├── core/               # Core business logic
│   ├── config.py       # Configuration management
│   ├── device.py       # Device information extraction
│   ├── setup.py        # Dependency setup
│   └── test.py         # Integration testing
├── downloaders/        # Download implementations
├── extractors/         # Extraction implementations
├── modules/            # Shared utilities
├── utils/              # Console, Git, Telegram utilities
└── bin/                # Binary dependencies
```

### Adding New Features

1. **New firmware format**: Add extractor in `dumprx/extractors/`
2. **New download source**: Add downloader in `dumprx/downloaders/`
3. **New output format**: Add formatter in `dumprx/modules/formatters.py`
4. **New CLI command**: Add to `dumprx/cli.py`

### Testing

```bash
# Run all tests
python3 dumprx.py test

# Test specific components
python3 -c "from dumprx.core.test import test_system_dependencies; test_system_dependencies()"
```

## Future Plans

- **Package distribution** via PyPI for easier installation
- **Plugin system** for third-party extensions
- **Web interface** for browser-based usage
- **Docker support** for containerized environments
- **Enhanced device database** with automatic detection
- **Parallel processing** for faster extraction

## Contributing

The Python architecture makes contributing much easier:

1. Fork the repository
2. Create a feature branch
3. Add your changes in the appropriate module
4. Test with `python3 dumprx.py test`
5. Submit a pull request

See the modular structure for guidance on where to add new functionality.