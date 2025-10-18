import unittest
import os
from crdclib import crdclib as cl


class TestGetCreds(unittest.TestCase):

    def test_getCreds(self):
        os.environ['LOCALTESTAPI'] = 'local_test_environment_variable'
        check_dict = {'url': 'https://this.is.a.test/url/graphql', 'token': 'local_test_environment_variable'}
        self.assertEqual(cl.dhAPICreds('localtest'), check_dict)


if __name__ == "__main__":
    unittest.main(verbosity=2)
