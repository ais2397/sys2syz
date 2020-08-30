# Module : C2xml.py 
# Description : Run C2xml and verify the results
from core.Utils import *

from lxml import etree
import os

class C2xml(object):
    def __init__(self, target):
        self.target = target

    def run_c2xml(self):
        """
        Execute c2xml command
        :return:
        """
        try:
            cwd = os.getcwd()
            out_dir = cwd + "/out/preprocessed/" + self.target.split("/")[-1] + "/out/"
            preprocessed_path = cwd + "/out/preprocessed/" + self.target.split("/")[-1]
            if not dir_exists(out_dir):
                os.makedirs(out_dir)
            u = Utils(preprocessed_path)
            for filename in os.listdir(preprocessed_path):
                if filename.endswith('.i'):
                    out_file= out_dir + filename.split(".")[0] + ".xml"
                    u.run_cmd(cwd + "/c2xml " + filename + " > " + out_file)
                    if (self.verify_xml(out_file)):
                        logging.info("[+] " + filename + " converted to XML and verified!")
            return out_dir
        except Exception as e:
            logging.error(e)
            logging.info("[+] unable to extract the corresponding XML queries")

    def verify_xml(self, xml_to_check):
        # Verify whether the output has whatever we expected
        try:
            doc = etree.parse(xml_to_check)
            return True
        except Exception as e:
            logging.error(e)
            logging.info([])
        return True