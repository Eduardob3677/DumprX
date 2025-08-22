#!/usr/bin/env python3

import os
import struct
import subprocess
import shutil
from pathlib import Path
from typing import Optional, Tuple

class BootImageUnpacker:
    def __init__(self, boot_img_path: str, output_dir: str):
        self.boot_img_path = Path(boot_img_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.header_addr = 40
        self.vndrboot = False
        
    def unpack(self) -> bool:
        try:
            shutil.copy2(self.boot_img_path, self.output_dir)
            os.chdir(self.output_dir)
            bootimg = self.boot_img_path.name
            
            offset = self._find_android_header(bootimg)
            if offset is None:
                return False
                
            if offset > 0:
                self._extract_with_offset(bootimg, offset)
            
            if self._is_vndrboot(bootimg):
                self.vndrboot = True
                
            return self._parse_boot_image(bootimg)
            
        except Exception as e:
            print(f"Error unpacking boot image: {e}")
            return False
    
    def _find_android_header(self, bootimg: str) -> Optional[int]:
        with open(bootimg, 'rb') as f:
            data = f.read()
            
        android_pos = data.find(b'ANDROID!')
        vndrboot_pos = data.find(b'VNDRBOOT')
        
        if android_pos != -1:
            return android_pos
        elif vndrboot_pos != -1:
            return vndrboot_pos
        
        return None
    
    def _extract_with_offset(self, bootimg: str, offset: int):
        with open(bootimg, 'rb') as f:
            f.seek(offset)
            data = f.read()
            
        with open('bootimg', 'wb') as f:
            f.write(data)
    
    def _is_vndrboot(self, bootimg: str) -> bool:
        with open(bootimg, 'rb') as f:
            header = f.read(8)
            return header == b'VNDRBOOT'
    
    def _parse_boot_image(self, bootimg: str) -> bool:
        try:
            with open(bootimg, 'rb') as f:
                magic = f.read(8)
                
                if magic not in [b'ANDROID!', b'VNDRBOOT']:
                    return False
                
                kernel_size = struct.unpack('<I', f.read(4))[0]
                kernel_addr = struct.unpack('<I', f.read(4))[0]
                ramdisk_size = struct.unpack('<I', f.read(4))[0]
                ramdisk_addr = struct.unpack('<I', f.read(4))[0]
                second_size = struct.unpack('<I', f.read(4))[0]
                second_addr = struct.unpack('<I', f.read(4))[0]
                tags_addr = struct.unpack('<I', f.read(4))[0]
                page_size = struct.unpack('<I', f.read(4))[0]
                
                if self.vndrboot:
                    dt_size = struct.unpack('<I', f.read(4))[0]
                    dt_addr = struct.unpack('<I', f.read(4))[0]
                else:
                    dt_size = 0
                    dt_addr = 0
                
                f.seek(8)
                name = f.read(16).rstrip(b'\x00').decode('ascii', errors='ignore')
                cmdline = f.read(512).rstrip(b'\x00').decode('ascii', errors='ignore')
                
                print(f"Boot image info:")
                print(f"  Page size: {page_size}")
                print(f"  Kernel size: {kernel_size}")
                print(f"  Ramdisk size: {ramdisk_size}")
                print(f"  Second size: {second_size}")
                if self.vndrboot:
                    print(f"  DT size: {dt_size}")
                print(f"  Name: {name}")
                print(f"  Command line: {cmdline}")
                
                self._extract_components(bootimg, page_size, kernel_size, ramdisk_size, second_size, dt_size)
                self._save_info(page_size, kernel_addr, ramdisk_addr, second_addr, tags_addr, dt_addr, name, cmdline)
                
                return True
                
        except Exception as e:
            print(f"Error parsing boot image: {e}")
            return False
    
    def _extract_components(self, bootimg: str, page_size: int, kernel_size: int, ramdisk_size: int, second_size: int, dt_size: int):
        with open(bootimg, 'rb') as f:
            offset = page_size
            
            if kernel_size > 0:
                f.seek(offset)
                kernel_data = f.read(kernel_size)
                with open('kernel', 'wb') as kernel_f:
                    kernel_f.write(kernel_data)
                offset += self._round_to_page(kernel_size, page_size)
                print("Kernel extracted")
            
            if ramdisk_size > 0:
                f.seek(offset)
                ramdisk_data = f.read(ramdisk_size)
                with open('ramdisk.cpio', 'wb') as ramdisk_f:
                    ramdisk_f.write(ramdisk_data)
                offset += self._round_to_page(ramdisk_size, page_size)
                print("Ramdisk extracted")
                
                self._decompress_ramdisk()
            
            if second_size > 0:
                f.seek(offset)
                second_data = f.read(second_size)
                with open('second', 'wb') as second_f:
                    second_f.write(second_data)
                offset += self._round_to_page(second_size, page_size)
                print("Second stage extracted")
            
            if dt_size > 0:
                f.seek(offset)
                dt_data = f.read(dt_size)
                with open('dt.img', 'wb') as dt_f:
                    dt_f.write(dt_data)
                print("Device tree extracted")
    
    def _round_to_page(self, size: int, page_size: int) -> int:
        return ((size + page_size - 1) // page_size) * page_size
    
    def _decompress_ramdisk(self):
        ramdisk_path = Path('ramdisk.cpio')
        if not ramdisk_path.exists():
            return
        
        ramdisk_dir = Path('ramdisk')
        ramdisk_dir.mkdir(exist_ok=True)
        
        with open(ramdisk_path, 'rb') as f:
            header = f.read(10)
        
        decompression_commands = [
            (['gzip', '-dc'], 'gzip'),
            (['xz', '-dc'], 'xz'),
            (['lz4', '-dc'], 'lz4'),
            (['brotli', '-dc'], 'brotli'),
            (['lzop', '-dc'], 'lzop')
        ]
        
        extracted = False
        for cmd, format_name in decompression_commands:
            try:
                with open(ramdisk_path, 'rb') as input_f:
                    process = subprocess.run(
                        cmd, 
                        stdin=input_f,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE
                    )
                    
                if process.returncode == 0:
                    with open('ramdisk_decompressed.cpio', 'wb') as output_f:
                        output_f.write(process.stdout)
                    
                    os.chdir(ramdisk_dir)
                    with open('../ramdisk_decompressed.cpio', 'rb') as cpio_f:
                        subprocess.run(['cpio', '-i'], stdin=cpio_f)
                    os.chdir('..')
                    
                    print(f"Ramdisk decompressed using {format_name}")
                    extracted = True
                    break
                    
            except FileNotFoundError:
                continue
            except Exception:
                continue
        
        if not extracted:
            try:
                os.chdir(ramdisk_dir)
                with open('../ramdisk.cpio', 'rb') as cpio_f:
                    subprocess.run(['cpio', '-i'], stdin=cpio_f)
                os.chdir('..')
                print("Ramdisk extracted without decompression")
            except Exception:
                print("Failed to extract ramdisk")
    
    def _save_info(self, page_size: int, kernel_addr: int, ramdisk_addr: int, second_addr: int, tags_addr: int, dt_addr: int, name: str, cmdline: str):
        info_content = f"""page_size={page_size}
kernel_addr=0x{kernel_addr:08x}
ramdisk_addr=0x{ramdisk_addr:08x}
second_addr=0x{second_addr:08x}
tags_addr=0x{tags_addr:08x}
"""
        
        if dt_addr > 0:
            info_content += f"dt_addr=0x{dt_addr:08x}\n"
        
        if name:
            info_content += f"name={name}\n"
        
        if cmdline:
            info_content += f"cmdline={cmdline}\n"
        
        with open('img_info', 'w') as f:
            f.write(info_content)

def main():
    import sys
    
    if len(sys.argv) != 3:
        print("Usage: unpackboot.py <boot.img> <output_dir>")
        print("Example: unpackboot.py boot.img boot_extracted")
        sys.exit(1)
    
    boot_img_path = sys.argv[1]
    output_dir = sys.argv[2]
    
    if not Path(boot_img_path).exists():
        print(f"Error: Boot image not found: {boot_img_path}")
        sys.exit(1)
    
    unpacker = BootImageUnpacker(boot_img_path, output_dir)
    
    print(f"Unpacking {boot_img_path} to {output_dir}")
    
    if unpacker.unpack():
        print("Unpack completed.")
    else:
        print("Unpack failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()