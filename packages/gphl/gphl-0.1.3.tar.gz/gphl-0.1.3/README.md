# GraphLib

GraphLib is a modern C++ library for graph theory and network analysis. It provides a flexible and easy-to-use API for creating, manipulating, and analyzing graphs. The library is header-only, making it easy to integrate into any C++ project. It also includes Python bindings for easy use in Python applications.

## Features

*   **Generic Graph Representation:** Supports both directed and undirected graphs with weighted edges.
*   **Core Algorithms:**
    *   **Traversals:** Breadth-First Search (BFS), Depth-First Search (DFS), and Iterative DFS.
    *   **Shortest Path:** Dijkstra's, Bellman-Ford, A*, and BFS-based algorithms.
    *   **Minimum Spanning Tree:** Kruskal's, Prim's, and Boruvka's algorithms.
    *   **Cycle Detection:** For both directed and undirected graphs.
    *   **Topological Sort:** For Directed Acyclic Graphs (DAGs).
*   **Advanced Analysis:**
    *   **Centrality Measures:** Degree, Closeness, Betweenness, and Katz Centrality.
    *   **Graph Coloring:** Greedy node and edge coloring.
    *   **Connectivity:** Connected components, strongly connected components (Tarjan's and Kosaraju's algorithms), articulation points, and bridges.
    *   **Eulerian Paths and Circuits.**
*   **Graph Serialization (JSON):** Save graphs to and load graphs from JSON files.
*   **Python Bindings:** A significant portion of the C++ API is exposed to Python using pybind11.

## Installation

### Prerequisites

*   A C++17 compatible compiler (e.g., GCC, Clang, MSVC).
*   CMake 3.14 or later.
*   Python 3.8 or later (for the Python bindings).

### Building the Project

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/GraphLib.git
    cd GraphLib
    ```

2.  **Configure with CMake:**
    ```bash
    mkdir build
    cd build
    cmake ..
    ```

3.  **Build the project:**
    ```bash
    cmake --build .
    ```

This will build the C++ example, the Python bindings, and the C++ test suite.

## Usage

### C++ Example

The following example demonstrates how to create a graph, add nodes and edges, and run a shortest path algorithm.

```cpp
#include <iostream>
#include "include/graph.hpp"

int main() {
    gphl::Graph<std::string, int> graph(false);
    graph.addNode("A");
    graph.addNode("B");
    graph.addNode("C");
    graph.addEdge("A", "B", 7);
    graph.addEdge("A", "C", 9);
    graph.addEdge("B", "C", 10);

    auto path = graph.shortestPath("A", "C", "dijkstra");

    for (const auto& node : path) {
        std::cout << node << " ";
    }
    std::cout << std::endl;

    // Save the graph to a file
    graph.save("my_graph.json");

    // Load the graph from a file
    auto loaded_graph = gphl::Graph<std::string, int>::load("my_graph.json");
    
    return 0;
}
```

### Python Example

The Python bindings provide a similar API to the C++ library.

```python
import gphl

graph = gphl.Graph(False)
graph.addNode("A")
graph.addNode("B")
graph.addNode("C")
graph.addEdge("A", "B", 7)
graph.addEdge("A", "C", 9)
graph.addEdge("B", "C", 10)

path = graph.shortestPath("A", "C", "dijkstra", lambda x, y: 0)

print(path)

# Save the graph to a file
graph.save("my_graph.json")

# Load the graph from a file
loaded_graph = gphl.Graph.load("my_graph.json")
```

## Testing

The project includes both a C++ and a Python test suite to ensure the correctness of the library.

### Running the C++ Tests

To run the C++ tests, build the project as described in the **Installation** section, and then run `ctest` from the `build` directory.

```bash
cd build
ctest
```

### Running the Python Tests

To run the Python tests, build the project and then run the `run_tests.py` script.

```bash
python src/python/run_tests.py
```

## API Reference

The main classes and their functionalities are briefly described below.

*   `gphl::Graph<T, W>`: The main graph class.
    *   `addNode(const T& data)`: Adds a node to the graph.
    *   `addEdge(const T& src, const T& dest, const W& weight)`: Adds an edge to the graph.
    *   `shortestPath(...)`: Finds the shortest path between two nodes.
    *   `minimumSpanningTree(...)`: Finds the Minimum Spanning Tree of the graph.
    *   `degreeCentrality()`: Calculates the degree centrality of each node.
    *   `closenessCentrality()`: Calculates the closeness centrality of each node.
    *   `betweennessCentrality()`: Calculates the betweenness centrality of each node.
    *   `edgeColoring()`: Colors the edges of the graph.
    *   `save(const std::string& filename)`: Saves the graph to a JSON file.
    *   `load(const std::string& filename)`: Loads a graph from a JSON file.
    *   ... and many more.

*   `gphl::Edge<T, W>`: Represents an edge in the graph.

For more details, please refer to the source code and the examples.

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
