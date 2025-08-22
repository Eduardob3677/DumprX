#!/bin/bash

# DumprX Workflow Validation Script
# This script validates that all components needed for the GitHub Actions workflow are working

echo "🔍 Validating DumprX Workflow Components..."
echo "============================================"

# Check if workflow file exists and is valid YAML
echo "1. Checking workflow file..."
if [[ -f ".github/workflows/firmware-dump.yml" ]]; then
    echo "✅ Workflow file exists"
    if python3 -c "import yaml; yaml.safe_load(open('.github/workflows/firmware-dump.yml'))" 2>/dev/null; then
        echo "✅ Workflow YAML syntax is valid"
    else
        echo "❌ Workflow YAML syntax is invalid"
        exit 1
    fi
else
    echo "❌ Workflow file not found"
    exit 1
fi

# Check setup script
echo "2. Checking setup script..."
if [[ -f "setup.sh" && -x "setup.sh" ]]; then
    echo "✅ Setup script exists and is executable"
else
    echo "❌ Setup script not found or not executable"
    exit 1
fi

# Check main script
echo "3. Checking main script..."
if [[ -f "dumprx.py" && -x "dumprx.py" ]]; then
    echo "✅ Main Python script exists and is executable"
else
    echo "❌ Main Python script not found or not executable"
    exit 1
fi

# Check Python dependencies
echo "4. Checking Python dependencies..."
if [[ -f "requirements.txt" ]]; then
    echo "✅ Requirements file exists"
    if python3 -c "import aiohttp, aiofiles, yaml" 2>/dev/null; then
        echo "✅ Required Python packages are available"
    else
        echo "❌ Required Python packages not installed"
        exit 1
    fi
else
    echo "❌ Requirements file not found"
    exit 1
fi

# Check modular structure
echo "5. Checking modular structure..."
if [[ -d "lib" && -f "lib/__init__.py" && -f "lib/config.py" && -f "lib/extractors.py" ]]; then
    echo "✅ Modular Python structure exists"
else
    echo "❌ Modular Python structure not found"
    exit 1
fi

# Check Git LFS availability
echo "6. Checking Git LFS..."
if command -v git-lfs >/dev/null 2>&1; then
    echo "✅ Git LFS is available"
else
    echo "❌ Git LFS not found"
    exit 1
fi

# Test token file logic
echo "7. Testing token file logic..."
echo "test_token" > .test_token
if [[ -s .test_token ]]; then
    echo "✅ Token file creation and reading works"
    rm -f .test_token
else
    echo "❌ Token file logic failed"
    exit 1
fi

# Check .gitignore
echo "8. Checking .gitignore..."
if grep -q "github_token\|gitlab_token" .gitignore; then
    echo "✅ Sensitive files are in .gitignore"
else
    echo "❌ Token files not properly ignored"
    exit 1
fi

# Check documentation
echo "9. Checking documentation..."
if grep -q "GitHub Actions Workflow Usage" README.md; then
    echo "✅ Workflow documentation exists in README"
else
    echo "❌ Workflow documentation missing"
    exit 1
fi

if [[ -f "WORKFLOW_EXAMPLES.md" ]]; then
    echo "✅ Workflow examples file exists"
else
    echo "❌ Workflow examples file missing"
    exit 1
fi

echo "============================================"
echo "🎉 All validation checks passed!"
echo ""
echo "Your DumprX repository is ready for the GitHub Actions workflow!"
echo ""
echo "To use the workflow:"
echo "1. Go to the Actions tab in your GitHub repository"
echo "2. Select 'Firmware Dump Workflow'"
echo "3. Click 'Run workflow'"
echo "4. Fill in the required parameters"
echo "5. Click 'Run workflow' to start the process"