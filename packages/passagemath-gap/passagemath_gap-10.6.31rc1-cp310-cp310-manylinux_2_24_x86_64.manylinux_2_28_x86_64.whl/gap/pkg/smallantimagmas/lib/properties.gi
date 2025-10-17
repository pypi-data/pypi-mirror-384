InstallGlobalFunction(AllSubmagmas,
    function(M)
        local result, c, T;
        result := [];
        for c in Combinations(GeneratorsOfMagma(M)) do
            T := Submagma(M, c);
            if not ForAny(result, N -> IsMagmaIsomorphic(N, T)) and Size(T) > 0 then
                Add(result, T);
            fi;
        od;
        return result;
end);

InstallMethod(DiagonalOfMultiplicationTable, "for a magma", [IsMagma],
    function(M)
        return DiagonalOfMatrix(MultiplicationTable(M));
end);

InstallMethod(AssociativityIndex, "for a magma", [IsMagma],
    function(M)
        return Size(Filtered(EnumeratorOfTuples(M, 3), t -> (t[1] * t[2]) * t[3] = t[1] * (t[2] * t[3])));
end);

InstallMethod(CommutativityIndex, "for a magma", [IsMagma],
    function(M)
        return Size(Filtered(Combinations(Elements(M), 2), m -> m[1] * m[2] = m[2] * m[1]));
end);

InstallMethod(AnticommutativityIndex, "for a magma", [IsMagma],
    function(M)
        return ((Binomial(Size(M), 2)) - CommutativityIndex(M));
end);

InstallMethod(SquaresIndex, "for a magma", [IsMagma],
    function(M)
        return Size(Set(M, m -> m ^ 2));
end);

InstallMethod(IsAntiassociative, "for a magma", [IsMagma],
    function(M)
        local x;
        for x in IteratorOfTuples(M, 3) do
            if (x[1] * (x[2] * x[3])) = ((x[1] * x[2]) * x[3]) then
                return false;
            fi;
        od;
        return true;
end);

InstallGlobalFunction(TransposedMagma,
    function(M)
        return MagmaByMultiplicationTable(TransposedMat(MultiplicationTable(M)));
end);

InstallGlobalFunction(MagmaIsomorphismInvariantsMatch,
    function(M, N)
        local invariants;
        invariants := [
            Size,
            IsLeftCancellative,
            IsRightCancellative,
            IsLeftDistributive,
            IsRightDistributive,
            IsLeftFPFInducted,
            IsRightFPFInducted,
            CommutativityIndex,
            AnticommutativityIndex,
            SquaresIndex,
            LeftOrdersOfElements,
            RightOrdersOfElements,
            IsLeftCyclic,
            IsRightCyclic];
        return ForAll(invariants, f -> f(M) = f(N));
end);

InstallMethod(MagmaIsomorphism, "for two magmas", true, [IsMagma, IsMagma], 0,
    function(M, N)
        local psi, n, p, m, elms;

        if not MagmaIsomorphismInvariantsMatch(M, N) then
            return fail;
        fi;

        n := Size(M);
        m := Elements(M);

        for p in PermutationsList(Elements(N)) do
            elms := List([1 .. n], i -> DirectProductElement([m[i], p[i]]));

            psi := GeneralMappingByElements(M, N, elms);

            if RespectsMultiplication(psi) then
                return psi;
            fi;
        od;
        return fail;
end);

InstallMethod(MagmaAntiisomorphism, "for two magmas", true, [IsMagma, IsMagma], 0,
    function(M, N)
        local psi, n, p, m, elms;

        if Size(M) <> Size(N) then
            return fail;
        fi;

        n := Size(M);
        m := Elements(M);

        for p in PermutationsList(Elements(N)) do
            elms := List([1 .. n], i -> DirectProductElement([m[i], p[i]]));
            psi := GeneralMappingByElements(M, N, elms);

            if ForAll(EnumeratorOfTuples(m, 2), t -> psi(t[1] * t[2]) = psi(t[2]) * psi(t[1])) then
                return psi;
            fi;
        od;
        return fail;
end);

InstallGlobalFunction(IsMagmaIsomorphic,
    function(M, N)
        if MagmaIsomorphism(M, N) <> fail then
            return true;
        fi;
        return false;
end);

InstallGlobalFunction(IsMagmaAntiisomorphic,
    function(M, N)
        if MagmaAntiisomorphism(M, N) <> fail then
            return true;
        fi;
        return false;
end);

InstallGlobalFunction(LeftPower,
    function(m, k)
        local result;

        if (not IsInt(k)) or (k < 1) then
            Error("SmallAntimagmas: ", "<id> must be an integer");
        fi;

        result := m;
        while k > 1 do
            result := m * result;
            k := k - 1;
        od;
        return result;
end);

InstallGlobalFunction(RightPower,
    function(m, k)
        local result;

        if (not IsInt(k)) or (k < 1) then
            Error("SmallAntimagmas: ", "<id> must be an integer");
        fi;

        result := m;
        while k > 1 do
            result := result * m;
            k := k - 1;
        od;
        return result;
end);

InstallMethod(LeftOrder, "for a left-multiplicable element", [IsExtLElement],
    function(m)
        local temporary, next;
        temporary := [m * m];

        next := m * Last(temporary);
        while not (next in temporary) do
            Add(temporary, next);
            next := m * Last(temporary);
        od;

        if m = Last(temporary) then
            return Size(temporary);
        fi;
        return infinity;
end);

InstallMethod(RightOrder, "for a right-multiplicable element", [IsExtRElement],
    function(m)
        local temporary, next;
        temporary := [m * m];

        next := Last(temporary) * m;
        while not (next in temporary) do
            Add(temporary, next);
            next := Last(temporary) * m;
        od;

        if m = Last(temporary) then
            return Size(temporary);
        fi;
        return infinity;
end);

InstallMethod(LeftOrdersOfElements, "for a magma", [IsMagma],
    function(M)
        return Collected(List(M, m -> LeftOrder(m)));
end);

InstallMethod(RightOrdersOfElements, "for a magma", [IsMagma],
    function(M)
        return Collected(List(M, m -> RightOrder(m)));
end);

InstallMethod(IsLeftCyclic, "for a magma", [IsMagma],
    function(M)
        return ForAny(List(M), m -> LeftOrder(m) = Size(M));
end);

InstallMethod(IsRightCyclic, "for a magma", [IsMagma],
    function(M)
        return ForAny(List(M), m -> RightOrder(m) = Size(M));
end);

InstallMethod(IsLeftCancellative, "for a magma", [IsMagma],
    function(M)
        return ForAll(Filtered(EnumeratorOfTuples(M, 3), m -> m[3] * m[1] = m[3] * m[2]), m -> m[1] = m[2]);
end);

InstallMethod(IsRightCancellative, "for a magma", [IsMagma],
    function(M)
        return IsLeftCancellative(TransposedMagma(M));
end);

InstallMethod(IsLeftDistributive, "for a magma", [IsMagma],
    function(M)
        return ForAll(EnumeratorOfTuples(M, 3), m -> m[1] * (m[2] * m[3]) = (m[1] * m[2]) * (m[1] * m[3]));
end);

InstallMethod(IsRightDistributive, "for a magma", [IsMagma],
    function(M)
        return IsLeftDistributive(TransposedMagma(M));
end);

InstallMethod(IsCancellative, "for a magma", [IsMagma],
    function(M)
        return IsLeftCancellative(M) and IsRightCancellative(M);
end);

InstallMethod(IsLeftFPFInducted, "for a magma", [IsMagma],
    function(M)
        return ForAll(M, m -> Size(Unique(m * Elements(M))) = 1 and First(Unique(m * Elements(M))) <> m);
end);

InstallMethod(IsRightFPFInducted, "for a magma", [IsMagma],
    function(M)
        return IsLeftFPFInducted(TransposedMagma(M));
end);

InstallMethod(IsLeftDerangementInducted, "for a magma", [IsMagma],
    function(M)
        return ForAny(PartitionsSet(Elements(M)), p ->
            ForAny(Derangements(p), d ->
                ForAll([1 .. Size(p)], i ->
                    ForAll(p[i], m -> IsSubset(d[i], Unique(m * Elements(M)))))));
end);

InstallMethod(IsRightDerangementInducted, "for a magma", [IsMagma],
    function(M)
        return IsLeftDerangementInducted(TransposedMagma(M));
end);

InstallMethod(IsLeftAlternative, "for a magma", [IsMagma],
    function(M)
        return ForAll(EnumeratorOfTuples(M, 2), c -> c[1] * (c[1] * c[2]) = (c[1] * c[1]) * c[2]);
end);

InstallMethod(IsRightAlternative, "for a magma", [IsMagma],
    function(M)
        return IsLeftAlternative(TransposedMagma(M));
end);
