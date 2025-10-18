cmake_minimum_required (VERSION 3.18)

# Setting the compiler hard coded is not recommended in this script.
# It avoids accidentally to use the wrong standard compiler.
if(WITH_ZOS)
    set(CMAKE_C_COMPILER "ibm-clang64")
    set(CMAKE_CXX_COMPILER "ibm-clang++64")
endif()

project (libsnapml)

option(WITH_GPU "WITH_GPU" ON)
option(WITH_NUMA "WITH_NUMA" ON)
option(WITH_ZFLAGS "WITH_ZFLAGS" OFF)
option(WITH_NATIVE "WITH_NATIVE" OFF)
option(WITH_MAC "WITH_MAC" OFF)
option(WITH_WIN "WITH_WIN" OFF)
option(WITH_ZOS "WITH_ZOS" OFF)
option(WITH_POWER "WITH_POWER" OFF)
option(WITH_AVX512 "WITH_AVX512" OFF)
option(WITH_AVX2 "WITH_AVX2" ON)
option(USE_STATIC_GRAPH "USE_STATIC_GRAPH" OFF)

message(">> -------------------------------------------------------")
message(">> Snap ML Compilation Options")
message(">> GPU support (WITH_GPU):                  ${WITH_GPU}")
message(">> NUMA support (WITH_NUMA):                ${WITH_NUMA}")
message(">> Z-specific compiler flags (WITH_ZFLAGS): ${WITH_ZFLAGS}")
message(">> Native compiler flags (WITH_NATIVE):     ${WITH_NATIVE}")
message(">> Mac OS compilation (WITH_MAC):           ${WITH_MAC}")
message(">> Compile with Visual Studio (WITH_WIN):   ${WITH_WIN}")
message(">> z/OS compilation (WITH_ZOS):             ${WITH_ZOS}")
message(">> Compile on Power (WITH_POWER):           ${WITH_POWER}")
message(">> Compile for x86 AVX-512 (WITH_AVX512):   ${WITH_AVX512}")
message(">> Compile for x86 AVX2 (WITH_AVX2):        ${WITH_AVX2}")
message(">> Preprocessor graph (USE_STATIC_GRAPH):   ${USE_STATIC_GRAPH}")
message(">> -------------------------------------------------------")

set(CMAKE_MODULE_PATH ${CMAKE_HOME_DIRECTORY}/../cmake)
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_HOME_DIRECTORY}/../../)
set(CMAKE_TEST_DIRECTORY ${CMAKE_HOME_DIRECTORY}/../../../test)
#set(CMAKE_SHARED_LINKER_FLAGS "${CMAKE_SHARED_LINKER_FLAGS} -Wl,--no-undefined" )

if(NOT(WITH_ZOS))
   find_package(OpenMP REQUIRED)
endif()
#find_package(BLAS REQUIRED)

if(WITH_ZOS)
    message("build for USS")

    file(TOUCH "${CMAKE_BINARY_DIR}/libsnapmlutils.x")

    add_definitions(--config /etc/clang.cfg)
    add_definitions(-D_ALL_SOURCE)
    add_definitions(-D_OPEN_SYS_MUTEX_EXT)
    add_definitions(-DWITH_ZOS)
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -O3 -Wall -Werror -Wno-error=unused-function -Wno-sign-compare -Wno-unused-lambda-capture -march=arch12 -fzos-le-char-mode=ascii -std=c++11 -fzvector -fvisibility=default -fPIC")
    add_definitions(-DGLM_INLINE=inline)
    add_definitions(-DUNUSED=__attribute__\(\(unused\)\))
    add_definitions(-DZ14_SIMD)
elseif(NOT(WITH_WIN))
    set(CMAKE_SHARED_LIBRARY_SUFFIX .so)
    add_definitions(-DGLM_INLINE=inline)
    add_definitions(-DUNUSED=__attribute__\(\(unused\)\))

    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -O3 -Wall -Werror -Wno-sign-compare -fPIC")

    if(WITH_MAC)
        message("Using macOS")
        set (CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wno-unused-private-field")
        add_definitions(-DWITH_MAC)
    else()
        # Linux
        set (CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -fopenmp")
    endif()

    # normal behaviour (x86)
    if(NOT(WITH_NATIVE) AND NOT(WITH_ZFLAGS) AND NOT (WITH_POWER))
        if(WITH_AVX512)
            set (CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -mfma -mavx512f -mavx512dq -mtune='corei7'")
            add_compile_definitions(X86_AVX512)
        else()
            if(WITH_AVX2)
                set (CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -mavx2 -mtune='corei7'")
                add_compile_definitions(X86_AVX2)
            endif()
        endif()
    endif()

    # tune of native architecture
    if(WITH_NATIVE)
        set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -march=native -mtune=native")
    endif()

    # additional Z-specific flags
    if(WITH_ZFLAGS)
        # Let compiler make Z-specific optimizations
        message("Using ZFLAGS")
        set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -std=gnu++11 -mvx -m64 -march=z14 -mtune=z14 -mzarch -mzvector -Wno-attributes -Wno-unused-variable")
        # Add -march=z14 -mzvector -fstack-protector-all -funroll-loops to CMAKE_CXX_FLAGS?
        add_compile_definitions(Z14_SIMD)
    else()
        if(WITH_POWER)
            message("Using POWER")
            set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -std=gnu++11 -maltivec -Wno-attributes -Wno-unused-variable")
            add_compile_definitions(POWER_VMX)
        else()
            set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -std=c++11 -ffast-math -fno-finite-math-only -flto -fno-operator-names")
        endif()
    endif()

else()
    message("Using Windows")
    set (CMAKE_SHARED_LIBRARY_SUFFIX .pyd)
    set (CMAKE_SHARED_LIBRARY_PREFIX "lib")
    add_definitions(-DWITH_VS)
    add_definitions(-D_USE_MATH_DEFINES)
    add_definitions(-DGLM_INLINE=__forceinline)
    add_definitions(-DUNUSED=)
    set(CMAKE_CXX_STANDARD 11)
    set(CMAKE_CXX_STANDARD_REQUIRED ON)
    set(CMAKE_CXX_FLAGS "/WX /MD /Zi /O2 /Oi /Oy /GT /Gy /Qpar /fp:fast /openmp /EHsc")
    if(WITH_AVX2)
        set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} /arch:AVX /arch:AVX2")
        add_compile_definitions(X86_AVX2)
    endif()
    set(CMAKE_CXX_FLAGS_RELEASE ${CMAKE_CXX_FLAGS})
    set(CMAKE_CXX_FLAGS_RELWITHDEBINFO ${CMAKE_CXX_FLAGS})
    add_compile_definitions(WIN_BUILD)
endif()

if(WITH_GPU)
    # Compile with GPU support
    find_package(CUDA REQUIRED)
    if(CUDA_VERSION LESS 10)
        set(CUDA_ARCH_TARGETS "-gencode=arch=compute_60,code=sm_60;-gencode=arch=compute_70,code=sm_70")
    elseif(CUDA_VERSION LESS 11)
        set(CUDA_ARCH_TARGETS "-gencode=arch=compute_60,code=sm_60;-gencode=arch=compute_70,code=sm_70;-gencode=arch=compute_75,code=sm_75;-gencode=arch=compute_75,code=compute_75")
    else()
        set(CUDA_ARCH_TARGETS "-gencode=arch=compute_60,code=sm_60;-gencode=arch=compute_70,code=sm_70;-gencode=arch=compute_75,code=sm_75;-gencode=arch=compute_80,code=sm_80")
    endif()
    set(CUDA_HOST_COMPILATION_CPP "ON")
    set(CUDA_PROPAGATE_HOST_FLAGS "FALSE")
    set(CUDA_HOST_FLAGS "-O3,-Wall,-Werror,-Wno-sign-compare,-fPIC,-fopenmp,-ffast-math,-fno-finite-math-only,-fno-operator-names")
    if(NOT(WITH_POWER))
        set(CUDA_HOST_FLAGS "${CUDA_HOST_FLAGS},-mtune='corei7'")
    else()
        set(CUDA_HOST_FLAGS "${CUDA_HOST_FLAGS},-mno-float128")
    endif()

    set(CUDA_NVCC_FLAGS "-std=c++14;-use_fast_math;-Werror cross-execution-space-call,deprecated-declarations;-Xcompiler ${CUDA_HOST_FLAGS};${CUDA_ARCH_TARGETS}")

    add_definitions(-DWITH_CUDA)
    #add_definitions(-DTWO_GPUS)
    #message("${CUDA_NVCC_FLAGS}")
else()
    add_definitions(-D__host__=)
    add_definitions(-D__device__=)
    #message("${CMAKE_CXX_FLAGS}")
endif()

if(WITH_NUMA)
    # compile with numa
    add_definitions(-DWITH_NUMA)
    find_package(Numa REQUIRED)
endif()

message("${CMAKE_CURRENT_SOURCE_DIR}")

# USE DYNAMIC GRAPH BY DEFAULT
if( NOT USE_STATIC_GRAPH )
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -DUSE_DYNAMIC_GRAPH=True")
else()
    message(STATUS "Using the static graph preprocessor representation")
endif()

set(CPLUSPLUS_SRC_FILES ${CPLUSPLUS_SRC_FILES})
file(GLOB CPLUSPLUS_SRC_FILES "${PROJECT_SOURCE_DIR}/../../src/include/*" "${PROJECT_SOURCE_DIR}/../../src/preprocessing/src/*")
list(APPEND CPLUSPLUS_SRC_FILES "${PROJECT_SOURCE_DIR}/../../src/graph-preprocessor/include/internal"
"${PROJECT_SOURCE_DIR}/../../src/graph-preprocessor/src/outputDataStructures.cpp"
                         "${PROJECT_SOURCE_DIR}/../../src/graph-preprocessor/src/cycles.cpp"
                         "${PROJECT_SOURCE_DIR}/../../src/graph-preprocessor/src/fanDegreeInOut.cpp"
                         "${PROJECT_SOURCE_DIR}/../../src/graph-preprocessor/src/vertexStatisticsFeatures.cpp"
                         "${PROJECT_SOURCE_DIR}/../../src/graph-preprocessor/src/featureEngineering.cpp"
                         "${PROJECT_SOURCE_DIR}/../../src/graph-preprocessor/src/outputDataStructures.cpp"
                         "${PROJECT_SOURCE_DIR}/../../src/graph-preprocessor/src/scatterGather.cpp"
                         "${PROJECT_SOURCE_DIR}/../../src/graph-preprocessor/src/GraphFeatures.cpp")
                         
if(NOT(WITH_WIN OR WITH_ZOS))
    ## GRAPH REPRESENTATION
    set(GRAPH_REP_DIR "${PROJECT_SOURCE_DIR}/../../src/graph-preprocessor/components/graph-representation")
    file(GLOB GRAPH_REP_SRC "${GRAPH_REP_DIR}/src/*.cpp")
    set(CPLUSPLUS_SRC_FILES ${CPLUSPLUS_SRC_FILES} ${GRAPH_REP_SRC})

    ## CYCLE ENUMERATION
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -DUSE_EXT_GRAPH")
    set(CYCLE_ENUM_DIR "${PROJECT_SOURCE_DIR}/../../src/graph-preprocessor/components/parallel_cycle_enumeration")
    file(GLOB CYCLE_ENUM_SRC_FILES "${CYCLE_ENUM_DIR}/src/*.cpp")
    set(CPLUSPLUS_SRC_FILES ${CPLUSPLUS_SRC_FILES} ${CYCLE_ENUM_SRC_FILES})

    ## AML-PATTERN-DETECTION
    set(PATTERNS_DIR "${PROJECT_SOURCE_DIR}../../src/graph-preprocessor")
    file(GLOB PATTERNS_SRC_FILES "${PATTERNS_DIR}/src/*.cpp")
    set(CPLUSPLUS_SRC_FILES ${CPLUSPLUS_SRC_FILES} ${PATTERNS_SRC_FILES})
endif()

if(WITH_MAC OR WITH_ZOS)
    set(CPLUSPLUS_SRC_FILES "${CPLUSPLUS_SRC_FILES};../../src/third-party/pthread-barrier-macos/src/pthread_barrier.c")
endif()


if(WITH_AVX2 OR WITH_AVX512)
    set(LIBNAME_CORE snapmlcore_avx2)
else()
    set(LIBNAME_CORE snapmlcore)
endif()

if(WITH_GPU)
    cuda_add_library(${LIBNAME_CORE} SHARED ${CPLUSPLUS_SRC_FILES})
else()
    add_library(${LIBNAME_CORE} SHARED ${CPLUSPLUS_SRC_FILES})
endif()

if(WITH_ZFLAGS)
    add_library(zdnninternal SHARED IMPORTED)
    set_target_properties(zdnninternal PROPERTIES IMPORTED_LOCATION "/usr/lib64/libzdnn.so")
    target_link_libraries(${LIBNAME_CORE} zdnninternal)
endif()

if(WITH_MAC OR WITH_ZOS)
    include_directories(PUBLIC "${PROJECT_SOURCE_DIR}/../../src/third-party/pthread-barrier-macos/inc")
endif()


include_directories(PUBLIC "${PROJECT_SOURCE_DIR}/../../include")
include_directories(PUBLIC "${PROJECT_SOURCE_DIR}/../../src/include")


if(NOT(WITH_WIN OR WITH_ZOS))
    include_directories(PUBLIC "${PROJECT_SOURCE_DIR}/../../src/graph-preprocessor/include")
    include_directories(PUBLIC "${GRAPH_REP_DIR}/include")
    include_directories(PUBLIC "${GRAPH_REP_DIR}/include/internal")
    include_directories(PUBLIC "${CYCLE_ENUM_DIR}/include")
    include_directories(PUBLIC "${CYCLE_ENUM_DIR}/include/internal")
    
    # GRAPH PREPROCESSOR
    include_directories(PUBLIC  ${PROJECT_SOURCE_DIR}/../../src/graph-preprocessor/include
                                ${PROJECT_SOURCE_DIR}/../../src/graph-preprocessor/include/internal)
endif()

include_directories(PUBLIC "${PROJECT_SOURCE_DIR}/../../src/test")
include_directories(PUBLIC "${PROJECT_SOURCE_DIR}/../../src/third-party/cub")
include_directories(PUBLIC "${PROJECT_SOURCE_DIR}/../../src/third-party/eigen")
include_directories(PUBLIC "${PROJECT_SOURCE_DIR}/../../src/third-party/rapidjson/include")
include_directories(PUBLIC "${PROJECT_SOURCE_DIR}/../utils")

if(WITH_ZOS)
    include_directories(PUBLIC "/usr/lpp/aie/zdnn/include") 
endif()

if (WITH_MAC)
    target_link_libraries(${LIBNAME_CORE} OpenMP::OpenMP_CXX)
    set_target_properties(${LIBNAME_CORE} PROPERTIES LINK_FLAGS "-undefined dynamic_lookup")
endif ()

if (WITH_WIN)
    set_target_properties(${LIBNAME_CORE} PROPERTIES RUNTIME_OUTPUT_DIRECTORY_RELEASE ${CMAKE_HOME_DIRECTORY}/../../)
endif ()

if(WITH_NUMA)
    target_link_libraries(${LIBNAME_CORE} ${NUMA_LIBRARY})
    include_directories(PUBLIC ${NUMA_INCLUDE_DIR})
endif()

if(WITH_ZOS)
    target_link_libraries(${LIBNAME_CORE} "/usr/lpp/aie/zdnn/lib/libzdnn.x")
endif()

