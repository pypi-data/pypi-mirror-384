cmake_minimum_required(VERSION 3.16)
add_executable(PrivacyTest PrivacyTest.cpp)

## GRAPH REPRESENTATION
set(GRAPH_REP_DIR "${PROJECT_SOURCE_DIR}/graph-preprocessor/components/graph-representation")
file(GLOB GRAPH_REP_SRC "${GRAPH_REP_DIR}/src/*.cpp")
set(SRC_FILES ${SRC_FILES} ${GRAPH_REP_SRC})

## GFP Unit Test
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -DGFP_TEST")
## CYCLE ENUMERATION
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -DUSE_EXT_GRAPH")
set(CYCLE_ENUM_DIR "${PROJECT_SOURCE_DIR}/graph-preprocessor/components/parallel_cycle_enumeration")
set(SRC_FILES ${SRC_FILES}
        ${CYCLE_ENUM_DIR}/src/CycleEnumeration.cpp
        ${CYCLE_ENUM_DIR}/src/LCJohnsonAlgorithm.cpp
        ${CYCLE_ENUM_DIR}/src/JohnsonsAlgorithm.cpp
        ${CYCLE_ENUM_DIR}/src/TempCycleJohnson.cpp
        ${CYCLE_ENUM_DIR}/src/ParallelCycleEnumeration.cpp)

## AML-PATTERN-DETECTION
set(SRC_FILES ${SRC_FILES}
        ${PROJECT_SOURCE_DIR}/graph-preprocessor/src/outputDataStructures.cpp
        ${PROJECT_SOURCE_DIR}/graph-preprocessor/src/cycles.cpp
        ${PROJECT_SOURCE_DIR}/graph-preprocessor/src/scatterGather.cpp
        ${PROJECT_SOURCE_DIR}/graph-preprocessor/src/fanDegreeInOut.cpp
        ${PROJECT_SOURCE_DIR}/graph-preprocessor/src/vertexStatisticsFeatures.cpp
        ${PROJECT_SOURCE_DIR}/graph-preprocessor/src/featureEngineering.cpp
        ${PROJECT_SOURCE_DIR}/graph-preprocessor/src/GraphFeatures.cpp
        )

include_directories(PUBLIC ${PROJECT_SOURCE_DIR}/graph-preprocessor/include
        ${PROJECT_SOURCE_DIR}/include
        ${PROJECT_SOURCE_DIR}/graph-preprocessor/include/internal        
        ${GRAPH_REP_DIR}/include
        ${CYCLE_ENUM_DIR}/include
        ${CYCLE_ENUM_DIR}/include/internal)

# Include all source files in API_SRC directly
file(GLOB API_SRC "../include/*.cpp" "../preprocessing/src/*.cpp" ${SRC_FILES})
add_library(api SHARED ${API_SRC})

if(WITH_ZOS)
    target_link_libraries(api /usr/lpp/aie/zdnn/lib/libzdnn.x)
endif()

if(WITH_ZFLAGS)
	target_link_libraries(api "/usr/lib64/libzdnn.so")
endif()

if(WITH_GPU)
    set_source_files_properties(RidgeRegressionTest.cpp PROPERTIES CUDA_SOURCE_PROPERTY_FORMAT OBJ)
    set_source_files_properties(LogisticRegressionTest.cpp PROPERTIES CUDA_SOURCE_PROPERTY_FORMAT OBJ)
    set_source_files_properties(SupportVectorMachineTest.cpp PROPERTIES CUDA_SOURCE_PROPERTY_FORMAT OBJ)
    set_source_files_properties(LassoRegressionTest.cpp PROPERTIES CUDA_SOURCE_PROPERTY_FORMAT OBJ)
    set_source_files_properties(SparseLogisticRegressionTest.cpp PROPERTIES CUDA_SOURCE_PROPERTY_FORMAT OBJ)
    set_source_files_properties(ChunkingTest.cpp PROPERTIES CUDA_SOURCE_PROPERTY_FORMAT OBJ)
    set_source_files_properties(LoadersTest.cpp PROPERTIES CUDA_SOURCE_PROPERTY_FORMAT OBJ)
    set_source_files_properties(CocoaTest.cpp PROPERTIES CUDA_SOURCE_PROPERTY_FORMAT OBJ)
    set_source_files_properties(DatasetTest.cpp PROPERTIES CUDA_SOURCE_PROPERTY_FORMAT OBJ)
    set_source_files_properties(MultiThreadingTest.cpp PROPERTIES CUDA_SOURCE_PROPERTY_FORMAT OBJ)
    set_source_files_properties(LoadBalancingTest.cpp PROPERTIES CUDA_SOURCE_PROPERTY_FORMAT OBJ)
    set_source_files_properties(SGDTest.cpp PROPERTIES CUDA_SOURCE_PROPERTY_FORMAT OBJ)

    cuda_add_executable(RidgeRegressionTest RidgeRegressionTest.cpp)
    cuda_add_executable(LogisticRegressionTest LogisticRegressionTest.cpp)
    cuda_add_executable(SupportVectorMachineTest SupportVectorMachineTest.cpp)
    cuda_add_executable(LassoRegressionTest LassoRegressionTest.cpp)
    cuda_add_executable(SparseLogisticRegressionTest SparseLogisticRegressionTest.cpp)
    cuda_add_executable(ChunkingTest ChunkingTest.cpp)
    cuda_add_executable(LoadersTest LoadersTest.cpp)
    cuda_add_executable(CocoaTest CocoaTest.cpp)
    cuda_add_executable(DatasetTest DatasetTest.cpp)
    cuda_add_executable(MultiThreadingTest MultiThreadingTest.cpp)
    cuda_add_executable(LoadBalancingTest LoadBalancingTest.cpp)
    cuda_add_executable(SGDTest SGDTest.cpp)
    cuda_add_executable(RBFSamplerTest RBFSamplerTest.cpp)

    cuda_add_library(histdevice SHARED DeviceSolverWrapper.cu ../include/HistSolverGPUFactory.cu)

    cuda_add_executable(TreeLearnerTest TreeLearnerTest.cpp)
    cuda_add_executable(TreeForestTest TreeForestTest.cpp)
    cuda_add_executable(TreeBoosterTest TreeBoosterTest.cpp)
    cuda_add_executable(MixBoosterTest MixBoosterTest.cpp)
    cuda_add_executable(CompressedTreesTest CompressedTreesTest.cpp)
    cuda_add_executable(MulticlassBoosterTest MulticlassBoosterTest.cpp)
    cuda_add_executable(PreProcessingTest PreProcessingTestUtils.cpp PreProcessingTest.cpp)

else()
    if(WITH_MAC OR WITH_ZOS)
        add_executable(RidgeRegressionTest RidgeRegressionTest.cpp;../third-party/pthread-barrier-macos/src/pthread_barrier.c)
        add_executable(LogisticRegressionTest LogisticRegressionTest.cpp;../third-party/pthread-barrier-macos/src/pthread_barrier.c)
        add_executable(SupportVectorMachineTest SupportVectorMachineTest.cpp;../third-party/pthread-barrier-macos/src/pthread_barrier.c)
        add_executable(LassoRegressionTest LassoRegressionTest.cpp;../third-party/pthread-barrier-macos/src/pthread_barrier.c)
        add_executable(SparseLogisticRegressionTest SparseLogisticRegressionTest.cpp;../third-party/pthread-barrier-macos/src/pthread_barrier.c)
        add_executable(ChunkingTest ChunkingTest.cpp;../third-party/pthread-barrier-macos/src/pthread_barrier.c)
        add_executable(LoadersTest LoadersTest.cpp;../third-party/pthread-barrier-macos/src/pthread_barrier.c)
        add_executable(CocoaTest CocoaTest.cpp;../third-party/pthread-barrier-macos/src/pthread_barrier.c)
        add_executable(DatasetTest DatasetTest.cpp;../third-party/pthread-barrier-macos/src/pthread_barrier.c)
        add_executable(TreeForestTest TreeForestTest.cpp;../third-party/pthread-barrier-macos/src/pthread_barrier.c)
        add_executable(MultiThreadingTest MultiThreadingTest.cpp;../third-party/pthread-barrier-macos/src/pthread_barrier.c)
        add_executable(SGDTest SGDTest.cpp;../third-party/pthread-barrier-macos/src/pthread_barrier.c)
    else()
        add_executable(RidgeRegressionTest RidgeRegressionTest.cpp)
        add_executable(LogisticRegressionTest LogisticRegressionTest.cpp)
        add_executable(SupportVectorMachineTest SupportVectorMachineTest.cpp)
        add_executable(LassoRegressionTest LassoRegressionTest.cpp)
        add_executable(SparseLogisticRegressionTest SparseLogisticRegressionTest.cpp)
        add_executable(ChunkingTest ChunkingTest.cpp)
        add_executable(LoadersTest LoadersTest.cpp)
        add_executable(CocoaTest CocoaTest.cpp)
        add_executable(DatasetTest DatasetTest.cpp)
        add_executable(TreeForestTest TreeForestTest.cpp)
        add_executable(MultiThreadingTest MultiThreadingTest.cpp)
        add_executable(SGDTest SGDTest.cpp)
    endif()
    add_executable(LoadBalancingTest LoadBalancingTest.cpp)
    add_executable(RBFSamplerTest RBFSamplerTest.cpp)
    add_executable(TreeLearnerTest TreeLearnerTest.cpp)
    add_executable(TreeBoosterTest TreeBoosterTest.cpp)
    add_executable(MixBoosterTest MixBoosterTest.cpp)
    add_executable(CompressedTreesTest CompressedTreesTest.cpp)
    add_executable(MulticlassBoosterTest MulticlassBoosterTest.cpp)
    add_executable(PreProcessingTest  PreProcessingTestUtils.cpp PreProcessingTest.cpp)

    if(WITH_ZFLAGS OR WITH_ZOS)
        add_executable(MBITBoosterTest MBITBoosterTest.cpp)
        add_executable(MBITBoosterThrdTest MBITBoosterThrdTest.cpp)
        # add_executable(MBITBoosterOptTest MBITBoosterOptTest.cpp)
    endif()

endif()
add_executable(GfpEncoderTest PreProcessingTestUtils.cpp GfpEncoderTest.cpp)
if(WITH_GPU)
	#target_link_libraries(histdevice ${CUDA_CUBLAS_LIBRARIES})
    target_link_libraries(TreeLearnerTest histdevice)
    target_link_libraries(TreeForestTest histdevice)
    target_link_libraries(TreeBoosterTest histdevice)
    target_link_libraries(MixBoosterTest histdevice)
    target_link_libraries(CompressedTreesTest histdevice)
    target_link_libraries(MulticlassBoosterTest histdevice)
    target_link_libraries(api histdevice)
endif()


target_link_libraries(TreeLearnerTest api)
target_link_libraries(TreeForestTest api)
target_link_libraries(TreeBoosterTest api)
target_link_libraries(MixBoosterTest api)
target_link_libraries(CompressedTreesTest api)
target_link_libraries(MulticlassBoosterTest api)
target_link_libraries(CocoaTest api)
target_link_libraries(SGDTest api)
target_link_libraries(LassoRegressionTest api)
target_link_libraries(DatasetTest api)
target_link_libraries(SparseLogisticRegressionTest api)
target_link_libraries(SupportVectorMachineTest api)
target_link_libraries(LogisticRegressionTest api)
target_link_libraries(LoadersTest api)
target_link_libraries(ChunkingTest api)
target_link_libraries(MultiThreadingTest api)
target_link_libraries(RidgeRegressionTest api)
target_link_libraries(RBFSamplerTest api)
target_link_libraries(PreProcessingTest api)
target_link_libraries(GfpEncoderTest api)

if(WITH_ZFLAGS OR WITH_ZOS)
    target_link_libraries(MBITBoosterTest api)
    target_link_libraries(MBITBoosterThrdTest api)
    # target_link_libraries(MBITBoosterOptTest api)
endif()
