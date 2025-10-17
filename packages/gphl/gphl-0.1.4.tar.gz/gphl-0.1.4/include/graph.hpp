#pragma once

#include <vector>
#include <map>
#include <queue>
#include <stack>
#include <string>
#include <functional>
#include <stdexcept>
#include <set>
#include <unordered_set>
#include <unordered_map>
#include <limits>
#include <algorithm>
#include <utility>
#include <fstream>
#include <nlohmann/json.hpp>

#include "DSU.hpp"

namespace gphl {

const double INF = std::numeric_limits<double>::max();

enum class ShortestPathAlgo {
    BFS,
    DIJKSTRA,
    A_STAR,
    UNIFORM_COST_SEARCH,
    BELLMAN_FORD
};

enum class MSTAlgo {
    KRUSKAL,
    PRIM,
    BORUVKA
};

enum class SCCAlgo {
    TARJAN,
    KOSARAJU
};

enum class SSSPAlgo {
    DIJKSTRA,
    BELLMAN_FORD
};

enum class APSPAlgo {
    DIJKSTRA,
    FLOYD_WARSHALL,
    JHONSON
};


template<typename T, typename W>
class Edge
{
    private:
        T src;
        T dest;
        W  weight;
    public:
        Edge(T _src, T _dest, W _weight)
        {
            this->src = _src;
            this->dest = _dest;
            this->weight = _weight;
        }

        T getSource() const
        {
            return this->src;        
        }

        T getDestination() const
        {
            return this->dest;
        }

        W getWeight() const
        {
            return this->weight;
        }
};



template<typename T, typename W>
class Graph
{
    private:
        struct pair_hash {
            template <class T1, class T2>
            std::size_t operator () (const std::pair<T1,T2> &p) const {
                auto h1 = std::hash<T1>{}(p.first);
                auto h2 = std::hash<T2>{}(p.second);
                return h1 ^ h2;
            }
        };

        std::unordered_map<T,size_t> enc;
        std::unordered_map<size_t,T> dec;
        size_t idx;

        std::vector<std::vector<std::pair<size_t,double>>> adjList;
        std::vector<Edge<T,W>> edgeList;
        std::unordered_map<std::pair<T,T>,bool, pair_hash> isEdgeInEdgeList;

        size_t size;
        bool directed;

        std::vector<T> decode_path(const std::vector<size_t>& p) {
            std::vector<T> res;
            for(auto it : p) {
                res.push_back(dec[it]);
            }
            return res;
        }

    public:
        Graph(bool _directed)
        {
            this->directed = _directed;
            size = 0;
        }

        template<typename... Args>
        Graph(bool _directed, Args&&... args)
        {
            this->directed = _directed;
            size = 0;
            (addNode(std::forward<Args>(args)), ...);
        }
        // above codes are constructurs 

        void addNode(const T& data)
        {
            if(enc.find(data) == enc.end())
            {
                enc[data] = size;
                dec[size] = data;

                adjList.push_back(std::vector<std::pair<size_t,double>>());
                size++;
            }
            else
            {
                throw std::runtime_error("duplicate nodes are not allowed");
            }
        }

        bool hasNode(const T& data) const
        {
            return enc.find(data) != enc.end();
        }

        void addEdge(const T& src, const T& dest, const W& weight = W())
        {
            size_t encSrc = enc[src];
            size_t encDest = enc[dest];
            double castWeight = static_cast<double>(weight);
            if(this->directed == true)
            {
                adjList[encSrc].push_back(std::make_pair(encDest,castWeight));
                edgeList.push_back(Edge<T,W>(src,dest,weight));
            }
            else
            {
                adjList[encSrc].push_back(std::make_pair(encDest,castWeight));
                adjList[encDest].push_back(std::make_pair(encSrc,castWeight));
                if(!isEdgeInEdgeList[std::make_pair(src,dest)] && !isEdgeInEdgeList[std::make_pair(dest,src)])
               {     
                    isEdgeInEdgeList[std::make_pair(src,dest)] = true;
                    isEdgeInEdgeList[std::make_pair(dest,src)] = true;
                    edgeList.push_back(Edge<T,W>(src,dest,weight));
                }

            }
        }
        
        std::vector<T> bfs(T start)
        {
            size_t startEnc = enc[start];
            std::queue<size_t> que;
            std::vector<bool> vis(size, false);
            que.push(startEnc);
            vis[startEnc] = 1;
            std::vector<T> ans;
            vis[startEnc] = 1;
            while(!que.empty())
            {
                size_t curr = que.front();que.pop();
                ans.push_back(dec[curr]);
                for(auto it:adjList[curr])
                {
                    if(!vis[it.first])
                    {
                        vis[it.first] = 1;
                        que.push(it.first);
                    }
                }
            }
            return ans;
        }

        std::vector<T> dfs(T start)
        {
            std::vector<T> ans;
            size_t startEnc = enc[start];
            std::vector<bool> vis(size, false);

            std::function<void(size_t curr)> dfs = [&](size_t curr)
            {
                vis[curr] = 1;
                ans.push_back(dec[curr]);
                for(auto it:adjList[curr])
                {
                    if(!vis[it.first])
                    {
                        dfs(it.first);
                    }
                }
            };

            dfs(startEnc);
            return ans;

        }

        std::vector<T> iterativeDFS(T start)
        {
            size_t startEnc = enc[start];
            std::stack<size_t> que;
            std::vector<bool> vis(size, false);
            que.push(startEnc);
            vis[startEnc] = 1;
            std::vector<T> ans;
            vis[startEnc] = 1;
            while(!que.empty())
            {
                size_t curr = que.top();que.pop();
                ans.push_back(dec[curr]);
                for(auto it:adjList[curr])
                {
                    if(!vis[it.first])
                    {
                        vis[it.first] = 1;
                        que.push(it.first);
                    }
                }
            }
            return ans;            
        }
        
        bool hasCycle()
        {
            size_t numNodes = size;
            std::vector<bool> visited(numNodes, false);
            std::unordered_set<size_t> recursionStack;

            std::function<bool(size_t)> hasCycleDFS = [&](size_t node)
            {
                visited[node] = true;
                recursionStack.insert(node);

                for (const std::pair<size_t, double>& neighbor : adjList[node]) {
                    size_t neighborNode = neighbor.first;
                    
                    if (!visited[neighborNode]) {
                        if (hasCycleDFS(neighborNode)) {
                            return true;
                        }
                    } else if (recursionStack.count(neighborNode)) {
                        return true;
                    }
                }

                recursionStack.erase(node);
                return false;
            };

            for (size_t i = 0; i < numNodes; i++) {
                if (!visited[i] && hasCycleDFS(i)) {
                    return true;
                }
            }

            return false;
        }
        //----------------------------------------------------------------------------------------------------------------------------------------------------

        //below will be shortest path between src and dest finding algos

        std::vector<T> shortestPath(const T& start , const T& goal , ShortestPathAlgo method = ShortestPathAlgo::A_STAR , std::function<double(T, T)> heuristic = [](T a,T b){return 0;})
        {
            if(start == goal)
            {
                return std::vector<T>(1,start);
            }

            switch(method)
            {
                case ShortestPathAlgo::BFS:
                    return decode_path(shortestPathBfs(enc[start],enc[goal]));
                case ShortestPathAlgo::DIJKSTRA:
                    return decode_path(shortestPathDijkstra(enc[start],enc[goal]));
                case ShortestPathAlgo::UNIFORM_COST_SEARCH:
                    return decode_path(shortestPathUniformCostSearch(enc[start],enc[goal]));
                case ShortestPathAlgo::BELLMAN_FORD:
                    return decode_path(shortestPathBellmanFord(enc[start],enc[goal]));
                case ShortestPathAlgo::A_STAR:
                    return decode_path(shortestPathAStar(enc[start],enc[goal],heuristic));
                default:
                    throw std::runtime_error("wrong method name!!");
            }
            
            return {};
        }

        std::vector<size_t> shortestPathBfs(const size_t& start , const size_t& goal)
        {
            std::queue<std::pair<size_t, std::vector<size_t>>> q;
            q.push({start, {start}});
            std::vector<bool> vis(size, false);
            vis[start] = true;
            
            while (!q.empty()) {
                size_t current = q.front().first;
                std::vector<size_t> path = q.front().second;
                q.pop();
                
                if (current == goal) {
                    return path;
                }
                
                for (auto it : adjList[current]) {
                    size_t neighbor = it.first;
                    if (!vis[neighbor]) {
                        vis[neighbor] = true;
                        std::vector<size_t> newPath = path;
                        newPath.push_back(neighbor);
                        q.push({neighbor, newPath});
                    }
                }
            }
            
            return {};
        }

        std::vector<size_t> shortestPathDijkstra(const size_t& start, const size_t& goal)
        {
            size_t n = size;
            
            std::vector<double> distances(n, std::numeric_limits<double>::max());
            distances[start] = 0.0;
            
            std::priority_queue<std::pair<double, size_t>> pq; // Min-heap of pairs: (-distance, vertex)
            pq.push({0, start});
            
            std::vector<size_t> parent(n, -1);
            
            while (!pq.empty()) {

                size_t current;
                double distance;
            #pragma omp critical
                {
                    current = pq.top().second;
                    distance = -pq.top().first;
                    pq.pop();
                }
                
                if (distance > distances[current]) {
                    continue;
                }

            #pragma omp parallel for
                for (const auto& neighbor : adjList[current]) {
                    size_t next = neighbor.first;
                    double weight = neighbor.second;
                    double newDistance = distance + weight;
                #pragma omp critical
                    {    
                        if (newDistance < distances[next]) {
                            distances[next] = newDistance;
                            parent[next] = current;
                            pq.push({-newDistance, next});
                        }
                    }
                }
            }
            
            std::vector<size_t> path;
            size_t current = goal;
            
            while (current != -1) {
                path.insert(path.begin(), current);
                current = parent[current];
            }
            
            return path;            
        }

        std::vector<size_t> shortestPathUniformCostSearch(const size_t& start, const size_t& goal)
        {
            std::priority_queue<std::pair<double, size_t>, std::vector<std::pair<double, size_t>>, std::greater<std::pair<double, size_t>>> pq;
            std::vector<size_t> parent(size, -1);
            std::vector<double> cost(size, std::numeric_limits<double>::max());
            
            cost[start] = 0;
            pq.push(std::make_pair(0, start));

            while (!pq.empty()) {
                std::pair<double, size_t> current;
                size_t currentNode;
                double currentCost;
            #pragma omp critical
                {
                    current = pq.top();
                    pq.pop();
                    currentNode = current.second;
                    currentCost = current.first;
                }

                if (currentNode == goal) {
                    break;
                }

            #pragma omp parallel for
                for (const std::pair<size_t, double>& neighbor : adjList[currentNode]) {
                    double newCost = currentCost + neighbor.second;
                #pragma omp critical
                    {
                        if (newCost < cost[neighbor.first]) {
                            cost[neighbor.first] = newCost;
                            parent[neighbor.first] = currentNode;
                            pq.push(std::make_pair(newCost, neighbor.first));
                        }
                    }
                }
            }

            std::vector<size_t> path;
            size_t currentNode = goal;
            while (currentNode != -1) {
                path.push_back(currentNode);
                currentNode = parent[currentNode];
            }
            std::reverse(path.begin(),path.end());
            return path;
 
        }

        std::vector<size_t> shortestPathBellmanFord(const size_t& start, const size_t& goal)
        {
            size_t V = size;
            std::vector<double> distances(V, INF);
            distances[start] = 0;
            std::vector<size_t> predecessors(V, -1);

        #pragma omp parallel for 
            for (size_t i = 1; i < V; i++) {
                for (size_t u = 0; u < V; u++) {
                    for (const std::pair<size_t, double>& edge : adjList[u]) {
                        size_t v = edge.first;
                        double weight = edge.second;
                        if (distances[u] + weight < distances[v]) {
                            distances[v] = distances[u] + weight;
                            predecessors[v] = u;
                        }
                    }
                }
            }

            // Detect negative cycle
            for (size_t u = 0; u < V; u++) {
                for (const std::pair<size_t, double>& edge : adjList[u]) {
                    size_t v = edge.first;
                    double weight = edge.second;
                    if (distances[u] + weight < distances[v]) {
                        throw std::runtime_error("Negative cycle detected"); // Throw an exception
                    }
                }
            }

            std::vector<size_t> path;
            size_t current = goal;
            while (current != -1) {
                path.push_back(current);
                current = predecessors[current];
            }
            std::reverse(path.begin(), path.end());

            return path;            
        }

        std::vector<size_t> shortestPathAStar(const size_t& start, const size_t& goal, std::function<double(T,T)> heuristic)
        {
            size_t n = size;
            
            std::vector<double> distances(n, std::numeric_limits<double>::max());
            distances[start] = 0.0;
            
            std::priority_queue<std::pair<double, size_t>> pq; // Min-heap of pairs: (-distance, vertex)
            pq.push({0, start});
            
            std::vector<size_t> parent(n, -1);
            
            while (!pq.empty()) {

                size_t current;
                double distance;

            #pragma omp ciritcal
                {
                    current = pq.top().second;
                    distance = -pq.top().first;
                    pq.pop();
                }

                if (distance > distances[current]) {
                    continue;
                }
                
            #pragma omp parallel for
                for (const auto& neighbor : adjList[current]) {
                    size_t next = neighbor.first;
                    double weight = neighbor.second;
                    double newDistance = distance + weight;

                #pragma omp critical 
                    {
                        if (newDistance < distances[next]) {
                            distances[next] = newDistance;
                            parent[next] = current;
                            pq.push({-(newDistance + heuristic(dec[current],dec[next])), next});
                        }
                    }
                }
            }
            
            std::vector<size_t> path;
            size_t current = goal;
            
            while (current != -1) {
                path.insert(path.begin(), current);
                current = parent[current];
            }
            
            return path;              
        }

        //-------------------------------------------------------------------------------------------------------------------------------------------------------

        //below is the codes for single source shortest paths

        std::unordered_map<T,std::vector<T>> singleSourceShortestPaths(const T& source, SSSPAlgo method = SSSPAlgo::DIJKSTRA)
        {
            switch(method)
            {
                case SSSPAlgo::DIJKSTRA:
                {
                    std::unordered_map<T,std::vector<T>> res;
                    std::vector<std::vector<size_t>> paths = singleSourceShortestPathsDijkstra(enc[source]);
                    
                #pragma omp parallel for reduction(=:res)
                    for(size_t i=0;i<size;i++)
                    {
                        res[dec[i]] = decode_path(paths[i]);
                    }

                    return res;
                }
                case SSSPAlgo::BELLMAN_FORD:
                {
                    std::unordered_map<T,std::vector<T>> res;
                    std::vector<std::vector<size_t>> paths = singleSourceShortestPathsBellmanFord(enc[source]);
                    
                #pragma omp parallel for reduction(=:res)
                    for(size_t i=0;i<size;i++)
                    {
                        res[dec[i]] = decode_path(paths[i]);
                    }
                    return res;                
                }
                default:
                    throw std::runtime_error("wrong Method name!!");
            }
            return std::unordered_map<T,std::vector<T>>();
        } 

        std::vector<std::vector<size_t>> singleSourceShortestPathsDijkstra(const size_t& source)
        {
            size_t n = size; // Number of nodes in the graph
            std::vector<std::vector<size_t>> paths(n); // To store the paths
            
            std::vector<double> distance(n, INF);
            std::vector<size_t> parent(n, -1);
            std::vector<bool> visited(n, false);
            
            std::priority_queue<std::pair<double, size_t>, std::vector<std::pair<double, size_t>>, std::greater<std::pair<double, size_t>>> pq;
            pq.push(std::make_pair(0.0, source));
            distance[source] = 0.0;
            
            while (!pq.empty()) {
                size_t u = pq.top().second;
                pq.pop();
                
                if (visited[u]) continue;
                visited[u] = true;
                
                for (const auto& neighbor : adjList[u]) {
                    size_t v = neighbor.first;
                    double weight = neighbor.second;
                    
                    if (distance[u] + weight < distance[v]) {
                        distance[v] = distance[u] + weight;
                        parent[v] = u;
                        pq.push(std::make_pair(distance[v], v));
                    }
                }
            }
        #pragma omp parallel for reduction(=:paths)
            for (size_t i = 0; i < n; i++) {
                if (distance[i] == INF) {
                    paths[i] = std::vector<size_t>();
                    continue;
                }
                
                size_t current = i;
                while (current != -1) {
                    paths[i].insert(paths[i].begin(), current);
                    current = parent[current];
                }
            }
            
            return paths;            
        }

        std::vector<std::vector<size_t>> singleSourceShortestPathsBellmanFord(const size_t& source)
        {
            size_t n = adjList.size(); // Number of nodes in the graph
            std::vector<std::vector<size_t>> paths(n); // To store the paths
            
            std::vector<double> distance(n, INF);
            std::vector<size_t> parent(n, -1);
            distance[source] = 0.0;
            
        #pragma omp parallel for reduction(=:distance) reduction(=:parent)
            for (size_t i = 0; i < n - 1; i++) {
                for (size_t u = 0; u < n; u++) {
                    for (const auto& neighbor : adjList[u]) {
                        size_t v = neighbor.first;
                        double weight = neighbor.second;
                        
                        if (distance[u] + weight < distance[v]) 
                        {
                        #pragma omp cirtical
                            {
                                distance[v] = distance[u] + weight;
                                parent[v] = u;
                            }
                        }
                    }
                }
            }
            
            // Check for negative cycles
        #pragma omp parallel
        {
            bool local_negative_cycle = false;
            #pragma omp for
            for (size_t u = 0; u < n; u++) {
                for (const auto& neighbor : adjList[u]) {
                    size_t v = neighbor.first;
                    double weight = neighbor.second;
                    
                    if (distance[u] + weight < distance[v]) {
                        local_negative_cycle = true;
                    }
                }
            }

            #pragma omp critical
            {
                if (local_negative_cycle) {
                    throw std::runtime_error("Negative cycle detected.");
                }
            }
        }

        #pragma omp parallel for   
            for (size_t i = 0; i < n; i++) {
                if (distance[i] == INF) {
                    paths[i] = std::vector<size_t>();
                    continue;
                }
                
                size_t current = i;
                while (current != -1) {
                    paths[i].insert(paths[i].begin(), current);
                    current = parent[current];
                }
            }
            
            return paths;
        }
        // ------------------------------------------------------------------------------------------------------------------------------------------------------
        //below is the code for all pairs shortest paths

        std::unordered_map<T,std::unordered_map<T,std::vector<T>>> allPairsShortestPaths(APSPAlgo method = APSPAlgo::DIJKSTRA)
        {
            switch(method)
            {
                case APSPAlgo::DIJKSTRA:
                {
                    std::unordered_map<T,std::unordered_map<T,std::vector<T>>> res;
                    std::vector<std::vector<std::vector<size_t>>> ans = allPairsShortestPathsDijkstra();
                #pragma omp parallel for reduction(=:res)
                    for(size_t i=0;i<size;i++)
                    {                        
                        std::unordered_map<T,std::vector<T>> temp;
                    #pragma omp parallel for reduction(=:temp)
                        for(size_t j=0;j<size;j++)
                        {
                            temp[dec[j]] = decode_path(ans[i][j]);
                        }
                        res[dec[i]] = temp;
                    }
                    return res;                
                }
                case APSPAlgo::FLOYD_WARSHALL:
                {
                    std::unordered_map<T,std::unordered_map<T,std::vector<T>>> res;
                    std::vector<std::vector<std::vector<size_t>>> ans = allPairsShortestPathsFloydWarshall();
                #pragma omp parallel for reduction(=:res)
                    for(size_t i=0;i<size;i++)
                    {                        
                        std::unordered_map<T,std::vector<T>> temp;
                    #pragma omp parallel for reduction(=:temp)
                        for(size_t j=0;j<size;j++)
                        {
                            temp[dec[j]] = decode_path(ans[i][j]);
                        }
                        res[dec[i]] = temp;
                    }
                    return res;
                }
                case APSPAlgo::JHONSON:
                {
                    std::unordered_map<T,std::unordered_map<T,std::vector<T>>> res;
                    std::vector<std::vector<std::vector<size_t>>> ans = allPairsShortestPathsJhonson();
                #pragma omp parallel for reduction(=:res)
                    for(size_t i=0;i<size;i++)
                    {                        
                        std::unordered_map<T,std::vector<T>> temp;
                    #pragma omp parallel for reduction(=:temp)
                        for(size_t j=0;j<size;j++)
                        {
                            temp[dec[j]] = decode_path(ans[i][j]);
                        }
                        res[dec[i]] = temp;
                    }
                    return res;                
                }
                default:
                    throw std::runtime_error("wrong method!!!");
            }
            return std::unordered_map<T,std::unordered_map<T,std::vector<T>>>();
        }

        std::vector<std::vector<std::vector<size_t>>> allPairsShortestPathsDijkstra()
        {
            size_t n = size;
            std::vector<std::vector<std::vector<size_t>>> ans(n);

        #pragma omp parallel for reduction(=:ans)    
            for(size_t i=0;i<n;i++)
            {
                ans[i] = singleSourceShortestPathsDijkstra(i);
            }

            return ans;
        }

        std::vector<std::vector<std::vector<size_t>>> allPairsShortestPathsFloydWarshall()
        {
            size_t n = size;
            std::vector<std::vector<std::vector<size_t>>> paths(n, std::vector<std::vector<size_t>>(n));
            std::vector<std::vector<double>> dist(n, std::vector<double>(n, INF));

        #pragma omp parallel for reduction(=:dist) reduction(=:paths)
            for (size_t i = 0; i < n; i++) {
                dist[i][i] = 0;
                for (const auto& edge : adjList[i]) {
                    size_t v = edge.first;
                    double weight = edge.second;
                    dist[i][v] = weight;
                    paths[i][v] = {i, v};  // Initialize paths
                }
            }
            
            
            for (size_t k = 0; k < n; k++) {
                for (size_t i = 0; i < n; i++) {
                    for (size_t j = 0; j < n; j++) {
                        if (dist[i][k] + dist[k][j] < dist[i][j]) {
                            dist[i][j] = dist[i][k] + dist[k][j];
                            paths[i][j] = paths[i][k];  // Update path
                            paths[i][j].insert(paths[i][j].end(), paths[k][j].begin() + 1, paths[k][j].end());
                        }
                    }
                }
            }


            return paths;         
        }

        std::vector<std::vector<std::vector<size_t>>> allPairsShortestPathsJhonson()
        {
            size_t n = size;
            std::vector<double> h(n, 0); // Potential values for Bellman-Ford

            // Step 1: Bellman-Ford algorithm to re-weight edges
            std::vector<double> dist(n, INF);
            dist[0] = 0;
            for (size_t i = 0; i < n - 1; i++) {
                for (size_t u = 0; u < n; u++) {
                #pragma omp parallel for reduction(=:dist)
                    for (const auto& edge : adjList[u]) {
                        size_t v = edge.first;
                        double weight = edge.second + h[u] - h[v];
                        if (dist[u] + weight < dist[v]) {
                            dist[v] = dist[u] + weight;
                        }
                    }

                }
            }

            // Step 2: Create new graph with re-weighted edges
            std::vector<std::vector<std::pair<size_t, double>>> newGraph(n);
        #pragma omp parallel for reduction(=:newGraph)
            for (size_t u = 0; u < n; u++) {
                for (const auto& edge : adjList[u]) {
                    size_t v = edge.first;
                    double weight = edge.second + h[u] - h[v];
                    newGraph[u].emplace_back(v, weight);
                }
            }

            std::vector<std::vector<std::vector<size_t>>> allPaths(n, std::vector<std::vector<size_t>>(n));

            // Step 3: Run Dijkstra's algorithm for all pairs of vertices
            for (size_t u = 0; u < n; u++) {
                std::priority_queue<std::pair<double, size_t>, std::vector<std::pair<double, size_t>>, std::greater<std::pair<double, size_t>>> pq;
                std::vector<double> dist(n, INF);
                std::vector<size_t> prev(n, -1);

                dist[u] = 0;
                pq.emplace(0, u);

                while (!pq.empty()) {
                    size_t current = pq.top().second;
                    double currentDist = pq.top().first;
                    pq.pop();

                    if (currentDist > dist[current]) {
                        continue;
                    }

                    for (const std::pair<size_t, double>& edge : newGraph[current]) {
                        size_t v = edge.first;
                        double weight = edge.second;

                        if (currentDist + weight < dist[v]) {
                            dist[v] = currentDist + weight;
                            prev[v] = current;
                            pq.emplace(dist[v], v);
                        }
                    }
                }

                // Step 4: Construct paths from predecessors
            #pragma omp parallel for reduction(=:allPaths)
                for (size_t v = 0; v < n; v++) {
                    if (prev[v] != -1) {
                        size_t current = v;
                        while (current != -1) {
                            allPaths[u][v].insert(allPaths[u][v].begin(), current);
                            current = prev[current];
                        }
                    }
                }
            }

            return allPaths;           
        }


        //------------------------------------------------------------------------------------------------------------------------------------------------------
        // below is the code for all Minimum Spanning Tree generation

        std::vector<Edge<T,W>> minimumSpanningTree(MSTAlgo method = MSTAlgo::KRUSKAL)
        {
            switch(method)
            {
                case MSTAlgo::KRUSKAL:
                {
                    std::vector<Edge<T,W>> ans;
                    std::vector<std::pair<std::pair<size_t,size_t>,double>> temp = mstKruskal();
                    for(auto it:temp)
                    {
                        ans.push_back(Edge<T,W>(dec[it.first.first],dec[it.first.second],static_cast<W>(it.second)));
                    }
                    return ans;
                }
                case MSTAlgo::PRIM:
                {
                    std::vector<Edge<T,W>> ans;
                    std::vector<std::pair<std::pair<size_t,size_t>,double>> temp = mstPrim();
                    for(auto it:temp)
                    {
                        ans.push_back(Edge<T,W>(dec[it.first.first],dec[it.first.second],static_cast<W>(it.second)));
                    }
                    return ans;                
                }
                case MSTAlgo::BORUVKA:
                {
                    std::vector<Edge<T,W>> ans;
                    std::vector<std::pair<std::pair<size_t,size_t>,double>> temp = mstBoruvka();
                    for(auto it:temp)
                    {
                        ans.push_back(Edge<T,W>(dec[it.first.first],dec[it.first.second],static_cast<W>(it.second)));
                    }
                    return ans;                   
                }
                default:
                    throw std::runtime_error("wrong method!!!");
            }
            return std::vector<Edge<T,W>>();
        }

        std::vector<std::pair<std::pair<size_t,size_t>,double>> mstKruskal()
        {
            size_t n = size;
            std::vector<std::pair<std::pair<size_t, size_t>, double>> mstEdges;

            std::vector<std::pair<double, std::pair<size_t, size_t>>> edges;
            for (size_t u = 0; u < n; u++) {
                for (const auto &edge : adjList[u]) {
                    size_t v = edge.first;
                    double weight = edge.second;
                    edges.push_back({weight, {u, v}});
                }
            }

            std::sort(edges.begin(), edges.end());

            DSU dsu(n);
            for (const auto &edge : edges) {
                size_t u = edge.second.first;
                size_t v = edge.second.second;
                double weight = edge.first;

                if (dsu.leader(static_cast<int>(u)) != dsu.leader(static_cast<int>(v))) {
                    mstEdges.push_back({{u, v}, weight});
                    dsu.merge(static_cast<int>(u), static_cast<int>(v));
                }
            }

            return mstEdges;
        }

        std::vector<std::pair<std::pair<size_t,size_t>,double>> mstPrim()
        {
            size_t n = size;
            std::vector<std::pair<std::pair<size_t, size_t>, double>> mst; // The Minimum Spanning Tree
            std::vector<bool> visited(n, false); // Track visited nodes
            std::vector<double> key(n, std::numeric_limits<double>::max()); // Minimum weights to each node
            std::vector<size_t> parent(n, -1); // Parent of each node in MST

            // Custom comparator for priority queue
            auto compare = [](const std::pair<size_t, double>& a, const std::pair<size_t, double>& b) {
                return a.second > b.second;
            };
            std::priority_queue<std::pair<size_t, double>, std::vector<std::pair<size_t, double>>, decltype(compare)> pq(compare);

            // Start with the first node
            key[0] = 0.0;
            pq.push(std::make_pair(0, 0.0));

            while (!pq.empty()) {
                size_t u = pq.top().first;
                pq.pop();

                if (visited[u])
                    continue;

                visited[u] = true;

                // Add the edge to the MST
                if (parent[u] != -1) {
                    mst.push_back(std::make_pair(std::make_pair(parent[u], u), key[u]));
                }

                for (const std::pair<size_t, double>& neighbor : adjList[u]) {
                    size_t v = neighbor.first;
                    double weight = neighbor.second;

                    if (!visited[v] && weight < key[v]) {
                        parent[v] = u;
                        key[v] = weight;
                        pq.push(std::make_pair(v, key[v]));
                    }
                }
            }

            return mst;            
        }

        std::vector<std::pair<std::pair<size_t,size_t>,double>> mstBoruvka()
        {
            size_t n = size;
            std::vector<std::pair<std::pair<size_t, size_t>, double>> mstEdges;

            DSU dsu(n);

            while (mstEdges.size() < (n - 1)) {
                std::vector<std::pair<std::pair<size_t, size_t>, double>> cheapestEdge(n, {{-1, -1}, INF});

                for (size_t u = 0; u < n; u++) {
                    for (const auto& edge : adjList[u]) {
                        size_t v = edge.first;
                        double weight = edge.second;
                        int rootU = dsu.leader(static_cast<int>(u));
                        int rootV = dsu.leader(static_cast<int>(v));

                        if (rootU != rootV && weight < cheapestEdge[rootU].second) {
                            cheapestEdge[rootU] = {{u, v}, weight};
                        }
                    }
                }

                for (size_t u = 0; u < n; u++) {
                    if (cheapestEdge[u].first.first != -1) {
                        int rootU = dsu.leader(static_cast<int>(cheapestEdge[u].first.first));
                        int rootV = dsu.leader(static_cast<int>(cheapestEdge[u].first.second));

                        if (rootU != rootV) {
                            mstEdges.push_back(cheapestEdge[u]);
                            dsu.merge(rootU, rootV);
                        }
                    }
                }
            }

            return mstEdges;
        }       

        // ------------------------------------------------------------------------------------------------------------------------------------------------------
        // below is the code for toposort of a graph , it uses khan's algorithm , and the functions requried for toposort is also defined

        std::vector<T> topologicalSort()
        {
            if(directed == false)
            {
                throw std::runtime_error("Graph is not a Directed Acyclic Graph (DAG)");
            }
            else
            {
                auto topoHelper = [&]()
                {
                    size_t n = size;
                    std::vector<size_t> inDegree(n, 0);
                    
                    // Calculate in-degrees of all nodes
                    for (size_t u = 0; u < n; u++) {
                        for (const auto& edge : adjList[u]) {
                            size_t v = edge.first;
                            inDegree[v]++;
                        }
                    }
                    
                    std::queue<size_t> q;
                    for (size_t u = 0; u < n; u++) {
                        if (inDegree[u] == 0) {
                            q.push(u);
                        }
                    }
                    
                    std::vector<size_t> topoOrder;
                    
                    while (!q.empty()) {
                        size_t u = q.front();
                        q.pop();
                        topoOrder.push_back(u);
                        
                        for (const auto& edge : adjList[u]) {
                            size_t v = edge.first;
                            inDegree[v]--;
                            if (inDegree[v] == 0) {
                                q.push(v);
                            }
                        }
                    }
                    
                    // Check if graph is not a DAG (cycle exists)
                    if (topoOrder.size() != n) {
                        throw std::runtime_error("Graph is not a Directed Acyclic Graph (DAG)");
                    }
                    
                    return topoOrder;                    
                };

                std::vector<size_t> temp = topoHelper();
                std::vector<T> ans(size);
                for(size_t i=0;i<size;i++)
                {
                    ans[i] = dec[temp[i]];
                }
                return ans;
            }
            return std::vector<T>();
        }

        //------------------------------------------------------------------------------------------------------------------------------------------------------
        //below is the code for node coloring , is Bipartite, edge coloring and try coloring with n colors

            std::vector<int> nodeColoringHelper()
            {
                size_t numNodes = size;
                std::vector<int> colors(numNodes, -1); // Initialize all nodes with no color assigned

                std::unordered_map<int, std::set<size_t>> colorToNodes;

                // Iterate through each node and assign colors
                for (size_t node = 0; node < numNodes; node++) {
                    std::set<int> usedColors;

                    // Check colors of adjacent nodes and mark them as used
                    for (auto& neighbor : adjList[node]) {
                        size_t neighborNode = neighbor.first;
                        if (colors[neighborNode] != -1) {
                            usedColors.insert(colors[neighborNode]);
                        }
                    }

                    // Find the smallest available color
                    for (int color = 0; color < numNodes; color++) {
                        if (usedColors.find(color) == usedColors.end()) {
                            colors[node] = color;
                            colorToNodes[color].insert(node);
                            break;
                        }
                    }
                }
                return colors;                
            };

        std::unordered_map<T,int> nodeColoring()
        {
            std::unordered_map<T,int> ans;
            std::vector<int> temp = nodeColoringHelper();
            for(size_t i=0;i<size;i++)
            {
                ans[dec[i]] = temp[i];
            }
            return ans;
        }

        std::unordered_map<std::pair<T, T>, int, pair_hash> edgeColoring()
        {
            std::unordered_map<std::pair<T, T>, int, pair_hash> colored_edges;
            std::unordered_map<std::pair<size_t, size_t>, int, pair_hash> encoded_colored_edges;

            for (size_t u = 0; u < size; ++u) {
                for (const auto& edge : adjList[u]) {
                    size_t v = edge.first;

                    // For undirected graphs, only color an edge once
                    if (!directed && u > v) {
                        continue;
                    }

                    std::set<int> used_colors;

                    // Check colors of edges incident to u
                    for (const auto& incident_edge : adjList[u]) {
                        size_t neighbor = incident_edge.first;
                        if (encoded_colored_edges.count({u, neighbor})) {
                            used_colors.insert(encoded_colored_edges[{u, neighbor}]);
                        } else if (encoded_colored_edges.count({neighbor, u})) {
                            used_colors.insert(encoded_colored_edges[{neighbor, u}]);
                        }
                    }

                    // Check colors of edges incident to v
                    for (const auto& incident_edge : adjList[v]) {
                        size_t neighbor = incident_edge.first;
                        if (encoded_colored_edges.count({v, neighbor})) {
                            used_colors.insert(encoded_colored_edges[{v, neighbor}]);
                        } else if (encoded_colored_edges.count({neighbor, v})) {
                            used_colors.insert(encoded_colored_edges[{neighbor, v}]);
                        }
                    }

                    int color = 1;
                    while (used_colors.count(color)) {
                        color++;
                    }
                    
                    encoded_colored_edges[{u, v}] = color;
                }
            }

            for(auto const& [edge, color] : encoded_colored_edges) {
                colored_edges[{dec[edge.first], dec[edge.second]}] = color;
            }

            return colored_edges;
        }

        /**
         * @brief Calculates the Katz centrality of each node in the graph.
         * 
         * Katz centrality is a measure of the influence of a node in a network. It is
         * calculated by summing the influence of its neighbors, attenuated by a factor alpha.
         * 
         * @param alpha The attenuation factor, typically a small constant.
         * @param beta The constant bias, typically 1.
         * @param max_iterations The maximum number of iterations to perform.
         * @param tolerance The tolerance for convergence.
         * @return A map from each node to its Katz centrality score.
         */
        std::unordered_map<T, double> katzCentrality(double alpha = 0.1, double beta = 1.0, int max_iterations = 1000, double tolerance = 1e-6) const
        {
            size_t n = size;
            std::unordered_map<T, double> centrality;
            std::vector<double> x(n, 1.0 / n);
            std::vector<double> x_prev(n);

            for (int iter = 0; iter < max_iterations; ++iter) {
                x_prev = x;
                double sum_sq = 0.0;

                for (size_t i = 0; i < n; ++i) {
                    double sum = 0.0;
                    for (const auto& neighbor : adjList[i]) {
                        sum += x_prev[neighbor.first];
                    }
                    x[i] = alpha * sum + beta;
                    sum_sq += x[i] * x[i];
                }

                double norm = std::sqrt(sum_sq);
                for (size_t i = 0; i < n; ++i) {
                    x[i] /= norm;
                }

                double diff = 0.0;
                for (size_t i = 0; i < n; ++i) {
                    diff += std::abs(x[i] - x_prev[i]);
                }

                if (diff < tolerance) {
                    break;
                }
            }

            for (size_t i = 0; i < n; ++i) {
                centrality[dec.at(i)] = x[i];
            }

            return centrality;
        }

        std::unordered_map<T, double> degreeCentrality() const
        {
            std::unordered_map<T, double> centrality;
            for (size_t i = 0; i < size; ++i) {
                centrality[dec.at(i)] = static_cast<double>(adjList[i].size());
            }
            return centrality;
        }

        std::unordered_map<T, double> closenessCentrality()
        {
            std::unordered_map<T, double> centrality;
            for (size_t i = 0; i < size; ++i) {
                double sum_of_distances = 0.0;
                for (size_t j = 0; j < size; ++j) {
                    if (i == j) continue;
                    auto path = shortestPath(dec.at(i), dec.at(j), ShortestPathAlgo::BFS);
                    if (!path.empty()) {
                        sum_of_distances += static_cast<double>(path.size() - 1);
                    }
                }
                if (sum_of_distances > 0) {
                    centrality[dec.at(i)] = 1.0 / sum_of_distances;
                } else {
                    centrality[dec.at(i)] = 0.0;
                }
            }
            return centrality;
        }

        std::unordered_map<T, double> betweennessCentrality()
        {
            std::unordered_map<T, double> centrality;
            for (size_t i = 0; i < size; ++i) {
                centrality[dec.at(i)] = 0.0;
            }

            for (size_t s = 0; s < size; ++s) {
                std::stack<size_t> S;
                std::vector<std::vector<size_t>> P(size);
                std::vector<double> sigma(size, 0.0);
                std::vector<int> d(size, -1);

                sigma[s] = 1.0;
                d[s] = 0;

                std::queue<size_t> Q;
                Q.push(s);

                while (!Q.empty()) {
                    size_t v = Q.front();
                    Q.pop();
                    S.push(v);

                    for (const auto& edge : adjList[v]) {
                        size_t w = edge.first;
                        if (d[w] < 0) {
                            Q.push(w);
                            d[w] = d[v] + 1;
                        }
                        if (d[w] == d[v] + 1) {
                            sigma[w] += sigma[v];
                            P[w].push_back(v);
                        }
                    }
                }

                std::vector<double> delta(size, 0.0);
                while (!S.empty()) {
                    size_t w = S.top();
                    S.pop();

                    for (size_t v : P[w]) {
                        delta[v] += (sigma[v] / sigma[w]) * (1.0 + delta[w]);
                    }
                    if (w != s) {
                        centrality[dec.at(w)] += delta[w];
                    }
                }
            }
            return centrality;
        }

        bool isBipartite()
        {
            std::vector<int> temp = nodeColoringHelper();
            std::set<int> st;
            for(auto it:temp)
            {
                st.insert(it);
            }
            if(st.size() <= 2)
                return true;
            return false;
        }

        //------------------------------------------------------------------------------------------------------------------------------------------------------
        // below is the code to find articulation points of a graph (cut vertices) and is_biconnected graph

        std::vector<T> articulationPoints()
        {
            // dfs algo to find articulation points
            if(directed == true)
            {
                throw std::runtime_error("not implemented for directed");
            }
            //int n = size;
            std::vector<int> vis(size,0);

            auto articulationPointsHelper = [&]()
            {
                size_t numNodes = size;
                std::vector<size_t> disc(numNodes, -1);
                std::vector<size_t> low(numNodes, -1);
                std::vector<bool> visited(numNodes, false);
                std::unordered_set<size_t> articulationPoints;
                size_t time = 0;

                std::function<void(size_t,size_t)> dfsArticulationPoints = [&](size_t node, size_t parent)
                {
                    visited[node] = true;
                    disc[node] = low[node] = ++time;
                    size_t children = 0;

                    for (const std::pair<size_t, double>& edge : adjList[node]) {
                        size_t neighbor = edge.first;
                        if (!visited[neighbor]) {
                            children++;
                            dfsArticulationPoints(neighbor, node);
                            low[node] = std::min(low[node], low[neighbor]);

                            if (low[neighbor] >= disc[node] && parent != -1) {
                                articulationPoints.insert(node);
                            }
                        } else if (neighbor != parent) {
                            low[node] = std::min(low[node], disc[neighbor]);
                        }
                    }

                    if (parent == -1 && children > 1) {
                        articulationPoints.insert(node);
                    }
                };

                for (size_t i = 0; i < numNodes; ++i) {
                    if (!visited[i]) {
                        dfsArticulationPoints(i, -1);
                    }
                }

                return std::vector<size_t>(articulationPoints.begin(), articulationPoints.end());
            };
            

            std::vector<T> ans;
            std::vector<size_t> temp = articulationPointsHelper();
            
            for(auto it:temp)
            {
                if(vis[it] == 0)
                {
                    vis[it] = 1;
                    ans.push_back(dec[it]);
                }
            }
            
            return ans;
        }

        bool isBiconnected()
        {
            auto temp = articulationPoints();
            if(temp.size() > 0)
                return false;
            return true;
        }

        //-------------------------------------------------------------------------------------------------------------------------------------------------------
        // below is the code to find the bridges in the graph

        std::vector<Edge<T,W>> bridges()
        {
            size_t n = adjList.size(); // Number of vertices in the graph
            std::vector<bool> visited(n, false); // To keep track of visited vertices
            std::vector<size_t> disc(n, 0); // Discovery time of vertices
            std::vector<size_t> low(n, 0); // Lowest discovery time reachable from the vertex
            std::vector<std::pair<size_t, size_t>> bridges; // Store the bridge edges

            size_t time = 0; // Initialize time

            // DFS function to find bridges
            std::function<void(size_t, size_t)> dfs = [&](size_t u, size_t parent) {
                visited[u] = true;
                disc[u] = low[u] = ++time;

                for (auto& neighbor : adjList[u]) {
                    size_t v = neighbor.first;
                    if (v == parent)
                        continue;

                    if (!visited[v]) {
                        dfs(v, u);
                        low[u] = std::min(low[u], low[v]);
                        
                        if (low[v] > disc[u]) {
                            bridges.push_back({u, v});
                        }
                    } else {
                        low[u] = std::min(low[u], disc[v]);
                    }
                }
            };

            // Call DFS for each unvisited vertex
            for (size_t i = 0; i < n; i++) {
                if (!visited[i]) {
                    dfs(i, -1);
                }
            }

            // Construct the result vector with std::pair<std::pair<size_t, size_t>, double>
            std::vector<Edge<T,W>> result;
            for (auto bridge : bridges) {
                size_t u = bridge.first;
                size_t v = bridge.second;
                for (auto& neighbor : adjList[u]) {
                    if (neighbor.first == v) {
                        result.push_back(Edge<T,W>(dec[u],dec[v],neighbor.second));
                        //result.push_back({{u, v}, neighbor.second});
                        break;
                    }
                }
            }

            return result;            
        }

        //------------------------------------------------------------------------------------------------------------------------------------------------------
        // below is the code for eulerian paths and circuits
        
        std::vector<std::vector<Edge<T,W>>> eulerianPathFromSource(T source)
        {
            std::vector<std::vector<Edge<T,W>>> ans;
            size_t srcEnc = enc[source];
            //cout<<"hi"<<endl;
            std::set<std::vector<std::pair<size_t,size_t>>> result;
            std::unordered_map<std::pair<size_t,size_t>,bool, pair_hash> visEdge;
            std::vector<std::pair<size_t,size_t>> curPath;
            std::vector<Edge<T,W>> temp_edge_list(edgeList.begin(),edgeList.end());
            size_t numEdges = temp_edge_list.size();
            if(!directed)
                numEdges/=2;
            //cout<<numEdges<<endl;
            std::function<void(size_t)> dfs = [&](size_t cur)
            {
                //cout<<dec[cur]<<endl;
                //cout<<curPath.size()<<endl;
                if(curPath.size() == numEdges)
                {
                    result.insert(curPath);
                }

                for(auto it:adjList[cur])
                {
                    size_t neighbor = it.first;
                    if(!visEdge[std::make_pair(cur,neighbor)])
                    {
                        visEdge[std::make_pair(cur,neighbor)] = true;
                        visEdge[std::make_pair(neighbor,cur)] = true;
                        curPath.push_back(std::make_pair(cur,neighbor));
                        dfs(neighbor);
                        curPath.pop_back();
                        visEdge[std::make_pair(cur,neighbor)] = false;
                        visEdge[std::make_pair(neighbor,cur)] = false;
                    }
                }

            };

            dfs(srcEnc);

            //cout<<result.size()<<endl;
            //std::vector<std::vector<std::pair<size_t,size_t>>> temp(result.begin(),result.end());
            for(auto it:result)
            {
                std::vector<Edge<T,W>> temp;
                for (auto ed : it) {
                    size_t u = ed.first;
                    size_t v = ed.second;
                    for (auto& neighbor : adjList[u]) {
                        if (neighbor.first == v) {
                            temp.push_back(Edge<T,W>(dec[u],dec[v],neighbor.second));
                            break;
                        }
                    }
                }
                ans.push_back(temp);
            }

            return ans;
        }

        std::unordered_map<T,std::vector<std::vector<Edge<T,W>>>> allSourceEulerianPaths()
        {
            std::unordered_map<T,std::vector<std::vector<Edge<T,W>>>> ans;
            for(auto it:enc)
            {
                ans[it.first] = eulerianPathFromSource(it.first);
            }
            return ans;
        }

        std::vector<std::vector<Edge<T,W>>> eulerianCircuitsFromSource(T source)
        {
            std::vector<std::vector<Edge<T,W>>> ans;
            size_t srcEnc = enc[source];
            //cout<<"hi"<<endl;
            std::set<std::vector<std::pair<size_t,size_t>>> result;
            std::unordered_map<std::pair<size_t,size_t>,bool, pair_hash> visEdge;
            std::vector<std::pair<size_t,size_t>> curPath;
            size_t numEdges = edgeList.size();
            if(!directed)
                numEdges/=2;
            //cout<<numEdges<<endl;
            std::function<void(size_t)> dfs = [&](size_t cur)
            {
                //cout<<dec[cur]<<"    ";
                //cout<<curPath.size()<<endl;
                //cout<<curPath.size()<<endl;
                if(curPath.size() == numEdges)
                {
                    if(curPath[numEdges-1].second == srcEnc)
                        result.insert(curPath);
                }

                for(auto it:adjList[cur])
                {
                    size_t neighbor = it.first;
                    if(!visEdge[std::make_pair(cur,neighbor)])
                    {
                        visEdge[std::make_pair(cur,neighbor)] = true;
                        visEdge[std::make_pair(neighbor,cur)] = true;
                        curPath.push_back(std::make_pair(cur,neighbor));
                        dfs(neighbor);
                        curPath.pop_back();
                        visEdge[std::make_pair(cur,neighbor)] = false;
                        visEdge[std::make_pair(neighbor,cur)] = false;
                    }
                }

            };

            dfs(srcEnc);

            //cout<<result.size()<<endl;
            //std::vector<std::vector<std::pair<size_t,size_t>>> temp(result.begin(),result.end());
            for(auto it:result)
            {
                std::vector<Edge<T,W>> temp;
                for (auto ed : it) {
                    size_t u = ed.first;
                    size_t v = ed.second;
                    for (auto& neighbor : adjList[u]) {
                        if (neighbor.first == v) {
                            temp.push_back(Edge<T,W>(dec[u],dec[v],neighbor.second));
                            break;
                        }
                    }
                }
                ans.push_back(temp);
            }

            return ans;            
        }

        std::unordered_map<T,std::vector<std::vector<Edge<T,W>>>> allSourceEulerianCircuits()
        {
            std::unordered_map<T,std::vector<std::vector<Edge<T,W>>>> ans;
            for(auto it:enc)
            {
                ans[it.first] = eulerianCircuitsFromSource(it.first);
            }
            return ans;
        }

        bool isEulerian()
        {
            auto ans = allSourceEulerianPaths();
            for(auto it:ans)
            {
                if(it.size()>0) 
                    return true;
            }
            return false;
        }

        //-------------------------------------------------------------------------------------------------------------------------------------------------------
        // below is the code to find number of components

        std::vector<std::vector<T>> connectedComponents()
        {
            std::vector<std::vector<T>> components;
            std::vector<bool> visited(size, false);

            for (size_t i = 0; i < size; ++i) {
                if (!visited[i]) {
                    std::vector<T> component;
                    std::queue<size_t> q;

                    q.push(i);
                    visited[i] = true;

                    while (!q.empty()) {
                        size_t u = q.front();
                        q.pop();
                        component.push_back(dec.at(u));

                        for (const auto& edge : adjList[u]) {
                            size_t v = edge.first;
                            if (!visited[v]) {
                                visited[v] = true;
                                q.push(v);
                            }
                        }
                    }
                    components.push_back(component);
                }
            }
            return components;
        }     

        //------------------------------------------------------------------------------------------------------------------------------------------------------
        // code to find strongly connected components (SCC) 

        std::vector<std::vector<T>> stronglyConnectedComponents(SCCAlgo method = SCCAlgo::TARJAN)
        {
            if(!directed)
            {
                throw std::runtime_error("implemented only for directed graph");
            }

            switch(method)
            {
                case SCCAlgo::TARJAN:
                {
                    std::vector<std::vector<size_t>> ans = tarjanSCC();
                    std::vector<std::vector<T>> res;
                    for(auto it:ans)
                    {
                        std::vector<T> temp;
                        for(auto xd:it)
                        {
                            temp.push_back(dec[xd]);
                        }
                        res.push_back(temp);
                    }
                    return res;
                }
                case SCCAlgo::KOSARAJU:
                {
                    std::vector<std::vector<size_t>> ans = kosarajuSCC();
                    std::vector<std::vector<T>> res;
                    for(auto it:ans)
                    {
                        std::vector<T> temp;
                        for(auto xd:it)
                        {
                            temp.push_back(dec[xd]);
                        }
                        res.push_back(temp);
                    }
                    return res;                
                }
                default:
                    throw std::runtime_error("wrong method!!!");
            }

            return std::vector<std::vector<T>>();
        }

        std::vector<std::vector<size_t>> tarjanSCC()
        {
            size_t n = size;
            
            std::vector<size_t> disc(n, -1);
            std::vector<size_t> low(n, -1);
            std::vector<bool> inStack(n, false);
            std::stack<size_t> nodeStack;
            std::vector<std::vector<size_t>> sccs;
            size_t time = 0;

            std::function<void(size_t)> dfs = [&](size_t node)
            {
                disc[node] = low[node] = ++time;
                nodeStack.push(node);
                inStack[node] = true;
                
                for (auto neigh : adjList[node]) 
                {
                    auto neighbor = neigh.first;
                    if (disc[neighbor] == -1) {
                        dfs(neighbor);
                        low[node] = std::min(low[node], low[neighbor]);
                    } else if (inStack[neighbor]) {
                        low[node] = std::min(low[node], disc[neighbor]);
                    }
                }
                
                if (disc[node] == low[node]) 
                {
                    std::vector<size_t> scc;
                    while (true) {
                        size_t curr = nodeStack.top();
                        nodeStack.pop();
                        inStack[curr] = false;
                        scc.push_back(curr);
                        if (curr == node) {
                            break;
                        }
                    }
                    sccs.push_back(scc);
                }
            };

            for (size_t i = 0; i < n; ++i) {
                if (disc[i] == -1) {
                    dfs(i);
                }
            }
            
            return sccs;            
        }

        std::vector<std::vector<size_t>> kosarajuSCC()
        {
            size_t n = size;
            
            std::vector<bool> visited(n, false);
            std::stack<size_t> order;
            
            std::function<void(size_t)> dfs = [&](size_t node) 
            {
                visited[node] = true;
                for (auto neigh : adjList[node]) 
                {
                    auto neighbor = neigh.first;
                    if (!visited[neighbor]) 
                    {
                        dfs(neighbor);
                    }
                }
                order.push(node);
            };

            // Step 1: Perform DFS on the original graph to get the finishing times
            for (size_t i = 0; i < n; i++) 
            {
                if (!visited[i]) {
                    dfs(i);
                }
            };
            
            // Step 2: Reverse the graph
            std::vector<std::vector<size_t>> reversedAdjList(n);

            auto reverseGraph = [&]()
            {
                for (size_t i = 0; i < size; i++) 
                {
                    for (auto neigh : adjList[i]) 
                    {
                        auto neighbor = neigh.first;
                        reversedAdjList[neighbor].push_back(i);
                    }
                }
            };

            reverseGraph();
            
            // Step 3: Perform DFS on the reversed graph to find SCCs
            std::vector<std::vector<size_t>> stronglyConnectedComponents;
            visited.assign(n, false);        

            while (!order.empty()) 
            {
                size_t node = order.top();
                order.pop();
                
                if (!visited[node]) 
                {
                    std::vector<size_t> component;

                    std::function<void(size_t)> dfsSCC = [&](size_t node)
                    {
                        visited[node] = true;
                        component.push_back(node);
                        for (size_t neighbor : reversedAdjList[node]) 
                        {
                            if (!visited[neighbor]) 
                            {
                                dfsSCC(neighbor);
                            }
                        }
                    };     

                    dfsSCC(node);
                    stronglyConnectedComponents.push_back(component);
                }
            }
            
            return stronglyConnectedComponents;            
        }

        void save(const std::string& filename) const {
            nlohmann::json j;
            j["directed"] = directed;
            j["nodes"] = nlohmann::json::array();
            for (size_t i = 0; i < size; ++i) {
                j["nodes"].push_back(dec.at(i));
            }

            j["edges"] = nlohmann::json::array();
            for (const auto& edge : edgeList) {
                nlohmann::json j_edge;
                j_edge["src"] = edge.getSource();
                j_edge["dest"] = edge.getDestination();
                j_edge["weight"] = edge.getWeight();
                j["edges"].push_back(j_edge);
            }

            std::ofstream o(filename);
            o << std::setw(4) << j << std::endl;
        }

        static Graph<T, W> load(const std::string& filename) {
            std::ifstream i(filename);
            nlohmann::json j;
            i >> j;

            Graph<T, W> graph(j["directed"]);

            for (const auto& node : j["nodes"]) {
                graph.addNode(node.get<T>());
            }

            for (const auto& edge : j["edges"]) {
                graph.addEdge(edge["src"].get<T>(), edge["dest"].get<T>(), edge["weight"].get<W>());
            }

            return graph;
        }
};

} // namespace gphl