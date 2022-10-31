# Module : Bear.py 
# Description : Contains functions which handle the compilation of a file
from core.utils import Utils
from core.logger import get_logger

import os
import collections
import json

INVALID_GCC_FLAGS = ['-mno-thumb-interwork', '-fconserve-stack', '-fno-var-tracking-assignments',
                     '-fno-delete-null-pointer-checks', '--param=allow-store-data-races=0',
                     '-Wno-unused-but-set-variable', '-Werror=frame-larger-than=1', '-Werror', '-Wall',
                     '-fno-jump-tables', '-nostdinc', '-mpc-relative-literal-loads', '-mabi=lp64']


class Bear(object):
    def __init__(self, sysobj):
        self.sysobj = sysobj
        self.target = self.sysobj.target
        self.compile_commands = self.sysobj.compile_commands
        self.verbosity = self.sysobj.log_level

        self.logger = get_logger("Bear", self.verbosity)
        self.output_path = os.path.join(os.getcwd(), "out/", self.sysobj.os, "preprocessed/")

    def compile_target(self, compilation_commands) -> bool:
        """
        Generates preprocessed files.
        :return: True
        """
        
        for curr_command in compilation_commands:
            self.logger.debug("[*] Initialising the environment " + curr_command[1])
            Utils(curr_command[1]).run_cmd(f"{' '.join(curr_command[0])} > {curr_command[3]}", doexit = True)
        return True

    def parse_compile_commands(self, target_path=None) -> bool:
        """
        Parses commands recorded by bear
        :return:
        """
        CompilationCommand = collections.namedtuple("CompilationCommand", ["curr_args", "work_dir", "src_file", "output_file"])
        commands = []

        try: 
            self.logger.debug("[*] Parsing compile_commands.json")
            fp = open(self.compile_commands, "r")
            all_cont = fp.read()
            fp.close()
        except IOError:
            self.logger.error("Unable to open compile_commands file for reading")
            return False

        json_obj = json.loads(all_cont)
        if self.sysobj.input_type =="ioctl":
            target_name = os.path.basename(self.target)
            if self.sysobj.os_type == 1:
                target_path = "/dev/" + target_name
            elif self.sysobj.os_type == 2:
                target_path = "drivers/" + target_name
        else:
            target_name = self.target
        
        output_path = os.path.join(os.getcwd(), "out/", self.sysobj.os, "preprocessed/", target_name)

        if not Utils.dir_exists(output_path):
            os.makedirs(output_path)
        flag = 0

        for curr_command in json_obj:
            src_file = curr_command["file"]
            if target_path in src_file:
                flag = 1
                curr_args = curr_command["arguments"]
                args = []
                i = 0
                # convert each string in the argument into a python friendly escaped string.
                while i < len(curr_args):
                    cura = curr_args[i]
                    if '="' in cura:
                        cn = cura.index('="')
                        curr_args[i] = cura[0:cn+1] + "'" + cura[cn+1:]
                        curr_args[i] = curr_args[i] + "'"
                    if "-o" in curr_args[i]:
                        del_arg = curr_args[i+1]
                        curr_args.remove(curr_args[i])
                        curr_args.remove(del_arg)
                    i += 1
                curr_args[0] += (" -fdirectives-only -E")
                work_dir = curr_command["directory"]
                output_file = output_path + "/"+ src_file.split("/")[-1].split(".")[0] + ".i" 
                self.logger.debug("[*] Extracting commands for " + src_file.split("/")[-1] )
                commands.append(CompilationCommand(curr_args, work_dir, src_file, output_file))
        
        if flag == 0:
            self.logger.error("Unable to find the target in compile_commands.json")
            return False
        else:
            self.logger.debug("[*] Found the target in compile_commands.json")
            return self.compile_target(commands)

def is_gcc_flag_allowed(curr_flag):
    """
    Filter out the optimisation flags
    :return: True
    """
    # Remove optimization flags
    if str(curr_flag)[:2] == "-O":
        return False

    # if the flag is invalid
    for curr_in_flag in INVALID_GCC_FLAGS:
        if curr_flag.startswith(curr_in_flag):
            return False
    return True