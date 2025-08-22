import os
import struct
import subprocess
import gzip
import lzma
from pathlib import Path
from rich.console import Console

console = Console()

class UnpackBoot:
    def __init__(self):
        self.formats = {
            'gzip': self._test_gzip,
            'lzma': self._test_lzma,
            'xz': self._test_xz,
            'lzo': self._test_lzo,
            'lz4': self._test_lz4,
        }
    
    def unpack(self, boot_img_path, output_dir):
        boot_path = Path(boot_img_path)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        console.print(f"Unpack & decompress {boot_path.name} to {output_path}")
        
        bootimg_copy = output_path / boot_path.name
        if bootimg_copy != boot_path:
            import shutil
            shutil.copy2(boot_path, bootimg_copy)
        
        os.chdir(output_path)
        
        offset = self._find_android_header(bootimg_copy)
        if offset is None:
            raise Exception("Android boot header not found")
        
        if offset > 0:
            with open(bootimg_copy, 'rb') as f_in:
                f_in.seek(offset)
                with open('bootimg', 'wb') as f_out:
                    f_out.write(f_in.read())
            bootimg_file = 'bootimg'
        else:
            bootimg_file = str(bootimg_copy)
        
        vndrboot = self._check_vndrboot(bootimg_file)
        header_addr = 8 if vndrboot else 40
        
        boot_info = self._parse_boot_header(bootimg_file, vndrboot, header_addr)
        
        self._extract_components(bootimg_file, boot_info)
        
        self._extract_ramdisk(boot_info)
        
        self._write_img_info(boot_info)
        
        console.print("Unpack completed.")
        return str(output_path)
    
    def _find_android_header(self, bootimg_path):
        with open(bootimg_path, 'rb') as f:
            data = f.read()
            
        android_pos = data.find(b'ANDROID!')
        vndrboot_pos = data.find(b'VNDRBOOT')
        
        if android_pos != -1:
            return android_pos
        elif vndrboot_pos != -1:
            return vndrboot_pos
        else:
            return None
    
    def _check_vndrboot(self, bootimg_file):
        with open(bootimg_file, 'rb') as f:
            header = f.read(8)
            return b'VNDRBOOT' in header
    
    def _parse_boot_header(self, bootimg_file, vndrboot, header_addr):
        with open(bootimg_file, 'rb') as f:
            
            f.seek(12)
            kernel_addr = struct.unpack('<I', f.read(4))[0]
            
            f.seek(20)
            ramdisk_addr = struct.unpack('<I', f.read(4))[0]
            
            f.seek(28)
            second_addr = struct.unpack('<I', f.read(4))[0]
            
            f.seek(32)
            tags_addr = struct.unpack('<I', f.read(4))[0]
            
            f.seek(8)
            kernel_size = struct.unpack('<I', f.read(4))[0]
            
            f.seek(16)
            ramdisk_size = struct.unpack('<I', f.read(4))[0]
            
            f.seek(24)
            second_size = struct.unpack('<I', f.read(4))[0]
            
            f.seek(36)
            page_size = struct.unpack('<I', f.read(4))[0]
            
            f.seek(40)
            dtb_size = struct.unpack('<I', f.read(4))[0]
            
            f.seek(1632)
            dtbo_size = struct.unpack('<I', f.read(4))[0]
            
            dtbo_addr = 0
            if dtbo_size > 0:
                f.seek(1636)
                dtbo_addr = struct.unpack('<I', f.read(4))[0]
            
            f.seek(64)
            cmd_line = f.read(512).decode('ascii', errors='ignore').rstrip('\x00')
            
            f.seek(48)
            board = f.read(16).decode('ascii', errors='ignore').rstrip('\x00')
            
            f.seek(header_addr)
            version = struct.unpack('<I', f.read(4))[0]
        
        base_addr = kernel_addr - 0x00008000
        
        return {
            'kernel_addr': kernel_addr,
            'ramdisk_addr': ramdisk_addr,
            'second_addr': second_addr,
            'tags_addr': tags_addr,
            'kernel_size': kernel_size,
            'ramdisk_size': ramdisk_size,
            'second_size': second_size,
            'page_size': page_size,
            'dtb_size': dtb_size,
            'dtbo_size': dtbo_size,
            'dtbo_addr': dtbo_addr,
            'cmd_line': cmd_line,
            'board': board,
            'version': version,
            'base_addr': base_addr,
            'vndrboot': vndrboot,
        }
    
    def _extract_components(self, bootimg_file, boot_info):
        page_size = boot_info['page_size']
        kernel_size = boot_info['kernel_size']
        ramdisk_size = boot_info['ramdisk_size']
        second_size = boot_info['second_size']
        dtb_size = boot_info['dtb_size']
        dtbo_size = boot_info['dtbo_size']
        
        k_count = (kernel_size + page_size - 1) // page_size
        r_count = (ramdisk_size + page_size - 1) // page_size
        s_count = (second_size + page_size - 1) // page_size
        d_count = (dtb_size + page_size - 1) // page_size
        do_count = (dtbo_size + page_size - 1) // page_size
        
        k_offset = 1
        r_offset = k_offset + k_count
        s_offset = r_offset + r_count
        do_offset = s_offset + s_count
        d_offset = do_offset + do_count
        
        with open(bootimg_file, 'rb') as f:
            
            if kernel_size > 0:
                f.seek(k_offset * page_size)
                kernel_data = f.read(k_count * page_size)[:kernel_size]
                with open('kernel', 'wb') as kernel_file:
                    kernel_file.write(kernel_data)
            
            if ramdisk_size > 0:
                f.seek(r_offset * page_size)
                ramdisk_data = f.read(r_count * page_size)[:ramdisk_size]
                with open('ramdisk.packed', 'wb') as ramdisk_file:
                    ramdisk_file.write(ramdisk_data)
            
            if second_size > 0:
                f.seek(s_offset * page_size)
                second_data = f.read(s_count * page_size)[:second_size]
                with open('second.img', 'wb') as second_file:
                    second_file.write(second_data)
            
            if dtb_size > 0:
                f.seek(d_offset * page_size)
                dtb_data = f.read(d_count * page_size)[:dtb_size]
                dtb_name = 'dtb.img' if boot_info['version'] > 1 else 'dt.img'
                with open(dtb_name, 'wb') as dtb_file:
                    dtb_file.write(dtb_data)
            
            if dtbo_size > 0:
                f.seek(do_offset * page_size)
                dtbo_data = f.read(do_count * page_size)[:dtbo_size]
                with open('dtbo.img', 'wb') as dtbo_file:
                    dtbo_file.write(dtbo_data)
    
    def _extract_ramdisk(self, boot_info):
        if not os.path.exists('ramdisk.packed'):
            console.print("No ramdisk found")
            return
        
        mtk_header = self._check_mtk_header('ramdisk.packed')
        if mtk_header:
            console.print("ramdisk has a MTK header")
            self._handle_mtk_ramdisk('ramdisk.packed')
        
        os.makedirs('ramdisk', exist_ok=True)
        os.chdir('ramdisk')
        
        format_detected = None
        for format_name, test_func in self.formats.items():
            if test_func('../ramdisk.packed'):
                format_detected = format_name
                console.print(f"ramdisk is {format_name} format.")
                break
        
        if format_detected:
            self._decompress_ramdisk(f'../{Path("ramdisk.packed")}', format_detected)
        else:
            console.print("ramdisk is unknown format, can't unpack ramdisk")
        
        os.chdir('..')
    
    def _check_mtk_header(self, ramdisk_file):
        try:
            with open(ramdisk_file, 'rb') as f:
                header = f.read(4)
                return header == b'\x88\x16\x88\x58'
        except:
            return False
    
    def _handle_mtk_ramdisk(self, ramdisk_file):
        with open(ramdisk_file, 'rb') as f_in:
            
            f_in.seek(512)
            ramdisk_data = f_in.read()
            with open('ramdisk.packed', 'wb') as f_out:
                f_out.write(ramdisk_data)
            
            f_in.seek(0)
            header_data = f_in.read(512)
            with open('ramdisk.mtk_header', 'wb') as f_out:
                f_out.write(header_data)
    
    def _test_gzip(self, filepath):
        try:
            with gzip.open(filepath, 'rb') as f:
                f.read(10)
            return True
        except:
            return False
    
    def _test_lzma(self, filepath):
        try:
            with lzma.open(filepath, 'rb') as f:
                f.read(10)
            return True
        except:
            return False
    
    def _test_xz(self, filepath):
        try:
            result = subprocess.run(['xz', '-t', filepath], capture_output=True)
            return result.returncode == 0
        except:
            return False
    
    def _test_lzo(self, filepath):
        try:
            result = subprocess.run(['lzop', '-t', filepath], capture_output=True)
            return result.returncode == 0
        except:
            return False
    
    def _test_lz4(self, filepath):
        try:
            result = subprocess.run(['lz4', '-t', filepath], capture_output=True)
            return result.returncode == 0
        except:
            return False
    
    def _decompress_ramdisk(self, ramdisk_file, format_type):
        if format_type == 'gzip':
            with gzip.open(ramdisk_file, 'rb') as f_in:
                decompressed = f_in.read()
        elif format_type == 'lzma':
            with lzma.open(ramdisk_file, 'rb') as f_in:
                decompressed = f_in.read()
        else:
            
            decompress_cmds = {
                'xz': ['xz', '-d', '-c', ramdisk_file],
                'lzo': ['lzop', '-d', '-c', ramdisk_file],
                'lz4': ['lz4', '-d', ramdisk_file]
            }
            
            cmd = decompress_cmds.get(format_type)
            if cmd:
                result = subprocess.run(cmd, capture_output=True)
                if result.returncode == 0:
                    decompressed = result.stdout
                else:
                    raise Exception(f"Decompression failed: {result.stderr}")
            else:
                raise Exception(f"Unsupported format: {format_type}")
        
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(decompressed)
            temp_cpio = temp_file.name
        
        try:
            subprocess.run(['cpio', '-i', '-d', '-m', '--no-absolute-filenames'], 
                         input=decompressed, check=True)
        finally:
            os.unlink(temp_cpio)
    
    def _write_img_info(self, boot_info):
        kernel_offset = boot_info['kernel_addr'] - boot_info['base_addr']
        ramdisk_offset = boot_info['ramdisk_addr'] - boot_info['base_addr']
        second_offset = boot_info['second_addr'] - boot_info['base_addr']
        tags_offset = boot_info['tags_addr'] - boot_info['base_addr']
        dtbo_offset = boot_info['dtbo_addr'] - boot_info['base_addr'] if boot_info['dtbo_addr'] else 0
        
        with open('img_info', 'w') as f:
            f.write(f"kernel=kernel\n")
            f.write(f"ramdisk=ramdisk\n")
            if boot_info['second_size'] > 0:
                f.write(f"second=second.img\n")
            f.write(f"page_size={boot_info['page_size']}\n")
            if boot_info['dtbo_size'] > 0:
                f.write(f"dtbo=dtbo.img\n")
            if boot_info['dtb_size'] > 0:
                dtb_name = 'dtb.img' if boot_info['version'] > 1 else 'dt.img'
                f.write(f"dt={dtb_name}\n")
            f.write(f"kernel_size={boot_info['kernel_size']}\n")
            f.write(f"ramdisk_size={boot_info['ramdisk_size']}\n")
            if boot_info['second_size'] > 0:
                f.write(f"second_size={boot_info['second_size']}\n")
            if boot_info['dtb_size'] > 0:
                f.write(f"dtb_size={boot_info['dtb_size']}\n")
            f.write(f"base_addr=0x{boot_info['base_addr']:08x}\n")
            f.write(f"kernel_offset=0x{kernel_offset:08x}\n")
            f.write(f"ramdisk_offset=0x{ramdisk_offset:08x}\n")
            f.write(f"tags_offset=0x{tags_offset:08x}\n")
            if boot_info['dtbo_size'] > 0:
                f.write(f"dtbo_offset=0x{dtbo_offset:08x}\n")
            f.write(f"cmd_line='{boot_info['cmd_line']}'\n")
            f.write(f'board="{boot_info["board"]}"\n')