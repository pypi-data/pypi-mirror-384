
@mainpage
@copydoc maingroup

@defgroup maingroup Main Page

@defgroup wrapper Wrapper Code

@defgroup python Python Interface

@defgroup c-api Snap ML C++ API

@defgroup pythonclasses Classes
@ingroup python

@defgroup pythonutils Utilities
@ingroup python

@addtogroup maingroup
@{

### Documentation of the Snap ML code

The Snap ML code consist of three layers:
* a Python interface for public usage,
* C++ code where the algorithms are implemented,
* and an interface between both.

@dot
graph design {
    node [shape=record, width=2 ];
    py [ label = "Python interface code" URL="@ref python" ];
    wrapper [ label = "Python-C++ interface" URL="@ref wrapper" ];
    cpp [ label = "C++ source code" ];
    py -- wrapper -- cpp;
}
@enddot

@}
