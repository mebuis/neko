# -*- encoding: UTF-8 -*-


import argparse
import os
import sys
import traceback

from neko import Dispatcher
from neko.Common.Utilities.Logger import logger

parser = argparse.ArgumentParser()
group = parser.add_mutually_exclusive_group()
group.add_argument("-f", "--file")
group.add_argument("-d", "--directory")  # input directory
parser.add_argument("-o", "--output", default = ".")  # output directory
parser.add_argument("-s", "--suffix", default = "output.json")

args = parser.parse_args()

result = None

file_list = list()
if args.file:
    if os.path.isfile(args.file):
        file_list.append(os.path.abspath(args.file))
    else:
        logger.error(f"{args.file} is not a valid file.")
        sys.exit(-1)
elif args.directory:
    if os.path.isdir(args.directory):
        for root, dirs, files in os.walk(args.directory):
            for file in files:
                file_list.append(os.path.abspath(os.path.join(root, file)))
    else:
        logger.error(f"{args.directory} is not a valid directory.")
        sys.exit(-1)
else:
    logger.error("Please specify a file or a directory to scan.")
    sys.exit(-1)

if args.output:
    if not os.path.isdir(args.output):
        logger.error(f"{args.output} is not a valid directory.")
        if os.path.isfile(args.output):
            sys.exit(-1)
        else:
            logger.info("Creating output directory...")
            os.makedirs(args.output, exist_ok = True)

for file_path in file_list:
    logger.info(f"Scanning {file_path}...")
    result = None
    try:
        f1 = open(file_path, "rb")
        dispatcher = Dispatcher(label = os.path.basename(file_path), is_root_dispatcher = True)
        dispatcher.Dispatch(f1.read())

        output_directory = os.path.abspath(args.output)
        output_file_name = f"[{os.path.basename(file_path)}]-{args.suffix}"  # may overwrite
        output_file_name = os.path.join(output_directory, output_file_name)
        f2 = open(output_file_name, "w")
        f2.write(dispatcher.GenerateJsonResult())
        f2.close()

        result = True
    except Exception as e:
        result = False
        logger.critical(traceback.format_exc())
    finally:
        if result:
            logger.info(f"[V]PASSED: {file_path}")
        else:
            logger.warning(f"[X]FAILED: {file_path}")
