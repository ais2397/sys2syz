# Module : Extractor.py
# Description : Extracts the necessary details from the source code
from core.Utils import *

import logging
import os
import re

class Extractor(object):
    def __init__(self, target):
        self.target = target

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
        
        header_files = []
        for filename in os.listdir(self.target):
            if filename.endswith('.h'):
                header_files.append(filename)
        return header_files    

    def get_syscalls(self, source):
        # Get the syscall args
        # use regex to match the syscall file you used to use
        # get the details
        return details