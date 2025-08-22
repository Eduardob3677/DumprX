import sys
from pathlib import Path
from typing import List, Tuple, Optional
from dumprx.utils.logging import logger

class SparseDataImageConverter:
    def __init__(self):
        self.block_size = 4096
        
    def convert(self, transfer_list_file: Path, new_data_file: Path, output_image_file: Path) -> bool:
        try:
            if not transfer_list_file.exists():
                logger.error(f"Transfer list file not found: {transfer_list_file}")
                return False
                
            if not new_data_file.exists():
                logger.error(f"New data file not found: {new_data_file}")
                return False
                
            version, new_blocks, commands = self._parse_transfer_list_file(transfer_list_file)
            
            version_names = {
                1: 'Android Lollipop 5.0',
                2: 'Android Lollipop 5.1', 
                3: 'Android Marshmallow 6.x',
                4: 'Android Nougat 7.x / Oreo 8.x'
            }
            
            logger.info(f"{version_names.get(version, f'Unknown version {version}')} detected!")
            
            with open(new_data_file, 'rb') as new_data:
                with open(output_image_file, 'wb') as output_img:
                    all_block_sets = [i for command in commands for i in command[1]]
                    max_file_size = max(all_block_sets) * self.block_size if all_block_sets else 0
                    
                    for command in commands:
                        if command[0] == 'new':
                            for block in command[1]:
                                begin = block[0]
                                end = block[1]
                                block_count = end - begin
                                logger.info(f"Copying {block_count} blocks into position {begin}...")
                                
                                output_img.seek(begin * self.block_size)
                                
                                while block_count > 0:
                                    output_img.write(new_data.read(self.block_size))
                                    block_count -= 1
                                    
            logger.success(f"Converted sparse data image: {output_image_file}")
            return True
            
        except Exception as e:
            logger.error(f"Conversion failed: {e}")
            return False
    
    def _parse_transfer_list_file(self, path: Path) -> Tuple[int, int, List]:
        with open(path, 'r') as trans_list:
            version = int(trans_list.readline())
            new_blocks = int(trans_list.readline())
            
            if version >= 2:
                trans_list.readline()
                trans_list.readline()
            
            commands = []
            for line in trans_list:
                line = line.split(' ')
                cmd = line[0]
                if cmd in ['erase', 'new', 'zero']:
                    commands.append([cmd, self._rangeset(line[1])])
                elif cmd[0].isdigit():
                    continue
                else:
                    raise ValueError(f'Command "{cmd}" is not valid.')
                    
        return version, new_blocks, commands
    
    def _rangeset(self, src: str) -> List[Tuple[int, int]]:
        src_set = src.split(',')
        num_set = [int(item) for item in src_set]
        
        if len(num_set) != num_set[0] + 1:
            raise ValueError(f'Error on parsing following data to rangeset:\n{src}')
            
        return [(num_set[i], num_set[i+1]) for i in range(1, len(num_set), 2)]

def convert_sdat2img(transfer_list: str, new_data: str, output_image: str) -> bool:
    converter = SparseDataImageConverter()
    return converter.convert(Path(transfer_list), Path(new_data), Path(output_image))