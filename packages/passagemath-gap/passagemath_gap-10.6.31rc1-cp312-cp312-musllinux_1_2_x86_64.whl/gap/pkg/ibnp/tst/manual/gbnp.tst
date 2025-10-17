#############################################################################
##
#W  gbnp.tst          GAP4 package IBNP          Gareth Evans & Chris Wensley
##

gap> START_TEST( "gbnp.tst" );
gap> ibnp_infolevel_saved := InfoLevel( InfoIBNP );; 
gap> SetInfoLevel( InfoIBNP, 0 );; 

## Section 2.1
gap> A3 := FreeAssociativeAlgebraWithOne(Rationals,"a","b","c");;
gap> a := A3.1;; b := A3.2;; c := A3.3;;
gap> ## define a polynomial and convert to NP-format
gap> p1 := 7*a^2*b*c + 8*b*c*a;
(8)*b*c*a+(7)*a^2*b*c
gap> Lp1 := GP2NP( p1 );
[ [ [ 1, 1, 2, 3 ], [ 2, 3, 1 ] ], [ 7, 8 ] ]
gap> ## define an NP-poly; clean it; and convert to a polynomial
gap> Lp2 := [ [ [1,1], [1,2,1], [3], [1,1], [3,1,2] ], [5,6,7,8,9] ];;
gap> PrintNP( Lp2 );
 5a^2 + 6aba + 7c + 8a^2 + 9cab
gap> Lp2 := CleanNP( Lp2 );
[ [ [ 3, 1, 2 ], [ 1, 2, 1 ], [ 1, 1 ], [ 3 ] ], [ 9, 6, 13, 7 ] ]
gap> ## note the degree lexicographic ordering
gap> PrintNP( Lp2 );
 9cab + 6aba + 13a^2 + 7c
gap> p2 := NP2GP( Lp2, A3 );
(9)*c*a*b+(6)*a*b*a+(13)*a^2+(7)*c
gap> PrintNPList( [ Lp1, Lp2, [ [], [] ], [ [ [] ], [9] ] ] );
 7a^2bc + 8bca
 9cab + 6aba + 13a^2 + 7c
 0
 9 

## Section 2.2
gap> p := [ [ [2,2,2], [2,1], [1,2] ], [1,3,-1] ];;
gap> q := [ [ [1,1], [2] ], [1,1] ];;
gap> PrintNPList( [p,q] );
 b^3 + 3ba - ab
 a^2 + b
gap> GB := SGrobner( [p,q] );;
gap> PrintNPList(GB);
 a^2 + b
 ba - ab
 b^3 + 2ab

## Section 2.3
gap> Lp1;
[ [ [ 1, 1, 2, 3 ], [ 2, 3, 1 ] ], [ 7, 8 ] ]
gap> Lp2;
[ [ [ 3, 1, 2 ], [ 1, 2, 1 ], [ 1, 1 ], [ 3 ] ], [ 9, 6, 13, 7 ] ]
gap> GtNPoly( Lp1, Lp2 );
true
gap> ## select the lexicographic ordering and reorder p1, p2
gap> lexord := NCMonomialLeftLexicographicOrdering( A3 );;
gap> PatchGBNP( lexord );
LtNP patched.
GtNP patched.
gap> Lp1 := CleanNP( Lp1 );
[ [ [ 2, 3, 1 ], [ 1, 1, 2, 3 ] ], [ 8, 7 ] ]
gap> Lp2 := CleanNP( Lp2 );
[ [ [ 3, 1, 2 ], [ 3 ], [ 1, 2, 1 ], [ 1, 1 ] ], [ 9, 7, 6, 13 ] ]
gap> GtNPoly( Lp1, Lp2 );
false
gap> ## revert to degree lex order
gap> UnpatchGBNP();;
LtNP restored.
GtNP restored.
gap> Lp1 := CleanNP( Lp1 );
[ [ [ 1, 1, 2, 3 ], [ 2, 3, 1 ] ], [ 7, 8 ] ]
gap> Lp2 := CleanNP( Lp2 );
[ [ [ 3, 1, 2 ], [ 1, 2, 1 ], [ 1, 1 ], [ 3 ] ], [ 9, 6, 13, 7 ] ]
gap> GtNPoly( Lp1, Lp2 );
true

gap> SetInfoLevel( InfoIBNP, ibnp_infolevel_saved );; 
gap> STOP_TEST( "gbnp.tst", 10000 );

#############################################################################
##
#E  gbnp.tst . . . . . . . . . . . . . . . . . . . . . . . . . . . ends here
