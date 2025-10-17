LoadPackage("alco");
dirs := DirectoriesPackageLibrary( "alco", "tst" );
TestDirectory(dirs, rec(exitGAP := true, testOptions := rec(transformFunction := NormalizedWhitespace)));
