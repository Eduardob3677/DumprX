import struct
import os
from pathlib import Path
from typing import Dict, Optional, Tuple
from rich.console import Console


class BootImageUnpacker:
    def __init__(self, console: Console):
        self.console = console
    
    def unpack(self, boot_img_path: Path, output_dir: Path) -> bool:
        if not boot_img_path.exists():
            self.console.print(f"[red]Boot image not found: {boot_img_path}[/red]")
            return False
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(boot_img_path, 'rb') as f:
                # Read the header to detect format
                header = f.read(2048)
                
                if b'ANDROID!' in header:
                    return self._unpack_android_boot(boot_img_path, output_dir)
                elif b'VNDRBOOT' in header:
                    return self._unpack_vndr_boot(boot_img_path, output_dir)
                else:
                    self.console.print("[red]Unknown boot image format[/red]")
                    return False
                    
        except Exception as e:
            self.console.print(f"[red]Error reading boot image: {e}[/red]")
            return False
    
    def _unpack_android_boot(self, boot_img_path: Path, output_dir: Path) -> bool:
        self.console.print("[blue]Unpacking Android boot image[/blue]")
        
        with open(boot_img_path, 'rb') as f:
            # Find the actual start of the boot image
            offset = self._find_boot_magic(f)
            if offset is None:
                return False
            
            f.seek(offset)
            
            # Read Android boot header
            header = f.read(2048)
            if len(header) < 2048:
                self.console.print("[red]Boot image header too short[/red]")
                return False
            
            # Parse header
            boot_info = self._parse_android_header(header, offset)
            
            # Extract kernel
            self._extract_kernel(f, boot_info, output_dir)
            
            # Extract ramdisk
            self._extract_ramdisk(f, boot_info, output_dir)
            
            # Extract second stage (if present)
            if boot_info['second_size'] > 0:
                self._extract_second(f, boot_info, output_dir)
            
            # Extract device tree (if present)
            if boot_info['dtb_size'] > 0:
                self._extract_dtb(f, boot_info, output_dir)
            
            # Write boot info
            self._write_boot_info(boot_info, output_dir)
            
            return True
    
    def _find_boot_magic(self, f) -> Optional[int]:
        f.seek(0)
        data = f.read(4096)
        
        android_magic = b'ANDROID!'
        vndr_magic = b'VNDRBOOT'
        
        for magic in [android_magic, vndr_magic]:
            offset = data.find(magic)
            if offset != -1:
                return offset
        
        return None
    
    def _parse_android_header(self, header: bytes, offset: int) -> Dict:
        # Android boot image header structure
        magic = header[0:8]
        kernel_size = struct.unpack('<I', header[8:12])[0]
        kernel_addr = struct.unpack('<I', header[12:16])[0]
        ramdisk_size = struct.unpack('<I', header[16:20])[0]
        ramdisk_addr = struct.unpack('<I', header[20:24])[0]
        second_size = struct.unpack('<I', header[24:28])[0]
        second_addr = struct.unpack('<I', header[28:32])[0]
        tags_addr = struct.unpack('<I', header[32:36])[0]
        page_size = struct.unpack('<I', header[36:40])[0]
        
        # Version and other fields
        version = 0
        if len(header) >= 44:
            version = struct.unpack('<I', header[40:44])[0]
        
        # Command line and board name
        cmd_line = header[64:576].rstrip(b'\x00').decode('utf-8', errors='ignore')
        board = header[48:64].rstrip(b'\x00').decode('utf-8', errors='ignore')
        
        # DTB info (version 1+)
        dtb_size = 0
        dtb_addr = 0
        if len(header) >= 648:
            dtb_size = struct.unpack('<I', header[640:644])[0]
            dtb_addr = struct.unpack('<I', header[644:648])[0]
        
        # Calculate offsets
        base_addr = kernel_addr - 0x00008000
        kernel_offset = kernel_addr - base_addr
        ramdisk_offset = ramdisk_addr - base_addr
        second_offset = second_addr - base_addr
        tags_offset = tags_addr - base_addr
        dtb_offset = dtb_addr - base_addr if dtb_addr else 0
        
        return {
            'magic': magic.decode('utf-8', errors='ignore'),
            'kernel_size': kernel_size,
            'kernel_addr': kernel_addr,
            'ramdisk_size': ramdisk_size,
            'ramdisk_addr': ramdisk_addr,
            'second_size': second_size,
            'second_addr': second_addr,
            'tags_addr': tags_addr,
            'page_size': page_size,
            'version': version,
            'cmd_line': cmd_line,
            'board': board,
            'dtb_size': dtb_size,
            'dtb_addr': dtb_addr,
            'base_addr': base_addr,
            'kernel_offset': kernel_offset,
            'ramdisk_offset': ramdisk_offset,
            'second_offset': second_offset,
            'tags_offset': tags_offset,
            'dtb_offset': dtb_offset,
            'header_offset': offset
        }
    
    def _extract_kernel(self, f, boot_info: Dict, output_dir: Path) -> None:
        if boot_info['kernel_size'] == 0:
            return
        
        page_size = boot_info['page_size']
        kernel_pages = (boot_info['kernel_size'] + page_size - 1) // page_size
        
        # Seek to kernel start (after header)
        f.seek(boot_info['header_offset'] + page_size)
        
        kernel_data = f.read(kernel_pages * page_size)
        kernel_data = kernel_data[:boot_info['kernel_size']]
        
        kernel_path = output_dir / "kernel"
        with open(kernel_path, 'wb') as kf:
            kf.write(kernel_data)
        
        self.console.print(f"[green]✓ Extracted kernel ({boot_info['kernel_size']} bytes)[/green]")
    
    def _extract_ramdisk(self, f, boot_info: Dict, output_dir: Path) -> None:
        if boot_info['ramdisk_size'] == 0:
            return
        
        page_size = boot_info['page_size']
        kernel_pages = (boot_info['kernel_size'] + page_size - 1) // page_size
        ramdisk_pages = (boot_info['ramdisk_size'] + page_size - 1) // page_size
        
        # Seek to ramdisk start
        ramdisk_offset = boot_info['header_offset'] + page_size + (kernel_pages * page_size)
        f.seek(ramdisk_offset)
        
        ramdisk_data = f.read(ramdisk_pages * page_size)
        ramdisk_data = ramdisk_data[:boot_info['ramdisk_size']]
        
        ramdisk_path = output_dir / "ramdisk.packed"
        with open(ramdisk_path, 'wb') as rf:
            rf.write(ramdisk_data)
        
        self.console.print(f"[green]✓ Extracted ramdisk ({boot_info['ramdisk_size']} bytes)[/green]")
        
        # Try to decompress ramdisk
        self._decompress_ramdisk(ramdisk_path, output_dir)
    
    def _extract_second(self, f, boot_info: Dict, output_dir: Path) -> None:
        if boot_info['second_size'] == 0:
            return
        
        page_size = boot_info['page_size']
        kernel_pages = (boot_info['kernel_size'] + page_size - 1) // page_size
        ramdisk_pages = (boot_info['ramdisk_size'] + page_size - 1) // page_size
        second_pages = (boot_info['second_size'] + page_size - 1) // page_size
        
        # Seek to second stage start
        second_offset = boot_info['header_offset'] + page_size + (kernel_pages * page_size) + (ramdisk_pages * page_size)
        f.seek(second_offset)
        
        second_data = f.read(second_pages * page_size)
        second_data = second_data[:boot_info['second_size']]
        
        second_path = output_dir / "second"
        with open(second_path, 'wb') as sf:
            sf.write(second_data)
        
        self.console.print(f"[green]✓ Extracted second stage ({boot_info['second_size']} bytes)[/green]")
    
    def _extract_dtb(self, f, boot_info: Dict, output_dir: Path) -> None:
        if boot_info['dtb_size'] == 0:
            return
        
        page_size = boot_info['page_size']
        kernel_pages = (boot_info['kernel_size'] + page_size - 1) // page_size
        ramdisk_pages = (boot_info['ramdisk_size'] + page_size - 1) // page_size
        second_pages = (boot_info['second_size'] + page_size - 1) // page_size
        
        # Seek to DTB start
        dtb_offset = boot_info['header_offset'] + page_size + (kernel_pages * page_size) + (ramdisk_pages * page_size) + (second_pages * page_size)
        f.seek(dtb_offset)
        
        dtb_data = f.read(boot_info['dtb_size'])
        
        dtb_path = output_dir / "dtb"
        with open(dtb_path, 'wb') as df:
            df.write(dtb_data)
        
        self.console.print(f"[green]✓ Extracted device tree ({boot_info['dtb_size']} bytes)[/green]")
    
    def _decompress_ramdisk(self, ramdisk_path: Path, output_dir: Path) -> None:
        import subprocess
        import gzip
        import lzma
        
        ramdisk_dir = output_dir / "ramdisk"
        ramdisk_dir.mkdir(exist_ok=True)
        
        # Try different decompression methods
        with open(ramdisk_path, 'rb') as f:
            magic = f.read(6)
            f.seek(0)
            
            try:
                if magic.startswith(b'\x1f\x8b'):  # gzip
                    with gzip.open(ramdisk_path, 'rb') as gz:
                        decompressed = gz.read()
                elif magic.startswith(b'\xfd7zXZ'):  # xz
                    with lzma.open(ramdisk_path, 'rb') as xz:
                        decompressed = xz.read()
                else:
                    # Try cpio directly
                    decompressed = f.read()
                
                # Extract cpio archive
                cpio_path = output_dir / "ramdisk.cpio"
                with open(cpio_path, 'wb') as cf:
                    cf.write(decompressed)
                
                # Extract using cpio
                result = subprocess.run([
                    'cpio', '-i', '-d', '-m', '-v'
                ], input=decompressed, cwd=ramdisk_dir, capture_output=True)
                
                if result.returncode == 0:
                    self.console.print("[green]✓ Decompressed and extracted ramdisk[/green]")
                else:
                    self.console.print("[yellow]Warning: Could not extract ramdisk contents[/yellow]")
                    
            except Exception as e:
                self.console.print(f"[yellow]Warning: Could not decompress ramdisk: {e}[/yellow]")
    
    def _write_boot_info(self, boot_info: Dict, output_dir: Path) -> None:
        info_path = output_dir / "img_info"
        
        with open(info_path, 'w') as f:
            f.write(f"magic={boot_info['magic']}\n")
            f.write(f"kernel_size={boot_info['kernel_size']}\n")
            f.write(f"kernel_addr=0x{boot_info['kernel_addr']:08x}\n")
            f.write(f"ramdisk_size={boot_info['ramdisk_size']}\n")
            f.write(f"ramdisk_addr=0x{boot_info['ramdisk_addr']:08x}\n")
            f.write(f"second_size={boot_info['second_size']}\n")
            f.write(f"second_addr=0x{boot_info['second_addr']:08x}\n")
            f.write(f"tags_addr=0x{boot_info['tags_addr']:08x}\n")
            f.write(f"page_size={boot_info['page_size']}\n")
            f.write(f"version={boot_info['version']}\n")
            f.write(f"cmd_line={boot_info['cmd_line']}\n")
            f.write(f"board={boot_info['board']}\n")
            if boot_info['dtb_size'] > 0:
                f.write(f"dtb_size={boot_info['dtb_size']}\n")
                f.write(f"dtb_addr=0x{boot_info['dtb_addr']:08x}\n")
            f.write(f"base_addr=0x{boot_info['base_addr']:08x}\n")
            f.write(f"kernel_offset=0x{boot_info['kernel_offset']:08x}\n")
            f.write(f"ramdisk_offset=0x{boot_info['ramdisk_offset']:08x}\n")
            f.write(f"second_offset=0x{boot_info['second_offset']:08x}\n")
            f.write(f"tags_offset=0x{boot_info['tags_offset']:08x}\n")
            if boot_info['dtb_offset'] > 0:
                f.write(f"dtb_offset=0x{boot_info['dtb_offset']:08x}\n")
        
        self.console.print("[green]✓ Boot image info written[/green]")
    
    def _unpack_vndr_boot(self, boot_img_path: Path, output_dir: Path) -> bool:
        self.console.print("[blue]Unpacking vendor boot image[/blue]")
        # Simplified VNDR boot unpacking - would need more implementation
        self.console.print("[yellow]VNDR boot unpacking not fully implemented[/yellow]")
        return True