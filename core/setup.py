import os
import subprocess
import shutil
from pathlib import Path


class DependencyManager:
    def __init__(self):
        self.utils_dir = Path("bin")
        self.external_tools = [
            "bkerler/oppo_ozip_decrypt",
            "bkerler/oppo_decrypt", 
            "marin-m/vmlinux-to-elf",
            "ShivamKumarJha/android_tools",
            "HemanthJabalpuri/pacextractor"
        ]
    
    def setup_all(self):
        self._setup_external_tools()
        self._setup_python_dependencies()
    
    def _setup_external_tools(self):
        for tool_slug in self.external_tools:
            tool_name = tool_slug.split('/')[-1]
            tool_dir = self.utils_dir / tool_name
            
            if not tool_dir.exists():
                cmd = ['git', 'clone', '-q', f'https://github.com/{tool_slug}.git', str(tool_dir)]
                subprocess.run(cmd, check=True)
            else:
                cmd = ['git', '-C', str(tool_dir), 'pull']
                subprocess.run(cmd, check=False)
    
    def _setup_python_dependencies(self):
        requirements = [
            "click>=8.0.0",
            "rich>=10.0.0", 
            "pyyaml>=6.0",
            "requests>=2.25.0",
            "gitpython>=3.1.0"
        ]
        
        for req in requirements:
            cmd = ['pip', 'install', req]
            subprocess.run(cmd, check=True)


class TestRunner:
    def run_all(self) -> dict:
        results = {
            'success': True,
            'failures': []
        }
        
        tests = [
            self._test_config,
            self._test_extractors,
            self._test_downloaders
        ]
        
        for test in tests:
            try:
                test()
            except Exception as e:
                results['success'] = False
                results['failures'].append(str(e))
        
        return results
    
    def _test_config(self):
        from core.config import Config
        config = Config()
        assert config is not None
    
    def _test_extractors(self):
        from extractors.manager import ExtractorManager
        manager = ExtractorManager(Path("out"), Path("utils"))
        assert manager is not None
    
    def _test_downloaders(self):
        from downloaders.manager import DownloadManager
        manager = DownloadManager("input")
        assert manager is not None