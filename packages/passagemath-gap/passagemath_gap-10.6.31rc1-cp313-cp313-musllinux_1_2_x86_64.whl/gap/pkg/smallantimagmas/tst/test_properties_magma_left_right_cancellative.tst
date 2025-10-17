gap> START_TEST("test_properties_magma_left_right_cancellative.tst");

gap> ForAll(AllSmallGroups([2 .. 4]), G -> IsLeftCancellative(G));
true

gap> ForAll(AllSmallGroups([2 .. 4]), G -> IsRightCancellative(G));
true

gap> ForAll(AllSmallGroups([2 .. 4]), G -> IsCancellative(G));
true

gap> ForAny(AllSmallAntimagmas([2 .. 3]), M -> IsCancellative(M));
false

gap> STOP_TEST("test_properties_magma_left_right_cancellative.tst");