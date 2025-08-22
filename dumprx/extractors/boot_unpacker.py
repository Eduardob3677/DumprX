import os
import struct
import shutil
from pathlib import Path
from typing import Tuple, Optional
from rich.console import Console

console = Console()

class BootImageUnpacker:
    def __init__(self, config):
        self.config = config
    
    def unpack_boot_image(self, boot_img_path: Path, output_dir: Path) -> bool:
        try:
            console.print(f"[blue]🥾 Unpacking boot image: {boot_img_path.name}[/blue]")
            
            output_dir.mkdir(parents=True, exist_ok=True)
            
            shutil.copy2(boot_img_path, output_dir / boot_img_path.name)
            os.chdir(output_dir)
            
            bootimg = boot_img_path.name
            
            offset = self._find_android_header(bootimg)
            if offset is None:
                console.print("[red]❌ Android boot header not found[/red]")
                return False
            
            if offset > 0:
                console.print(f"[yellow]⚠️  Boot header found at offset {offset}[/yellow]")
                with open(bootimg, 'rb') as f:
                    f.seek(offset)
                    data = f.read()
                with open('bootimg', 'wb') as f:
                    f.write(data)
                bootimg = 'bootimg'
            
            header_info = self._parse_boot_header(bootimg)
            if not header_info:
                console.print("[red]❌ Failed to parse boot header[/red]")
                return False
            
            self._extract_boot_components(bootimg, header_info, output_dir)
            self._write_boot_info(header_info, output_dir)
            
            console.print("[green]✅ Boot image unpacked successfully[/green]")
            return True
            
        except Exception as e:
            console.print(f"[red]💥 Boot unpacking failed: {str(e)}[/red]")
            return False
    
    def _find_android_header(self, bootimg: str) -> Optional[int]:
        try:
            with open(bootimg, 'rb') as f:
                data = f.read(8192)  # Read first 8KB
                
                android_pos = data.find(b'ANDROID!')
                if android_pos != -1:
                    return android_pos
                
                vndrboot_pos = data.find(b'VNDRBOOT')
                if vndrboot_pos != -1:
                    return vndrboot_pos
                
            return None
        except Exception:
            return None
    
    def _parse_boot_header(self, bootimg: str) -> Optional[dict]:
        try:
            with open(bootimg, 'rb') as f:
                magic = f.read(8)
                
                is_vndrboot = magic == b'VNDRBOOT'
                
                if magic not in [b'ANDROID!', b'VNDRBOOT']:
                    return None
                
                kernel_size = struct.unpack('<I', f.read(4))[0]
                kernel_addr = struct.unpack('<I', f.read(4))[0]
                ramdisk_size = struct.unpack('<I', f.read(4))[0]
                ramdisk_addr = struct.unpack('<I', f.read(4))[0]
                second_size = struct.unpack('<I', f.read(4))[0]
                second_addr = struct.unpack('<I', f.read(4))[0]
                tags_addr = struct.unpack('<I', f.read(4))[0]
                page_size = struct.unpack('<I', f.read(4))[0]
                
                if is_vndrboot:
                    version = struct.unpack('<I', f.read(4))[0]
                    f.read(4)  # skip reserved
                    dtb_size = struct.unpack('<I', f.read(4))[0]
                    dtb_addr = struct.unpack('<I', f.read(8))[0]  # 64-bit
                else:
                    version = struct.unpack('<I', f.read(4))[0] if f.tell() < 36 else 0
                    dtbo_size = struct.unpack('<I', f.read(4))[0] if version > 0 else 0
                    dtbo_addr = struct.unpack('<Q', f.read(8))[0] if version > 0 else 0
                    dtb_size = struct.unpack('<I', f.read(4))[0] if version > 1 else 0
                    dtb_addr = struct.unpack('<Q', f.read(8))[0] if version > 1 else 0
                
                f.seek(64)  # Skip to name field
                product_name = f.read(16).decode('ascii', errors='ignore').rstrip('\0')
                cmdline = f.read(512).decode('ascii', errors='ignore').rstrip('\0')
                
                return {
                    'is_vndrboot': is_vndrboot,
                    'kernel_size': kernel_size,
                    'kernel_addr': kernel_addr,
                    'ramdisk_size': ramdisk_size,
                    'ramdisk_addr': ramdisk_addr,
                    'second_size': second_size,
                    'second_addr': second_addr,
                    'tags_addr': tags_addr,
                    'page_size': page_size,
                    'version': version,
                    'dtbo_size': dtbo_size if not is_vndrboot else 0,
                    'dtbo_addr': dtbo_addr if not is_vndrboot else 0,
                    'dtb_size': dtb_size,
                    'dtb_addr': dtb_addr,
                    'product_name': product_name,
                    'cmdline': cmdline
                }
                
        except Exception as e:
            console.print(f"[red]💥 Header parsing failed: {str(e)}[/red]")
            return None
    
    def _extract_boot_components(self, bootimg: str, header: dict, output_dir: Path):
        page_size = header['page_size']
        
        def align_size(size, alignment):
            return (size + alignment - 1) // alignment * alignment
        
        kernel_offset = page_size
        ramdisk_offset = kernel_offset + align_size(header['kernel_size'], page_size)
        second_offset = ramdisk_offset + align_size(header['ramdisk_size'], page_size)
        dtbo_offset = second_offset + align_size(header['second_size'], page_size)
        dtb_offset = dtbo_offset + align_size(header.get('dtbo_size', 0), page_size)
        
        with open(bootimg, 'rb') as f:
            if header['kernel_size'] > 0:
                f.seek(kernel_offset)
                kernel_data = f.read(header['kernel_size'])
                with open(output_dir / 'kernel', 'wb') as kf:
                    kf.write(kernel_data)
                console.print("[cyan]📦 Extracted kernel[/cyan]")
            
            if header['ramdisk_size'] > 0:
                f.seek(ramdisk_offset)
                ramdisk_data = f.read(header['ramdisk_size'])
                with open(output_dir / 'ramdisk.cpio', 'wb') as rf:
                    rf.write(ramdisk_data)
                console.print("[cyan]📦 Extracted ramdisk[/cyan]")
                
                self._decompress_ramdisk(output_dir / 'ramdisk.cpio', output_dir)
            
            if header['second_size'] > 0:
                f.seek(second_offset)
                second_data = f.read(header['second_size'])
                with open(output_dir / 'second', 'wb') as sf:
                    sf.write(second_data)
                console.print("[cyan]📦 Extracted second stage[/cyan]")
            
            if header.get('dtbo_size', 0) > 0:
                f.seek(dtbo_offset)
                dtbo_data = f.read(header['dtbo_size'])
                with open(output_dir / 'dtbo', 'wb') as df:
                    df.write(dtbo_data)
                console.print("[cyan]📦 Extracted DTBO[/cyan]")
            
            if header['dtb_size'] > 0:
                f.seek(dtb_offset)
                dtb_data = f.read(header['dtb_size'])
                with open(output_dir / 'dt', 'wb') as df:
                    df.write(dtb_data)
                console.print("[cyan]📦 Extracted DTB[/cyan]")
    
    def _decompress_ramdisk(self, ramdisk_file: Path, output_dir: Path):
        try:
            ramdisk_dir = output_dir / 'ramdisk'
            ramdisk_dir.mkdir(exist_ok=True)
            
            import subprocess
            
            with open(ramdisk_file, 'rb') as f:
                header = f.read(10)
            
            if header[:3] == b'\x1f\x8b\x08':  # gzip
                cmd = ['gunzip', '-c', str(ramdisk_file)]
            elif header[:6] == b'\xfd7zXZ\x00':  # xz
                cmd = ['xz', '-dc', str(ramdisk_file)]
            elif header[:4] == b'\x04"M\x18':  # lz4
                cmd = ['lz4', '-dc', str(ramdisk_file)]
            elif header[:3] == b'BZh':  # bzip2
                cmd = ['bzip2', '-dc', str(ramdisk_file)]
            else:
                cmd = ['cat', str(ramdisk_file)]
            
            with open(output_dir / 'ramdisk.cpio.decompressed', 'wb') as out_file:
                subprocess.run(cmd, stdout=out_file, check=True)
            
            os.chdir(ramdisk_dir)
            with open(output_dir / 'ramdisk.cpio.decompressed', 'rb') as cpio_file:
                subprocess.run(['cpio', '-i'], stdin=cpio_file, check=True)
            
            console.print("[cyan]📦 Decompressed and extracted ramdisk[/cyan]")
            
        except Exception as e:
            console.print(f"[yellow]⚠️  Ramdisk decompression failed: {str(e)}[/yellow]")
    
    def _write_boot_info(self, header: dict, output_dir: Path):
        try:
            base_addr = header['kernel_addr'] - 0x00008000
            kernel_offset = header['kernel_addr'] - base_addr
            ramdisk_offset = header['ramdisk_addr'] - base_addr
            second_offset = header['second_addr'] - base_addr
            tags_offset = header['tags_addr'] - base_addr
            dtbo_offset = header.get('dtbo_addr', 0) - base_addr if header.get('dtbo_addr', 0) else 0
            dtb_offset = header['dtb_addr'] - base_addr if header['dtb_addr'] else 0
            
            info_content = f"""base address: 0x{base_addr:08x}
kernel offset: 0x{kernel_offset:08x}
ramdisk offset: 0x{ramdisk_offset:08x}
second offset: 0x{second_offset:08x}
tags offset: 0x{tags_offset:08x}
"""
            
            if header.get('dtbo_size', 0) > 0:
                info_content += f"dtbo offset: 0x{dtbo_offset:08x}\\n"
            
            if header['dtb_size'] > 0:
                info_content += f"dtb offset: 0x{dtb_offset:08x}\\n"
            
            info_content += f"""page size: {header['page_size']}
kernel size: {header['kernel_size']}
ramdisk size: {header['ramdisk_size']}
"""
            
            if header['second_size'] > 0:
                info_content += f"second size: {header['second_size']}\\n"
            
            if header.get('dtbo_size', 0) > 0:
                info_content += f"dtbo size: {header['dtbo_size']}\\n"
            
            if header['dtb_size'] > 0:
                info_content += f"dtb size: {header['dtb_size']}\\n"
            
            info_content += f"""boot header version: {header['version']}
product name: {header['product_name']}
command line: {header['cmdline']}
"""
            
            (output_dir / 'img_info').write_text(info_content)
            
        except Exception as e:
            console.print(f"[yellow]⚠️  Failed to write boot info: {str(e)}[/yellow]")