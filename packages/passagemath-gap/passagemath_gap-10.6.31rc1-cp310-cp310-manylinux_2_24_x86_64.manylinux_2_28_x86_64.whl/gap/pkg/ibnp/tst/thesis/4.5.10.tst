#############################################################################
##
#W  4.5.10.tst        GAP4 package IBNP          Gareth Evans & Chris Wensley
##
##  Copyright (C) 2024: please refer to the COPYRIGHT file for details.
##  

gap> START_TEST( "4.5.10.tst" );
gap> ibnp_infolevel_saved := InfoLevel( InfoIBNP );; 
gap> SetInfoLevel( InfoIBNP, 0 );; 

gap> ## this implements Example 4.5.10 in the thesis,

gap> CommutativeDivision := "Janet";;
gap> CommutativeDivision;
 "Janet"

gap> R2 := PolynomialRing( Rationals, [ "x", "y" ] );;
gap> x := R2.1;; y := R2.2;;
gap> ord2 := MonomialLexOrdering( [y,x] );;

gap> F := [ 2*x*y + x^2 + 5, y^2 + x + 8 ];;
gap> drecF := DivisionRecord( R2, F, ord2 );
rec( div := "Janet", mvars := [ [ 1 ], [ 1, 2 ] ], 
  polys := [ x^2+2*x*y+5, y^2+x+8 ] )
gap> ibasF := InvolutiveBasisCP( R2, F, ord2 );
rec( div := "Janet", mvars := [ [ 1 ], [  ], [ 1 ], [ 1, 2 ] ], 
  polys := [ 1/2*x^4+2*x^3+21*x^2+25/2, -1/2*x^3-2*x^2-37/2*x+5*y, 
      x^2+2*x*y+5, y^2+x+8 ] )

gap> R3 := PolynomialRing( Rationals, [ "t", "x", "y" ] );;
gap> t := R3.1;; x := R3.2;; y := R3.3;;
gap> ord3 := MonomialLexOrdering( [y,x,t] );;

gap> ## H is the homogenised version of F obtained by adding variable t
gap> ## assuming the lead monomials of the polynomials are all distinct,
gap> ## making t the least variable ensures that t is multiplicative for
gap> ## every polynomial, and so the prolongations considered are the
gap> ## homogeneous versions of those computed when processing F.

gap> H := [ 2*x*y + x^2 + 5*t^2, y^2 + x*t + 8*t^2 ];;
gap> drecH := DivisionRecord( R3, H, ord3 );
rec( div := "Janet", mvars := [ [ 1, 2 ], [ 1, 2, 3 ] ], 
  polys := [ x^2+2*x*y+5*t^2, x*t+y^2+8*t^2 ] )
gap> ibasH := InvolutiveBasisCP( R3, H, ord3 );
rec( div := "Janet", mvars := [ [ 1, 2 ], [ 1 ], [ 1, 2 ], [ 1, 2, 3\
 ] ], 
  polys := [ 1/2*x^4+2*x^3*t+21*x^2*t^2+25/2*t^4, 
      -1/2*x^3-2*x^2*t-37/2*x*t^2+5*y*t^2, x^2+2*x*y+5*t^2, x*t+y^2+8*t^2 ] )

gap> ## putting t=1 in these polynomials gives the unhomogenised versions
gap> polys1 := List( ibasH.polys, p -> Value( p, [t], [1] ) );
[ 1/2*x^4+2*x^3+21*x^2+25/2, -1/2*x^3-2*x^2-37/2*x+5*y, x^2+2*x*y+5,\
 y^2+x+8 ]
gap> polys1 = ibasF.polys;                                    
true

gap> SetInfoLevel( InfoIBNP, ibnp_infolevel_saved );; 
gap> STOP_TEST( "4.5.10.tst", 10000 );

############################################################################
##
#E  4.5.10.tst . . . . . . . . . . . . . . . . . . . . . . . . . . ends here
