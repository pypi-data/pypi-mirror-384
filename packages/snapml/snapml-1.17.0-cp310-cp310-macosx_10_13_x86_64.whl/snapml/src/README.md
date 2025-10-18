# src

This repository contains a *header-only* library that provides the core functionality that is used by [snap-ml-local](https://github.ibm.com/mldlppc/snap-ml-local), [snap-ml-spark](https://github.ibm.com/mldlppc/snap-ml-spark) and [snap-ml-mpi](https://github.ibm.com/mldlppc/snap-ml-mpi).

# Compilation on Linux/MacOS
```
git clone --recursive git@github.ibm.com:snap-zrl/src.git
cd src
mkdir build
cd build
cmake .. (GPU based compile, for CPU based one use 'cmake -DWITH_GPU=OFF ..', for MacOS add '-DWITH_MAC=ON')
make -j
make test
```
# Dependencies on Ubuntu
install numctl related packages 
```
sudo apt-get install -y libnuma1 libnuma-dev numactl
```
# Dependencies on RHEL
install numctl related packages
```
sudo yum install -y numactl-libs numactl numactl-devel
```
# Compilation on Windows/Visual Studio
```
git clone --recursive git@github.ibm.com:snap-zrl/src.git
cd src
mkdir build
cd build
cmake ../CMakeLists.txt -G "Visual Studio 16 2019" -DWITH_GPU=OFF -DWITH_WIN=ON -B .
(or 'cmake -DWITH_GPU=OFF -DWITH_WIN=ON ..' with anaconda cmake)
cmake --build . --config Release -j
cmake --build . --target RUN_TESTS --config Release
```
 
You should see the output:
```
$ make test
Running tests...
Test project /home/ysm/Projects/SnapML/src/build
      Start  1: RidgeRegressionTest
 1/19 Test  #1: RidgeRegressionTest ..............   Passed    0.01 sec
      Start  2: LogisticRegressionTest
 2/19 Test  #2: LogisticRegressionTest ...........   Passed    0.01 sec
      Start  3: SupportVectorMachineTest
 3/19 Test  #3: SupportVectorMachineTest .........   Passed    0.01 sec
      Start  4: SparseLogisticRegressionTest
 4/19 Test  #4: SparseLogisticRegressionTest .....   Passed    0.00 sec
      Start  5: LassoRegressionTest
 5/19 Test  #5: LassoRegressionTest ..............   Passed    0.01 sec
      Start  6: ChunkingTest
 6/19 Test  #6: ChunkingTest .....................   Passed    0.83 sec
      Start  7: LoadersTest
 7/19 Test  #7: LoadersTest ......................   Passed   35.40 sec
      Start  8: CocoaTest
 8/19 Test  #8: CocoaTest ........................   Passed    1.18 sec
      Start  9: DatasetTest
 9/19 Test  #9: DatasetTest ......................   Passed    0.00 sec
      Start 10: MultiThreadingTest
10/19 Test #10: MultiThreadingTest ...............   Passed    3.30 sec
      Start 11: LoadBalancingTest
11/19 Test #11: LoadBalancingTest ................   Passed    0.00 sec
      Start 12: SGDTest
12/19 Test #12: SGDTest ..........................   Passed    3.68 sec
      Start 13: PrivacyTest
13/19 Test #13: PrivacyTest ......................   Passed    1.56 sec
      Start 14: TreeLearnerTest
14/19 Test #14: TreeLearnerTest ..................   Passed    0.01 sec
      Start 15: TreeForestTest
15/19 Test #15: TreeForestTest ...................   Passed    2.33 sec
      Start 16: TreeBoosterTest
16/19 Test #16: TreeBoosterTest ..................   Passed    0.58 sec
      Start 17: MixBoosterTest
17/19 Test #17: MixBoosterTest ...................   Passed   26.91 sec
      Start 18: RBFSamplerTest
18/19 Test #18: RBFSamplerTest ...................   Passed    0.01 sec
      Start 19: CompressedTreesTest
19/19 Test #19: CompressedTreesTest ..............   Passed    0.00 sec

100% tests passed, 0 tests failed out of 19

Total Test time (real) =  75.83 sec

```

