#############################################################################
##
##  poly.gi.         GAP package IBNP            Gareth Evans & Chris Wensley
##  

############################################################################
##
#M  IsZeroNP( <poly> )
## 
##  Overview: tests a polynomial to see if it is zero
##
InstallMethod( IsZeroNP, "for a polynomial", true, [ IsList ], 0,
function( pol )
    return ( pol = [ ] ) or ( pol = [ [ ], [ ] ] )
                         or ( pol = [ [ [] ], [ 0 ] ] );
end ); 

############################################################################
##
#M  MaxDegreeNP( <polys> )
## 
##  Overview: Returns maximal degree of lead term for the given FAlgList
##  Detail: Given an FAlgList, this function calculates the degree
##  of the lead term for each element of the list and returns
##  the largest value found.
##
InstallMethod( MaxDegreeNP, "for a list of polynomials in NP format", 
    true, [ IsList ], 0,
function( polys )
    local pol, test, output; 
    output := 0; 
    for pol in polys do 
        ## calculate the degree of the lead monomial
        test := Length( pol[1][1] ); 
        if ( test > output ) then 
            output := test;
        fi;
    od;
    ## return the maximal value
    return output;
end ); 

############################################################################
##
#M  ScalarMulNP( <poly> <const> )
## 
##  Detail: multiplies the polynomial by the constant.
##
InstallMethod( ScalarMulNP, "for a polynomial and a constant", true, 
    [ IsList, IsScalar ], 0,
function( pol, c )
    return [ pol[1], c*pol[2] ];
end ); 

############################################################################
##
#M  LtNPoly( <poly> )
#M  GtNPoly( <poly> )
## 
##  Overview: compares a pair of clean polynomials in NP format
##
InstallMethod( LtNPoly, "for two polynomials", true, [ IsList, IsList ], 0,
function( p, q )
    local lenp, lenq, len, i;
    lenp := Length( p[1] );
    lenq := Length( q[1] );
    len := Minimum( lenp, lenq ); 
    i := 0;
    while ( i < len ) do
        i := i+1;
        if LtNP( p[1][i], q[1][i] ) then
            return true;
        elif GtNP( p[1][i], q[1][i] ) then
            return false;
        fi;
    od;
    if ( lenp > lenq ) then
        return true;
    elif ( lenp < lenq ) then
        return false;
    fi;
    ## if here then p and q contain the same monomials
    i := 0;
    while ( i < len ) do
        i := i+1;
        if ( p[2][i] < q[2][i] ) then
            return true;
        elif ( p[2][i] > q[2][i] ) then
            return false;
        fi;
    od;
    return false;
end ); 

InstallMethod( GtNPoly, "for two polynomials", true, [ IsList, IsList ], 0,
function( p, q )
    local lenp, lenq, len, i;
    lenp := Length( p[1] );
    lenq := Length( q[1] );
    len := Minimum( lenp, lenq ); 
    i := 0;
    while ( i < len ) do
        i := i+1;
        if GtNP( p[1][i], q[1][i] ) then
            return true;
        elif LtNP( p[1][i], q[1][i] ) then
            return false;
        fi;
    od;
    if ( lenp > lenq ) then
        return true;
    elif ( lenp < lenq ) then
        return false;
    fi;
    ## if here then p and q contain the same monomials
    i := 0;
    while ( i < len ) do
        i := i+1;
        if ( p[2][i] > q[2][i] ) then
            return true;
        elif ( p[2][i] < q[2][i] ) then
            return false;
        fi;
    od;
    return false;
end ); 

############################################################################
##
#M  LeastLeadMonomialPosNP( <polys> )
## 
##  Overview: Returns the position of the smallest LM(g) in the given list
##  Detail: Given a list of polys, this function looks at all the leading
##  monomials of the polys in the list and returns the position of
##  the smallest lead monomial with respect to the monomial ordering
##  currently being used.
##
InstallMethod( LeastLeadMonomialPosNP, "for a list of polynomials", true, 
    [ IsList ], 0,
function( polys )
    local len, pol, lowest, output, i; 
    len := Length( polys );
    if ( len = 0 ) then
        return fail;
    fi;
    output := 1; 
    lowest := polys[1];
    i := 1;
    while ( i < len ) do
        i := i+1;
        pol := polys[i]; 
        if LtNPoly( pol, lowest ) then
            output := i; 
            lowest := pol; 
        fi; 
    od; 
    ## return position of smallest lead monomial
    return output;
end ); 

#############################################################################
##
#E  poly.gi . . . . . . . . . . . . . . . . . . . . . . . . . . .  ends here
## 