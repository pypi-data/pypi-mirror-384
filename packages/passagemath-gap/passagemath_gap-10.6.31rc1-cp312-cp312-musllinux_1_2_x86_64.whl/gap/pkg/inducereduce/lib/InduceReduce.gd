#
# InduceReduce.gd        The InduceReduce package         Jonathan Gruber
#
# Declarations
#
# Copyright (C) 2018     Jonathan Gruber
#

#############################################################################
##
#A  UngerRecord( <G> )
##
DeclareAttribute( "UngerRecord", IsGroup, "mutable" );

#############################################################################
##
#A  IrrUnger( <G> )
#O  IrrUnger( <G>[, <Options>] )
##
DeclareAttribute( "IrrUnger", IsGroup );
DeclareOperation( "IrrUnger", [ IsGroup, IsRecord ] );

#############################################################################
##
#F CharacterTableUnger( <G> [, <Options>] )
##
## Computes the character table of a finite group using Unger's algorithm
##
DeclareGlobalFunction( "CharacterTableUnger" );

#############################################################################
##
#F InduceReduce( <GR> , <Opt> )
##
## computes the irreducible characters of the group GR.G (upto sign) and puts
## them in the component GR.Ir of GR, returns GR.Ir
##
DeclareGlobalFunction( "InduceReduce" );

#############################################################################
##
#V IndRed
##
## a record containing subfunctions of CharacterTableUnger and InduceReduce
##
DeclareGlobalVariable( "IndRed" );

#############################################################################
##
## The info class for computations with InduceReduce
##
DeclareInfoClass("InfoCTUnger");
