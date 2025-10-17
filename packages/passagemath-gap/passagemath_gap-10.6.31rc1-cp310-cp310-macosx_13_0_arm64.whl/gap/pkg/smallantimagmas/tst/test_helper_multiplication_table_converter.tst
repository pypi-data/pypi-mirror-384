gap> START_TEST("test_helper_multiplicaton_table_converter.tst");

gap> List([1 .. 2], n -> List(EnumeratorOfTuples([1 .. n], n)));
[
    [
        [ 1 ] 
    ],
    [ 
        [ 1, 1 ], 
        [ 1, 2 ],
        [ 2, 1 ],
        [ 2, 2 ]
    ]
]

gap> ForAll([1 .. 5], n -> List(EnumeratorOfTuples([1 .. n], n)) = Tuples([1 .. n], n));
true

gap> ForAll([1 .. 5], n -> EnumeratorOfTuples([1 .. n], n) = SortedList(Tuples([1 .. n], n)));
true

gap> List(AllSmallAntimagmas([2 .. 3]), M -> __SmallAntimagmaHelper.MultiplicationTableConvert(MultiplicationTable(M)));
[ 
    [3, 3],
    [4, 1],
    [ 10, 10, 10 ],
    [ 10, 10, 19 ],
    [ 11, 17, 11 ],
    [ 10, 19, 10 ],
    [ 14, 1, 1 ],
    [ 14, 3, 14 ],
    [ 14, 7, 14 ],
    [ 14, 19, 14 ],
    [ 14, 27, 1 ],
    [ 16, 16, 16 ] 
]

gap> ForAll(AllSmallAntimagmas([2 .. 3]), M -> MultiplicationTable(M) = __SmallAntimagmaHelper.MultiplicationTableReverse(__SmallAntimagmaHelper.MultiplicationTableConvert(MultiplicationTable(M))));
true

gap> STOP_TEST("test_helper_multiplicaton_table_converter.tst");