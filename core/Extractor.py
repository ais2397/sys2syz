# Module : Extractor.py
# Description : Extracts the necessary details from the source code
from core.Utils import Utils
from logger import get_logger

from os.path import join, basename, isdir, isfile, exists
import os
import re
import collections


class Extractor(object):
    io = re.compile(r"#define\s+(.*)\s+_IO\((.*)\).*") # regex for IO_ 
    iow = re.compile(r"#define\s+(.*)\s+_IOW\((.*),\s+(.*),\s+(.*)\).*") #regex for IOW_
    ior = re.compile(r"#define\s+(.*)\s+_IOR\((.*),\s+(.*),\s+(.*)\).*") #regex for IOR_
    iowr = re.compile(r"#define\s+(.*)\s+_IOWR\((.*),\s+(.*),\s+(.*)\).*") #regex for IOWR_
    macros = re.compile(r"#define\s*\t*([A-Z_0-9]*)\t*\s*.*")
    more_macros = re.compile(r"#define(\s|\t)+([A-Z_0-9]*)[\t|\s]+(?!_IOWR|_IOR|_IOW|_IO|\()[0-9]*x?[a-z0-9]*")#define(\s|\t)+([A-Z_0-9]*)[\t\s]+([^_IOWR{][0-9]*)")#define(\s|\t)+([^_][A-Z_0-9]*)\t*\s*.*")
    
    def __init__(self, sysobj):
        self.sysobj = sysobj
        self.target = sysobj.target
        self.files = os.listdir(self.target)
        self.command_macros = []
        self.logger = get_logger("Extractor", sysobj.log_level)

        self.target_dir = join(os.getcwd(), "out/preprocessed/", basename(self.target))
        
        if not exists(self.target_dir):
            os.mkdir(self.target_dir)
        self.ioctl_file = ""


    def get_ioctls(self, header_files):
        """
        Fetch the ioctl commands with their arguments and sort them on the basis of their type
        :return:
        """
        command_descs = ""
        ioctl_commands = []
        command_file = []
        
        for file in header_files:
            try:
                fd = open(join(self.target, file), "r")
                content = fd.readlines()
                fd.close()
            except IOError:
                self.logger.error("Unable to read the file '%s'", file)
                self.logger.critical("Skipping this file")
                continue

            for line in content:
                # TODO: realign the matches
                command_desc = []
                io_match = self.io.match(line)
                iow_match = self.iow.match(line)
                ior_match = self.ior.match(line)
                iowr_match = self.iowr.match(line)

                #array to store: PTR direction of ioctl call argument, command macro , command arguments
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
                elif iowr_match:
                    command = iowr_match.groups()[0].strip()
                    description = iowr_match.groups()[-1]
                    command_desc = ["inout", command, description]
                    command_file.append(file)
                if command_desc:
                    self.command_macros.append(command)
                    ioctl_commands.append(command_desc)
                    command_descs += ", ".join(command_desc) + "\n"
                    command_file.append(file)
            self.logger.debug("[*] Analysed " + file)

        if command_descs == "":
            self.logger.debug("[*] Doesn't have Ioctl calls")
            return None
        else:
            #store commands in a file named ioctl_commands.txt in the corresponding out/<target> folder 
            output_file_path = join(os.getcwd(), "out/preprocessed", basename(self.target))
            if not exists(output_file_path):
                Utils.create_dir(output_file_path)

            self.ioctl_file = join(output_file_path, "ioctl_commands.txt") 
            output_file = open(self.ioctl_file, "w")
            output_file.write(command_descs)
            output_file.close()

            self.logger.debug(f"[*] Ioctl commands stored at {output_file_path} ioctl_commands.txt")
            # TODO: why are we returning
            return set(command_file)

    @property
    def header_files(self) -> list:
        """
        Find all the header files in device folder
        :return: list of header files
        """
        header_files = []
        for filename in self.files:
            #store all the filenames ending with ".h" in an array
            if filename.endswith('.h'):
                header_files.append(filename)
        return header_files


    def fetch_flags(self, header_files):
        """
        Fetch all the macros defined
        :return:
        """

        undefined_macros = []
        #read all the files present in target
        for file in header_files:
            try:
                buf = open(join(self.target, file), 'r').read()
                undefined_macros.extend(self.macros.findall(buf))
            except IOError:
                self.logger.error("Unable to open " + join(self.target, file))

        #TODO: structure this better
        #return the macros found, except the IOCTL command macros in header files
        return list(set(undefined_macros)-set(self.command_macros))

    def flag_details(self, flags_defined):
        """
        Stores the macros within a particular scope of struct etc. in tuples with the corresponding line numbers.
        :return:
        """

        all_macros = dict()
        for file in filter(lambda x: x if x.endswith(".i") else None, os.listdir(self.target_dir)):
            try:
                fd = open(join(self.target_dir, file))
            except IOError:
                self.logger.error("Unable to open " + join(self.target_dir, file))
                continue
            # placeholders during iteration
            prevline = None
            currset = None
            currset_start = None
            # to hold current file macros
            curr_file_macros = []
            # Iterate through all the lines in the file
            for linenum, line in enumerate(fd.readlines()):
                mobj = self.more_macros.match(line)
                if mobj:
                    # check if for new set or old set
                    define_new_set = False
                    if not prevline:
                        prevline = linenum
                        define_new_set = True
                    else:
                        if linenum - prevline != 1:
                            define_new_set = True
                    # if we need to define a new set append the older one if exists
                    # and then create a new one
                    if define_new_set:
                        if currset:
                            curr_file_macros.append((currset, currset_start, prevline))
                        currset = []
                        currset_start = linenum

                    # Append the set to the old one
                    macro_name = mobj.group(2)
                    if macro_name in flags_defined:
                        currset.append(mobj.group(2))
                        prevline = linenum

            all_macros[file] = curr_file_macros
        return all_macros

    def get_syscalls(self, source):
        # Get the syscall args
        # use regex to match the syscall file you used to use
        # get the details
        return self.syscall_details