#!/bin/bash

# DumprX Modern Setup Script
# This script installs system dependencies and sets up the Python environment

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NORMAL='\033[0m'

# Banner
echo -e "${GREEN}"
echo "██████╗░██╗░░░██╗███╗░░░███╗██████╗░██████╗░██╗░░██╗"
echo "██╔══██╗██║░░░██║████╗░████║██╔══██╗██╔══██╗╚██╗██╔╝"
echo "██║░░██║██║░░░██║██╔████╔██║██████╔╝██████╔╝░╚███╔╝░"
echo "██║░░██║██║░░░██║██║╚██╔╝██║██╔═══╝░██╔══██╗░██╔██╗░"
echo "██████╔╝╚██████╔╝██║░╚═╝░██║██║░░░░░██║░░██║██╔╝╚██╗"
echo "╚═════╝░░╚═════╝░╚═╝░░░░░╚═╝╚═╝░░░░░╚═╝░░╚═╝╚═╝░░╚═╝"
echo -e "${NORMAL}"
echo -e "${BLUE}DumprX v2.0 Setup - Installing Dependencies${NORMAL}"
echo

abort() {
    echo -e "${RED}$1${NORMAL}"
    exit 1
}

# Detect OS and install system packages
if [[ "$OSTYPE" == "linux-gnu" ]]; then
    if command -v apt > /dev/null 2>&1; then
        echo -e "${PURPLE}Ubuntu/Debian Based Distro Detected${NORMAL}"
        echo -e "${BLUE}>> Updating apt repos...${NORMAL}"
        sudo apt -y update || abort "Failed to update repositories"
        
        echo -e "${BLUE}>> Installing Required Packages...${NORMAL}"
        sudo apt install -y \
            unace unrar zip unzip p7zip-full p7zip-rar sharutils rar uudeview \
            mpack arj cabextract device-tree-compiler liblzma-dev python3-pip \
            brotli liblz4-tool axel gawk aria2 detox cpio rename liblz4-dev \
            jq git-lfs python3-venv python3-dev build-essential || abort "Failed to install packages"
            
    elif command -v dnf > /dev/null 2>&1; then
        echo -e "${PURPLE}Fedora Based Distro Detected${NORMAL}"
        echo -e "${BLUE}>> Installing Required Packages...${NORMAL}"
        sudo dnf install -y \
            unace unrar zip unzip sharutils uudeview arj cabextract file-roller \
            dtc python3-pip brotli axel aria2 detox cpio lz4 python3-devel \
            xz-devel p7zip p7zip-plugins git-lfs gcc || abort "Failed to install packages"
            
    elif command -v pacman > /dev/null 2>&1; then
        echo -e "${PURPLE}Arch or Arch Based Distro Detected${NORMAL}"
        echo -e "${BLUE}>> Updating system...${NORMAL}"
        sudo pacman -Syyu --needed --noconfirm || abort "Failed to update system"
        
        echo -e "${BLUE}>> Installing Required Packages...${NORMAL}"
        sudo pacman -Sy --noconfirm \
            unace unrar p7zip sharutils uudeview arj cabextract file-roller \
            dtc brotli axel gawk aria2 detox cpio lz4 jq git-lfs python-pip \
            base-devel || abort "Failed to install packages"
            
    else
        abort "Unsupported Linux distribution. Please install dependencies manually."
    fi
    
elif [[ "$OSTYPE" == "darwin"* ]]; then
    echo -e "${PURPLE}macOS Detected${NORMAL}"
    if ! command -v brew > /dev/null 2>&1; then
        abort "Homebrew not found. Please install Homebrew first: https://brew.sh"
    fi
    
    echo -e "${BLUE}>> Installing Required Packages...${NORMAL}"
    brew install protobuf xz brotli lz4 aria2 detox coreutils p7zip gawk git-lfs || abort "Failed to install packages"
    
else
    abort "Unsupported operating system: $OSTYPE"
fi

# Install Python dependencies
echo -e "${BLUE}>> Installing Python dependencies...${NORMAL}"
if command -v uv > /dev/null 2>&1; then
    echo "Using uv package manager..."
    uv pip install click rich requests py7zr patool pyyaml tqdm gitpython zstandard --system || abort "Failed to install Python packages with uv"
else
    echo "Using pip..."
    python3 -m pip install --user click rich requests py7zr patool pyyaml tqdm gitpython zstandard || abort "Failed to install Python packages with pip"
fi

# Set up external tools
echo -e "${BLUE}>> Setting up external tools...${NORMAL}"
python3 -m dumprx.cli.main --setup-tools || abort "Failed to setup external tools"

# Create symlink for easy access
echo -e "${BLUE}>> Creating command alias...${NORMAL}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Create a wrapper script in ~/.local/bin if it exists
if [ -d "$HOME/.local/bin" ]; then
    cat > "$HOME/.local/bin/dumprx" << EOF
#!/bin/bash
cd "$SCRIPT_DIR" && python3 -m dumprx.cli.main "\$@"
EOF
    chmod +x "$HOME/.local/bin/dumprx"
    echo -e "${GREEN}✓ Created command alias: dumprx${NORMAL}"
    
    # Add to PATH if not already there
    if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
        echo -e "${BLUE}Added ~/.local/bin to PATH in ~/.bashrc${NORMAL}"
        echo -e "${BLUE}Run 'source ~/.bashrc' or start a new terminal to use 'dumprx' command${NORMAL}"
    fi
else
    echo -e "${BLUE}To use 'dumprx' command, run:${NORMAL}"
    echo -e "${BLUE}cd $SCRIPT_DIR && python3 -m dumprx.cli.main${NORMAL}"
fi

echo
echo -e "${GREEN}✓ Setup Complete!${NORMAL}"
echo -e "${BLUE}You can now run firmware extraction with:${NORMAL}"
echo -e "${BLUE}  dumprx <firmware_file>${NORMAL}"
echo -e "${BLUE}  or${NORMAL}"
echo -e "${BLUE}  cd $SCRIPT_DIR && python3 -m dumprx.cli.main <firmware_file>${NORMAL}"
echo
echo -e "${BLUE}For help:${NORMAL}"
echo -e "${BLUE}  dumprx --help${NORMAL}"