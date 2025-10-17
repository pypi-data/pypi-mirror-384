gap> START_TEST("test_properties_magma_commutativity_index.txt");

gap> Collected(List(AllSmallAntimagmas([2 .. 3]), M -> CommutativityIndex(M)));
[ [ 0, 4 ], [ 1, 8 ] ]

gap> STOP_TEST("test_properties_magma_commutativity_index.txt");