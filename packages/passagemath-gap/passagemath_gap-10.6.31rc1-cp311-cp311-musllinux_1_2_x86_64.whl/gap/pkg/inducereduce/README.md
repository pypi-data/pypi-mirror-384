# The GAP 4 package `InduceReduce'

The package "InduceReduce" provides an implementation of Unger's algorithm for
computing the table of ordinary irreducile characters of a finite group. The
algorithm works by inducing characters from suitably chosen elementary
subgroups and finding an orthogonal basis of the resulting lattice of
characters by LLL lattice reduction.


## Installing and Loading the package

InduceReduce does not use external binaries and, therefore, works without
restrictions on the type of the operating system.

There are two ways of installing a GAP package. If you have permission to add
files to the installation of GAP on your system you may install InduceReduce into
the 'pkg' subdirectory of the GAP installation tree. Otherwise you may install
InduceReduce in a private 'pkg' directory (for details see '76.1 Installing a GAP Package'
and '9.2 GAP Root Directories' in the reference manual).

Once you have installed the package, you can load it in a GAP session using
the following command:

    gap> LoadPackage("InduceReduce");


## Support

For bug reports, feature requests and suggestions, please refer to

   <https://github.com/gap-packages/InduceReduce/issues>


## License

Copyright (C) 2018  Jonathan Gruber

This package is maintained by Jonathan Gruber <jonathan.gruber@fau.de>

Distributed under the terms of the GNU General Public License (GPL) v3

The GAP package "InduceReduce" is free software: you can redistribute
it and/or modify it under the terms of the GNU General Public License
as published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

InduceReduce is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with InduceReduce. If not, see <https://www.gnu.org/licenses/>.
