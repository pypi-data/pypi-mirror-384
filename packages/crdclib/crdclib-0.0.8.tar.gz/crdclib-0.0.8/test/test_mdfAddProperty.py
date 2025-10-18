import unittest
from crdclib import crdclib as cl
from bento_meta.model import Model

class TestAddMDFProps(unittest.TestCase):

    def test_mdfAddProperty(self):
        mdf = Model(handle='TestModel', version='1.0.0')
        nodelist = ['nodeA']
        prop_dictionary1 = {'nodeA': [{'prop':'PropertyA', 'isreq': 'Yes', 'val': 'value_set', 'desc': 'Test Property 1' }]}
        prop_dictionary2 = {'nodeB': [{'prop':'PropertyB', 'isreq': 'No', 'val': 'String', 'desc': 'Test Property 2'}]}

        mdf = cl.mdfAddNodes(mdf, nodelist)
        mdf = cl.mdfAddProperty(mdf, prop_dictionary1, False)
        self.assertEqual(('nodeA', 'PropertyA'), list(mdf.model.props))
        mdf = cl.mdfAddProperty(mdf, prop_dictionary2, True)
        self.assertTrue(('nodeB', 'PropertyB') in list(mdf.model.props))

if __name__ == "__main__":
    unittest.main(verbosity=2)