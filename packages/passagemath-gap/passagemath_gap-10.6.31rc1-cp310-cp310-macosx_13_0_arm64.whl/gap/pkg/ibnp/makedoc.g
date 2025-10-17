#############################################################################
##
##  makedoc.g          GAP package `ibnp'        Gareth Evans & Chris Wensley
##  
##  Copyright (C) 2024: please refer to the COPYRIGHT file for details.
##
##  This builds the documentation of the IBNP package. 
##  Needs: GAPDoc & AutoDoc packages, latex, pdflatex, mkindex
##  call this with GAP from within the package root directory 

LoadPackage( "ibnp" );
LoadPackage( "AutoDoc" ); 

AutoDoc(rec( 
    gapdoc := rec( 
        LaTeXOptions := rec( EarlyExtraPreamble := """
            \usepackage[all]{xy} 
        """ )),  
    scaffold := rec(
        includes := [ "intro.xml",  "gbnp.xml", "involutive-cp.xml",
                      "monom.xml",  "poly.xml", "involutive-np.xml" ],
        bib := "bib.xml", 
        entities := rec( 
            AutoDoc := "<Package>AutoDoc</Package>",
            IBNP := "<Package>IBNP</Package>",
            GBNP := "<Package>GBNP</Package>",
            Grob := "Gröbner"
        )
    )
));
