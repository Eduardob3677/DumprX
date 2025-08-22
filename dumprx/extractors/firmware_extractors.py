from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional
from rich.console import Console

class BaseExtractor(ABC):
    def __init__(self, config, tool_manager, console: Console):
        self.config = config
        self.tool_manager = tool_manager
        self.console = console
    
    @abstractmethod
    def extract(self, firmware_path: Path, output_dir: Path) -> bool:
        pass
    
    def _log_info(self, message: str):
        self.console.print(f"[blue]ℹ️  {message}[/blue]")
    
    def _log_success(self, message: str):
        self.console.print(f"[green]✅ {message}[/green]")
    
    def _log_warning(self, message: str):
        self.console.print(f"[yellow]⚠️  {message}[/yellow]")
    
    def _log_error(self, message: str):
        self.console.print(f"[red]❌ {message}[/red]")

class OppoOzipExtractor(BaseExtractor):
    def extract(self, firmware_path: Path, output_dir: Path) -> bool:
        self._log_info("Oppo/Realme ozip detected")
        
        try:
            ozip_file = output_dir / firmware_path.name
            ozip_file.parent.mkdir(parents=True, exist_ok=True)
            
            if firmware_path.parent != self.config.input_dir:
                import shutil
                shutil.copy2(firmware_path, ozip_file)
            else:
                ozip_file = firmware_path
            
            self._log_info("Decrypting ozip and making a zip...")
            
            requirements_file = self.config.utils_dir / "oppo_decrypt" / "requirements.txt"
            decrypt_script = self.config.tool_paths['ozipdecrypt']
            
            success = self.tool_manager.run_uv_script(
                decrypt_script, requirements_file, [str(ozip_file)]
            )
            
            if not success:
                return False
            
            decrypted_zip = ozip_file.with_suffix('.zip')
            out_dir = output_dir / "out"
            
            if decrypted_zip.exists():
                self._log_success("Decryption successful, processing zip...")
                # Process the decrypted zip
                return self.tool_manager.extract_with_7z(decrypted_zip, output_dir)
            elif out_dir.exists():
                self._log_success("Files extracted to out directory")
                import shutil
                for item in out_dir.iterdir():
                    shutil.move(str(item), str(output_dir / item.name))
                out_dir.rmdir()
                return True
            
            return False
            
        except Exception as e:
            self._log_error(f"Ozip extraction failed: {str(e)}")
            return False

class OppoOpsExtractor(BaseExtractor):
    def extract(self, firmware_path: Path, output_dir: Path) -> bool:
        self._log_info("Oppo/Oneplus ops detected")
        
        try:
            ops_file = output_dir / firmware_path.name
            ops_file.parent.mkdir(parents=True, exist_ok=True)
            
            if firmware_path.parent != self.config.input_dir:
                import shutil
                shutil.copy2(firmware_path, ops_file)
            else:
                ops_file = firmware_path
            
            self._log_info("Decrypting ops & extracting...")
            
            requirements_file = self.config.utils_dir / "oppo_decrypt" / "requirements.txt"
            decrypt_script = self.config.tool_paths['opsdecrypt']
            
            success = self.tool_manager.run_uv_script(
                decrypt_script, requirements_file, ["decrypt", str(ops_file)]
            )
            
            if not success:
                return False
            
            extract_dir = output_dir / "extract"
            if extract_dir.exists():
                self._log_success("OPS decryption successful")
                import shutil
                for item in extract_dir.iterdir():
                    shutil.move(str(item), str(output_dir / item.name))
                extract_dir.rmdir()
                return True
            
            return False
            
        except Exception as e:
            self._log_error(f"OPS extraction failed: {str(e)}")
            return False

class LgKdzExtractor(BaseExtractor):
    def extract(self, firmware_path: Path, output_dir: Path) -> bool:
        self._log_info("LG KDZ detected")
        
        try:
            kdz_file = output_dir / firmware_path.name
            if firmware_path.parent != self.config.input_dir:
                import shutil
                shutil.copy2(firmware_path, kdz_file)
            else:
                kdz_file = firmware_path
            
            os.chdir(output_dir)
            
            success = self.tool_manager.run_command([
                "python3", str(self.config.tool_paths['kdz_extract']),
                "-f", kdz_file.name, "-x", "-o", "./"
            ])
            
            if not success:
                return False
            
            dz_files = list(output_dir.glob("*.dz"))
            if dz_files:
                dz_file = dz_files[0]
                self._log_info("Extracting all partitions as individual images")
                
                success = self.tool_manager.run_command([
                    "python3", str(self.config.tool_paths['dz_extract']),
                    "-f", dz_file.name, "-s", "-o", "./"
                ])
                
                return success
            
            return False
            
        except Exception as e:
            self._log_error(f"KDZ extraction failed: {str(e)}")
            return False

class HuaweiUpdateExtractor(BaseExtractor):
    def extract(self, firmware_path: Path, output_dir: Path) -> bool:
        self._log_info("Huawei UPDATE.APP detected")
        
        try:
            import os
            os.chdir(output_dir)
            
            if firmware_path.name != "UPDATE.APP":
                success = self.tool_manager.extract_with_7z(
                    firmware_path, output_dir, ["UPDATE.APP"]
                )
                if not success:
                    return False
            
            update_app = output_dir / "UPDATE.APP"
            if not update_app.exists():
                update_apps = list(output_dir.rglob("UPDATE.APP"))
                if update_apps:
                    import shutil
                    shutil.move(str(update_apps[0]), str(update_app))
                else:
                    return False
            
            self._log_info("Extracting partitions from UPDATE.APP")
            
            success = self.tool_manager.run_command([
                "python3", str(self.config.tool_paths['splituapp']),
                "-f", "UPDATE.APP", "-l", "super", "preas", "preavs"
            ])
            
            if not success:
                for partition in self.config.partitions:
                    try:
                        self.tool_manager.run_command([
                            "python3", str(self.config.tool_paths['splituapp']),
                            "-f", "UPDATE.APP", "-l", partition.replace('.img', '')
                        ])
                    except:
                        continue
            
            return True
            
        except Exception as e:
            self._log_error(f"Huawei UPDATE.APP extraction failed: {str(e)}")
            return False

class AbOtaExtractor(BaseExtractor):
    def extract(self, firmware_path: Path, output_dir: Path) -> bool:
        self._log_info("A/B OTA Payload detected")
        
        try:
            if firmware_path.is_file():
                payload_file = firmware_path
            else:
                contents = self.tool_manager.list_archive_contents(firmware_path)
                if "payload.bin" not in contents:
                    return False
                
                success = self.tool_manager.extract_with_7z(
                    firmware_path, output_dir, ["payload.bin"]
                )
                if not success:
                    return False
                
                payload_file = output_dir / "payload.bin"
                if not payload_file.exists():
                    payload_files = list(output_dir.rglob("payload.bin"))
                    if payload_files:
                        payload_file = payload_files[0]
                    else:
                        return False
            
            import multiprocessing
            cpu_count = multiprocessing.cpu_count()
            
            success = self.tool_manager.run_command([
                str(self.config.tool_paths['payload_extractor']),
                "-c", str(cpu_count),
                "-o", str(output_dir),
                str(payload_file)
            ])
            
            return success
            
        except Exception as e:
            self._log_error(f"A/B OTA extraction failed: {str(e)}")
            return False

class GenericArchiveExtractor(BaseExtractor):
    def extract(self, firmware_path: Path, output_dir: Path) -> bool:
        self._log_info(f"Extracting archive: {firmware_path.suffix}")
        
        try:
            return self.tool_manager.extract_with_7z(firmware_path, output_dir)
        except Exception as e:
            self._log_error(f"Archive extraction failed: {str(e)}")
            return False

class ExtractedFirmwareHandler(BaseExtractor):
    def extract(self, firmware_path: Path, output_dir: Path) -> bool:
        self._log_info("Processing extracted firmware directory")
        
        try:
            import shutil
            for item in firmware_path.iterdir():
                dest = output_dir / item.name
                if item.is_dir():
                    shutil.copytree(item, dest, dirs_exist_ok=True)
                else:
                    shutil.copy2(item, dest)
            
            return True
            
        except Exception as e:
            self._log_error(f"Directory processing failed: {str(e)}")
            return False

class FirmwareExtractorFactory:
    def __init__(self, config, tool_manager, console):
        self.config = config
        self.tool_manager = tool_manager
        self.console = console
        
        self.extractors = {
            'oppo_ozip': OppoOzipExtractor,
            'oppo_ops': OppoOpsExtractor,
            'lg_kdz': LgKdzExtractor,
            'huawei_update': HuaweiUpdateExtractor,
            'ab_ota': AbOtaExtractor,
            'ab_ota_archive': AbOtaExtractor,
            'huawei_archive': HuaweiUpdateExtractor,
            'firmware_archive': GenericArchiveExtractor,
            'generic_archive': GenericArchiveExtractor,
            'archive': GenericArchiveExtractor,
            'extracted_firmware': ExtractedFirmwareHandler,
            'archive_folder': ExtractedFirmwareHandler,
        }
    
    def get_extractor(self, file_type: str) -> Optional[BaseExtractor]:
        extractor_class = self.extractors.get(file_type)
        if extractor_class:
            return extractor_class(self.config, self.tool_manager, self.console)
        return None