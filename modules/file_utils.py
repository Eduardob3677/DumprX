import hashlib
import os
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

class FileUtils:
    @staticmethod
    def create_sha1_checksums(output_dir):
        output_path = Path(output_dir)
        
        blob_files = []
        partitions = ['system', 'vendor', 'product', 'odm', 'system_ext']
        
        for partition in partitions:
            partition_dir = output_path / partition
            if partition_dir.exists():
                for root, dirs, files in os.walk(partition_dir):
                    for file in files:
                        if not file.endswith(('.txt', '.xml', '.json')):
                            blob_files.append(os.path.join(root, file))
        
        if not blob_files:
            return
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Creating SHA1 checksums...", total=len(blob_files))
            
            sha1_files = {}
            
            for blob_file in blob_files:
                try:
                    with open(blob_file, 'rb') as f:
                        sha1_hash = hashlib.sha1()
                        for chunk in iter(lambda: f.read(4096), b""):
                            sha1_hash.update(chunk)
                        
                        relative_path = os.path.relpath(blob_file, output_path)
                        sha1_files[relative_path] = sha1_hash.hexdigest()
                        
                except Exception as e:
                    console.print(f"[yellow]Warning: Could not hash {blob_file}: {e}[/yellow]")
                
                progress.advance(task)
            
            if sha1_files:
                for partition in partitions:
                    partition_sha1 = output_path / f"{partition}_sha1sum.txt"
                    partition_files = {k: v for k, v in sha1_files.items() 
                                     if k.startswith(f"{partition}/")}
                    
                    if partition_files:
                        with open(partition_sha1, 'w') as f:
                            for file_path, sha1 in sorted(partition_files.items()):
                                f.write(f"{sha1}  {file_path}\n")
                
                all_sha1 = output_path / "all_files_sha1sum.txt"
                with open(all_sha1, 'w') as f:
                    for file_path, sha1 in sorted(sha1_files.items()):
                        f.write(f"{sha1}  {file_path}\n")
                
                console.print(f"[green]Created SHA1 checksums for {len(sha1_files)} files[/green]")
    
    @staticmethod
    def split_large_files(directory, min_size_mb=100, part_size_mb=50):
        dir_path = Path(directory)
        min_size = min_size_mb * 1024 * 1024
        part_size = part_size_mb * 1024 * 1024
        
        for file_path in dir_path.rglob('*'):
            if file_path.is_file() and file_path.stat().st_size > min_size:
                console.print(f"[blue]Splitting large file: {file_path.name}[/blue]")
                
                with open(file_path, 'rb') as input_file:
                    part_num = 0
                    while True:
                        chunk = input_file.read(part_size)
                        if not chunk:
                            break
                        
                        part_suffix = chr(ord('a') + part_num // 26) + chr(ord('a') + part_num % 26)
                        part_name = f"{file_path}.{part_suffix}"
                        
                        with open(part_name, 'wb') as part_file:
                            part_file.write(chunk)
                        
                        part_num += 1
                
                os.remove(file_path)
                console.print(f"[green]Split into {part_num} parts[/green]")
    
    @staticmethod
    def detox_filename(filename):
        import re
        
        detoxed = re.sub(r'[^\w\-_\.]', '_', filename)
        
        detoxed = re.sub(r'_+', '_', detoxed)
        
        detoxed = detoxed.strip('_')
        
        return detoxed or 'unnamed_file'