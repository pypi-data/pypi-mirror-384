InstallGlobalFunction(NrSmallAntimagmas,
    function(order)
    return Size(__SmallAntimagmaHelper.getSmallAntimagmaMetadata(order)());
end);

InstallGlobalFunction(SmallAntimagma,
    function(order, id)
        return MagmaByMultiplicationTable(
            __SmallAntimagmaHelper.MultiplicationTableReverse(__SmallAntimagmaHelper.getSmallAntimagmaMetadata(order)()[id]));
end);

InstallGlobalFunction(AllSmallAntimagmas,
    function(order)
        if IsList(order) and ForAll(order, o -> IsInt(o)) then
            return Flat(
                List(order, o -> List(__SmallAntimagmaHelper.getSmallAntimagmaMetadata(o)(),
                                    table -> MagmaByMultiplicationTable(
                                        __SmallAntimagmaHelper.MultiplicationTableReverse(table)))));
        elif IsInt(order) then
            return List(__SmallAntimagmaHelper.getSmallAntimagmaMetadata(order)(), table -> MagmaByMultiplicationTable(
                                        __SmallAntimagmaHelper.MultiplicationTableReverse(table)));
        fi;
end);

InstallMethod(IdSmallAntimagma, "for a magma", [IsMagma],
    function(M)
        local n;
        n := Size(M);
        return [n, First(Filtered([1 .. NrSmallAntimagmas(n)], index -> IsMagmaIsomorphic(M, SmallAntimagma(n, index))))];
end);

InstallGlobalFunction(OneSmallAntimagma,
    function(order)
        return SmallAntimagma(order, Random([1 .. NrSmallAntimagmas(order)]));
end);

InstallGlobalFunction(ReallyNrSmallAntimagmas,
    function(order)
        return Size(__SmallAntimagmaHelper.getAllSmallAntimagmaMetadata(order)());
end);

InstallGlobalFunction(ReallyAllSmallAntimagmas,
    function(order)
        if IsList(order) and ForAll(order, o -> IsInt(o)) then
            return Flat(
                List(order, o -> List(__SmallAntimagmaHelper.getAllSmallAntimagmaMetadata(o)(),
                                    table -> MagmaByMultiplicationTable(
                                        __SmallAntimagmaHelper.MultiplicationTableReverse(table)))));
        elif IsInt(order) then
            return List(__SmallAntimagmaHelper.getAllSmallAntimagmaMetadata(order)(),
                                    table -> MagmaByMultiplicationTable(
                                        __SmallAntimagmaHelper.MultiplicationTableReverse(table)));
        fi;
end);