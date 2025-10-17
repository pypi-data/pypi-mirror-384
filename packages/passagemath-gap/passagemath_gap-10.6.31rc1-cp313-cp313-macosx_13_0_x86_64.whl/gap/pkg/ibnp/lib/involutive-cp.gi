#############################################################################
##
#W  involutive-cp.gi      GAP4 package IBNP      Gareth Evans & Chris Wensley
##

#############################################################################
##
#M  PommaretDivision( <alg> <polys> <ord> )
##
InstallMethod( PommaretDivision, "generic method for list of monomials",
    true, [ IsAlgebra, IsList, IsMonomialOrdering ], 0,
function( A, mons, ord )

    local nmons, mvars, vars, i, posi, emoni;
    nmons := Length( mons );
    mvars := ListWithIdenticalEntries( nmons, 0 );
    vars := OccuringVariableIndices( ord );
    if ( vars = true ) then
        Error( "specify the variable list in the ordering" );
    fi;
    for i in [1..nmons] do   ## for each monnomial 
        emoni := ExtRepPolynomialRatFun( mons[i] )[1];
        posi := Position( vars, emoni[1] );
        mvars[i] := [1..posi];  ## [1 .. first letter]
    od;
    return mvars;
end );

#############################################################################
##
#M  ThomasDivision( <alg> <polys> <ord> )
##
InstallMethod( ThomasDivision, "generic method for list of monomials",
    true, [ IsAlgebra, IsList, IsMonomialOrdering ], 0,
function( A, mons, ord )

    local genA, ngens, nmons, vars, e, max, j, k, p, i, m, mvars;
    genA := GeneratorsOfLeftOperatorRingWithOne( A );
    ngens := Length( genA );
    nmons := Length( mons );
    vars := OccuringVariableIndices( ord );
    if ( vars = true ) then
        Error( "specify the variable list in the ordering" );
    fi;
    ## find the maximal exponents
    max := ListWithIdenticalEntries( ngens, 0 );
    for j in [1..nmons] do
        e := ExtRepPolynomialRatFun( mons[j] )[1];
        for k in [1..Length(e)/2] do 
            p := k+k-1;
            i := Position( vars, e[p] );
            m := e[p+1];
            if ( m > max[i] ) then 
                max[i] := m;
            fi;
        od;
    od;
    Info( InfoIBNP, 2, "maximal exponents = ", max );
    ## find the multiplicative variables
    mvars := ListWithIdenticalEntries( nmons, 0 );
    for j in [1..nmons] do
        mvars[j] := [ ];
        e := ExtRepPolynomialRatFun( mons[j] )[1];
        for k in [1..Length(e)/2] do
            p := k+k-1;
            i := Position( vars, e[p] );
            m := e[p+1];
            if ( m = max[i] ) then 
                Add( mvars[j], i );
            fi;
        od;
    od;
    Info( InfoIBNP, 2, "multiplicative variables = ", mvars );
    return mvars;
end );

#############################################################################
##
#M  JanetDivision( <alg> <polys> <ord> )
##
InstallMethod( JanetDivision, "generic method for list of monomials",
    true, [ IsAlgebra, IsList, IsMonomialOrdering ], 0,
function( A, mons, ord )

    local  genA, ngens, nmons, vpos, vars, ordfn, expos, j, e, k, i, 
           mvars, done, ej, L, subj, ei, ok;
    genA := ShallowCopy( GeneratorsOfLeftOperatorRingWithOne( A ) );
    ngens := Length( genA );
    Info( InfoIBNP, 2, "in JanetDivision, mons = ", mons );
    nmons := Length( mons );
    vpos := List( genA, g -> ExtRepPolynomialRatFun(g)[1][1] );
    vars := OccuringVariableIndices( ord );
    if ( vars = true ) then
        Error( "specify the variable list in the ordering" );
    fi;
    ordfn := MonomialComparisonFunction( ord );
    ## create list of exponents, including zeroes
    expos := ListWithIdenticalEntries( nmons, 0 );
    for j in [1..nmons] do
        expos[j] := ListWithIdenticalEntries( ngens, 0 );
        e := ExtRepPolynomialRatFun( mons[j] )[1];
        Info( InfoIBNP, 2, "e(mons[j]) = ", e );
        for k in [1..Length(e)/2] do
            i := Position( vpos, e[k+k-1] );
            expos[j][i] := e[k+k];
        od;
    od;
    Info( InfoIBNP, 2, "expos = ", expos );
    ## now set up the lists of multiplicative variables
    mvars := ListWithIdenticalEntries( nmons, 0 );
    for j in [1..nmons] do
        mvars[j] := [ ];
    od;
    ## test for x_1 .. x_{n-1}
    for j in [1..ngens-1] do
        done := ListWithIdenticalEntries( nmons, false );
        for k in [1..nmons] do
            if not done[k] then
                done[k] := true;
                ej := expos[k][j];
                L := [k];
                subj := expos[k]{[j+1..ngens]};
                for i in [k+1..nmons] do
                    if ( subj = expos[i]{[j+1..ngens]} ) then
                        done[i] := true;
                        Add( L, i );
                        if ( expos[i][j] > ej ) then
                            ej := expos[i][j];
                        fi;
                    fi;
                od;
                for i in L do
                    if ( subj = expos[i]{[j+1..ngens]} ) 
                        and ( expos[i][j] = ej ) then
                        Add( mvars[i], j );
                    fi;
                od;
            fi;
        od;
    od;
    ## now test for x_n
    ei := expos[1][ngens];
    for k in [2..nmons] do
        if ( expos[k][ngens] > ei ) then
            ei := expos[k][ngens];
        fi;
    od;
## Error("here");
    for k in [1..nmons] do
        if ( expos[k][ngens] = ei ) then
            Add( mvars[k], ngens );
        fi;
    od;
    return mvars;
end );

#############################################################################
##
#M  DivisionRecord( <args> )
##
BindGlobal( "DivisionRecord", 
function( arg )
    local nargs, A, polys, ord;
    nargs := Length( arg );
    if not ( nargs = 3 ) then 
        Error( "expecting arguments [ A, polys, ord ]" ); 
    fi;
    A := arg[1];
    polys := arg[2];
    ord := arg[3];
    if not IsNearAdditiveMagma( A ) then 
        Error( "expecting an algebra as first parameter" ); 
    fi;
    if IsCommutative( A ) then 
        return DivisionRecordCP( A, polys, ord ); 
    else 
        return DivisionRecordNP( A, polys, ord );
    fi;
end );

############################################################################
##
#M IsDivisionRecord
## 
InstallMethod( IsDivisionRecord, "generic method for records", true, 
    [ IsRecord ], 0,
function( r )
    return ( IsBound\.( r, RNamObj( "div" ) ) ) 
       and ( IsBound\.( r, RNamObj( "mvars" ) ) )
       and ( IsBound\.( r, RNamObj( "polys" ) ) );
end );

#############################################################################
##
#M  DivisionRecordCP( <alg> <polys> <ord> )
##
InstallMethod( DivisionRecordCP, "generic method for list of monomials",
    true, [ IsAlgebra, IsList, IsMonomialOrdering ], 0,
function( A, polys, ord )

    ## Overview: returns local overlap-based multiplicative variables
    ## Detail: this function implements various algorithms
    ## described in the thesis "Noncommutative Involutive Bases"
    ## for finding multiplicative variable for a set of polynomials 

    local  pl, genA, ordfn, ngens, npolys, mons, mvars;

    pl := InfoLevel( InfoIBNP );
    if( polys = [ ] ) then 
        return [ ];
    fi;
    genA := ShallowCopy( GeneratorsOfLeftOperatorRingWithOne( A ) );
    ordfn := MonomialComparisonFunction( ord );
    Sort( genA, ordfn );
    ngens := Length( genA );
    ## set up arrays
    npolys := Length( polys );
    mons := List( polys, p -> LeadingMonomialOfPolynomial( p, ord ) );
    Info( InfoIBNP, 2, "mons = ", mons );
    if ( CommutativeDivision = "Pommaret" ) then 
        mvars := PommaretDivision( A, mons, ord );
    elif ( CommutativeDivision = "Thomas" ) then
        mvars := ThomasDivision( A, mons, ord );
    elif ( CommutativeDivision = "Janet" ) then
        mvars := JanetDivision( A, mons, ord );
    else
        Error( "invalid CommutativeDivision" );
    fi;
    return rec( div := CommutativeDivision, mvars := mvars, polys := polys );
end );

#############################################################################
##
#M  IPolyReduce( <alg> <poly> <drec> <ord> )
##
BindGlobal( "IPolyReduce",
function( arg )
    local nargs, A, p, drec, ord, polys, mvars;
    nargs := Length( arg );
    if not ( nargs = 4 ) then 
        Error( "expecting arguments [ A, pol, overlaprec, ordering ]" ); 
    fi;
    A := arg[1];
    p := arg[2];
    drec := arg[3];
    polys := drec.polys;
    mvars := drec.mvars;
    ord := arg[4];
    if not IsNearAdditiveMagma( A ) then 
        Error( "expecting an algebra as first parameter" ); 
    fi;
    if IsCommutative( A ) then
        ## add some tests
        return IPolyReduceCP( A, p, drec, ord ); 
    else
        ## add more tests
        return IPolyReduceNP( A, p, drec, ord );
    fi;
end );

#############################################################################
##
#M  IPolyReduceCP( <alg> <poly> <drec> <ord> )
##
InstallMethod( IPolyReduceCP, 
    "generic method for a poly, record with fields [polys, mult vars]",
    true, [ IsPolynomialRing, IsPolynomial, IsRecord, IsMonomialOrdering ], 0,
function( A, pol, drec, ord )
##
## Overview: Reduces 2nd arg w.r.t. 3rd arg (polys and vars)
##
## Detail: drec is a record containing a list 'polys' of polynomials
## and their multiplicative variables 'vars'.
## Given a polynomial _pol_, this function involutively
## reduces the polynomial with respect to the given polys
## with associated left and right multiplicative variables vars.

    return CombinedIPolyReduceCP( A, pol, drec, ord, false );
end );

#############################################################################
##
#M  LoggedIPolyReduce( <alg> <poly> <drec> <ord> )
##
BindGlobal( "LoggedIPolyReduce",
function( arg )
    local nargs, A, p, drec, ord, polys, mvars;
    nargs := Length( arg );
    if not ( nargs = 4 ) then 
        Error( "expecting arguments [ A, pol, overlaprec, ordering ]" ); 
    fi;
    A := arg[1];
    p := arg[2];
    drec := arg[3];
    polys := drec.polys;
    mvars := drec.mvars;
    ord := arg[4];
    if not IsNearAdditiveMagma( A ) then 
        Error( "expecting an algebra as first parameter" ); 
    fi;
    if IsCommutative( A ) then
        ## add some tests
        return CombinedIPolyReduceCP( A, p, drec, ord, true ); 
    else
        ## add more tests
        return CombinedIPolyReduceNP( A, p, drec, ord, true );
    fi;
end );

#############################################################################
##
#M  LoggedIPolyReduceCP( <alg> <poly> <drec> <ord> )
##
InstallMethod( LoggedIPolyReduceCP, 
    "generic method for a poly, record with fields [polys, mult vars]",
    true, [ IsPolynomialRing, IsPolynomial,
            IsRecord, IsMonomialOrdering ], 0,
function( A, pol, drec, ord )
##
## Overview: Reduces 2nd arg w.r.t. 3rd arg (polys and vars)
## just as in IPolyReduceCP, but returns a record contsaining the reduced
## polynomial and also logged information showing how the result is 
## obtained from the original polynomial.
##
    return CombinedIPolyReduceCP( A, pol, drec, ord, true );
end );

#############################################################################
##
#M  CombinedIPolyReduceCP( <alg> <poly> <drec> <ord> <logging> )
##
InstallMethod( CombinedIPolyReduceCP, 
    "generic method for a poly, record with fields [polys, mult vars]",
    true, [ IsPolynomialRing, IsPolynomial,
            IsRecord, IsMonomialOrdering, IsBool ], 0,
function( A, pol, drec, ord, logging )

    local  polys, mvars, genA, vpos, a, z, front, back, eback, 
           numpolys, mons, coeffs, reduced, mon, coeff, term,
           i, poli, moni, fac, coeffi, efac, lenf, ok, logs;

    if not IsDivisionRecord( drec ) then
        Error( "third argument should be an overlap record" );
    fi;
    Info( InfoIBNP, 3, "in IPolyReduceCP: pol = ", pol, 
                       ",  logging = ", logging );
    polys := drec.polys;
    numpolys := Length( polys );
    logs := List( [1..numpolys], i -> Zero( A ) );
    mvars := drec.mvars;
    genA := GeneratorsOfLeftOperatorRingWithOne( A );
    vpos := List( genA, g -> ExtRepPolynomialRatFun(g)[1][1] );
    a := genA[1];
    z := a-a;  ## zero polynomial;
    front := z;
    back := pol;
    eback := ExtRepPolynomialRatFun( back );
    mons := List( polys, p -> LeadingMonomialOfPolynomial( p, ord ) );
    coeffs := List( polys, p -> LeadingCoefficientOfPolynomial( p, ord ) );
    ## we now recursively reduce every term in the polynomial
    ## until no more reductions are possible
    while ( eback <> [ ] ) do
        reduced := true;
        while reduced and ( eback <> [ ] ) do
            reduced := false;
            mon := LeadingMonomialOfPolynomial( back, ord );
            coeff := LeadingCoefficientOfPolynomial( back, ord );
            i := 0;
            while ( i < numpolys ) and ( not reduced ) do  
                ## for each polynomial in the list
                i := i+1;
                poli := polys[i];
                moni := mons[i];  ## pick a test monomial
                fac := mon/moni;
                if IsPolynomial( fac ) then  ## moni divides mon
                    Info( InfoIBNP, 3, "divisor found: fac = ", fac );
                    coeffi := coeffs[i];
                    efac := ExtRepPolynomialRatFun( fac )[1];
                    Info( InfoIBNP, 3, "fac = ", fac, ",  efac = ", efac );
                    lenf := Length( efac );
                    ok := ( lenf = 0 ) or ForAll( [1,3..lenf-1], 
                            j -> Position( vpos, efac[j] ) in mvars[i] );
                    ## if an involutive division was found
                    if ok then
                        ## indicate a reduction has been carried out 
                        ## to exit the loop
                        ## pick the divisor's leading coefficient
                        ## pick 'nice' cancelling coefficients
                        term := (coeff/coeffi)*fac;
                        back := back - term*poli;
                        if logging then
                            logs[i] := logs[i] + term;
                        fi;
                        Info( InfoIBNP, 2, "reduced to: ", front+back );
                        eback := ExtRepPolynomialRatFun( back );
                        reduced := true;
                    fi;
                fi;
            od;
        od;
        if ( eback <> [ ] ) then
            ## no reduction of the lead term, so add it to front
            front := front + coeff*mon;
            back := back - coeff*mon;
            eback := ExtRepPolynomialRatFun( back );
        fi;
    od;
    if ( front <> z ) then
        if ( LeadingCoefficientOfPolynomial( front, ord ) < 0 ) then
            front := (-1)*front;
            if logging then
                logs := List( logs, t -> (-1)*t );
            fi;
        fi;
    fi;
    if not logging then
        return front;  ## return the reduced and simplified polynomial
    else
        return rec( result := front, logs := logs, polys := polys );
    fi;
end );

#############################################################################
##
#M  IAutoreduce( <args> )
##
BindGlobal( "IAutoreduce",
function( arg )
    local nargs, A, polys, ord;
    nargs := Length( arg );
    if not ( nargs = 3 ) then 
        Error( "expecting arguments [ A, polys, ord ]" ); 
    fi;
    A := arg[1];
    polys := arg[2];
    ord := arg[3];
    if not IsNearAdditiveMagma( A ) then
        ## add some tgests
        Error( "expecting an algebra as first parameter" ); 
    fi;
    if IsCommutative( A ) then
        ## add more tests
        return IAutoreduceCP( A, polys, ord ); 
    else 
        return IAutoreduceNP( A, polys, ord ); 
    fi;
end );

#############################################################################
##
#M  IAutoreduceCP( <alg> <polys> <ord> )
##
InstallMethod( IAutoreduceCP, "generic method for list of polys",
    true, [ IsAlgebra, IsList, IsMonomialOrdering ], 0,
function( A, polys, ord )

    ## Overview: Autoreduces a list of polynomials recursively 
    ## until no more reductions are possible 
    ## Detail: This function involutively reduces each member of a
    ## list of polynomials w.r.t. all the other members of the list, 
    ## removing the polynomial from the list if it is involutively
    ## reduced to 0. Iterate until no more such reductions are possible. 

    local pl, div, npolys, genA, a, z, pos, old, reduced, ordfn,
          oldPoly, nrec, newvars, vars, drec, oldvars, new, newPoly;

    pl := InfoLevel( InfoIBNP );
    div := CommutativeDivision;
    npolys := Length( polys );
    if( npolys < 2 ) then 
        ## the input basis is empty or consists of a single polynomial
        return polys;
    fi;
    genA := GeneratorsOfLeftOperatorRingWithOne( A );
    a := genA[1];
    z := a-a;  ## zero polynomial;
    ## start by reducing the final element (working backwards means
    ## that less work has to be done calculating multiplicative variables)
    ## if we are using a local division and the basis is sorted by DegRevLex,
    ## the last polynomial is irreducible so we do not have to consider it.
    ## make a copy of the input basis for traversal
    old := StructuralCopy( polys );
    ordfn := MonomialComparisonFunction( ord );
    reduced := true;
    while reduced do
        reduced := false;
        Sort( old, ordfn );
        npolys := Length( old );
        pos := npolys;
        drec := DivisionRecordCP( A, old, ord );
        oldvars := drec.mvars;
        if ( pl > 2 ) then 
            Print( "old = ", old, "\n" );
            Print( "oldvars = ", oldvars, "\n" );
        fi;
        while ( pos > 0 ) and ( not reduced ) do   ## for each poly in old
            ## extract pos-th element of the basis and reduce using the rest
            oldPoly := old[pos];
            if ( pl > 2 ) then 
                Print( "oldPoly = ", oldPoly, "\n" );
            fi;
            ## construct basis without oldPoly
            ## calculate multiplicative Variables if using a local division
            newvars := Concatenation( oldvars{[1..pos-1]},
                                      oldvars{[pos+1..npolys]} ); 
            new := Concatenation( old{[1..pos-1]}, old{[pos+1..npolys]} );
            nrec := rec( div := div, mvars := newvars, polys := new );
            ## involutively reduce old polynomial w.r.t. the truncated list
            newPoly := IPolyReduceCP( A, oldPoly, nrec, ord );
            Info( InfoIBNP, 2, "newPoly = ", newPoly );
            ## if the polynomial did not reduce to 0
            if ( newPoly = z ) then 
                ## the polynomial reduced to zero
                ## remove the polynomial from the list
                new := Concatenation( new{[1..pos-1]},
                                      new{[pos+1..npolys]} );
                pos := pos - 1;
                npolys := npolys - 1;
            elif ( oldPoly = newPoly ) then 
                ## we may proceed to look at the next polynomial 
                pos := pos - 1;
            else
                ## otherwise some reduction took place so start again
                ## add the new polynomial onto the list
                reduced := true;
                old := Concatenation( new, [ newPoly ]  );
                Info( InfoIBNP, 2, "reduction!  now old = ", old );
            fi;
        od;
    od; 
    Sort( old, ordfn );
    ##  return the fully autoreduced basis
    if ( old = polys ) then ## no change
        return true;
    else
        return old;
    fi;
end );

#############################################################################
##
#M  InvolutiveBasis( <args> )
##
BindGlobal( "InvolutiveBasis",
function( arg )
    local nargs, A, polys, ord;
    nargs := Length( arg );
    if not ( nargs = 3 ) then 
        Error( "expecting arguments [ A, polys, ord ]" ); 
    fi;
    A := arg[1];
    polys := arg[2];
    ord := arg[3];
    if not IsNearAdditiveMagma( A ) then
        ## add some tests
        Error( "expecting an algebra as first parameter" ); 
    fi;
    if IsCommutative( A ) then
        ## add more tests
        return InvolutiveBasisCP( A, polys, ord ); 
    else 
        return InvolutiveBasisNP( A, polys, ord ); 
    fi;
end );

#############################################################################
##
#M  InvolutiveBasisCP( <alg> <polys> <ord> )
##
InstallMethod( InvolutiveBasisCP, 
    "generic method for commutative algebra + list of polys + ordering",
    true, [ IsAlgebra, IsList, IsMonomialOrdering ], 0,
function( A, polys, ord )

    ##  Implements Algorithm 9 for computing commutative involutive bases. 

    local  pl, npolys, genA, a, z, ngens, all, basis, vars, done, 
           ordfn, basis0, nbasis, drec, mvars, nvars, prolong, 
           i, j, npro, found, u, v;

    pl := InfoLevel( InfoIBNP );
    Info( InfoIBNP, 2, "Computing an Involutive Basis...");
    npolys := Length( polys );
    if( npolys < 2 ) then 
        ## the input basis is empty or consists of a single polynomial
        return polys;
    fi;
    genA := GeneratorsOfLeftOperatorRingWithOne( A );
    a := genA[1];
    z := a-a;  ## zero polynomial;
    ngens := Length( genA );
    all := [ 1..ngens ];
    basis := IAutoreduceCP( A, polys, ord );
    if ( basis = true ) then ## no reduction
        basis := polys;
    fi;
    Info( InfoIBNP, 2, "initial basis = ", basis ); 
    done := false;
    ordfn := MonomialComparisonFunction( ord );
    while ( not done ) do
        Sort( basis, ordfn );
        Info( InfoIBNP, 1, "restarting with basis:\n", basis );
        basis0 := ShallowCopy( basis );
        basis := IAutoreduceCP( A, basis0, ord );
        if ( basis = true ) then 
            basis := basis0;
        else
            Info( InfoIBNP, 1, "after autoreduction basis = \n", basis );
        fi;
        nbasis := Length( basis );
        drec := DivisionRecordCP( A, basis, ord );
        Info( InfoIBNP, 1, "division record for basis: ", drec );
        mvars := drec.mvars;
        nvars := List( mvars, v -> Difference( all, v ) );
        Info( InfoIBNP, 2, "mvars = ", mvars );
        Info( InfoIBNP, 2, "nvars = ", nvars );
        ## construct the prolongations
        prolong := [ ];
        for i in [ 1..nbasis ] do
            for j in nvars[i] do
                Add( prolong, genA[j]*basis[i] );
            od;
        od;
        Sort( prolong, ordfn );
        Info( InfoIBNP, 1, "prolongations = ", prolong );
        npro := Length( prolong ); 
        found := false;
        for i in [1..npro] do
            u := prolong[i];
            v := IPolyReduceCP( A, u, drec, ord );
            Info( InfoIBNP, 2, "u = ", u, ",  v = ", v );
            if ( v <> z ) then 
                found := true; 
                Add( basis, v );
                Info( InfoIBNP, 2, "adding ", v );
                if ( pl > 0 ) and 
                   ( Length(basis) > InvolutiveAbortLimit ) then
                      return fail;
                fi;
                drec := DivisionRecordCP( A, basis, ord );
            fi;
        od;
        if not found then
            done := true;
        fi;
    od;
    return DivisionRecordCP( A, basis, ord);
end );

#############################################################################
##
#E  involutive-cp.gi . . . . . . . . . . . . . . . . . . . . . . .  ends here
## 