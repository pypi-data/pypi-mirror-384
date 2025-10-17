This file describes changes in the GAP package 'liealgdb'.

* 2.3.0 (2025-09-24)

  - Fix incorrect ordering for `N6_26`, `N6_27`; that is, the order
    of `NilpotentLieAlgebra(F, [6,26])` and `NilpotentLieAlgebra(F, [6,27])`
    was swapped, and also their order in the output of `AllNilpotentLieAlgebras`;
    that manifested in the output of `LieAlgebraIdentification` not matching.
  - Stop using `DeclareAutoreadableVariables`
  - Various janitorial changes

* 2.2.1 (2019-10-07)

  - Minor janitorial changes

* 2.2 (2018-04-09)

  - Clarify that package is licensed under GPL 2 or later
  - Move package to GitHub
  - Set the GAP team as new package maintainer
  - Use AutoDoc to build the manual
  - Other internal (technical) or administrative changes

* 2.1 (2010-03-28)

* 2.0.2 (2007-08-28)

* 2.0.1 (2007-08-28)

* 2.0 (2007-08-06)

* 1.0 (2006-10-20)
