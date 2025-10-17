LoadPackage("smallantimagmas");

TestDirectory(DirectoriesPackageLibrary("smallantimagmas", "tst"),
  rec(exitGAP     := true,
      testOptions := rec(compareFunction := "uptowhitespace")));

FORCE_QUIT_GAP(1);
