import unittest
from crdclib import crdclib as cl
from bento_meta.model import Model

class TestAddMDFEdges(unittest.TestCase):

    def test_mdfAddEdges(self):
        mdf = Model(handle='TestModel', version='1.0.0')
        nodelist = ['nodeA', 'nodeB', 'nodeC','Yabba', 'Dabba', 'Doo']
        mdf = cl.mdfAddNodes(mdf, nodelist)

        edglist = [{'handle': 'of_yabba', 'multiplicity': 'one-to-one', 'src': 'nodeA', 'dst': 'Yabba'},
                   {'handle': 'of_dabba', 'multiplicity': 'many-to-one', 'src': 'nodeB', 'dst': 'Dabba'}]
        
        mdf = cl.mdfAddEdges(mdf, edglist)
        
        self.assertEqual([('of_yabba', 'nodeA', 'Yabba'), ('of_dabba', 'nodeB', 'Dabba')], list(mdf.edges))
        
if __name__ == "__main__":
    unittest.main(verbosity=2)