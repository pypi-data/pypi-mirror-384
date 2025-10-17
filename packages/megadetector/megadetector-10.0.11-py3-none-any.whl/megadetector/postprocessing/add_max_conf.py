"""

add_max_conf.py

The MD output format included a "max_detection_conf" field with each image
up to and including version 1.2; it was removed as of version 1.3 (it's
redundant with the individual detection confidence values).

Just in case someone took a dependency on that field, this script allows you
to add it back to an existing .json file.

"""

#%% Imports and constants

import os
import json
import sys
import argparse

from megadetector.utils.ct_utils import get_max_conf
from megadetector.utils.ct_utils import write_json


#%% Main function

def add_max_conf(input_file,output_file):
    """
    Add maximum confidence values to [input_file] and write the results to [output_file].

    Args:
        input_file (str): MD-formatted .json file to which we should add maxconf values
        output_file (str): output .json file
    """

    assert os.path.isfile(input_file), "Can't find input file {}".format(input_file)

    with open(input_file,'r') as f:
        d = json.load(f)

    for im in d['images']:

        max_conf = get_max_conf(im)

        if 'max_detection_conf' in im:
            assert abs(max_conf - im['max_detection_conf']) < 0.00001
        else:
            im['max_detection_conf'] = max_conf

    write_json(output_file,d)


#%% Driver

def main(): # noqa

    parser = argparse.ArgumentParser()
    parser.add_argument('input_file',type=str,
                        help='Input .json file')
    parser.add_argument('output_file',type=str,
                        help='Output .json file')

    if len(sys.argv[1:]) == 0:
        parser.print_help()
        parser.exit()

    args = parser.parse_args()
    add_max_conf(args.input_file, args.output_file)

if __name__ == '__main__':
    main()

