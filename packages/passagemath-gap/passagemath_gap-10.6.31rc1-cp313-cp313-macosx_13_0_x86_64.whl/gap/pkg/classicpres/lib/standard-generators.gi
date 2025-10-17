#AH 7/19: commented out as unused
# #   function from Allan Steel
# find_quad_ext_prim:=function(K,L)
# #  /out:
# #  L must be a degree-2 extension of K, where #K = q.
# #  Return a primitive element alpha of L such that
# #  alpha^(q + 1) = PrimitiveElement(K).
# 
# local alpha,flag,q,w;
#   q:=Size(K);
#   Assert(1,Size(L)=q^2);
#   w:=PrimitiveElement(K);
#   repeat
#     # =v= MULTIASSIGN =v=
#     alpha:=NormEquation(L,w);
#     flag:=alpha.val1;
#     alpha:=alpha.val2;
#     # =^= MULTIASSIGN =^=
#     Assert(1,flag);
#     Assert(1,alpha^(q+1)=w);
#     
#   until IsPrimitive(alpha);
#   return alpha;
# end;

#   canonical basis for SL(d, q) 
BindGlobal("SLChosenElements@",function(G)
local F,M,P,a,b,d,delta,i,t,w,one;
  d:=DimensionOfMatrixGroup(G);
  F:=DefaultFieldOfMatrixGroup(G);
  w:=PrimitiveElement(F);
  a:=IdentityMat(d,F);
  one:=One(F);
  a[1][1]:=0*one;
  a[1][2]:=one;
  a[2][1]:=-one;
  a[2][2]:=0*one;
  b:=0*a;
  for i in [2..d] do
    b[i][i-1]:=-one;
  od;
  b[1][d]:=one;
  #   if d eq 3 then b := b^-1; end if;
  t:=IdentityMat(d,F);
  t[1][2]:=one;
  delta:=IdentityMat(d,F);
  delta[1][1]:=w;
  delta[2][2]:=w^-1;
  a:=ImmutableMatrix(F,a);
  b:=ImmutableMatrix(F,b);
  t:=ImmutableMatrix(F,t);
  delta:=ImmutableMatrix(F,delta);
  return [a,b,t,delta];
end);

#   additional element to generate all of Sp 
BindGlobal("SpAdditionalElement@",function(F)
local I,M;
  I:=IdentityMat(4,F);
  I[2][3]:=One(F);
  I[4][1]:=One(F);
  I:=ImmutableMatrix(F,I);
  return I;
end);

#   canonical basis for Sp(d, q) 
BindGlobal("SpChosenElements@",function(G)
local F,M,P,a,b,d,delta,i,n,p,t,v,w,one;
  d:=DimensionOfMatrixGroup(G);
  F:=DefaultFieldOfMatrixGroup(G);
  w:=PrimitiveElement(F);
  a:=IdentityMat(d,F);
  one:=One(F);
  a[1][1]:=0*one;
  a[1][2]:=one;
  a[2][1]:=-one;
  a[2][2]:=0*one;
  t:=IdentityMat(d,F);
  t[1][2]:=one;
  delta:=IdentityMat(d,F);
  delta[1][1]:=w;
  delta[2][2]:=w^-1;
  if d >= 4 then
    p:=NullMat(d,d,F);
    p[1][3]:=one;
    p[2][4]:=one;
    p[3][1]:=one;
    p[4][2]:=one;
    for i in [5..d] do
      p[i][i]:=one;
    od;
  else
    p:=IdentityMat(d,F);
  fi;
  if d >= 4 then
    b:=NullMat(d,d,F);
    n:=QuoInt(d,2);
    for i in [1,1+2..d-3] do
      b[i][i+2]:=one;
    od;
    b[d-1][1]:=one;
    for i in [2,2+2..d-2] do
      b[i][i+2]:=one;
    od;
    b[d][2]:=one;
  else
    b:=IdentityMat(d,F);
  fi;
  a:=ImmutableMatrix(F,a);
  b:=ImmutableMatrix(F,b);
  p:=ImmutableMatrix(F,p);
  t:=ImmutableMatrix(F,t);
  delta:=ImmutableMatrix(F,delta);
  if d > 4 then
    #v:=(DirectSumMat(Identity(MatrixAlgebra(F,d-4)),SpAdditionalElement(F))) *FORCEOne(P);
    v:=IdentityMat(d,F);
    v{[d-3..d]}{[d-3..d]}:=SpAdditionalElement@(F);
  elif d=4 then
    v:=SpAdditionalElement@(F);
  else
    v:=IdentityMat(d,F);
  fi;
  v:=ImmutableMatrix(F,v);

  return [a,b,t,delta,p,v];
end);

#   additional elements to generate SU 
BindGlobal("SUAdditionalElements@",function(F)
local EvenCase,I,J,M,d,gamma,phi,q,one;
  EvenCase:=ValueOption("EvenCase");
  if EvenCase=fail then
    EvenCase:=true;
  fi;
  if EvenCase then
    d:=4;
  else
    d:=3;
  fi;
  gamma:=PrimitiveElement(F);
  q:=RootInt(Size(F),2);
  I:=IdentityMat(d,F);
  one:=One(F);
  if EvenCase then
    I[1][3]:=one;
    I[4][2]:=-one;
    J:=DiagonalMat([gamma,gamma^-q,gamma^-1,gamma^q]);
  else
    if IsEvenInt(q) then
      phi:=(Trace(F,GF(q),gamma))^-1*gamma;
    else
      phi:=-1/2*one;
    fi;
    I:=[[1,phi,1],[0,1,0],[0,-1,1]]*one;
    J:=DiagonalMat([gamma,gamma^(-q),gamma^(q-1)]);
  fi;

  I:=ImmutableMatrix(F,I);
  J:=ImmutableMatrix(F,J);
  return [I,J];
end);

#   canonical basis for SU(d, q) 
BindGlobal("SUChosenElements@",function(G)
local varE,F,P,a,alpha,b,d,delta,f,i,n,p,q,t,w,w0,x,y,one;
  d:=DimensionOfMatrixGroup(G);
  varE:=DefaultFieldOfMatrixGroup(G);
  f:=QuoInt(DegreeOverPrimeField(varE),2);
  p:=Characteristic(varE);
  q:=p^f;
  F:=GF(q);
  w:=PrimitiveElement(varE);
  one:=One(F);
  if IsEvenInt(Size(varE)) then
    w0:=w^(q+1);
    alpha:=one;
  else
    alpha:=w^(QuoInt((q+1),2));
    w0:=alpha^2;
  fi;
  a:=NullMat(d,d,varE);
  a[1][2]:=alpha;
  a[2][1]:=alpha^-q;
  for i in [3..d] do
    a[i][i]:=one;
  od;
  t:=IdentityMat(d,varE);
  t[1][2]:=alpha;
  delta:=IdentityMat(d,varE);
  if (d=3 and p=2 and f=1) then
    delta[1][2]:=w;
    delta[1][3]:=w;
    delta[3][2]:=w^2;
  else
    delta[1][1]:=w0;
    delta[2][2]:=w0^-1;
  fi;
  if d >= 4 then
    p:=NullMat(d,d,varE);
    p[1][3]:=one;
    p[2][4]:=one;
    p[3][1]:=one;
    p[4][2]:=one;
    for i in [5..d] do
      p[i][i]:=one;
    od;
  else
    p:=IdentityMat(d,varE);
  fi;
  if d >= 4 then
    b:=NullMat(d,d,varE);
    n:=QuoInt(d,2);
    for i in [1,1+2..2*n-3] do
      b[i][i+2]:=one;
    od;
    b[2*n-1][1]:=one;
    for i in [2,2+2..2*n-2] do
      b[i][i+2]:=one;
    od;
    b[2*n][2]:=one;
    if IsOddInt(d) then
      b[d][d]:=one;
    fi;
  else
    b:=IdentityMat(d,varE);
  fi;
  a:=ImmutableMatrix(varE,a);
  b:=ImmutableMatrix(varE,b);
  p:=ImmutableMatrix(varE,p);
  t:=ImmutableMatrix(varE,t);
  delta:=ImmutableMatrix(varE,delta);

  if d=2 then
    x:=IdentityMat(d,varE);
    y:=IdentityMat(d,varE);
  elif d in [3,4] then
    y:=SUAdditionalElements@(varE:EvenCase:=IsEvenInt(d));
    x:=y[1];
    y:=y[2];
  else
    y:=SUAdditionalElements@(varE:EvenCase:=IsEvenInt(d));
    x:=y[1];
    y:=y[2];
    #x:=(DirectSumMat(Identity(MatrixAlgebra(varE,f)),x))*FORCEOne(GL(d,varE));
    #y:=(DirectSumMat(Identity(MatrixAlgebra(varE,f)),y))*FORCEOne(GL(d,varE));
    f:=IdentityMat(d,varE);
    f{[d-Length(x)+1..d]}{[d-Length(x)+1..d]}:=x;x:=f;
    f:=IdentityMat(d,varE);
    f{[d-Length(y)+1..d]}{[d-Length(y)+1..d]}:=y;y:=f;
  fi;
  x:=ImmutableMatrix(varE,x);
  y:=ImmutableMatrix(varE,y);
  return [a,b,t,delta,p,x,y];
end);

#   if SpecialGroup is true, then standard generators
#  for SO^0, otherwise for Omega 
BindGlobal("SOChosenElements@",function(G)
local one,D,F,Gens,I,L,M,P,SpecialGroup,U,_,a,b,delta,gens,h,i,m,n,q,u,w,x,y;
  SpecialGroup:=ValueOption("SpecialGroup");
  if SpecialGroup=fail then
    SpecialGroup:=false;
  fi;
  n:=DegreeOfMatrixGroup(G);
  Assert(1,IsOddInt(n) and n > 1);
  F:=DefaultFieldOfMatrixGroup(G);
  q:=Size(F);
  w:=PrimitiveElement(F);
  one:=One(F);
  #MA:=MatrixAlgebra(F,n);
  #A:=MatrixAlgebra(F,2);
  #M:=MatrixAlgebra(F,3);
  a:=[[1,1,2],[0,1,0],[0,1,1]]*one;
  U:=IdentityMat(n,F);
  #InsertBlock(TILDEU,a,n-2,n-2);
  U{[n-2..n]}{[n-2..n]}:=a;
  b:=[[0,1,0],[1,0,0],[0,0,-1]]*one;
  L:=IdentityMat(n,F);
  #InsertBlock(TILDEL,b,n-2,n-2);
  L{[n-2..n]}{[n-2..n]}:=b;
  delta:=DiagonalMat([w^2,w^-2,one]);
  D:=IdentityMat(n,F);
  #InsertBlock(TILDED,delta,n-2,n-2);
  D{[n-2..n]}{[n-2..n]}:=delta;
  Gens:=[L,U,D];
  if n=3 then
    h:=IdentityMat(n,F);
  else
    I:=[[1,0],[0,1]]*one;
    h:=NullMat(n,n,F);
    m:=n-1;
    for i in [1..QuoInt(m,2)-1] do
      x:=(i-1)*2+1;
      y:=x+2;
      #InsertBlock(TILDEh,I,x,y);
      h{[x..x+1]}{[y..y+1]}:=I;
    od;
    #InsertBlock(TILDEh,(-1)^(QuoInt(n,2)-1)*I,m-1,1);
    h{[m-1..m-1+Length(I)-1]}{[1..Length(I)]}:=(-1)^(QuoInt(n,2)-1)*I;
    h[n][n]:=One(F);
  fi;
  Add(Gens,h);
  #   EOB -- add additional generator u Oct 2012
  if n > 3 then
    u:=NullMat(n,n,F);
    for i in [5..n] do
      u[i][i]:=One(F);
    od;
    u[1][3]:=One(F);
    u[2][4]:=One(F);
    u[3][1]:=-One(F);
    u[4][2]:=-One(F);
  else
    u:=IdentityMat(n,F);
  fi;
  Add(Gens,u);
  if SpecialGroup then
    m:=IdentityMat(n,F);
    #_,b:=Valuation(q-1,2);
    b:=q-1;
    while IsEvenInt(NumeratorRat(b)) do b:=b/2;od;
    while IsEvenInt(DenominatorRat(b)) do b:=b*2;od;
    m[n-2][n-2]:=w^b;
    m[n-1][n-1]:=w^-b;
    Add(Gens,m);
  fi;
  gens:=List(Gens,x->ImmutableMatrix(F,x));
  return gens;
end);

#   if SpecialGroup is true, then standard generators
#  for SO+, otherwise for Omega+ 
BindGlobal("PlusChosenElements@",function(G)
local 
   A,F,Gens,I,M,P,SpecialGroup,_,a,b,delta,delta1,delta4,gens,i,n,q,s,s1,t,
   t1,t4,u,v,w,x,y,one;
  SpecialGroup:=ValueOption("SpecialGroup");
  if SpecialGroup=fail then
    SpecialGroup:=false;
  fi;
  n:=DegreeOfMatrixGroup(G);
  F:=DefaultFieldOfMatrixGroup(G);
  one:=One(F);
  q:=Size(F);
  w:=PrimitiveElement(F);
  #A:=MatrixAlgebra(F,2);
  if n=2 then
    Gens:=List([1..8],i->IdentityMat(2,F));
    if Size(F) > 3 then
      x:=OmegaPlus(2,F).1;
      Gens[3]:=x;
    fi;
    if SpecialGroup then
      w:=PrimitiveElement(F);
      if IsOddInt(q) then
        Gens[Size(Gens)+1]:=[[w,0],[0,w^-1]]*one;
      else
        Gens[Size(Gens)+1]:=[[0,1],[1,0]]*one;
      fi;
    fi;
  else
    #MA:=MatrixAlgebra(F,n);
    #M:=MatrixAlgebra(F,4);
    s:=NullMat(n,n,F);
    for i in [5..n] do
      s[i][i]:=one;
    od;
    s[1][4]:=-one;
    s[2][3]:=-one;
    s[3][2]:=one;
    s[4][1]:=one;
    t4:=[[1,0,0,-1],[0,1,0,0],[0,1,1,0],[0,0,0,1]]*one;
    t:=IdentityMat(n,F);
    #InsertBlock(TILDEt,t4,1,1);
    t{[1..4]}{[1..4]}:=t4;
    delta4:=DiagonalMat([w,w^-1,w,w^-1]);
    delta:=IdentityMat(n,F);
    #InsertBlock(TILDEdelta,delta4,1,1);
    delta{[1..4]}{[1..4]}:=delta4;
    s1:=NullMat(n,n,F);
    for i in [5..n] do
      s1[i][i]:=one;
    od;
    s1[1][3]:=one;
    s1[2][4]:=one;
    s1[3][1]:=-one;
    s1[4][2]:=-one;
    t4:=[[1,0,1,0],[0,1,0,0],[0,0,1,0],[0,-1,0,1]]*one;
    t1:=IdentityMat(n,F);
    #InsertBlock(TILDEt1,t4,1,1);
    t1{[1..4]}{[1..4]}:=t4;
    delta4:=DiagonalMat([w,w^-1,w^-1,w]);
    delta1:=IdentityMat(n,F);
    #InsertBlock(TILDEdelta1,delta4,1,1);
    delta1{[1..4]}{[1..4]}:=delta4;
    u:=IdentityMat(n,F);
    I:=IdentityMat(2,F);
    v:=NullMat(n,n,F);
    for i in [1..QuoInt(n,2)-1] do
      x:=(i-1)*2+1;
      y:=x+2;
      #InsertBlock(TILDEv,I,x,y);
      v{[x..x+Length(I)-1]}{[y..y+Length(I[1])-1]}:=I;
    od;
    #InsertBlock(TILDEv,(-1)^(QuoInt(n,2)+1)*I,n-1,1);
    v{[n-1..n-1+Length(I)-1]}{[1..Length(I[1])]}:=(-1)^(QuoInt(n,2)+1)*I;
    Gens:=[s,t,delta,s1,t1,delta1,u,v];
    if SpecialGroup then
      a:=IdentityMat(n,F);
      if IsOddInt(q) then
        #_,b:=Valuation(q-1,2);
        b:=q-1;
        while IsEvenInt(NumeratorRat(b)) do b:=b/2;od;
        while IsEvenInt(DenominatorRat(b)) do b:=b*2;od;
        # =^= MULTIASSIGN =^=
        a[1][1]:=w^b;
        a[2][2]:=w^-b;
      else
        a[1][1]:=0*one;
        a[1][2]:=one;
        a[2][1]:=one;
        a[2][2]:=0*one;
      fi;
      Add(Gens,a);
    fi;
  fi;
  gens:=List(Gens,x->ImmutableMatrix(F,x));
  return gens;
end);

BindGlobal("MinusChar2Elements@",function(G)
local 
   C,CC,F,GG,Gens,I,II,K,M,O,SpecialGroup,a,alpha,d,d1,dd,delta,deltaq,gamma,
   h,i,m,p,pow,q,r,r1,rr,sl,t,t1,tt,x,y,one;
  SpecialGroup:=ValueOption("SpecialGroup");
  if SpecialGroup=fail then
    SpecialGroup:=false;
  fi;
  d:=DimensionOfMatrixGroup(G);
  F:=DefaultFieldOfMatrixGroup(G);
  one:=One(F);
  q:=Size(F);
  alpha:=PrimitiveElement(F);
  K:=GF(q^2);
  gamma:=PrimitiveElement(K);
  for i in [1..q-1] do
    if (gamma^i)^(q+1)=alpha then
      pow:=i;
      break;
    fi;
  od;
  gamma:=gamma^pow;
  Assert(1,gamma^(q+1)=alpha);
  M:=MatrixAlgebra(GF(q^2),d);
  if d=2 then
    Gens:=List([1..5],i->One(G));
    O:=OmegaMinus(d,q);
    x:=O.Ngens(O);
    Gens[3]:=x;
    if SpecialGroup then
      #Gens[Size(Gens)+1]:=SOMinus(2,q).1;
      Gens[Size(Gens)+1]:=SO(-1,2,q).1;
    fi;
  else
    C:=[[1,0,0,0],[0,gamma,1,0],[0,gamma^q,1],[0,0,0,0,1]]*one;
    C:=TransposedMat(C);
    CC:=[[1,0,0,0],[0,0,0,1],[0,0,1,0],[0,1,0,0]]*one;
    sl:=SL(2,GF(q^2));
    t:=[[1,1],[0,1]]*one;
    r:=[[1,0],[1,1]]*one;
    delta:=[[gamma,0],[0,gamma^-1]]*one;
    deltaq:=[[gamma^q,0],[0,gamma^-q]]*one;
    G:=GL(4,GF(q^2));
    t1:=(KroneckerProduct(t,t)^(C^-1))^(CC^-1);
    r1:=(KroneckerProduct(r,r)^(C^-1))^(CC^-1);
    d1:=(KroneckerProduct(delta,deltaq)^(C^-1))^(CC^-1);
    GG:=GL(d,GF(q));
    #tt:=InsertBlock(One(GG),t1,d-3,d-3);
    tt:=List(One(GG),ShallowCopy);
    tt{[d-3..d-3+Length(t1)-1]}{[d-3..d-3+Length(t1[1])-1]}:=t1;
    #rr:=InsertBlock(One(GG),r1,d-3,d-3);
    rr:=List(One(GG),ShallowCopy);
    rr{[d-3..d-3+Length(r1)-1]}{[d-3..d-3+Length(r1[1])-1]}:=r1;
    #dd:=InsertBlock(One(GG),d1,d-3,d-3);
    dd:=List(One(GG),ShallowCopy);
    dd{[d-3..d-3+Length(d1)-1]}{[d-3..d-3+Length(d1[1])-1]}:=d1;
    Gens:=[tt,rr,dd];
    I:=One(GL(2,GF(q^2)));
    if d > 4 then
      p:=NullMat(d,d,F);
      #InsertBlock(TILDEp,I,1,3);
      p{[1..Length(I)]}{[3..Length(I[1])+2]}:=I;
      #InsertBlock(TILDEp,-I,3,1);
      p{[3..Length(I)+2]}{[1..Length(I[1])]}:=-I;
      for i in [5..d] do
        p[i][i]:=1;
      od;
    else
      p:=One(GG);
    fi;
    Add(Gens,p);
    if d > 6 then
      h:=NullMat(d,d,F);
      m:=d-2;
      for i in [1..QuoInt(m,2)-1] do
        x:=(i-1)*2+1;
        y:=x+2;
        #InsertBlock(TILDEh,I,x,y);
        h{[x..x+Length(I)-1]}{[y..y+Length(I[1])-1]}:=I;
      od;
      # rewritten select statement
      if IsEvenInt(QuoInt(d,2)) then
        II:=I;
      else
        II:=-I;
      fi;
      #InsertBlock(TILDEh,II,m-1,1);
      h{[m-1..m-1+Length(II)-1]}{[1..Length(II[1])]}:=II;
      #InsertBlock(TILDEh,I,d-1,d-1);
      h{[d-1..d-1+Length(I)-1]}{[d-1..d-1+Length(I[1])-1]}:=I;
      Add(Gens,h);
    else
      Add(Gens,p);
    fi;
    if SpecialGroup then
      a:=List(One(Gens[1]),ShallowCopy);
      a[1][1]:=0*one;
      a[2][2]:=0*one;
      a[1][2]:=1*one;
      a[2][1]:=1*one;
      Add(Gens,a);
    fi;
  fi;
  return List(Gens,x->ImmutableMatrix(F,x));
end);

#   if SpecialGroup is true, then standard generators
#  for SO-, otherwise for Omega- 
BindGlobal("MinusChosenElements@",function(G)
local 
   A,D,varE,lvarEE,F,Gens,I,L,M,P,SpecialGroup,U,a,b,c,d,delta,gens,h,i,m,mu,n,p,
   q,w,x,y,one;
  SpecialGroup:=ValueOption("SpecialGroup");
  if SpecialGroup=fail then
    SpecialGroup:=false;
  fi;
  n:=DegreeOfMatrixGroup(G);
  F:=DefaultFieldOfMatrixGroup(G);
  one:=One(F);
  q:=Size(F);
  if IsEvenInt(q) then
    return MinusChar2Elements@(G:SpecialGroup:=SpecialGroup);
  fi;
  #A:=MatrixAlgebra(F,2);
  if n=2 then
    Gens:=List([1..5],i->IdentityMat(2,F));
    x:=OmegaMinus(n,q).1;
    Gens[2]:=x;
    if SpecialGroup then
      if q mod 4=1 then
        Gens[Size(Gens)+1]:=-IdentityMat(2,F);
      else
        y:=SO(-1,n,q).1;
        Gens[Size(Gens)+1]:=y*x^-1;
      fi;
    fi;
    return List(Gens,x->ImmutableMatrix(F,x));
  fi;
  w:=PrimitiveElement(F);
  #MA:=MatrixAlgebra(F,n);
  #   EE := ext<F | 2>;
  lvarEE:=GF(q^2);
  delta:=PrimitiveElement(lvarEE);
  mu:=delta^(QuoInt((q+1),2));
  #  
  #  if mu^2 ne w then
  #  x := find_quad_ext_prim(F, EE);
  #  E<delta> := sub<EE | x>;
  #  SetPrimitiveElement(E, delta);
  #  mu := delta^((q + 1) div 2);
  #  else
  #  E := EE;
  #  end if;
  
  varE:=lvarEE;
  #   EOB Nov 2012 -- we need this to be true but known problem
  Assert(1,mu^2=w);
  #MA:=MatrixAlgebra(F,n);
  I:=[[1,0],[0,1]]*one;
  M:=MatrixAlgebra(F,4);
  a:=[[1,1],[0,1]]*one;
  b:=[[2,0],[0,0]]*one;
  c:=[[0,1],[0,0]]*one;
  d:=[[1,0],[0,1]]*one;
  U:=IdentityMat(n,F);
  U[n-3][n-3]:=0*one;
  U[n-3][n-2]:=1*one;
  U[n-2][n-3]:=1*one;
  U[n-2][n-2]:=0*one;
  U[n-1][n-1]:=-1*one;
  a:=[[1,0],[1,1]]*one;
  b:=[[0,0],[2,0]]*one;
  c:=[[1,0],[0,0]]*one;
  d:=[[1,0],[0,1]]*one;
  L:=NullMat(n,n,F);
  for i in [1..n-4] do
    L[i][i]:=1;
  od;
  #InsertBlock(TILDEL,a,n-3,n-3);
  L{[n-3,n-2]}{[n-3,n-2]}:=a;
  #InsertBlock(TILDEL,b,n-3,n-1);
  L{[n-3,n-2]}{[n-1,n]}:=b;
  #InsertBlock(TILDEL,c,n-1,n-3);
  L{[n-1,n]}{[n-3,n-2]}:=c;
  #InsertBlock(TILDEL,d,n-1,n-1);
  L{[n-1,n]}{[n-1,n]}:=d;
  L:=TransposedMat(L);
  a:=[[delta^(q+1),0],[0,delta^(-q-1)]]*one;
  d:=[[1/2*(delta^(q-1)+delta^(-q+1)),1/2*mu*(delta^(q-1)-delta^(-q+1))]
   ,[1/2*mu^(-1)*(delta^(q-1)-delta^(-q+1)),1/2*(delta^(q-1)+delta^(-q+1))]]*one;
  D:=NullMat(n,n,F);
  for i in [1..n-4] do
    D[i][i]:=1;
  od;
  #InsertBlock(TILDED,a,n-3,n-3);
  D{[n-3,n-2]}{[n-3,n-2]}:=a;
  #InsertBlock(TILDED,d,n-1,n-1);
  D{[n-1,n]}{[n-1,n]}:=d;
  D:=TransposedMat(D);
  Gens:=[U,L,D];
  if n <= 4 then
    p:=IdentityMat(n,F);
  elif n > 4 then
    p:=NullMat(n,n,F);
    #InsertBlock(TILDEp,I,1,3);
    p{[1..Length(I)]}{[3..2+Length(I[1])]}:=I;
    #InsertBlock(TILDEp,-I,3,1);
    p{[3..2+Length(I)]}{[1..Length(I[1])]}:=-I;
    for i in [5..n] do
      p[i][i]:=1;
    od;
  fi;
  Add(Gens,p);
  #   if n gt 6 then
  h:=NullMat(n,n,F);
  m:=n-2;
  for i in [1..QuoInt(m,2)-1] do
    x:=(i-1)*2+1;
    y:=x+2;
    #InsertBlock(TILDEh,I,x,y);
    h{[x..x+Length(I)-1]}{[y..y+Length(I[1])-1]}:=I;
  od;
  #InsertBlock(TILDEh,(-1)^(QuoInt(n,2))*I,m-1,1);
  h{[m-1..m-1+Length(I)-1]}{[1..Length(I[1])]}:=(-1)^(QuoInt(n,2))*I;
  #InsertBlock(TILDEh,I,n-1,n-1);
  h{[n-1..n-1+Length(I)-1]}{[n-1..n-1+Length(I[1])-1]}:=I;
  Add(Gens,h);
  #   end if;
  if SpecialGroup then
    m:=IdentityMat(n,F);
    if q mod 4=3 then
      m[1][1]:=-1;
      m[2][2]:=-1;
    else
      m[n-1][n-1]:=-1;
      m[n][n]:=-1;
    fi;
    Add(Gens,m);
  fi;
  gens:=List(Gens,x->ImmutableMatrix(F,x));
  return rec(val1:=gens,
    val2:=varE);
end);

InstallGlobalFunction(ClassicalStandardGenerators,function(type,d,F)
#  -> ,]  return the Leedham - Green and O ' Brien standard generators for the
#  quasisimple classical group of specified type in dimension d and defining
#  field F ; the string type := one of SL , Sp , SU , Omega , Omega + , Omega -
local PresentationGenerators,SpecialGroup,q,l,w,gens;
  SpecialGroup:=ValueOption("SpecialGroup");
  if SpecialGroup=fail then
    SpecialGroup:=false;
  fi;
  PresentationGenerators:=ValueOption("PresentationGenerators");
  if PresentationGenerators=fail then
    PresentationGenerators:=false;
  fi;

  if IsInt(F) then
    if not IsPrimePowerInt(F) then
      Error("<q> must be a prime power");
    fi;
    q:=F;
    F:=GF(q);
  else
    if not IsField(F) and IsFinite(F) then 
      Error("<F> must be a finite field");
    fi;
    q:=Size(F);
  fi;

  if not type in ["SL","Sp","SU","Omega","Omega+","Omega-"] then
    Error("Type is not valid");
  fi;
  if not d > 1 then
    Error("Dimension is not valid");
  fi;
  if type="Omega" then
      if not IsOddInt(d) and IsOddInt(Size(F)) then
      Error("Dimension and field size must be odd");
    fi;
  fi;
  if type in Set(["Omega+","Omega-"]) then
      if not (IsEvenInt(d) and d >= 4) then
      Error("Dimension must be even and at least 4");
    fi;
  fi;
  if PresentationGenerators=true then
    l := Internal_PresentationGenerators@(type,d,Size(F));
  elif type="SL" then
    l := SLChosenElements@(SL(d,F));
  elif type="Sp" then
    l := SpChosenElements@(SP(d,F));
  elif type="SU" then
    # need to do `Size` as field not recognized by SU. And no extra 2 needed
    l := SUChosenElements@(SU(d,Size(F)));
  elif type="Omega" then
    l := SOChosenElements@(Omega(d,F):SpecialGroup:=SpecialGroup);
  elif type="Omega+" then
    l := PlusChosenElements@(OmegaPlus(d,Size(F))
     :SpecialGroup:=SpecialGroup);
    #   avoid OmegaMinus -- it sets order, too hard for large d, q
  elif type="Omega-" then
#    Cannot do so, as we don't have ChevalleyGroup command
#    return MinusChosenElements@(ChevalleyGroup("2D",QuoInt(d,2),F)
#     :SpecialGroup:=SpecialGroup);
    # just use the presentation generators and translate
    l := Internal_PresentationGenerators@(type,d,Size(F));
    w:=MinusPresentationToStandard@classicpres(d,Size(F));
    gens:=GeneratorsOfGroup(FamilyObj(w)!.wholeGroup);
    l:=List(w,x->MappedWord(x,gens,l));
  fi;
  if type="SU" then F:=GF(F,2);fi;
  l:=List(l,x->ImmutableMatrix(F,x));
  return l;
end);

