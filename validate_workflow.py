#!/usr/bin/env python3

import os
import sys
import yaml
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

def validate_workflow_components():
    console.print(Panel("🔍 Validating DumprX Workflow Components", style="bold blue"))
    
    checks = []
    
    # Check workflow file
    console.print("[blue]1. Checking workflow file...[/blue]")
    workflow_file = Path(".github/workflows/firmware-dump.yml")
    if workflow_file.exists():
        console.print("✅ Workflow file exists")
        try:
            with open(workflow_file, 'r') as f:
                yaml.safe_load(f)
            console.print("✅ Workflow YAML syntax is valid")
            checks.append(("Workflow file", "✅ Valid"))
        except yaml.YAMLError:
            console.print("❌ Workflow YAML syntax is invalid")
            checks.append(("Workflow file", "❌ Invalid YAML"))
    else:
        console.print("❌ Workflow file not found")
        checks.append(("Workflow file", "❌ Not found"))
    
    # Check setup script
    console.print("[blue]2. Checking setup script...[/blue]")
    new_setup = Path("setup_new.sh")
    old_setup = Path("setup.sh")
    
    if new_setup.exists() and new_setup.stat().st_mode & 0o111:
        console.print("✅ New setup script exists and is executable")
        checks.append(("Setup script", "✅ New script ready"))
    elif old_setup.exists() and old_setup.stat().st_mode & 0o111:
        console.print("✅ Original setup script exists and is executable")
        checks.append(("Setup script", "✅ Original script"))
    else:
        console.print("❌ No executable setup script found")
        checks.append(("Setup script", "❌ Not found"))
    
    # Check DumprX Python package
    console.print("[blue]3. Checking DumprX Python package...[/blue]")
    dumprx_init = Path("dumprx/__init__.py")
    setup_py = Path("setup.py")
    requirements = Path("requirements.txt")
    
    if dumprx_init.exists() and setup_py.exists() and requirements.exists():
        console.print("✅ DumprX Python package structure exists")
        checks.append(("Python package", "✅ Complete"))
    else:
        console.print("❌ DumprX Python package incomplete")
        checks.append(("Python package", "❌ Incomplete"))
    
    # Check CLI availability
    console.print("[blue]4. Checking CLI interface...[/blue]")
    cli_main = Path("dumprx/cli/main.py")
    if cli_main.exists():
        console.print("✅ CLI interface exists")
        checks.append(("CLI interface", "✅ Available"))
    else:
        console.print("❌ CLI interface not found")
        checks.append(("CLI interface", "❌ Missing"))
    
    # Check Git LFS availability
    console.print("[blue]5. Checking Git LFS...[/blue]")
    if os.system("command -v git-lfs >/dev/null 2>&1") == 0:
        console.print("✅ Git LFS is available")
        checks.append(("Git LFS", "✅ Available"))
    else:
        console.print("❌ Git LFS not found")
        checks.append(("Git LFS", "❌ Not found"))
    
    # Test token file logic
    console.print("[blue]6. Testing token file logic...[/blue]")
    test_token_file = Path(".test_token")
    try:
        test_token_file.write_text("test_token")
        if test_token_file.exists() and test_token_file.read_text().strip():
            console.print("✅ Token file creation and reading works")
            checks.append(("Token files", "✅ Working"))
        else:
            console.print("❌ Token file logic failed")
            checks.append(("Token files", "❌ Failed"))
        test_token_file.unlink(missing_ok=True)
    except Exception:
        console.print("❌ Token file logic failed")
        checks.append(("Token files", "❌ Failed"))
    
    # Check .gitignore
    console.print("[blue]7. Checking .gitignore...[/blue]")
    gitignore = Path(".gitignore")
    if gitignore.exists():
        content = gitignore.read_text()
        if "github_token" in content or "gitlab_token" in content:
            console.print("✅ Sensitive files are in .gitignore")
            checks.append((".gitignore", "✅ Configured"))
        else:
            console.print("❌ Token files not properly ignored")
            checks.append((".gitignore", "❌ Missing tokens"))
    else:
        console.print("❌ .gitignore not found")
        checks.append((".gitignore", "❌ Not found"))
    
    # Check documentation
    console.print("[blue]8. Checking documentation...[/blue]")
    readme = Path("README.md")
    workflow_examples = Path("WORKFLOW_EXAMPLES.md")
    
    docs_status = []
    if readme.exists():
        readme_content = readme.read_text()
        if "GitHub Actions Workflow Usage" in readme_content:
            docs_status.append("README workflow docs")
        docs_status.append("README exists")
    
    if workflow_examples.exists():
        docs_status.append("Workflow examples exist")
    
    if docs_status:
        console.print(f"✅ Documentation: {', '.join(docs_status)}")
        checks.append(("Documentation", "✅ Available"))
    else:
        console.print("❌ Documentation missing")
        checks.append(("Documentation", "❌ Missing"))
    
    # Summary table
    console.print()
    table = Table(title="🔍 Validation Summary")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="bold")
    
    for component, status in checks:
        table.add_row(component, status)
    
    console.print(table)
    
    # Final result
    failed_checks = [check for check in checks if "❌" in check[1]]
    
    if not failed_checks:
        console.print()
        console.print(Panel(
            "[green]🎉 All validation checks passed![/green]\n\n"
            "[blue]Your DumprX repository is ready for the GitHub Actions workflow![/blue]\n\n"
            "[yellow]To use the workflow:[/yellow]\n"
            "1. Go to the Actions tab in your GitHub repository\n"
            "2. Select 'Firmware Dump Workflow'\n"
            "3. Click 'Run workflow'\n"
            "4. Enter the firmware URL and run",
            title="✅ Validation Complete"
        ))
        return True
    else:
        console.print()
        console.print(Panel(
            f"[red]❌ {len(failed_checks)} validation check(s) failed![/red]\n\n"
            "[yellow]Please fix the issues above before using the workflow[/yellow]",
            title="⚠️  Validation Failed"
        ))
        return False

if __name__ == "__main__":
    try:
        success = validate_workflow_components()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️  Validation cancelled by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]💥 Validation error: {str(e)}[/red]")
        sys.exit(1)