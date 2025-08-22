import os
import struct
from pathlib import Path
from typing import List, Optional
from dumprx.utils.logging import logger

class HuaweiUpdateExtractor:
    def __init__(self):
        self.byte_num = 4
        
    def extract(self, source_file: Path, output_dir: Path, file_list: Optional[List[str]] = None) -> bool:
        if not source_file.exists():
            logger.error(f"Source file not found: {source_file}")
            return False
            
        output_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(source_file, 'rb') as f:
                img_files = []
                
                while True:
                    head_size = f.read(4)
                    if len(head_size) < 4:
                        break
                        
                    head_size = struct.unpack('<I', head_size)[0]
                    
                    if head_size == 0:
                        break
                        
                    header_info = f.read(head_size - 4)
                    if len(header_info) < head_size - 4:
                        break
                        
                    header_info_str = header_info.decode('utf-8', errors='ignore')
                    
                    fileinfo_size = struct.unpack('<I', f.read(4))[0]
                    file_size = struct.unpack('<I', f.read(4))[0]
                    f.read(8)
                    
                    file_date = f.read(16).decode('utf-8', errors='ignore').strip('\x00')
                    file_time = f.read(16).decode('utf-8', errors='ignore').strip('\x00')
                    file_type = f.read(16).decode('utf-8', errors='ignore').strip('\x00')
                    f.read(16)
                    
                    header_crc = f.read(4)
                    block_size = struct.unpack('<I', f.read(4))[0]
                    
                    filename = ''
                    i = 72
                    while i < fileinfo_size:
                        char = f.read(1)
                        if char == b'\x00':
                            break
                        filename += char.decode('utf-8', errors='ignore')
                        i += 1
                        
                    f.seek(fileinfo_size - i, 1)
                    
                    crc_data = f.read(4)
                    file_size = struct.unpack('<I', f.read(4))[0]
                    
                    if file_list and filename not in file_list:
                        f.seek(file_size, 1)
                    else:
                        output_file = output_dir / f"{filename}.img"
                        
                        logger.info(f"Extracting {filename}.img ({file_size} bytes)")
                        
                        try:
                            with open(output_file, 'wb') as out_file:
                                remaining = file_size
                                chunk_size = 8192
                                
                                while remaining > 0:
                                    chunk = min(chunk_size, remaining)
                                    data = f.read(chunk)
                                    if not data:
                                        break
                                    out_file.write(data)
                                    remaining -= len(data)
                                    
                            img_files.append(filename)
                            logger.success(f"Extracted {filename}.img")
                            
                        except Exception as e:
                            logger.error(f"Failed to create {filename}.img: {e}")
                            return False
                    
                    x_bytes = self.byte_num - f.tell() % self.byte_num
                    if x_bytes < self.byte_num:
                        f.seek(x_bytes, 1)
                        
            logger.success("Extraction complete")
            return True
            
        except Exception as e:
            logger.error(f"Extraction failed: {e}")
            return False

def extract_huawei_update(source_file: str, output_dir: str, file_list: Optional[List[str]] = None) -> bool:
    extractor = HuaweiUpdateExtractor()
    return extractor.extract(Path(source_file), Path(output_dir), file_list)