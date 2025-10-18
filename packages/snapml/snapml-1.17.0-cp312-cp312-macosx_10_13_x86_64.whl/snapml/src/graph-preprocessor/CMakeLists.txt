cmake_minimum_required(VERSION 3.12)
project(graph-feature-preprocessor)

enable_testing()

set(CMAKE_CXX_STANDARD 14)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_COLOR_MAKEFILE ON)

string(TOUPPER "${CMAKE_BUILD_TYPE}" CMAKE_BUILD_TYPE)

# Execute if the flags have not already been specified by snapml
if("${CMAKE_CXX_FLAGS}" STREQUAL "")
    if( NOT DEFINED USE_TBB )
        if(CMAKE_C_COMPILER MATCHES "clang")
            # To be removed for the integration
            set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -fopenmp=libomp  -I/usr/lib/gcc/x86_64-redhat-linux/4.8.2/include")
        else()
            find_package(OpenMP REQUIRED)
            set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -fopenmp")
        endif()
    else()
        message(STATUS "TBB used")
        set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -DUSE_TBB")
    endif()

    ##
    # Build specific flags
    if(CMAKE_BUILD_TYPE MATCHES "DEBUG")
        message(STATUS "DEBUG build")
        set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -DDEBUG -O0 -fno-inline -fno-omit-frame-pointer")
        set(CMAKE_VERBOSE_MAKEFILE ON)
        if(CMAKE_C_COMPILER MATCHES "clang")
            set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -fsanitize=address -fno-optimize-sibling-calls")
        elseif(CMAKE_C_COMPILER MATCHES "gcc")
            set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -ftrapv")
            if(CMAKE_C_COMPILER_VERSION VERSION_GREATER 4.8)
                set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -fno-optimize-sibling-calls")
            endif()
            if(CMAKE_CXX_COMPILER_VERSION VERSION_GREATER 8.2)
                set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -fsanitize=address -ggdb")
                set(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} -fsanitize=address -ggdb")
            endif()
        endif()
    elseif (CMAKE_BUILD_TYPE MATCHES PROFILING)
        message(STATUS "PROFILING build")

        set(VTUNE_DIR "$ENV{VTUNE_PROFILER_2022_DIR}")
        set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -O2 -fno-inline -g -fno-omit-frame-pointer -DPROFILE") #
        include_directories(${VTUNE_DIR}/sdk/include)
        message(STATUS "VTUNE include directory: " ${VTUNE_DIR}/sdk/include)
        LINK_DIRECTORIES(${VTUNE_DIR}/sdk/lib64)
        message(STATUS "VTUNE lib directory: " ${VTUNE_DIR}/sdk/lib64)
    elseif (CMAKE_BUILD_TYPE MATCHES RELEASE)
        message(STATUS "RELEASE build")
        set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -O3 -Wall -Werror -Wno-sign-compare -fPIC")
    else()
        message(STATUS "RELEASE build")
        set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -O3 -Wall -Werror -Wno-sign-compare -fPIC")
    endif()
else()
    if( NOT DEFINED USE_TBB )
        find_package(OpenMP REQUIRED)
    endif()
endif()

# USE DYNAMIC GRAPH BY DEFAULT
if( NOT USE_STATIC_GRAPH )
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -DUSE_DYNAMIC_GRAPH=True")
else()
    message(STATUS "Using the static graph representation")
endif()

## GRAPH REPRESENTATION
set(GRAPH_REP_DIR "${PROJECT_SOURCE_DIR}/components/graph-representation")
file(GLOB GRAPH_REP_SRC "${GRAPH_REP_DIR}/src/*.cpp")
set(SRC_FILES ${SRC_FILES} ${GRAPH_REP_SRC})

## CYCLE ENUMERATION
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -DUSE_EXT_GRAPH")
set(CYCLE_ENUM_DIR "${PROJECT_SOURCE_DIR}/components/parallel_cycle_enumeration")
set(SRC_FILES ${SRC_FILES}
        ${CYCLE_ENUM_DIR}/src/CycleEnumeration.cpp
        ${CYCLE_ENUM_DIR}/src/LCJohnsonAlgorithm.cpp
        ${CYCLE_ENUM_DIR}/src/JohnsonsAlgorithm.cpp
        ${CYCLE_ENUM_DIR}/src/TempCycleJohnson.cpp
        ${CYCLE_ENUM_DIR}/src/ParallelCycleEnumeration.cpp)


## AML-PATTERN-DETECTION
set(SRC_FILES ${SRC_FILES}
        ${PROJECT_SOURCE_DIR}/src/outputDataStructures.cpp
        ${PROJECT_SOURCE_DIR}/src/cycles.cpp
        ${PROJECT_SOURCE_DIR}/src/scatterGather.cpp
        ${PROJECT_SOURCE_DIR}/src/fanDegreeInOut.cpp
        ${PROJECT_SOURCE_DIR}/src/vertexStatisticsFeatures.cpp
        ${PROJECT_SOURCE_DIR}/src/featureEngineering.cpp
        ${PROJECT_SOURCE_DIR}/src/GraphFeatures.cpp
        )

include_directories(PUBLIC ${PROJECT_SOURCE_DIR}/include
        ${PROJECT_SOURCE_DIR}/include/internal
        ${GRAPH_REP_DIR}/include
        ${CYCLE_ENUM_DIR}/include
        ${CYCLE_ENUM_DIR}/include/internal)

if( USE_TBB )
    find_package(TBB COMPONENTS tbbmalloc tbbmalloc_proxy REQUIRED)
    include_directories(${TBB_DIR}/../include)
endif()


if( BUILD_EXECUTABLES )
    include_directories(aml-pattern PUBLIC "${PROJECT_SOURCE_DIR}/components/parallel_cycle_enumeration/include")

    add_executable(aml-pattern src/benchmarkMain.cpp ${SRC_FILES})
    add_executable(api-test src/apiTestMain.cpp ${SRC_FILES})

    if(CMAKE_BUILD_TYPE MATCHES "PROFILING")
        target_link_libraries(aml-pattern ittnotify -ldl)
    endif()

    if( USE_TBB )
        target_link_libraries(aml-pattern tbb)
        target_link_libraries(api-test tbb)
    endif()
endif()

add_library(graphfeatures SHARED ${SRC_FILES} )
set_target_properties(graphfeatures PROPERTIES PUBLIC_HEADER ${PROJECT_SOURCE_DIR}/include/GraphFeatures.h
                                               LIBRARY_OUTPUT_DIRECTORY ${PROJECT_SOURCE_DIR}/lib)

if( USE_TBB )
    target_link_libraries(graphfeatures tbb)
endif()

if(CMAKE_BUILD_TYPE MATCHES DEBUG)
    message(STATUS "Project dir: " ${PROJECT_SOURCE_DIR})
    message(STATUS "Platform   : " ${CMAKE_SYSTEM_NAME})
    message(STATUS "Compiler   :" "${CMAKE_CXX_COMPILER} ${CMAKE_CXX_COMPILER_VERSION}")
endif()

message(STATUS "Building unit tests")
add_definitions( -DPROJECT_SOURCE_DIR=\"${PROJECT_SOURCE_DIR}\" )
add_subdirectory(test)

add_test(GraphFeatureEngineeringTest test/GraphFeatureEngineeringTest)
#add_test(GraphLibraryAPITest test/GraphLibraryAPITest)
