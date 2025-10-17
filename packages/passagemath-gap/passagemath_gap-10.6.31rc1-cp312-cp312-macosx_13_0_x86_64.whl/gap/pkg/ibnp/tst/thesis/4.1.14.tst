#############################################################################
##
#W  4.1.14.tst        GAP4 package IBNP          Gareth Evans & Chris Wensley
##
##  Copyright (C) 2024: please refer to the COPYRIGHT file for details.
##  
gap> START_TEST( "4.1.14.tst" );
gap> ibnp_infolevel_saved := InfoLevel( InfoIBNP );; 
gap> SetInfoLevel( InfoIBNP, 0 );; 

gap> ## this implements Example 4.1.14 in the thesis,
gap> ## using four different orderings when finding a Grobner basis,
gap> ## and where GB3 = GB4 is the Grobner basis found there

gap> R := PolynomialRing( Rationals, [ "x", "y", "z" ] );;
gap> x := R.1;; y := R.2;; z := R.3;;
gap> U := [ x^5*y^2*z, x^4*y*z^2, x^2*y^2*z, x*y*z^3, x*z^3, y^2*z, z ];
[ x^5*y^2*z, x^4*y*z^2, x^2*y^2*z, x*y*z^3, x*z^3, y^2*z, z ]
gap> ord := MonomialLexOrdering( [x,y,z] );;
gap> PommaretDivision( R, U, ord );
[ [ 1 ], [ 1 ], [ 1 ], [ 1 ], [ 1 ], [ 1, 2 ], [ 1 .. 3 ] ]
gap> ThomasDivision( R, U, ord );
[ [ 1, 2 ], [  ], [ 2 ], [ 3 ], [ 3 ], [ 2 ], [  ] ]
gap> JanetDivision( R, U, ord );
[ [ 1, 2 ], [ 1, 2 ], [ 2 ], [ 1, 2, 3 ], [ 1, 3 ], [ 2 ], [ 1 ] ]
gap> ##
gap> ## get the same results using OverlapDivCP
gap> ##
gap> CommutativeDivision := "Thomas";
"Thomas"
gap> DivisionRecord( R, U, ord );     
rec( div := "Thomas", 
  mvars := [ [ 1, 2 ], [  ], [ 2 ], [ 3 ], [ 3 ], [ 2 ], [  ] ], 
  polys := [ x^5*y^2*z, x^4*y*z^2, x^2*y^2*z, x*y*z^3, x*z^3, y^2*z, z ] )
gap> CommutativeDivision := "Janet"; 
"Janet"
gap> DivisionRecord( R, U, ord );    
rec( div := "Janet", 
  mvars := [ [ 1, 2 ], [ 1, 2 ], [ 2 ], [ 1, 2, 3 ], [ 1, 3 ], [ 2 ], [ 1 ] ],
  polys := [ x^5*y^2*z, x^4*y*z^2, x^2*y^2*z, x*y*z^3, x*z^3, y^2*z, z ] )
gap> CommutativeDivision := "Pommaret";
"Pommaret"
gap> DivisionRecord( R, U, ord );       
rec( div := "Pommaret", 
  mvars := [ [ 1 ], [ 1 ], [ 1 ], [ 1 ], [ 1 ], [ 1, 2 ], [ 1 .. 3 ] ], 
  polys := [ x^5*y^2*z, x^4*y*z^2, x^2*y^2*z, x*y*z^3, x*z^3, y^2*z, z ] )

gap> SetInfoLevel( InfoIBNP, ibnp_infolevel_saved );; 
gap> STOP_TEST( "4.1.14.tst", 10000 );

############################################################################
##
#E  4.1.14.tst . . . . . . . . . . . . . . . . . . . . . . . . . . ends here
