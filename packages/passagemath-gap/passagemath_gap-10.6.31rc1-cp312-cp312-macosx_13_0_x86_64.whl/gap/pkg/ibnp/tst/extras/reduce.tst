#############################################################################
##
#W  reduce.tst           GAP4 package IBNP       Gareth Evans & Chris Wensley
##

gap> START_TEST( "reduce.tst" );
gap> ibnp_infolevel_saved := InfoLevel( InfoIBNP );; 
gap> SetInfoLevel( InfoIBNP, 0 );; 

gap> A3 := Algebra3IBNP;;
gap> a:=A3.1;;  b:=A3.2;;  c:=A3.3;;
gap> ord := NCMonomialLeftLengthLexicographicOrdering( A3 );;

gap> NoncommutativeDivision := "RightOverlap";;

gap> L1 := [ 2*c^3 - 3*a*b, 2*b^3 - 3*c*a, 2*a^3 - 3*b*c ];
[ (-3)*a*b+(2)*c^3, (-3)*c*a+(2)*b^3, (-3)*b*c+(2)*a^3 ]
gap> L2 := List( L1, p -> GP2NP(p) );
[ [ [ [ 3, 3, 3 ], [ 1, 2 ] ], [ 2, -3 ] ], 
  [ [ [ 2, 2, 2 ], [ 3, 1 ] ], [ 2, -3 ] ], 
  [ [ [ 1, 1, 1 ], [ 2, 3 ] ], [ 2, -3 ] ] ]
gap> PrintNPList( L2 );
 2c^3 - 3ab 
 2b^3 - 3ca 
 2a^3 - 3bc 

gap> drec := DivisionRecord( A3, L2, ord );
rec( div := "RightOverlap", 
  mvars := [ [ [ 1, 2 ], [ 1, 3 ], [ 2, 3 ] ], 
      [ [ 1 .. 3 ], [ 1 .. 3 ], [ 1 .. 3 ] ] ], 
  polys := [ [ [ [ 3, 3, 3 ], [ 1, 2 ] ], [ 2, -3 ] ], 
      [ [ [ 2, 2, 2 ], [ 3, 1 ] ], [ 2, -3 ] ], 
      [ [ [ 1, 1, 1 ], [ 2, 3 ] ], [ 2, -3 ] ] ] )

gap> p1 := 4*c^2*a^2*c^4*a^2*b^2 + 8*b^5*a^4 + 12*a^4*b^2*c^2;
(12)*a^4*b^2*c^2+(8)*b^5*a^4+(4)*c^2*a^2*c^4*a^2*b^2
gap> p2 := CleanNP( GP2NP(p1) );
[ [ [ 3, 3, 1, 1, 3, 3, 3, 3, 1, 1, 2, 2 ], [ 2, 2, 2, 2, 2, 1, 1, 1\
, 1 ], 
      [ 1, 1, 1, 1, 2, 2, 3, 3 ] ], [ 4, 8, 12 ] ]

gap> q2 := LoggedIPolyReduceNP( A3, p2, drec, ord );
rec( 
  logs := [ [ [ 2, [ 3, 3, 1, 1 ], [ 3, 1, 1, 2, 2 ] ] ], 
      [ [ 4, [  ], [ 2, 2, 1, 1, 1, 1 ] ], [ 9, [ 3, 1 ], [ 3, 1 ] ] ], 
      [ [ 3, [ 3, 3 ], [ 2, 3, 1, 1, 2, 2 ] ], [ 6, [ 3, 1, 2, 2 ], [ 1 ] ], 
          [ 6, [  ], [ 1, 2, 2, 3, 3 ] ] ] ], 
  polys := [ [ [ [ 3, 3, 3 ], [ 1, 2 ] ], [ 2, -3 ] ], 
      [ [ [ 2, 2, 2 ], [ 3, 1 ] ], [ 2, -3 ] ], 
      [ [ [ 1, 1, 1 ], [ 2, 3 ] ], [ 2, -3 ] ] ], 
  result := 
    [ 
      [ [ 3, 3, 2, 3, 2, 3, 1, 1, 2, 2 ], [ 2, 3, 1, 2, 2, 3, 3 ], 
          [ 3, 1, 3, 1, 3, 1 ] ], [ 9, 18, 27 ] ] )
gap> r2 := q2.result;;
gap> PrintNP( r2 );            
 9c^2bcbca^2b^2 + 18bcab^2c^2 + 27cacaca 

gap> ## check the logging information
gap> log1 := q2.logs[1];;
gap> pol1 := q2.polys[1];;
gap> add1 := [ ];;
gap> for i in [1..Length(log1)] do
>        Li := log1[i];;
>        if ( Li[2] <> [ ] ) then
>            p := MulNP( [ [ Li[2] ], [1] ], pol1 );
>        else
>            p := pol1;
>        fi;
>        if ( Li[3] <> [ ] ) then
>            p := MulNP( p, [ [ Li[3] ], [1] ] );
>        fi;
>        Add( add1, [ p[1], Li[1]*p[2] ] );
>    od;
gap> PrintNPList( add1 );
 4c^2a^2c^4a^2b^2 - 6c^2a^3bca^2b^2 
gap> log2 := q2.logs[2];;
gap> pol2 := q2.polys[2];;
gap> add2 := [ ];;
gap> for i in [1..Length(log2)] do
>        Li := log2[i];;
>        if ( Li[2] <> [ ] ) then
>            p := MulNP( [ [ Li[2] ], [1] ], pol2 );
>        else
>            p := pol2;
>        fi;
>        if ( Li[3] <> [ ] ) then
>            p := MulNP( p, [ [ Li[3] ], [1] ] );
>        fi;
>        Add( add2, [ p[1], Li[1]*p[2] ] );
>    od;
gap> PrintNPList( add2 );
 8b^5a^4 - 12cab^2a^4 
 18cab^3ca - 27cacaca 
gap> log3 := q2.logs[3];;
gap> pol3 := q2.polys[3];;
gap> add3 := [ ];;
gap> for i in [1..Length(log3)] do
>        Li := log3[i];;
>        if ( Li[2] <> [ ] ) then
>            p := MulNP( [ [ Li[2] ], [1] ], pol3 );
>        else
>            p := pol3;
>        fi;
>        if ( Li[3] <> [ ] ) then
>            p := MulNP( p, [ [ Li[3] ], [1] ] );
>        fi;
>        Add( add3, [ p[1], Li[1]*p[2] ] );
>    od;
gap> PrintNPList( add3 );
 6c^2a^3bca^2b^2 - 9c^2bcbca^2b^2 
 12cab^2a^4 - 18cab^3ca 
 12a^4b^2c^2 - 18bcab^2c^2 
gap> ## these 6 terms have been added to the original p2 to make r2
gap> ## so subtract them from the result r2 to get back to p2
gap> r1 := AddNP( r2, add1[1], 1, 1 );;
gap> r1 := AddNP( r1, add2[1], 1, 1 );;
gap> r1 := AddNP( r1, add2[2], 1, 1 );;
gap> r1 := AddNP( r1, add3[1], 1, 1 );;
gap> r1 := AddNP( r1, add3[2], 1, 1 );;
gap> r1 := AddNP( r1, add3[3], 1, 1 );;
gap> PrintNP( r1 );
 4c^2a^2c^4a^2b^2 + 8b^5a^4 + 12a^4b^2c^2 
gap> r1 = p2;
true

gap> ## the above calculation can be done more simply by:
gap> VerifyLoggedRecordNP( p2, q2 );
true

gap> SetInfoLevel( InfoIBNP, ibnp_infolevel_saved );; 
gap> STOP_TEST( "reduce.tst", 10000 );

#############################################################################
##
#E  reduce.tst . . . . . . . . . . . . . . . . . . . . . . . . . . ends here
