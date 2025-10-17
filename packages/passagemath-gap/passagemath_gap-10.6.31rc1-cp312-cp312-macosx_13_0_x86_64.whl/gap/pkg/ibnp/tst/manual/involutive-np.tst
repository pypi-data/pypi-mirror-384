#############################################################################
##
#W  involutive-np.tst     GAP4 package IBNP      Gareth Evans & Chris Wensley
##

gap> START_TEST( "involutive-np.tst" );
gap> ibnp_infolevel_saved := InfoLevel( InfoIBNP );; 
gap> SetInfoLevel( InfoIBNP, 0 );; 

gap> ## Section 6.1.1
gap> A3 := Algebra3IBNP;;
gap> a:=A3.1;;  b:=A3.2;; c:=A3.3;;
gap> ord := NCMonomialLeftLengthLexicographicOrdering( A3 );;
gap> M6 := [ a*b, a, b*c, a*c, c*b, c^2 ];;           
gap> U6 := GM2NMList( M6 );
[ [ 1, 2 ], [ 1 ], [ 2, 3 ], [ 1, 3 ], [ 3, 2 ], [ 3, 3 ] ]
gap> LeftDivision( A3, U6, ord );   
[ [ [ 1 .. 3 ], [ 1 .. 3 ], [ 1 .. 3 ], [ 1 .. 3 ], [ 1 .. 3 ], [ 1 .. 3 ] ], 
  [ [  ], [  ], [  ], [  ], [  ], [  ] ] ]

gap> ## Section 6.1.2
gap> RightDivision( A3, U6, ord );
[ [ [  ], [  ], [  ], [  ], [  ], [  ] ], 
  [ [ 1 .. 3 ], [ 1 .. 3 ], [ 1 .. 3 ], [ 1 .. 3 ], [ 1 .. 3 ], [ 1 .. 3 ] ] ]

gap> ## Section 6.1.3
gap> M6;
[ (1)*a*b, (1)*a, (1)*b*c, (1)*a*c, (1)*c*b, (1)*c^2 ]
gap> LeftOverlapDivision( A3, U6, ord );               
[ [ [ 1 .. 3 ], [ 1 .. 3 ], [ 1 .. 3 ], [ 1 .. 3 ], [ 1 .. 3 ], [ 1 .. 3 ] ], 
  [ [ 1, 2 ], [ 1 ], [ 1 ], [ 1 ], [ 1, 2 ], [ 1 ] ] ]

gap> ## Section 6.1.4
gap> RightOverlapDivision( A3, U6, ord );               
[ [ [ 1 .. 3 ], [ 1 .. 3 ], [ 2 ], [ 1 .. 3 ], [  ], [  ] ], 
  [ [ 1 .. 3 ], [ 1 .. 3 ], [ 1 .. 3 ], [ 1 .. 3 ], [ 1 .. 3 ], [ 1 .. 3 ] ] ]

gap> ## Section 6.1.5
gap> NoncommutativeDivision := "LeftOverlap";
"LeftOverlap"

gap> ## Section 6.1.6
gap> L3 := [ [ [ [1,2,2], [3] ], [1,-1] ],
>            [ [ [2,3,3], [1] ], [1,-1] ],
>            [ [ [3,1,1], [2] ], [1,-1] ] ];;
gap> PrintNPList( L3 );
 ab^2 - c 
 bc^2 - a 
 ca^2 - b 
gap> drec := DivisionRecord( A3, L3, ord );
rec( div := "LeftOverlap", 
  mvars := [ [ [ 1 .. 3 ], [ 1 .. 3 ], [ 1 .. 3 ] ], 
      [ [ 1, 2 ], [ 2, 3 ], [ 1, 3 ] ] ], 
  polys := [ [ [ [ 1, 2, 2 ], [ 3 ] ], [ 1, -1 ] ], 
      [ [ [ 2, 3, 3 ], [ 1 ] ], [ 1, -1 ] ], 
      [ [ [ 3, 1, 1 ], [ 2 ] ], [ 1, -1 ] ] ] )

gap> ## Section 6.1.7
gap> ## choose a polynomial to reduce
gap> p := 5*c^2*a^2*b^2 + 6*b^2*c^2*a^2 + 7*a^2*b^2*c^2;;
gap> ## convert to NP format and reduce
gap> Lp := GP2NP( p );
[ [ [ 3, 3, 1, 1, 2, 2 ], [ 2, 2, 3, 3, 1, 1 ], [ 1, 1, 2, 2, 3, 3 ] ], 
  [ 5, 6, 7 ] ]
gap> Lrp := IPolyReduce( A3, Lp, drec, ord );;
gap> ## convert back to a polynomial
gap> rp := NP2GP( Lrp, A3 );
(5)*c^2*a*c+(6)*b^2*c*b+(7)*a^2*b*a
gap> ## p-rp should now belong to the ideal and reduce to 0
gap> q := p - rp;;
gap> Lq := GP2NP( q );;
gap> Lrq := IPolyReduce( A3, Lq, drec, ord );
[ [  ], [  ] ]

gap> ## Section 6.1.8
gap> logr := LoggedIPolyReduce( A3, Lp, drec, ord );  
rec( logs := [ [ [ 5, [ 3, 3, 1 ], [  ] ] ], [ [ 7, [ 1, 1, 2 ], [  ] ] ], 
      [ [ 6, [ 2, 2, 3 ], [  ] ] ] ], 
  polys := [ [ [ [ 1, 2, 2 ], [ 3 ] ], [ 1, -1 ] ], 
      [ [ [ 2, 3, 3 ], [ 1 ] ], [ 1, -1 ] ], 
      [ [ [ 3, 1, 1 ], [ 2 ] ], [ 1, -1 ] ] ], 
  result := [ [ [ 3, 3, 1, 3 ], [ 2, 2, 3, 2 ], [ 1, 1, 2, 1 ] ], [ 5, 6, 7 ] 
     ] )
gap> logr.result = Lrp;
true
gap> L := logr.logs;;
gap> p1 := ScalarMulNP( BimulNP( L[1][1][2], L3[1], L[1][1][3] ), L[1][1][1] );;
gap> p2 := ScalarMulNP( BimulNP( L[2][1][2], L3[2], L[2][1][3] ), L[2][1][1] );;
gap> q := AddNP( p1, p2, 1, 1 );;
gap> p3 := ScalarMulNP( BimulNP( L[3][1][2], L3[3], L[3][1][3] ), L[3][1][1] );;
gap> q := AddNP( q, p3, 1, 1 );;
gap> Lp = AddNP( q, Lrp, 1, 1 );
true

gap> ## Section 6.1.9
gap> VerifyLoggedRecordNP( Lp, logr );
true

gap> ## Section 6.1.10
gap> L4 := Concatenation( L3, [Lp] );;
gap> R4 := IAutoreduceNP( A3, L4, ord );;
gap> PrintNPList( R4 );
 5c^2ac + 6b^2cb + 7a^2ba 
 ca^2 - b 
 bc^2 - a 
 ab^2 - c 
gap> IAutoreduceNP( A3, R4, ord );
true

gap> ## Section 6.2.1
gap> gbas := SGrobner( L3 );;
gap> Length( gbas );         
64
gap> ## that's too large an example to continue with, so add a fourth poly
gap> K4 := Concatenation( L3, [ [ [ [1,1,2], [3] ], [1,-1] ] ] );;
gap> PrintNPList( K4 );             
 ab^2 - c 
 bc^2 - a 
 ca^2 - b 
 a^2b - c 
gap> gbas := SGrobner( K4 );;
gap> PrintNPList( gbas );
 b - a 
 c - a 
 a^3 - a 
gap> ## so the only reduced elements are {1,a,a^2} with a^3=a
gap> ibasK := InvolutiveBasis( A3, K4, ord );
rec( div := "LeftOverlap", 
  mvars := 
    [ 
      [ [ 1 .. 3 ], [ 1 .. 3 ], [ 1 .. 3 ], [ 1 .. 3 ], [ 1 .. 3 ], 
          [ 1 .. 3 ], [ 1 .. 3 ] ], 
      [ [ 2, 3 ], [ 2, 3 ], [ 2, 3 ], [ 2, 3 ], [ 2, 3 ], [ 2, 3 ], [ 2, 3 ] 
         ] ], 
  polys := [ [ [ [ 3, 1, 1 ], [ 1 ] ], [ 1, -1 ] ], 
      [ [ [ 2, 1, 1 ], [ 1 ] ], [ 1, -1 ] ], 
      [ [ [ 1, 1, 1 ], [ 1 ] ], [ 1, -1 ] ], 
      [ [ [ 3, 1 ], [ 1, 1 ] ], [ 1, -1 ] ], 
      [ [ [ 2, 1 ], [ 1, 1 ] ], [ 1, -1 ] ], [ [ [ 3 ], [ 1 ] ], [ 1, -1 ] ], 
      [ [ [ 2 ], [ 1 ] ], [ 1, -1 ] ] ] )
gap> PrintNPList( ibasK.polys );             
 ca^2 - a 
 ba^2 - a 
 a^3 - a 
 ca - a^2 
 ba - a^2 
 c - a 
 b - a 
gap> Lr := IPolyReduce( A3, p, ibasK, ord );;
gap> PrintNP( Lr );
 18a^2 

gap> NoncommutativeDivision := "RightOverlap";;
gap> ribasK := InvolutiveBasis( A3, K4, ord );;  
gap> PrintNPList( ribasK.polys );                
 a^3 - a 
 c - a 
 b - a 
gap> ## note that this different

gap> ## Section 6.3.1
gap> P4 := [ [ [ [1,2], [3] ], [1,-2] ],
>            [ [ [2,1], [3] ], [1,-2] ],
>            [ [ [1,3], [2] ], [1,-2] ],
>            [ [ [3,1], [2] ], [1,-2] ] ];;
gap> PrintNPList( P4 );
 ab - 2c 
 ba - 2c 
 ac - 2b 
 ca - 2b 
gap> NoncommutativeDivision := "LeftOverlap";;
gap> ibasP := InvolutiveBasisNP( A3, P4, ord );
rec( div := "LeftOverlap", 
  mvars := 
    [ 
      [ [ 1 .. 3 ], [ 1 .. 3 ], [ 1 .. 3 ], [ 1 .. 3 ], [ 1 .. 3 ], [ 1 .. 3 ]\
 
         ], [ [  ], [ 2, 3 ], [ 1 ], [ 1 ], [  ], [ 2, 3 ] ] ], 
  polys := [ [ [ [ 3, 3 ], [ 2, 2 ] ], [ 1, -1 ] ], 
      [ [ [ 3, 2 ], [ 2, 3 ] ], [ 1, -1 ] ], 
      [ [ [ 3, 1 ], [ 2 ] ], [ 1, -2 ] ], [ [ [ 2, 1 ], [ 3 ] ], [ 1, -2 ] ], 
      [ [ [ 1, 3 ], [ 2 ] ], [ 1, -2 ] ], [ [ [ 1, 2 ], [ 3 ] ], [ 1, -2 ] ] 
     ] )
gap> PrintNPList( ibasP.polys );
 c^2 - b^2 
 cb - bc 
 ca - 2b 
 ba - 2c 
 ac - 2b 
 ab - 2c 
gap> ## check that cbc reduces to b^3 and abc reduces to 2b^2
gap> IPolyReduce( A3, GP2NP( c*b*c ), ibasP, ord );
[ [ [ 2, 2, 2 ] ], [ 1 ] ]
gap> IPolyReduce( A3, GP2NP( a*b*c ), ibasP, ord );
[ [ [ 2, 2 ] ], [ 2 ] ]
gap> ## now apply the strong left overlap division - two polynomials are added
gap> NoncommutativeDivision := "StrongLeftOverlap";;
gap> sbasP := InvolutiveBasisNP( A3, P4, ord );
rec( div := "StrongLeftOverlap", 
  mvars := 
    [ 
      [ [ 1 .. 3 ], [ 1 .. 3 ], [ 1 .. 3 ], [ 1 .. 3 ], [ 1 .. 3 ], 
          [ 1 .. 3 ], [ 1 .. 3 ], [ 1 .. 3 ] ], 
      [ [  ], [  ], [  ], [ 2 ], [ 1 ], [ 1 ], [  ], [ 2 ] ] ], 
  polys := [ [ [ [ 3, 2, 3 ], [ 2, 2, 2 ] ], [ 1, -1 ] ], 
      [ [ [ 1, 2, 3 ], [ 2, 2 ] ], [ 1, -2 ] ], 
      [ [ [ 3, 3 ], [ 2, 2 ] ], [ 1, -1 ] ], 
      [ [ [ 3, 2 ], [ 2, 3 ] ], [ 1, -1 ] ], 
      [ [ [ 3, 1 ], [ 2 ] ], [ 1, -2 ] ], [ [ [ 2, 1 ], [ 3 ] ], [ 1, -2 ] ], 
      [ [ [ 1, 3 ], [ 2 ] ], [ 1, -2 ] ], [ [ [ 1, 2 ], [ 3 ] ], [ 1, -2 ] ] 
     ] )
gap> PrintNPList( sbasP.polys );
 cbc - b^3 
 abc - 2b^2 
 c^2 - b^2 
 cb - bc 
 ca - 2b 
 ba - 2c 
 ac - 2b 
 ab - 2c 

gap> ## Section 6.3.2
gap> NoncommutativeDivision := "RightOverlap";;
gap> rbasP := InvolutiveBasisNP( A3, P4, ord );
rec( div := "RightOverlap", 
  mvars := [ [ [ 2 ], [ 2 ], [ 2 ], [ 2 ], [ 1 ], [ 1 ] ], 
      [ [ 1 .. 3 ], [ 1 .. 3 ], [ 1 .. 3 ], [ 1 .. 3 ], [ 1 .. 3 ], 
          [ 1 .. 3 ] ] ], 
  polys := [ [ [ [ 3, 3 ], [ 2, 2 ] ], [ 1, -1 ] ], 
      [ [ [ 3, 2 ], [ 2, 3 ] ], [ 1, -1 ] ], 
      [ [ [ 3, 1 ], [ 2 ] ], [ 1, -2 ] ], [ [ [ 2, 1 ], [ 3 ] ], [ 1, -2 ] ], 
      [ [ [ 1, 3 ], [ 2 ] ], [ 1, -2 ] ], [ [ [ 1, 2 ], [ 3 ] ], [ 1, -2 ] ] 
     ] )
gap> NoncommutativeDivision := "StrongRightOverlap";;
gap> srbasP := InvolutiveBasisNP( A3, P4, ord );;
gap> ( rbasP.polys = srbasP.polys ) and ( rbasP.mvars = srbasP.mvars );
true

gap> SetInfoLevel( InfoIBNP, ibnp_infolevel_saved );; 
gap> STOP_TEST( "involutive-np.tst", 10000 );

#############################################################################
##
#E  involutive-np.tst . . . . . . . . . . . . . . . . . . . . . . . ends here