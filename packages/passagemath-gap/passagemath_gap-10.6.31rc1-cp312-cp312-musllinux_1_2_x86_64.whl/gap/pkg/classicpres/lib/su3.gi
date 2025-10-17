# Partially checked (up to line 409) MW 19/07/19

#   Explicit version of presentation for SU(3, q)
#   Last revised Ocotober 2018
#   to get paper version V (alpha, beta)
#   call V(alpha, beta - psi * alpha^(1+q))
BindGlobal("VMatrix@",function(q,alpha,gamma)
local F,beta,psi,v,w;
  F:=GF(q^2);
  w:=PrimitiveElement(F);
  if IsEvenInt(q) then
    # was "psi:=Trace(w,GF(q))^(-1)*w;"
    psi:=Trace(F,GF(q),w)^(-1)*w;
    Assert(1,psi=1/(1+w^(q-1)));
  else
    psi:=(-1/2)*w^0;
  fi;
  beta:=psi*alpha^(1+q)+gamma;
  v:=[[1,alpha,beta],[0,1,-alpha^q],[0,0,1]]*One(F);
  return v;
end);

BindGlobal("DeltaMatrix@",function(q,alpha)
local delta;
  delta:=DiagonalMat([alpha,alpha^(q-1),alpha^-q]*Z(q)^0);
  return delta;
end);

BindGlobal("TauMatrix@",function(q,gamma)
local F,tau;
  F:=GF(q^2);
  tau:=[[1,0,gamma],[0,1,0],[0,0,1]]*One(F);
  return tau;
end);

BindGlobal("TMatrix@",function(q)
local t,f;
  f:=GF(q^2);
  t:=NullMat(3, 3, f);
  t[1][3]:=One(f);
  t[2][2]:=-One(f);
  t[3][1]:=One(f);
  return t;
end);

BindGlobal("BorelGenerators@",function(q)
local F,alpha,beta,delta,tau,v,w;
  F:=GF(q^2);
  w:=PrimitiveElement(F);
  v:=VMatrix@(q,1,0);
  beta:=v[1][3];
  alpha:=v[1][2];
  Assert(1,Trace(F,GF(q),beta)=-alpha^(q+1));
  if IsEvenInt(q) then
    tau:=TauMatrix@(q,1);
  else
    tau:=TauMatrix@(q,w^(QuoInt((q+1),2)));
  fi;

  delta:=DeltaMatrix@(q,w);
  return [v,tau,delta];
end);

BindGlobal("SU32Generators@",function()
local lvarDelta,F,beta0,q,t,v,v1,w,w0;
  q:=2;
  F:=GF(q^2);
  w:=PrimitiveElement(F);
  w0:=w^(q+1);
  beta0:=w^(1+QuoInt((q^2+q),2));
  v:=VMatrix@(q,1,0);
  v1:=VMatrix@(q,w^2,0);
  lvarDelta:=DeltaMatrix@(q,w);
  t:=TMatrix@(q);
  return [v,v1,lvarDelta,t];
end);

BindGlobal("SU3Generators@",function(q)
if q=2 then
    return SU32Generators@();
  fi;
  return Concatenation(BorelGenerators@(q),[TMatrix@(q)]);
end);

#   g is upper-triangular matrix with just one non-zero entry in top right
#  corner;
#  write as word in Borel subgroup generators
BindGlobal("SpecialSLPForElement@",function(g,q,W)
local lvarDelta,F,Gens,R,lvarTau,V,c,delta,entry,matrix,tau,theta,v,w,word,z;

  if g=g^0 then
    return Identity(W);
    #return rec(val1:=Identity(W), val2:=g);
  fi;
  Assert(1,IsOne(g[1][1]) and IsZero(g[1][2]) and IsZero(g[2][3]));
  v:=W.1;
  tau:=W.2;
  delta:=W.3;
  F:=GF(q^2);
  w:=PrimitiveElement(F);
  Gens:=SU3Generators@(q);
  V:=Gens[1];
  lvarTau:=Gens[2];
  lvarDelta:=Gens[3];
  entry:=lvarTau[1][3];

  z:=g[1][3];
  if z<>0 then
    theta:=w^-(q+1);
    #R:=SubStructure(F,theta);
    #c:=Eltseq((entry^-1*z)*FORCEOne(R));
    R:=Field(theta);
    c:=List([0..DegreeOverPrimeField(R)-1],x->theta^x);
    R:=Basis(R,c);

    c:=Coefficients(R,(entry^-1*z));
    c:=List(c,Int);
    word:=Product(List([1..Size(c)],i->(tau^(delta^(i-1)))^c[i]));
    matrix:=Product(List([1..Size(c)],i->(lvarTau^(lvarDelta^(i-1)))^c[i]));
    g:=matrix^-1*g;
    Assert(1,IsZero(g[1][3]));
  fi;
  return word;
  #return rec(val1:=word, val2:=g);
end);



#   find solutions x and y to Lemma 4.1
BindGlobal("FindSolutions@",function(q)
local F,c,d,found,m,n,psi,t,w,w0,x,y;
  F:=GF(q^2);
  w:=PrimitiveElement(F);
  n:=q+1;
  m:=q-2;
  w0:=w^(q+1);
  if IsEvenInt(q) then
    x:=-(q+1) mod (q^2-1);
    # was "c:=Log(w0,(1-w0)^Z(q)^0);"
    c:=LogFFE((1-w0)*Z(q)^0,w0);
    y:=-c*(q+1) mod (q^2-1);
    Assert(1,IsOne(w^(x*m)+w^(y*m)) and IsOne(w^(-x*n)+w^(-y*n)));
    Assert(1,Size(Subfield(GF(q^2),[w^(x*m)]))=q 
     and Size(Subfield(GF(q^2),[w^(x*n)]))=q);
    return rec(val1:=x,
      val2:=y);
  fi;
  psi:=w^(QuoInt((q+1),2));
  for t in F do
    if t^2=psi^2 then
      continue;
    fi;
    c:=t*(t^2+3*psi^2)*(t+psi)*(t^2-psi^2)^-2;
    d:=(c-c^(q-1));
    if IsZero(c) or IsZero(d) then
      continue;
    fi;
    # was "x:=-Log(c) mod (q^2-1);"
    x:=-LogFFE(c,w) mod (q^2-1);
    y:=-LogFFE(d,w) mod (q^2-1);
    if IsOne(w^(x*m)+w^(y*m)) and IsOne(w^(-x*n)+w^(-y*n)) then
      found:=Size(Subfield(GF(q^2),[w^(x*m)]))=q^2 and
       Size(Subfield(GF(q^2),[w^(x*n)]))=q;
      if found then
        return rec(val1:=x,
          val2:=y);
      fi;
    fi;
  od;
  Error("Failed to find x and y");
end);

#   find two polynomials g, h of degree Degree (F) - 1 which satisfy
#      w^(2*q - 4) = g(r) + w^(q - 2) * h(r)
#   where r  = w^(x * (q - 2))
BindGlobal("TwoPolynomials@",function(varE,F,p,q,w,x)
local P,W,e,g,h,l,one,r,two,pair,Wb;
  e:=DegreeOverPrimeField(F);
  r:=w^(x*(q-2));
  W:=Field(r);
  Wb:=List([0..DegreeOverPrimeField(W)-1],x->r^x);
  Wb:=Basis(W,Wb);
  one:=w^((q+1)*(q-2));
  two:=(w^(2*q-4)-one)*w^-(q-2);
  if one in W and two in W then
    # was "g:=Eltseq(one*FORCEOne(W))*FORCEOne(P);"
    g:=Coefficients(Wb,one);
    h:=Coefficients(Wb,two);
    g:=UnivariatePolynomial(F,g,1);
    h:=UnivariatePolynomial(F,h,1);
    if w^(2*q-4)=Value(g,r)+w^(q-2)*Value(h,r) then
      return rec(val1:=g,
        val2:=h);
    fi;
  fi;
  #   possibly solution is wrong: if so, must search over q^2 elements
  pair:=ForAny(F, u->ForAny(F, z->z+w^(q-2)*u=w^(2*q-4)));
  one:=pair[1];
  two:=pair[2];
  # was "g:=Eltseq(one*FORCEOne(W))*FORCEOne(P);"
  g:=Coefficients(Wb,one);
  h:=Coefficients(Wb,two);
  g:=UnivariatePolynomial(F,g,1);
  h:=UnivariatePolynomial(F,h,1);
  Assert(1,w^(2*q-4)=Value(g,r)+w^(q-2)*Value(h,r));
  return rec(val1:=g,
    val2:=h);
end);

#   Presentation for Borel subgroup
#   power relation needed in Borel presentation only
#   if used to set up SU(3, q) then AddPower = false;
BindGlobal("BorelPresentation@",function(q)
local A,AddPower,B,lvarDelta,varE,F,Gens,I,K,L,R,Rels,
   lvarTau,V,W,a,b,b1,b2,b3,b4,delta,e,
   f,lhs,m1,m2,m3,m4,matrix,p,rhs,tau,theta,v,w,w0,word,x,y;
  AddPower:=ValueOption("AddPower");
  if AddPower=fail then AddPower:=false; fi;
  W:=FreeGroup("v","tau","delta");
  W:=Group(StraightLineProgGens(GeneratorsOfGroup(W)));
  v:=W.1;
  tau:=W.2;
  delta:=W.3;
  varE:=GF(q^2);
  F:=GF(q);
  e:=DegreeOverPrimeField(F);
  p:=Characteristic(varE);
  w:=PrimitiveElement(varE);
  w0:=w^(q+1);
  theta:=w^(q-2);
  Gens:=BorelGenerators@(q);
  V:=Gens[1];
  lvarTau:=Gens[2];
  lvarDelta:=Gens[3];
  y:=FindSolutions@(q);
  x:=y.val1;
  y:=y.val2;
  A:=(lvarDelta^1)^x;
  B:=(lvarDelta^1)^y;
  Rels:=[];
  #   R1
  a:=(delta^1)^x;
  b:=(delta^1)^y;
  #   this relation can be omitted for SU(3, q)
  if AddPower then
    Add(Rels,delta^(q^2-1));
  fi;
  if IsEvenInt(q) then
    Add(Rels,v^2/tau);
  else
    Add(Rels,v^p);
  fi;
  Add(Rels,tau^p);
  #   R2
  Add(Rels,tau/(tau^(a)*tau^(b)));
  if IsOddInt(p) then
    Add(Rels,tau/(tau^(b)*tau^(a)));
  fi;
  if e > 1 then
    m1:=MinimalPolynomial(PrimeField(varE), w0^-x);
    b1:=CoefficientsOfUnivariatePolynomial(m1);
    b1:=List(b1,Int);
    Add(Rels,Product(List([1..Size(b1)],i->(tau^(a^(i-1)))^b1[i])));
  fi;
  if e=1 or Gcd(x,q^2-1) > 1 then

    b2:=w0^-x;
    K:=Field(b2);
    b2:=List([0..DegreeOverPrimeField(K)-1],x->b2^x);
    K:=Basis(K,b2);

    # was "b2:=Eltseq((w0^-1)*FORCEOne(K));"
    b2:=Coefficients(K,(w0^-1));
    b2:=List(b2,Int);
    Add(Rels,Product(List([1..Size(b2)],i->(tau^(a^(i-1)))^b2[i]))
     /tau^(delta));
  fi;
  #   R3
  #   (i)
  lhs:=v;
  rhs:=v^a*v^b*SpecialSLPForElement@((V^A*V^B)^-1*V,q,W);
  Add(Rels,lhs/rhs);
#Print("L1=",Length(Rels),"\n");
  if IsOddInt(p) then
    lhs:=v;
    rhs:=v^b*v^a*SpecialSLPForElement@((V^B*V^A)^-1*V,q,W);
    Add(Rels,lhs/rhs);
  fi;
  #   (ii)
  Add(Rels,Comm(v^a,tau));
  Add(Rels,Comm(v^b,tau));
  #   (iii)
  lhs:=Comm(v,v^a);
  rhs:=SpecialSLPForElement@(Comm(V,V^A),q,W);
  Add(Rels,lhs/rhs);
  #   (iv)
  if IsEvenInt(q) and e > 1 then
    lhs:=Comm(v^delta,v^a);
    rhs:=SpecialSLPForElement@(Comm(V^lvarDelta,V^A),q,W);
    Add(Rels,lhs/rhs);
    lhs:=Comm(v^delta,v^b);
    rhs:=SpecialSLPForElement@(Comm(V^lvarDelta,V^B),q,W);
    Add(Rels,lhs/rhs);
  fi;
  #   (v)
  m2:=MinimalPolynomial(PrimeField(F),w^(x*(q-2)));
  b:=CoefficientsOfUnivariatePolynomial(m2);
  b:=List(b,Int);
  lhs:=Product(List([1..Size(b)],i->(v^(a^(i-1)))^b[i]));
  matrix:=Product(List([1..Size(b)],i->(V^(A^(i-1)))^b[i]));
  rhs:=SpecialSLPForElement@(matrix,q,W);
  Add(Rels,lhs/rhs);
  #   (vi)
  if IsOddInt(q) and Gcd(x,q^2-1) > 1 then

    b:=w^(x * (q - 2));
    K:=Field(b);
    b:=List([0..DegreeOverPrimeField(K)-1],x->b^x);
    K:=Basis(K,b);

    # was "b:=Eltseq((w^(q-2))*FORCEOne(K));"

    b:=Coefficients(K, (w^(q-2)));
    b:=List(b,Int);
    L:=V^(lvarDelta);
    R:=Product(List([1..Size(b)],i->(V^(A^(i-1)))^b[i]));
    matrix:=R^-1*L;
    word:=SpecialSLPForElement@(matrix,q,W);
    lhs:=v^delta;
    rhs:=Product(List([1..Size(b)],i->(v^(a^(i-1)))^b[i]))*word;
    Add(Rels,lhs/rhs);
  elif IsEvenInt(q) then
    m4:=TwoPolynomials@(varE,F,p,q,w,x);
    m3:=m4.val1;
    m4:=m4.val2;
    b3:=CoefficientsOfUnivariatePolynomial(m3);
    b3:=List(b3,Int);
    b4:=CoefficientsOfUnivariatePolynomial(m4);
    b4:=List(b4,Int);
    L:=V^(lvarDelta^2);
    R:=Product(List([1..Size(b3)],i->(V^(A^(i-1)))^b3[i]))
     *Product(List([1..Size(b4)],i->(V^(lvarDelta*A^(i-1)))^b4[i]));
    matrix:=R^-1*L;
    word:=SpecialSLPForElement@(matrix,q,W);
    lhs:=v^(delta^2);
    rhs:=Product(List([1..Size(b3)],i->(v^(a^(i-1)))^b3[i]))
     *Product(List([1..Size(b4)],i->(v^(delta*a^(i-1)))^b4[i]))*word;
    Add(Rels,lhs/rhs);
  fi;
  return W/Rels;
end);

BindGlobal("ChooseGamma@",function(q,beta,eta,w,zeta)
local gamma,t,x;
  Assert(1,Trace(GF(q^2),GF(q),eta)<>0);
  # was "Assert(1,Trace(beta,GF(q))<>0);"
  Assert(1,Trace(GF(q^2),GF(q),beta)<>0);
  t:=Trace(GF(q^2),GF(q),beta)*Trace(GF(q^2),GF(q),eta)^-1;
  gamma:=t*eta-beta;
  Assert(1,IsZero(Trace(GF(q^2),GF(q),gamma)));
  x:=(w*zeta^-1)*(beta+gamma);
  Assert(1,x in GF(q) and x<>0);
  return gamma;
end);

#   definition of U0
BindGlobal("DefineU0@",function(q)
local lvarAlpha,F,alpha,beta0,eta,gamma0,n,t,w,w0,zeta;
  F:=GF(q^2);
  w:=PrimitiveElement(F);
  w0:=w^(q+1);
  beta0:=w^(1+QuoInt((q^2+q),2));
  t:=Trace(F,GF(q),beta0);
  n:=LogFFE(-t, w0);
  alpha:=w^n;
  Assert(1,alpha^(q+1)=-t);
  if q mod 3<>2 then
    lvarAlpha:=[alpha];
  else
    lvarAlpha:=[alpha,alpha*w^(q-1),alpha*w^(2*(q-1))];

    #Assert(1,ForAll(lvarAlpha,a->a^(q+1)=-t) and IsPower(w^(q-1),3)=false and
    # IsPower(w^(2*(q-1)),3)=false);
    Assert(1,ForAll(lvarAlpha,a->a^(q+1)=-t) and [3]<>Set(Factors(w^(q-1))) and
     [3]<>Set(Factors(w^(2*(q-1)))));
  fi;
  zeta:=-w^(QuoInt((q^2+q),2));
  Assert(1,zeta^2=w0);
  eta:=w^-1*zeta;
  gamma0:=ChooseGamma@(q,beta0,eta,w,zeta);
  return rec(val1:=lvarAlpha,
    val2:=gamma0);
end);

BindGlobal("MatrixToTuple@",function(F,A)
local alpha,beta,psi,q,w;
  if IsMatrix(A) then A:=A[1];fi;
  q:=RootInt(Size(F),2);
  w:=PrimitiveElement(F);
  alpha:=A[2];
  beta:=A[3];
  if IsEvenInt(q) then
    psi:=Trace(F,GF(q),w)^(-1)*w;
  else
    psi:=-1/2;
  fi;
  beta:=A[3]-psi*(alpha^(1+q));
  return [alpha,beta];
end);

BindGlobal("TupleToMatrix@",function(q,v)
  return VMatrix@(q,v[1],v[2]);
end);

BindGlobal("ComputeRight@",function(q,U)
local F,V,m,r,s,t;
  F:=GF(q^2);
  r:=Reversed(U[1]);
  s:=ShallowCopy(NormedRowVector(r));
  s[2]:=-s[2];
  t:=MatrixToTuple@(F,s);
  m:=TupleToMatrix@(q,t);
  Assert(1,MatrixToTuple@(F,m)=t);
  return [m,t];
end);

BindGlobal("ProcessRelation@",function(G,v)
local F,U,d,left,lv,q,rest,right,rv,t;
  F:=DefaultFieldOfMatrixGroup(G);
  q:=RootInt(Size(F),2);
  t:=TMatrix@(q);
  U:=TupleToMatrix@(q,v);
  rv:=ComputeRight@(q,U);
  right:=rv[1];
  rv:=rv[2];
  rest:=t^-1*U*t*right^-1*t^-1;
  d:=DiagonalMat(List([1..Length(rest)],i->rest[i][i]));
  left:=rest*d^-1;
  #Assert(1,IsUpperTriangular(left));
  lv:=MatrixToTuple@(F,left);
  Assert(1,t^-1*U*t=left*d*t*right);
  return rec(val1:=lv,
    val2:=rv,
    val3:=left,
    val4:=d,
    val5:=t,
    val6:=right);
end);

#   construct v-matrix whose 1, 2 entry is w^power, as word
#  in delta = Delta (w) and v = VMatrix(1, 0),
#  where w is primitive element for GF(q^2)
BindGlobal("ConstructVMatrix@",function(q,delta,v,power)
local A,varE,F,I,m,n,nu,w,z;
  # =v= MULTIASSIGN =v=
  m:=Gcdex(q-2,q^2-1);
  z:=m.gcd; #gcd
  n:=m.coeff1; #n*(q-2)+m*(q^2-1)=gcd
  m:=m.coeff2;
  # =^= MULTIASSIGN =^=
  F:=GF(q^2);
  w:=PrimitiveElement(F);
  nu:=w^z;

  varE:=Field(nu);
  varE:=Basis(varE,List([0..DegreeOverPrimeField(varE)-1],x->nu^x));

  # was "A:=Eltseq(power*FORCEOne(varE));"
  A:=Coefficients(varE, power);
  A:=List(A,Int);
  return Product(List([0..Length(A)-1],i->(v^(delta^(n*i)))^A[i+1]));
end);

#   construct tau-matrix whose 1, 3 entry is power, as word in
#  tau = TauMatrix (a) where a = w^((q+ 1) div 2) or 1 and
#  delta = Delta (w), where w is primitive element for GF(q^2)
BindGlobal("ConstructTauMatrix@",function(q,delta,tau,power)
local A,varE,Eb,F,I,gamma,w,w0;
  F:=GF(q^2);
  w:=PrimitiveElement(F);
  w0:=w^(q+1);
  varE:=Field(w0);
  Eb:=List([0..DegreeOverPrimeField(varE)-1],x->w0^x);
  Eb:=Basis(varE,Eb);
  if IsOddInt(q) then
    gamma:=power/w^(QuoInt((q+1),2));
  else
    gamma:=power;
  fi;
  Assert(1,gamma in varE);
  # was "A:=Eltseq(gamma*FORCEOne(varE));"
  A:=Coefficients(Eb,gamma);
  A:=List(A,Int);
  return Product(List([0..Size(A)-1],i->(tau^(delta^(-i)))^A[i+1]));
end);

#   write matrix mat as word in Borel subgroup generators delta, v, tau
BindGlobal("SLPForElement@",function(q,delta,v,tau,mat_v,mat,wdelta,wv,wtau)
local A,B,a,b,m,wA,wB;
  a:=mat_v[1];
  if not IsZero(a) then
    A:=ConstructVMatrix@(q,delta,v,a);
    wA:=ConstructVMatrix@(q,wdelta,wv,a);
  else
    A:=v^0;
    wA:=wv^0;
  fi;
  m:=A*mat^-1;
  b:=m[1][3];
  B:=ConstructTauMatrix@(q,delta,tau,m[1][3]);
  wB:=ConstructTauMatrix@(q,wdelta,wtau,m[1][3]);
  Assert(1,mat=A*B^-1);
  return rec(val1:=wA,
    val2:=wB^-1,
    val3:=A,
    val4:=B^-1);
end);

BindGlobal("R2Relations@",function(q)
local lvarAlpha,F,G,L,R,U,W,a,a1,b,b1,beta0,d,delta,e,gamma0,i,left,lhs,
   lv,m,mats,
   pow,psi,rhs,right,rv,t,tau,tau0,u,v,w,w0,w1,wdelta,wlhs,wrhs,wt,wtau,wv,x,x1,
   y,y1,z,z1;

  F:=GF(GF(q),2);
  w:=PrimitiveElement(F);
  w0:=w^(q+1);
  beta0:=w^(1+QuoInt((q^2+q),2));
  G:=SU(3,q);
  L:=SU3Generators@(q);
  v:=L[1];
  tau:=L[2];
  delta:=L[3];
  t:=L[4];
  W:=FreeGroup(4);
  W:=Group(StraightLineProgGens(GeneratorsOfGroup(W)));
  wv:=W.1;
  wtau:=W.2;
  wdelta:=W.3;
  wt:=W.4;
  gamma0:=DefineU0@(q);
  lvarAlpha:=gamma0.val1;
  gamma0:=gamma0.val2;
  if IsEvenInt(q) then
    psi:=Trace(F,w)^(-1)*w;
  else
    psi:=-1/2;
  fi;
  tau0:=VMatrix@(q,0,gamma0);
  mats:=[];
  for i in [1..Size(lvarAlpha)] do
    e:=beta0-psi*lvarAlpha[i]^(q+1);
    Add(mats,VMatrix@(q,lvarAlpha[i],e));
  od;
  mats:=Concatenation(mats,List(mats,m->m*tau0));
  Add(mats,tau0);
  U:=List( mats,m->MatrixToTuple@(F,m));
  #   determine relation u^t = u_L * Delta^pow * t * u_r
  R:=[];
  for u in U do
    right:=ProcessRelation@(G,u);
    lv:=right.val1;
    rv:=right.val2;
    left:=right.val3;
    d:=right.val4;
    t:=right.val5;
    right:=right.val6;
    pow:=LogFFE(d[1][1],PrimitiveElement(F));
    m:=TupleToMatrix@(q,u);
    b1:=SLPForElement@(q,delta,v,tau,u,m,wdelta,wv,wtau);
    a:=b1.val1;
    b:=b1.val2;
    a1:=b1.val3;
    b1:=b1.val4;
    y1:=SLPForElement@(q,delta,v,tau,lv,left,wdelta,wv,wtau);
    x:=y1.val1;
    y:=y1.val2;
    x1:=y1.val3;
    y1:=y1.val4;
    w1:=SLPForElement@(q,delta,v,tau,rv,right,wdelta,wv,wtau);
    z:=w1.val1;
    w:=w1.val2;
    z1:=w1.val3;
    w1:=w1.val4;
    lhs:=t^-1*a1*b1*t;
    rhs:=(x1*y1)*delta^pow*t*z1*w1;
    Assert(1,lhs=rhs);
    wlhs:=wt^-1*a*b*wt;
    wrhs:=(x*y)*wdelta^pow*wt*z*w;
    Add(R,wlhs/wrhs);
  od;
  return W/R;
end);

#   presentation for SU(3, 2) on its standard generators
BindGlobal("SU32Presentation@",function()
local F,Projective,Q,R,Rels,W,phi;
  Projective:=ValueOption("Projective");
  if Projective=fail then
    Projective:=false;
  fi;
  F:=FreeGroup(7);
  F:=Group(StraightLineProgGens(GeneratorsOfGroup(F)));
  Q:=F/[F.1^2/One(F),
    F.2/One(F),
    F.3^2/One(F),
    F.4^-1*F.3*F.4^-1/One(F),
    F.6^-1*F.3*F.6^-1/One(F),
    F.4^-1*F.6^-1*F.4*F.6^-1/One(F),
    F.5/One(F),
    (F.3*F.1)^3/One(F),
    F.1*F.4*F.1*F.4^-1*F.1*F.6^-1*F.1*F.6/One(F),
    F.1*F.6^-1*F.1*F.4^-1*F.1*F.4*F.6^-1*F.7/One(F)];
  W:=FreeGroup(7);
  W:=Group(StraightLineProgGens(GeneratorsOfGroup(W)));
  Rels:=RelatorsOfFpGroup(Q);
  phi:=GroupHomomorphismByImages(FreeGroupOfFpGroup(Q),W,
    FreeGeneratorsOfFpGroup(Q),GeneratorsOfGroup(W));
  Rels:=List(Rels,r->ImagesRepresentative(phi,r));
  if Projective then
    Add(Rels,W.7^2);
  fi;
  return W/Rels;
end);


#   presentation for SU(3, q) for q = 2, 3, 5 on presentation generators
BindGlobal("ExceptionalCase@",function(q)
local F,lvarGamma,R,T,a,b,t,tau,v,v1;
  if q=2 then
    F:=FreeGroup("v","v1","Gamma","t");
    F:=Group(StraightLineProgGens(GeneratorsOfGroup(F)));
    # Implicit generator Assg from previous line.
    v:=F.1;
    v1:=F.2;
    lvarGamma:=F.3;
    t:=F.4;
    a:=Comm(v,t);
    b:=(a^2)^v;
    T:=[a/Comm(v,t),b/(a^2)^v,a^3,b^3,lvarGamma^3,
    Comm(a,lvarGamma),Comm(b,lvarGamma),
    Comm(a,b)*lvarGamma,a^v*b,b^v/(a*lvarGamma^1),a^v1/(a*b*a),
    b^v1/(a*b*lvarGamma^1),
    v^2/v1^2,v1^2/Comm(v,v1),t/(v^2*a^2*b)];
  elif q=3 then
    F:=FreeGroup("v","tau","Gamma","t");
    F:=Group(StraightLineProgGens(GeneratorsOfGroup(F)));
    # Implicit generator Assg from previous line.
    v:=F.1;
    tau:=F.2;
    lvarGamma:=F.3;
    t:=F.4;
    T:=[F.1^3,F.4^2,F.3^-1*F.1^-1*F.3^-1*F.2^-1*F.1*F.3^2*F.1^-1
     ,F.3^-1*F.1*F.3^-1*F.2^-1*F.1^-1*F.3^2*F.1
     ,F.2*F.4*F.3^-2*F.2*F.4*F.2*F.4
     ,F.3*F.2^-1*F.1^-1*F.4*F.3*F.2^-1*F.1*F.3*F.4*F.1*F.2^-1*F.4];
  elif q=5 then
    F:=FreeGroup(4);
    F:=Group(StraightLineProgGens(GeneratorsOfGroup(F)));
    T:=[F.1^5,F.3^1*F.2^2*F.3^-1*F.2
     ,F.3^2*F.1^2*F.3^-2*F.1^-1,
     F.3^5*F.4*F.3*F.4
     ,F.3^-1*F.1*F.4*F.1^-2*F.4*F.1*F.3*F.4
     ,F.3*F.1*F.3^-1*F.2^-1*F.1^-1*F.3*F.1^-1*F.3^-1*F.1
     ,
     F.1^-1*F.4*F.2^-1*F.1^-1*F.4*F.3^-1*F.1^2*F.4*F.3*F.1^-1*F.4*F.3*F.2^-1];

       fi;
  return F/T;
end);

BindGlobal("SU3Presentation@",function(q)
local Q,R,R1,R2,Rels,W,delta,phi,t,tau,v;
  if q in [2,3,5] then
    return ExceptionalCase@(q);
  fi;
  W:=FreeGroup("v","tau","delta","t");
  W:=Group(StraightLineProgGens(GeneratorsOfGroup(W)));
  v:=W.1;
  tau:=W.2;
  delta:=W.3;
  t:=W.4;
  #   relations of type R1
  R1:=BorelPresentation@(q);
  Q:=FreeGroupOfFpGroup(R1);
  R1:=RelatorsOfFpGroup(R1);
  phi:=GroupHomomorphismByImages(Q,W,
    GeneratorsOfGroup(Q),GeneratorsOfGroup(W){[1..3]});
  Rels:=List(R1,r->ImagesRepresentative(phi,r));
#Print("L=",Length(Rels),"\n");
  #   relations of type R2
  R2:=R2Relations@(q);
  Q:=FreeGroupOfFpGroup(R2);
  R2:=RelatorsOfFpGroup(R2);
  phi:=GroupHomomorphismByImages(Q,W,
     GeneratorsOfGroup(Q),GeneratorsOfGroup(W){[1..4]});
  Rels:=Concatenation(Rels,List(R2,r->ImagesRepresentative(phi,r)));
#Print("L=",Length(Rels),"\n");
  Add(Rels,t^2);
  Add(Rels,delta^t/delta^-q);
  return W/Rels;
  #Rels:=List(Rels,r->LHS(r)*RHS(r)^-1);
  #return rec(val1:=W,
  #  val2:=Rels);
end);

#  S := Evaluate (R, X); assert #Set (S) eq 1;
#  end if;
#  end for;
#
#  for e in [2..20] do
#  e;
#  q := 2^e;
#  G, R := SU3Presentation (q);
#  X := SU3Generators (q);
#  S := Evaluate (R, X); assert #Set (S) eq 1;
#  end for;
#
#  SetGlobalTCParameters (:Hard, CosetLimit:=10^8, Print:=10^5);
#  for q in [2..1000] do
#  if IsPrimePower (q) then
#  q;
#  Q, R := SU3Presentation (q);
#  X := SU3Generators (q);
#  S := Evaluate (R, X); assert #Set (S) eq 1;
#  F := SLPToFP (Q, R);
#  H := sub<F | F.1, F.2, F.3>;
#  I := CosetImage (F, H);
#  RandomSchreier (I);
#  "Comp factors", CompositionFactors (I);
#  end if;
#/  end for;
