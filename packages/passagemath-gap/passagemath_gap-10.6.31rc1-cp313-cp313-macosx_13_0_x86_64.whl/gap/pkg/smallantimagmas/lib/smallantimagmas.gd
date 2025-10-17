#! @Arguments n
#! @Description
#! returns all antiassociative magmas of specified size <A>n</A> (a number)
#!
#! @BeginExampleSession
#! gap> AllSmallAntimagmas(2);
#! [ <magma with 2 generators>, <magma with 2 generators> ]
#! gap> AllSmallAntimagmas(3);
#! [ 
#!   <magma with 3 generators>, <magma with 3 generators>, <magma with 3 generators>,
#!   <magma with 3 generators>, <magma with 3 generators>, <magma with 3 generators>,
#!   <magma with 3 generators>, <magma with 3 generators>,
#!   <magma with 3 generators>, <magma with 3 generators>
#! ]
#! @EndExampleSession
#!
DeclareGlobalFunction("AllSmallAntimagmas");

#! @Arguments n
#! @Description
#! counts number of antiassociative magmas of specified size <A>n</A> (a number).
#!
#! @BeginExampleSession
#! gap> NrSmallAntimagmas(2);
#! 2
#! gap> NrSmallAntimagmas(3);
#! 10
#! gap> NrSmallAntimagmas(4);
#! 17780
#! @EndExampleSession
#!
DeclareGlobalFunction("NrSmallAntimagmas");

#! @Arguments n, i
#! @Description
#! returns antiassociative magma of id <A>[n, i]</A>.
#!
#! @BeginExampleSession
#! gap> SmallAntimagma(2, 1);
#! <magma with 2 generators>
#! gap> SmallAntimagma(4, 5);
#! <magma with 4 generators>
#! @EndExampleSession
#!
DeclareGlobalFunction("SmallAntimagma");

#! @Arguments n
#! @Description
#! returns a random antiassociative magma of size <A>n</A>.
#!
#! @BeginExampleSession
#! gap> OneSmallAntimagma(2);
#! <magma with 2 generators>
#!
#! gap> OneSmallAntimagma(3);
#! <magma with 3 generators>
#! @EndExampleSessions
#!
DeclareGlobalFunction("OneSmallAntimagma");

#! @Arguments n
#! @Description
#! returns really-all antiassociative magmas, isomorphic, of specified size <A>n</A> (a number)
#! 
#! @BeginExampleSession
#! gap> ReallyAllSmallAntimagmas(2);
#! [ <magma with 2 generators>, <magma with 2 generators> ]
#! @EndExampleSession
#!
DeclareGlobalFunction("ReallyAllSmallAntimagmas");

#! @Arguments n
#! @Description
#! counts number of antiassociative magmas of specified size <A>n</A> (a number) 
#!
#! @BeginExampleSession
#! gap> ReallyNrSmallAntimagmas(3);
#! 52
#! @EndExampleSession
#!
DeclareGlobalFunction("ReallyNrSmallAntimagmas");