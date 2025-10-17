#############################################################################
##
#W  testall.g         GAP4 package IBNP          Gareth Evans & Chris Wensley
##

LoadPackage( "ibnp" ); 
dir := DirectoriesPackageLibrary("ibnp","tst");
TestDirectory(dir, rec(exitGAP := true,
    testOptions:=rec(compareFunction := "uptowhitespace")));
FORCE_QUIT_GAP(1);
