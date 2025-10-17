gap> START_TEST("smallantimagmas: test_utils.tst");

gap> ForAll(AllSmallAntimagmas([2 .. 3]), M -> ForAll(M, m -> LeftPower(m, 1) = m));
true

gap> ForAll(AllSmallAntimagmas([2 .. 3]), M -> ForAll(M, m -> RightPower(m, 1) = m));
true

gap> ForAll(AllSmallAntimagmas([2 .. 3]), M -> ForAll(M, m -> LeftPower(m, 2) = RightPower(m, 2)));
true

gap> AntimagmaGeneratorPossibleDiagonals(2);  
[[2, 1 ]]

gap> AntimagmaGeneratorPossibleDiagonals(3);
[ 
    [ 2, 1, 1 ], [ 2, 1, 2 ], 
    [ 2, 3, 1 ], [ 2, 3, 2 ], 
    [ 3, 1, 1 ], [ 3, 1, 2 ], 
    [ 3, 3, 1 ], [ 3, 3, 2 ] 
]

gap> AntimagmaGeneratorPossibleDiagonals(4);
[ 
    [ 2, 1, 1, 1 ], [ 2, 1, 1, 2 ], [ 2, 1, 1, 3 ], 
    [ 2, 1, 2, 1 ], [ 2, 1, 2, 2 ], [ 2, 1, 2, 3 ], 
    [ 2, 1, 4, 1 ], [ 2, 1, 4, 2 ], [ 2, 1, 4, 3 ], 
    [ 2, 3, 1, 1 ], [ 2, 3, 1, 2 ], [ 2, 3, 1, 3 ], 
    [ 2, 3, 2, 1 ], [ 2, 3, 2, 2 ], [ 2, 3, 2, 3 ], 
    [ 2, 3, 4, 1 ], [ 2, 3, 4, 2 ], [ 2, 3, 4, 3 ], 
    [ 2, 4, 1, 1 ], [ 2, 4, 1, 2 ], [ 2, 4, 1, 3 ], 
    [ 2, 4, 2, 1 ], [ 2, 4, 2, 2 ], [ 2, 4, 2, 3 ], 
    [ 2, 4, 4, 1 ], [ 2, 4, 4, 2 ], [ 2, 4, 4, 3 ], 
    [ 3, 1, 1, 1 ], [ 3, 1, 1, 2 ], [ 3, 1, 1, 3 ], 
    [ 3, 1, 2, 1 ], [ 3, 1, 2, 2 ], [ 3, 1, 2, 3 ], 
    [ 3, 1, 4, 1 ], [ 3, 1, 4, 2 ], [ 3, 1, 4, 3 ], 
    [ 3, 3, 1, 1 ], [ 3, 3, 1, 2 ], [ 3, 3, 1, 3 ], 
    [ 3, 3, 2, 1 ], [ 3, 3, 2, 2 ], [ 3, 3, 2, 3 ], 
    [ 3, 3, 4, 1 ], [ 3, 3, 4, 2 ], [ 3, 3, 4, 3 ], 
    [ 3, 4, 1, 1 ], [ 3, 4, 1, 2 ], [ 3, 4, 1, 3 ], 
    [ 3, 4, 2, 1 ], [ 3, 4, 2, 2 ], [ 3, 4, 2, 3 ], 
    [ 3, 4, 4, 1 ], [ 3, 4, 4, 2 ], [ 3, 4, 4, 3 ], 
    [ 4, 1, 1, 1 ], [ 4, 1, 1, 2 ], [ 4, 1, 1, 3 ], 
    [ 4, 1, 2, 1 ], [ 4, 1, 2, 2 ], [ 4, 1, 2, 3 ], 
    [ 4, 1, 4, 1 ], [ 4, 1, 4, 2 ], [ 4, 1, 4, 3 ], 
    [ 4, 3, 1, 1 ], [ 4, 3, 1, 2 ], [ 4, 3, 1, 3 ], 
    [ 4, 3, 2, 1 ], [ 4, 3, 2, 2 ], [ 4, 3, 2, 3 ], 
    [ 4, 3, 4, 1 ], [ 4, 3, 4, 2 ], [ 4, 3, 4, 3 ], 
    [ 4, 4, 1, 1 ], [ 4, 4, 1, 2 ], [ 4, 4, 1, 3 ], 
    [ 4, 4, 2, 1 ], [ 4, 4, 2, 2 ], [ 4, 4, 2, 3 ], 
    [ 4, 4, 4, 1 ], [ 4, 4, 4, 2 ], [ 4, 4, 4, 3 ] 
]

gap> UpToIsomorphism(AllSmallAntimagmas(3));
[ 
    <magma with 3 generators>, <magma with 3 generators>, <magma with 3 generators>, <magma with 3 generators>, <magma with 3 generators>,
    <magma with 3 generators>, <magma with 3 generators>, <magma with 3 generators>, <magma with 3 generators>, <magma with 3 generators>
]

gap> UpToIsomorphism(ReallyAllSmallAntimagmas(3));
[ 
    <magma with 3 generators>, <magma with 3 generators>, <magma with 3 generators>, <magma with 3 generators>, <magma with 3 generators>,
    <magma with 3 generators>, <magma with 3 generators>, <magma with 3 generators>, <magma with 3 generators>, <magma with 3 generators>
]

gap> STOP_TEST("test_utils.tst");

