import os
import subprocess
import shutil
from pathlib import Path
from typing import Optional, Dict, Any
from dumprx.utils.logging import logger
from dumprx.core.device import DeviceDetector
from dumprx.core.config import Config

class FirmwareExtractor:
    def __init__(self, config: Config, device_detector: DeviceDetector):
        self.config = config
        self.device_detector = device_detector
        
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
        
        try:
            if firmware_type == 'lg_kdz':
                return self._extract_lg_kdz(input_file)
            elif firmware_type == 'oppo_ozip':
                return self._extract_oppo_ozip(input_file)
            elif firmware_type == 'oppo_ofp':
                return self._extract_oppo_ofp(input_file)
            elif firmware_type == 'oppo_ops':
                return self._extract_oppo_ops(input_file)
            elif firmware_type == 'payload':
                return self._extract_payload(input_file)
            elif firmware_type == 'htc_ruu':
                return self._extract_htc_ruu(input_file)
            elif firmware_type == 'huawei_update':
                return self._extract_huawei_update(input_file)
            elif firmware_type == 'nokia_nb0':
                return self._extract_nokia_nb0(input_file)
            elif firmware_type == 'spreadtrum_pac':
                return self._extract_spreadtrum_pac(input_file)
            elif firmware_type == 'sony_sin':
                return self._extract_sony_sin(input_file)
            elif firmware_type == 'super_img':
                return self._extract_super_img(input_file)
            elif firmware_type == 'archive':
                return self._extract_archive(input_file)
            elif firmware_type == 'android_dat':
                return self._extract_android_dat(input_file)
            elif firmware_type == 'raw_img':
                return self._extract_raw_img(input_file)
            else:
                logger.error(f"Unsupported firmware type: {firmware_type}")
                return False
                
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
    
    def _extract_lg_kdz(self, input_file: Path) -> bool:
        logger.info("LG KDZ Detected.")
        
        shutil.copy2(input_file, self.config.tmp_dir)
        tmp_file = self.config.tmp_dir / input_file.name
        
        kdz_extract = self.config.python_tools['kdz_extract']
        if not self._run_command(['python3', str(kdz_extract), '-f', str(tmp_file), '-x', '-o', './'], 
                                cwd=self.config.tmp_dir):
            return False
            
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
                
        return self._process_extracted_files()
    
    def _extract_oppo_ozip(self, input_file: Path) -> bool:
        logger.info("OPPO OZIP Detected.")
        
        shutil.copy2(input_file, self.config.tmp_dir)
        tmp_file = self.config.tmp_dir / input_file.name
        
        ozipdecrypt = self.config.python_tools['ozipdecrypt']
        if not self._run_command(['python3', str(ozipdecrypt), str(tmp_file)], 
                                cwd=self.config.tmp_dir):
            return False
            
        return self._process_extracted_files()
    
    def _extract_oppo_ofp(self, input_file: Path) -> bool:
        logger.info("OPPO OFP Detected.")
        
        shutil.copy2(input_file, self.config.tmp_dir)
        tmp_file = self.config.tmp_dir / input_file.name
        
        ofp_qc_decrypt = self.config.python_tools['ofp_qc_decrypt']
        if not self._run_command(['python3', str(ofp_qc_decrypt), str(tmp_file)], 
                                cwd=self.config.tmp_dir):
            
            ofp_mtk_decrypt = self.config.python_tools['ofp_mtk_decrypt']
            if not self._run_command(['python3', str(ofp_mtk_decrypt), str(tmp_file)], 
                                   cwd=self.config.tmp_dir):
                return False
                
        return self._process_extracted_files()
    
    def _extract_oppo_ops(self, input_file: Path) -> bool:
        logger.info("OPPO OPS Detected.")
        
        shutil.copy2(input_file, self.config.tmp_dir)
        tmp_file = self.config.tmp_dir / input_file.name
        
        opsdecrypt = self.config.python_tools['opsdecrypt']
        if not self._run_command(['python3', str(opsdecrypt), str(tmp_file)], 
                                cwd=self.config.tmp_dir):
            return False
            
        return self._process_extracted_files()
    
    def _extract_payload(self, input_file: Path) -> bool:
        logger.info("Payload.bin Detected.")
        
        payload_extractor = self.config.tools['payload_extractor']
        if not self._run_command([str(payload_extractor), '-o', str(self.config.tmp_dir), str(input_file)]):
            return False
            
        return self._process_extracted_files()
    
    def _extract_archive(self, input_file: Path) -> bool:
        logger.info(f"Archive Detected: {input_file.suffix}")
        
        if not self._run_command([self.config.bin_7zz, 'x', str(input_file), f'-o{self.config.tmp_dir}', '-y']):
            return False
            
        return self._process_extracted_files()
    
    def _extract_android_dat(self, input_file: Path) -> bool:
        logger.info("Android DAT Image Detected.")
        
        base_name = input_file.stem
        if base_name.endswith('.new'):
            base_name = base_name[:-4]
            
        transfer_list = input_file.parent / f"{base_name}.transfer.list"
        if not transfer_list.exists():
            logger.error(f"Transfer list not found: {transfer_list}")
            return False
            
        output_img = self.config.tmp_dir / f"{base_name}.img"
        
        sdat2img = self.config.python_tools['sdat2img']
        if not self._run_command(['python3', str(sdat2img), str(transfer_list), str(input_file), str(output_img)]):
            return False
            
        return self._process_extracted_files()
    
    def _extract_super_img(self, input_file: Path) -> bool:
        logger.info("Super Image Detected.")
        
        lpunpack = self.config.tools['lpunpack']
        if not self._run_command([str(lpunpack), str(input_file), str(self.config.tmp_dir)]):
            return False
            
        return self._process_extracted_files()
    
    def _extract_raw_img(self, input_file: Path) -> bool:
        logger.info("Raw Image Detected.")
        
        shutil.copy2(input_file, self.config.tmp_dir)
        return self._process_extracted_files()
    
    def _extract_htc_ruu(self, input_file: Path) -> bool:
        logger.info("HTC RUU Detected.")
        
        ruudecrypt = self.config.tools['ruudecrypt']
        if not self._run_command([str(ruudecrypt), '-s', str(input_file)], cwd=self.config.tmp_dir):
            return False
            
        return self._process_extracted_files()
    
    def _extract_huawei_update(self, input_file: Path) -> bool:
        logger.info("Huawei UPDATE.APP Detected.")
        
        splituapp = self.config.python_tools['splituapp']
        if not self._run_command(['python3', str(splituapp), str(input_file)], cwd=self.config.tmp_dir):
            return False
            
        return self._process_extracted_files()
    
    def _extract_nokia_nb0(self, input_file: Path) -> bool:
        logger.info("Nokia NB0 Detected.")
        
        nb0_extract = self.config.tools['nb0_extract']
        if not self._run_command([str(nb0_extract), str(input_file)], cwd=self.config.tmp_dir):
            return False
            
        return self._process_extracted_files()
    
    def _extract_spreadtrum_pac(self, input_file: Path) -> bool:
        logger.info("Spreadtrum PAC Detected.")
        
        pacextractor = self.config.python_tools['pacextractor']
        if not self._run_command(['python3', str(pacextractor), str(input_file)], cwd=self.config.tmp_dir):
            return False
            
        return self._process_extracted_files()
    
    def _extract_sony_sin(self, input_file: Path) -> bool:
        logger.info("Sony SIN Detected.")
        
        unsin = self.config.tools['unsin']
        if not self._run_command([str(unsin), str(input_file)], cwd=self.config.tmp_dir):
            return False
            
        return self._process_extracted_files()
    
    def _process_extracted_files(self) -> bool:
        device_info = self.device_detector.detect_from_build_props(self.config.tmp_dir)
        partitions = self.device_detector.detect_partitions(self.config.tmp_dir)
        
        logger.info(f"Detected device: {device_info.get('model', 'Unknown')}")
        logger.info(f"Detected partitions: {', '.join(partitions)}")
        
        return True