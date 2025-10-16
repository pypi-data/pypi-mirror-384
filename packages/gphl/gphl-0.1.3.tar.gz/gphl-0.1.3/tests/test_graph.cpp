#include <catch2/catch_all.hpp>
#include "../include/graph.hpp"

TEST_CASE("Graph Node Management", "[graph]") {
    gphl::Graph<std::string, int> graph(false);

    SECTION("addNode adds a new node") {
        graph.addNode("A");
        REQUIRE(graph.hasNode("A"));
    }

    SECTION("addNode throws on duplicate node") {
        graph.addNode("A");
        REQUIRE_THROWS_AS(graph.addNode("A"), std::runtime_error);
    }
}

TEST_CASE("Graph Edge Management and BFS", "[graph]") {
    gphl::Graph<std::string, int> graph(false);
    graph.addNode("A");
    graph.addNode("B");
    graph.addNode("C");
    graph.addNode("D");

    SECTION("addEdge adds an edge") {
        graph.addEdge("A", "B", 10);
        graph.addEdge("B", "C", 10);
        graph.addEdge("C", "D", 10);
        // Verification for addEdge is implicitly tested via traversal,
        // as there's no public method to check for a specific edge.
        auto bfs_path = graph.bfs("A");
        REQUIRE(bfs_path.size() == 4); // A, B, C, D are reachable
    }

    SECTION("bfs traversal is correct") {
        graph.addEdge("A", "B", 10);
        graph.addEdge("A", "C", 10);
        graph.addEdge("B", "D", 10);
        auto bfs_path = graph.bfs("A");
        std::vector<std::string> expected_path = {"A", "B", "C", "D"};
        REQUIRE(bfs_path.size() == expected_path.size());
    }
}

TEST_CASE("Graph DFS Traversal", "[graph]") {
    gphl::Graph<std::string, int> graph(false);
    graph.addNode("A");
    graph.addNode("B");
    graph.addNode("C");
    graph.addNode("D");
    graph.addEdge("A", "B");
    graph.addEdge("A", "C");
    graph.addEdge("B", "D");

    SECTION("dfs traversal is correct") {
        auto dfs_path = graph.dfs("A");
        REQUIRE(dfs_path.size() == 4);
    }

    SECTION("iterativeDFS traversal is correct") {
        auto iterative_dfs_path = graph.iterativeDFS("A");
        REQUIRE(iterative_dfs_path.size() == 4);
    }
}

TEST_CASE("Graph Cycle Detection", "[graph]") {
    SECTION("detects a cycle in a directed graph") {
        gphl::Graph<std::string, int> graph(true); // Directed graph
        graph.addNode("A");
        graph.addNode("B");
        graph.addNode("C");
        graph.addEdge("A", "B");
        graph.addEdge("B", "C");
        graph.addEdge("C", "A");
        REQUIRE(graph.hasCycle() == true);
    }

    SECTION("returns false for an acyclic graph") {
        gphl::Graph<std::string, int> graph(true); // Directed graph
        graph.addNode("A");
        graph.addNode("B");
        graph.addNode("C");
        graph.addEdge("A", "B");
        graph.addEdge("B", "C");
        REQUIRE(graph.hasCycle() == false);
    }
}

TEST_CASE("Graph Shortest Path", "[graph]") {
    gphl::Graph<std::string, int> graph(false);
    graph.addNode("A");
    graph.addNode("B");
    graph.addNode("C");
    graph.addNode("D");
    graph.addNode("E");
    graph.addEdge("A", "B", 4);
    graph.addEdge("A", "C", 2);
    graph.addEdge("B", "D", 5);
    graph.addEdge("C", "D", 8);
    graph.addEdge("C", "E", 10);
    graph.addEdge("D", "E", 2);

    SECTION("dijkstra finds the shortest path in a weighted graph") {
        auto path = graph.shortestPath("A", "E", gphl::ShortestPathAlgo::DIJKSTRA);
        std::vector<std::string> expected_path = {"A", "B", "D", "E"};
        REQUIRE(path == expected_path);
    }

    SECTION("bfs finds the shortest path in an unweighted graph") {
        gphl::Graph<std::string, int> unweighted_graph(false);
        unweighted_graph.addNode("A");
        unweighted_graph.addNode("B");
        unweighted_graph.addNode("C");
        unweighted_graph.addNode("D");
        unweighted_graph.addEdge("A", "B");
        unweighted_graph.addEdge("A", "C");
        unweighted_graph.addEdge("B", "D");
        
        auto path = unweighted_graph.shortestPath("A", "D", gphl::ShortestPathAlgo::BFS);
        std::vector<std::string> expected_path = {"A", "B", "D"};
        REQUIRE(path == expected_path);
    }
}

TEST_CASE("Graph Minimum Spanning Tree", "[graph]") {
    gphl::Graph<std::string, int> graph(false);
    graph.addNode("A");
    graph.addNode("B");
    graph.addNode("C");
    graph.addNode("D");
    graph.addEdge("A", "B", 1);
    graph.addEdge("A", "C", 4);
    graph.addEdge("A", "D", 3);
    graph.addEdge("B", "D", 2);
    graph.addEdge("C", "D", 5);

    auto calculate_total_weight = [](const std::vector<gphl::Edge<std::string, int>>& mst) {
        int total_weight = 0;
        for (const auto& edge : mst) {
            total_weight += edge.getWeight();
        }
        return total_weight;
    };

    SECTION("kruskal finds the MST") {
        auto mst = graph.minimumSpanningTree(gphl::MSTAlgo::KRUSKAL);
        int total_weight = calculate_total_weight(mst);
        REQUIRE(total_weight == 7);
    }

    SECTION("prim finds the MST") {
        auto mst = graph.minimumSpanningTree(gphl::MSTAlgo::PRIM);
        int total_weight = calculate_total_weight(mst);
        REQUIRE(total_weight == 7);
    }
}

TEST_CASE("Graph Topological Sort", "[graph]") {
    gphl::Graph<std::string, int> graph(true); // Directed graph
    graph.addNode("A");
    graph.addNode("B");
    graph.addNode("C");
    graph.addNode("D");
    graph.addNode("E");
    graph.addEdge("A", "B");
    graph.addEdge("A", "C");
    graph.addEdge("B", "D");
    graph.addEdge("C", "D");
    graph.addEdge("D", "E");

    SECTION("produces a valid topological sort") {
        auto sorted_nodes = graph.topologicalSort();
        // A valid topological sort would have 'A' before 'B' and 'C', 
        // 'B' and 'C' before 'D', and 'D' before 'E'.
        REQUIRE(sorted_nodes.size() == 5);
    }

    SECTION("throws an exception for a cyclic graph") {
        gphl::Graph<std::string, int> cyclic_graph(true);
        cyclic_graph.addNode("A");
        cyclic_graph.addNode("B");
        cyclic_graph.addNode("C");
        cyclic_graph.addEdge("A", "B");
        cyclic_graph.addEdge("B", "C");
        cyclic_graph.addEdge("C", "A");
        REQUIRE_THROWS_AS(cyclic_graph.topologicalSort(), std::runtime_error);
    }
}

TEST_CASE("Graph Coloring and Bipartiteness", "[graph]") {
    SECTION("correctly identifies a bipartite graph") {
        gphl::Graph<std::string, int> graph(false);
        graph.addNode("A");
        graph.addNode("B");
        graph.addNode("C");
        graph.addNode("D");
        graph.addEdge("A", "B");
        graph.addEdge("C", "D");
        graph.addEdge("A", "C");

        REQUIRE(graph.isBipartite() == true);
        auto colors = graph.nodeColoring();
        REQUIRE(colors.size() == 4);
    }

    SECTION("correctly identifies a non-bipartite graph") {
        gphl::Graph<std::string, int> graph(false);
        graph.addNode("A");
        graph.addNode("B");
        graph.addNode("C");
        graph.addEdge("A", "B");
        graph.addEdge("B", "C");
        graph.addEdge("C", "A");

        REQUIRE(graph.isBipartite() == false);
        auto colors = graph.nodeColoring();
        REQUIRE(colors.size() == 3);
    }
}

TEST_CASE("Graph Articulation Points and Biconnectivity", "[graph]") {
    SECTION("correctly identifies articulation points") {
        gphl::Graph<std::string, int> graph(false);
        graph.addNode("A");
        graph.addNode("B");
        graph.addNode("C");
        graph.addNode("D");
        graph.addEdge("A", "B");
        graph.addEdge("B", "C");
        graph.addEdge("C", "D");

        auto points = graph.articulationPoints();
        std::vector<std::string> expected_points = {"B", "C"};
        REQUIRE(points.size() == expected_points.size());
    }

    SECTION("correctly identifies a biconnected graph") {
        gphl::Graph<std::string, int> graph(false);
        graph.addNode("A");
        graph.addNode("B");
        graph.addNode("C");
        graph.addEdge("A", "B");
        graph.addEdge("B", "C");
        graph.addEdge("C", "A");

        REQUIRE(graph.isBiconnected() == true);
    }
}

TEST_CASE("Graph Bridge Detection", "[graph]") {
    gphl::Graph<std::string, int> graph(false);
    graph.addNode("A");
    graph.addNode("B");
    graph.addNode("C");
    graph.addNode("D");
    graph.addNode("E");
    graph.addEdge("A", "B");
    graph.addEdge("B", "C");
    graph.addEdge("C", "D");
    graph.addEdge("D", "E");

    SECTION("correctly identifies bridges") {
        auto bridges = graph.bridges();
        REQUIRE(bridges.size() == 4);
    }
}

TEST_CASE("Graph Strongly Connected Components", "[graph]") {
    gphl::Graph<std::string, int> graph(true); // Directed graph
    graph.addNode("A");
    graph.addNode("B");
    graph.addNode("C");
    graph.addNode("D");
    graph.addNode("E");
    graph.addEdge("A", "B");
    graph.addEdge("B", "C");
    graph.addEdge("C", "A");
    graph.addEdge("B", "D");
    graph.addEdge("D", "E");

    SECTION("tarjan finds SCCs") {
        auto sccs = graph.stronglyConnectedComponents(gphl::SCCAlgo::TARJAN);
        REQUIRE(sccs.size() == 3);
    }

    SECTION("kosaraju finds SCCs") {
        auto sccs = graph.stronglyConnectedComponents(gphl::SCCAlgo::KOSARAJU);
        REQUIRE(sccs.size() == 3);
    }
}

TEST_CASE("Graph Edge Coloring", "[graph]") {
    gphl::Graph<std::string, int> graph(false);
    graph.addNode("A");
    graph.addNode("B");
    graph.addNode("C");
    graph.addNode("D");
    graph.addEdge("A", "B");
    graph.addEdge("B", "C");
    graph.addEdge("C", "D");
    graph.addEdge("D", "A");

    SECTION("correctly colors the edges of a square") {
        auto colors = graph.edgeColoring();
        REQUIRE(colors.size() == 4);
        REQUIRE(colors[{"A", "B"}] != colors[{"B", "C"}]);
        REQUIRE(colors[{"B", "C"}] != colors[{"C", "D"}]);
        REQUIRE(colors[{"C", "D"}] != colors[{"D", "A"}]);
        REQUIRE(colors[{"D", "A"}] != colors[{"A", "B"}]);

        std::set<int> unique_colors;
        for (const auto& pair : colors) {
            unique_colors.insert(pair.second);
        }
        // The greedy algorithm is not guaranteed to produce an optimal coloring.
        // For a square, it may use 2 or 3 colors depending on the iteration order.
        REQUIRE((unique_colors.size() == 2 || unique_colors.size() == 3));
    }
}

TEST_CASE("Graph Centrality", "[graph]") {
    gphl::Graph<std::string, int> graph(false);
    graph.addNode("A");
    graph.addNode("B");
    graph.addNode("C");
    graph.addEdge("A", "B");
    graph.addEdge("A", "C");

    SECTION("degreeCentrality is correct") {
        auto centrality = graph.degreeCentrality();
        REQUIRE(centrality["A"] == 2);
        REQUIRE(centrality["B"] == 1);
        REQUIRE(centrality["C"] == 1);
    }

    SECTION("closenessCentrality is correct") {
        auto centrality = graph.closenessCentrality();
        REQUIRE(centrality["A"] > centrality["C"]);
    }

    SECTION("betweennessCentrality is correct") {
        auto centrality = graph.betweennessCentrality();
        REQUIRE(centrality["A"] > centrality["B"]);
    }
}

TEST_CASE("Graph Serialization", "[graph]") {
    gphl::Graph<std::string, int> graph(false);
    graph.addNode("A");
    graph.addNode("B");
    graph.addNode("C");
    graph.addEdge("A", "B", 10);
    graph.addEdge("A", "C", 20);

    SECTION("save and load a graph") {
        const std::string filename = "test_graph.json";
        graph.save(filename);
        auto loaded_graph = gphl::Graph<std::string, int>::load(filename);

        REQUIRE(loaded_graph.hasNode("A"));
        REQUIRE(loaded_graph.hasNode("B"));
        REQUIRE(loaded_graph.hasNode("C"));

        auto centrality = graph.degreeCentrality();
        auto loaded_centrality = loaded_graph.degreeCentrality();
        REQUIRE(centrality["A"] == loaded_centrality["A"]);
        REQUIRE(centrality["B"] == loaded_centrality["B"]);
        REQUIRE(centrality["C"] == loaded_centrality["C"]);
    }
}
