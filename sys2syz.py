# User imports
from core.Utils import *
from core.Bear import *

# Default imports 
import argparse
import logging
import os

def main():
    # Parse the command line arguments
    parser = argparse.ArgumentParser(description="Sys2Syz : A Utility to convert Syscalls and Ioctls to Syzkaller representation")

    parser.add_argument("-t", "--target", help="target file to generate descriptions for", type=str, required=True)
    parser.add_argument("-c", "--compile-commands", help="path to compile_commands.json", type=str, required=True)
    parser.add_argument("-v", "--verbosity", help="make Griller spit more things out", action="store_true")
    args = parser.parse_args()

    target = os.path.realpath(args.target)
    Utils.file_exists(target, True)
    logging.info("[+] The target file is %s", target)

    compile_commands = os.path.realpath(args.compile_commands)
    Utils.file_exists(compile_commands, True)
    logging.info("[+] The compile commands is %s", compile_commands)

    verbose = args.verbose

    bear = Bear(target, compile_commands, verbose)
    bear.compile_target()

if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)
    main()