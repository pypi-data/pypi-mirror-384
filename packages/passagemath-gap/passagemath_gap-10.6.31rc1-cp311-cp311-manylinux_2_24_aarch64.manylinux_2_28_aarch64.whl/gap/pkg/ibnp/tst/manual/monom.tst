#############################################################################
##
#W  monom.tst         GAP4 package IBNP          Gareth Evans & Chris Wensley
##

gap> START_TEST( "monom.tst" );
gap> LoadPackage( "ibnp" );
true
gap> ibnp_infolevel_saved := InfoLevel( InfoIBNP );; 
gap> SetInfoLevel( InfoIBNP, 0 );; 

## SubSection 4.1.1
gap> GeneratorsOfAlgebra( AlgebraIBNP );
[ (1)*<identity ...>, (1)*a, (1)*b ]
gap> Algebra2IBNP = AlgebraIBNP;
true
gap> A3 := Algebra3IBNP;
<algebra-with-one over Rationals, with 3 generators>

## Subsection 4.1.2
gap> GBNP.ConfigPrint( "a", "b", "c" );
gap> mon := [2,1,1,1,3,3,1];;
gap> PrintNM( mon );
ba^3c^2a
gap> L := [ [1,2,2], [3,1,2], [3,3,3], [2], [ ] ];;
gap> PrintNMList( L );                            
ab^2
cab
c^3
b
1

## SubSection 4.1.3
gap> m := NM2GM( mon, A3 );
(1)*b*a^3*c^2*a
gap> NM2GMList( [ mon, Reversed(mon), Concatenation(mon,mon) ], A3 );
[ (1)*b*a^3*c^2*a, (1)*a*c^2*a^3*b, (1)*(b*a^3*c^2*a)^2 ]

## SubSection 4.1.4                      ^
gap> a:=A3.1;; b:=A3.2;; c:=A3.3;;
gap> p := (a*b*c)^2;;             
gap> GM2NM(p);
[ 1, 2, 3, 1, 2, 3 ]
gap> GM2NMList( [ p, p^2, a^3, b^4, c^5 ] );
[ [ 1, 2, 3, 1, 2, 3 ], [ 1, 2, 3, 1, 2, 3, 1, 2, 3, 1, 2, 3 ], [ 1, 1, 1 ], 
  [ 2, 2, 2, 2 ], [ 3, 3, 3, 3, 3 ] ]

## SubSection 4.1.5
gap> mon := [2,1,1,1,3,3,1];;
gap> PrefixNM( mon, 3 );
[ 2, 1, 1 ]
gap> SubwordNM( mon, 3, 6 );
[ 1, 1, 3, 3 ]
gap> SuffixNM( mon, 3 );
[ 3, 3, 1 ]

## SubSection 4.1.6
gap> m1 := [2,1,1,1,2,2,1,1];;           ## m1 = ba^3b^2a^2
gap> m2 := [1,1,2,2,1,1];;               ## m2 = a^2b^2a^2
gap> SuffixPrefixPosNM( m1, m2, 1, 5 );  ## overlap is a
1
gap> SuffixPrefixPosNM( m1, m2, 2, 5 );  ## overlap is a^2
2
gap> SuffixPrefixPosNM( m1, m2, 3, 5 );  ## no longer an overlap
0
gap> SuffixPrefixPosNM( m2, m1, 1, 5 );  ## overlap is ba^2
3

## SubSection 4.1.7
gap> m3 := [ 1, 1, 2 ];;
gap> SubwordPosNM( m3, m1, 1 );
3
gap> SubwordPosNM( m3, m2, 1 );
1
gap> SubwordPosNM( m3, m2, 2 );
0
gap> IsSubwordNM( [ 2, 1, 2 ], m1 );
false

## SubSection 4.1.8
gap> mon4 := [2,2,2,2,1,1,1,3,3];;
gap> LeadVarNM( mon4 );
2
gap> LeadExpNM( mon4 );
4
gap> TailNM( mon4 );
[ 1, 1, 1, 3, 3 ]

## SubSection 4.1.9
gap> GBNP.ConfigPrint( "a", "b", "c" );
gap> m := [ 1, 2, 3, 1, 2, 1, 2, 3 ];;
gap> d := [ 1, 2 ];;
gap> PrintNMList( [ m, d ] );
abcababc
ab
gap> divs := DivNM( m, d );
[ [ [ 1, 2, 3, 1, 2 ], [ 3 ] ], [ [ 1, 2, 3 ], [ 1, 2, 3 ] ],
[[ ],[3,1,2,1,2,3]]]
gap> PrintNMList( divs[1] );
abcab
c

gap> SetInfoLevel( InfoIBNP, ibnp_infolevel_saved );; 
gap> STOP_TEST( "monom.tst", 10000 );

#############################################################################
##
#E  monom.tst . . . . . . . . . . . . . . . . . . . . . . . . . . . ends here
