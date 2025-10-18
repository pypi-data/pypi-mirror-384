import unittest
from crdclib import crdclib as cl
from bento_meta.model import Model

class TestAddMDFTerms(unittest.TestCase):

    def test_mdfAddTerms(self):
        mdf = Model(handle='TestModel', version='1.0.0')
        prop_dictionary1 = {'nodeA': [{'prop':'PropertyA', 'isreq': 'Yes', 'val': 'value_set', 'desc': 'Test Property 1' }]}
        prop_dictionary2 = {'nodeB': [{'prop':'PropertyB', 'isreq': 'No', 'val': 'String', 'desc': 'Test Property 2'}]}

        mdf = cl.mdfAddProperty(mdf, prop_dictionary1, True)
        mdf = cl.mdfAddProperty(mdf, prop_dictionary2, True)

        cdeinfo = {'handle': 'TestCDE', 'value':'TestCDE', 'origin_version': 1.00, 'origin_name': 'CRDCInc.', 'origin_id':12345, 'origin_definition': 'A CDE for testing Only'}
        mdf = cl.mdfAddTerms(mdf, 'nodeA', 'PropertyA', cdeinfo)

        self.assertEqual(cdeinfo, mdf.terms[('TestCDE','CRDCInc.')].get_attr_dict())





if __name__ == "__main__":
    unittest.main(verbosity=2)