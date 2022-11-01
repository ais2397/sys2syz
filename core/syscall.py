from core.utils import Utils
from core.logger import get_logger

import ctags
import os

class Syscall(object):
        def __init__(self, sysobj):
                self.sysobj = sysobj
                self.target = self.sysobj.target
                self.compile_commands = self.sysobj.compile_commands
                self.verbosity = self.sysobj.log_level

                self.logger = get_logger("Syscall", self.verbosity)
                self.output_path = os.path.join(os.getcwd(), "out/", self.sysobj.os, "preprocessed/")
        
        def find_file(self):
                """Find the file containing the syscall definition using ctags"""
                self.logger.debug("[+] Finding syscall definition")
                
                tags_file = os.path.join(os.getcwd(), "tags_dir", "tags_" + self.sysobj.os)
                print(tags_file)
                if not os.path.exists(tags_file):
                        self.logger.critical("[+] Tags file not found")
                        return False
                tags = ctags.CTags(tags_file)
                entry = ctags.TagEntry()
                #find kernel file in which syscall is present using ctags
                if tags.find(entry, bytes(self.target, "utf-8"), ctags.TAG_PARTIALMATCH):
                        self.logger.debug("[+] Found syscall definition in file %s" % entry["file"])
                        ret_name = entry["file"].decode("utf-8").split("/")[-1]
                        return ret_name
                else:
                       
                        self.logger.critical("[+] Syscall not found in tags file")
                        return False
                