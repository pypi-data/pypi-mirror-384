cmake_minimum_required (VERSION 3.18)

if(CMAKE_HOST_SYSTEM_NAME STREQUAL "OS390")
    set(CMAKE_C_COMPILER "ibm-clang64")
    set(CMAKE_CXX_COMPILER "ibm-clang++64")
endif()

project(testapi)

enable_testing()

set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -std=c++11")
include_directories(PUBLIC "${PROJECT_SOURCE_DIR}/include")

if(CMAKE_HOST_SYSTEM_NAME STREQUAL "OS390")
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -fzos-le-char-mode=ascii")
endif()

add_executable(test-rf capi-rf-example.cpp Dataset.cpp)
add_executable(test-boost capi-booster-example.cpp Dataset.cpp)
add_executable(test-dt capi-dt-example.cpp Dataset.cpp)
add_executable(test-import capi-import-example.cpp Dataset.cpp)
add_executable(test-fail capi-failure-tests.cpp)

target_include_directories(test-rf PUBLIC "${PROJECT_SOURCE_DIR}/../../../include")
target_include_directories(test-boost PUBLIC "${PROJECT_SOURCE_DIR}/../../../include")
target_include_directories(test-dt PUBLIC "${PROJECT_SOURCE_DIR}/../../../include")
target_include_directories(test-import PUBLIC "${PROJECT_SOURCE_DIR}/../../../include")
target_include_directories(test-fail PUBLIC "${PROJECT_SOURCE_DIR}/../../../include")

if(CMAKE_HOST_SYSTEM_NAME STREQUAL "OS390")
    target_link_libraries(test-rf "${PROJECT_SOURCE_DIR}/../../../libsnapmlcore.x")
    target_link_libraries(test-boost "${PROJECT_SOURCE_DIR}/../../../libsnapmlcore.x")
    target_link_libraries(test-dt "${PROJECT_SOURCE_DIR}/../../../libsnapmlcore.x")
    target_link_libraries(test-import "${PROJECT_SOURCE_DIR}/../../../libsnapmlcore.x")
    target_link_libraries(test-fail "${PROJECT_SOURCE_DIR}/../../../libsnapmlcore.x")
else()
    target_link_libraries(test-rf "${PROJECT_SOURCE_DIR}/../../../libsnapmlcore.so")
    target_link_libraries(test-boost "${PROJECT_SOURCE_DIR}/../../../libsnapmlcore.so")
    target_link_libraries(test-dt "${PROJECT_SOURCE_DIR}/../../../libsnapmlcore.so")
    target_link_libraries(test-import "${PROJECT_SOURCE_DIR}/../../../libsnapmlcore.so")
    target_link_libraries(test-fail "${PROJECT_SOURCE_DIR}/../../../libsnapmlcore.so")
endif()

add_test(test-rf test-rf)
add_test(test-boost test-boost)
add_test(test-dt test-dt)
add_test(test-import test-import)
add_test(test-fail test-fail)
