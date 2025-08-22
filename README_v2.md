# DumprX v2.0 - Modern Firmware Extraction Toolkit

DumprX is a powerful Python-based toolkit for extracting firmware files from various formats including Android ROMs, OTA packages, and vendor-specific firmware formats.

## 🚀 Features

- **Modern CLI**: Built with Click and Rich for beautiful console output
- **Multi-format Support**: OZIP, KDZ, OPS, ZIP, 7Z, TAR, payload.bin, UPDATE.APP, and more
- **Auto-detection**: Automatically detects firmware types and applies appropriate extraction methods
- **External Tools**: Manages and automatically sets up required external tools
- **Boot Image Support**: Extract and unpack Android boot images
- **Download Support**: Direct firmware downloading from Mega, MediaFire, Google Drive, and AndroidFileHost
- **Progress Tracking**: Beautiful progress bars and status indicators

## 📦 Installation

### Prerequisites

Install system dependencies:

```bash
# Ubuntu/Debian
sudo apt install -y unace unrar zip unzip p7zip-full p7zip-rar sharutils rar uudeview mpack arj cabextract device-tree-compiler liblzma-dev python3-pip brotli liblz4-tool axel gawk aria2 detox cpio rename liblz4-dev jq git-lfs

# Fedora
sudo dnf install -y unace unrar zip unzip sharutils uudeview arj cabextract file-roller dtc python3-pip brotli axel aria2 detox cpio lz4 python3-devel xz-devel p7zip p7zip-plugins git-lfs

# Arch Linux
sudo pacman -Sy --noconfirm unace unrar p7zip sharutils uudeview arj cabextract file-roller dtc brotli axel gawk aria2 detox cpio lz4 jq git-lfs
```

### Install DumprX

```bash
# Clone repository
git clone https://github.com/Eduardob3677/DumprX.git
cd DumprX

# Install Python dependencies and setup
pip install -r requirements.txt
pip install -e .

# Setup external tools
dumprx setup
```

Or use the automated setup script:

```bash
chmod +x setup.sh
./setup.sh
```

## 🎯 Usage

### Extract Firmware

```bash
# Extract local firmware file
dumprx dump firmware.zip

# Extract with custom output directory
dumprx dump firmware.zip --output /path/to/output

# Extract from URL (with automatic download)
dumprx dump "https://example.com/firmware.zip"

# Extract with tool setup
dumprx dump firmware.zip --setup-tools
```

### Unpack Boot Images

```bash
# Unpack boot image
dumprx unpack-boot boot.img

# Unpack with custom output directory
dumprx unpack-boot boot.img --output boot_unpacked
```

### Project Management

```bash
# Get project information
dumprx info

# Analyze firmware file
dumprx info firmware.zip

# Setup external tools
dumprx setup

# Clean temporary files
dumprx clean

# Show version
dumprx --version
```

## 📋 Supported Formats

### Archive Formats
- ZIP, RAR, 7Z, TAR, TAR.GZ, TGZ, TAR.MD5

### Firmware Formats
- **Android**: payload.bin (OTA), super.img, system.img, boot.img
- **Oppo/OnePlus**: .ozip, .ops, .ofp
- **LG**: .kdz, .dz
- **Huawei**: UPDATE.APP
- **Sony**: .sin files
- **HTC**: RUU executables
- **Spreadtrum**: .pac files
- **Nokia**: .nb0 files

### Download Sources
- Mega.nz
- MediaFire
- Google Drive
- AndroidFileHost
- Direct HTTP/HTTPS URLs

## 🏗️ Architecture

DumprX v2.0 is built with a modular Python architecture:

```
dumprx/
├── cli.py              # Main CLI interface
├── firmware_extractor.py  # Core extraction logic
├── firmware_detector.py   # Format detection
├── boot_unpacker.py       # Boot image handling
├── external_tools.py      # Tool management
├── downloader.py          # URL downloading
├── utils.py               # Shared utilities
└── banner.py              # UI components
```

## 🔧 Development

### Running from Source

```bash
# Direct execution
python3 dumprx_main.py dump firmware.zip

# Or use the installed package
dumprx dump firmware.zip
```

### Adding New Formats

1. Add detection logic in `firmware_detector.py`
2. Implement extraction in `firmware_extractor.py`
3. Add any required external tools in `external_tools.py`

## 📝 Migration from v1.x

DumprX v2.0 is a complete rewrite in Python. Key changes:

- **Shell scripts replaced**: All bash scripts migrated to Python modules
- **Modern CLI**: Click-based command interface
- **Rich output**: Beautiful console output with progress bars
- **Modular design**: Easy to extend and maintain
- **Better error handling**: Proper exception handling and logging

Old v1.x usage:
```bash
./dumper.sh firmware.zip
```

New v2.0 usage:
```bash
dumprx dump firmware.zip
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## 🙏 Credits

- Original DumprX by the Android development community
- External tools by their respective authors
- Python rewrite and modernization