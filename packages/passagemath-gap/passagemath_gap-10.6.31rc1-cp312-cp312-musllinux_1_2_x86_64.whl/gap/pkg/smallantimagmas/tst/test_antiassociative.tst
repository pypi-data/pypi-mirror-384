gap> START_TEST("test_antiassociative.tst");

gap> IsAntiassociative(MagmaByMultiplicationTable([[1]]));
false

gap> IsAntiassociative(MagmaByMultiplicationTable([[2, 2], [2, 2]]));
false

gap> IsAntiassociative(MagmaByMultiplicationTable([[2, 1], [2, 1]]));
true

gap> STOP_TEST("test_antiassociative.tst");