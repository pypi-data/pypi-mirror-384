gap> START_TEST("test_properties_element_left_right_order.tst");

gap> ForAll(AllSmallGroups([2 .. 10]), G -> ForAll(Elements(G), g -> Order(g) = LeftOrder(g)));
true

gap> ForAll(AllSmallGroups([2 .. 10]), G -> ForAll(Elements(G), g -> Order(g) = RightOrder(g)));
true

gap> ForAll(AllSmallAntimagmas([2 .. 3]), M -> ForAll(Filtered(Elements(M), m -> LeftOrder(m) <> infinity), m -> LeftOrder(m) <> RightOrder(m)));
true

gap> ForAll(AllSmallAntimagmas([2 .. 3]), M -> ForAll(Filtered(Elements(M), m -> RightOrder(m) <> infinity), m -> LeftOrder(m) <> RightOrder(m)));
true

gap> STOP_TEST("test_properties_element_left_right_order.tst");