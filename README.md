<div align="center">

  <h1>DumprX</h1>

  <h4>Modern Python-Based Firmware Dumping Toolkit</h4>

</div>


## What this really is

DumprX is a completely modernized and refactored firmware dumping toolkit, rewritten in Python with a modern architecture. Originally based on Phoenix Firmware Dumper, it now features:

## Key Features and Improvements

- [x] **Complete Python rewrite** - Modern, maintainable, and extensible codebase
- [x] **Modular architecture** - Clean separation of concerns with lib/ structure  
- [x] **Modern CLI interface** - Intuitive command-line interface with proper argument parsing
- [x] **Async/await support** - Efficient handling of downloads and I/O operations
- [x] **Type hints throughout** - Better code quality and IDE support
- [x] **Advanced firmware detection** - Enhanced detection for various firmware types
- [x] **Multiple downloader support** - Mega.NZ, MediaFire, Google Drive, AndroidFileHost, WeTransfer
- [x] **Smart extraction engine** - Automatic firmware type detection and appropriate extractor selection
- [x] **Device tree generation** - TWRP and LineageOS device tree generation
- [x] **Git integration** - GitHub and GitLab upload support
- [x] **Telegram notifications** - Real-time progress and completion notifications
- [x] **Configuration management** - YAML-based configuration system
- [x] **Validation system** - Comprehensive workflow validation
- [x] **Progress indicators** - Visual progress bars and status updates
- [x] **Error handling** - Robust error handling with clear messages

## System Requirements

This toolkit can run on any modern Linux distribution with Python 3.8+. Tested on:
- Ubuntu 20.04+ (Focal and newer)
- Debian 11+ (Bullseye and newer)  
- Arch Linux
- Fedora 35+
- macOS (with Homebrew)

For any other UNIX Distributions, please refer to internal [Setup File](setup.sh) and install the required programs via their own package manager.

## Quick Start

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Eduardob3677/DumprX.git
   cd DumprX
   ```

2. **Run the setup script:**
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```

3. **Validate the installation:**
   ```bash
   python3 dumprx.py --validate
   ```

### Usage

**Extract firmware from a file:**
```bash
python3 dumprx.py /path/to/firmware.zip
```

**Download and extract from URL:**
```bash
python3 dumprx.py 'https://example.com/firmware.zip'
```

**Extract with custom output directory:**
```bash
python3 dumprx.py firmware.zip --output /path/to/output
```

**Skip git upload:**
```bash
python3 dumprx.py firmware.zip --no-upload
```

**Verbose logging:**
```bash
python3 dumprx.py firmware.zip --verbose
```

### Supported Firmware Types

- **Archives:** ZIP, RAR, 7Z, TAR, TAR.GZ, TAR.MD5
- **OEM Formats:** OZIP, OFP, OPS (OPPO), KDZ/DZ (LG), RUU (HTC)
- **Android Images:** payload.bin, super.img, system.img, system.new.dat
- **Vendor Specific:** UPDATE.APP (Huawei), PAC, NB0, SIN (Sony)
- **Boot Images:** boot.img, recovery.img, vendor_boot.img
- **Sparse Images:** Android sparse image format
- **Chunk Files:** Samsung chunk-based firmware

### Configuration

Edit `config.yaml` to customize:
- Download settings (timeouts, retry attempts)
- Git repository settings  
- Telegram notification settings
- Extraction parameters
- Logging configuration

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
