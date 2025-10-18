import unittest
from crdclib import crdclib as cl
from bento_meta.model import Model

class TestAddMDFTags(unittest.TestCase):

    def test_mdfAddTags(self):
        mdf = Model(handle='TestModel', version='1.0.0')
        prop_dictionary1 = {'nodeA': [{'prop':'PropertyA', 'isreq': 'Yes', 'val': 'value_set', 'desc': 'Test Property 1' }]}
        prop_dictionary2 = {'nodeB': [{'prop':'PropertyB', 'isreq': 'No', 'val': 'String', 'desc': 'Test Property 2'}]}

        mdf = cl.mdfAddProperty(mdf, prop_dictionary1, True)
        mdf = cl.mdfAddProperty(mdf, prop_dictionary2, True)

        edglist = [{'handle': 'of_nodeA', 'multiplicity': 'one-to-one', 'src': 'nodeB', 'dst': 'nodeA'}]

        mdf = cl.mdfAddEdges(mdf, edglist)

        tag_dict = {'key': 'Barney', 'value':'Rubble'}

        mdf = cl.mdfAddTags(mdf, 'node', 'nodeA', tag_dict)
        mdf = cl.mdfAddTags(mdf, 'property', ('nodeA', 'PropertyA'), tag_dict)
        mdf = cl.mdfAddTags(mdf, 'edge', ('of_nodeA', 'nodeB', 'nodeA'), tag_dict)

        self.assertEqual({'key': 'Barney', 'value': 'Rubble'}, mdf.nodes['nodeA'].tags['Barney'].get_attr_dict())
        self.assertEqual({'key': 'Barney', 'value': 'Rubble'}, mdf.props[('nodeA', 'PropertyA')].tags['Barney'].get_attr_dict())
        self.assertEqual({'key': 'Barney', 'value': 'Rubble'}, mdf.edges['nodeA'].tags['Barney'].get_attr_dict())

if __name__ == "__main__":
    unittest.main(verbosity=2)