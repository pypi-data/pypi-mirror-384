gap> START_TEST("test_isomorphism.tst");

gap> List([2, 3], n -> List(AllSmallAntimagmas(n), M -> Size(Filtered(ReallyAllSmallAntimagmas(n), N -> IsMagmaIsomorphic(M, N)))));
[ [ 1, 1 ], [ 6, 6, 6, 6, 6, 6, 6, 6, 2, 2 ] ]

gap> List([2, 3], n -> ForAll(List(AllSmallAntimagmas(n), M -> Size(Filtered(ReallyAllSmallAntimagmas(n), N -> IsMagmaIsomorphic(M, N)))), k -> (Order(SymmetricGroup(n)) mod k = 0)));
[ true, true ]

gap> List([2, 3], n -> Sum(List(AllSmallAntimagmas(n), M -> Size(Filtered(ReallyAllSmallAntimagmas(n), N -> IsMagmaIsomorphic(M, N))))) = ReallyNrSmallAntimagmas(n));
[ true, true ]

gap> STOP_TEST("test_isomorphism.tst");
