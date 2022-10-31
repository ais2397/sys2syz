# Module : C2xml.py 
# Description : Run C2xml and verify the results
from core.utils import *
from core.logger import get_logger

from os.path import join, basename, isdir, isfile, exists
from lxml import etree
import os

class C2xml(object):
    def __init__(self, sysobj):
        self.sysobj = sysobj
        self.target = sysobj.target
        self.output_path = sysobj.out_dir
        self.logger = get_logger("C2xml", sysobj.log_level)

    def run_c2xml(self):
        """
        Execute c2xml command
        :return:
        """
        cwd = os.getcwd()
        preprocessed_path = join(os.getcwd(), "out/", self.sysobj.os, "preprocessed/", basename(self.target))
        if not dir_exists(self.output_path):
            os.makedirs(self.output_path)
        for filename in os.listdir(preprocessed_path):
            if filename.endswith('.i'):
                out_file = join(self.output_path, filename.split(".")[0] + ".xml")
                Utils(preprocessed_path).run_cmd(cwd + "/c2xml " + filename + " > " + out_file)
                if (self.verify_xml(out_file)):
                    self.logger.debug("[+] " + filename + " converted to XML and verified!")
                else:
                    return False
        self.logger.debug("[+] Generated XML files for corresponding C code.")

    def verify_xml(self, xml_to_check):
        # Verify whether the output has whatever we expected
        try:
            etree.parse(xml_to_check)
            print(xml_to_check)
            return True
        except Exception as e:
            self.logger.error(e)
            self.logger.warning( xml_to_check + ": Corrupted XML file" )
        return False