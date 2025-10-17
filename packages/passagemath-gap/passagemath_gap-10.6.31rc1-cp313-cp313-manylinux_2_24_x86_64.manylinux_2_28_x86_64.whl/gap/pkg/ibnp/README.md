[![CI](https://github.com/gap-packages/ibnp/actions/workflows/CI.yml/badge.svg)](https://github.com/gap-packages/ibnp/actions/workflows/CI.yml)
[![Code Coverage](https://codecov.io/github/gap-packages/ibnp/coverage.svg?branch=master&token=)](https://codecov.io/gh/gap-packages/ibnp)

# The GAP 4 package 'IBNP' 

## Introduction

The IBNP package provides methods for computing an involutive (Gröbner) 
basis B for an ideal J over a polynomial ring R in both the commutative 
and noncommutative cases. Methods are also provided to involutively reduce 
a given polynomial to its normal form in R/J.

## Distribution

 * The 'IBNP' package may be obtained from the GitHub repository at:  
     <https://gap-packages.github.io/ibnp/>

## Copyright

Copyright 2024-2025 by Gareth Evans and Chris Wensley

## Installation

 * unpack `ibnp-<version_number>.tar.gz` in the `pkg` subdirectory of the GAP root directory.
 * From within GAP load the package with:

       gap> LoadPackage("ibnp");
       true

 * The documentation is in the `doc` subdirectory.
 * To run the test file read `testall.g` from the `ibnp/tst/` directory. 

Contact
-------
If you have a question relating to ibnp, encounter any problems, or have a suggestion for extending the package in any way, please 
 * email: cdwensley.maths@btinternet.com 
 * or report an issue at: https://github.com/gap-packages/ibnp/issues/new 
