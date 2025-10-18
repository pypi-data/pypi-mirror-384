import unittest
import sys
import os
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/../src")
from crdclib import crdclib as cl

class TestGetCDERecord(unittest.TestCase):
    def test_getSTSCCPVs(self):
        cdeid = '7572817'
        cdeversion = '3.00'
        cdeinfo = cl.getSTSCCPVs(cdeid, cdeversion)
        self.assertEqual(cdeinfo, {'C17998':'Unknown', 'C20197':'Male', 'C16576':'Female'})
        empty_cdeid = '11479876'
        empty_cdeversion = '1.00'
        empty_cdeinfo = cl.getSTSCCPVs(empty_cdeid, empty_cdeversion)
        self.assertEqual(empty_cdeinfo, None)

if __name__ == "__main__":
    unittest.main(verbosity=2)