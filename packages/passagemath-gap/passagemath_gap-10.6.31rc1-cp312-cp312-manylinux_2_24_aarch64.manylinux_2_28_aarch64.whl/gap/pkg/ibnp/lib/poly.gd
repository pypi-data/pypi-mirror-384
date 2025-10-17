#############################################################################
##
##  poly.gd          GAP package IBNP            Gareth Evans & Chris Wensley
##  

#############################################################################
##
#O  IsZeroNP( <poly> )
##
DeclareOperation( "IsZeroNP", [ IsList ] );

#############################################################################
##
#O  MaxDegreeNP( <list> )
##
DeclareOperation( "MaxDegreeNP", [ IsList ] ); 

#############################################################################
##
#O  ScalarMulNP( <poly> <const> )
##
DeclareOperation( "ScalarMulNP", [ IsList, IsScalar ] ); 

#############################################################################
##
#O  LtNPoly( <list> )
#O  GtNPoly( <list> )
##
DeclareOperation( "LtNPoly", [ IsList, IsList ] ); 
DeclareOperation( "GtNPoly", [ IsList, IsList ] ); 

#############################################################################
##
#O  LeastLeadMonomialPosNP( <list> )
##
DeclareOperation( "LeastLeadMonomialPosNP", [ IsList ] ); 

#############################################################################
##
#E  poly.gd . . . . . . . . . . . . . . . . . . . . . . . . . . .  ends here
##  