#############################################################################
##
##  monom.gi         GAP package IBNP            Gareth Evans & Chris Wensley
##  

#############################################################################
##
#M  PrintNM( <mon> )
##
InstallMethod( PrintNM, "generic method for a noncommutative monomial",
    true, [ IsList ], 0,
function( mon )
## Overview: Prints a monomial as a word
## Detail: this just calls a GBNP operation
## 
    if ( mon= [ ] ) then 
        Print( 1 );
    else
        Print( GBNP.TransWord( mon ) );
    fi;
end );

InstallMethod( PrintNMList, "generic method for a list of monomials",
    true, [ IsList ], 0,
function( L )
## Overview: Prints a list of monomials as a list of words
##
    local mon;
    if not ForAll( L, m -> IsList(m) ) then 
        Error( "expecting a list of monomials" );
    fi;
    for mon in L do
        PrintNM( mon );
        Print( "\n" );
    od;
end );

#############################################################################
##
#M  NM2GM( <list> <alg> )
##
InstallMethod( NM2GM, "generic method for a noncommutative monomial",
    true, [ IsList, IsAlgebra ], 0,
function( mon, A )
## Overview: Converts a monomial from NM format
## 
    return NP2GP( [ [ mon ], [ 1 ] ], A );
end );

InstallMethod( GM2NM, "generic method for a noncommutative monomial",
    true, [ IsAssociativeElement ], 0,
function( mon )
## Overview: Converts a monomial to NM format
## 
    return GP2NP( mon )[1][1];
end );

InstallMethod( NM2GMList, "for a list of noncommutative monomials",
    true, [ IsList, IsAlgebra ], 0,
function( L, A )
## Overview: Converts a list of monomial from NM format
## 
    return List( L, m -> NP2GP( [ [ m ], [ 1 ] ], A ) );
end );

InstallMethod( GM2NMList, "for a list of noncommutative monomials",
    true, [ IsList ], 0,
function( L )
## Overview: Converts a monomial to NM format
## 
    return List( L, m -> GP2NP( m )[1][1] );
end );

#############################################################################
##
#M  SuffixNM( <pol> <int> )
#M  SubwordNM( <pol> <int> <int> )
#M  PrefixNM( <pol> <int> )
##
InstallMethod( SuffixNM, "generic method for a monomial and a length",
    true, [ IsList, IsInt ], 0,
function( mon, i )
    local len, j;
    if ( i=0 ) then 
        return [ ];
    elif ( i < 0 ) then 
        return fail; 
    fi;
    len := Length( mon ); 
    j := Minimum( i, len ); 
    return mon{[len-j+1..len]}; 
end );

InstallMethod( SubwordNM, "generic method for monomial, start and finish",
    true, [ IsList, IsPosInt, IsPosInt ], 0,
function( mon, s, f )
    local len, i, j;
    if ( s > f ) then
        Error( "start cannot be greater than finish" ); 
    fi;
    len := Length( mon );
    i := Minimum( s, len );
    j := Minimum( f, len );
    return mon{[i..j]}; 
end );

InstallMethod( PrefixNM, "generic method for a monomial and a length",
    true, [ IsList, IsInt ], 0,
function( mon, i )
    local len, j;
    if ( i=0 ) then 
        return [ ];
    elif ( i<0 ) then 
        return fail;
    fi;
    len := Length( mon ); 
    j := Minimum( i, len ); 
    return mon{[1..j]}; 
end );

#############################################################################
##
#M  SubwordPosNM( <mon>, <mon>, <posint>, <posint> )
#M  IsSubwordNM( <mon>, <mon> )
#M  SuffixPrefixPosNM( <mon>, <mon>, <posint>, <posint> )
##
InstallMethod( SubwordPosNM, 
    "generic method for 2 monomials and a start position",
    true, [ IsList, IsList, IsPosInt ], 0,
function( small, large, start )

    ## Overview: Is the 1st arg a subword of the 2nd arg? 
    ## if so, return start pos in 2nd arg 
    ## Detail: Answers the question "Is small a subword of large?"
    ## The function returns i if small is a subword of large, 
    ## where i is the position in large of the first subword found,
    ## and returns 0 if no overlap exists. 
    ## We start looking for subwords starting at position start in large 
    ## and finish looking for subwords when all possibilities have been 
    ## exhausted (we work left-to-right). 
    ## To test all possibilities the 3rd argument should be 1, 
    ## but note that you should use the function (IsSubword) 
    ## if you only want to know if a monomial is a subword of another 
    ## monomial and are not fussed where the overlap takes place.

    local i, slen, llen; 
    i := start; 
    slen := Length( small ); 
    llen := Length( large );
    ## while there are more subwords to test for
    while ( i <= llen-slen+1 ) do 
        ## if small is equal to a subword of large
        if ( small = large{[i..i+slen-1]} ) then 
            return i;   ## subword found
        fi; 
        i := i+1; 
    od; 
    return 0;   ## no subwords found
end ); 

InstallMethod( IsSubwordNM, 
    "generic method for 2 monomials",
    true, [ IsList, IsList ], 0,
function( small, large )

    ## Overview: Does small appear as a subword in large? 
    local i, lens, lenl; 
    lens := Length( small ); 
    lenl := Length( large );
    for i in [1..lenl-lens+1] do 
        if ( small = large{[i..i+lens-1]} ) then 
            return true;   ## overlap found
        fi; 
    od;
    return false;   ## no overlap found
end ); 

InstallMethod( SuffixPrefixPosNM, 
    "generic method for 2 monomials and a start position",
    true, [ IsList, IsList, IsPosInt, IsInt ], 0,
function( left, right, start, limit )

    ## Overview: Returns size of smallest overlap of type 
    ## (suffix of 1st arg = prefix of 2nd arg) 
    ## Detail: Answers the question "Is a suffix of left a prefix of right?"
    ## The function returns i if a suffix of left equals a prefix of right,
    ## where i is the length of the smallest overlap, 
    ## and returns 0 if no overlap exists.
    ## The lengths of the overlaps looked at are controlled by the 
    ## 3rd and 4th arguments - start by looking at the overlap of size 
    ## start and finish by looking at the overlap of size limit. 
    ## It is the user's responsibility to ensure that these bounds are 
    ## correct - no checks are made by the function.
    ## To test all possibilities, the 3rd argument should be 1 
    ## and the fourth argument should be min( |left|, |right| ) - 1.

    local i;
    i := start; 
    while ( i <= limit ) do   ## for each overlap
        if ( SuffixNM( left, i ) = PrefixNM( right, i ) ) then 
            return i;   ## prefix found
        fi; 
        i := i+1; 
    od;
    return 0;   ## no prefixes found 
end );

#############################################################################
##
#M  LeadVarNM( <mon> )
#M  LeadExpNM( <mon> )
#M  TailNM( <mon> )
##
InstallMethod( LeadVarNM, "generic method for a monomial",
    true, [ IsList ], 0,
function( mon )
    if ( mon = [ ] ) then 
        Error( "empty monomial" ); 
    fi;
    return mon[1];
end );

InstallMethod( LeadExpNM, "generic method for a monomial",
    true, [ IsList ], 0,
function( mon )
    local x, done, len, j, count;
    x := LeadVarNM( mon );
    done := false;
    len := Length( mon ); 
    j := 1;
    count := 1;
    while ( j < len ) and ( not done ) do 
        j := j+1; 
        if ( mon[j] = x ) then 
            count := count + 1;
        else
            done := true;
        fi;
    od; 
    return count;
end );

InstallMethod( TailNM, "generic method for a monomial",
    true, [ IsList ], 0,
function( mon )
    return mon{ [LeadExpNM(mon)+1..Length(mon)] };
end );

############################################################################
##
#M DivNM( <mon> <mon> )
## 
## Overview: Returns all possible ways that 2nd arg divides 1st arg;
##           3rd arg = is division possible?
## Detail: Given two NMs _m_ and _d_, this function returns all possible
## ways that _d_ divides _m_ in the form of an FMonPairList. 
## For example, if m = abcababc and d = ab, then the output FMonPairList 
## is ((abcab, c), (abc, abc), (1, cababc))..
## External variables needed: int pl;

InstallMethod( DivNM, "for two monomials", true, [ IsList, IsList ], 0,
function( m, d )
    local i, lenm, lend, diff, resm, resp, pair;
    resm := [ ];  ## initialise the output list
    lenm := Length( m );
    lend := Length( d );
    if ( lenm < lend ) then   ## no possible divisions if |m| < |d|
        return [ ];
    fi;
    ## we must now consider each possibility in turn
    diff := lenm - lend;
    for i in Reversed( [1..diff+1] ) do  ## working right to left
        ## is the subword of m of length |d| starting at i equal to d?
        if ( d = m{[i..i+lend-1]} ) then
            ## match found; push the left/right factors onto the output list
            pair := [ PrefixNM( m, i-1 ), 
                      SuffixNM( m, lenm-lend-i+1 ) ];
            Add( resm, pair );
            if ( InfoLevel( InfoIBNP ) > 2 ) then 
                PrintNMList( pair );
            fi; 
        fi; 
    od;
    resp := List( resm, L -> [ L, [1,1] ] ); 
    return resm;
end);

#############################################################################
##
#E  monom.gi . . . . . . . . . . . . . . . . . . . . . . . . . . .  ends here
## 