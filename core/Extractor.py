# Module : Extractor.py
# Description : Extracts the necessary details from the source code
import Utils

import os
import re

class Extractor(object):
    def __init__(self, target):
        self.target = target

    def get_ioctls(self, header_files):

        # Get the headers
        # use regex to match the IO calls
        # get the structure names and details
        try:
            ioctl_commands = []
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
                    elif ior_match:
                        command = ior_match.groups()[0].strip()
                        description = ior_match.groups()[-1]
                        command_desc = ["in", command, description]
                    elif iow_match:
                        command = iow_match.groups()[0].strip()
                        description = iow_match.groups()[-1]
                        command_desc = ["out", command, description]
                    elif iowr.match(line):
                        command = iowr_match.groups()[0].strip()
                        description = iowr_match.groups()[-1]
                        command_desc = ["inout", command, description]
                    if command_desc:
                        ioctl_commands.append(command_desc)
        except:
            print("Error occurred while Extracting ioctl commands")
        return ioctl_commands
    

    def get_header_files(self):
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