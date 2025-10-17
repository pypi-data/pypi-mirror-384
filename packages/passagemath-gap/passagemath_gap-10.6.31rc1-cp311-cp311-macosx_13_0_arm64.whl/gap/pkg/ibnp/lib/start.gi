#############################################################################
##
##  start.gi         GAP package IBNP            Gareth Evans & Chris Wensley
##  

#############################################################################
##
#V  InfoIBNP
##
DeclareInfoClass( "InfoIBNP" );
SetInfoLevel( InfoIBNP, 1 );

#############################################################################
##
##  declare default algebras Algebra2 and Algebra3
##
Algebra2IBNP := FreeAssociativeAlgebraWithOne(Rationals,"a","b"); 
Algebra3IBNP := FreeAssociativeAlgebraWithOne(Rationals,"a","b","c"); 
Algebra4IBNP := FreeAssociativeAlgebraWithOne(Rationals,"a","A","b","B"); 
AlgebraIBNP := Algebra2IBNP;

#############################################################################
##
##  declare various parameters
##
ZeroNP := [ [ [] ], [0] ];   ## NP form of the zero polynomial
InvolutiveAbortLimit := 20;  ## abort when generating an infinite basis 

#############################################################################
##
#M  DisplayIBNP( <polys>, <pl> )
## 
##  displays a list of polynomials according to print level
##
InstallMethod( DisplayIBNP, "displays list of polynomials by print level",
    true, [ IsList, IsInt ], 0,
function( polys, pl ) 
    local i, pol, Lpol;
    for i in [1..Length(polys)] do 
        pol := polys[i]; 
        Lpol := GP2NP( pol ); 
        ## if pl=1, display the polynomial using the original generators
        if( pl = 1 ) then 
            PrintNP( Lpol );
        ## else  display the polynomial using ASCII generators
        elif ( pl = 2 ) then  
            Print( Lpol, "\n" ); 
        else 
            Error( "pl not in [1,2]" );  
        fi; 
    od; 
end );

#############################################################################
##
#M  declare default divisions
## 
CommutativeDivision := "Pommaret";
NoncommutativeDivision := "LeftOverlap";

#############################################################################
##
#E  start.gi . . . . . . . . . . . . . . . . . . . . . . . . . . . ends here
## 