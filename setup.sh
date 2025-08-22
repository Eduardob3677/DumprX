#!/bin/bash

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
UTILS_DIR="${PROJECT_DIR}/utils"
BIN_DIR="${UTILS_DIR}/bin"

echo "🔧 Setting up DumprX v2.0"
echo "Project directory: ${PROJECT_DIR}"

install_system_packages() {
    echo "📦 Installing system packages..."
    
    if command -v apt-get >/dev/null 2>&1; then
        sudo apt-get update
        sudo apt-get install -y \
            python3 \
            python3-pip \
            python3-venv \
            git \
            curl \
            wget \
            aria2 \
            p7zip-full \
            unzip \
            tar \
            xz-utils \
            lz4 \
            brotli \
            lzop \
            cpio \
            file \
            xxd \
            build-essential \
            cmake \
            golang-go \
            default-jdk \
            device-tree-compiler
    elif command -v yum >/dev/null 2>&1; then
        sudo yum install -y \
            python3 \
            python3-pip \
            git \
            curl \
            wget \
            aria2 \
            p7zip \
            unzip \
            tar \
            xz \
            lz4 \
            brotli \
            lzop \
            cpio \
            file \
            xxd \
            gcc \
            gcc-c++ \
            make \
            cmake \
            golang \
            java-11-openjdk-devel \
            dtc
    elif command -v pacman >/dev/null 2>&1; then
        sudo pacman -S --noconfirm \
            python \
            python-pip \
            git \
            curl \
            wget \
            aria2 \
            p7zip \
            unzip \
            tar \
            xz \
            lz4 \
            brotli \
            lzop \
            cpio \
            file \
            xxd \
            base-devel \
            cmake \
            go \
            jdk11-openjdk \
            dtc
    elif command -v brew >/dev/null 2>&1; then
        brew install \
            python3 \
            git \
            curl \
            wget \
            aria2 \
            p7zip \
            unzip \
            tar \
            xz \
            lz4 \
            brotli \
            lzop \
            cpio \
            file \
            xxd \
            cmake \
            go \
            openjdk \
            dtc
    else
        echo "❌ Unsupported package manager. Please install dependencies manually."
        exit 1
    fi
}

install_python_deps() {
    echo "🐍 Installing Python dependencies..."
    
    if command -v python3 >/dev/null 2>&1; then
        python3 -m pip install --upgrade pip
        python3 -m pip install -r "${PROJECT_DIR}/requirements.txt"
    else
        echo "❌ Python 3 not found. Please install Python 3."
        exit 1
    fi
}

create_directories() {
    echo "📁 Creating directories..."
    mkdir -p "${BIN_DIR}"
    mkdir -p "${PROJECT_DIR}/input"
    mkdir -p "${PROJECT_DIR}/out"
    mkdir -p "${PROJECT_DIR}/out/tmp"
}

setup_tools() {
    echo "🛠️ Setting up extraction tools..."
    
    cd "${UTILS_DIR}"
    
    if [[ ! -f "${BIN_DIR}/7zz" ]]; then
        echo "Installing 7zip..."
        if [[ "$(uname -m)" == "x86_64" ]]; then
            curl -L "https://www.7-zip.org/a/7z2301-linux-x64.tar.xz" | tar -xJ -C "${BIN_DIR}" 7zz
        elif [[ "$(uname -m)" == "aarch64" ]]; then
            curl -L "https://www.7-zip.org/a/7z2301-linux-arm64.tar.xz" | tar -xJ -C "${BIN_DIR}" 7zz
        fi
        chmod +x "${BIN_DIR}/7zz" 2>/dev/null || true
    fi
    
    if [[ ! -f "${BIN_DIR}/payload-dumper-go" ]]; then
        echo "Installing payload-dumper-go..."
        if [[ "$(uname -m)" == "x86_64" ]]; then
            curl -L "https://github.com/ssut/payload-dumper-go/releases/latest/download/payload-dumper-go_linux_amd64.tar.gz" | tar -xz -C "${BIN_DIR}"
        elif [[ "$(uname -m)" == "aarch64" ]]; then
            curl -L "https://github.com/ssut/payload-dumper-go/releases/latest/download/payload-dumper-go_linux_arm64.tar.gz" | tar -xz -C "${BIN_DIR}"
        fi
        chmod +x "${BIN_DIR}/payload-dumper-go" 2>/dev/null || true
    fi
    
    if [[ ! -f "${BIN_DIR}/simg2img" ]]; then
        echo "Installing simg2img..."
        if [[ ! -d android_tools ]]; then
            git clone https://github.com/ShivamKumarJha/android_tools.git
        fi
        cd android_tools
        if [[ -f Makefile ]]; then
            make simg2img
            cp simg2img "${BIN_DIR}/"
        fi
        cd ..
    fi
    
    clone_external_repos
}

clone_external_repos() {
    echo "📥 Cloning external repositories..."
    
    declare -a repos=(
        "bkerler/oppo_ozip_decrypt"
        "bkerler/oppo_decrypt"
        "marin-m/vmlinux-to-elf"
        "ShivamKumarJha/android_tools"
        "HemanthJabalpuri/pacextractor"
    )
    
    for repo in "${repos[@]}"; do
        repo_name="${repo##*/}"
        if [[ ! -d "${repo_name}" ]]; then
            echo "Cloning ${repo}..."
            git clone "https://github.com/${repo}.git" "${repo_name}" --depth=1 || true
        fi
    done
    
    if [[ -d "vmlinux-to-elf" && ! -f "${BIN_DIR}/vmlinux-to-elf" ]]; then
        echo "Building vmlinux-to-elf..."
        cd vmlinux-to-elf
        make
        cp vmlinux-to-elf "${BIN_DIR}/"
        cp kallsyms-finder "${BIN_DIR}/"
        cd ..
    fi
}

set_permissions() {
    echo "🔐 Setting permissions..."
    
    find "${BIN_DIR}" -type f -exec chmod +x {} \; 2>/dev/null || true
    find "${UTILS_DIR}" -name "*.py" -exec chmod +x {} \; 2>/dev/null || true
    find "${UTILS_DIR}" -name "*.sh" -exec chmod +x {} \; 2>/dev/null || true
    
    chmod +x "${PROJECT_DIR}/dumprx_main.py" 2>/dev/null || true
    chmod +x "${UTILS_DIR}/unpackboot.py" 2>/dev/null || true
}

validate_setup() {
    echo "✅ Validating setup..."
    
    local python_ok=false
    local tools_ok=true
    
    if command -v python3 >/dev/null 2>&1; then
        if python3 -c "import yaml, aiohttp, aiofiles" 2>/dev/null; then
            python_ok=true
        fi
    fi
    
    if [[ ! -f "${BIN_DIR}/7zz" ]]; then
        tools_ok=false
        echo "⚠️ 7zip not found"
    fi
    
    if $python_ok && $tools_ok; then
        echo "🎉 Setup completed successfully!"
        echo ""
        echo "Usage:"
        echo "  python3 dumprx_main.py <firmware_file_or_url>"
        echo ""
        echo "Examples:"
        echo "  python3 dumprx_main.py firmware.zip"
        echo "  python3 dumprx_main.py 'https://example.com/firmware.zip'"
        return 0
    else
        echo "❌ Setup validation failed"
        return 1
    fi
}

main() {
    cd "${PROJECT_DIR}"
    
    install_system_packages
    install_python_deps
    create_directories
    setup_tools
    set_permissions
    validate_setup
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi