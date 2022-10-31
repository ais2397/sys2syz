# Module : Extractor.py
# Description : Extracts the necessary details from the source code
from core.utils import Utils
from core.logger import get_logger

from os.path import join, basename, isdir, isfile, exists
import os
import re
import collections

class Ioctl(object):
    IO = 1
    IOW = 2
    IOR = 3
    IOWR = 4
    types = {IO: 'null', IOW: 'in', IOR: 'out', IOWR: 'inout'}

    def __init__(self, gtype, filename, command, description=None):
        self.type = gtype
        self.command = command
        self.filename = filename
        self.description = description

    def __repr__(self):
        return str(self.types[self.type]) + ", " + str(self.command)  + ", " + str(self.filename) + ", " + str(self.description)

class Extractor(object):

    #define a regex map for the ioctls corresponding to OS
    ioctl_regex_map = {
        1: "linux_type", 2: "linux_type"
    }
    
    #define regex for the different variations of all the ioctl commands found accross the supported OSes
    ioctl_regex_type = { 
        "linux_type": {
            "io": re.compile(r"#define\s+(.*)\s+_IO\((.*)\).*"), # regex for IO_ 
            "iow": re.compile(r"#define\s+(.*)\s+_IOW\((.*),\s+(.*),\s+(.*)\).*"), #regex for IOW_
            "ior": re.compile(r"#define\s+(.*)\s+_IOR\((.*),\s+(.*),\s+(.*)\).*"), #regex for IOR_
            "iowr" : re.compile(r"#define\s+(.*)\s+_IOWR\((.*),\s+(.*),\s+(.*)\).*") #regex for IOWR_
        }
    }
    
    #io = re.compile(r"#define\s+(.*)\s+_IO\((.*)\).*") # regex for IO_ 
    #iow = re.compile(r"#define\s+(.*)\s+_IOW\((.*),\s+(.*),\s+(.*)\).*") #regex for IOW_
    #ior = re.compile(r"#define\s+(.*)\s+_IOR\((.*),\s+(.*),\s+(.*)\).*") #regex for IOR_
    #iowr = re.compile(r"#define\s+(.*)\s+_IOWR\((.*),\s+(.*),\s+(.*)\).*") #regex for IOWR_
    macros = re.compile(r"#define\s*\t*([A-Z_0-9]*)\t*\s*.*")
    more_macros = re.compile(r"#define(\s|\t)+([A-Z_0-9]*)[\t|\s]+(?!_IOWR|_IOR|_IOW|_IO|\()[0-9]*x?[a-z0-9]*")#define(\s|\t)+([A-Z_0-9]*)[\t\s]+([^_IOWR{][0-9]*)")#define(\s|\t)+([^_][A-Z_0-9]*)\t*\s*.*")
    
    def __init__(self, sysobj):
        self.sysobj = sysobj
        self.target = sysobj.target
        self.files = os.listdir(self.target)
        self.logger = get_logger("Extractor", sysobj.log_level)
        self.os_type = sysobj.os_type
        self.ioctl_type = self.ioctl_regex_map[self.os_type]

        self.ioctls = []
        self.target_dir = join(os.getcwd(), "out/", self.sysobj.os, "preprocessed/", basename(self.target))
        
        if not exists(self.target_dir):
            os.mkdir(self.target_dir)
        self.ioctl_file = ""

    def get_ioctls(self):
        """
        Fetch the ioctl commands with their arguments and sort them on the basis of their type
        :return:
        """
        
        for file in self.header_files:
            try:
                fd = open(join(self.target, file), "r")
                content = fd.readlines()
                fd.close()
            except IOError:
                self.logger.error("Unable to read the file '%s'", file)
                self.logger.critical("Skipping this file")
                continue

            for line in content:
                io_match = self.ioctl_regex_type[self.ioctl_type]["io"].match(line)
                if io_match:
                    self.ioctls.append(Ioctl(Ioctl.IO, file, io_match.groups()[0].strip()))
                    continue
                        
                ior_match = self.ioctl_regex_type[self.ioctl_type]["ior"].match(line)
                if ior_match:
                    self.ioctls.append(Ioctl(Ioctl.IOR, file, ior_match.groups()[0].strip(), ior_match.groups()[-1]))
                    continue

                iow_match = self.ioctl_regex_type[self.ioctl_type]["iow"].match(line)
                if iow_match:
                    self.ioctls.append(Ioctl(Ioctl.IOW, file, iow_match.groups()[0].strip(), iow_match.groups()[-1]))
                    continue
                
                iowr_match = self.ioctl_regex_type[self.ioctl_type]["iowr"].match(line)
                if iowr_match:
                    self.ioctls.append(Ioctl(Ioctl.IOWR, file, iowr_match.groups()[0].strip(), iowr_match.groups()[-1]))
                    continue

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

    @property
    def command_macros(self) -> list:
        """Finds all the commands in the Ioctls

        Returns:
            list: list of generated ioctls
        """
        commands = []
        for ioctl in self.ioctls:
            commands.append(ioctl.command)
        return commands
    
    @property
    def ioctl_files(self) -> list:
        """Finds all the files where Ioctls are defined

        Returns:
            list: list of files
        """
        files = set()
        for ioctl in self.ioctls:
            files.add(ioctl.filename)
        return list(files)


    def fetch_flags(self):
        """
        Fetch all the macros defined
        :return:
        """
        undefined_macros = []
        #read all the files present in target
        for file in self.header_files:
            try:
                buf = open(join(self.target, file), 'r').read()
                undefined_macros.extend(self.macros.findall(buf))
            except IOError:
                self.logger.error("Unable to open " + join(self.target, file))

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
                fd = open(join(self.target_dir, file), "r")
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