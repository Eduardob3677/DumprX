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

# Check dumper CLI
echo "3. Checking dumper CLI..."
if [[ -f "cli.py" ]]; then
    echo "✅ Python CLI exists"
    if python3 cli.py --help >/dev/null 2>&1; then
        echo "✅ Python CLI is functional"
    else
        echo "❌ Python CLI not working"
        exit 1
    fi
else
    echo "❌ Python CLI not found"
    exit 1
fi

# Check Git LFS availability
echo "4. Checking Git LFS..."
if command -v git-lfs >/dev/null 2>&1; then
    echo "✅ Git LFS is available"
else
    echo "❌ Git LFS not found"
    exit 1
fi

# Test CLI functionality
echo "5. Testing CLI functionality..."
if python3 cli.py config show >/dev/null 2>&1; then
    echo "✅ CLI configuration system works"
else
    echo "❌ CLI configuration failed"
    exit 1
fi

if python3 cli.py test >/dev/null 2>&1; then
    echo "✅ CLI integration tests pass"
else
    echo "❌ CLI integration tests failed"
    exit 1
fi

# Check dependencies
echo "6. Checking Python dependencies..."
if python3 -c "import click, rich, yaml, requests" 2>/dev/null; then
    echo "✅ Python dependencies are installed"
else
    echo "❌ Python dependencies missing"
    exit 1
fi

# Check .gitignore  
echo "7. Checking .gitignore..."
if grep -q "config.yml\\|__pycache__" .gitignore; then
    echo "✅ Sensitive files are in .gitignore"
else
    echo "❌ Sensitive files not properly ignored"
    exit 1
fi

# Check documentation
echo "8. Checking documentation..."
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