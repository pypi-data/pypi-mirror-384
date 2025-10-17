#############################################################################
##
#W  reduce.g         GAP4 package IBNP          Gareth Evans & Chris Wensley
##
  
LoadPackage( "ibnp" );

SetInfoLevel( InfoIBNP, 2 );; 

A3 := Algebra3IBNP;;
a:=A3.1;;  b:=A3.2;;  c:=A3.3;;
ord := NCMonomialLeftLengthLexicographicOrdering( A3 );;

NoncommutativeDivision := "RightOverlap";
SetInfoLevel( InfoIBNP, 3 );

L1 := [ 2*c^3 - 3*a*b, 2*b^3 - 3*c*a, 2*a^3 - 3*b*c ];
L2 := List( L1, p -> GP2NP(p) );
Print( "L2 = ", L2, "\n" );
PrintNPList( L2 );

drec := DivisionRecord( A3, L2, ord );Print( "drec = ", drec, "\n" );

p1 := 4*c^2*a^2*c^4*a^2*b^2 + 8*b^5*a^4 + 12*a^4*b^2*c^2;
p2 := CleanNP( GP2NP(p1) );
Print( "p2 = ", p2, "\n", "p1 = ", p1, "\n" );

q2 := LoggedIPolyReduceNP( A3, p2, drec, ord );