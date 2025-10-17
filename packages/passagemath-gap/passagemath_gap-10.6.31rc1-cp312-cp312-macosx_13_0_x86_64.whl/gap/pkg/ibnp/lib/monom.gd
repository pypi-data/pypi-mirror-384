#############################################################################
##
##  monom.gd         GAP package IBNP            Gareth Evans & Chris Wensley
##  

#############################################################################
##
#O  PrintNM( <mon> )
#O  PrintNMList( <list> )
##
DeclareOperation( "PrintNM", [ IsList ] );
DeclareOperation( "PrintNMList", [ IsList ] );

#############################################################################
##
#O  NM2GM( <list> <alg> )
#O  GM2NM( <list> )
#O  NM2GMList( <list> )
#O  GM2NMList( <list> )
##
DeclareOperation( "NM2GM", [ IsList, IsAlgebra ] );
DeclareOperation( "GM2NM", [ IsAssociativeElement ] );
DeclareOperation( "NM2GMList", [ IsList, IsAlgebra ] );
DeclareOperation( "GM2NMList", [ IsList ] );

#############################################################################
##
#O  SuffixNM( <mon>, <posint> )
#O  SubwordNM( <mon>, <posint>, <posint> )
#O  PrefixNM( <mon>, <posint> );
##
DeclareOperation( "SuffixNM", [ IsList, IsInt ] );
DeclareOperation( "SubwordNM", [ IsList, IsPosInt, IsPosInt ] );
DeclareOperation( "PrefixNM", [ IsList, IsInt ] );

#############################################################################
##
#O  SubwordPosNM( <mon>, <mon>, <posint> )
#O  IsSubwordNM( <mon>, <mon> )
#O  SuffixPrefixPosNM( <mon>, <mon>, <posint>, <posint> )
##
DeclareOperation( "SubwordPosNM", [ IsList, IsList, IsPosInt ] );
DeclareOperation( "IsSubwordNM", [ IsList, IsList ] );
DeclareOperation( "SuffixPrefixPosNM", [ IsList, IsList, IsPosInt, IsInt ] );

#############################################################################
##
#O  LeadVarNM( <list> )
#O  LeadExpNM( <list> )
#O  TailNM( <list> )
##
DeclareOperation( "LeadVarNM", [ IsList ] );
DeclareOperation( "LeadExpNM", [ IsList ] );
DeclareOperation( "TailNM", [ IsList ] );

#############################################################################
##
#O  DivNM( <mon> <mon> )
#O  DivFirstNM( <mon> <mon> ) - for now just take DivNM(x,y)[1]
##
DeclareOperation( "DivNM", [ IsList, IsList ] ); 

#############################################################################
##
#E  monom.gd . . . . . . . . . . . . . . . . . . . . . . . . . . .  ends here
##  