file(GLOB_RECURSE TEST_SOURCES LIST_DIRECTORIES false *.h *.cpp)

set(TEST_SOURCES
        ${PROJECT_SOURCE_DIR}/src/GraphFeatures.cpp
        ${SRC_FILES}
        )

add_executable(GraphFeatureEngineeringTest GraphFeatureEngineeringTest.cpp ${TEST_SOURCES})

include_directories(GraphFeatureEngineeringTest PUBLIC "${PROJECT_SOURCE_DIR}/submodules/parallel_cycle_enumeration/include")

if( USE_TBB )
    target_link_libraries(GraphFeatureEngineeringTest tbb)
endif()
