#############################################################################
##
#W  involutive-cp.tst     GAP4 package IBNP      Gareth Evans & Chris Wensley
##

gap> START_TEST( "involutive-cp.tst" );
gap> ibnp_infolevel_saved := InfoLevel( InfoIBNP );; 
gap> SetInfoLevel( InfoIBNP, 0 );; 

gap> ## Section 3.2.2
gap> CommutativeDivision := "Pommaret";
"Pommaret"

gap> ## Section 3.2.3
gap> R := PolynomialRing( Rationals, [ "x", "y", "z" ] );;
gap> x := R.1;; y := R.2;; z := R.3;;
gap> ord := MonomialLexOrdering( [x,y,z] );;

gap> ## Section 3.2.4
gap> U := [ x^5*y^2*z, x^4*y*z^2, x^2*y^2*z, x*y*z^3, x*z^3, y^2*z, z ];
[ x^5*y^2*z, x^4*y*z^2, x^2*y^2*z, x*y*z^3, x*z^3, y^2*z, z ]
gap> PommaretDivision( R, U, ord );
[ [ 1 ], [ 1 ], [ 1 ], [ 1 ], [ 1 ], [ 1, 2 ], [ 1 .. 3 ] ]

gap> ## Section 3.2.5
gap> ThomasDivision( R, U, ord );
[ [ 1, 2 ], [  ], [ 2 ], [ 3 ], [ 3 ], [ 2 ], [  ] ]

gap> ## Section 3.2.6
gap> JanetDivision( R, U, ord );
[ [ 1, 2 ], [ 1, 2 ], [ 2 ], [ 1, 2, 3 ], [ 1, 3 ], [ 2 ], [ 1 ] ]

gap> ## Section 3.2.7
gap> R := PolynomialRing( Rationals, [ "a", "b" ] );;
gap> a := R.1;; b := R.2;;
gap> L2 := [ b^3 - 3*a, a^3 - 3*b ];;
gap> ord := MonomialGrlexOrdering( [a,b] );;
gap> GB2 := ReducedGroebnerBasis( L2, ord );;
gap> GB2 = L2;
true
gap> CommutativeDivision := "Pommaret";;
gap> drec2 := DivisionRecordCP( R, L2, ord );
rec( div := "Pommaret", mvars := [ [ 1, 2 ], [ 1 ] ], 
  polys := [ b^3-3*a, a^3-3*b ] )

gap> ## Section 3.2.8
gap> p := a^3*b^3 + 2*a^3*b + 3*a*b^3;;
gap> q := IPolyReduce( R, p, drec2, ord );
2*a^3*b+9*a^2+9*a*b

gap> ## Section 3.2.9
gap> r := LoggedIPolyReduceCP( R, p, drec2, ord );
rec( logs := [ a^3+3*a, 3*a ], polys := [ b^3-3*a, a^3-3*b ], 
  result := 2*a^3*b+9*a^2+9*a*b )
gap> p = r.result + r.logs[1]*r.polys[1] + r.logs[2]*r.polys[2];
true

gap> ## Section 3.2.10
gap> L3 := Concatenation( L2, [p] );;
gap> IAutoreduceCP( R, L3, ord );
[ b^3-3*a, a^3-3*b, 2*a^3*b+9*a^2+9*a*b ]
gap> L4 := Concatenation( L2, [ a^3*b-3*b^2, a^3*b^2-9*a ] );;
gap> IAutoreduceCP( R, L4, ord );
true

gap> ## Section 3.3.2
gap> ibasP := InvolutiveBasis( R, L2, ord );
rec( div := "Pommaret", mvars := [ [ 1, 2 ], [ 1 ], [ 1 ], [ 1 ] ], 
  polys := [ b^3-3*a, a^3-3*b, a^3*b-3*b^2, a^3*b^2-9*a ] )
gap> r := IPolyReduce( R, p, ibasP, ord );
9*a^2+9*a*b+6*b^2

gap> CommutativeDivision := "Thomas";;
gap> ibasT := InvolutiveBasis( R, L2, ord );
rec( div := "Thomas", 
  mvars := [ [ 2 ], [ 1 ], [ 2 ], [ 1 ], [ 2 ], [ 1 ], [ 1, 2 ] ], 
  polys := [ b^3-3*a, a^3-3*b, a*b^3-3*a^2, a^3*b-3*b^2, a^2*b^3-9*b, 
      a^3*b^2-9*a, a^3*b^3-9*a*b ] )
gap> CommutativeDivision := "Janet";;
gap> ibasJ := InvolutiveBasis( R, L2, ord );;
gap> ( ibasJ.mvars = ibasP.mvars ) and ( ibasJ.polys = ibasP.polys );
true

gap> r := LoggedIPolyReduceCP( R, p, ibasT, ord );
rec( logs := [ 0, 0, 3, 2, 0, 0, 1 ], 
  polys := [ b^3-3*a, a^3-3*b, a*b^3-3*a^2, a^3*b-3*b^2, a^2*b^3-9*b, 
      a^3*b^2-9*a, a^3*b^3-9*a*b ], result := 9*a^2+9*a*b+6*b^2 )

gap> ## Section 3.3.3
gap> ## this implements Example 4.5.2 in the thesis,
gap> SetInfoLevel( InfoIBNP, 1 );; 
gap> CommutativeDivision := "Janet";;
gap> R3 := PolynomialRing( Rationals, [ "x", "y", "z" ] );;
gap> x := R3.1;; y := R3.2;; z := R3.3;; 
gap> ord3 := MonomialLexOrdering( [x,y,z] );;
gap> F := [ y^3 + x^2, z^3 + x ];;
gap> gbas := GrobnerBasis( F, ord3 );
[ y^3+x^2, z^3+x, -z^6-y^3 ]
gap> rgbas := ReducedGrobnerBasis( F, ord3 );
[ z^6+y^3, z^3+x ]
gap> ibasF := InvolutiveBasisCP( R3, F, ord3 );
#I  restarting with basis:
[ z^3+x, y^3+x^2 ]
#I  division record for basis: rec(
div := "Janet",
mvars := [ [ 2, 3 ], [ 1, 2, 3 ] ],
polys := [ z^3+x, y^3+x^2 ] )
#I  prolongations = [ x*z^3+x^2 ]
#I  restarting with basis:
[ z^6+y^3, z^3+x, y^3+x^2 ]
#I  after autoreduction basis = 
[ z^6+y^3, z^3+x, -z^6+x^2 ]
#I  division record for basis: rec(
div := "Janet",
mvars := [ [ 1, 2, 3 ], [ 3 ], [ 1, 3 ] ],
polys := [ z^6+y^3, z^3+x, -z^6+x^2 ] )
#I  prolongations = [ y*z^3+x*y, x*z^3+x^2, -y*z^6+x^2*y ]
#I  restarting with basis:
[ z^6+y^3, z^3+x, y*z^3+x*y, -z^6+x^2 ]
#I  division record for basis: rec(
div := "Janet",
mvars := [ [ 1, 2, 3 ], [ 3 ], [ 1, 3 ], [ 1, 3 ] ],
polys := [ z^6+y^3, z^3+x, y*z^3+x*y, -z^6+x^2 ] )
#I  prolongations = [ y*z^3+x*y, y^2*z^3+x*y^2, x*z^3+x^2, -y*z^6+x^2*y ]
#I  restarting with basis:
[ z^6+y^3, z^3+x, y*z^3+x*y, y^2*z^3+x*y^2, -z^6+x^2 ]
#I  division record for basis: rec(
div := "Janet",
mvars := [ [ 1, 2, 3 ], [ 3 ], [ 1, 3 ], [ 1, 3 ], [ 1, 3 ] ],
polys := [ z^6+y^3, z^3+x, y*z^3+x*y, y^2*z^3+x*y^2, -z^6+x^2 ] )
#I  prolongations = [ y*z^3+x*y, y^2*z^3+x*y^2, y^3*z^3+x*y^3, x*z^3+x^2, -y*z\
^6+x^2*y ]
rec( div := "Janet", 
  mvars := [ [ 1, 2, 3 ], [ 3 ], [ 1, 3 ], [ 1, 3 ], [ 1, 3 ] ], 
  polys := [ z^6+y^3, z^3+x, y*z^3+x*y, y^2*z^3+x*y^2, -z^6+x^2 ] )
gap> ## now for a reduction - reset the info level:
gap> SetInfoLevel( InfoIBNP, 2 );; 
gap> p := x^7 + y^7 + z^7;;
gap> IPolyReduce( R3, p, ibasF, ord3 );
#I  reduced to: x^5*z^6+y^7+z^7
#I  reduced to: x^3*z^12+y^7+z^7
#I  reduced to: x*z^18+y^7+z^7
#I  reduced to: -z^21+y^7+z^7
#I  reduced to: -z^21-y^4*z^6+z^7
#I  reduced to: -z^21+y*z^12+z^7
-z^21+y*z^12+z^7

gap> ## Section 3.3.4
gap> SetInfoLevel( InfoIBNP, 0 );
gap> R4 := PolynomialRing( Rationals, [ "x", "y", "z", "t" ] );;
gap> x := R4.1;; y := R4.2;; z := R4.3;; t := R4.4;;
gap> H := [ x^2*t + y^3, x*t^2 + z^3 ];;
gap> ord4 := MonomialLexOrdering( [x,y,z,t] );;
gap> ibasH := InvolutiveBasisCP( R4, H, ord4 );
rec( div := "Janet",
  mvars := [ [ 1, 2, 3, 4 ], [ 1, 2, 3 ], [ 1, 3, 4 ], [ 1, 2, 3 ], 
      [ 1, 2, 3 ], [ 1, 3, 4 ], [ 1, 3, 4 ], [ 1, 2 ], [ 1, 2 ], [ 1, 2 ] ],
  polys := [ y^3*t^3+z^6, x*t^2+z^3, x*t^3+z^3*t, x*z^3-y^3*t, 
      x*z^3*t-y^3*t^2, x*y*t^3+y*z^3*t, x*y^2*t^3+y^2*z^3*t, x^2*t+y^3, 
      x^2*z*t+y^3*z, x^2*z^2*t+y^3*z^2 ] )

gap> SetInfoLevel( InfoIBNP, ibnp_infolevel_saved );; 
gap> STOP_TEST( "involutive-cp.tst", 10000 );

#############################################################################
##
#E  involutive-cp.tst . . . . . . . . . . . . . . . . . . . . . . . ends here
