if IsPackageMarkedForLoading( "atlasrep", "1.6.0" ) then
  ReadPackage( "browse", "app/atlasbrowse.g" );
else
  ReadPackage( "browse", "app/atlasbrowse_old.g" );
fi;

# This contributes to the list that gets created in 'app/demo.g'.
Add( NCurses.DemoDefaults,
rec( title:= "Table of Contents of AtlasRep (non-interactive)",
inputblocks:= [
"d:= [ NCurses.keys.DOWN ];;  r:= [ NCurses.keys.RIGHT ];;\n\
c:= [ NCurses.keys.ENTER ];;  n:= [ 14, 14, 14 ];;  # ``do nothing''\n\
BrowseData.SetReplay( Concatenation(\n\
  \"/A5\",     # Find the string A5\n\
  d, d, r, c, c, n,  # s. t. just the word matches, enter, click on A5,\n\
  d, c, \"Q\",  # move down, click on this row, return to the first table,\n\
  d, d, c, d, c, n, # move down twice, click on A6, click on the first row\n\
  \"Q\", \"Q\" ) );     # and quit the two nested tables\n\
",
"tworeps:= BrowseAtlasInfo();;\n\
BrowseData.SetReplay( false );\n\
if fail in tworeps then\n\
  NCurses.Alert( [ \"no access to the Web ATLAS\" ], 2000 );;\n\
else\n\
  NCurses.Alert( [ \"the representations returned belong to the groups \",\n\
     String( List( tworeps, x -> x.identifier[1] ) ) ], 2000 );;\n\
fi;\n\
" ],
footer:= "(enter 'Q' for interrupting)",
cleanup:= "BrowseData.SetReplay( false );\n\
",
) );

