#############################################################################
##
#W  4.5.11.tst        GAP4 package IBNP          Gareth Evans & Chris Wensley
##
##  Copyright (C) 2024: please refer to the COPYRIGHT file for details.
##  
gap> START_TEST( "4.5.11.tst" );
gap> ibnp_infolevel_saved := InfoLevel( InfoIBNP );; 
gap> SetInfoLevel( InfoIBNP, 0 );; 

gap> ## this implements Example 4. in the thesis,

gap> R := PolynomialRing( Rationals, [ "x", "y", "z" ] );;
gap> x := R.1;; y := R.2;; z := R.3;;
gap> ord := MonomialGrlexOrdering();;
gap> CommutativeDivision := "Pommaret";;



gap> SetInfoLevel( InfoIBNP, ibnp_infolevel_saved );; 
gap> STOP_TEST( "4.5.11.tst", 10000 );

############################################################################
##
#E  4.5.11.tst . . . . . . . . . . . . . . . . . . . . . . . . . . ends here
