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

echo -e ${BLUE}">> Setting up DumprX v2.0 - Modern Python Edition <<"${NORMAL}
sleep 1

# Detect OS and install system dependencies
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
        sudo apt install -y unace unrar zip unzip p7zip-full p7zip-rar sharutils rar uudeview mpack arj cabextract device-tree-compiler liblzma-dev python3-pip python3-dev brotli liblz4-tool axel gawk aria2 detox cpio rename liblz4-dev jq git-lfs python3-venv || abort "Setup Failed!"

    elif command -v dnf > /dev/null 2>&1; then

        echo -e ${PURPLE}"Fedora Based Distro Detected"${NORMAL}
        sleep 1
	    echo -e ${BLUE}">> Installing Required Packages..."${NORMAL}
	    sleep 1

	    # "dnf" automatically updates repos before installing packages
        sudo dnf install -y unace unrar zip unzip sharutils uudeview arj cabextract file-roller dtc python3-pip python3-devel brotli axel aria2 detox cpio lz4 python3-devel xz-devel p7zip p7zip-plugins git-lfs || abort "Setup Failed!"

    elif command -v pacman > /dev/null 2>&1; then

        echo -e ${PURPLE}"Arch or Arch Based Distro Detected"${NORMAL}
        sleep 1
	    echo -e ${BLUE}">> Installing Required Packages..."${NORMAL}
	    sleep 1

        sudo pacman -Syyu --needed --noconfirm >/dev/null || abort "Setup Failed!"
        sudo pacman -Sy --noconfirm unace unrar p7zip sharutils uudeview arj cabextract file-roller dtc brotli axel gawk aria2 detox cpio lz4 jq git-lfs python python-pip || abort "Setup Failed!"

    elif command -v apk > /dev/null 2>&1; then

        echo -e ${PURPLE}"Alpine Linux Detected"${NORMAL}
        sleep 1
	    echo -e ${BLUE}">> Installing Required Packages..."${NORMAL}
	    sleep 1

        sudo apk update || abort "Setup Failed!"
        sudo apk add --no-cache unrar zip unzip p7zip sharutils arj brotli xz lz4 gawk aria2 cpio dtc python3 python3-dev py3-pip git-lfs build-base || abort "Setup Failed!"

    else
        echo -e ${RED}"Unsupported Linux distribution. Please install dependencies manually."${NORMAL}
        abort "Setup Failed!"
    fi

elif [[ "$OSTYPE" == "darwin"* ]]; then

    echo -e ${PURPLE}"macOS Detected"${NORMAL}
    sleep 1
	echo -e ${BLUE}">> Installing Required Packages..."${NORMAL}
	sleep 1
    
    # Check if Homebrew is installed
    if ! command -v brew > /dev/null 2>&1; then
        echo -e ${BLUE}">> Installing Homebrew..."${NORMAL}
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)" || abort "Homebrew installation failed!"
    fi
    
    brew install protobuf xz brotli lz4 aria2 detox coreutils p7zip gawk git-lfs python3 || abort "Setup Failed!"

else
    echo -e ${RED}"Unsupported operating system: $OSTYPE"${NORMAL}
    abort "Setup Failed!"
fi

sleep 1

# Install Python package in development mode
echo -e ${BLUE}">> Installing DumprX Python package..."${NORMAL}
sleep 1

# Check if we're in a virtual environment, if not create one
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo -e ${BLUE}">> Creating Python virtual environment..."${NORMAL}
    python3 -m venv venv || abort "Failed to create virtual environment!"
    source venv/bin/activate || abort "Failed to activate virtual environment!"
fi

# Upgrade pip
python -m pip install --upgrade pip || abort "Failed to upgrade pip!"

# Install package in development mode
python -m pip install -e . || abort "Failed to install DumprX package!"

# Install optional cryptography for Mega downloads
python -m pip install cryptography || echo -e ${YELLOW}"Warning: Cryptography not installed, Mega downloads will not work"${NORMAL}

sleep 1

# Make dumprx command available globally by creating a symlink or adding to PATH
echo -e ${BLUE}">> Setting up dumprx command..."${NORMAL}

# Add to bash profile if not already there
if [[ -f ~/.bashrc ]] && ! grep -q "dumprx" ~/.bashrc; then
    echo 'export PATH="$(pwd)/venv/bin:$PATH"' >> ~/.bashrc
    echo -e ${GREEN}"Added dumprx to ~/.bashrc"${NORMAL}
fi

if [[ -f ~/.zshrc ]] && ! grep -q "dumprx" ~/.zshrc; then
    echo 'export PATH="$(pwd)/venv/bin:$PATH"' >> ~/.zshrc
    echo -e ${GREEN}"Added dumprx to ~/.zshrc"${NORMAL}
fi

sleep 1

# Test installation
echo -e ${BLUE}">> Testing installation..."${NORMAL}
if command -v dumprx > /dev/null 2>&1; then
    echo -e ${GREEN}"✓ DumprX installed successfully!"${NORMAL}
    dumprx version
else
    echo -e ${YELLOW}"Warning: dumprx command not found in PATH. You may need to:"${NORMAL}
    echo -e ${YELLOW}"  - Restart your terminal or run: source ~/.bashrc"${NORMAL}
    echo -e ${YELLOW}"  - Or use: python -m dumprx.cli"${NORMAL}
fi

sleep 1

# Done!
echo -e ${GREEN}"Setup Complete!"${NORMAL}
echo -e ${GREEN}"You can now use: dumprx <firmware_file_or_url>"${NORMAL}

# Exit
exit 0