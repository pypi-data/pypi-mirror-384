ReadPackage( "browse", "app/filetree.g" );

# This contributes to the list that gets created in 'app/demo.g'.
Add( NCurses.DemoDefaults,
rec( title:= "Contents of the Browse Directory (non-interactive)",
inputblocks:= [
"n:= [ 14, 14, 14 ];;  # ``do nothing'' input (means timeout)\n\
BrowseData.SetReplay( Concatenation(\n\
   \"x\", n,                     # expand the first category row,\n\
   \"ddddd\", n,                 # move the selection down,\n\
   [ NCurses.keys.ENTER ], n,  # click the entry,\n\
   \"Q\" ) );                    # and quit\n\
file:= Filename( DirectoriesPackageLibrary( \"Browse\" ), \"\" );;\n\
BrowseDirectory( file );;\n\
" ],
footer:= "(enter 'Q' for interrupting)",
cleanup:= "BrowseData.SetReplay( false );\n\
",
) );

