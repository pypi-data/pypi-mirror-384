gap> START_TEST("test_properties_magma_isomorphism_invariants.tst");

gap> List([2 .. 3], n -> List(AllSmallAntimagmas(n), M -> MagmaIsomorphismInvariantsMatch(M, TransposedMagma(M))));
[ [ false, false ], 
  [ false, false, false, false, false, false, false, false, false, false ] 
]

gap> STOP_TEST("test_properties_magma_isomorphism_invariants.tst");