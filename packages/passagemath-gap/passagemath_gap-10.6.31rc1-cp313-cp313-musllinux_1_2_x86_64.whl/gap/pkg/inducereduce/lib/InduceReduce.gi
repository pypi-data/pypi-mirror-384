#
# InduceReduce.gi        The InduceReduce package         Jonathan Gruber
#
# Implementations
#
# Copyright (C) 2018     Jonathan Gruber
#
#############################################################################
##
## Initialize the options record with the default values.
## The meaning of the components is as follows:
##
## DoCyclicFirst
##
## a boolean variable that tells the program to induce the charaters of all
## cyclic subgroups before proceeding to the non-cyclic elementary subgroups
##
## DoCyclicLast
##
## a boolean variable that tells the program to induce the charaters of all
## cyclic subgroups before proceeding to the non-cyclic elementary subgroups
##
## LLLOffset
##
## an integer variable that tells the program to postpone the first LLL
## reduction until the characters of the LLLOffset-th elementary subgroup
## have been induced.
##
## DELTA
##
## a rational that specifies the parameter delta for the LLL reduction
##
CTUngerDefaultOptions := rec(
    DoCyclicFirst := false,
    DoCyclicLast := false,
    LLLOffset := 0,
    Delta := 3/4
);

#############################################################################
##
#V IndRed
##
## a record containing subfunctions of CharacterTableUnger
##
InstallValue( IndRed , rec(

#############################################################################
##
#F IndRed.Init( <G> )
##
## Initialization of the algorithm, returns a record which contains all
## relevant data concerning the group G
##
    Init:=function(G)
    local GR,i;

        GR:=rec();

        GR.G:=G;   #  The group itself
        GR.C:=CharacterTable(G);  # the character table (without irreducible characters)
        GR.n:= Size(G);  # the order of G
        GR.classes:=ShallowCopy(ConjugacyClasses(GR.C)); # the conjugacy classes (mutable)
        GR.k:=Size(GR.classes); # number of conjugacy classes
        GR.classreps:=List(GR.classes,Representative); # class representatives
        GR.orders:=List(GR.classreps, Order); # element orders

        Info(InfoCTUnger, 1, "Induce/Restrict: group with ",
             Length(GR.orders), " conjugacy classes.");
        Info(InfoCTUnger, 2, "Induce/Restrict: orders of class reps: ",
             GR.orders);

        GR.perm:=Sortex(GR.orders,function(x,y) return y<x; end);
            # sort by decreasing order of representatives
        GR.classes:=Permuted(GR.classes,GR.perm); # adjust the order of classes and classreps
        GR.classreps:=Permuted(GR.classreps,GR.perm);
        GR.ccsizes:=List(GR.classes,Size); # sizes of conjugacy classes
        GR.OrderPrimes:=List(GR.orders,PrimeDivisors);
            # primes dividing the orders of class representatives
        GR.CentralizerPrimes:=List([1..GR.k],
            x-> Difference( PrimeDivisors(GR.n/GR.ccsizes[x]), GR.OrderPrimes[x] ) );
            # primes dividing the order of the centralizer, but not the order of the element
        GR.InduceCyclic:=ListWithIdenticalEntries(GR.k,true);
            # the characters of the corresponding cyclic groups still need to be induced
        GR.NumberOfCyclic:=GR.k; # number of cyclic groups whose characters need to be induced
        GR.NumberOfPrimes:=Sum(GR.CentralizerPrimes,Size);
            # number of primes for elementary subgroups not used so far
        GR.ordersPos:=[];
            # create a non-dense list such that ordersPos[i] is the position of the first class of elements of order i
        for i in [1..GR.k] do
            if not IsBound(GR.ordersPos[GR.orders[i]]) then
                GR.ordersPos[GR.orders[i]]:=i;
            fi;
        od;
        GR.Ir:=[ Zero([1..GR.k])+1 ]; # initialize Irr(G) with the trivial character:
        GR.B:=[];  # B as an empty list
        GR.Gram:=[]; # Gram empty
        GR.IndexCyc:=0;
        # position of the cyclic group curretly used in the list of class representatives
        GR.m:=0; # positions from which on characters are not reduced so far
        GR.centralizers:=[];  # centralizers and powermaps computed so far
        GR.powermaps:=[];
        return GR;
    end,

#############################################################################
##
#F IndRed.GroupTools
##
## a record with different functions used for the algorithm
##
    GroupTools:=rec(

        # find the position of the conjugacy class containing g in GR.classes ,
        # ord is the order of g
        FindClass:= function(GR,h,ord)
        local j;
            for j in [GR.ordersPos[ord]..GR.k] do
                if GR.orders[j] <> ord then
                    break;
                fi;
                if h=GR.classreps[j] then
                # first check if h actually equals one of the class representatives
                    return j;
                fi;
            od;
            for j in [GR.ordersPos[ord]..GR.k] do
                if h in GR.classes[j] then
                    return j;
                fi;
            od;
        end,

        ## compute powermap of l-th class representative and add it to GR
        PowMap:= function(GR,l)
        local h, res, i, ord;
            if GR.orders[l]=1 then GR.powermaps[l]:=[l]; fi;
            res:=[IndRed.GroupTools.FindClass(GR,One(GR.G),1),l];
            h:=GR.classreps[l]^2;
            for i in [2..GR.orders[l]-1] do
                ord:=GR.orders[l]/GcdInt(GR.orders[l],i);

                Add(res, IndRed.GroupTools.FindClass(GR,h,ord));

                h:=h*GR.classreps[l];
            od;
            GR.powermaps[l]:=res;
        end,

        ## Compute character table of cyclic group as matrix
        Vandermonde:= function(GR)
        local n, i, j, M;
            n:=GR.orders[GR.IndexCyc];
            M:=NullMat(n,n);
            for i in [0..n-1] do
                for j in [0..n-1] do
                    M[i+1,j+1]:=E(n)^(i*j);
                od;
            od;
            return M;
        end,

        # conjugacy class representatives of cyclic group corresponding to
        # the ordering of columns in Vandermonde
        ClassesCyclic:=function(GR)
        local res, h;
            res:=[Identity(GR.G)];
            h:=GR.Elementary.z;
            while not IsOne(h) do
                Add(res,h);
                h:=h*GR.Elementary.z;
            od;
            return res;
        end,
    ),

#############################################################################
##
#F IndRed.ReduceTools
##
## a record with different functions required for lattice reduction
##
    ReduceTools:=rec(

        # inner product of class functions x and y
        ip:= function(GR,x,y)
            local res, i;
            res := 0;
            for i in [1..GR.k] do
              if x[i] <> 0 and y[i] <> 0 then
                res := res + x[i]*ComplexConjugate(y[i])*GR.ccsizes[i];
              fi;
            od;
            return res/GR.n;
        end,

        # inner product of class functions x and y with few entries
        # one of them has all non-zero entries in GR.Elementary.FusedClasses
        ipSparse:= function(GR,x,y)
            return Sum(GR.Elementary.FusedClasses,
                i->x[i]*ComplexConjugate(y[i])*GR.ccsizes[i])/GR.n;
        end,

        # reduce new induced characters by the irreducibles found so far
        redsparse:=function(GR)
        local mat,pos;
            if GR.m+1>Size(GR.B) then return; fi;
            pos:=[GR.m+1..Size(GR.B)];
            mat:=List( pos, x->List(GR.Ir, y -> IndRed.ReduceTools.ipSparse(GR,GR.B[x],y) ) );
            GR.B{pos}:=GR.B{pos}-mat*GR.Ir;
        end,

        # extend the gram matrix with the scalar products of the new characters
        GramMatrixGR:=function(GR)
        local i,j,mat,b;
            b:=Size(GR.B);
            mat:=NullMat(b,b);
            mat{[1..GR.m]}{[1..GR.m]}:=GR.Gram;
            for i in [GR.m+1..b] do
                for j in [1..i] do
                    mat[i,j]:=IndRed.ReduceTools.ip(GR,GR.B[i],GR.B[j]);
                    mat[j,i]:=mat[i,j];
                od;
            od;
            GR.Gram:=mat;
        end,

    ),

#############################################################################
##
#F IndRed.FindElementary( <GR> )
##
## finds the next elementary subgroup and puts it in the component Elementary
## of the record GR.
##
    FindElementary:=function(GR,Opt)
    local Elementary;
        Elementary:=rec();
        while true do
            GR.IndexCyc:=GR.IndexCyc+1; # run over the conjugacy classes
            if GR.IndexCyc>GR.k then GR.IndexCyc:=1; fi;
            if not IsEmpty(GR.CentralizerPrimes[GR.IndexCyc]) then
                # search for a prime that has not been used yet
                Elementary.isCyclic:=false;
                Elementary.z:=GR.classreps[GR.IndexCyc];
                Elementary.p:=Random(GR.CentralizerPrimes[GR.IndexCyc]);
                    # choose a random prime for that conjugacy class
                RemoveSet(GR.CentralizerPrimes[GR.IndexCyc], Elementary.p);
                GR.NumberOfPrimes:=GR.NumberOfPrimes-1;
                if not IsBound(GR.centralizers[GR.IndexCyc]) then
                    # compute the centralizer, if not done already
                    GR.centralizers[GR.IndexCyc]:=Centralizer(GR.G,Elementary.z);
                fi;
                Elementary.P:=SylowSubgroup(GR.centralizers[GR.IndexCyc],Elementary.p);
                GR.Elementary:=Elementary;
                break;
            elif GR.InduceCyclic[GR.IndexCyc] and
                (not Opt.DoCyclicLast or GR.NumberOfPrimes<=0) then
                # if there are no primes left for this class, induce from cyclic group
                # if Opt.DoCyclicLast=true: only induce from cyclic groups
                # when all primes have been used
                Elementary.isCyclic:=true;
                Elementary.z:=GR.classreps[GR.IndexCyc];
                GR.InduceCyclic[GR.IndexCyc]:=false;
                GR.NumberOfCyclic:=GR.NumberOfCyclic-1;
                GR.Elementary:=Elementary;
                break;
            fi;
        od;
        return;
    end ,

#############################################################################
##
#F IndRed.InitElementary( <GR> , <TR> )
##
## initialize data concerning the elementary subgroups and exclude its
## subgroups and their conjugates from the computations yet to come.
##
    InitElementary:=function(GR,TR)
        local i,j,i1,j1,p,temp,powermap,pm;
        if GR.Elementary.isCyclic then
            GR.Elementary.n:=GR.orders[GR.IndexCyc]; # order of the elementary group
            GR.Elementary.k:=GR.Elementary.n; # number of conjugacy classes
            GR.Elementary.ccsizes:=ListWithIdenticalEntries(GR.Elementary.k,1); # class sizes
            if not IsBound(GR.powermaps[GR.IndexCyc]) then # if necessary, compute powermap
                TR.PowMap(GR,GR.IndexCyc);
            fi;
            powermap:=GR.powermaps[GR.IndexCyc];
            GR.Elementary.classfusion:=powermap;
                # class fusion equals power map for cyclic group
            GR.Elementary.classreps:=TR.ClassesCyclic(GR); # class representatives
            GR.Elementary.XE:=TR.Vandermonde(GR); # character table
        else
            GR.Elementary.n:=GR.orders[GR.IndexCyc]*Size(GR.Elementary.P); # order
            GR.Elementary.ctblP:=CharacterTable(GR.Elementary.P);
                # character table of p-group
            GR.Elementary.classrepsP:=List(ConjugacyClasses(GR.Elementary.ctblP),
                Representative);
                #classes of p-group in corresponding order
            GR.Elementary.ccsizesP:=List(ConjugacyClasses(GR.Elementary.ctblP),Size);                 # class sizes p-group
            GR.Elementary.kP:=Size(GR.Elementary.classrepsP); # number of classes of p-group
            GR.Elementary.classrepsZ:=TR.ClassesCyclic(GR);
                # class representatives cyclic group
            GR.Elementary.kZ:=GR.orders[GR.IndexCyc]; # number of classes cyclic group
            if not IsBound(GR.powermaps[GR.IndexCyc]) then # if necessary, compute powermap
                TR.PowMap(GR,GR.IndexCyc);
            fi;
            powermap:=GR.powermaps[GR.IndexCyc];
            GR.Elementary.k:=GR.Elementary.kP*GR.Elementary.kZ;
                # number of classes elementary group
            GR.Elementary.classreps:=[]; # compute the class representatives
            GR.Elementary.ccsizes:=[]; # and the class sizes
            for i in [1..GR.Elementary.kP] do
                for j in [1..GR.Elementary.kZ] do
                    Add(GR.Elementary.classreps,
                        GR.Elementary.classrepsP[i]*GR.Elementary.classrepsZ[j]);
                    Add(GR.Elementary.ccsizes,GR.Elementary.ccsizesP[i]);
                od;
            od;
            GR.Elementary.classfusion:=List(GR.Elementary.classreps, r -> TR.FindClass(GR, r, Order(r)));
                # compute the fusion of conjugacy classes of the elementary group
                # to conjugacy classes of G
            GR.Elementary.XP:=Irr(GR.Elementary.ctblP);
                # irreducible characters of the p-group
            GR.Elementary.XZ:=TR.Vandermonde(GR); # character table of the cycic group
            GR.Elementary.XE:=[]; # compute character table of the elementary group
            for i in [1..GR.Elementary.kP] do
                for j in [1..GR.Elementary.kZ] do
                    temp:=[];
                    for i1 in [1..GR.Elementary.kP] do
                        for j1 in [1..GR.Elementary.kZ] do
                            Add(temp,GR.Elementary.XP[i][i1]*GR.Elementary.XZ[j][j1]);
                        od;
                    od;
                    Add(GR.Elementary.XE,temp);
                od;
            od;
        fi;
        GR.Elementary.FusedClasses:=Set(GR.Elementary.classfusion);
            # positions of classes of G which contain classes of the elementary group
        for i in GR.Elementary.FusedClasses do # eliminate some elementary subgroups:
            if GR.InduceCyclic[i] then # the cyclic subgroups of the elementary groups
                GR.InduceCyclic[i]:=false;
                GR.NumberOfCyclic:=GR.NumberOfCyclic-1;
            fi;
            if GR.Elementary.isCyclic then
                # some elementary groups contained in the cyclic group
                for p in GR.CentralizerPrimes[i] do
                    if PValuation(GR.n/GR.ccsizes[i],p)=PValuation(GR.orders[GR.IndexCyc],p) then
                        RemoveSet(GR.CentralizerPrimes[i],p);
                        GR.NumberOfPrimes:=GR.NumberOfPrimes-1;
                    fi;
                od;
            fi;
        od;
        if not GR.Elementary.isCyclic then
            p:=GR.Elementary.p;
            for i in Set(powermap) do
                # elementary subgroups, where the cyclic part is generated
                # by a power of GR.Elementary.z and the p-groups coincide
                if PValuation(GR.n/GR.ccsizes[i],p)=PValuation(GR.n/GR.ccsizes[GR.IndexCyc],p) and
                        p in GR.CentralizerPrimes[i] then
                    RemoveSet(GR.CentralizerPrimes[i],p);
                    GR.NumberOfPrimes:=GR.NumberOfPrimes-1;
                fi;
            od;
        fi;
        for i in [0..GR.orders[GR.IndexCyc]-1] do
            # derive the powermaps of powers of GR.Elementary.z
            pm:=powermap[i+1];
            if not IsBound(GR.powermaps[pm]) then
                GR.powermaps[pm]:=[];
                for j in [0..GR.orders[pm]-1] do
                    Add(GR.powermaps[pm], powermap[ i*j mod GR.orders[GR.IndexCyc] +1 ]);
                od;
            fi;
        od;
        return;
    end ,

#############################################################################
##
#F IndRed.InduceCyc( <GR> )
##
## induce characters from all cyclic subgroups
##
    InduceCyc:=function(GR)
    local ords, inds;
        GR.Elementary:=rec();
        ords := ShallowCopy(OrdersClassRepresentatives(GR.C));
        inds := [1..NrConjugacyClasses(GR.C)];
        SortParallel(ords, inds, function(x,y) return x>y; end);
        GR.Elementary.FusedClasses := [1..GR.k];
        Append(GR.B, List(InducedCyclic(GR.C,inds,"all"), ch-> Permuted(ch, GR.perm)));
        return;
    end ,

#############################################################################
##
#F IndRed.Induce( <GR> )
##
## Induce all irreducible characters of the elementary subgroup in
## GR.Elementary to the group GR.G and add them to GR.B
##
    Induce:=function(GR)
    local mat, i, j, cfj;
        mat:=NullMat(GR.Elementary.k,GR.k);
        for i in [1..GR.Elementary.k] do
            for j in [1..GR.Elementary.k] do
                cfj := GR.Elementary.classfusion[j];
                mat[i,cfj]:=mat[i,cfj] + ( (GR.n/GR.ccsizes[cfj]) /
                    (GR.Elementary.n/GR.Elementary.ccsizes[j])*GR.Elementary.XE[i][j] );
            od;
        od;
        mat:=Set(mat); # remove duplicates
        Append(GR.B,mat);
        return;
    end ,

#############################################################################
#
# IndRed.Reduce( <GR>, ><RedTR> )
#
# reduce the induced characters by the irreducibles found so far and do LLL
# lattice reduction
#
    Reduce:=function(GR,RedTR,Opt)
    local mat,temp,ind,I,i;
        RedTR.redsparse(GR); #reduce new characters by all irreducibles
        RedTR.GramMatrixGR(GR); # update the gram matrix
        if Opt.LLLOffset>0 then
            GR.m:=Size(GR.Gram);
        else
            temp:=LLLReducedGramMat(GR.Gram,Opt.Delta); # LLL reduction on gram matrix
            GR.Gram:=temp.remainder;
            GR.B:=temp.transformation*GR.B;
            temp:=[];
            ind:=[];
            GR.m:=Size(GR.Gram);
            for i in [1..GR.m] do
                if GR.Gram[i,i]=1 then
                    Add(temp,i); # find positions of characters of norm 1
                else
                    Add(ind,i);
                fi;
            od;
            if Size(temp)=0 then
                Info(InfoCTUnger, 2, "Reduce: |Irr| = ", Length(GR.Ir),
                    ", dim = ", Length(GR.Ir)+Length(GR.Gram),
                    ", det(G) = ", DeterminantMat(GR.Gram));
                return;
            fi;
            I:=GR.B{temp}; # irreducible characters in B (up to sign)
            if Size(ind)=0 then
                Append(GR.Ir,I);
                GR.Gram:=[];
                Info(InfoCTUnger, 2, "Reduce: |Irr| = ", Length(GR.Ir));
                return;
            fi;
            for i in Reversed(temp) do
                Remove(GR.B,i); # remove irreducible characters from B
            od;
            mat:=GR.Gram{ind}{temp};
            GR.Gram:=GR.Gram{ind}{ind}-mat*TransposedMat(mat);
            GR.m:=Size(ind);
            GR.B:=GR.B-mat*I;
            Append(GR.Ir,Set(I)); # add the new irreducible characters to I
            Info(InfoCTUnger, 2, "Reduce: |Irr| = ", Length(GR.Ir),
                ", dim = ", Length(GR.Ir)+Length(GR.Gram),
                ", det(G) = ", DeterminantMat(GR.Gram));
        fi;
        return;
    end ,

#############################################################################
##
#F IndRed.tinI( <GR> )
##
## adjusts the signs of the characters and permutes them to the right
## ordering of conjugacy classes
##
    tinI:=function(GR)
    local irr,i,perm;

        for i in [1..GR.k] do # adjust the signs
            if GR.Ir[i][GR.ordersPos[1]]<0 then
                GR.Ir[i]:=-GR.Ir[i];
            fi;
        od;
        irr:=[];
        for i in [1..GR.k] do
            # permute irreducible characters back to the order of classes in GR.C
            GR.Ir[i]:=Permuted(GR.Ir[i],Inverse(GR.perm));
            irr[i]:=Character(GR.C,GR.Ir[i]);
        od;
        GR.Ir:=irr;
        return;
    end ));
## end of the record IndRed #################################################

#############################################################################
##
#F InduceReduce(GR)
##
## computes the irreducible characters of the group GR.G (upto sign) and puts
## them in the component GR.Ir of GR, returns GR.Ir
##
InstallGlobalFunction( InduceReduce,
function(GR,Opt)
local TR, RedTR, H, ccsizesH, temp, it;

    TR:=IndRed.GroupTools; # get group tools and reduce tools
    RedTR:=IndRed.ReduceTools;

    if Opt.DoCyclicFirst = true then # if option Opt.DoCyclicFirst is set,
        # induce from all cyclic groups first and reduce

        Info(InfoCTUnger, 2, "Induce: from cyclic subgroups");

        IndRed.InduceCyc(GR);
        IndRed.Reduce(GR,RedTR,Opt);
        GR.InduceCyclic:=ListWithIdenticalEntries(GR.k,false);
        GR.NumberOfCyclic:=0;
    fi;

    if Size(GR.Ir)>=GR.k then
        return GR.Ir;
    fi;


    while Size(GR.Ir)<GR.k and not (GR.NumberOfPrimes=0 and GR.NumberOfCyclic=0) do
        # if number of irr. characters=number of conjugacy classes,
        # all irr. characters have been found.

        Opt.LLLOffset:=Opt.LLLOffset-1;
        # Opt.LLLOffset postpones the first LLL lattice reduction

        IndRed.FindElementary(GR,Opt); # find elementary subgroup

        IndRed.InitElementary(GR,TR); # determine information needed about elementary subgroup


        Info(InfoCTUnger, 1, "Induce/Restrict: Trying [|Z|, |P|, k(E)] = ",
            [ GR.orders[GR.IndexCyc],
                GR.Elementary.n/GR.orders[GR.IndexCyc], GR.Elementary.k ]);

        IndRed.Induce(GR); # append induced characters to GR.B

        IndRed.Reduce(GR,RedTR,Opt); # reduce GR.B by GR.Ir and do lattice reduction
    od;

    if Size(GR.Ir)>=GR.k then
        return GR.Ir;
    else
        Opt.Delta:=1;
        # if there are still characters missing, do on last LLL reduction with Opt.Delta:=1
        Opt.LLLOffset:=0;
        IndRed.Reduce(GR,RedTR,Opt);
        return GR.Ir;
    fi;

end );


#############################################################################
##
#M  UngerRecord( <G> )
##
##  Compute a record that contains data used by Unger's algorithm.
##
InstallMethod( UngerRecord,
    [ "IsGroup" ],
    IndRed.Init );


#############################################################################
##
#M  IrrUnger( <G>[, <options>] )  . . . . . . . . . .  call Unger's algorithm
##
##  Compute the irreducible characters of <G>, using Unger's algorithm.
##
InstallMethod( IrrUnger,
    [ "IsGroup" ],
    G -> IrrUnger( G, rec() ) );

InstallMethod( IrrUnger,
    [ "IsGroup", "IsRecord" ],
    function( G, Options )
    local t, GR, Opt;

    GR:= UngerRecord( G );
    t:= GR.C;

    Opt:= ShallowCopy( CTUngerDefaultOptions );
    if IsBound( Options.DoCyclicFirst ) and IsBool( Options.DoCyclicFirst ) then
      Opt.DoCyclicFirst:= Options.DoCyclicFirst;
    fi;
    if IsBound( Options.DoCyclicLast ) and IsBool( Options.DoCyclicLast ) then
      Opt.DoCyclicLast:= Options.DoCyclicLast;
    fi;
    if IsBound( Options.LLLOffset ) and IsInt( Options.LLLOffset ) then
      Opt.LLLOffset:= Options.LLLOffset;
    fi;
    if IsBound( Options.Delta ) and IsRat( Options.Delta )
       and 1/4 < Options.Delta and Options.Delta <= 1 then
      Opt.Delta:= Options.Delta;
    fi;

    InduceReduce( GR, Opt ); # do the induce-reduce algorithm

    IndRed.tinI( GR ); # adjusts the sorting of vectors in `GR.Ir`
    return List( GR.Ir, x -> Character( t, x ) );
    end );

#############################################################################
##
#M  Irr( <G>, 0 ) . . . . . . . . . . . . . . . . . .  call Unger's algorithm
##
InstallMethod( Irr,
  "for a group and zero, use Unger's algorithm",
  [ IsGroup, IsZeroCyc ],
  function( G, zero )
  local t, irr;

  t:= OrdinaryCharacterTable( G );
  irr:= IrrUnger( G );
  SetIrr( t, irr );
  SetInfoText( t, "origin: Unger's algorithm" );
  return irr;
  end );


#############################################################################
##
#F CharacterTableUnger( <G>[, <Options>] )
##
##  Return a character table of <G> whose irreducible characters are computed
##  using Unger's algorithm.
##
InstallGlobalFunction( CharacterTableUnger, function(G, Options...)
    local GR, T;

    if Length( Options ) = 0 then
      IrrUnger( G );
    else
      IrrUnger( G, Options[1] );
    fi;
    GR:= UngerRecord( G );

    # Create a character table independent of the one stored in `G`.
    T:=rec();
    T.UnderlyingCharacteristic:=0;
    T.NrConjugacyClasses:=GR.k;
    T.ConjugacyClasses:=ConjugacyClasses(GR.C);
    T.Size:=GR.n;
    T.OrdersClassRepresentatives:=Permuted(GR.orders,Inverse(GR.perm));
    T.SizesCentralizers:=Permuted(List(GR.ccsizes,x->GR.n/x),Inverse(GR.perm));
    T.Irr:=GR.Ir;
    T.UnderlyingGroup:=UnderlyingGroup(GR.C);
    T.IdentificationOfConjugacyClasses:=IdentificationOfConjugacyClasses(GR.C);
    T.InfoText:="Computed using Unger's induce-reduce algorithm";
    return ConvertToCharacterTableNC( T );
end );
