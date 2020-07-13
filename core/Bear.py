# Module : Bear.py 
# Description : Contains functions which handle the compilation of a file

import Utils

import os
import logging

class Bear(object):
    def __init__(self, target, compile_commands, verbose):
        self.target = target
        self.compile_commands = compile_commands
    
    def compile_target(self):
        args = self.parse_compile_commands()
        Utils.compile_file(self.target, args, exit=True)
        compiled = True # modify based on the result
        if (compiled):
            logging.info("[+] Preprocessing completed!")
            return True 
        else:
            logging.info("[+] Unable to preprocess the file! Exiting..")
            exit(-1)
            return False

    def parse_compile_commands(self):
        # open compile commands
        # read the data for a file
        extracted_args = ""
        return extracted_args