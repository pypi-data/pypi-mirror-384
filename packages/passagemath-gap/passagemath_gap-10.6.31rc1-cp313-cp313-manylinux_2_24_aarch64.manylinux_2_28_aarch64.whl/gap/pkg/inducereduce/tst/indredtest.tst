gap> START_TEST("indredtest.tst");

#############################################################################
# testing the main function
gap> ct:=CharacterTableUnger(AlternatingGroup(6));
CharacterTable( Alt( [ 1 .. 6 ] ) )
gap> Display(ct);
CT1

     2  3  3  .  .  2  .  .
     3  2  .  2  2  .  .  .
     5  1  .  .  .  .  1  1

       1a 2a 3a 3b 4a 5a 5b

X.1     1  1  1  1  1  1  1
X.2     5  1  2 -1 -1  .  .
X.3     9  1  .  .  1 -1 -1
X.4     8  . -1 -1  .  A *A
X.5     8  . -1 -1  . *A  A
X.6    10 -2  1  1  .  .  .
X.7     5  1 -1  2 -1  .  .

A = -E(5)^2-E(5)^3
  = (1+Sqrt(5))/2 = 1+b5

#
gap> ct:=CharacterTableUnger(GeneralLinearGroup(2,3));
CharacterTable( GL(2,3) )
gap> Display(ct);
CT2

     2  4  1  4  1  3  3  3  2
     3  1  1  1  1  .  .  .  .

       1a 6a 2a 3a 4a 8a 8b 2b

X.1     1  1  1  1  1  1  1  1
X.2     3  .  3  . -1 -1 -1  1
X.3     3  .  3  . -1  1  1 -1
X.4     2 -1  2 -1  2  .  .  .
X.5     1  1  1  1  1 -1 -1 -1
X.6     2  1 -2 -1  .  A -A  .
X.7     4 -1 -4  1  .  .  .  .
X.8     2  1 -2 -1  . -A  A  .

A = -E(8)-E(8)^3
  = -Sqrt(-2) = -i2

#
gap> STOP_TEST("indredtest.tst");
