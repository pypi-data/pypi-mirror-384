gap> START_TEST("test_properties_magma_associativity_index.txt");

gap> ForAll(AllSmallGroups([2 .. 12]), M -> AssociativityIndex(M) = Size(M) ^ 3);
true

gap>  ForAll(AllSmallAntimagmas([2 .. 3]), M -> AssociativityIndex(M) = 0);
true

gap> STOP_TEST("test_properties_magma_associativity_index.txt");