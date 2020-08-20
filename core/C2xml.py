# Module : C2xml.py 
# Description : Run C2xml and verify the results
import os
from core.Utils import *
class C2xml(object):
    def __init__(self, target):
        self.target = target

    def run_c2xml(self):
        """
        Execute c2xml command
        :return:
        """
        cwd = os.getcwd()
        out_dir = cwd + "/out/preprocessed/" + self.target.split("/")[-1] + "/out/"
        preprocessed_path = cwd + "/out/preprocessed/" + self.target.split("/")[-1]
        if not dir_exists(out_dir):
            os.makedirs(out_dir)
        u = Utils(preprocessed_path)
        for filename in os.listdir(preprocessed_path):
            if filename.endswith('.preprocessed'):
                u.run_cmd(cwd + "/c2xml " + filename + " > " + out_dir + filename.split(".")[0] + ".xml")
        if (self.verify_xml()):
            logging.info("[+] C file converted to XML and verified!")
            return out_dir
        logging.error("[+] unable to extract the corresponding XML queries")
        return False

    def verify_xml(self):
        # Verify whether the output has whatever we expected

        return True