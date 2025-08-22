#!/usr/bin/env python3

import os
import struct
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

from rich.console import Console

from .utils import run_command

console = Console()

class BootImageUnpacker:
    def __init__(self):
        self.ANDROID_MAGIC = b'ANDROID!'
        self.VNDRBOOT_MAGIC = b'VNDRBOOT'
        self.MTK_MAGIC = 0x58881688
    
    def unpack_boot_image(self, boot_img: Path, output_dir: Path) -> bool:
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
            
            console.print(f"[blue]Unpacking {boot_img.name} to {output_dir}[/blue]")
            
            # Copy boot image to output directory
            boot_copy = output_dir / boot_img.name
            import shutil
            shutil.copy2(boot_img, boot_copy)
            
            os.chdir(output_dir)
            
            # Find Android/VNDRBOOT offset
            offset = self._find_boot_offset(boot_copy)
            if offset is None:
                console.print("[red]No valid boot image magic found[/red]")
                return False
            
            # Extract boot image if offset > 0
            if offset > 0:
                self._extract_boot_at_offset(boot_copy, offset)
                boot_copy = output_dir / "bootimg"
            
            # Parse boot header
            header_info = self._parse_boot_header(boot_copy)
            if not header_info:
                return False
            
            # Extract components
            self._extract_boot_components(boot_copy, header_info, output_dir)
            
            # Unpack ramdisk
            self._unpack_ramdisk(output_dir, header_info)
            
            # Write boot info
            self._write_boot_info(output_dir, header_info)
            
            console.print("[green]Boot image unpacked successfully[/green]")
            return True
            
        except Exception as e:
            console.print(f"[red]Error unpacking boot image: {e}[/red]")
            return False
    
    def _find_boot_offset(self, boot_img: Path) -> Optional[int]:
        with open(boot_img, 'rb') as f:
            data = f.read()
            
            android_offset = data.find(self.ANDROID_MAGIC)
            vndrboot_offset = data.find(self.VNDRBOOT_MAGIC)
            
            if android_offset != -1:
                return android_offset
            elif vndrboot_offset != -1:
                return vndrboot_offset
            
            return None
    
    def _extract_boot_at_offset(self, boot_img: Path, offset: int):
        with open(boot_img, 'rb') as infile:
            infile.seek(offset)
            with open("bootimg", 'wb') as outfile:
                outfile.write(infile.read())
    
    def _parse_boot_header(self, boot_img: Path) -> Optional[Dict[str, Any]]:
        try:
            with open(boot_img, 'rb') as f:
                # Check magic
                magic = f.read(8)
                is_vndrboot = magic.startswith(self.VNDRBOOT_MAGIC)
                
                f.seek(0)
                
                # Read header based on type
                if is_vndrboot:
                    return self._parse_vndrboot_header(f)
                else:
                    return self._parse_android_header(f)
                    
        except Exception as e:
            console.print(f"[red]Error parsing boot header: {e}[/red]")
            return None
    
    def _parse_android_header(self, f) -> Dict[str, Any]:
        # Android boot image header structure
        f.seek(0)
        header_data = f.read(1648)
        
        # Parse basic header
        magic = header_data[0:8]
        kernel_size = struct.unpack('<I', header_data[8:12])[0]
        kernel_addr = struct.unpack('<I', header_data[12:16])[0]
        ramdisk_size = struct.unpack('<I', header_data[16:20])[0]
        ramdisk_addr = struct.unpack('<I', header_data[20:24])[0]
        second_size = struct.unpack('<I', header_data[24:28])[0]
        second_addr = struct.unpack('<I', header_data[28:32])[0]
        tags_addr = struct.unpack('<I', header_data[32:36])[0]
        page_size = struct.unpack('<I', header_data[36:40])[0]
        
        # Header version (at offset 40 for v1+)
        version = 0
        if len(header_data) > 40:
            version = struct.unpack('<I', header_data[40:44])[0]
        
        # DTB info for v2+
        dtb_size = 0
        dtb_addr = 0
        if version >= 2 and len(header_data) > 1648:
            dtb_size = struct.unpack('<I', header_data[1648:1652])[0]
            dtb_addr = struct.unpack('<I', header_data[1652:1656])[0]
        
        # DTBO info for v1+
        dtbo_size = 0
        dtbo_addr = 0
        if version >= 1 and len(header_data) > 1632:
            dtbo_size = struct.unpack('<I', header_data[1632:1636])[0]
            if dtbo_size > 0:
                dtbo_addr = struct.unpack('<I', header_data[1636:1640])[0]
        
        # Command line and board name
        cmdline = header_data[64:576].rstrip(b'\x00').decode('ascii', errors='ignore')
        board = header_data[48:64].rstrip(b'\x00').decode('ascii', errors='ignore')
        
        # OS version for v3+
        os_version = ""
        patch_level = ""
        if version >= 3:
            os_version_raw = struct.unpack('<I', header_data[16:20])[0]
            if os_version_raw > 0:
                patch_level = os_version_raw & ((1 << 11) - 1)
                os_version_raw >>= 11
                
                os_patch_year = (patch_level >> 4) + 2000
                os_patch_month = patch_level & ((1 << 4) - 1)
                patch_level = f"{os_patch_year}:{os_patch_month:02d}"
                
                os_a = (os_version_raw >> 14) & ((1 << 7) - 1)
                os_b = (os_version_raw >> 7) & ((1 << 7) - 1) 
                os_c = os_version_raw & ((1 << 7) - 1)
                os_version = f"{os_a}.{os_b}.{os_c}"
        
        return {
            'magic': magic,
            'kernel_size': kernel_size,
            'kernel_addr': kernel_addr,
            'ramdisk_size': ramdisk_size,
            'ramdisk_addr': ramdisk_addr,
            'second_size': second_size,
            'second_addr': second_addr,
            'tags_addr': tags_addr,
            'page_size': page_size,
            'version': version,
            'dtb_size': dtb_size,
            'dtb_addr': dtb_addr,
            'dtbo_size': dtbo_size,
            'dtbo_addr': dtbo_addr,
            'cmdline': cmdline,
            'board': board,
            'os_version': os_version,
            'patch_level': patch_level,
            'is_vndrboot': False
        }
    
    def _parse_vndrboot_header(self, f) -> Dict[str, Any]:
        # VNDRBOOT header is different
        f.seek(0)
        header_data = f.read(2112)
        
        version = struct.unpack('<I', header_data[8:12])[0]
        kernel_addr = struct.unpack('<I', header_data[16:20])[0]
        ramdisk_addr = struct.unpack('<I', header_data[20:24])[0]
        ramdisk_size = struct.unpack('<I', header_data[24:28])[0]
        cmdline = header_data[28:2076].rstrip(b'\x00').decode('ascii', errors='ignore')
        tags_addr = struct.unpack('<I', header_data[2076:2080])[0]
        page_size = 4096  # Fixed for v3+
        dtb_size = struct.unpack('<I', header_data[2100:2104])[0]
        dtb_addr = struct.unpack('<I', header_data[2104:2108])[0]
        
        return {
            'kernel_size': 0,
            'kernel_addr': kernel_addr,
            'ramdisk_size': ramdisk_size,
            'ramdisk_addr': ramdisk_addr,
            'second_size': 0,
            'second_addr': 0,
            'tags_addr': tags_addr,
            'page_size': page_size,
            'version': version,
            'dtb_size': dtb_size,
            'dtb_addr': dtb_addr,
            'dtbo_size': 0,
            'dtbo_addr': 0,
            'cmdline': cmdline,
            'board': '',
            'os_version': '',
            'patch_level': '',
            'is_vndrboot': True
        }
    
    def _extract_boot_components(self, boot_img: Path, header: Dict[str, Any], output_dir: Path):
        page_size = header['page_size']
        
        # Calculate page counts and offsets
        k_count = (header['kernel_size'] + page_size - 1) // page_size
        r_count = (header['ramdisk_size'] + page_size - 1) // page_size
        s_count = (header['second_size'] + page_size - 1) // page_size
        d_count = (header['dtb_size'] + page_size - 1) // page_size
        do_count = (header['dtbo_size'] + page_size - 1) // page_size
        
        k_offset = 1
        r_offset = k_offset + k_count
        s_offset = r_offset + r_count
        do_offset = s_offset + s_count
        d_offset = do_offset + do_count
        
        with open(boot_img, 'rb') as f:
            # Extract kernel
            if header['kernel_size'] > 0:
                f.seek(k_offset * page_size)
                kernel_data = f.read(k_count * page_size)[:header['kernel_size']]
                with open(output_dir / "kernel", 'wb') as kernel_file:
                    kernel_file.write(kernel_data)
            
            # Extract ramdisk
            if header['ramdisk_size'] > 0:
                f.seek(r_offset * page_size)
                ramdisk_data = f.read(r_count * page_size)[:header['ramdisk_size']]
                with open(output_dir / "ramdisk.packed", 'wb') as ramdisk_file:
                    ramdisk_file.write(ramdisk_data)
            
            # Extract second stage
            if header['second_size'] > 0:
                f.seek(s_offset * page_size)
                second_data = f.read(s_count * page_size)[:header['second_size']]
                with open(output_dir / "second.img", 'wb') as second_file:
                    second_file.write(second_data)
            
            # Extract DTB
            if header['dtb_size'] > 0:
                f.seek(d_offset * page_size)
                dtb_data = f.read(d_count * page_size)[:header['dtb_size']]
                dtb_name = "dtb.img" if header['version'] > 1 else "dt.img"
                with open(output_dir / dtb_name, 'wb') as dtb_file:
                    dtb_file.write(dtb_data)
            
            # Extract DTBO
            if header['dtbo_size'] > 0:
                f.seek(do_offset * page_size)
                dtbo_data = f.read(do_count * page_size)[:header['dtbo_size']]
                with open(output_dir / "dtbo.img", 'wb') as dtbo_file:
                    dtbo_file.write(dtbo_data)
    
    def _unpack_ramdisk(self, output_dir: Path, header: Dict[str, Any]):
        ramdisk_packed = output_dir / "ramdisk.packed"
        if not ramdisk_packed.exists():
            return
        
        # Check for MTK header
        mtk_info = self._check_mtk_header(ramdisk_packed)
        if mtk_info:
            console.print("[blue]Ramdisk has MTK header[/blue]")
            self._extract_mtk_ramdisk(ramdisk_packed, mtk_info)
        
        # Create ramdisk directory
        ramdisk_dir = output_dir / "ramdisk"
        ramdisk_dir.mkdir(exist_ok=True)
        
        os.chdir(ramdisk_dir)
        
        # Try different compression formats
        ramdisk_file = "../ramdisk.packed"
        
        # Try gzip
        if self._try_decompress("gzip", ramdisk_file):
            return
        
        # Try lzma
        if self._try_decompress("lzma", ramdisk_file):
            return
        
        # Try xz
        if self._try_decompress("xz", ramdisk_file):
            return
        
        # Try lzop
        if self._try_decompress("lzop", ramdisk_file):
            return
        
        # Try lz4
        if self._try_decompress("lz4", ramdisk_file):
            return
        
        console.print("[yellow]Unknown ramdisk compression format[/yellow]")
    
    def _check_mtk_header(self, ramdisk_packed: Path) -> Optional[Dict[str, Any]]:
        with open(ramdisk_packed, 'rb') as f:
            header = f.read(512)
            if len(header) >= 8:
                magic = struct.unpack('<I', header[0:4])[0]
                if magic == self.MTK_MAGIC:
                    partition_size = struct.unpack('<I', header[4:8])[0]
                    partition_name = header[8:40].rstrip(b'\x00').decode('ascii', errors='ignore')
                    return {
                        'partition_size': partition_size,
                        'partition_name': partition_name
                    }
        return None
    
    def _extract_mtk_ramdisk(self, ramdisk_packed: Path, mtk_info: Dict[str, Any]):
        # Save MTK header
        with open(ramdisk_packed, 'rb') as infile:
            header = infile.read(512)
            with open(ramdisk_packed.parent / "ramdisk.mtk_header", 'wb') as outfile:
                outfile.write(header)
        
        # Extract ramdisk without header
        with open(ramdisk_packed, 'rb') as infile:
            infile.seek(512)
            with open(ramdisk_packed.parent / "ramdisk.packed.new", 'wb') as outfile:
                outfile.write(infile.read())
        
        # Replace original
        ramdisk_packed.unlink()
        (ramdisk_packed.parent / "ramdisk.packed.new").rename(ramdisk_packed)
    
    def _try_decompress(self, format_name: str, ramdisk_file: str) -> bool:
        try:
            if format_name == "gzip":
                cmd = ["sh", "-c", f"gzip -dc {ramdisk_file} | cpio -i -d -m --no-absolute-filenames"]
            elif format_name == "lzma":
                cmd = ["sh", "-c", f"lzma -dc {ramdisk_file} | cpio -i -d -m --no-absolute-filenames"]
            elif format_name == "xz":
                cmd = ["sh", "-c", f"xz -dc {ramdisk_file} | cpio -i -d -m --no-absolute-filenames"]
            elif format_name == "lzop":
                cmd = ["sh", "-c", f"lzop -dc {ramdisk_file} | cpio -i -d -m --no-absolute-filenames"]
            elif format_name == "lz4":
                cmd = ["sh", "-c", f"lz4 -dc {ramdisk_file} | cpio -i -d -m --no-absolute-filenames"]
            else:
                return False
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                console.print(f"[green]Ramdisk is {format_name} format[/green]")
                return True
        except:
            pass
        
        return False
    
    def _write_boot_info(self, output_dir: Path, header: Dict[str, Any]):
        info_file = output_dir / "img_info"
        
        # Calculate offsets
        base_addr = header['kernel_addr'] - 0x00008000
        kernel_offset = header['kernel_addr'] - base_addr
        ramdisk_offset = header['ramdisk_addr'] - base_addr
        second_offset = header['second_addr'] - base_addr
        tags_offset = header['tags_addr'] - base_addr
        dtbo_offset = header['dtbo_addr'] - base_addr
        dtb_offset = header['dtb_addr'] - base_addr
        
        # Format as hex
        base_addr_hex = f"0x{base_addr:08x}"
        kernel_offset_hex = f"0x{kernel_offset:08x}"
        ramdisk_offset_hex = f"0x{ramdisk_offset:08x}"
        second_offset_hex = f"0x{second_offset:08x}"
        tags_offset_hex = f"0x{tags_offset:08x}"
        dtbo_offset_hex = f"0x{dtbo_offset:08x}"
        dtb_offset_hex = f"0x{dtb_offset:08x}"
        
        # Build info content
        info_lines = []
        
        if not header['is_vndrboot']:
            info_lines.append("kernel=kernel")
        info_lines.append("ramdisk=ramdisk")
        
        if header['second_size'] > 0:
            info_lines.append("second=second.img")
        
        info_lines.append(f"page_size={header['page_size']}")
        
        if header['dtbo_size'] > 0:
            info_lines.append("dtbo=dtbo.img")
        
        if header['dtb_size'] > 0:
            dtb_name = "dtb.img" if header['version'] > 1 else "dt.img"
            info_lines.append(f"dt={dtb_name}")
        
        if not header['is_vndrboot']:
            info_lines.append(f"kernel_size={header['kernel_size']}")
        info_lines.append(f"ramdisk_size={header['ramdisk_size']}")
        
        if header['second_size'] > 0:
            info_lines.append(f"second_size={header['second_size']}")
        
        if header['dtb_size'] > 0:
            info_lines.append(f"dtb_size={header['dtb_size']}")
        
        info_lines.append(f"base_addr={base_addr_hex}")
        
        if not header['is_vndrboot']:
            info_lines.append(f"kernel_offset={kernel_offset_hex}")
        info_lines.append(f"ramdisk_offset={ramdisk_offset_hex}")
        info_lines.append(f"tags_offset={tags_offset_hex}")
        
        if header['dtbo_size'] > 0:
            info_lines.append(f"dtbo_offset={dtbo_offset_hex}")
        
        if header['dtb_size'] > 0 and header['version'] > 1:
            info_lines.append(f"dtb_offset={dtb_offset_hex}")
        
        if header['second_size'] > 0:
            info_lines.append(f"second_offset={second_offset_hex}")
        
        if header['os_version']:
            info_lines.append(f"os_version={header['os_version']}")
            info_lines.append(f"os_patch_level={header['patch_level']}")
        
        # Escape command line properly
        escaped_cmdline = header['cmdline'].replace("'", "'\"'\"'")
        info_lines.append(f"cmd_line='{escaped_cmdline}'")
        
        if header['board']:
            info_lines.append(f'board="{header["board"]}"')
        
        # Write to file
        with open(info_file, 'w') as f:
            f.write('\n'.join(info_lines) + '\n')
        
        # Print summary
        if header['board']:
            console.print(f"  board               : {header['board']}")
        
        if not header['is_vndrboot']:
            console.print(f"  kernel              : kernel")
        console.print(f"  ramdisk             : ramdisk")
        console.print(f"  page size           : {header['page_size']}")
        
        if not header['is_vndrboot']:
            console.print(f"  kernel size         : {header['kernel_size']}")
        console.print(f"  ramdisk size        : {header['ramdisk_size']}")
        
        if header['second_size'] > 0:
            console.print(f"  second_size         : {header['second_size']}")
        
        console.print(f"  base                : {base_addr_hex}")
        
        if not header['is_vndrboot']:
            console.print(f"  kernel offset       : {kernel_offset_hex}")
        console.print(f"  ramdisk offset      : {ramdisk_offset_hex}")
        
        if header['version'] > 0 and header['dtbo_size'] > 0:
            console.print(f"  boot header version : {header['version']}")
            console.print(f"  dtbo                : dtbo.img")
            console.print(f"  dtbo size           : {header['dtbo_size']}")
            console.print(f"  dtbo offset         : {dtbo_offset_hex}")
        
        if header['dtb_size'] > 0:
            dtb_name = "dtb.img" if header['version'] > 1 else "dt.img"
            console.print(f"  dtb img             : {dtb_name}")
            console.print(f"  dtb size            : {header['dtb_size']}")
            
            if header['version'] > 1:
                console.print(f"  dtb offset          : {dtb_offset_hex}")
        
        if header['second_size'] > 0:
            console.print(f"  second_offset       : {second_offset_hex}")
        
        if header['os_version']:
            console.print(f"  os_version          : {header['os_version']}")
            console.print(f"  os_patch_level      : {header['patch_level']}")
        
        console.print(f"  tags offset         : {tags_offset_hex}")
        console.print(f"  cmd line            : {header['cmdline']}")