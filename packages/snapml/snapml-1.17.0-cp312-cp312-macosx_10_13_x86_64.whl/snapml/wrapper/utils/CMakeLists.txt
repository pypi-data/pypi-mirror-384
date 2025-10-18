cuda_add_library(snapmlutils SHARED common.cpp)
target_link_libraries(snapmlutils "${PYTHON_LIBRARIES}")
