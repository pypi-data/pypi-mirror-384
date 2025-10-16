import unittest
import gphl

class TestGraph(unittest.TestCase):

    def setUp(self):
        self.graph = gphl.Graph(False)
        self.graph.addNode("A")
        self.graph.addNode("B")
        self.graph.addNode("C")
        self.graph.addNode("D")
        self.graph.addNode("E")
        self.graph.addEdge("A", "B", 4)
        self.graph.addEdge("A", "C", 2)
        self.graph.addEdge("B", "D", 5)
        self.graph.addEdge("C", "D", 8)
        self.graph.addEdge("C", "E", 10)
        self.graph.addEdge("D", "E", 2)

    def test_add_node(self):
        self.assertTrue(self.graph.hasNode("A"))

    def test_add_edge(self):
        # This is implicitly tested by the other methods
        pass

    def test_has_cycle(self):
        cyclic_graph = gphl.Graph(True)
        cyclic_graph.addNode("A")
        cyclic_graph.addNode("B")
        cyclic_graph.addNode("C")
        cyclic_graph.addEdge("A", "B")
        cyclic_graph.addEdge("B", "C")
        cyclic_graph.addEdge("C", "A")
        self.assertTrue(cyclic_graph.hasCycle())

    def test_node_coloring(self):
        colors = self.graph.nodeColoring()
        self.assertEqual(len(colors), 5)

    def test_is_bipartite(self):
        self.assertFalse(self.graph.isBipartite())

    def test_connected_components(self):
        components = self.graph.connectedComponents()
        self.assertEqual(len(components), 1)

    def test_katz_centrality(self):
        centrality = self.graph.katzCentrality()
        self.assertEqual(len(centrality), 5)

    def test_minimum_spanning_tree(self):
        mst = self.graph.minimumSpanningTree(gphl.MSTAlgo.KRUSKAL)
        total_weight = sum(edge.getWeight() for edge in mst)
        self.assertEqual(total_weight, 13)

    def test_iterative_dfs(self):
        path = self.graph.iterativeDFS("A")
        self.assertEqual(len(path), 5)

    def test_shortest_path(self):
        path = self.graph.shortestPath("A", "E", gphl.ShortestPathAlgo.DIJKSTRA, lambda x, y: 0)
        self.assertEqual(path, ["A", "B", "D", "E"])

    def test_edge_coloring(self):
        colors = self.graph.edgeColoring()
        self.assertEqual(len(colors), 6)

    def test_degree_centrality(self):
        centrality = self.graph.degreeCentrality()
        self.assertEqual(centrality["A"], 2)
        self.assertEqual(centrality["E"], 2)

    def test_closeness_centrality(self):
        centrality = self.graph.closenessCentrality()
        self.assertGreater(centrality["C"], centrality["A"])

    def test_betweenness_centrality(self):
        centrality = self.graph.betweennessCentrality()
        self.assertGreater(centrality["C"], centrality["A"])

    def test_save_load(self):
        filename = "test_graph.json"
        self.graph.save(filename)
        loaded_graph = gphl.Graph.load(filename)
        self.assertEqual(len(self.graph.degreeCentrality()), len(loaded_graph.degreeCentrality()))
        self.assertEqual(len(self.graph.edgeColoring()), len(loaded_graph.edgeColoring()))

if __name__ == '__main__':
    unittest.main()
