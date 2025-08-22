import os
import subprocess
import shutil
from pathlib import Path
import zipfile
import tarfile
import tempfile

class ExtractorManager:
    def __init__(self, console, temp_dir, bin_dir, utils_dir, verbose=False):
        self.console = console
        self.temp_dir = Path(temp_dir)
        self.bin_dir = Path(bin_dir)
        self.utils_dir = Path(utils_dir)
        self.verbose = verbose
        
        self.supported_formats = {
            '.zip': self._extract_zip,
            '.rar': self._extract_rar,
            '.7z': self._extract_7z,
            '.tar': self._extract_tar,
            '.tar.gz': self._extract_tar,
            '.tgz': self._extract_tar,
            '.tar.md5': self._extract_tar,
            '.ozip': self._extract_ozip,
            '.ofp': self._extract_ofp,
            '.ops': self._extract_ops,
            '.kdz': self._extract_kdz,
            '.exe': self._extract_ruu,
            '.bin': self._extract_bin,
            '.img': self._extract_img,
            '.pac': self._extract_pac,
            '.nb0': self._extract_nb0,
            '.sin': self._extract_sin,
        }
    
    def extract_firmware(self, firmware_path):
        firmware_path = Path(firmware_path)
        
        if not firmware_path.exists():
            self.console.print(f"[red]❌ Firmware file not found: {firmware_path}[/red]")
            return None
        
        self.console.print(f"[blue]🔧 Extracting firmware: {firmware_path.name}[/blue]")
        
        extract_dir = self.temp_dir / "extracted"
        extract_dir.mkdir(parents=True, exist_ok=True)
        
        if firmware_path.is_dir():
            self.console.print("[green]📁 Using directory as source[/green]")
            return firmware_path
        
        file_extension = self._get_file_extension(firmware_path)
        
        if file_extension in self.supported_formats:
            try:
                result = self.supported_formats[file_extension](firmware_path, extract_dir)
                if result:
                    self.console.print(f"[green]✅ Extraction completed: {result}[/green]")
                    return result
                else:
                    self.console.print(f"[red]❌ Extraction failed for {firmware_path}[/red]")
                    return None
            except Exception as e:
                self.console.print(f"[red]❌ Extraction error: {str(e)}[/red]")
                if self.verbose:
                    self.console.print_exception()
                return None
        else:
            self.console.print(f"[yellow]⚠️  Unsupported file format: {file_extension}[/yellow]")
            return self._try_generic_extraction(firmware_path, extract_dir)
    
    def _get_file_extension(self, filepath):
        filepath = Path(filepath)
        
        if filepath.name.endswith('.tar.gz'):
            return '.tar.gz'
        elif filepath.name.endswith('.tar.md5'):
            return '.tar.md5'
        elif filepath.name.endswith('.new.dat'):
            return '.new.dat'
        elif filepath.name.endswith('.new.dat.br'):
            return '.new.dat.br'
        elif filepath.name.endswith('.new.dat.xz'):
            return '.new.dat.xz'
        elif filepath.name.startswith('ruu_') and filepath.suffix == '.exe':
            return '.exe'
        else:
            return filepath.suffix.lower()
    
    def _extract_zip(self, filepath, extract_dir):
        try:
            with zipfile.ZipFile(filepath, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            return extract_dir
        except zipfile.BadZipFile:
            return self._extract_with_7z(filepath, extract_dir)
    
    def _extract_rar(self, filepath, extract_dir):
        try:
            result = subprocess.run([
                "unrar", "x", str(filepath), str(extract_dir) + "/"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                return extract_dir
            else:
                return self._extract_with_7z(filepath, extract_dir)
        except FileNotFoundError:
            return self._extract_with_7z(filepath, extract_dir)
    
    def _extract_7z(self, filepath, extract_dir):
        return self._extract_with_7z(filepath, extract_dir)
    
    def _extract_with_7z(self, filepath, extract_dir):
        try:
            bin_7z = self.bin_dir / "7zz"
            cmd = [str(bin_7z)] if bin_7z.exists() else ["7zz"]
            
            result = subprocess.run(
                cmd + ["x", str(filepath), f"-o{extract_dir}", "-y"],
                capture_output=True, text=True
            )
            
            if result.returncode == 0:
                return extract_dir
            else:
                self.console.print(f"[red]7z extraction failed: {result.stderr}[/red]")
                return None
        except FileNotFoundError:
            self.console.print("[red]❌ 7z not found[/red]")
            return None
    
    def _extract_tar(self, filepath, extract_dir):
        try:
            with tarfile.open(filepath, 'r:*') as tar_ref:
                tar_ref.extractall(extract_dir)
            return extract_dir
        except Exception as e:
            if self.verbose:
                self.console.print(f"[yellow]Tar extraction error: {str(e)}[/yellow]")
            return None
    
    def _extract_ozip(self, filepath, extract_dir):
        try:
            ozip_script = self.utils_dir / "oppo_ozip_decrypt" / "ozipdecrypt.py"
            if ozip_script.exists():
                result = subprocess.run([
                    "python3", str(ozip_script), str(filepath)
                ], cwd=extract_dir, capture_output=True, text=True)
                
                if result.returncode == 0:
                    return extract_dir
            
            return None
        except Exception as e:
            if self.verbose:
                self.console.print(f"[yellow]OZIP extraction error: {str(e)}[/yellow]")
            return None
    
    def _extract_ofp(self, filepath, extract_dir):
        try:
            ofp_qc_script = self.utils_dir / "oppo_decrypt" / "ofp_qc_decrypt.py"
            ofp_mtk_script = self.utils_dir / "oppo_decrypt" / "ofp_mtk_decrypt.py"
            
            if ofp_qc_script.exists():
                result = subprocess.run([
                    "python3", str(ofp_qc_script), str(filepath)
                ], cwd=extract_dir, capture_output=True, text=True)
                
                if result.returncode == 0:
                    return extract_dir
            
            if ofp_mtk_script.exists():
                result = subprocess.run([
                    "python3", str(ofp_mtk_script), str(filepath)
                ], cwd=extract_dir, capture_output=True, text=True)
                
                if result.returncode == 0:
                    return extract_dir
            
            return None
        except Exception as e:
            if self.verbose:
                self.console.print(f"[yellow]OFP extraction error: {str(e)}[/yellow]")
            return None
    
    def _extract_ops(self, filepath, extract_dir):
        try:
            ops_script = self.utils_dir / "oppo_decrypt" / "opscrypto.py"
            if ops_script.exists():
                result = subprocess.run([
                    "python3", str(ops_script), str(filepath)
                ], cwd=extract_dir, capture_output=True, text=True)
                
                if result.returncode == 0:
                    return extract_dir
            
            return None
        except Exception as e:
            if self.verbose:
                self.console.print(f"[yellow]OPS extraction error: {str(e)}[/yellow]")
            return None
    
    def _extract_kdz(self, filepath, extract_dir):
        try:
            kdz_script = self.utils_dir / "kdztools" / "unkdz.py"
            if kdz_script.exists():
                result = subprocess.run([
                    "python3", str(kdz_script), "-f", str(filepath), "-x", "-o", str(extract_dir)
                ], capture_output=True, text=True)
                
                if result.returncode == 0:
                    dz_files = list(extract_dir.glob("*.dz"))
                    if dz_files:
                        dz_script = self.utils_dir / "kdztools" / "undz.py"
                        if dz_script.exists():
                            for dz_file in dz_files:
                                subprocess.run([
                                    "python3", str(dz_script), "-f", str(dz_file), "-s", "-o", str(extract_dir)
                                ], capture_output=True)
                    
                    return extract_dir
            
            return None
        except Exception as e:
            if self.verbose:
                self.console.print(f"[yellow]KDZ extraction error: {str(e)}[/yellow]")
            return None
    
    def _extract_ruu(self, filepath, extract_dir):
        try:
            ruu_tool = self.utils_dir / "RUU_Decrypt_Tool"
            if ruu_tool.exists():
                result = subprocess.run([
                    str(ruu_tool), "-s", str(filepath), str(extract_dir)
                ], capture_output=True, text=True)
                
                if result.returncode == 0:
                    return extract_dir
            
            return None
        except Exception as e:
            if self.verbose:
                self.console.print(f"[yellow]RUU extraction error: {str(e)}[/yellow]")
            return None
    
    def _extract_bin(self, filepath, extract_dir):
        if "UPDATE.APP" in filepath.name.upper():
            return self._extract_update_app(filepath, extract_dir)
        elif "payload.bin" in filepath.name:
            return self._extract_payload(filepath, extract_dir)
        else:
            return self._try_generic_extraction(filepath, extract_dir)
    
    def _extract_update_app(self, filepath, extract_dir):
        from dumprx.extractors.update_app_extractor import extract_update_app
        
        try:
            if splituapp_script.exists():
                result = extract_update_app(str(filepath), str(extract_dir))
                if result:
                    return extract_dir
            
            return None
        except Exception as e:
            if self.verbose:
                self.console.print(f"[yellow]UPDATE.APP extraction error: {str(e)}[/yellow]")
            return None
    
    def _extract_payload(self, filepath, extract_dir):
        try:
            payload_tool = self.bin_dir / "payload-dumper-go"
            if payload_tool.exists():
                result = subprocess.run([
                    str(payload_tool), "-o", str(extract_dir), str(filepath)
                ], capture_output=True, text=True)
                
                if result.returncode == 0:
                    return extract_dir
            
            return None
        except Exception as e:
            if self.verbose:
                self.console.print(f"[yellow]Payload extraction error: {str(e)}[/yellow]")
            return None
    
    def _extract_img(self, filepath, extract_dir):
        return self._try_generic_extraction(filepath, extract_dir)
    
    def _extract_pac(self, filepath, extract_dir):
        try:
            pac_script = self.utils_dir / "pacextractor" / "python" / "pacExtractor.py"
            if pac_script.exists():
                result = subprocess.run([
                    "python3", str(pac_script), str(filepath), str(extract_dir)
                ], capture_output=True, text=True)
                
                if result.returncode == 0:
                    return extract_dir
            
            return None
        except Exception as e:
            if self.verbose:
                self.console.print(f"[yellow]PAC extraction error: {str(e)}[/yellow]")
            return None
    
    def _extract_nb0(self, filepath, extract_dir):
        try:
            nb0_tool = self.utils_dir / "nb0-extract"
            if nb0_tool.exists():
                result = subprocess.run([
                    str(nb0_tool), str(filepath)
                ], cwd=extract_dir, capture_output=True, text=True)
                
                if result.returncode == 0:
                    return extract_dir
            
            return None
        except Exception as e:
            if self.verbose:
                self.console.print(f"[yellow]NB0 extraction error: {str(e)}[/yellow]")
            return None
    
    def _extract_sin(self, filepath, extract_dir):
        try:
            unsin_tool = self.utils_dir / "unsin"
            if unsin_tool.exists():
                result = subprocess.run([
                    str(unsin_tool), "-d", str(extract_dir), str(filepath)
                ], capture_output=True, text=True)
                
                if result.returncode == 0:
                    return extract_dir
            
            return None
        except Exception as e:
            if self.verbose:
                self.console.print(f"[yellow]SIN extraction error: {str(e)}[/yellow]")
            return None
    
    def _try_generic_extraction(self, filepath, extract_dir):
        shutil.copy2(filepath, extract_dir)
        return extract_dir
    
    def extract_partition_image(self, partition_file, partition_name):
        try:
            simg2img_tool = self.bin_dir / "simg2img"
            if simg2img_tool.exists() and partition_file.suffix == '.img':
                output_file = partition_file.parent / f"{partition_name}_raw.img"
                result = subprocess.run([
                    str(simg2img_tool), str(partition_file), str(output_file)
                ], capture_output=True, text=True)
                
                if result.returncode == 0:
                    self.console.print(f"[green]✅ Converted sparse image: {output_file}[/green]")
        except Exception as e:
            if self.verbose:
                self.console.print(f"[yellow]Image processing error: {str(e)}[/yellow]")
    
    def convert_sparse_data(self, sparse_file, partition_name):
        from dumprx.extractors.sdat2img import convert_sdat_to_img
        
        try:
            if sdat2img_script.exists():
                transfer_list = sparse_file.parent / f"{partition_name}.transfer.list"
                output_img = sparse_file.parent / f"{partition_name}.img"
                
                if transfer_list.exists():
                    convert_sdat_to_img(str(transfer_list), str(sparse_file), str(output_img))
                    self.console.print(f"[green]✅ Converted sparse data: {output_img}[/green]")
        except Exception as e:
            if self.verbose:
                self.console.print(f"[yellow]Sparse data conversion error: {str(e)}[/yellow]")