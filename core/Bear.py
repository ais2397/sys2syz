# Module : Bear.py 
# Description : Contains functions which handle the compilation of a file

from Utils import Utils

import os
import logging
import collections
import json

INVALID_GCC_FLAGS = ['-mno-thumb-interwork', '-fconserve-stack', '-fno-var-tracking-assignments',
                     '-fno-delete-null-pointer-checks', '--param=allow-store-data-races=0',
                     '-Wno-unused-but-set-variable', '-Werror=frame-larger-than=1', '-Werror', '-Wall',
                     '-fno-jump-tables', '-nostdinc', '-mpc-relative-literal-loads', '-mabi=lp64']

class Bear(object):
    def __init__(self, target, compile_commands, verbose):
        self.target = target
        self.compile_commands = compile_commands
    
    def compile_target(self, compilation_commands):
        try:
            for i, curr_command in enumerate(compilation_commands):
                modified_args=[]
                for curr_flag in curr_command[0]:
                    if is_gcc_flag_allowed(curr_flag):
                        modified_args.append(curr_flag)
                command = " ".join(modified_args) +" -E " + curr_command[1] + "/" + curr_command[2]
                u = Utils(curr_command[1])
                output_file = curr_command[3]
                u.run_cmd(command + " > " + output_file, doexit = True)
        except:
            print "Failed to generate preprocessed files"

    def parse_compile_commands(self):
        CompilationCommand = collections.namedtuple("CompilationCommand", ["curr_args", "work_dir", "src_file", "output_file"])
        # open compile commands
        # read the data for a file
        commands = []
        try:
            fp = open(self.compile_commands, "r")
            all_cont = fp.read()
            fp.close()
            json_obj = json.loads(all_cont)
            driver_path = "/dev/" + self.target.split("/")[-1]
            for curr_command in json_obj:
                src_file = curr_command["file"]
                if driver_path in src_file:
                    curr_args = curr_command["arguments"]
                    i = 0
                    # convert each string in the argument
                    # into a python friendly escaped string.
                    while i < len(curr_args):
                        cura = curr_args[i]
                        if '="' in cura:
                            cn = cura.index('="')
                            curr_args[i] = cura[0:cn+1] + "'" + cura[cn+1:]
                            curr_args[i] = curr_args[i] + "'"
                        i += 1
                    work_dir = curr_command["directory"]
                    output_file = src_file + ".preprocessed" 
                    commands.append(CompilationCommand(curr_args, work_dir, src_file, output_file))
        except:
            print("Error occurred while trying to parse provided json file")
        return commands

def is_gcc_flag_allowed(curr_flag):
    # Remove optimization flag
    if str(curr_flag)[:2] == "-O":
        return False

    # if the flag is invalid
    for curr_in_flag in INVALID_GCC_FLAGS:
        if curr_flag.startswith(curr_in_flag):
            return False

    return True