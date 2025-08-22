#!/bin/bash

# Clear Screen
tput reset 2>/dev/null || clear

# Colours (or Colors in en_US)
RED='\033[0;31m'
GREEN='\033[0;32m'
PURPLE='\033[0;35m'
BLUE='\033[0;34m'
NORMAL='\033[0m'

# Abort Function
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

# Welcome Banner
printf "\e[32m" && __bannerTop && printf "\e[0m"

# Minor Sleep
sleep 1

if [[ "$OSTYPE" == "linux-gnu" ]]; then

    if command -v apt > /dev/null 2>&1; then

        echo -e ${PURPLE}"Ubuntu/Debian Based Distro Detected"${NORMAL}
        sleep 1
        echo -e ${BLUE}">> Updating apt repos..."${NORMAL}
        sleep 1
	    sudo apt -y update || abort "Setup Failed!"
	    sleep 1
	    echo -e ${BLUE}">> Installing Required Packages..."${NORMAL}
	    sleep 1
        sudo apt install -y unace unrar zip unzip p7zip-full p7zip-rar sharutils rar uudeview mpack arj cabextract device-tree-compiler liblzma-dev python3-pip brotli liblz4-tool axel gawk aria2 detox cpio rename liblz4-dev jq git-lfs || abort "Setup Failed!"

    elif command -v dnf > /dev/null 2>&1; then

        echo -e ${PURPLE}"Fedora Based Distro Detected"${NORMAL}
        sleep 1
	    echo -e ${BLUE}">> Installing Required Packages..."${NORMAL}
	    sleep 1

	    # "dnf" automatically updates repos before installing packages
        sudo dnf install -y unace unrar zip unzip sharutils uudeview arj cabextract file-roller dtc python3-pip brotli axel aria2 detox cpio lz4 python3-devel xz-devel p7zip p7zip-plugins git-lfs || abort "Setup Failed!"

    elif command -v pacman > /dev/null 2>&1; then

        echo -e ${PURPLE}"Arch or Arch Based Distro Detected"${NORMAL}
        sleep 1
	    echo -e ${BLUE}">> Installing Required Packages..."${NORMAL}
	    sleep 1

        sudo pacman -Syyu --needed --noconfirm >/dev/null || abort "Setup Failed!"
        sudo pacman -Sy --noconfirm unace unrar p7zip sharutils uudeview arj cabextract file-roller dtc brotli axel gawk aria2 detox cpio lz4 jq git-lfs || abort "Setup Failed!"

    fi

elif [[ "$OSTYPE" == "darwin"* ]]; then

    echo -e ${PURPLE}"macOS Detected"${NORMAL}
    sleep 1
	echo -e ${BLUE}">> Installing Required Packages..."${NORMAL}
	sleep 1
    brew install protobuf xz brotli lz4 aria2 detox coreutils p7zip gawk git-lfs || abort "Setup Failed!"

fi

sleep 1

# Install `uv`
echo -e ${BLUE}">> Installing uv for python packages..."${NORMAL}
sleep 1
bash -c "$(curl -sL https://astral.sh/uv/install.sh)" || abort "Setup Failed!"

# Install Python dependencies
echo -e ${BLUE}">> Installing Python dependencies..."${NORMAL}
sleep 1

if command -v uv > /dev/null 2>&1; then
    export PATH="${HOME}/.local/bin:${PATH}"
    uv init --no-readme --python 3.11 || true
    
    cat > pyproject.toml << 'EOF'
[project]
name = "dumprx"
version = "2.0.0"
description = "Modern firmware extraction toolkit"
requires-python = ">=3.8"
dependencies = [
    "aiohttp",
    "aiofiles", 
    "PyYAML",
    "rich",
    "click",
    "tqdm"
]

[tool.uv]
dev-dependencies = []
EOF
    
    uv sync || abort "Python dependency installation failed!"
else
    echo -e ${RED}"uv installation failed, falling back to pip"${NORMAL}
    pip3 install aiohttp aiofiles PyYAML rich click tqdm || abort "Python dependency installation failed!"
fi

# Create Python dependencies directory
echo -e ${BLUE}">> Setting up project structure..."${NORMAL}
sleep 1

# Make main script executable
chmod +x dumprx.py 2>/dev/null || true

# Done!
echo -e ${GREEN}"Setup Complete!"${NORMAL}
echo -e ${GREEN}"You can now run: ./dumprx.py <firmware_file_or_url>"${NORMAL}

# Exit
exit 0
