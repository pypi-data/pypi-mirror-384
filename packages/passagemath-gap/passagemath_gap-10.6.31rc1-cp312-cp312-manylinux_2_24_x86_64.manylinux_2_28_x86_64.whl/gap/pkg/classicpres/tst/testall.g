#
# This file runs package tests. It is also referenced in the package
# metadata in PackageInfo.g.
#
LoadPackage("classicpres");
ReadPackage("classicpres","lib/test.g");

TestDirectory(DirectoriesPackageLibrary( "classicpres", "tst" ), 
  rec(exitGAP := true,compareFunction:="uptowhitespace"));

FORCE_QUIT_GAP(1);
