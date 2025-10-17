cmake_minimum_required(VERSION 3.14)
project(GraphLibTests)

add_executable(test_graph test_graph.cpp)

target_link_libraries(test_graph PRIVATE GraphLibCore Catch2::Catch2WithMain)

include(CTest)
include(Catch)
catch_discover_tests(test_graph)
