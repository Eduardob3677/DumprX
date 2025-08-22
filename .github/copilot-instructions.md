# DumprX - Firmware Dumping Toolkit

DumprX is a comprehensive firmware extraction toolkit based on shell scripts and binary utilities. It supports extracting various firmware formats and can operate both locally and through GitHub Actions workflows. This toolkit processes Android firmware files, OTA packages, and other embedded system firmware.

Always reference these instructions first and fallback to search or bash commands only when you encounter unexpected information that does not match the info here.

## Working Effectively

### Bootstrap and Setup (One-time)
- `./setup.sh` -- takes 80-90 seconds to complete. NEVER CANCEL. Set timeout to 180+ seconds.
  - Installs system dependencies via package managers (apt/dnf/pacman/brew)
  - Installs Python package manager `uv`
  - Configures Git LFS for large file handling
  - Must be run with sudo privileges for package installation

### Firmware Processing (Per Firmware)
- `./dumper.sh <firmware_file_or_url>` -- time varies by firmware size (30 seconds to 2+ hours). NEVER CANCEL for large firmware files. Set timeout to 3+ hours.
  - Supports local files: `.zip`, `.rar`, `.7z`, `.tar`, `.ozip`, `.kdz`, `.nb0`, `.pac`, `payload.bin`, etc.
  - Supports URLs from: direct downloads, mega.nz, mediafire, gdrive, onedrive, androidfilehost
  - URLs must be wrapped in single quotes: `'https://example.com/firmware.zip'`
  - Creates output in `out/` directory with extracted partitions and metadata

### Validation and Verification
- `./validate-workflow.sh` -- takes under 1 second. Validates all workflow components.
- ALWAYS run this before using GitHub Actions workflow
- ALWAYS run `shellcheck` on modified shell scripts before committing

## GitHub Actions Workflow Usage

### Cloud-based Processing
- Go to Actions tab → Select "Firmware Dump Workflow" → Click "Run workflow"
- **8-hour timeout** for large firmware processing. NEVER CANCEL.
- Required parameters:
  - **Firmware URL**: Direct download link
  - **Git Provider**: `github` or `gitlab`
  - **Authentication tokens**: Based on provider selection
- Optional: Telegram notifications via bot token and chat ID

### Environment Variables Configured by Workflow
- `PUSH_TO_GITLAB`: Set to `true` when GitLab selected, `false` for GitHub
- Git configuration with appropriate user email and name
- HTTP buffer settings for large file uploads

## Validation Scenarios

### After Making Code Changes
- ALWAYS run `./setup.sh` if dependencies changed
- ALWAYS run `./validate-workflow.sh` to verify workflow components
- ALWAYS test dumper functionality with a small test firmware:
  ```bash
  # Create test firmware
  mkdir -p /tmp/test && echo "test" > /tmp/test/system.img
  cd /tmp/test && zip ../test.zip . && cd -
  ./dumper.sh /tmp/test.zip
  # Verify out/ directory contains extracted content
  ```
- ALWAYS run `shellcheck` on modified shell scripts:
  ```bash
  shellcheck setup.sh dumper.sh validate-workflow.sh
  ```

### Manual Testing Workflow
1. Test basic help functionality: `./dumper.sh` (should show usage)
2. Test with invalid input: `./dumper.sh nonexistent.zip` (should fail gracefully)
3. Test with valid small firmware file (as shown above)
4. Verify output structure in `out/` directory
5. Clean up: `rm -rf out/*` between tests

## Command Timing and Expectations

- **Setup**: 80-90 seconds (includes package installation)
- **Validation**: Under 1 second
- **Small firmware dumping**: 5-30 seconds
- **Large firmware dumping**: 30 minutes to 2+ hours
- **GitHub Actions workflow**: Up to 8 hours for very large files

## Critical Dependencies

### System Requirements
- Linux (Ubuntu/Debian preferred, Fedora/Arch supported)
- macOS supported via Homebrew
- Minimum 4GB free disk space
- Internet connection for downloads

### Key Commands Installed by setup.sh
- `python3` (3.8+)
- `git` and `git-lfs`
- Archive tools: `7z`, `unrar`, `zip`, `unzip`
- Download tools: `aria2c`, `axel`, `wget`
- Build tools: `device-tree-compiler`, `cpio`
- Processing tools: `brotli`, `lz4`, `detox`

### Binary Utilities (Pre-compiled)
- `utils/lpunpack` - Super partition unpacker
- `utils/sdat2img.py` - Sparse Android data image converter
- `utils/unsin` - Xperia firmware unpacker
- `utils/dtc` - Device tree compiler
- `utils/extract-ikconfig` - Kernel config extractor

## Common File Locations

### Repository Structure
```
.
├── README.md                    # Main documentation
├── setup.sh                    # Dependency installer (run once)
├── dumper.sh                   # Main firmware processor
├── validate-workflow.sh        # Component validator
├── .github/workflows/          # GitHub Actions workflow
├── utils/                      # Binary tools and utilities
├── out/                        # Output directory (created during processing)
└── WORKFLOW_EXAMPLES.md        # GitHub Actions examples
```

### Input/Output Directories
- `input/` - Temporary firmware download directory (auto-created)
- `out/` - Final extracted firmware output (auto-created)
- `out/tmp/` - Temporary processing directory (auto-created)

## Error Handling and Troubleshooting

### Common Issues
- **Space issues**: Clean up `out/` and `input/` directories between runs
- **Permission issues**: Ensure `setup.sh` and `dumper.sh` are executable
- **Python syntax errors**: Some legacy utilities have minor syntax issues but still function
- **Mount failures**: System partition extraction may fail for newer filesystem types (EROFS, F2FS)

### Debug Information
- Firmware processing logs are displayed in real-time
- Failed GitHub Actions workflows upload debug artifacts
- Use `shellcheck` to validate shell script syntax

## Security Notes

### Local Setup
- Token files (.github_token, .gitlab_token, .tg_token) are git-ignored
- Store authentication tokens in separate files, not in scripts
- Clean up token files after use

### GitHub Actions
- All tokens handled securely through GitHub Actions secrets
- Automatic cleanup of sensitive data after workflow completion
- No sensitive data logged or stored in artifacts

## Do Not Do

- Do not modify binary utilities in `utils/` unless absolutely necessary
- Do not commit token files or sensitive credentials
- Do not cancel long-running firmware processing operations
- Do not skip dependency installation via `setup.sh`
- Do not use this toolkit on Windows (Linux/macOS only)
- Do not process firmware files larger than available disk space