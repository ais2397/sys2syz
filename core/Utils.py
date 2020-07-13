# Module : Utils.py
# Description : Contains basic utility functions required for all modules
import os
import subprocess
import logging

class Utils(object):

    @staticmethod
    def file_exists(path, exit=False):
        if os.path.isfile(path):
            return True
        else:
            logging.warn("[+] No file found at %s" % path)
            if exit:
                exit(0)
            return False

    @staticmethod
    def compile_file(file, args, exit=False):
        # TODO: complete this
        subprocess.check_call()
