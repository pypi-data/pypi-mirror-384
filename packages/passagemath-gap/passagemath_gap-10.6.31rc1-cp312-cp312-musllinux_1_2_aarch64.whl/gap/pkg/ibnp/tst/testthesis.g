#############################################################################
##
#W  testthesis.g        GAP4 package IBNP        Gareth Evans & Chris Wensley
##
##  Copyright (C) 2024: please refer to the COPYRIGHT file for details.
##  

LoadPackage( "ibnp" ); 
TestDirectory( DirectoriesPackageLibrary( "ibnp", "tst/thesis" ), 
    rec( testOptions := rec(compareFunction := "uptowhitespace") ) );

