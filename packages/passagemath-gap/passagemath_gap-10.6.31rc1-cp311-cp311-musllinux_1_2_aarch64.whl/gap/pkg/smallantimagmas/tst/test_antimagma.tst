gap> START_TEST("test_antimagma.tst");

gap> ForAll([2 .. 3], n -> ForAll(Combinations([1 .. NrSmallAntimagmas(n)], 2), c -> not IsMagmaIsomorphic(SmallAntimagma(n, c[1]), SmallAntimagma(n, c[2]))));
true

gap> List(Cartesian(AllSmallAntimagmas(2), AllSmallAntimagmas(3)), c -> MagmaIsomorphism(c[1], c[2]));
[ fail, fail, fail, fail, fail, fail, fail, fail, fail, fail, fail, fail, fail, fail, fail, fail, fail, fail, fail, fail ]

gap> ForAll(AllSmallAntimagmas([2 .. 3]), M -> IsEmpty(Idempotents(M)));
true

gap> ForAll(AllSmallAntimagmas([2 .. 3]), M -> IsEmpty(Center(M)));
true

gap> ForAll(AllSmallAntimagmas([2 .. 3]), M -> IsAntiassociative(M));
true

gap> ForAll(ReallyAllSmallAntimagmas([2 .. 3]), M -> IdSmallAntimagma(M)[1] = Size(M));
true

gap> ForAll(ReallyAllSmallAntimagmas([2 .. 3]), M -> IdSmallAntimagma(M)[2] <= NrSmallAntimagmas(Size(M)));
true

gap> STOP_TEST("test_antimagma.tst");
