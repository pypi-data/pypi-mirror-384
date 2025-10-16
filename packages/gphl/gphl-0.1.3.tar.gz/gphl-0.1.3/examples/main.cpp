#include <iostream>
#include <vector>
#include <functional>
#include "../include/graph.hpp"

int main()
{
    gphl::Graph<char,int> grp(false, 'a', 'd', 'c', 'b', 'e', 'f', 'g');

    grp.addEdge('c','a',23);
    grp.addEdge('a','b',20);
    grp.addEdge('b','c',45);
    grp.addEdge('d','a',56);
    grp.addEdge('d','c',99);
    grp.addEdge('d','b');
    grp.addEdge('e','a',90);
    grp.addEdge('e','f',213);
    grp.addEdge('f','g',987);
    grp.addEdge('g','e',7);

    std::cout<<std::endl<<std::endl<<std::endl;


    if(grp.hasCycle() == 1)
        std::cout<<"has Cycle"<<std::endl;
    else
        std::cout<<"no Cycle"<<std::endl;

    std::cout<<std::endl<<std::endl;

    std::cout<<"Node colors:-"<<std::endl;
    auto node_colors = grp.nodeColoring();
    for(auto const& [key, val] : node_colors)
    {
        std::cout << key << ":" << val << std::endl;
    }
    std::cout<<std::endl<<std::endl;
    
    if(grp.isBipartite())
    {
        std::cout<<"it is bipartite"<<std::endl;
    }
    else
    {
        std::cout<<"not bipartite"<<std::endl;
    }

    std::cout<<std::endl;

    std::cout<<"Katz Centrality:-"<<std::endl;
    auto katz_centrality = grp.katzCentrality();
    for(auto const& [node, score] : katz_centrality)
    {
        std::cout << node << ": " << score << std::endl;
    }
    std::cout<<std::endl;

    std::cout<<"Prim's MST"<<std::endl;
    auto primMST = grp.minimumSpanningTree(gphl::MSTAlgo::PRIM);
    for(auto it:primMST)
    {
        if(it.getSource() == it.getDestination())
            continue;
        std::cout<<'('<<it.getSource()<<" "<<it.getDestination()<<')'<<"  , ";
    }
    std::cout<<std::endl<<std::endl;

    std::cout<<"Krushkal MST"<<std::endl;
    auto kruskalMST = grp.minimumSpanningTree(gphl::MSTAlgo::KRUSKAL);
    for(auto it:kruskalMST)
    {
        if(it.getSource() == it.getDestination())
            continue;
        std::cout<<'('<<it.getSource()<<" "<<it.getDestination()<<')'<<"  , ";
    }
    std::cout<<std::endl<<std::endl;
    
    std::cout<<"Iterative DFS"<<std::endl;
    auto iterativeDFS = grp.iterativeDFS('b');
    for(auto it:iterativeDFS)
    {
        std::cout<<it<<"-->";
    }
    std::cout<<std::endl<<std::endl;

    std::cout<<"Uniform Cost Search"<<std::endl;
    auto unifromCostSearch = grp.shortestPath('a','g', gphl::ShortestPathAlgo::UNIFORM_COST_SEARCH);
    for(auto it:unifromCostSearch)
    {
        std::cout<<it<<"-->";
    }
    std::cout<<std::endl<<std::endl;   

    std::cout<<"A* huristic search"<<std::endl;
    std::function<double(char,char)> huristic = [&](char node1 , char node2)
    {
        if(node1 > node2)
        {
            return 0.04335;
        }
        
        return 0.012;
    };

    auto A_start_search = grp.shortestPath('a','g',gphl::ShortestPathAlgo::A_STAR,huristic);
    for(auto it:A_start_search)
    {
        std::cout<<it<<"-->";
    }
    std::cout<<std::endl<<std::endl;

    return 0;
}

