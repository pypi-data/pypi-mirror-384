cmake_minimum_required(VERSION 3.15)
project(${SKBUILD_PROJECT_NAME} LANGUAGES CXX)

set(PYBIND11_FINDPYTHON ON)
find_package(pybind11 CONFIG REQUIRED)

# Collect all C++ source files
file(GLOB_RECURSE SOURCES "src/*.cpp")
# Alternatively, you can list them manually:
# set(SOURCES
#     src/main.cpp
#     src/cpp_src/volgrid.cpp
# )
pybind11_add_module(_core MODULE ${SOURCES})
install(TARGETS _core DESTINATION ${SKBUILD_PROJECT_NAME})
