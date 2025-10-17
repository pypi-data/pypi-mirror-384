BindGlobal("MinusDeltaMatrix@",function(d,q,w,i)
local A,B,C,delta,n,psi,w0;
  w0:=w^(q+1);
  psi:=w^(QuoInt((q+1),2));
  Assert(1,psi=-(w^(QuoInt((q^2+q),2))));
  Assert(1,psi^q=-psi);
  A:=(w^(q-1)+w^(1-q))/2;
  B:=psi*(w^(1-q)-w^(q-1))/2;
  C:=psi^-1*(w^(1-q)-w^(q-1))/2;
  delta:=IdentityMat(d, GF(q));
  n:=QuoInt((d-2),2);
  delta[2*i-1][2*i-1]:=w0^-1;
  delta[2*i][2*i]:=w0;
  delta[d-1][d-1]:=A;
  delta[d-1][d]:=-C;
  delta[d][d-1]:=-B;
  delta[d][d]:=A;
  return ImmutableMatrix(GF(q),delta*Z(q)^0);
end);

BindGlobal("MinusEvenDeltaMatrix@",function(d,q,w,i)
local A,B,C,delta,n,w0;
  w0:=w^(q+1);
  A:=(w^(1-q)+w^(q-1)+1);
  B:=(w^(1)+w^(q));
  C:=(w^(-1)+w^(-q));
  delta:=IdentityMat(d, GF(q));
  n:=QuoInt((d-2),2);
  delta[2*i-1][2*i-1]:=w0^-1;
  delta[2*i][2*i]:=w0;
  delta[d-1][d-1]:=A;
  delta[d-1][d]:=C;
  delta[d][d-1]:=B;
  delta[d][d]:=1;
  return ImmutableMatrix(GF(q),delta*Z(q)^0);
end);

BindGlobal("Minus6Presentation@",function(q)
local N,Q,R,S,U,d,delta,eta,images,sigma,tau,z;
  d:=4;
  R:=Internal_StandardPresentationForSU@(d,q:Presentation:=true,Projective:=false);
  Q:=FreeGroupOfFpGroup(R);
  R:=RelatorsOfFpGroup(R);
  N:=FreeGroup("z","tau","sigma","delta","U");
  N:=Group(StraightLineProgGens(GeneratorsOfGroup(N)));
  z:=N.1;
  tau:=N.2;
  sigma:=N.3;
  delta:=N.4;
  U:=N.5;
  if IsOddInt(q) then
    images:=[U,z*U^2,sigma,delta*(delta^-1)^U,z*U^2,tau^-1,delta];
  else
    images:=[U,z,sigma,delta*(delta^-1)^U,z,tau^1,delta];
  fi;
  eta:=GroupHomomorphismByImages(Q,N, GeneratorsOfGroup(Q),images);
  S:=List(R,r->ImagesRepresentative(eta,r));
  if IsOddInt(q) then
    Add(S,delta^(QuoInt((q^2-1),2)));
  fi;
  return N/S;
end);

BindGlobal("Minus_PresentationForN1@",function(d,q)
local F,OMIT,R,R1,Rels,S,U,V,m,n,phi,z;
  F:=FreeGroup("z","U","V");
  F:=Group(StraightLineProgGens(GeneratorsOfGroup(F)));
  z:=F.1;
  U:=F.2;
  V:=F.3;
  m:=QuoInt((d-2),2);
  if IsOddInt(q) then
    R:=SignedPermutations@(m);
    S:=FreeGroupOfFpGroup(R);
    R:=RelatorsOfFpGroup(R);
  elif IsEvenInt(q) then
    R:=PresentationForSn@(m);
    S:=FreeGroupOfFpGroup(R);
    R:=RelatorsOfFpGroup(R);
  fi;
  phi:=GroupHomomorphismByImages(S,F,
    GeneratorsOfGroup(S),
    [U,V]);
  R:=List(R,r->ImagesRepresentative(phi,r));
  n:=QuoInt(d,2);
  R1:=[];
  Add(R1,Comm(z,U^V));
  if n > 4 then
    Add(R1,Comm(z,V*U^-1));
  fi;
  OMIT:=true;
  if not OMIT then
    Add(R1,z^2);
    Add(R1,Comm(z,z^U));
    if IsOddInt(q) then
      Add(R1,Comm(z,U^2));
    fi;
  fi;
  Rels:=Concatenation(R1,R);
  return F/Rels;
end);

#Minus_Order_N1:=function(d,q)
#local n;
#  n:=QuoInt(d,2);
#  if IsOddInt(q) then
#    return 2^(2*n-3)*Factorial(n-1);
#  else
#    return 2^(n-1)*Factorial(n-1);
#  fi;
#end;

BindGlobal("Minus_PresentationForN@",function(d,q)
local F,OMIT,R,R1,Rels,S,U,V,delta,n,phi,z;
  F:=FreeGroup("delta","z","U","V");
  F:=Group(StraightLineProgGens(GeneratorsOfGroup(F)));
  delta:=F.1;
  z:=F.2;
  U:=F.3;
  V:=F.4;
  R:=Minus_PresentationForN1@(d,q);
  S:=FreeGroupOfFpGroup(R);
  R:=RelatorsOfFpGroup(R);
  phi:=GroupHomomorphismByImages(S,F,
    GeneratorsOfGroup(S),
    [z,U,V]);
  R:=List(R,r->ImagesRepresentative(phi,r));
  n:=QuoInt(d,2);
  R1:=[];
  Add(R1,Comm(delta,U^V));
  if n > 4 then
    Add(R1,Comm(delta,V*U^-1));
  fi;
  OMIT:=true;
  if not OMIT then
    if IsOddInt(q) then
      Add(R1,U^2/((delta*(delta^-1)^U)^(QuoInt((q-1),2))));
    fi;
    Add(R1,Comm(delta,z^U)/delta^(q-1));
    if IsOddInt(q) then
      Add(R1,delta^(QuoInt((q^2-1),2)));
    else
      Add(R1,delta^((q^2-1)));
    fi;
    Add(R1,Comm(delta,delta^U));
    Add(R1,delta^z*delta);
    Add(R1,Comm(delta^(q-1),U));
  fi;
  Rels:=Concatenation(R1,R);
  return F/Rels;
end);

#Minus_OrderN:=function(d,q)
#local n;
#  n:=QuoInt(d,2);
#  if IsOddInt(q) then
#    return (q+1)*(q-1)^(n-1)*2^(n-2)*Factorial(n-1);
##  else
#    return (q+1)*(q-1)^(n-1)*2^(n-1)*Factorial(n-1);
#  fi;
#end;

BindGlobal("Setup_MinusPresentation@",function(d,q)
local F,OMIT,R,R1,R2,R3,R4,R5,Rels,S,U,V,W,delta,e,f,n,p,phi,sigma,tau,z;
  if d=6 then
    return Minus6Presentation@(q);
  fi;
  F:=FreeGroup("z","tau","sigma","delta","U","V");
  F:=Group(StraightLineProgGens(GeneratorsOfGroup(F)));
  z:=F.1;
  tau:=F.2;
  sigma:=F.3;
  delta:=F.4;
  U:=F.5;
  V:=F.6;
  e := Factors(q);
  if Size(DuplicateFreeList(e)) > 1 then
      f := false;
  else
      f := true;
      p := e[1];
      e := Size(e);
  fi;
  R:=Minus_PresentationForN@(d,q);
  S:=FreeGroupOfFpGroup(R);
  R:=RelatorsOfFpGroup(R);
  phi:=GroupHomomorphismByImages(S,F, GeneratorsOfGroup(S), [delta,z,U,V]);
  R:=List(R,r->ImagesRepresentative(phi,r));
  n:=QuoInt(d,2);
  R1:=[];
  #   centraliser of sigma in N
  Add(R1,Comm(sigma,z^(V^2)));
  Add(R1,Comm(sigma,delta^(V^2)));
  OMIT:=true;
  if not OMIT then
    Add(R1,Comm(sigma,delta*delta^U));
    Add(R1,Comm(sigma,z*z^U*U));
  fi;
  if n > 4 then
    Add(R1,Comm(sigma,U^(V^2)));
  fi;
  #   elements generate the same group but for odd q reflects direct product
  if n > 5 then
    if IsOddInt(q) then
      Add(R1,Comm(sigma,V*U^-1*(U^-1)^V));
    else
      Add(R1,Comm(sigma,V*U*U^V));
    fi;
  fi;
  R2:=[];
  #   centraliser of tau in N
  Add(R2,Comm(tau,U^V));
  if n > 4 then
    Add(R2,Comm(tau,V*U^-1));
  fi;
  if IsEvenInt(q) then
    Add(R2,Comm(tau,delta^(V^2)*(delta^-1)^(V)));
  fi;
  R3:=Minus6Presentation@(q);
  S:=FreeGroupOfFpGroup(R3);
  R3:=RelatorsOfFpGroup(R3);
  phi:=GroupHomomorphismByImages(S,F, GeneratorsOfGroup(S),
    [z,tau,sigma,delta,U]);
  R3:=List(R3,r->ImagesRepresentative(phi,r));
  R4:=[];
  Add(R4,Comm(sigma,sigma^V)/sigma^(V*U^-1));
  Add(R4,Comm(sigma,sigma^(V*U^-1)));
  W:=U^(V*U^-1);
  Add(R4,Comm(sigma,sigma^W));
  if n > 4 then
    Add(R4,Comm(sigma,sigma^(V^2)));
  fi;
  R5:=[];
  Add(R5,Comm(sigma^V,tau));
  Rels:=Concatenation(R,R1,R2,R3,R4,R5);
  return F/Rels;
end);

#   generator of centre as word in presentation generators
BindGlobal("MinusGeneratorOfCentre@",
function(d,q,F)
local V,delta,n,z;
  Assert(1,IsEvenInt(d) and d > 4);
  n:=QuoInt(d,2);
  if IsOddInt(n) and q mod 4=3 then
    delta:=F.4;
    if d=6 then
      V:=F.5;
    else
      V:=F.6;
    fi;
    z:=V^(n-1)*delta^(QuoInt((q^2-1),4));
  else
    z:=Identity(F);
  fi;
  return z;
end);

#   express presentation generators as words in standard generators
BindGlobal("MinusStandardToPresentation@",
function(d,q)
local lvarDelta,F,U,V,W,delta,m,p,s,sigma,t,tau,w,w0,x,z,gens;
  Assert(1,IsEvenInt(d) and d > 4);
  if IsOddInt(q) then
    W:=FreeGroup("s","t","delta","U","V");
    W:=Group(StraightLineProgGens(GeneratorsOfGroup(W)));
    gens:=GeneratorsOfGroup(W);
    gens:=StraightLineProgGens(gens);
    s:=gens[1];
    t:=gens[2];
  else
    W:=FreeGroup("t","es","delta","U","V");
    W:=Group(StraightLineProgGens(GeneratorsOfGroup(W)));
    gens:=GeneratorsOfGroup(W);
    gens:=StraightLineProgGens(gens);
    t:=gens[1];
    s:=gens[2];
    #   correct discrepancy between published s and code s
    s:=s^t;
  fi;
  delta:=gens[3];
  U:=gens[4];
  V:=gens[5];
  z:=s^V;
  # rewritten select statement
  if d mod 4=2 then
    tau:=(t^V)^-1;
  else
    tau:=(t^V);
  fi;
  if IsOddInt(q) then
    lvarDelta:=(delta^V)^(QuoInt((q^2-1),2)-q);
  else
    lvarDelta:=(delta^-1)^V;
  fi;
  p:=Characteristic(GF(q));
  if IsOddInt(p) then
    sigma:=Comm(tau,tau^(z*U))^(QuoInt((p-1),2));
  else
    F:=GF(q^2);
    w:=PrimitiveElement(F);
    w0:=w^(q+1);
    # was "m:=Log(w0,w^2+w^(2*q));"
    m:=LogFFE(w^2+w^(2*q), w0);
    x:=Comm(tau^delta,tau^U)^(z*U);
    sigma:=x^(lvarDelta^(q-m));
  fi;
  if d=6 then
    return [z,tau,sigma,lvarDelta,U,U];
  else
    return [z,tau,sigma,lvarDelta,U,V];
  fi;
end);

BindGlobal("MinusPresentationToStandard@",
function(d,q)
local lvarDelta,U,V,W,delta,s,sigma,t,tau,z;
  Assert(1,IsEvenInt(d) and d > 4);
  W:=FreeGroup("z","tau","sigma","Delta","U","V");
  W:=Group(StraightLineProgGens(GeneratorsOfGroup(W)));
  z:=W.1;
  tau:=W.2;
  sigma:=W.3;
  lvarDelta:=W.4;
  U:=W.5;
  V:=W.6;
  # rewritten select statement
  if d mod 4=0 then
    t:=tau^(V^-1);
  else
    t:=(tau^-1)^(V^-1);
  fi;
  if IsOddInt(q) then
    delta:=(lvarDelta^(V^-1))^(QuoInt((q^2-1),2)-q);
  else
    delta:=(lvarDelta^-1)^(V^-1);
  fi;
  s:=z^(V^-1);
  if IsEvenInt(q) then
    #   correct discrepancy between published s and code s
    s:=s^(t^-1);
    return [t,s,delta,U,V];
  else
    return [s,t,delta,U,V];
  fi;
end);

#   relations are on presentation generators;
#  convert to relations on standard generators
BindGlobal("MinusConvertToStandard@",
function(d,q,Rels)
local A,B,C,T,U,W,tau,gens;
  A:=MinusStandardToPresentation@(d,q);
  #was Rels:=Evaluate(Rels,A);
  gens:=GeneratorsOfGroup(FamilyObj(Rels)!.wholeGroup);
  Rels:=List(Rels, w-> MappedWord(w, gens, A));
  B:=MinusPresentationToStandard@(d,q);
  #was C:=Evaluate(B,A);
  gens:=GeneratorsOfGroup(FamilyObj(B)!.wholeGroup);
  C:=List(B, w-> MappedWord(w, gens, A));

  U:=FamilyObj(C)!.wholeGroup;
  W:=FamilyObj(Rels)!.wholeGroup;
  tau:=GroupHomomorphismByImages(U,W,GeneratorsOfGroup(U),GeneratorsOfGroup(W));
  T:=List([1..Length(GeneratorsOfGroup(W))],
    i->W.(i)^-1*ImagesRepresentative(tau,C[i]));
  Rels:=Concatenation(Rels,T);
  return W/Rels;
end);

BindGlobal("MinusPresentation@",function(d,q)
local gens,P,Presentation,Projective,Q,R,Rels,S,n,z;
  Projective:=ValueOption("Projective");
  if Projective=fail then
    Projective:=false;
  fi;
  Presentation:=ValueOption("Presentation");
  if Presentation=fail then
    Presentation:=false;
  fi;
  Assert(1,d >= 4);
  Assert(1,IsEvenInt(d));
  n:=QuoInt(d,2);
  if d=4 then
    R:=ClassicalStandardPresentation("SL",2,q^2:Projective:=true,
      Presentation:=false);
    # added variable "gen" for function MappedWord below
    gens:=GeneratorsOfGroup(FreeGroupOfFpGroup(R));
    R:=RelatorsOfFpGroup(R);
    Q:=FreeGroup(5);
    Q:=Group(StraightLineProgGens(GeneratorsOfGroup(Q)));
    if IsEvenInt(q) then
      # was "R:=Evaluate(R,[Q.1^Q.2,Q.1^Q.2,Q.1,Q.3]);"
      R:=List(R, w -> MappedWord(w, gens, [Q.1^Q.2,Q.1^Q.2,Q.1,Q.3]));
      Add(R,(Q.1*Q.1^Q.2*Q.1)*Q.2^-1);
    else
      # was "R:=Evaluate(R,List([1,1,2,3],i->Q.i));"
      R:=List(R, w -> MappedWord(w, gens, GeneratorsOfGroup(Q){[1,1,2,3]}));
    fi;
    Add(R,Q.4);
    Add(R,Q.5);
    return Q/R;
  fi;
  R:=Setup_MinusPresentation@(d,q);
  P:=FreeGroupOfFpGroup(R);
  R:=ShallowCopy(RelatorsOfFpGroup(R));
  if Projective and IsOddInt(n) and q mod 4=3 then
    z:=MinusGeneratorOfCentre@(d,q,P);
    Add(R,z);
  fi;
  if Presentation then
    return P/R;
  fi;
  #   do conversion
  Rels:=MinusConvertToStandard@(d,q,R);
  S:=FreeGroupOfFpGroup(Rels);
  Rels:=RelatorsOfFpGroup(Rels);
  Rels:=Filtered(Rels,w->not IsOne(w));
  return S/Rels;
end);

InstallGlobalFunction(MinusGenerators@,function(d,q)
local B,varE,U,V,delta,gens,i,n,s,sigma,tau,w,z,one;
  if d=4 then
    return ClassicalStandardGenerators("Omega-",d,q:
      PresentationGenerators:=false);
  fi;
  varE:=GF(q^2);
  one:=One(varE);
  w:=PrimitiveElement(varE);
  i:=1;
  if IsEvenInt(q) then
    delta:=MinusEvenDeltaMatrix@(d,q,w,i);
  else
    delta:=MinusDeltaMatrix@(d,q,w,i);
  fi;
  n:=QuoInt((d-2),2);
  z:=NullMat(d, d, GF(q));
  z[1][2]:=1;
  z[2][1]:=1;
  for i in [3..d-1] do
    z[i][i]:=1;
  od;
  if IsOddInt(q) then
    z[d-1][d-1]:=-one;
  else
    B:=w+w^q;
    z[d][d-1]:=B;
  fi;
  z[d][d]:=1;
  tau:=IdentityMat(d, GF(q));
  if IsOddInt(q) then
    s:=one;
    tau[1][1]:=one;
    tau[1][2]:=s^2;
    tau[1][d-1]:=s;
    tau[d-1][d-1]:=one;
    tau[d-1][2]:=2*s;
  else
    B:=w+w^q;
    tau[1][1]:=one;
    tau[1][2]:=one;
    tau[1][d-1]:=one;
    tau[d][d]:=one;
    tau[d][2]:=B;
  fi;
  s:=1;
  sigma:=NullMat(d, d, GF(q));
  sigma[1][1]:=one;
  sigma[1][3]:=s;
  sigma[4][4]:=one;
  sigma[4][2]:=-s;
  for i in Concatenation([2,3],[5..d]) do
    sigma[i][i]:=one;
  od;
  U:=NullMat(d, d, GF(q));
  U[1][3]:=one;
  U[3][1]:=-one;
  U[2][4]:=one;
  U[4][2]:=-one;
  for i in [5..d] do
    U[i][i]:=one;
  od;
  V:=NullMat(d, d, GF(q));
  for i in [1..n-1] do
    V[2*i-1][2*i+1]:=one;
    V[2*i][2*i+2]:=one;
  od;
  V[d-3][1]:=(-1)^(n-1);
  V[d-2][2]:=(-1)^(n-1);
  for i in [d-1..d] do
    V[i][i]:=one;
  od;
  gens:=List([z,tau,sigma,delta,U,V],x->x*Z(q)^0);
  return gens;
end);
