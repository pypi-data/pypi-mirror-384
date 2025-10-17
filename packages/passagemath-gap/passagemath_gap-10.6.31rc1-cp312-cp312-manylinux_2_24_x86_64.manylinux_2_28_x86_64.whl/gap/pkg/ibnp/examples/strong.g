#############################################################################
##
#W  strong.g          GAP4 package IBNP          Gareth Evans & Chris Wensley
##
  
LoadPackage( "ibnp" );

SetInfoLevel( InfoIBNP, 1 );; 

A3 := Algebra3IBNP;;
a:=A3.1;;  b:=A3.2;; c:=A3.3;;
ord := NCMonomialLeftLengthLexicographicOrdering( A3 );;

L3 := [ [ [ [3,3,3], [2] ], [1,-1] ],
        [ [ [1,1,1], [2] ], [1,-1] ], 
        [ [ [3,2], [2,3] ], [1,-1] ],
        [ [ [2,1], [1,2] ], [1,-1] ],
        [ [ [3,1], [1,3] ], [1,-1] ] ];
L3 := List( L3, p -> CleanNP(p) );
PrintNPList( L3 );

NoncommutativeDivision := "LeftOverlap";
drec := DivisionRecordNP( A3, L3, ord );
Print( "drec = ", drec, "\n" );

ibas := InvolutiveBasisNP( A3, L3, ord );
Print( "ibas = ", ibas, "\n\n" );
PrintNPList( ibas.polys );

NoncommutativeDivision := "RightOverlap";
rdrec := DivisionRecordNP( A3, L3, ord );
Print( "rdrec = ", rdrec, "\n" );

ribas := InvolutiveBasisNP( A3, L3, ord );
Print( "ribas = ", ribas, "\n\n" );
PrintNPList( ribas.polys );

mons := List( drec.polys, p -> p[1][1] );
Print( "\nmons = ", mons, "\n" );
vars := List( mons, m -> Set(m) );
Print( "vars = ", vars, "\n" );

rvars := drec.mvars[2];
Print( "rvars = ", rvars, "\n" ); 

NoncommutativeDivision := "StrongLeftOverlap";
srec := DivisionRecordNP( A3, L3, ord );
Print( "srec = ", srec, "\n" );

sbas := InvolutiveBasisNP( A3, L3, ord );
Print( "sbas = ", sbas, "\n\n" );
PrintNPList( sbas.polys );

NoncommutativeDivision := "StrongRightOverlap";
rsrec := DivisionRecordNP( A3, L3, ord );
Print( "rsrec = ", rsrec, "\n" );

rsbas := InvolutiveBasisNP( A3, L3, ord );
Print( "rsbas = ", rsbas, "\n\n" );
PrintNPList( rsbas.polys );
