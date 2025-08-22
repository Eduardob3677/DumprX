import asyncio
import struct
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from .ui import UI

class BootImageExtractor:
    def __init__(self, utils_dir: Path):
        self.utils_dir = utils_dir
        self.magic_signatures = {
            b'ANDROID!': 'android_boot',
            b'VNDRBOOT': 'vendor_boot',
            b'BOOTIMAGE': 'boot_image'
        }
    
    async def extract(self, boot_path: Path, output_dir: Path) -> bool:
        UI.processing(f"Extracting boot image: {boot_path.name}")
        
        try:
            with open(boot_path, 'rb') as f:
                data = f.read()
            
            header_info = self._parse_boot_header(data)
            if not header_info:
                UI.warning(f"Unknown boot image format: {boot_path.name}")
                return False
            
            success = await self._extract_components(data, header_info, output_dir)
            
            if success:
                await self._extract_ramdisk(output_dir)
                UI.success("Boot image extraction completed")
            
            return success
            
        except Exception as e:
            UI.error(f"Boot extraction failed: {e}")
            return False
    
    def _parse_boot_header(self, data: bytes) -> Optional[Dict[str, Any]]:
        if len(data) < 2048:
            return None
        
        magic = data[:8]
        if magic != b'ANDROID!':
            return None
        
        try:
            header = struct.unpack('<8s10I16s512s32s1024sI', data[:2048])
            
            return {
                'magic': header[0],
                'kernel_size': header[1],
                'kernel_addr': header[2],
                'ramdisk_size': header[3],
                'ramdisk_addr': header[4],
                'second_size': header[5],
                'second_addr': header[6],
                'tags_addr': header[7],
                'page_size': header[8],
                'dt_size': header[9],
                'unused': header[10],
                'name': header[11],
                'cmdline': header[12],
                'id': header[13],
                'extra_cmdline': header[14],
                'recovery_dtbo_size': header[15]
            }
        except:
            return None
    
    async def _extract_components(self, data: bytes, header: Dict[str, Any], output_dir: Path) -> bool:
        output_dir.mkdir(parents=True, exist_ok=True)
        
        page_size = header['page_size']
        kernel_size = header['kernel_size']
        ramdisk_size = header['ramdisk_size']
        second_size = header['second_size']
        dt_size = header['dt_size']
        
        offset = page_size
        
        if kernel_size > 0:
            kernel_data = data[offset:offset + kernel_size]
            with open(output_dir / 'kernel', 'wb') as f:
                f.write(kernel_data)
            offset += self._align_to_page(kernel_size, page_size)
        
        if ramdisk_size > 0:
            ramdisk_data = data[offset:offset + ramdisk_size]
            with open(output_dir / 'ramdisk.packed', 'wb') as f:
                f.write(ramdisk_data)
            offset += self._align_to_page(ramdisk_size, page_size)
        
        if second_size > 0:
            second_data = data[offset:offset + second_size]
            with open(output_dir / 'second', 'wb') as f:
                f.write(second_data)
            offset += self._align_to_page(second_size, page_size)
        
        if dt_size > 0:
            dt_data = data[offset:offset + dt_size]
            with open(output_dir / 'dt', 'wb') as f:
                f.write(dt_data)
        
        info_content = f"""magic={header['magic'].decode('ascii', errors='ignore')}
kernel_size={kernel_size}
kernel_addr=0x{header['kernel_addr']:08x}
ramdisk_size={ramdisk_size}
ramdisk_addr=0x{header['ramdisk_addr']:08x}
second_size={second_size}
second_addr=0x{header['second_addr']:08x}
tags_addr=0x{header['tags_addr']:08x}
page_size={page_size}
dt_size={dt_size}
name={header['name'].decode('ascii', errors='ignore').rstrip('\\x00')}
cmdline={header['cmdline'].decode('ascii', errors='ignore').rstrip('\\x00')}
"""
        
        with open(output_dir / 'img_info', 'w') as f:
            f.write(info_content)
        
        return True
    
    def _align_to_page(self, size: int, page_size: int) -> int:
        return ((size + page_size - 1) // page_size) * page_size
    
    async def _extract_ramdisk(self, output_dir: Path) -> bool:
        ramdisk_path = output_dir / 'ramdisk.packed'
        if not ramdisk_path.exists():
            return False
        
        ramdisk_dir = output_dir / 'ramdisk'
        ramdisk_dir.mkdir(exist_ok=True)
        
        compression_methods = [
            ('gzip', ['gunzip', '-c']),
            ('lzma', ['lzma', '-d', '-c']),
            ('xz', ['xz', '-d', '-c']),
            ('lz4', ['lz4', '-d']),
            ('bzip2', ['bzip2', '-d', '-c']),
            ('lzop', ['lzop', '-d', '-c'])
        ]
        
        for method_name, cmd in compression_methods:
            try:
                UI.processing(f"Trying {method_name} decompression")
                
                cmd_full = cmd + [str(ramdisk_path)]
                
                process = await asyncio.create_subprocess_exec(
                    *cmd_full,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                stdout, stderr = await process.communicate()
                
                if process.returncode == 0:
                    UI.info(f"Ramdisk is {method_name} format")
                    
                    cpio_process = await asyncio.create_subprocess_exec(
                        'cpio', '-i', '-d', '-m', '--no-absolute-filenames',
                        stdin=asyncio.subprocess.PIPE,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                        cwd=str(ramdisk_dir)
                    )
                    
                    await cpio_process.communicate(input=stdout)
                    
                    if cpio_process.returncode == 0:
                        UI.success("Ramdisk extracted successfully")
                        
                        with open(output_dir / 'img_info', 'a') as f:
                            f.write(f"format={method_name}\n")
                        
                        return True
                
            except Exception as e:
                continue
        
        UI.warning("Could not decompress ramdisk")
        return False