# Module : Utils.py
# Description : Contains basic utility functions required for all modules
import os
import subprocess
import logging

class Utils(object):
    ENV_NONE = 0

    def __init__(self, cwd):
        self.cwd = cwd

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
    def dir_exists(path, exit=False):
        if os.path.isdir(path):
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
    
    @staticmethod 
    def create_dir(path):
        if os.path.exists(path):
            logging.debug("Directory already exists not creating")
            return False
        else:
            try:
                os.mkdir(path)
            except Exception as e:
                logging.exception(e)
                logging.critical("Unable to create directory")
                return False
            return True

    @staticmethod
    def delete_dir(path):
        if os.path.isdir(path):
            shutil.rmtree(path)
            return True
        else:
            logging.debug("Unable to delete directory")

    def delete_file(path):
        if os.path.isfile(path):
            os.remove(path)
        else:
            logging.warn("[+] No file found at %s" % path)

    def get_env(self, version):
        my_env = os.environ.copy()
        if version == self.ENV_NONE:
            return my_env
            
    def run_cmd(self, command, env=ENV_NONE, doexit=False):
        try:
            subprocess.check_call(command, env=self.get_env(env), shell=True, cwd=self.cwd)
        except Exception as e:
            logging.exception(e)
            logging.critical("Unable to run command : {}".format(command))
            if doexit:
                exit(-1)

    def run_silent_cmd(self, command, env=ENV_NONE, doexit=False):
        try:
            subprocess.check_call(command, env=self.get_env(env), shell=True, cwd=self.cwd, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
        except Exception as e:
            logging.exception(e)
            logging.critical("Unable to run command : {}".format(command))
            if doexit:
                exit(-1)

    def run_and_get_output(self, command, env=ENV_NONE, doexit=False):
        try:
            out = subprocess.check_output(command, env=self.get_env(env), cwd=self.cwd, shell=True, stderr=subprocess.STDOUT)
            return out
        except Exception as e:
            logging.exception(e)
            logging.critical("Unable to run command : {}".format(command))
            if doexit:
                exit(-1)

def file_exists(path, exit=False):
    if os.path.isfile(path):
        return True
    else:
        logging.warn("[+] No file found at %s" % path)
        if exit:
            exit(0)
        return False

def dir_exists(path, exit=False):
    if os.path.isdir(path):
        return True
    else:
        logging.warn("[+] No file found at %s" % path)
        if exit:
            exit(0)
        return False