#############################################################################
##
#W  2.3.2.tst         GAP4 package IBNP          Gareth Evans & Chris Wensley
##
##  Copyright (C) 2024: please refer to the COPYRIGHT file for details.
##  
gap> START_TEST( "2.3.2.tst" );
gap> ibnp_infolevel_saved := InfoLevel( InfoIBNP );; 
gap> SetInfoLevel( InfoIBNP, 0 );; 

gap> ## this implements Example 2.3.2 in the thesis,
gap> ## using four different orderings when finding a Grobner basis,
gap> ## and where GB3 = GB4 is the Grobner basis found there

gap> R := PolynomialRing( Rationals, [ "x", "y" ] );;
gap> x := R.1;; y := R.2;;
gap> L := [ x^2 - 2*x*y + 3, 2*x*y + y^2 + 5 ];;
gap> ord1 := MonomialLexOrdering();;
gap> GB1 := GroebnerBasis( L, ord1 );
[ x^2-2*x*y+3, 2*x*y+y^2+5, -5/2*y^3+5*x-37/2*y, 5/4*y^4+21/2*y^2+25\
/4 ]
gap> ord2 := MonomialLexOrdering( [y,x] );;
gap> GB2 := GroebnerBasis( L, ord2 );
[ x^2-2*x*y+3, 2*x*y+y^2+5, -5/2*x^3-35/2*x-3*y, 5*x^4+38*x^2+9 ]
gap> ord3 := MonomialGrlexOrdering();;
gap> GB3 := GroebnerBasis( L, ord3 );
[ x^2-2*x*y+3, 2*x*y+y^2+5, -5/2*y^3+5*x-37/2*y ]
gap> ord4 := MonomialGrevlexOrdering();;
gap> GB4 := GroebnerBasis( L, ord4 );
[ x^2-2*x*y+3, 2*x*y+y^2+5, -5/2*y^3+5*x-37/2*y ]

gap> SetInfoLevel( InfoIBNP, ibnp_infolevel_saved );; 
gap> STOP_TEST( "2.3.2.tst", 10000 );

############################################################################
##
#E  2.3.2.tst  . . . . . . . . . . . . . . . . . . . . . . . . . . ends here
