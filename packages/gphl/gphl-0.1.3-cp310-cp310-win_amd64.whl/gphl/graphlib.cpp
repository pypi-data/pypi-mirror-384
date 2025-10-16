#include "graph.hpp"
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/functional.h>

namespace py = pybind11;

PYBIND11_MODULE(gphl, m) {
    py::class_<gphl::Edge<std::string, int>>(m, "Edge")
        .def(py::init<const std::string&, const std::string&, const int&>())
        .def("getSource", &gphl::Edge<std::string, int>::getSource)
        .def("getDestination", &gphl::Edge<std::string, int>::getDestination)
        .def("getWeight", &gphl::Edge<std::string, int>::getWeight);

    py::enum_<gphl::ShortestPathAlgo>(m, "ShortestPathAlgo")
        .value("BFS", gphl::ShortestPathAlgo::BFS)
        .value("DIJKSTRA", gphl::ShortestPathAlgo::DIJKSTRA)
        .value("A_STAR", gphl::ShortestPathAlgo::A_STAR)
        .value("UNIFORM_COST_SEARCH", gphl::ShortestPathAlgo::UNIFORM_COST_SEARCH)
        .value("BELLMAN_FORD", gphl::ShortestPathAlgo::BELLMAN_FORD)
        .export_values();

    py::enum_<gphl::MSTAlgo>(m, "MSTAlgo")
        .value("KRUSKAL", gphl::MSTAlgo::KRUSKAL)
        .value("PRIM", gphl::MSTAlgo::PRIM)
        .value("BORUVKA", gphl::MSTAlgo::BORUVKA)
        .export_values();

    py::enum_<gphl::SCCAlgo>(m, "SCCAlgo")
        .value("TARJAN", gphl::SCCAlgo::TARJAN)
        .value("KOSARAJU", gphl::SCCAlgo::KOSARAJU)
        .export_values();

    py::class_<gphl::Graph<std::string, int>>(m, "Graph")
        .def(py::init<bool>())
        .def("addNode", &gphl::Graph<std::string, int>::addNode)
        .def("hasNode", &gphl::Graph<std::string, int>::hasNode)
        .def("addEdge", &gphl::Graph<std::string, int>::addEdge, py::arg("src"), py::arg("dest"), py::arg("weight") = 0)
        .def("hasCycle", &gphl::Graph<std::string, int>::hasCycle)
        .def("nodeColoring", &gphl::Graph<std::string, int>::nodeColoring)
        .def("edgeColoring", &gphl::Graph<std::string, int>::edgeColoring)
        .def("isBipartite", &gphl::Graph<std::string, int>::isBipartite)
        .def("connectedComponents", &gphl::Graph<std::string, int>::connectedComponents)
        .def("katzCentrality", &gphl::Graph<std::string, int>::katzCentrality, py::arg("alpha") = 0.1, py::arg("beta") = 1.0, py::arg("max_iterations") = 1000, py::arg("tolerance") = 1e-6)
        .def("degreeCentrality", &gphl::Graph<std::string, int>::degreeCentrality)
        .def("closenessCentrality", &gphl::Graph<std::string, int>::closenessCentrality)
        .def("betweennessCentrality", &gphl::Graph<std::string, int>::betweennessCentrality)
        .def("minimumSpanningTree", &gphl::Graph<std::string, int>::minimumSpanningTree, py::arg("method") = gphl::MSTAlgo::KRUSKAL)
        .def("iterativeDFS", &gphl::Graph<std::string, int>::iterativeDFS)
        .def("shortestPath", &gphl::Graph<std::string, int>::shortestPath, py::arg("start"), py::arg("goal"), py::arg("method") = gphl::ShortestPathAlgo::A_STAR, py::arg("heuristic"))
        .def("stronglyConnectedComponents", &gphl::Graph<std::string, int>::stronglyConnectedComponents, py::arg("method") = gphl::SCCAlgo::TARJAN)
        .def("save", &gphl::Graph<std::string, int>::save)
        .def_static("load", &gphl::Graph<std::string, int>::load);
}