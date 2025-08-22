import os
import struct
import subprocess
from pathlib import Path
from typing import Dict, Optional, Tuple
from dumprx.utils.logging import logger

class BootUnpacker:
    def __init__(self, config):
        self.config = config
        
    def unpack(self, boot_img_path: Path, output_dir: Path) -> bool:
        if not boot_img_path.exists():
            logger.error(f"Boot image not found: {boot_img_path}")
            return False
            
        output_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            info = self._parse_boot_header(boot_img_path)
            if not info:
                return False
                
            self._extract_components(boot_img_path, output_dir, info)
            self._save_boot_info(output_dir, info)
            
            logger.success("Boot image unpacked successfully")
            return True
            
        except Exception as e:
            logger.error(f"Boot unpacking failed: {e}")
            return False
    
    def _parse_boot_header(self, boot_img_path: Path) -> Optional[Dict]:
        with open(boot_img_path, 'rb') as f:
            header = f.read(1660)
            
        if len(header) < 1660:
            logger.error("Boot image too small")
            return None
            
        magic = header[:8]
        if magic != b'ANDROID!':
            if header[512:520] == b'ANDROID!':
                logger.info("MTK Header Detected")
                return self._parse_mtk_boot_header(boot_img_path)
            else:
                logger.error("Invalid boot image magic")
                return None
        
        vndr_boot = header[1648:1656] == b'VNDRBOOT'
        header_addr = 8 if vndr_boot else 0
        
        info = {
            'vndr_boot': vndr_boot,
            'header_addr': header_addr,
            'kernel_size': struct.unpack('<I', header[8:12])[0],
            'kernel_addr': struct.unpack('<I', header[12:16])[0],
            'ramdisk_size': struct.unpack('<I', header[16:20])[0],
            'ramdisk_addr': struct.unpack('<I', header[20:24])[0],
            'second_size': struct.unpack('<I', header[24:28])[0],
            'second_addr': struct.unpack('<I', header[28:32])[0],
            'tags_addr': struct.unpack('<I', header[32:36])[0],
            'page_size': struct.unpack('<I', header[36:40])[0],
            'dtb_size': struct.unpack('<I', header[40:44])[0],
            'dtbo_size': struct.unpack('<I', header[1632:1636])[0] if len(header) >= 1636 else 0,
            'cmd_line': header[64:576].decode('ascii', errors='ignore').strip('\x00'),
            'board': header[48:64].decode('ascii', errors='ignore').strip('\x00'),
            'version': header[header_addr],
        }
        
        if info['dtbo_size'] > 0 and len(header) >= 1640:
            info['dtbo_addr'] = struct.unpack('<I', header[1636:1640])[0]
        else:
            info['dtbo_addr'] = 0
            
        version = info['version']
        
        if version == 2:
            if len(header) >= 1656:
                info['dtb_size'] = struct.unpack('<I', header[1648:1652])[0]
                info['dtb_addr'] = struct.unpack('<I', header[1652:1656])[0]
        elif version == 3:
            info['page_size'] = 4096
            info['board'] = ''
            
            if vndr_boot:
                info['kernel_addr'] = struct.unpack('<I', header[16:20])[0]
                info['ramdisk_addr'] = struct.unpack('<I', header[20:24])[0]
                info['ramdisk_size'] = struct.unpack('<I', header[24:28])[0]
                info['cmd_line'] = header[28:2076].decode('ascii', errors='ignore').strip('\x00')
                info['tags_addr'] = struct.unpack('<I', header[2076:2080])[0]
                info['dtb_size'] = struct.unpack('<I', header[2100:2104])[0]
                info['dtb_addr'] = struct.unpack('<I', header[2104:2108])[0]
            else:
                info['kernel_addr'] = 0x00008000
                info['kernel_size'] = struct.unpack('<I', header[8:12])[0]
                info['ramdisk_size'] = struct.unpack('<I', header[12:16])[0]
                info['cmd_line'] = header[44:1580].decode('ascii', errors='ignore').strip('\x00')
                
                os_version = struct.unpack('<I', header[16:20])[0]
                patch_level = os_version & ((1 << 11) - 1)
                os_version = os_version >> 11
                
                info['os_version'] = f"{(os_version >> 14)}.{(os_version >> 7) & ((1 << 7) - 1)}.{os_version & ((1 << 7) - 1)}"
                info['patch_level'] = f"{(patch_level >> 4) + 2000}:{patch_level & ((1 << 4) - 1)}"
        
        self._calculate_offsets(info)
        return info
    
    def _parse_mtk_boot_header(self, boot_img_path: Path) -> Optional[Dict]:
        with open(boot_img_path, 'rb') as f:
            f.seek(512)
            header = f.read(1148)
            
        if len(header) < 1148 or header[:8] != b'ANDROID!':
            logger.error("Invalid MTK boot image")
            return None
            
        info = {
            'mtk_header': True,
            'vndr_boot': False,
            'header_addr': 0,
            'kernel_size': struct.unpack('<I', header[8:12])[0],
            'kernel_addr': struct.unpack('<I', header[12:16])[0],
            'ramdisk_size': struct.unpack('<I', header[16:20])[0],
            'ramdisk_addr': struct.unpack('<I', header[20:24])[0],
            'second_size': struct.unpack('<I', header[24:28])[0],
            'second_addr': struct.unpack('<I', header[28:32])[0],
            'tags_addr': struct.unpack('<I', header[32:36])[0],
            'page_size': struct.unpack('<I', header[36:40])[0],
            'dtb_size': struct.unpack('<I', header[40:44])[0],
            'cmd_line': header[64:576].decode('ascii', errors='ignore').strip('\x00'),
            'board': header[48:64].decode('ascii', errors='ignore').strip('\x00'),
            'version': header[0],
            'dtbo_size': 0,
            'dtbo_addr': 0,
        }
        
        self._calculate_offsets(info)
        return info
    
    def _calculate_offsets(self, info: Dict):
        base_addr = info['kernel_addr'] - 0x00008000
        
        info['base_addr'] = base_addr
        info['kernel_offset'] = info['kernel_addr'] - base_addr
        info['ramdisk_offset'] = info['ramdisk_addr'] - base_addr
        info['second_offset'] = info['second_addr'] - base_addr
        info['tags_offset'] = info['tags_addr'] - base_addr
        info['dtbo_offset'] = info.get('dtbo_addr', 0) - base_addr
        info['dtb_offset'] = info.get('dtb_addr', 0) - base_addr
        
        page_size = info['page_size']
        info['k_count'] = (info['kernel_size'] + page_size - 1) // page_size
        info['r_count'] = (info['ramdisk_size'] + page_size - 1) // page_size
        info['s_count'] = (info['second_size'] + page_size - 1) // page_size
        info['d_count'] = (info['dtb_size'] + page_size - 1) // page_size
        info['do_count'] = (info['dtbo_size'] + page_size - 1) // page_size
        
        start_offset = 512 if info.get('mtk_header') else 0
        k_offset = start_offset + page_size
        r_offset = k_offset + info['k_count'] * page_size
        s_offset = r_offset + info['r_count'] * page_size
        do_offset = s_offset + info['s_count'] * page_size
        d_offset = do_offset + info['do_count'] * page_size
        
        info['k_offset'] = k_offset
        info['r_offset'] = r_offset
        info['s_offset'] = s_offset
        info['do_offset'] = do_offset
        info['d_offset'] = d_offset
    
    def _extract_components(self, boot_img_path: Path, output_dir: Path, info: Dict):
        with open(boot_img_path, 'rb') as f:
            if info['kernel_size'] > 0:
                f.seek(info['k_offset'])
                kernel_data = f.read(info['kernel_size'])
                (output_dir / 'kernel').write_bytes(kernel_data)
                
            if info['ramdisk_size'] > 0:
                f.seek(info['r_offset'])
                ramdisk_data = f.read(info['ramdisk_size'])
                ramdisk_packed = output_dir / 'ramdisk.packed'
                ramdisk_packed.write_bytes(ramdisk_data)
                
                self._unpack_ramdisk(ramdisk_packed, output_dir)
                
            if info['second_size'] > 0:
                f.seek(info['s_offset'])
                second_data = f.read(info['second_size'])
                (output_dir / 'second').write_bytes(second_data)
                
            if info['dtb_size'] > 0:
                f.seek(info['d_offset'])
                dtb_data = f.read(info['dtb_size'])
                (output_dir / 'dtb').write_bytes(dtb_data)
                
            if info['dtbo_size'] > 0:
                f.seek(info['do_offset'])
                dtbo_data = f.read(info['dtbo_size'])
                (output_dir / 'dtbo').write_bytes(dtbo_data)
    
    def _unpack_ramdisk(self, ramdisk_packed: Path, output_dir: Path):
        ramdisk_dir = output_dir / 'ramdisk'
        ramdisk_dir.mkdir(exist_ok=True)
        
        with open(ramdisk_packed, 'rb') as f:
            magic = f.read(4)
            
        compression_type = None
        if magic[:3] == b'\x1f\x8b\x08':
            compression_type = 'gzip'
        elif magic == b'BZh9':
            compression_type = 'bzip2'
        elif magic[:4] == b'\x04"M\x18':
            compression_type = 'lz4'
        elif magic[:6] == b'\xfd7zXZ':
            compression_type = 'xz'
        elif magic[:4] == b'(\xb5/\xfd':
            compression_type = 'zstd'
        
        if compression_type:
            logger.info(f"Decompressing ramdisk ({compression_type})")
            
            ramdisk_uncompressed = output_dir / 'ramdisk.cpio'
            
            if compression_type == 'gzip':
                subprocess.run(['gunzip', '-c', str(ramdisk_packed)], 
                             stdout=open(ramdisk_uncompressed, 'wb'))
            elif compression_type == 'lz4':
                subprocess.run(['lz4', '-d', str(ramdisk_packed), str(ramdisk_uncompressed)])
            elif compression_type == 'xz':
                subprocess.run(['xz', '-d', '-c', str(ramdisk_packed)], 
                             stdout=open(ramdisk_uncompressed, 'wb'))
            elif compression_type == 'zstd':
                subprocess.run(['zstd', '-d', str(ramdisk_packed), '-o', str(ramdisk_uncompressed)])
            else:
                ramdisk_uncompressed = ramdisk_packed
                
            subprocess.run(['cpio', '-idmv'], 
                         stdin=open(ramdisk_uncompressed, 'rb'), 
                         cwd=ramdisk_dir)
        else:
            logger.info("Extracting uncompressed ramdisk")
            subprocess.run(['cpio', '-idmv'], 
                         stdin=open(ramdisk_packed, 'rb'), 
                         cwd=ramdisk_dir)
    
    def _save_boot_info(self, output_dir: Path, info: Dict):
        info_file = output_dir / 'img_info'
        
        lines = []
        if info.get('mtk_header'):
            lines.append('mtk=true')
        if info.get('vndr_boot'):
            lines.append('vndr_boot=true')
            
        lines.extend([
            f"board={info.get('board', '')}",
            f"base=0x{info['base_addr']:08x}",
            f"pagesize={info['page_size']}",
            f"kerneloff=0x{info['kernel_offset']:08x}",
            f"ramdiskoff=0x{info['ramdisk_offset']:08x}",
            f"secondoff=0x{info['second_offset']:08x}",
            f"tagsoff=0x{info['tags_offset']:08x}",
            f"dtboff=0x{info['dtb_offset']:08x}",
            f"dtbooff=0x{info['dtbo_offset']:08x}",
            f"cmdline={info.get('cmd_line', '')}",
        ])
        
        if info.get('os_version'):
            lines.append(f"osversion={info['os_version']}")
        if info.get('patch_level'):
            lines.append(f"patchlevel={info['patch_level']}")
            
        info_file.write_text('\n'.join(lines) + '\n')