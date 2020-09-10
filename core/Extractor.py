# Module : Extractor.py
# Description : Extracts the necessary details from the source code
from core.Utils import *

import logging
import os
import re
import collections

class Extractor(object):
    def __init__(self, target):
        self.target = target
        self.files = os.listdir(self.target)

    def get_ioctls(self, header_files):
        """
        Fetch the ioctl commands with their arguments and sort them on the basis of their type
        :return:
        """

        try:
            command_descs = ""
            ioctl_commands = []
            command_file = []
            for file in header_files:
                fd = open(self.target + "/" + file, "r")
                content = fd.readlines()
                fd.close()
                io = re.compile("#define\s+(.*)\s+_IO\((.*)\).*")
                iow = re.compile("#define\s+(.*)\s+_IOW\((.*),\s+(.*),\s+(.*)\).*")
                ior = re.compile("#define\s+(.*)\s+_IOR\((.*),\s+(.*),\s+(.*)\).*")
                iowr = re.compile("#define\s+(.*)\s+_IOWR\((.*),\s+(.*),\s+(.*)\).*")
                for line in content:
                    io_match = io.match(line)
                    iow_match = iow.match(line)
                    ior_match = ior.match(line)
                    iowr_match = iowr.match(line)
                    command_desc = []
                    if io_match:
                        command = io_match.groups()[0].strip()
                        command_desc = ["null", command, "null"]
                        command_file.append(file)
                    elif ior_match:
                        command = ior_match.groups()[0].strip()
                        description = ior_match.groups()[-1]
                        command_desc = ["in", command, description]
                        command_file.append(file)
                    elif iow_match:
                        command = iow_match.groups()[0].strip()
                        description = iow_match.groups()[-1]
                        command_desc = ["out", command, description]
                        command_file.append(file)
                    elif iowr.match(line):
                        command = iowr_match.groups()[0].strip()
                        description = iowr_match.groups()[-1]
                        command_desc = ["inout", command, description]
                        command_file.append(file)
                    if command_desc:
                        ioctl_commands.append(command_desc)
                        command_descs += ", ".join(command_desc) + "\n"
                        command_file.append(file)
                logging.debug("[*] Analysed " + file)
            if command_descs == "":
                logging.debug("[*] Doesn't have Ioctl calls")
                return None, None
            else:
                #store commands in a file named ioctl_commands.txt in the corresponding out/<target> folder 
                output_file_path = os.getcwd() + "/out/preprocessed/" + self.target.split("/")[-1] + "/"
                if not Utils.dir_exists(output_file_path, False):
                    os.makedirs(output_file_path)
                output_file = open(output_file_path + "ioctl_commands.txt", "w")
                output_file.write(command_descs)
                logging.debug("[*] Ioctl commands stored at " + output_file_path + "ioctl_commands.txt")
                output_file.close()
                return str(output_file_path + "ioctl_commands.txt"), set(command_file)
        except Exception as e:
            logging.exception(e)
            print("Error occurred while Extracting ioctl commands")
    

    def get_header_files(self):
        """
        Find all the header files in device folder
        :return: list of header files
        """
        try:
            header_files = []
            for filename in self.files:
                if filename.endswith('.h'):
                    header_files.append(filename)
            return header_files
        except Exception as e:
            logging.exception(e)
            print("Error while fetching header files")


    def fetch_flags(self, header_files):
        try:
            macros_defined = []
            #del_buf = open("del_buf", "w")
            undefined_macros = []
            MacroDetails = collections.namedtuple("MacroDetails", ["struct_name", "element_name", "macros"])
            struct_str = re.compile("struct\s*([a-z0-9_ ]*)\s*{.*\n(\t*\s*[a-z0-9]*\s*\t*[A-Za-z0-9,;\s*-\.\\/\*\\\#\{\(\)\[\]_]*)\n};")
            element_str = re.compile("([a-zA-Z]+);((?!#define).)*\n((#define.*\n*)+)")
            macros_str = re.compile("#define\s*\t*([A-Z_]*).*")
            #"\t[a-z_]*\s*\t*([a-zA-Z]*);.*\n#define\s*\t*[A-Z_]*\s*\t*[0-9x\t]*.*\n*\")
            target = self.target + "/"
            for file in header_files:
                with open(target+file) as fd:
                    print(file)            
                    logging.info("target file opened " + target + file)
                    buf = fd.read()
                    #del_buf.write(file + "\n--------------\n" + buf)
                    undefined_macros.extend(macros_str.findall(buf))
                    struct_details = re.findall(struct_str, buf)
                    #print(buf)
                    logging.debug("structs found: "+ str(struct_details))
                    for struct in struct_details:                    
                        #print("-"*50)
                        print(str(struct[0]))# + ": \n" + struct[1])
                        elements_details = element_str.findall(struct[1])
                        #print(elements_details)
                        if elements_details is not None:
                            for element in elements_details:
                                #print("[*] " + element[2])
                                macros = self.parse_macros(element[2])
                                macros_defined.append(MacroDetails(struct[0], element[0], macros))
                                undefined_macros = list(set(undefined_macros)-set(macros))
            #del_buf.close()
            print(macros_defined)
            print(undefined_macros)
            return macros_defined, undefined_macros
        except Exception as e:
            logging.error(e)
            print("Fails to fetch flags")
        

    def parse_macros(self, macro_details):
        macro_groups = [] 
        macros_array = macro_details.split("\n")
        #print("macros" + str(macros_array))
        macros = re.compile("#define\s*\t*([A-Z_]*).*")
        for macro in macros_array:
            macro_match = macros.match(macro)
            if macro_match is not None:
                macro_groups.append(macro_match.groups()[0])
        return macro_groups

    def get_syscalls(self, source):
        # Get the syscall args
        # use regex to match the syscall file you used to use
        # get the details
        return details