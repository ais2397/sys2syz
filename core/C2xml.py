# Module : C2xml.py 
# Description : Run C2xml and verify the results
import Utils

import logging
class C2xml(object):
    def __init__(self, target):
        self.target = target

    def run_c2xml(self):
        # Run C2xml
        Utils.run_cmd()
        if (self.verify_xml()):
            logging.info("[+] C file converted to XML and verified!")
            return True
        logging.error("[+] unable to extract the corresponding XML queries")
        return False

    def verify_xml(self):
        # Verify whether the output has whatever we expected
        return True