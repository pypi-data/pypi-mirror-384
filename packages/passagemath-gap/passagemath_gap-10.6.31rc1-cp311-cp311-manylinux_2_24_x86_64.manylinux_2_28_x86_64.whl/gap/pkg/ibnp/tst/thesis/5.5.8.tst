#############################################################################
##
#W  5.5.8.tst         GAP4 package IBNP          Gareth Evans & Chris Wensley
##
##  Copyright (C) 2024: please refer to the COPYRIGHT file for details.
##  
gap> START_TEST( "5.5.8.tst" );
gap> ibnp_infolevel_saved := InfoLevel( InfoIBNP );; 
gap> SetInfoLevel( InfoIBNP, 0 );; 

gap> ## this implements Example 5.5.8 in the thesis,
gap> ## where  x -> b  and  y -> a

gap> A2 := AlgebraIBNP;;
gap> ord := NCMonomialLeftLengthLexicographicOrdering( A2 );;
gap> NoncommutativeDivision := "LeftOverlap";;
gap> u := [ [ [1,2], [1,1], [ ] ], [2,1,5] ];;
gap> v := [ [ [1,1], [2,2], [ ] ], [1,1,8] ];;
gap> PrintNPList( [u,v] );
 2ab + a^2 + 5 
 a^2 + b^2 + 8 
gap> grob := SGrobner( [u,v] );
[ [ [ [ 1, 2 ], [ 1, 1 ], [  ] ], [ 1, 1/2, 5/2 ] ], 
  [ [ [ 2, 1 ], [ 1, 1 ], [  ] ], [ 1, 1/2, 5/2 ] ], 
  [ [ [ 2, 2 ], [ 1, 1 ], [  ] ], [ 1, 1, 8 ] ], 
  [ [ [ 1, 1, 1 ], [ 2 ], [ 1 ] ], [ 1, -2, 37/5 ] ] ]
gap> PrintNPList( grob );      
 ab + 1/2a^2 + 5/2 
 ba + 1/2a^2 + 5/2 
 b^2 + a^2 + 8 
 a^3 - 2b + 37/5a 
gap> ibas := InvolutiveBasisNP( A2, [u,v], ord );
rec( div := "LeftOverlap", 
  mvars := [ [ [ 1, 2 ], [ 1, 2 ], [ 1, 2 ], [ 1, 2 ], [ 1, 2 ] ], 
      [ [  ], [  ], [  ], [  ], [  ] ] ], 
  polys := [ [ [ [ 2, 1, 1 ], [ 2 ], [ 1 ] ], [ 1, 1, -6/5 ] ], 
      [ [ [ 1, 1, 1 ], [ 2 ], [ 1 ] ], [ -5/2, 5, -37/2 ] ], 
      [ [ [ 2, 2 ], [ 1, 1 ], [  ] ], [ 1, 1, 8 ] ], 
      [ [ [ 2, 1 ], [ 1, 1 ], [  ] ], [ 5, 5/2, 25/2 ] ], 
      [ [ [ 1, 2 ], [ 1, 1 ], [  ] ], [ 2, 1, 5 ] ] ] )
gap> PrintNPList( ibas.polys );                  
 ba^2 + b - 6/5a 
 - 5/2a^3 + 5b - 37/2a 
 b^2 + a^2 + 8 
 5ba + 5/2a^2 + 25/2 
 2ab + a^2 + 5 

gap> SetInfoLevel( InfoIBNP, ibnp_infolevel_saved );; 
gap> STOP_TEST( "5.5.8.tst", 10000 );

############################################################################
##
#E  5.5.8.tst . . . . . . . . . . . . . . . . . . . . . . . . . . ends here
