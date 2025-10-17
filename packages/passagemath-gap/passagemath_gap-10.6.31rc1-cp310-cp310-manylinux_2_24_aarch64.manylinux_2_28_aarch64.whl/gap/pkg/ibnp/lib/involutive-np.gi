#############################################################################
##
##  involutive-np.gi     GAP package IBNP        Gareth Evans & Chris Wensley
##  

#############################################################################
##
#M  LeftDivision( <alg> <mons> <ord> )
##
InstallMethod( LeftDivision, "generic method for list of monomials",
    true, [ IsAlgebra, IsList, IsNoncommutativeMonomialOrdering ], 0,
function( A, mons, ord )

    local genA, ngens, nmons, lvars, rvars, i, emoni;
    genA := GeneratorsOfAlgebra( A );
    if not ( genA[1] = One(A) ) then 
        Error( "expecting genA[1] = One(A)" );
    fi;
    genA := genA{ [2..Length(genA)] };
    ngens := Length( genA );
    nmons := Length( mons );
    lvars := ListWithIdenticalEntries( nmons, 0 );
    rvars := ListWithIdenticalEntries( nmons, 0 );
    for i in [1..nmons] do   ## for each monnomial 
        lvars[i] := [1..ngens];
        rvars[i] := [ ];
    od;
    return [ lvars, rvars ];
end );


#############################################################################
##
#M  RightDivision( <alg> <mons> <ord> )
##
InstallMethod( RightDivision, "generic method for list of monomials",
    true, [ IsAlgebra, IsList, IsNoncommutativeMonomialOrdering ], 0,
function( A, mons, ord )

    local genA, ngens, nmons, lvars, rvars, i, emoni;
    genA := GeneratorsOfAlgebra( A );
    if not ( genA[1] = One(A) ) then 
        Error( "expecting genA[1] = One(A)" );
    fi;
    genA := genA{ [2..Length(genA)] };
    ngens := Length( genA );
    nmons := Length( mons );
    lvars := ListWithIdenticalEntries( nmons, 0 );
    rvars := ListWithIdenticalEntries( nmons, 0 );
    for i in [1..nmons] do   ## for each monnomial 
        lvars[i] := [ ];
        rvars[i] := [1..ngens];
    od;
    return [ lvars, rvars ];
end );

#############################################################################
##
#M  LeftOverlapDivision( <alg>, <mons> <ord> )
##
InstallMethod( LeftOverlapDivision, "generic method for list of monomials",
    true, [ IsAlgebra, IsList, IsNoncommutativeMonomialOrdering ], 0,
function( A, mons, ord )

    ## Overview: this is an implementation of Algorithm 13.
    ## returns local overlap-based multiplicative variables
    ## Detail: this function implements various algorithms
    ## described in the thesis "Noncommutative Involutive Bases"
    ## for finding left and right multiplicative variables
    ## for a set of polynomials based on the overlaps
    ## between the leading monomials of the polynomials.

    local  genA, ngenA, nmons, lenmon, nonMult, leftMult, rightMult, 
           i, moni, leni, j, monj, lenj, k, m;

    genA := GeneratorsOfAlgebra( A );
    if not ( genA[1] = One(A) ) then 
        Error( "expecting genA[1] = One(A)" );
    fi;
    genA := genA{ [2..Length(genA)] };
    ngenA := Length( genA );
    nmons := Length( mons );
    if( nmons = 0 ) then 
        return [ [], [] ];
    fi;
    ## set up arrays
    lenmon := List( mons, m -> Length(m) );
    leftMult := ListWithIdenticalEntries( nmons, 0 );
    rightMult := ListWithIdenticalEntries( nmons, 0 );
    nonMult := ListWithIdenticalEntries( nmons, 0 );
    for i in [1..nmons] do
        nonMult[i] := [ ];
    od;
    ## apply the conditions
    for i in [1..nmons] do
        moni := mons[i];
        leni := lenmon[i];
        for j in [i..nmons] do
            monj := mons[j];
            lenj := lenmon[j];
            if ( i <> j ) then
                ## looking for monj as a subword of moni
                for k in [1..leni-lenj] do
                    if moni{[k..(k+lenj-1)]} = monj then
                        Info( InfoIBNP, 3, "(1) [i,j,k]=", [i,j,k],
                            " adding ", moni[k+lenj], " to ", nonMult[j] );
                        Add( nonMult[j], moni[k+lenj] );
                    fi;
                od;
                ## looking for moni as a subword of monj
                for k in [1..lenj-leni] do
                    if monj{[k..(k+leni-1)]} = moni then
                        Info( InfoIBNP, 3, "(2) [i,j,k]=", [i,j,k],
                            " adding ", monj[k+leni], " to ", nonMult[i] );
                        Add( nonMult[i], monj[k+leni] );
                    fi;
                od;
            fi;
            m := Minimum( leni-1, lenj-1 );
            ## looking for overlap RHS[j] = LHS[i]
            for k in [1..m] do
                if ( moni{[1..k]} = monj{[(lenj-k+1)..lenj]} ) then
                        Info( InfoIBNP, 3, "(3) [i,j,k]=", [i,j,k],
                            " adding ", moni[k+1], " to ", nonMult[j] );
                        Add( nonMult[j], moni[k+1] );
                fi;
            od;
            ## looking for overlap RHS[i] = LHS[j]
            for k in [1..m] do
                if ( monj{[1..k]} = moni{[(leni-k+1)..leni]} ) then
                       Info( InfoIBNP, 3, "(4) [i,j,k]=", [i,j,k],
                            " adding ", monj[k+1], " to ", nonMult[i] );
                        Add( nonMult[i], monj[k+1] );
                fi;
            od;
        od;
    od;
    for i in [1..nmons] do
        leftMult[i] := [1..ngenA];
        rightMult[i] := Difference( [1..ngenA], nonMult[i] );
    od;
    return [ leftMult, rightMult ];
end );

#############################################################################
##
#M  RightOverlapDivision( <alg> <mons> <ord> )
##
InstallMethod( RightOverlapDivision, "generic method for list of monomials",
    true, [ IsAlgebra, IsList, IsNoncommutativeMonomialOrdering ], 0,
function( A, mons, ord )

    ## Overview: this is an implementation of Algorithm 13.
    ## returns local overlap-based multiplicative variables
    ## Detail: this function implements various algorithms
    ## described in the thesis "Noncommutative Involutive Bases"
    ## for finding left and right multiplicative variables
    ## for a set of polynomials based on the overlaps
    ## between the leading monomials of the polynomials.
    ## This function is the mirror image of LeftOverlapDivision.

    local  genA, ngenA, nmons, lenmon, nonMult, leftMult, rightMult, 
           i, moni, leni, j, monj, lenj, k, m;

    genA := GeneratorsOfAlgebra( A );
    if not ( genA[1] = One(A) ) then 
        Error( "expecting genA[1] = One(A)" );
    fi;
    genA := genA{ [2..Length(genA)] };
    ngenA := Length( genA );
    nmons := Length( mons );
    if( nmons = 0 ) then 
        return [ [], [] ];
    fi;
    ## set up arrays
    lenmon := List( mons, m -> Length(m) );
    leftMult := ListWithIdenticalEntries( nmons, 0 );
    rightMult := ListWithIdenticalEntries( nmons, 0 );
    nonMult := ListWithIdenticalEntries( nmons, 0 );
    for i in [1..nmons] do
        nonMult[i] := [ ];
    od;
    ## apply the conditions
    for i in [1..nmons] do
        moni := mons[i];
        leni := lenmon[i];
        for j in [i..nmons] do
            monj := mons[j];
            lenj := lenmon[j];
            if ( i <> j ) then
                ## looking for monj as a subword of moni
                if ( leni > lenj ) then
                    for k in Reversed( [leni..lenj+1] ) do
                        if moni{[(k+lenj-1)..k]} = monj then
                            Info( InfoIBNP, 3, "(1) [i,j,k]=", [i,j,k],
                             " adding ", moni[k-lenj], " to ", nonMult[j] );
                            Add( nonMult[j], moni[k-lenj] );
                        fi;
                    od;
                fi;
                ## looking for moni as a subword of monj
                if ( lenj > leni ) then
                    for k in Reversed( [lenj..leni+1] ) do
                        if monj{[(k+leni-1)..k]} = moni then
                            Info( InfoIBNP, 3, "(2) [i,j,k]=", [i,j,k],
                             " adding ", monj[k-leni], " to ", nonMult[i] );
                            Add( nonMult[i], monj[k-leni] );
                        fi;
                    od;
                fi;
            fi;
            m := Minimum( leni-1, lenj-1 );
            ## looking for overlap RHS[i] = LHS[j]
            for k in [1..m] do
                if ( moni{[(leni-k+1)..leni]} = monj{[1..k]} ) then
                        Info( InfoIBNP, 3, "(3) [i,j,k]=", [i,j,k],
                            " adding ", moni[leni-k], " to ", nonMult[j] );
                        Add( nonMult[j], moni[leni-k] );
                fi;
            od;
            ## looking for overlap RHS[j] = LHS[i]
            for k in [1..m] do
                if ( monj{[(lenj-k+1)..lenj]} = moni{[1..k]} ) then
                        Info( InfoIBNP, 3, "(4) [i,j,k]=", [i,j,k],
                            " adding ", monj[lenj-k], " to ", nonMult[i] );
                        Add( nonMult[i], monj[lenj-k] );
                fi;
            od;
        od;
    od;
    for i in [1..nmons] do
        rightMult[i] := [1..ngenA];
        leftMult[i] := Difference( [1..ngenA], nonMult[i] );
    od;
    return [ leftMult, rightMult ];
end );

#############################################################################
##
#M  StrongLeftOverlapDivision( <alg> <mons> <ord> )
##
InstallMethod( StrongLeftOverlapDivision,
    "generic method for list of monomials", true,
    [ IsAlgebra, IsList, IsNoncommutativeMonomialOrdering ], 0,
function( A, mons, ord )

    local mvars, genA, ngenA, lvars, rvars, nvars, nmons, 
          i, ui, j, uj, lenj, found, k;

    mvars := LeftOverlapDivision( A, mons, ord );

    ## Disjoint right cones: ensure that at least one variable in every
    ## monomial u_j is right non-multiplicative for every monomial u_i.
    Info( InfoIBNP, 2, "checking disjoint cones condition" );
    genA := GeneratorsOfAlgebra( A );
    if not ( genA[1] = One(A) ) then 
        Error( "expecting genA[1] = One(A)" );
    fi;
    genA := genA{ [2..Length(genA)] };
    ngenA := Length( genA );
    lvars := ShallowCopy( mvars[1] );
    rvars := ShallowCopy( mvars[2] );
    nvars := List( rvars, L -> Difference( [1..ngenA], L ) );
    nmons := Length( mons );
    for i in [1..nmons] do
        ui := mons[i];
        for j in Reversed( [1..nmons] ) do
            uj := mons[j];
            lenj := Length( uj );
            found := false;
            k := 1;
            while ( k <= lenj ) do
                if ( uj[k] in nvars[i] ) then 
                    found := true;
                    k := lenj + 1;
                else
                    k := k+1;
                fi;
            od;
            if not found then
                Info( InfoIBNP, 3, "adding ", uj[1], " when j = ", j, 
                                   " to nvars[i] with i = ", i );
                Add( nvars[i], uj[1] );
            fi;
        od;
    od;
    rvars := List( nvars, L -> Difference( [1..ngenA], L ) );
    return [ lvars, rvars ];
end );

#############################################################################
##
#M  StrongRightOverlapDivision( <alg> <mons> <ord> )
##
InstallMethod( StrongRightOverlapDivision,
    "generic method for list of monomials", true,
    [ IsAlgebra, IsList, IsNoncommutativeMonomialOrdering ], 0,
function( A, mons, ord )

    local mvars, genA, ngenA, lvars, rvars, nvars, nmons, 
          i, ui, leni, j, uj, found, k;

    mvars := RightOverlapDivision( A, mons, ord );

    ## Disjoint left cones: ensure that at least one variable in every
    ## monomial u_i is right non-multiplicative for every monomial u_j.
    genA := GeneratorsOfAlgebra( A );
    if not ( genA[1] = One(A) ) then 
        Error( "expecting genA[1] = One(A)" );
    fi;
    genA := genA{ [2..Length(genA)] };
    ngenA := Length( genA );
    lvars := ShallowCopy( mvars[1] );
    rvars := ShallowCopy( mvars[2] );
    nvars := List( lvars, L -> Difference( [1..ngenA], L ) );
    nmons := Length( mons );
    for j in [1..nmons] do
        uj := mons[j];
        for i in Reversed( [1..nmons] ) do
            ui := mons[i];
            leni := Length( ui );
            found := false;
            k := 1;
            while ( k <= leni ) do
                if ( ui[k] in nvars[j] ) then 
                    found := true;
                    k := leni + 1;
                else
                    k := k+1;
                fi;
            od;
            if not found then
                Add( nvars[j], ui[leni] );
            fi;
        od;
    od;
    lvars := List( nvars, L -> Difference( [1..ngenA], L ) );
    return [ lvars, rvars ];
end );

#############################################################################
##
#M  DivisionRecordNP( <alg> <polys> <ord> )
##
InstallMethod( DivisionRecordNP, "generic method for list of monomials",
    true, [ IsAlgebra, IsList, IsNoncommutativeMonomialOrdering ], 0,
function( A, polys, ord )

    ## Overview: returns local overlap-based multiplicative variables
    ## Detail: this function implements various algorithms
    ## described in the thesis "Noncommutative Involutive Bases"
    ## for finding left and right multiplicative variable 
    ## for a set of noncommutative polynomials

    local  genA, ngens, npolys, p, Lp, mons, mvars, drec, ok;

    genA := GeneratorsOfAlgebra( A );
    if not ( genA[1] = One(A) ) then 
        Error( "expecting genA[1] = One(A)" );
    fi;
    genA := genA{ [2..Length(genA)] };
    ngens := Length( genA );
    if( polys = [ ] ) then 
        return [ ];
    fi;
    npolys := Length( polys );
    ## set up arrays
    mons := LMonsNP( polys ); 
    Info( InfoIBNP, 3, "mons = ", mons );
    if ( NoncommutativeDivision = "Left" ) then 
        mvars := LeftDivision( A, mons, ord );
    elif ( NoncommutativeDivision = "Right" ) then
        mvars := RightDivision( A, mons, ord );
    elif ( NoncommutativeDivision = "LeftOverlap" ) then
        mvars := LeftOverlapDivision( A, mons, ord );
    elif ( NoncommutativeDivision = "RightOverlap" ) then
        mvars := RightOverlapDivision( A, mons, ord );
    elif ( NoncommutativeDivision = "StrongLeftOverlap" ) then
        mvars := StrongLeftOverlapDivision( A, mons, ord );
    elif ( NoncommutativeDivision = "StrongRightOverlap" ) then
        mvars := StrongRightOverlapDivision( A, mons, ord );
    else
        Error( "invalid NoncommutativeDivision" );
    fi;
    drec := rec( div := NoncommutativeDivision,
                 mvars := mvars, polys := polys );
    ok := IsDivisionRecord( drec );
    return drec;
end );

#############################################################################
##
#M  IPolyReduceNP( <alg> <poly> <drec> <ord> )
##
InstallMethod( IPolyReduceNP, 
    "generic method for a poly, record with fields [polys, mult vars]", true,
    [ IsAlgebra, IsObject, IsRecord, IsNoncommutativeMonomialOrdering ], 0,
function( A, pol, drec, ord )
## Overview: Reduces 2nd arg w.r.t. 3rd arg (polys and vars)
##
## Detail: drec is a record containing a list 'polys' of polynomials
## and their multiplicative variables 'vars'.
## Given a polynomial _pol_, this function involutively
## reduces the polynomial with respect to the given polys
## with associated left and right multiplicative variables vars.

    return CombinedIPolyReduceNP( A, pol, drec, ord, false );
end );

#############################################################################
##
#M  LoggedIPolyReduceNP( <alg> <poly> <drec> <ord> )
##
InstallMethod( LoggedIPolyReduceNP, 
    "generic method for a poly, record with fields [polys, mult vars]", true,
    [ IsAlgebra, IsObject, IsRecord, IsNoncommutativeMonomialOrdering ], 0,
function( A, pol, drec, ord )
##
## Overview: Reduces 2nd arg w.r.t. 3rd arg (polys and vars)
## just as in IPolyReduceNP, but returns a record contsaining the reduced
## polynomial and also logged information showing how the result is 
## obtained from the original polynomial.
##
    return CombinedIPolyReduceNP( A, pol, drec, ord, true );
end );

#############################################################################
##
#M  CombinedIPolyReduceNP( <alg> <poly> <drec> <ord> <logging> )
##
InstallMethod( CombinedIPolyReduceNP, 
    "generic method for a poly, record with fields [polys, mult vars]", true,
    [ IsAlgebra, IsObject, IsRecord, 
      IsNoncommutativeMonomialOrdering, IsBool ], 0,
function( A, obj, drec, ord, logging )

    local  polys, vars, pol, pl, i, numpolys, cutoffL, cutoffR, value,
           lenOrig, lenSub, poli, front, back, diff, factors, mon, moni,
           varL, varR, facL, facR, monj, coeff, coeffi, quot, M, appears,
           term, found, reduced, f, facf, lenf, lenL, lenR, polL, polR, logs;

    if not IsDivisionRecord( drec ) then
        Error( "third argument should be an overlap record" );
    fi;
    ## determine whether obj is in NP or GP format
    if IsList( obj ) then 
        pol := obj;
    else
        pol := GP2NP( obj );
        if ( pol = fail ) then
            Error( "obj should be a polynomial in NP or GP format" );
        fi;
    fi;
    Info( InfoIBNP, 3, "in IPolyReduceNP: pol = ", pol, 
                       ",  logging = ", logging );
    pl := InfoLevel( InfoIBNP );
    polys := drec.polys;
    numpolys := Length( polys );
    logs := List( [1..numpolys], i -> [  ] );
    vars := drec.mvars;
    front := [ [ ], [ ] ];
    back := pol;
    ## we now recursively reduce every term in the polynomial
    ## until no more reductions are possible
    while ( back[1] <> [ ] ) do 
        Info( InfoIBNP, 3, "first loop: ",
                  "front = ", NP2GP( front, A ),
                  ", back = ", NP2GP( back, A ) );
        reduced := true;
        while reduced and ( back <> [ [], [] ] ) do
            Info( InfoIBNP, 3, "second loop: back = ", back );
            reduced := false;
            mon := back[1][1];
            coeff := back[2][1];
            i := 0;
            while ( i < numpolys ) and ( not reduced ) do  
                Info( InfoIBNP, 3, "third loop: back = ", back );
                ## for each polynomial in the list
                i := i+1;
                poli := polys[i];
                moni := poli[1][1];  ## pick a test monomial                                                                 
                factors := DivNM( mon, moni );
                lenf := Length(factors);
                if ( lenf > 0 ) then ## moni divides mon
                    M := 0;  ## assume that the first conventional division 
                             ## is not an involutive division
                             ## while there are conventional divisions left 
                             ## to look at and while none of these have yet
                             ## proved to be involutive divisions
                    found := false;
                    f := 0;
                    while ( not found ) and ( f < lenf ) and ( M = 0 ) do
                        ## assume that this conventional division 
                        ## is an involutive division
                        f := f+1;
                        facf := factors[f];
                        M := 1;
                        ## extract the ith left & right mult variables
                        varL := vars[1][i];
                        varR := vars[2][i];
                        ## Extract the left and right factors
                        facL := facf[1];
                        facR := facf[2];
                        ## test all variables in facL for left
                        ## multiplicability in the ith monomial
                        lenL := Length( facL );
                        ## decide whether one/all variables in facL 
                        ## are left multiplicative
                        ## right-most variable only
                        if ( lenL > 0 ) then
                            monj := facL[ lenL ];
                            appears := monj in varL;
                            ## if the generator doesn't appear this 
                            ## is not an involutive division
                            if ( not appears ) then 
                                M := 0;
                            else
                                Info( InfoIBNP, 3, monj, " not in ", varL );
                            fi;
                        fi;
                        ## test all variables in facR for right
                        ## multiplicability in the ith monomial
                        if ( M = 1 ) then
                            lenR := Length( facR );
                            ## decide whether one/all variables in facR
                            ## are left multiplicative
                            ## Left-most var only
                            if ( lenR > 0 ) then
                                monj := facR[1];
                                appears := monj in varR;
                                ## if the generator doesn't appear
                                ## this is not an involutive division
                                if ( not appears ) then
                                    M := 0;
                                else
                                    Info( InfoIBNP, 3, monj," not in ", varR );
                                fi;
                            fi;
                        fi;
                        ## if this conventional division wasn't involutive, 
                        ## look at the next division
                        if ( M = 1 ) then
                            found := true;
                        fi;
                    od;
                       
                    ## if an involutive division was found
                    if found then
                        if ( pl > 2 ) then
                            Print( "found: ", mon, " = ", facf[1], ",",
                                              moni, ",", facf[2], "\n" );
                        fi;
                        ## indicate a reduction has been carried out 
                        ## to exit the loop
                        ## pick the divisor's leading coefficient
                        coeffi := poli[2][1];
                        if ( facL <> [ ] ) then 
                            diff := MulNP( [ [facL], [1] ], poli ); 
                        else 
                            diff := poli;
                        fi;
                        if ( facR <> [ ] ) then
                            diff := MulNP( diff, [ [facR], [1] ] );
                        fi;
                        quot := - coeff/coeffi;
                        diff := AddNP( back, diff, 1, quot );
                        Info( InfoIBNP, 2, "front = ", NP2GP( front, A ) );
                        Info( InfoIBNP, 2, " diff = ", NP2GP( diff, A ) );
                        if logging then 
                            Add( logs[i], [ - quot, facf[1], facf[2] ] );
                        fi;
                        reduced := true;
                        ## in the next iteration we will be 
                        ## reducing the new polynomial diff
                        back := CleanNP( diff );
                        Info( InfoIBNP, 3, "cleaned back: ", back );
                    fi;
                fi;
            od;
        od;
        ## no reduction of the lead term, so add it to front
        if ( back <> [ [ ], [ ] ] ) then
            term := [ [ back[1][1] ], [ back[2][1] ] ];
            if ( front = [ [ ], [ ] ] ) then 
                front := term;
            else
                front := AddNP( front, term, 1, 1 ); 
            fi; 
            back := AddNP( back, term, 1, -1 );
            Info( InfoIBNP, 3, "front = ", front );
            Info( InfoIBNP, 3, " back = ", back );
        fi;
    od;
    if not logging then
        return front;  ## return the reduced and simplified polynomial
    else
        return rec( result := front, logs := logs, polys := polys );
    fi;
end );

#############################################################################
##
#M  VerifyLoggedIRecordNP( <poly> <logs> )
##
InstallMethod( VerifyLoggedRecordNP, 
    "generic method for an NP-poly and a logged record", true,
    [ IsList, IsRecord ], 0,
function( pol, logrec )
##
## Overview: Verifies that logrec.logs and logrec.result can be combined
## to recaculate the original pol
##
    local logs, polys, result, r, i, poli, j, Lij, p;

    logs := logrec.logs;
    polys := logrec.polys;
    result := logrec.result;
    r := ShallowCopy( result );
    for i in [1..Length(logs)] do
        poli := polys[i];
        for j in [1..Length( logs[i] )] do
            Lij := logs[i][j];
            if ( Lij[2] <> [ ] ) then
                p := MulNP( [ [ Lij[2] ], [1] ], poli );
            else
                p := poli;
            fi;
            if ( Lij[3] <> [ ] ) then
                p := MulNP( p, [ [ Lij[3] ], [1] ] );
            fi;
            r := AddNP( r, [ p[1], Lij[1]*p[2] ], 1, 1 );
        od;
    od;
    return ( r = pol );
end );

#############################################################################
##
#M  IAutoreduceNP( <alg> <polys> <ord> )
##
InstallMethod( IAutoreduceNP, "generic method for list of polys",
    true, [ IsAlgebra, IsList, IsNoncommutativeMonomialOrdering ], 0,
function( A, polys, ord )

    ## Overview: Autoreduces an FAlgList recursively 
    ## until no more reductions are possible 
    ## Detail: This function involutively reduces each member of an FAlgList 
    ## w.r.t. all the other members of the list, removing the polynomial 
    ## from the list if it is involutively reduced to 0. This process is
    ## iterated until no more such reductions are possible. 

    local d, twod, pl, oldPoly, newPoly, nrec, new, old, oldCopy, drec,
          vars, pos, pushPos, len, gcd;

    len := Length( polys );
    ## twod := 2^d;
    pl := InfoLevel( InfoIBNP );
    if( len < 2 ) then 
        ## the input basis is empty or consists of a single polynomial
        return polys;
    fi;

    ## start by reducing the final element (working backwards means
    ## that less work has to be done calculating multiplicative variables)
    pos := len;
    ## make a copy of the input basis for traversal
    old := StructuralCopy( polys );
    while( pos > 0 ) do   ## for each polynomial in old
        ## extract the pos-th element of the basis
        oldPoly := old[pos];
        Info( InfoIBNP, 3, "reducing polynomial polys(", pos, 
            "\nlooking at element ", oldPoly, " of basis" );
        ## construct basis without 'poly'
        oldCopy := StructuralCopy( old );  ## make a copy of old
        len := Length( oldCopy );
        ## calculate Multiplicative Variables if using a local division
        drec := DivisionRecordNP( A, oldCopy, ord );
        vars := drec.mvars;
        ## vars := fMonPairListRemoveNumber( pos, vars );
        vars[1] := Concatenation( vars[1]{[1..pos-1]}, 
                                  vars[1]{[pos+1..len]} ); 
        vars[2] := Concatenation( vars[2]{[1..pos-1]}, 
                                  vars[2]{[pos+1..len]} ); 

        new := Concatenation( old{[1..pos-1]}, old{[pos+1..len]} );
        Sort( new, GtNPoly );
        nrec := DivisionRecord( A, new, ord );
        old := StructuralCopy( oldCopy );     ## restore old
        ## to recap, old is now unchanged whilst new holds all
        ## the elements of old except oldPoly.
        ## involutively reduce the old polynomial w.r.t. the truncated list
        newPoly := IPolyReduceNP( A, oldPoly, nrec, ord );

        ## if the polynomial did not reduce to 0
        if not ( newPoly = [ [ ], [ ] ] ) then 
            ## divide the polynomial through by its GCD
            gcd := Gcd( newPoly[2] );
            newPoly := [ newPoly[1], newPoly[2]/gcd ];
            if( pl > 2 ) then 
                Print( "reduced pol to " ); 
                PrintNP( newPoly );
                Print( "\n" );
            fi;
            ## check for trivial ideal
            if ( newPoly = [ ] ) then 
                return [ [ ], [ ] ];
            fi;
            if IsNegInt( newPoly[2][1] ) then 
                newPoly[2] := -newPoly[2];
            fi;
            ## if the old polynomial is equal to the new polynomial
            ## (i.e. no reduction took place)
            if ( oldPoly = newPoly ) then 
                ## we may proceed to look at the next polynomial 
                pos := pos - 1;
            else 
                ## otherwise some reduction took place so start again
                ## if we are restricting prolongations based on degree,...
                ## add the new polynomial onto the list
                ## push the new polynomial onto the end of the list
                old := Concatenation( new, [ newPoly ] );
                Info( InfoIBNP, 3, "adding reduced poly: ", 
                      oldPoly, " --> ", newPoly );
                Sort( old, GtNPoly );
                ## return to the end of the list minus one
                ## (we know the last element is irreducible)
                pos := Length( old ) - 1;
            fi;
        else    
            ## the polynomial reduced to zero
            ## remove the polynomial from the list
            Info( InfoIBNP, 2, "poly reduced to zero: ", oldPoly );
            old := StructuralCopy( new );
            ## continue to look at the next element
            pos := pos - 1;
            if ( pl > 2 ) then 
                Print( "Reduced p to 0\n");
            fi;
        fi;
    od;
    Sort( old, GtNPoly );
    ##  return the fully autoreduced basis
    if ( old = polys ) then ## no change
        return true;
    else
        return old;
    fi;
end );

#############################################################################
##
#M  InvolutiveBasisNP( <alg> <polys> )
##
InstallMethod( InvolutiveBasisNP, 
    "generic method for algebra + list of polys", true,
    [ IsAlgebra, IsList, IsNoncommutativeMonomialOrdering ], 0,
function( A, polys, ord )

    ##  Implements Algorithm 12 for computing locally involutive bases. 

    local  pl, gens, ngens, all, zero, mrec, mvars, nvars, basis0, basis,
           nbasis, done, prolong, u, lenu, v, i, j, k, npro, found;

    pl := InfoLevel( InfoIBNP );
    gens := GeneratorsOfAlgebra( A );
    if not ( gens[1] = One(A) ) then 
        Error( "expecting gens[1] = One(A)" );
    fi;
    gens := gens{ [2..Length(gens)] };
    ngens := Length( gens );
    all := [ 1..ngens ];
    zero := [ [ ], [ ] ];
    Info( InfoIBNP, 2, "Computing an Involutive Basis...");
    basis := List( polys, p -> CleanNP(p) );
    done := false;
    Sort( basis, GtNPoly );
    while ( not done ) do
        if ( pl >= 2 ) then
            Print( "restarting with basis:\n" );
            PrintNPList( basis );
        fi;
        basis0 := ShallowCopy( basis );
        basis := IAutoreduceNP( A, basis0, ord );
        if ( basis = true ) then 
            basis := basis0;
        fi;
        nbasis := Length( basis );
        mrec := DivisionRecordNP( A, basis, ord );
        Info( InfoIBNP, 2, "mrec = ", mrec );
        mvars := mrec.mvars;
        nvars := [ List( mvars[1], v -> Difference( all, v ) ), 
                   List( mvars[2], v -> Difference( all, v ) ) ];
        Info( InfoIBNP, 2, "nvars = ", nvars );
        ## construct the prolongations
        prolong := [ ];
        for i in [1..nbasis] do
            ## left prolongations
            lenu := Length( basis[i][1] );
            for j in nvars[1][i] do
                u := StructuralCopy( basis[i] );
                for k in [1..lenu] do
                    u[1][k] := Concatenation( [j], u[1][k] );
                od;
                Add( prolong, CleanNP( u ) );
                Info( InfoIBNP, 2, "left prolongation: ", u );
            od;
            ## right prolongations
            for j in nvars[2][i] do
                u := StructuralCopy( basis[i] );
                for k in [1..lenu] do
                    Add( u[1][k], j );
                od;
                Add( prolong, CleanNP( u ) );
                Info( InfoIBNP, 2, "right prolongation: ", u );
            od;
        od;
        Sort( prolong, LtNPoly );
        if ( pl >= 2 ) then
            Print( "prolong = \n" );
            PrintNPList( prolong );
        fi;
        npro := Length( prolong ); 
        found := false;
        i := 0;
        while ( not found ) and ( i < npro ) do 
            i := i+1;
            u := prolong[i];
            v := IPolyReduceNP( A, u, mrec, ord );
            if ( v <> [ [ ], [ ] ] ) then 
                found := true; 
                if IsNegInt( v[2][1] ) then 
                    v[2] := -v[2];
                fi;
                Add( basis, v );
                if ( pl > 0 ) and 
                   ( Length(basis) > InvolutiveAbortLimit ) then
                      return fail;
                fi;
                Info( InfoIBNP, 1, "adding ", u, " -> ", v );
            fi;
        od;
        if not found then
            done := true;
        fi;
        basis0 := IAutoreduceNP( A, basis, ord );
        if not ( basis0 = true ) then
            basis := basis0;
            Sort( basis, GtNPoly );
        fi;
    od;
    return DivisionRecordNP( A, basis, ord );
end );

#############################################################################
##
#E  involutive-np.gi . . . . . . . . . . . . . . . . . . . . . . .  ends here
## 