#############################################################################
##
#W  5.5.9.tst         GAP4 package IBNP          Gareth Evans & Chris Wensley
##
##  Copyright (C) 2024: please refer to the COPYRIGHT file for details.
##  
gap> START_TEST( "5.5.9.tst" );
gap> ibnp_infolevel_saved := InfoLevel( InfoIBNP );; 
gap> SetInfoLevel( InfoIBNP, 0 );; 

gap> ## this implements Examples 5.5.9, 5.5.12 in the thesis,
gap> ## where  x -> c, y -> b  and  z -> a

gap> GBNP.ConfigPrint( "a", "b", "c" );
gap> NoncommutativeDivision := "LeftOverlap";;
gap> A3 := Algebra3IBNP;;
gap> ord := NCMonomialLeftLengthLexicographicOrdering( A3 );;
gap> r := [[ [3,2], [1] ], [1,-1] ];; 
gap> s := [[ [3], [1] ], [1,1] ];; 
gap> t := [[ [2,1], [1] ], [1,-1] ];;
gap> u := [[ [3,1] ], [1] ];; 
gap> v := [[ [1,2], [1] ], [1,1] ];;
gap> w := [[ [1,1] ], [1] ];;
gap> L6 := [ r, s, t, u, v, w ];; 
gap> PrintNPList( L6 );
cb - a 
c + a 
ba - a 
ca 
ab + a 
a^2 
gap> NoncommutativeDivision := "LeftOverlap";;
gap> drec6 := DivisionRecord( A3, L6, ord );
rec( div := "LeftOverlap", 
  mvars := 
    [ 
      [ [ 1 .. 3 ], [ 1 .. 3 ], [ 1 .. 3 ], [ 1 .. 3 ], [ 1 .. 3 ], [ 1 .. 3 ]\
 
         ], [ [ 2, 3 ], [ 3 ], [ 3 ], [ 3 ], [ 2, 3 ], [ 3 ] ] ], 
  polys := [ [ [ [ 3, 2 ], [ 1 ] ], [ 1, -1 ] ], 
      [ [ [ 3 ], [ 1 ] ], [ 1, 1 ] ], [ [ [ 2, 1 ], [ 1 ] ], [ 1, -1 ] ], 
      [ [ [ 3, 1 ] ], [ 1 ] ], [ [ [ 1, 2 ], [ 1 ] ], [ 1, 1 ] ], 
      [ [ [ 1, 1 ] ], [ 1 ] ] ] )
gap> ibas6 := InvolutiveBasis( A3, L6, ord );;
gap> PrintNPList( ibas6.polys );
 ba - a 
 ab + a 
 a^2 
 c + a 
gap> ## this test is aborted because it goes into an infinite loop
gap> NoncommutativeDivision := "Left";;
gap> SetInfoLevel( InfoIBNP, 1 );
gap> InvolutiveBasis( A3, L6, ord );
#I  adding [ [ [ 1, 2, 2 ], [ 1, 2 ] ], [ 1, 1 ] ] -> [ [ [ 1, 2, 2 ], [ 1 ] ], [ 1, -1 ] ]
#I  adding [ [ [ 3, 2, 2 ], [ 1, 2 ] ], [ 1, -1 ] ] -> [ [ [ 3, 2, 2 ], [ 1 ] ], [ 1, 1 ] ]
#I  adding [ [ [ 1, 2, 2, 2 ], [ 1, 2 ] ], [ 1, -1 ] ] -> [ [ [ 1, 2, 2, 2 ], [ 1 ] ], [ 1, 1 ] ]
#I  adding [ [ [ 3, 2, 2, 2 ], [ 1, 2 ] ], [ 1, 1 ] ] -> [ [ [ 3, 2, 2, 2 ], [ 1 ] ], [ 1, -1 ] ]
#I  adding [ [ [ 1, 2, 2, 2, 2 ], [ 1, 2 ] ], [ 1, 1 ] ] -> [ [ [ 1, 2, 2, 2, 2 ], [ 1 ] ], [ 1, -1 ] ]
#I  adding [ [ [ 3, 2, 2, 2, 2 ], [ 1, 2 ] ], [ 1, -1 ] ] -> [ [ [ 3, 2, 2, 2, 2 ], [ 1 ] ], [ 1, 1 ] ]
#I  adding [ [ [ 1, 2, 2, 2, 2, 2 ], [ 1, 2 ] ], [ 1, -1 ] ] -> [ [ [ 1, 2, 2, 2, 2, 2 ], [ 1 ] ], [ 1, 1 ] ]
#I  adding [ [ [ 3, 2, 2, 2, 2, 2 ], [ 1, 2 ] ], [ 1, 1 ] ] -> [ [ [ 3, 2, 2, 2, 2, 2 ], [ 1 ] ], [ 1, -1 ] ]
#I  adding [ [ [ 1, 2, 2, 2, 2, 2, 2 ], [ 1, 2 ] ], [ 1, 1 ] ] -> [ [ [ 1, 2, 2, 2, 2, 2, 2 ], [ 1 ] ], [ 1, -1 ] ]
#I  adding [ [ [ 3, 2, 2, 2, 2, 2, 2 ], [ 1, 2 ] ], [ 1, -1 ] ] -> [ [ [ 3, 2, 2, 2, 2, 2, 2 ], [ 1 ] ], [ 1, 1 ] ]
#I  adding [ [ [ 1, 2, 2, 2, 2, 2, 2, 2 ], [ 1, 2 ] ], [ 1, -1 ] ] -> [ [ [ 1, 2, 2, 2, 2, 2, 2, 2 ], [ 1 ] ], [ 1, 1 ] ]
#I  adding [ [ [ 3, 2, 2, 2, 2, 2, 2, 2 ], [ 1, 2 ] ], [ 1, 1 ] ] -> [ [ [ 3, 2, 2, 2, 2, 2, 2, 2 ], [ 1 ] ], [ 1, -1 ] ]
#I  adding [ [ [ 1, 2, 2, 2, 2, 2, 2, 2, 2 ], [ 1, 2 ] ], [ 1, 1 ] ] -> [ [ [ 1, 2, 2, 2, 2, 2, 2, 2, 2 ], [ 1 ] ], [ 1, -1 ] ]
#I  adding [ [ [ 3, 2, 2, 2, 2, 2, 2, 2, 2 ], [ 1, 2 ] ], [ 1, -1 ] ] -> [ [ [ 3, 2, 2, 2, 2, 2, 2, 2, 2 ], [ 1 ] ], [ 1, 1 ] ]
fail

gap> SetInfoLevel( InfoIBNP, ibnp_infolevel_saved );; 
gap> STOP_TEST( "5.5.9.tst", 10000 );

#############################################################################
##
#E  5.5.9.tst  . . . . . . . . . . . . . . . . . . . . . . . . . . ends here
