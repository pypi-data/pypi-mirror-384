#############################################################################
##
#W  4.1.16.tst        GAP4 package IBNP          Gareth Evans & Chris Wensley
##
##  Copyright (C) 2024: please refer to the COPYRIGHT file for details.
##  
gap> START_TEST( "4.1.16.tst" );
gap> ibnp_infolevel_saved := InfoLevel( InfoIBNP );; 
gap> SetInfoLevel( InfoIBNP, 0 );; 

gap> ## this implements Examples 4.1.16 and 4.4.11 in the thesis,
gap> ## using four different orderings when finding a Grobner basis,
gap> ## and where GB3 = GB4 is the Grobner basis found there

gap> CommutativeDivision := "Pommaret";;
gap> R := PolynomialRing( Rationals, [ "x", "y" ] );;
gap> x := R.1;; y := R.2;;
gap> L := [ x^2 - 2*x*y + 3, 2*x*y + y^2 + 5 ];;
gap> ord3 := MonomialGrlexOrdering( [x,y] );;
gap> GB3 := GroebnerBasis( L, ord3 );
[ x^2-2*x*y+3, 2*x*y+y^2+5, -5/2*y^3+5*x-37/2*y ]
gap> ibasP := InvolutiveBasis( R, GB3, ord3 );
rec( div := "Pommaret", mvars := [ [ 1 ], [ 1 ], [ 1, 2 ], [ 1 ] ], 
  polys := [ 2*x*y+y^2+5, x^2+y^2+8, 5/2*y^3-5*x+37/2*y, 2*x*y^2+2*x-12/5*y ] 
 )
gap> CommutativeDivision := "Janet";;
gap> ibasJ := InvolutiveBasis( R, GB3, ord3 );
rec( div := "Janet", mvars := [ [ 1 ], [ 1 ], [ 1, 2 ], [ 1 ] ], 
  polys := [ 2*x*y+y^2+5, x^2+y^2+8, 5/2*y^3-5*x+37/2*y, 2*x*y^2+2*x-12/5*y ] 
 )
gap> ## The Pommaret and Janet divisions give the same basis ...
gap> ibasJ.polys = ibasP.polys;     
true
gap> ibasJ.mvars = ibasP.mvars;
true
gap> ## ... but the Thoimas basis has an additional 4 polynomials
gap> CommutativeDivision := "Thomas";;
gap> ibasT := InvolutiveBasis( R, GB3, ord3 );
rec( div := "Thomas", 
  mvars := [ [  ], [ 1 ], [ 2 ], [  ], [ 1 ], [ 2 ], [ 1 ], [ 1, 2 ] ], 
  polys := [ 2*x*y+y^2+5, x^2+y^2+8, 5/2*y^3-5*x+37/2*y, 2*x*y^2+2*x-12/5*y, 
      x^2*y+2*x+3/5*y, 5/2*x*y^3-17/4*y^2-25/4, x^2*y^2-2/5*y^2-5, 
      5/2*x^2*y^3-2*x-51/10*y ] )
gap> SetInfoLevel( InfoIBNP, ibnp_infolevel_saved );; 
gap> STOP_TEST( "4.1.16.tst", 10000 );

############################################################################
##
#E  4.1.16.tst . . . . . . . . . . . . . . . . . . . . . . . . . . ends here
