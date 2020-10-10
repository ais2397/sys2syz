# Module : Extractor.py
# Description : Extracts the necessary details from the source code
from core.Utils import *

import logging
from os.path import join
import os
import re
import collections

class Extractor(object):
    def __init__(self, target):
        self.target = target
        self.files = os.listdir(self.target)
        self.command_macros = []

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
                        self.command_macros.append(command)
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
        """
        Fetch all the macros defined
        :return:
        """
        try:
            macros_defined = []
            #del_buf = open("del_buf", "w")
            undefined_macros = []
            macros = re.compile("#define\s*\t*([A-Z_0-9]*)\t*\s*.*")
            target = self.target + "/"
            for file in header_files:
                with open(target+file) as fd:
                    logging.info("target file opened " + target + file)
                    buf = fd.read()
                    #del_buf.write(file + "\n--------------\n" + buf)
                    undefined_macros.extend(macros.findall(buf))
            return list(set(undefined_macros)-set(self.command_macros))
        except Exception as e:
            logging.error(e)
            print("Fails to fetch flags")

    def flag_details(self, flags_defined):
        try:
            all_macros = dict()
            search_dir = os.getcwd() + "/out/preprocessed/" + self.target.split("/")[-1]
            macros = re.compile("#define(\s|\t)+([^_][A-Z_0-9]*)\t*\s*.*")
            for file in os.listdir(search_dir):
                if file.endswith(".i"):
                    with open(join(search_dir, file)) as fd:
                        logging.debug("target file opened " + join(self.target, file))
                        # placeholders during iteration
                        prevline = None
                        currset = None
                        currset_start = None
                        # to hold current file macros
                        curr_file_macros = []
                        # Iterate through all the lines in the file
                        for linenum, line in enumerate(fd.readlines()):
                            mobj = macros.match(line)
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
            
            print(all_macros)
            return all_macros
        except Exception as e:
            logging.error(e)
            print("Failed to fetch flag details")

    def get_syscalls(self, source):
        # Get the syscall args
        # use regex to match the syscall file you used to use
        # get the details
        return details