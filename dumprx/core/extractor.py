import os
import subprocess
import shutil
from pathlib import Path
from typing import Optional, Dict, Any
from rich.progress import Progress, TaskID, SpinnerColumn, TextColumn, BarColumn, MofNCompleteColumn
from dumprx.utils.logging import logger
from dumprx.core.device import DeviceDetector
from dumprx.core.config import Config

class FirmwareExtractor:
    def __init__(self, config: Config, device_detector: DeviceDetector):
        self.config = config
        self.device_detector = device_detector
        self.progress = None
        
    def extract(self, input_path: str) -> bool:
        input_file = Path(input_path)
        
        if not input_file.exists():
            if input_path.startswith(('http://', 'https://', 'mega:', 'gdrive:')):
                logger.info("URL detected, downloading first...")
                from dumprx.utils.downloads import DownloadManager
                downloader = DownloadManager(self.config)
                downloaded_file = downloader.download(input_path)
                if not downloaded_file:
                    return False
                input_file = Path(downloaded_file)
            else:
                logger.error(f"Input file does not exist: {input_path}")
                return False
        
        firmware_type = self.device_detector.detect_firmware_type(input_file)
        logger.info(f"Detected firmware type: {firmware_type}")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            expand=True
        ) as progress:
            self.progress = progress
            main_task = progress.add_task("Extracting firmware...", total=100)
            
            try:
                if firmware_type == 'lg_kdz':
                    result = self._extract_lg_kdz(input_file, main_task)
                elif firmware_type == 'oppo_ozip':
                    result = self._extract_oppo_ozip(input_file, main_task)
                elif firmware_type == 'oppo_ofp':
                    result = self._extract_oppo_ofp(input_file, main_task)
                elif firmware_type == 'oppo_ops':
                    result = self._extract_oppo_ops(input_file, main_task)
                elif firmware_type == 'payload':
                    result = self._extract_payload(input_file, main_task)
                elif firmware_type == 'htc_ruu':
                    result = self._extract_htc_ruu(input_file, main_task)
                elif firmware_type == 'huawei_update':
                    result = self._extract_huawei_update(input_file, main_task)
                elif firmware_type == 'nokia_nb0':
                    result = self._extract_nokia_nb0(input_file, main_task)
                elif firmware_type == 'spreadtrum_pac':
                    result = self._extract_spreadtrum_pac(input_file, main_task)
                elif firmware_type == 'sony_sin':
                    result = self._extract_sony_sin(input_file, main_task)
                elif firmware_type == 'super_img':
                    result = self._extract_super_img(input_file, main_task)
                elif firmware_type == 'archive':
                    result = self._extract_archive(input_file, main_task)
                elif firmware_type == 'android_dat':
                    result = self._extract_android_dat(input_file, main_task)
                elif firmware_type == 'raw_img':
                    result = self._extract_raw_img(input_file, main_task)
                else:
                    logger.error(f"Unsupported firmware type: {firmware_type}")
                    return False
                    
                if result:
                    progress.update(main_task, completed=100)
                    
                return result
                    
            except Exception as e:
                logger.error(f"Extraction failed: {e}")
                return False
    
    def _run_command(self, cmd: list, cwd: Optional[Path] = None) -> bool:
        try:
            result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
            if result.returncode != 0:
                logger.error(f"Command failed: {' '.join(map(str, cmd))}")
                logger.error(f"Error: {result.stderr}")
                return False
            return True
        except Exception as e:
            logger.error(f"Failed to run command: {e}")
            return False
    
    def _extract_lg_kdz(self, input_file: Path, task: TaskID) -> bool:
        logger.info("LG KDZ Detected.")
        self.progress.update(task, description="Extracting LG KDZ...", advance=10)
        
        shutil.copy2(input_file, self.config.tmp_dir)
        tmp_file = self.config.tmp_dir / input_file.name
        
        kdz_extract = self.config.python_tools['kdz_extract']
        if not self._run_command(['python3', str(kdz_extract), '-f', str(tmp_file), '-x', '-o', './'], 
                                cwd=self.config.tmp_dir):
            return False
            
        self.progress.update(task, advance=30)
            
        dz_files = list(self.config.tmp_dir.glob('*.dz'))
        if not dz_files:
            logger.error("No DZ file found after KDZ extraction")
            return False
            
        logger.info("Extracting All Partitions As Individual Images.")
        dz_extract = self.config.python_tools['dz_extract']
        for dz_file in dz_files:
            if not self._run_command(['python3', str(dz_extract), '-f', str(dz_file), '-s', '-o', './'],
                                   cwd=self.config.tmp_dir):
                return False
                
        self.progress.update(task, advance=40)
        return self._process_extracted_files(task)
    
    def _extract_oppo_ozip(self, input_file: Path, task: TaskID) -> bool:
        logger.info("OPPO OZIP Detected.")
        self.progress.update(task, description="Decrypting OPPO OZIP...", advance=20)
        
        shutil.copy2(input_file, self.config.tmp_dir)
        tmp_file = self.config.tmp_dir / input_file.name
        
        ozipdecrypt = self.config.python_tools['ozipdecrypt']
        if not self._run_command(['python3', str(ozipdecrypt), str(tmp_file)], 
                                cwd=self.config.tmp_dir):
            return False
            
        self.progress.update(task, advance=60)
        return self._process_extracted_files(task)
    
    def _extract_oppo_ofp(self, input_file: Path, task: TaskID) -> bool:
        logger.info("OPPO OFP Detected.")
        self.progress.update(task, description="Decrypting OPPO OFP...", advance=20)
        
        shutil.copy2(input_file, self.config.tmp_dir)
        tmp_file = self.config.tmp_dir / input_file.name
        
        ofp_qc_decrypt = self.config.python_tools['ofp_qc_decrypt']
        if not self._run_command(['python3', str(ofp_qc_decrypt), str(tmp_file)], 
                                cwd=self.config.tmp_dir):
            
            ofp_mtk_decrypt = self.config.python_tools['ofp_mtk_decrypt']
            if not self._run_command(['python3', str(ofp_mtk_decrypt), str(tmp_file)], 
                                   cwd=self.config.tmp_dir):
                return False
                
        self.progress.update(task, advance=60)
        return self._process_extracted_files(task)
    
    def _extract_oppo_ops(self, input_file: Path, task: TaskID) -> bool:
        logger.info("OPPO OPS Detected.")
        self.progress.update(task, description="Decrypting OPPO OPS...", advance=20)
        
        shutil.copy2(input_file, self.config.tmp_dir)
        tmp_file = self.config.tmp_dir / input_file.name
        
        opsdecrypt = self.config.python_tools['opsdecrypt']
        if not self._run_command(['python3', str(opsdecrypt), str(tmp_file)], 
                                cwd=self.config.tmp_dir):
            return False
            
        self.progress.update(task, advance=60)
        return self._process_extracted_files(task)
    
    def _extract_archive(self, input_file: Path, task: TaskID) -> bool:
        logger.info(f"Archive Detected: {input_file.suffix}")
        self.progress.update(task, description="Extracting archive...", advance=20)
        
        if not self._run_command([self.config.bin_7zz, 'x', str(input_file), f'-o{self.config.tmp_dir}', '-y']):
            return False
            
        self.progress.update(task, advance=60)
        return self._process_extracted_files(task)
    
    def _extract_payload(self, input_file: Path, task: TaskID) -> bool:
        logger.info("Payload.bin Detected.")
        self.progress.update(task, description="Extracting payload...", advance=20)
        
        payload_extractor = self.config.tools['payload_extractor']
        if not self._run_command([str(payload_extractor), '-o', str(self.config.tmp_dir), str(input_file)]):
            return False
            
        self.progress.update(task, advance=60)
        return self._process_extracted_files(task)
    
    def _extract_super_img(self, input_file: Path, task: TaskID) -> bool:
        logger.info("Super Image Detected.")
        self.progress.update(task, description="Extracting super image...", advance=20)
        
        lpunpack = self.config.tools['lpunpack']
        if not self._run_command([str(lpunpack), str(input_file), str(self.config.tmp_dir)]):
            return False
            
        self.progress.update(task, advance=60)
        return self._process_extracted_files(task)
    
    def _extract_huawei_update(self, input_file: Path, task: TaskID) -> bool:
        logger.info("Huawei UPDATE.APP Detected.")
        self.progress.update(task, description="Extracting Huawei UPDATE.APP...", advance=20)
        
        from dumprx.tools.splituapp import extract_huawei_update
        result = extract_huawei_update(str(input_file), str(self.config.tmp_dir))
        
        if not result:
            return False
            
        self.progress.update(task, advance=60)
        return self._process_extracted_files(task)
    
    def _extract_android_dat(self, input_file: Path, task: TaskID) -> bool:
        logger.info("Android DAT Image Detected.")
        self.progress.update(task, description="Converting sparse data image...", advance=20)
        
        base_name = input_file.stem
        if base_name.endswith('.new'):
            base_name = base_name[:-4]
            
        transfer_list = input_file.parent / f"{base_name}.transfer.list"
        if not transfer_list.exists():
            logger.error(f"Transfer list not found: {transfer_list}")
            return False
            
        output_img = self.config.tmp_dir / f"{base_name}.img"
        
        from dumprx.tools.sdat2img import convert_sdat2img
        result = convert_sdat2img(str(transfer_list), str(input_file), str(output_img))
        
        if not result:
            return False
            
        self.progress.update(task, advance=60)
        return self._process_extracted_files(task)
    
    def _extract_nokia_nb0(self, input_file: Path, task: TaskID) -> bool:
        logger.info("Nokia NB0 Detected.")
        self.progress.update(task, description="Extracting Nokia NB0...", advance=20)
        
        nb0_extract = self.config.tools['nb0_extract']
        if not self._run_command([str(nb0_extract), str(input_file)], cwd=self.config.tmp_dir):
            return False
            
        self.progress.update(task, advance=60)
        return self._process_extracted_files(task)
    
    def _extract_spreadtrum_pac(self, input_file: Path, task: TaskID) -> bool:
        logger.info("Spreadtrum PAC Detected.")
        self.progress.update(task, description="Extracting Spreadtrum PAC...", advance=20)
        
        pacextractor = self.config.python_tools['pacextractor']
        if not self._run_command(['python3', str(pacextractor), str(input_file)], cwd=self.config.tmp_dir):
            return False
            
        self.progress.update(task, advance=60)
        return self._process_extracted_files(task)
    
    def _extract_sony_sin(self, input_file: Path, task: TaskID) -> bool:
        logger.info("Sony SIN Detected.")
        self.progress.update(task, description="Extracting Sony SIN...", advance=20)
        
        unsin = self.config.tools['unsin']
        if not self._run_command([str(unsin), str(input_file)], cwd=self.config.tmp_dir):
            return False
            
        self.progress.update(task, advance=60)
        return self._process_extracted_files(task)
    
    def _extract_raw_img(self, input_file: Path, task: TaskID) -> bool:
        logger.info("Raw Image Detected.")
        self.progress.update(task, description="Copying raw image...", advance=20)
        
        shutil.copy2(input_file, self.config.tmp_dir)
        self.progress.update(task, advance=60)
        return self._process_extracted_files(task)
    
    def _extract_htc_ruu(self, input_file: Path, task: TaskID) -> bool:
        logger.info("HTC RUU Detected.")
        self.progress.update(task, description="Decrypting HTC RUU...", advance=20)
        
        ruudecrypt = self.config.tools['ruudecrypt']
        if not self._run_command([str(ruudecrypt), '-s', str(input_file)], cwd=self.config.tmp_dir):
            return False
            
        self.progress.update(task, advance=60)
        return self._process_extracted_files(task)
    
    def _process_extracted_files(self, task: TaskID) -> bool:
        self.progress.update(task, description="Processing extracted files...", advance=10)
        
        device_info = self.device_detector.detect_from_build_props(self.config.tmp_dir)
        partitions = self.device_detector.detect_partitions(self.config.tmp_dir)
        
        self.progress.update(task, advance=10)
        
        logger.info(f"Detected device: {device_info.get('model', 'Unknown')}")
        logger.info(f"Detected partitions: {', '.join(partitions)}")
        
        # Move extracted files to output directory
        if self.config.tmp_dir.exists():
            if self.config.output_dir.exists():
                shutil.rmtree(self.config.output_dir)
            shutil.move(str(self.config.tmp_dir), str(self.config.output_dir))
        
        return True