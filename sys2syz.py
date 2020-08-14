# User imports
from core.Utils import *
from core.Bear import *
from core.Extractor import *

# Default imports 
import argparse
import logging
import os

def main():
    # Parse the command line arguments
    parser = argparse.ArgumentParser(description="Sys2Syz : A Utility to convert Syscalls and Ioctls to Syzkaller representation")

    parser.add_argument("-t", "--target", help="target file to generate descriptions for", type=str, required=True)
    parser.add_argument("-c", "--compile-commands", help="path to compile_commands.json", type=str, required=True)
    parser.add_argument("-v", "--verbosity", help="make Griller spit more things out", action="count")
    args = parser.parse_args()

    verbose = args.verbosity

    if args.verbosity == 1:
        logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)
    
    elif args.verbosity == 2:
        logging.basicConfig(format='%(asctime)s %(message)s', level=logging.DEBUG)

    target = os.path.realpath(args.target)
    #Utils.dir_exists(target, True)     #throws error
    logging.info("[+] The target file is %s", target)

    compile_commands = os.path.realpath(args.compile_commands)
    #Utils.file_exists(compile_commands, True)      throws error
    logging.info("[+] The compile commands is %s", compile_commands)

    bear = Bear(target, compile_commands, verbose)
    commands = bear.parse_compile_commands()
    bear.compile_target(commands)
    logging.info("[+] Preprocessed files have been generated")

    extractor = Extractor(target)
    files = extractor.get_header_files()
    extractor.get_ioctls(files)
    logging.info("[+] Extracted ioctl commands")

    cwd = os.getcwd()
    out_dir = cwd + "/preprocessed/" + target.split("/")[-1] + "/out"
    preprocessed_path = cwd + "/preprocessed/" + target.split("/")[-1]
    if not dir_exists(out_dir):
        os.mkdir(out_dir)
    u = Utils.Utils(preprocessed_path)
    for filename in os.listdir(preprocessed_path):
        if filename.endswith('.preprocessed'):
            u.run_cmd(cwd + "/c2xml " + filename + " > " + out_dir + "/" + filename)

if __name__ == "__main__":
    main()