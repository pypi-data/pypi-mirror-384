# aml-pattern-detection

Library used for computing subgraph patterns in financial networks and generating ML features based on these patterns.

### Prerequisites

Compiler:
- GCC version 7 or higher (both Z and x86 systems)
or
- Clang version 5.0.1 or higher (only x86 systems)

TBB version of the code requires:
- Intel Threading Building Blocks 2020 Update 2, available here: https://github.com/oneapi-src/oneTBB/releases/tag/v2020.2

### Compilation

```
mkdir build
cd build
cmake ..
make
```

The compiled library and executables will use dynamic graph representation.
To use static graph representation instead, add `-DUSE_STATIC_GRAPH=True` to the cmake command.

#### Using Clang _libomp_ instead of GCC _libgomp_

On x86 systems, Clang and `libomp` can be used to improve performance of the openMP version of the library.
On Centos and RedHat systems, clang and `libomp` can be installed by executing the following instructions
```
sudo yum install llvm-toolset-7
scl enable llvm-toolset-7 bash
```

If clang with `libomp` is available, call cmake as follows:
```
cmake .. -DCMAKE_C_COMPILER=`which clang` -DCMAKE_CXX_COMPILER=`which clang++`
```
#### Using TBB instead of OpenMP
If you wish to use TBB instead of OpenMP, call cmake as follows:
```
cmake .. -DUSE_TBB
```

### Unit tests

To run unit tests, simply execute:
```
make test
```

The output should be:
```
Running tests...
Test project <...>/aml-pattern-detection/build
    Start 1: FeatureEngineeringTest
1/2 Test #1: FeatureEngineeringTest ...........   Passed    3.51 sec
    Start 2: LibraryAPITest
2/2 Test #2: LibraryAPITest ...................   Passed    5.74 sec

100% tests passed, 0 tests failed out of 2

Total Test time (real) =   9.26 sec
```

### Shared library

The generated shared library `libgraphfeatures.so` is placed in `lib` directory.
The python API of this library is defined in `python/pygraphfeatures.py`.
The C++ API is defined in `include/GraphFeatures.h`.
For more information, refer to those two files.


### Executables
By default, no executables were created. To create executables, add `-DBUILD_EXECUTABLES=True` to the cmake command.
The generated executable `aml-pattern` can be used to create the output features for the given AML benchmark and
to obtain the performance results.

```
./aml-pattern -f /path/to/input/network -config ../config_files/<config_file_name> -n 12 -batch 2048 -np 
```

Removing the `-np` option enables printing the output features to the file `output_type2_batch<batch_size>.csv`, which
is in the same directory as the input network.

Run `./aml-pattern -h` for the full list of command line options.