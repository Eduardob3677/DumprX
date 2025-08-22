import subprocess
from pathlib import Path
from rich.console import Console

console = Console()

class DeviceTreeGenerator:
    def __init__(self, config):
        self.config = config
    
    def generate_trees(self, output_dir):
        output_path = Path(output_dir)
        
        if self.config.get('device.treble_support', True):
            self._generate_aosp_tree(output_path)
        
        self._generate_twrp_tree(output_path)
    
    def _generate_aosp_tree(self, output_path):
        console.print("[blue]Generating AOSP device tree...[/blue]")
        
        aosp_dir = output_path / "aosp-device-tree"
        aosp_dir.mkdir(exist_ok=True)
        
        try:
            cmd = f'uvx -p 3.9 aospdtgen "{output_path}" -o "{aosp_dir}"'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                console.print("[green]✅ AOSP device tree generated[/green]")
                
                for git_dir in aosp_dir.rglob('.git'):
                    if git_dir.is_dir():
                        import shutil
                        shutil.rmtree(git_dir)
            else:
                console.print(f"[yellow]AOSP device tree generation failed: {result.stderr}[/yellow]")
                
        except Exception as e:
            console.print(f"[yellow]AOSP device tree generation failed: {e}[/yellow]")
    
    def _generate_twrp_tree(self, output_path):
        console.print("[blue]Generating TWRP device tree...[/blue]")
        
        twrp_dir = output_path / "twrp-device-tree"
        twrp_dir.mkdir(exist_ok=True)
        
        is_ab = self.config.get('device.is_ab', False)
        
        if is_ab:
            recovery_img = output_path / "recovery.img"
            if recovery_img.exists():
                console.print("Legacy A/B with recovery partition detected...")
                twrp_img = recovery_img
            else:
                twrp_img = output_path / "boot.img"
        else:
            twrp_img = output_path / "recovery.img"
        
        if twrp_img.exists():
            try:
                cmd = f'uvx -p 3.9 --from git+https://github.com/twrpdtgen/twrpdtgen@master twrpdtgen "{twrp_img}" -o "{twrp_dir}"'
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                
                if result.returncode == 0:
                    console.print("[green]✅ TWRP device tree generated[/green]")
                    
                    readme_path = twrp_dir / "README.md"
                    if not readme_path.exists():
                        try:
                            import requests
                            readme_url = "https://raw.githubusercontent.com/wiki/SebaUbuntu/TWRP-device-tree-generator/4.-Build-TWRP-from-source.md"
                            response = requests.get(readme_url)
                            if response.status_code == 200:
                                with open(readme_path, 'w') as f:
                                    f.write(response.text)
                        except:
                            pass
                    
                    for git_dir in twrp_dir.rglob('.git'):
                        if git_dir.is_dir():
                            import shutil
                            shutil.rmtree(git_dir)
                else:
                    console.print(f"[yellow]TWRP device tree generation failed: {result.stderr}[/yellow]")
                    
            except Exception as e:
                console.print(f"[yellow]TWRP device tree generation failed: {e}[/yellow]")
        else:
            console.print(f"[yellow]Recovery/boot image not found for TWRP tree generation[/yellow]")