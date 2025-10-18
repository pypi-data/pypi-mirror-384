import unittest
from crdclib import crdclib as cl


class TestGetCDERecord(unittest.TestCase):

    def test_getCDERecord(self):
        longname = "Electronic Data File Size Integer"
        cde_id = 11479876
        cde_version = 1
        cderef = cl.getCDERecord(cde_id, cde_version)
        self.assertEqual(cderef['DataElement']['longName'], longname)
        bad_id = "11479876$"
        badref = cl.getCDERecord(bad_id, cde_version)
        self.assertEqual(badref['status'], 'error')


if __name__ == "__main__":
    unittest.main(verbosity=2)
