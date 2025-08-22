import os
import shutil
import subprocess
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from urllib.parse import urlparse

from downloaders.manager import DownloadManager
from extractors.manager import ExtractorManager
from utils.git import GitManager
from utils.device import DeviceTreeGenerator
from modules.file_utils import FileUtils

console = Console()

class FirmwareDumper:
    def __init__(self, config, output_dir="out"):
        self.config = config
        self.output_dir = Path(output_dir)
        self.input_dir = Path(config.input_dir)
        self.tmp_dir = Path(config.tmp_dir)
        
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.input_dir.mkdir(parents=True, exist_ok=True)
        
        if self.tmp_dir.exists():
            shutil.rmtree(self.tmp_dir)
        self.tmp_dir.mkdir(parents=True, exist_ok=True)
        
        self.download_manager = DownloadManager(str(self.input_dir))
        self.extractor_manager = ExtractorManager(config)
        self.git_manager = GitManager(config)
        self.device_tree_generator = DeviceTreeGenerator(config)
        self.file_utils = FileUtils()
        
        self._setup_external_tools()
    
    def _setup_external_tools(self):
        console.print("[blue]Setting up external tools...[/blue]")
        
        external_tools = self.config.get_external_tools()
        utils_dir = Path(self.config.project_dir) / "utils"
        
        for tool_slug in external_tools:
            tool_name = tool_slug.split('/')[-1]
            tool_dir = utils_dir / tool_name
            
            if not tool_dir.exists():
                console.print(f"Cloning {tool_slug}...")
                cmd = f"git clone -q https://github.com/{tool_slug}.git {tool_dir}"
                subprocess.run(cmd, shell=True, check=True)
            else:
                console.print(f"Updating {tool_name}...")
                subprocess.run("git pull", shell=True, cwd=tool_dir, check=False)
    
    def process_firmware(self, firmware_input):
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TimeElapsedColumn(),
            console=console
        ) as progress:
            
            main_task = progress.add_task("Processing firmware...", total=7)
            
            progress.update(main_task, description="Step 1/7: Analyzing input...")
            filepath = self._handle_input(firmware_input)
            progress.advance(main_task)
            
            progress.update(main_task, description="Step 2/7: Extracting firmware...")
            extracted_files = self._extract_firmware(filepath)
            progress.advance(main_task)
            
            progress.update(main_task, description="Step 3/7: Processing images...")
            processed_files = self._process_images(extracted_files)
            progress.advance(main_task)
            
            progress.update(main_task, description="Step 4/7: Generating device trees...")
            self._generate_device_trees()
            progress.advance(main_task)
            
            progress.update(main_task, description="Step 5/7: Creating checksums...")
            self._create_checksums()
            progress.advance(main_task)
            
            progress.update(main_task, description="Step 6/7: Organizing output...")
            self._organize_output()
            progress.advance(main_task)
            
            progress.update(main_task, description="Step 7/7: Finalizing...")
            self._finalize_dump()
            progress.advance(main_task)
    
    def _handle_input(self, firmware_input):
        if self._is_url(firmware_input):
            console.print(f"[blue]Downloading from URL: {firmware_input}[/blue]")
            downloaded_files = self.download_manager.download(firmware_input)
            
            if len(downloaded_files) == 1 and os.path.isfile(self.input_dir / downloaded_files[0]):
                return self.input_dir / downloaded_files[0]
            else:
                return self.input_dir
        
        elif os.path.isdir(firmware_input):
            if str(firmware_input).startswith(str(self.input_dir)):
                return Path(firmware_input)
            else:
                console.print(f"Copying directory to input: {firmware_input}")
                shutil.copytree(firmware_input, self.tmp_dir / "copied", dirs_exist_ok=True)
                return self.tmp_dir / "copied"
        
        elif os.path.isfile(firmware_input):
            if str(firmware_input).startswith(str(self.input_dir)):
                return Path(firmware_input)
            else:
                console.print(f"Copying file to input: {firmware_input}")
                dest_file = self.input_dir / Path(firmware_input).name
                shutil.copy2(firmware_input, dest_file)
                return dest_file
        
        else:
            raise Exception(f"Input not found: {firmware_input}")
    
    def _is_url(self, text):
        try:
            result = urlparse(text)
            return all([result.scheme, result.netloc])
        except:
            return False
    
    def _extract_firmware(self, filepath):
        if os.path.isdir(filepath):
            return [filepath]
        
        extraction_dir = self.tmp_dir / "extracted"
        extraction_dir.mkdir(exist_ok=True)
        
        try:
            extracted = self.extractor_manager.extract(str(filepath), str(extraction_dir))
            return extracted
        except Exception as e:
            console.print(f"[yellow]Warning: Extraction failed: {e}[/yellow]")
            console.print("[blue]Treating as raw firmware file[/blue]")
            shutil.copy2(filepath, extraction_dir / Path(filepath).name)
            return [str(extraction_dir)]
    
    def _process_images(self, extracted_files):
        processed = []
        
        for file_path in extracted_files:
            if os.path.isdir(file_path):
                for root, dirs, files in os.walk(file_path):
                    for file in files:
                        full_path = os.path.join(root, file)
                        processed.extend(self._process_single_file(full_path))
            else:
                processed.extend(self._process_single_file(file_path))
        
        return processed
    
    def _process_single_file(self, file_path):
        file_path = Path(file_path)
        
        if file_path.suffix.lower() in ['.img']:
            return self._process_image_file(file_path)
        elif file_path.name.lower().endswith('.new.dat'):
            return self._process_sdat_file(file_path)
        elif 'super' in file_path.name.lower():
            return self._process_super_image(file_path)
        
        return [str(file_path)]
    
    def _process_image_file(self, img_file):
        if self._is_sparse_image(img_file):
            return self._convert_sparse_image(img_file)
        
        return [str(img_file)]
    
    def _is_sparse_image(self, img_file):
        try:
            with open(img_file, 'rb') as f:
                header = f.read(4)
                return header == b'\x3a\xff\x26\xed'
        except:
            return False
    
    def _convert_sparse_image(self, sparse_img):
        output_img = sparse_img.with_suffix('.raw.img')
        
        bin_dir = Path(__file__).parent.parent / "bin"
        simg2img = bin_dir / "simg2img"
        
        cmd = f'"{simg2img}" "{sparse_img}" "{output_img}"'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            console.print(f"Converted sparse image: {sparse_img.name}")
            return [str(output_img)]
        else:
            console.print(f"[yellow]Failed to convert sparse image: {sparse_img.name}[/yellow]")
            return [str(sparse_img)]
    
    def _process_sdat_file(self, sdat_file):
        try:
            from extractors.sdat import SdatExtractor
            extractor = SdatExtractor(self.config)
            return extractor.extract(str(sdat_file), str(self.tmp_dir))
        except Exception as e:
            console.print(f"[yellow]SDAT processing failed: {e}[/yellow]")
            return [str(sdat_file)]
    
    def _process_super_image(self, super_img):
        try:
            bin_dir = Path(__file__).parent.parent / "bin"
            lpunpack = bin_dir / "lpunpack"
            
            super_dir = self.tmp_dir / "super_extracted"
            super_dir.mkdir(exist_ok=True)
            
            cmd = f'"{lpunpack}" "{super_img}" "{super_dir}"'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                console.print(f"Extracted super image: {super_img.name}")
                return [str(super_dir)]
            else:
                console.print(f"[yellow]Super image extraction failed[/yellow]")
                return [str(super_img)]
        except Exception as e:
            console.print(f"[yellow]Super image processing failed: {e}[/yellow]")
            return [str(super_img)]
    
    def _generate_device_trees(self):
        console.print("[blue]Generating device trees...[/blue]")
        self.device_tree_generator.generate_trees(str(self.output_dir))
    
    def _create_checksums(self):
        console.print("[blue]Creating checksums...[/blue]")
        self.file_utils.create_sha1_checksums(str(self.output_dir))
    
    def _organize_output(self):
        console.print("[blue]Organizing output files...[/blue]")
        
        for item in self.tmp_dir.rglob("*"):
            if item.is_file():
                relative_path = item.relative_to(self.tmp_dir)
                dest_path = self.output_dir / relative_path
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                
                if not dest_path.exists():
                    shutil.copy2(item, dest_path)
        
        all_files_list = self.output_dir / "all_files.txt"
        with open(all_files_list, 'w') as f:
            for file_path in sorted(self.output_dir.rglob("*")):
                if file_path.is_file() and ".git/" not in str(file_path):
                    relative_path = file_path.relative_to(self.output_dir)
                    f.write(f"{relative_path}\n")
    
    def _finalize_dump(self):
        console.print("[blue]Finalizing dump...[/blue]")
        
        os.chdir(self.output_dir)
        
        subprocess.run(['chown', f'{os.getuid()}', '.', '-R'], check=False)
        subprocess.run(['chmod', '-R', 'u+rwX', '.'], check=False)
        
        if self.config.get('git.auto_push', False):
            self.git_manager.create_and_push_repo(str(self.output_dir))
        
        if self.tmp_dir.exists():
            shutil.rmtree(self.tmp_dir)
        
        console.print("[bold green]✅ Firmware dump completed successfully![/bold green]")