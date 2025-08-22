#!/bin/bash

# DumprX Setup Script - Python Edition
# This script installs all dependencies for the modern Python-based DumprX

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
PURPLE='\033[0;35m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NORMAL='\033[0m'

# Abort function
function abort(){
    [ ! -z "$@" ] && echo -e ${RED}"${@}"${NORMAL}
    exit 1
}

# Banner
function __bannerTop() {
    echo -e \
    ${GREEN}"
    ██████╗░██╗░░░██╗███╗░░░███╗██████╗░██████╗░██╗░░██╗
    ██╔══██╗██║░░░██║████╗░████║██╔══██╗██╔══██╗╚██╗██╔╝
    ██║░░██║██║░░░██║██╔████╔██║██████╔╝██████╔╝░╚███╔╝░
    ██║░░██║██║░░░██║██║╚██╔╝██║██╔═══╝░██╔══██╗░██╔██╗░
    ██████╔╝╚██████╔╝██║░╚═╝░██║██║░░░░░██║░░██║██╔╝╚██╗
    ╚═════╝░░╚═════╝░╚═╝░░░░░╚═╝╚═╝░░░░░╚═╝░░╚═╝╚═╝░░╚═╝
    "${NORMAL}
}

# Display banner
clear
echo -e ${GREEN} && __bannerTop && echo -e ${NORMAL}
echo -e ${BLUE}"🛠️  DumprX v2.0 - Modern Python Setup"${NORMAL}
echo -e ${PURPLE}"Setting up dependencies for the modern Python-based firmware extraction toolkit"${NORMAL}
echo ""

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo -e ${RED}"⚠️  This script should not be run as root"${NORMAL}
   echo -e ${YELLOW}"Please run as a regular user with sudo access"${NORMAL}
   exit 1
fi

# Detect OS
if [[ "$OSTYPE" == "linux-gnu" ]]; then

    if command -v apt > /dev/null 2>&1; then

        echo -e ${PURPLE}"🐧 Ubuntu/Debian Based Distro Detected"${NORMAL}
        sleep 1
        echo -e ${BLUE}">> Updating apt repos..."${NORMAL}
        sleep 1
        sudo apt -y update || abort "Setup Failed!"
        sleep 1
        echo -e ${BLUE}">> Installing Required Packages..."${NORMAL}
        sleep 1
        
        # Core system packages for firmware extraction
        sudo apt install -y \
            unace unrar zip unzip p7zip-full p7zip-rar sharutils rar uudeview mpack arj cabextract \
            device-tree-compiler liblzma-dev brotli liblz4-tool axel gawk aria2 detox cpio rename \
            liblz4-dev jq git-lfs curl wget python3 python3-pip python3-dev python3-venv \
            build-essential pkg-config libssl-dev libffi-dev \
            || abort "Setup Failed!"

    elif command -v dnf > /dev/null 2>&1; then

        echo -e ${PURPLE}"🔴 Fedora Based Distro Detected"${NORMAL}
        sleep 1
        echo -e ${BLUE}">> Installing Required Packages..."${NORMAL}
        sleep 1

        # "dnf" automatically updates repos before installing packages
        sudo dnf install -y \
            unace unrar zip unzip sharutils uudeview arj cabextract file-roller dtc \
            brotli axel aria2 detox cpio lz4 xz-devel p7zip p7zip-plugins git-lfs \
            curl wget python3 python3-pip python3-devel \
            gcc gcc-c++ make pkgconfig openssl-devel libffi-devel \
            || abort "Setup Failed!"

    elif command -v pacman > /dev/null 2>&1; then

        echo -e ${PURPLE}"🔵 Arch or Arch Based Distro Detected"${NORMAL}
        sleep 1
        echo -e ${BLUE}">> Installing Required Packages..."${NORMAL}
        sleep 1

        sudo pacman -Syyu --needed --noconfirm >/dev/null || abort "Setup Failed!"
        sudo pacman -Sy --noconfirm \
            unace unrar p7zip sharutils uudeview arj cabextract file-roller dtc brotli axel gawk \
            aria2 detox cpio lz4 jq git-lfs curl wget python python-pip \
            base-devel pkgconf openssl libffi \
            || abort "Setup Failed!"

    else
        echo -e ${RED}"❌ Unsupported Linux distribution"${NORMAL}
        echo -e ${YELLOW}"Please install the required packages manually"${NORMAL}
        abort "Setup Failed!"
    fi

elif [[ "$OSTYPE" == "darwin"* ]]; then

    echo -e ${PURPLE}"🍎 macOS Detected"${NORMAL}
    sleep 1
    echo -e ${BLUE}">> Installing Required Packages..."${NORMAL}
    sleep 1
    
    # Check if Homebrew is installed
    if ! command -v brew > /dev/null 2>&1; then
        echo -e ${YELLOW}"📦 Installing Homebrew..."${NORMAL}
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)" || abort "Homebrew installation failed!"
    fi
    
    brew install protobuf xz brotli lz4 aria2 detox coreutils p7zip gawk git-lfs \
                 python3 || abort "Setup Failed!"

else
    echo -e ${RED}"❌ Unsupported operating system: $OSTYPE"${NORMAL}
    abort "Setup Failed!"
fi

sleep 1

# Install uv for faster Python package management
echo -e ${BLUE}">> Installing uv for Python package management..."${NORMAL}
sleep 1
if ! command -v uv > /dev/null 2>&1; then
    curl -LsSf https://astral.sh/uv/install.sh | sh || abort "uv installation failed!"
    export PATH="$HOME/.local/bin:$PATH"
fi

sleep 1

# Install Python dependencies
echo -e ${BLUE}">> Installing Python dependencies..."${NORMAL}
sleep 1
if command -v uv > /dev/null 2>&1; then
    uv pip install --system click rich || abort "Python dependencies installation failed!"
else
    pip3 install click rich || abort "Python dependencies installation failed!"
fi

sleep 1

# Install DumprX package
echo -e ${BLUE}">> Installing DumprX package..."${NORMAL}
sleep 1
if command -v uv > /dev/null 2>&1; then
    uv pip install --system -e . || abort "DumprX installation failed!"
else
    pip3 install -e . || abort "DumprX installation failed!"
fi

sleep 1

# Verify installation
echo -e ${BLUE}">> Verifying installation..."${NORMAL}
sleep 1

if command -v dumprx > /dev/null 2>&1; then
    echo -e ${GREEN}"✅ DumprX command is available"${NORMAL}
else
    echo -e ${YELLOW}"⚠️  DumprX command not found in PATH"${NORMAL}
    echo -e ${BLUE}"Try running: export PATH=\"\$HOME/.local/bin:\$PATH\""${NORMAL}
fi

# Setup external tools
echo -e ${BLUE}">> Setting up external tools..."${NORMAL}
dumprx setup || echo -e ${YELLOW}"⚠️  External tools setup failed - you can run 'dumprx setup' later"${NORMAL}

sleep 1

# Done!
echo ""
echo -e ${GREEN}"🎉 Setup Complete!"${NORMAL}
echo ""
echo -e ${BLUE}"📱 DumprX v2.0 is now ready to use!"${NORMAL}
echo ""
echo -e ${YELLOW}"Usage Examples:"${NORMAL}
echo -e ${BLUE}"  dumprx dump firmware.zip"${NORMAL}
echo -e ${BLUE}"  dumprx dump 'https://example.com/firmware.zip'"${NORMAL}
echo -e ${BLUE}"  dumprx info firmware.zip"${NORMAL}
echo -e ${BLUE}"  dumprx --help"${NORMAL}
echo ""
echo -e ${GREEN}"✨ Happy firmware dumping!"${NORMAL}
echo ""

# Exit
exit 0