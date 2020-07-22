import json
import collections
import os
import sys


"""
Handles parsing json file produced by the Bear
"""

CompilationCommand = collections.namedtuple("CompilationCommand", ["curr_args", "work_dir", "src_file", "output_file"])

def parse_compile_json(json_file_path, driver_name):
    """
        Parse the json file output of Bear
    :param json_file_path: Path to the output json file of Bear
    :return: pair of compilation and linker commands.
    """
    compile_commands = []
    if os.path.exists(json_file_path):
        try:
            fp = open(json_file_path, "r")
            all_cont = fp.read()
            fp.close()
            json_obj = json.loads(all_cont)
            driver_path = "/dev/" + driver_name
            # it contains array of commands
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
                    output_file = "out/"+src_file.split("/")[-1]
                    compile_commands.append(CompilationCommand(curr_args, work_dir, src_file, output_file))

        except:
            print("Error occurred while trying to parse provided json file")
    else:
        print("Provided json file doesn't exist")
    return compile_commands