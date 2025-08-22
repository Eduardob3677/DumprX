import os
import re
import sys
import struct
from pathlib import Path

def extract_update_app(source, output_dir, file_list=None):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    def cmd(command):
        try:
            import subprocess
            test1 = subprocess.check_output(command, shell=True)
            test1 = test1.strip().decode()
        except:
            test1 = ''
        return test1

    bytenum = 4
    img_files = []

    py2 = None
    if int(''.join(str(i) for i in sys.version_info[0:2])) < 30:
        py2 = 1

    with open(source, 'rb') as f:
        while True:
            i = f.read(bytenum)

            if not i:
                break
            elif i != b'\x55\xAA\x5A\xA5':
                continue

            headersize = f.read(bytenum)
            headersize = list(struct.unpack('<L', headersize))[0]
            f.seek(16, 1)
            filesize = f.read(bytenum)
            filesize = list(struct.unpack('<L', filesize))[0]
            f.seek(32, 1)
            filename = f.read(16)

            try:
                filename = str(filename.decode())
            except UnicodeDecodeError:
                filename = filename.decode('gbk')

            filename = filename.split('\x00')[0]
            if len(filename) == 0:
                filename = 'unknown'
            
            filename = re.sub(r'[^\w\-_\.]', '_', filename)

            f.seek(headersize - 76, 1)

            if filename.endswith('.img') or filesize > 16:
                if file_list is None or filename in file_list:
                    print(f'Extracting {filename} ({filesize} bytes)...')
                    
                    output_file = output_dir / filename
                    with open(output_file, 'wb') as out:
                        while filesize > 0:
                            chunk_size = min(1024 * 1024, filesize)
                            data = f.read(chunk_size)
                            if not data:
                                break
                            out.write(data)
                            filesize -= len(data)
                    
                    img_files.append(str(output_file))
                else:
                    f.seek(filesize, 1)
            else:
                f.seek(filesize, 1)

            xbytes = bytenum - f.tell() % bytenum
            if xbytes < bytenum:
                f.seek(xbytes, 1)

    print('\nExtraction complete')
    return img_files