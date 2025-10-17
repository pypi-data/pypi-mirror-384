#############################################################################
##
##  involutive.gd        GAP package IBNP        Gareth Evans & Chris Wensley
##  

#############################################################################
##
#O  ThomasDivision( <alg> <polys> <ord> )     ??? is ord needed here ???
#O  JanetDivision( <alg> <polys> <ord> )
#O  PommaretDivision( <alg> <polys> <ord> )
##
DeclareOperation( "ThomasDivision", 
    [ IsAlgebra, IsList, IsMonomialOrdering ] );
DeclareOperation( "JanetDivision", 
    [ IsAlgebra, IsList, IsMonomialOrdering ] );
DeclareOperation( "PommaretDivision", 
    [ IsAlgebra, IsList, IsMonomialOrdering ] );
DeclareOperation( "LeftDivision", 
    [ IsAlgebra, IsList, IsNoncommutativeMonomialOrdering ] );
DeclareOperation( "RightDivision", 
    [ IsAlgebra, IsList, IsNoncommutativeMonomialOrdering ] );
DeclareOperation( "LeftOverlapDivision", 
    [ IsAlgebra, IsList, IsNoncommutativeMonomialOrdering ] );
DeclareOperation( "RightOverlapDivision", 
    [ IsAlgebra, IsList, IsNoncommutativeMonomialOrdering ] );
DeclareOperation( "StrongLeftOverlapDivision", 
    [ IsAlgebra, IsList, IsNoncommutativeMonomialOrdering ] );
DeclareOperation( "StrongRightOverlapDivision", 
    [ IsAlgebra, IsList, IsNoncommutativeMonomialOrdering ] );

#############################################################################
##
#F  DivisionRecord( <args> )
#O  DivisionRecordCP( <alg> <polys> <ord> )
#O  DivisionRecordNP( <alg> <polys> <ord> )
#P  IsDivisionRecord( <rec> )
##
DeclareGlobalName( "DivisionRecord" );
DeclareOperation( "DivisionRecordCP", 
    [ IsAlgebra, IsList, IsMonomialOrdering ] );
DeclareOperation( "DivisionRecordNP", 
    [ IsAlgebra, IsList, IsNoncommutativeMonomialOrdering ] );
DeclareProperty( "IsDivisionRecord", IsRecord );

#############################################################################
##
#F  IPolyReduce( <args> )
#O  IPolyReduceCP( <alg> <poly> <orec> <ord> )
#O  IPolyReduceNP( <alg> <poly> <orec> <ord> )
#F  LoggedIPolyReduce( <args> )
#O  LoggedIPolyReduceCP( <alg> <poly> <orec> <ord> )
#O  LoggedIPolyReduceNP( <alg> <poly> <orec> <ord> )
#O  CombinedIPolyReduceCP( <alg> <poly> <orec> <ord> <logging> )
#O  CombinedIPolyReduceNP( <alg> <poly> <orec> <ord> <logging> )
##
DeclareGlobalName( "IPolyReduce" );
DeclareOperation( "IPolyReduceCP", 
    [ IsPolynomialRing, IsPolynomial,IsRecord, IsMonomialOrdering ] );
DeclareOperation( "IPolyReduceNP",
    [ IsAlgebra, IsObject, IsRecord, IsNoncommutativeMonomialOrdering ] );
DeclareGlobalName( "LoggedIPolyReduce" );
DeclareOperation( "LoggedIPolyReduceCP", 
    [ IsPolynomialRing, IsPolynomial, IsRecord, IsMonomialOrdering ] );
DeclareOperation( "LoggedIPolyReduceNP",
    [ IsAlgebra, IsObject, IsRecord, IsNoncommutativeMonomialOrdering ] );
DeclareOperation( "CombinedIPolyReduceCP", 
    [ IsPolynomialRing, IsPolynomial, IsRecord, 
      IsMonomialOrdering, IsBool ] );
DeclareOperation( "CombinedIPolyReduceNP",
    [ IsAlgebra, IsObject, IsRecord, 
      IsNoncommutativeMonomialOrdering, IsBool ] );
DeclareOperation( "VerifyLoggedRecordNP",
    [ IsList, IsRecord ] );

#############################################################################
##
#F  IAutoreduce( <args> )
#O  IAutoreduceCP( <alg> <polys> <ord> )
#O  IAutoreduceNP( <alg> <polys> <ord> )
##
DeclareGlobalName( "IAutoreduce" );
DeclareOperation( "IAutoreduceCP", 
    [ IsAlgebra, IsList, IsMonomialOrdering ] );
DeclareOperation( "IAutoreduceNP", 
    [ IsAlgebra, IsList, IsNoncommutativeMonomialOrdering ] );

#############################################################################
##
#F  InvolutiveBasis( <args> )
#O  InvolutiveBasisCP( <alg> <list> <ord> )
#O  InvolutiveBasisNP( <alg> <list> <ord> )
##
DeclareGlobalName( "InvolutiveBasis" );
DeclareOperation( "InvolutiveBasisCP", 
    [ IsAlgebra, IsList, IsMonomialOrdering ] ); 
DeclareOperation( "InvolutiveBasisNP", 
    [ IsAlgebra, IsList, IsNoncommutativeMonomialOrdering ] ); 

#############################################################################
##
#E  involutive.gd . . . . . . . . . . . . . . . . . . . . . . . .  ends here
##  