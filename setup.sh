#!/bin/bash

tput reset 2>/dev/null || clear

RED='\033[0;31m'
GREEN='\033[0;32m'
PURPLE='\033[0;35m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NORMAL='\033[0m'

function abort(){
    [ ! -z "$@" ] && echo -e ${RED}"${@}"${NORMAL}
    exit 1
}

function __bannerTop() {
    echo -e \
    ${GREEN}"
    ██████╗░██╗░░░██╗███╗░░░███╗██████╗░██████╗░██╗░░██╗
    ██╔══██╗██║░░░██║████╗░████║██╔══██╗██╔══██╗╚██╗██╔╝
    ██║░░██║██║░░░██║██╔████╔██║██████╔╝██████╔╝░╚███╔╝░
    ██║░░██║██║░░░██║██║╚██╔╝██║██╔═══╝░██╔══██╗░██╔██╗░
    ██████╔╝╚██████╔╝██║░╚═╝░██║██║░░░░░██║░░██║██╔╝╚██╗
    ╚═════╝░░╚═════╝░╚═╝░░░░░╚═╝╚═╝░░░░░╚═╝░░╚═╝╚═╝░░╚═╝
    
    Modern Python Firmware Dumping Toolkit - Setup v2.0
    "${NORMAL}
}

echo -e ${GREEN} && __bannerTop && echo -e ${NORMAL}

echo -e ${BLUE}"🚀 Setting up DumprX Python environment..."${NORMAL}
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
        sudo apt install -y unace unrar zip unzip p7zip-full p7zip-rar sharutils rar uudeview mpack arj cabextract device-tree-compiler liblzma-dev python3-pip python3-venv brotli liblz4-tool axel gawk aria2 detox cpio rename liblz4-dev jq git-lfs || abort "Setup Failed!"

    elif command -v dnf > /dev/null 2>&1; then

        echo -e ${PURPLE}"Fedora Based Distro Detected"${NORMAL}
        sleep 1
        echo -e ${BLUE}">> Installing Required Packages..."${NORMAL}
        sleep 1

        sudo dnf install -y unace unrar zip unzip sharutils uudeview arj cabextract file-roller dtc python3-pip python3-venv brotli axel aria2 detox cpio lz4 python3-devel xz-devel p7zip p7zip-plugins git-lfs || abort "Setup Failed!"

    elif command -v pacman > /dev/null 2>&1; then

        echo -e ${PURPLE}"Arch or Arch Based Distro Detected"${NORMAL}
        sleep 1
        echo -e ${BLUE}">> Installing Required Packages..."${NORMAL}
        sleep 1

        sudo pacman -Syyu --needed --noconfirm >/dev/null || abort "Setup Failed!"
        sudo pacman -Sy --noconfirm unace unrar p7zip sharutils uudeview arj cabextract file-roller dtc brotli axel gawk aria2 detox cpio lz4 jq git-lfs python python-pip || abort "Setup Failed!"

    fi

elif [[ "$OSTYPE" == "darwin"* ]]; then

    echo -e ${PURPLE}"macOS Detected"${NORMAL}
    sleep 1
    echo -e ${BLUE}">> Installing Required Packages..."${NORMAL}
    sleep 1
    brew install protobuf xz brotli lz4 aria2 detox coreutils p7zip gawk git-lfs python@3.11 || abort "Setup Failed!"

fi

sleep 1

echo -e ${BLUE}">> Creating Python virtual environment..."${NORMAL}
sleep 1
python3 -m venv .venv || abort "Failed to create virtual environment!"

echo -e ${BLUE}">> Activating virtual environment..."${NORMAL}
source .venv/bin/activate || abort "Failed to activate virtual environment!"

echo -e ${BLUE}">> Upgrading pip..."${NORMAL}
python -m pip install --upgrade pip || abort "Failed to upgrade pip!"

echo -e ${BLUE}">> Installing Python dependencies..."${NORMAL}
sleep 1
pip install click rich requests pathlib2 || abort "Python package installation failed!"

echo -e ${BLUE}">> Installing DumprX package..."${NORMAL}
sleep 1
pip install -e . || abort "DumprX package installation failed!"

echo -e ${BLUE}">> Setting up Git LFS..."${NORMAL}
sleep 1
git lfs install || abort "Git LFS setup failed!"

echo -e ${GREEN}"✅ Setup Complete!"${NORMAL}
echo -e ${YELLOW}"🎉 DumprX is now ready to use!"${NORMAL}
echo ""
echo -e ${BLUE}"To use DumprX:"${NORMAL}
echo -e ${GREEN}"  1. Activate the virtual environment: source .venv/bin/activate"${NORMAL}
echo -e ${GREEN}"  2. Run: dumprx <firmware_file_or_url>"${NORMAL}
echo ""
echo -e ${BLUE}"Example:"${NORMAL}
echo -e ${GREEN}"  dumprx firmware.zip"${NORMAL}
echo -e ${GREEN}"  dumprx 'https://example.com/firmware.zip'"${NORMAL}

exit 0