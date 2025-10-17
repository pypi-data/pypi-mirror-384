cmake_minimum_required(VERSION 3.14)
project(GraphLib)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# --- Core C++ Library (Header-Only) ---
add_library(GraphLibCore INTERFACE)
target_include_directories(GraphLibCore INTERFACE include)

# --- pybind11 ---
add_subdirectory(pybind11)
pybind11_add_module(gphl src/gphl/graphlib.cpp)
target_link_libraries(gphl PRIVATE GraphLibCore)

install(TARGETS gphl DESTINATION .)

# --- Examples ---
option(GRAPHLIB_BUILD_EXAMPLES "Build the examples" ON)
if(GRAPHLIB_BUILD_EXAMPLES)
    add_executable(graph_example examples/main.cpp)
    target_link_libraries(graph_example PRIVATE GraphLibCore)
endif()

# --- Testing with Catch2 ---
enable_testing()
include(FetchContent)
FetchContent_Declare(
  Catch2
  GIT_REPOSITORY https://github.com/catchorg/Catch2.git
  GIT_TAG        v3.0.1
)
FetchContent_MakeAvailable(Catch2)
list(APPEND CMAKE_MODULE_PATH ${catch2_SOURCE_DIR}/extras)

add_subdirectory(tests)

# --- nlohmann/json ---
include(FetchContent)
FetchContent_Declare(
  nlohmann_json
  GIT_REPOSITORY https://github.com/nlohmann/json.git
  GIT_TAG        v3.11.2
)
FetchContent_MakeAvailable(nlohmann_json)
target_link_libraries(GraphLibCore INTERFACE nlohmann_json::nlohmann_json)