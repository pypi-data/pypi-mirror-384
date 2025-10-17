#############################################################################
##
#W  read.g          GAP 4 package `Browse'        Thomas Breuer, Frank Lübeck
##

ReadPackage("browse", "lib/ncurses.gi");
ReadPackage("browse", "lib/helpoverwrite.g");
ReadPackage( "browse", "lib/getpackagename.g" );
ReadPackage("browse", "lib/browse.gi");
ReadPackage( "browse", "lib/brgrids.g" );

# example applications
ReadPackage("browse", "app/matdisp.g");
ReadPackage("browse", "app/ctbldisp.g");
ReadPackage("browse", "app/tomdisp.g");
ReadPackage("browse", "app/gapbibl.g");
ReadPackage("browse", "app/knight.g");
ReadPackage("browse", "app/manual.g");
ReadPackage("browse", "app/puzzle.g");
ReadPackage("browse", "app/rubik.g");
ReadPackage("browse", "app/solitair.g");
ReadPackage("browse", "app/sudoku.g");
ReadPackage("browse", "app/pkgvar.g");
ReadPackage("browse", "app/gapdata.g");
ReadPackage("browse", "app/wizard.g");
# this app only works with 'readline' 
if IsBound(GAPInfo.UseReadline) and GAPInfo.UseReadline = true then
  ReadPackage("browse", "app/rldemo.g");
else
  # Bind 'LoadDemoFile' to something that shows a meaningful error message.
  BindGlobal( "LoadDemoFile", function( arg... )
    Error( "LoadDemoFile is not available without 'readline' support" );
  end );
fi;

# applications called by `BrowseGapData'
ReadPackage("browse", "app/conwaypols.g");
ReadPackage("browse", "app/methods.g");
ReadPackage("browse", "app/packages.g");
ReadPackage( "browse", "app/profile.g" );
if IsPackageMarkedForLoading( "tomlib", "1.2.0" )
   and not IsBound( GAPInfo.PackageExtensionsLoaded ) then
  ReadPackage( "browse", "app/tmdbattr.g" );
fi;
ReadPackage( "browse", "app/userpref.g" );

# demo
ReadPackage("browse", "app/demo.g");
ReadPackage("browse", "app/mouse.g");

# this must be read after 'app/demo.g'
if IsPackageMarkedForLoading( "atlasrep", "1.5.0" )
   and not IsBound( GAPInfo.PackageExtensionsLoaded ) then
  ReadPackage( "browse", "app/atlasrep_only.g" );
fi;
if IsPackageMarkedForLoading( "io", "" )
   and not IsBound( GAPInfo.PackageExtensionsLoaded ) then
  ReadPackage("browse", "app/io_only.g");
fi;

# support for database attributes
ReadPackage( "browse", "lib/brdbattr.gi" );

