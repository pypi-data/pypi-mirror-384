#############################################################################
##
#W  testextras.g        GAP4 package IBNP        Gareth Evans & Chris Wensley
##
##  Copyright (C) 2024: please refer to the COPYRIGHT file for details.
##  

LoadPackage( "ibnp" ); 
TestDirectory( DirectoriesPackageLibrary( "ibnp", "tst/extras" ), 
    rec( testOptions := rec(compareFunction := "uptowhitespace") ) );

