import sys
import os
from pathlib import Path

def convert_sdat_to_img(transfer_list_file, new_data_file, output_image_file):
    __version__ = '1.2'

    if sys.hexversion < 0x02070000:
        print("Python 2.7 or newer is required.", file=sys.stderr)
        sys.exit(1)
    else:
        print(f'sdat2img binary - version: {__version__}\n')

    def rangeset(src):
        src_set = src.split(',')
        num_set = [int(item) for item in src_set]
        if len(num_set) != num_set[0] + 1:
            print('Error on parsing following data to rangeset:\n{}'.format(src), file=sys.stderr)
            sys.exit(1)

        return tuple([(num_set[i], num_set[i + 1]) for i in range(1, len(num_set), 2)])

    def parse_transfer_list_file(path):
        trans_list = open(path, 'r')

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
                commands.append([cmd, rangeset(line[1])])
            else:
                if not cmd[0].isdigit():
                    print(f'Command "{cmd}" is not valid.', file=sys.stderr)
                    trans_list.close()
                    sys.exit(1)

        trans_list.close()
        return version, new_blocks, commands

    BLOCK_SIZE = 4096
    
    version, new_blocks, commands = parse_transfer_list_file(transfer_list_file)

    if version == 1:
        print('Android Lollipop 5.0 detected!\n')
    elif version == 2:
        print('Android Lollipop 5.1 detected!\n')
    elif version == 3:
        print('Android Marshmallow 6.x detected!\n')
    elif version == 4:
        print('Android Nougat 7.x / Oreo 8.x / Pie 9.x detected!\n')
    else:
        print(f'Unknown Android version!\n')

    output_img = open(output_image_file, 'wb')

    new_data_file_param = open(new_data_file, 'rb')
    all_block_sets = [i for command in commands for i in command[1]]
    max_file_size = max(all_block_sets) * BLOCK_SIZE

    for command in commands:
        if command[0] == 'new':
            for block in command[1]:
                begin = block[0]
                end = block[1]
                block_count = end - begin
                print(f'Copying {block_count} blocks into position {begin}...')

                output_img.seek(begin * BLOCK_SIZE)
                
                while block_count > 0:
                    output_img.write(new_data_file_param.read(BLOCK_SIZE))
                    block_count -= 1
        else:
            print(f'Skipping command {command[0]}...')

    output_img.close()
    new_data_file_param.close()
    print('Done! Output image: {}'.format(os.path.realpath(output_image_file)))