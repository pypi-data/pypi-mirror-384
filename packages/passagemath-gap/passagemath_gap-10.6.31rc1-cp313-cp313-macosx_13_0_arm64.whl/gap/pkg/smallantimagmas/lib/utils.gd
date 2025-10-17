#! @Arguments n
#! @Description
#! returns all possible diagonals of multiplication table for <A>[n]</A>-antimagma.
#!
#! @BeginExampleSession
#! gap> AntimagmaGeneratorPossibleDiagonals(2);
#! [ [ 2, 1 ] ]
#! gap> AntimagmaGeneratorPossibleDiagonals(3);
#! [
#!   [ 2, 1, 1 ], [ 2, 1, 2 ], [ 2, 3, 1 ], [ 2, 3, 2 ],
#!   [ 3, 1, 1 ], [ 3, 1, 2 ], [ 3, 3, 1 ], [ 3, 3, 2 ]
#! ]
#! @EndExampleSession
#!

DeclareOperation("AntimagmaGeneratorPossibleDiagonals", [IsInt]);

#! @Arguments Ms
#! @Description
#! filters non-isomorphic magmas <A>Ms</A>.

DeclareOperation("UpToIsomorphism", [IsList]);
