import unittest
from crdclib import crdclib as cl
from bento_meta.model import Model

class TestAddMDFEnums(unittest.TestCase):

    def test_mdfAddEnums(self):
        mdf = Model(handle='TestModel', version='1.0.0')
        prop_dictionary1 = {'nodeA': [{'prop':'PropertyA', 'isreq': 'Yes', 'val': 'value_set', 'desc': 'Test Property 1' }]}
        mdf = cl.mdfAddProperty(mdf, prop_dictionary1, True)

        enumlist = ['Yabba', 'Dabba', 'Doo']
        mdf = cl.mdfAddEnums(mdf, 'nodeA', 'PropertyA', enumlist)

        
        self.assertEqual(['Yabba', 'Dabba', 'Doo'], list(mdf.props[('nodeA', 'PropertyA')].value_set.terms))

if __name__ == "__main__":
    unittest.main(verbosity=2)