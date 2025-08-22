<div align="center">

  <h1>DumprX v2.0</h1>

  <h4>Modern Python Firmware Dumper with CLI Interface</h4>

  <p>Complete migration from bash to Python with enhanced features and modern architecture</p>

</div>

## What's New in v2.0

DumprX has been completely rewritten in Python with a modern architecture:

- **🐍 Pure Python Implementation**: No more bash dependencies, fully cross-platform
- **🖥️ Modern CLI Interface**: Beautiful Rich-based CLI with progress bars and colors
- **⚙️ Configuration Management**: YAML-based configuration with easy management
- **📦 Modular Architecture**: Clean separation of concerns with pluggable extractors and downloaders
- **🚀 Easy Installation**: Standard Python packaging with pip install
- **🔧 Developer Friendly**: Well-structured codebase for easy maintenance and extension

## Architecture

```
DumprX v2.0/
├── dumprx/           # Main CLI entry point
├── core/             # Core business logic and configuration
├── downloaders/      # Download modules for different services
├── extractors/       # Firmware extraction modules
├── modules/          # Shared utilities and functions
├── utils/            # Console, git, and integration utilities
└── bin/              # External binary tools
```

## Installation

### Prerequisites

- Python 3.8 or higher
- System dependencies (automatically installed via setup script)

### Quick Setup

```bash
# Clone the repository
git clone https://github.com/Eduardob3677/DumprX.git
cd DumprX

# Run setup script (installs system dependencies and Python package)
./setup.sh

# Or install manually
pip install -e .
```

## Usage

### Basic Firmware Dumping

```bash
# Dump firmware from file
dumprx dump /path/to/firmware.zip

# Dump firmware from URL
dumprx dump 'https://example.com/firmware.zip'

# Dump with custom output directory
dumprx dump firmware.zip -o my_output
```

### Download Only

```bash
# Download from various sources
dumprx download 'https://mega.nz/file/...'
dumprx download 'https://drive.google.com/file/...'
dumprx download 'https://mediafire.com/file/...'
```

### Configuration Management

```bash
# Show current configuration
dumprx config show

# Set configuration values
dumprx config set device.brand "Samsung"
dumprx config set device.codename "SM-G998B"
dumprx config set git.auto_push true
```

### System Dump with Configuration

```bash
# Advanced system dump with config variables
dumprx system-dump \
  --config-vars '{"device.brand": "Samsung", "device.codename": "galaxy_s21"}' \
  --firmware-url 'https://example.com/firmware.zip'
```

### Setup Dependencies

```bash
# Setup external tools and dependencies
dumprx setup
```

## Supported Formats

DumprX v2.0 supports all formats from the original version:

### Archive Formats
- ZIP, RAR, 7Z, TAR, TAR.GZ, TGZ, TAR.MD5

### Firmware Formats
- **OZIP/OFP/OPS** (OPPO/OnePlus)
- **KDZ** (LG)
- **UPDATE.APP** (Huawei)
- **Payload.bin** (Android OTA)
- **Super Images** (Android Dynamic Partitions)
- **SDAT** (Android Sparse Data)
- **PAC** (Spreadtrum)
- **RUU** (HTC)
- **NB0** (Nokia)
- **SIN** (Sony)

### Download Sources
- **Mega.nz**
- **MediaFire**
- **Google Drive**
- **AndroidFileHost**
- **WeTransfer**
- **Direct HTTP/HTTPS links**

## Configuration

Configuration is stored in `~/.dumprx/config.yaml` and includes:

```yaml
# Device Information
device:
  brand: "Samsung"
  codename: "SM-G998B"
  platform: "snapdragon"
  release: "13"
  treble_support: true
  is_ab: true

# Git Integration
git:
  auto_push: false
  organization: "your-github-org"
  user_name: "Your Name"
  user_email: "your@email.com"

# Telegram Notifications
telegram:
  enabled: false
  token: "your-bot-token"
  chat_id: "@YourChannel"
```

## Development

### Project Structure

- **Core Modules**:
  - `core/dumper.py` - Main firmware processing pipeline
  - `core/config.py` - Configuration management
  - `core/setup.py` - Dependency setup

- **Downloaders**:
  - `downloaders/mega.py` - Mega.nz downloader
  - `downloaders/mediafire.py` - MediaFire downloader
  - `downloaders/gdrive.py` - Google Drive downloader
  - `downloaders/afh.py` - AndroidFileHost downloader

- **Extractors**:
  - `extractors/kdz.py` - LG KDZ extractor
  - `extractors/update_app.py` - Huawei UPDATE.APP extractor
  - `extractors/ozip.py` - OPPO OZIP extractor
  - And many more...

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## Migration from v1.x

If you were using the bash version of DumprX:

1. Your existing `out/` directories remain compatible
2. Configuration needs to be migrated to the new YAML format
3. All functionality is preserved and enhanced
4. Binary tools are automatically managed

## Troubleshooting

### Common Issues

1. **Python Dependencies**: Run `./setup.sh` to install all dependencies
2. **Binary Tools**: External tools are automatically cloned and managed
3. **Permissions**: Ensure you have write permissions in the working directory

### Getting Help

- Check the configuration: `dumprx config show`
- Use verbose output: Add `-v` flag to commands
- Review logs in the output directory

## Credits

- Based on the original DumprX bash version
- Incorporates tools from AndroidDumps and various firmware extraction projects
- Built with modern Python libraries: Click, Rich, PyYAML, GitPython
         >> Must Wrap Website Link Inside Single-quotes ('')
  >> Supported File Formats For Direct Operation:
         *.zip | *.rar | *.7z | *.tar | *.tar.gz | *.tgz | *.tar.md5
         *.ozip | *.ofp | *.ops | *.kdz | ruu_*exe
         system.new.dat | system.new.dat.br | system.new.dat.xz
         system.new.img | system.img | system-sign.img | UPDATE.APP
         *.emmc.img | *.img.ext4 | system.bin | system-p | payload.bin
         *.nb0 | .*chunk* | *.pac | *super*.img | *system*.sin
```

## GitHub Actions Workflow Usage

You can now use the automated GitHub Actions workflow to dump firmware automatically in the cloud. This workflow allows you to:

- Specify a firmware URL to download and dump
- Choose between GitHub or GitLab as your git provider
- Configure authentication tokens through the workflow interface
- Automatically set up Git LFS for large files

### How to use the workflow:

1. **Go to the Actions tab** in your GitHub repository
2. **Select "Firmware Dump Workflow"** from the workflow list
3. **Click "Run workflow"** button
4. **Fill in the required parameters:**
   - **Firmware URL**: Direct download link to the firmware file
   - **Git Provider**: Choose between `github` or `gitlab`
   - **Authentication tokens**: Based on your provider selection:
     - For GitHub: Provide `github_token` and optionally `github_orgname`
     - For GitLab: Provide `gitlab_token` and optionally `gitlab_group` and `gitlab_instance`
   - **Optional**: Telegram tokens for notifications

### Workflow Features:

- ✅ **Automated dependency installation** using the existing setup.sh script
- ✅ **Git LFS configuration** for handling large firmware files
- ✅ **Disk space optimization** by cleaning up unnecessary packages
- ✅ **8-hour timeout** for large firmware processing
- ✅ **Automatic cleanup** of sensitive authentication data
- ✅ **Debug artifacts** uploaded on failure for troubleshooting

### Environment Variables Configured:

The workflow automatically configures the following based on your selections:
- `PUSH_TO_GITLAB`: Set to `true` when GitLab is selected, `false` for GitHub
- Git configuration with appropriate user email and name
- HTTP buffer settings for large file uploads

### Security Notes:

- All authentication tokens are handled securely through GitHub Actions secrets
- Token files are automatically cleaned up after the workflow completes
- No sensitive data is logged or stored in artifacts

## How to use it to Upload the Dump in GitHub (Local Setup)

- Copy your GITHUB_TOKEN in a file named .github_token and add your GitHub Organization name in another file named .github_orgname inside the project directory.
  - If only Token is given but Organization is not, your Git Username will be used.
- Copy your Telegram Token in a file named .tg_token and Telegram Chat/Channel ID in another file named .tg_chat file if you want to publish the uploading info in Telegram.

## Main Scripture Credit

As mentioned above, this toolkit is entirely focused on improving the Original Firmware Dumper available:  [Dumpyara](https://github.com/AndroidDumps/) [Phoenix Firmware Dumper](https://github.com/DroidDumps)

Credit for those tools goes to everyone whosoever worked hard to put all those programs in one place to make an awesome project.

## Download Utilities Credits

- mega-media-drive_dl.sh (for downloading from mega.nz, mediafire.com, google drive)
  - shell script, most of it's part belongs to badown by @stck-lzm
- afh_dl (for downloading from androidfilehosts.com)
  - python script, by @kade-robertson
- aria2c
- wget

## Internal Utilities Credits

- sdat2img.py (system-dat-to-img v1.2, python script)
  - by @xpirt, @luxi78, @howellzhu
- simg2img (Android sparse-to-raw images converter, binary built from source)
  - by @anestisb
- unsin (Xperia Firmware Unpacker v1.13, binary)
  - by @IgorEisberg
- extract\_android\_ota\_payload.py (OTA Payload Extractor, python script)
  - by @cyxx, with metadata update from [Android's update_engine Git Repository](https://android.googlesource.com/platform/system/update_engine/)
- extract-dtb.py (dtbs extractor v1.3, python script)
  - by @PabloCastellano
- dtc (Device Tree Compiler v1.6, binary built from source)
  - by kernel.org, from their [dtc Git Repository](https://git.kernel.org/pub/scm/utils/dtc/dtc.git)
- vmlinux-to-elf and kallsyms_finder (kernel binary to analyzable ELF converter, python scripts)
  - by @marin-m
- ozipdecrypt.py (Oppo/Oneplus .ozip Firmware decrypter v1.2, python script)
  - by @bkerler
- ofp\_qc\_extract.py and ofp\_mtk\_decrypt.py (Oppo .ofp firmware extractor, python scripts)
  - by @bkerler
- opscrypto.py (OnePlus/Oppo ops firmware extractor, python script)
  - by @bkerler
- lpunpack (OnePlus/Other super.img unpacker, binary built from source)
  - by @LonelyFool
- splituapp.py (UPDATE.APP extractor, python script)
  - by @superr
- pacextractor (Extractor of SpreadTrum firmware files with extension pac. See)
  - by @HemanthJabalpuri
- nb0-extract (Nokia/Sharp/Infocus/Essential nb0-extract, binary built from source)
  - by Heineken @Eddie07 / "FIH mobile"
- kdztools' unkdz.py and undz.py (LG KDZ and DZ Utilities, python scripts)
  - Originally by IOMonster (thecubed on XDA), Modified by @ehem (Elliott Mitchell) and improved by @steadfasterX
- RUU\_Decrypt\_Tool (HTC RUU/ROM Decryption Tool v3.6.8, binary)
  - by @nkk71 and @CaptainThrowback
- extract-ikconfig (.config file extractor from kernel image, shell script)
  - From within linux's source code by @torvalds
- unpackboot.sh (bootimg and ramdisk extractor, modified shell script)
  - Originally by @xiaolu and @carlitros900, stripped to unpack functionallity, by me @rokibhasansagar
- twrpdtgen by @SebaUbuntu
