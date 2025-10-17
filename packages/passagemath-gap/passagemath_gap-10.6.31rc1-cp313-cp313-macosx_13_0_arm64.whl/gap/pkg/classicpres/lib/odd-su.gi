#  File converted from Magma code -- requires editing and checking
#  Magma -> GAP converter, version 0.5, 11/5/18 by AH

BindGlobal("OddSUGenerators@",function(d,q)
local F,lvarGamma,S,U,V,alpha,gamma,i,phi,psi,sigma,t,tau,v,w,x,one;
  Assert(1,IsOddInt(d));
  F:=GF(q^2);
  one:=One(F);
  w:=PrimitiveElement(F);
  #   define tau
  tau:=IdentityMat(d, F);
  # rewritten select statement
  if IsEvenInt(q) then
    psi:=one;
  else
    psi:=w^(QuoInt((q+1),2));
  fi;
  tau[1][2]:=-psi;
  #   define Gamma
  lvarGamma:=Concatenation([w^-1,w^q],List([3..d-1],i->one),[w^(1-q)]);
  lvarGamma:=DiagonalMat(lvarGamma);
  #   define t
  t:=NullMat(d,d,F);
  t[1][2]:=one;
  t[2][1]:=one;
  t[d][d]:=-one;
  for i in [3..d-1] do
    t[i][i]:=one;
  od;
  #   define v
  alpha:=one;
  if IsEvenInt(q) then
    # was "phi:=Trace(w,GF(q))^(-1)*w;"
    phi:=Trace(F,GF(q),w)^(-1)*w;
    Assert(1,phi=w/(w+w^q));
  else
    phi:=-1/2;
  fi;
  gamma:=phi*alpha^(1+q);
  v:=NullMat(d,d,F);;
  v[1][1]:=one;
  v[1][2]:=gamma;
  v[1][d]:=alpha;
  for i in [2..d] do
    v[i][i]:=one;
  od;
  v[d][2]:=-alpha^q;
  #   U and V
  S:=ClassicalStandardGenerators("SU",d,q:
    PresentationGenerators:=false);
  U:=S[5];
  V:=S[2];
  S:=ClassicalStandardGenerators("SU",d-1,q:
    PresentationGenerators:=false);
  x:=S[6]^(S[2]^2);
  sigma:=NullMat(d,d,F);
  # was "InsertBlock(TILDEsigma,x,1,1);"
  sigma{[1..NrRows(x)]}{[1..NrCols(x)]}:=x;
  sigma[d][d]:=one;
  return [lvarGamma,t,U,V,sigma,tau,v];
end);

BindGlobal("Odd_SU_PresentationForN@",function(n,q)
local F,lvarGamma,OMIT,R,Rels,S,U,V,t,tau;
  F:=FreeGroup("Gamma","t","U","V");
  F:=Group(StraightLineProgGens(GeneratorsOfGroup(F)));
  lvarGamma:=F.1;
  t:=F.2;
  U:=F.3;
  V:=F.4;
  Rels:=[];
  R:=PresentationForSn@(n);
  S:=FreeGroupOfFpGroup(R);
  R:=RelatorsOfFpGroup(R);
  tau:=GroupHomomorphismByImages(S,F, GeneratorsOfGroup(S), [U,V]);
  R:=List(R,r->ImagesRepresentative(tau,r));
  OMIT:=true;
  if not OMIT then
    Add(Rels,lvarGamma^(q^2-1));
    Add(Rels,t^2);
    Add(Rels,lvarGamma^t/lvarGamma^-q);
  fi;
  if n > 2 then
    Add(Rels,Comm(lvarGamma,U^V));
    Add(Rels,Comm(t,U^V));
  fi;
  if n > 3 then
    Add(Rels,Comm(lvarGamma,V*U));
    Add(Rels,Comm(t,V*U));
  fi;
  Add(Rels,Comm(lvarGamma,lvarGamma^U));
  Add(Rels,Comm(t,t^U));
  Add(Rels,Comm(lvarGamma,t^U));
  Rels:=Concatenation(Rels,R);
  return F/Rels;
end);

#Order_Odd_SU_N:=function(n,q)
#local a;
#  a:=(q^2-1)*2;
#  return a^n*Factorial(n);
#end;

BindGlobal("OddSUPresentation@",function(d,q)
local lvarDelta,varE,F,lvarGamma,K,OMIT,Projective,Q,R,R3,R4,lvarR_N,
   R_SL2,R_SU3,Rels,U,V,W,
   varZ,a,e,f,m,n,p,phi,r,rhs,sigma,t,tau,v,w,w0,gens;

  Projective:=ValueOption("Projective");
  if Projective=fail then
    Projective:=false;
  fi;
  Assert(1,IsOddInt(d) and d >= 3);
  n:=QuoInt(d,2);
  if d=3 then
    if q=2 then
      return SU32Presentation@(:Projective:=Projective);
    else
      return SU3Presentation@(q:Projective:=Projective);
    fi;
  fi;
  e := Factors(q);
  if Size(DuplicateFreeList(e)) > 1 then
      f := false;
  else
      f := true;
      p := e[1];
      e := Size(e);
  fi;
  K:=GF(q^2);
  w:=PrimitiveElement(K);
  F:=FreeGroup("Gamma","t","U","V","sigma","tau","v");
  F:=Group(StraightLineProgGens(GeneratorsOfGroup(F)));
  # we het high powers, so use SLPs
  gens:=StraightLineProgGens(GeneratorsOfGroup(F));
  lvarGamma:=gens[1];
  t:=gens[2];
  U:=gens[3];
  V:=gens[4];
  sigma:=gens[5];
  tau:=gens[6];
  v:=gens[7];
  lvarDelta:=lvarGamma*(lvarGamma^-1)^U;
  R:=[];
  #   centraliser of v
  if n > 2 then
    Add(R,Comm(U^V,v));
  fi;
  if n > 3 then
    Add(R,Comm(V*U,v));
  fi;
  if IsEvenInt(q) then
    Add(R,Comm(t^U,v));
  else
    m:=QuoInt((q^2-1),2);
    Add(R,Comm(t^U*lvarDelta^m,v));
  fi;
  if n=2 and q mod 3=1 then
    Add(R,Comm(lvarGamma^(q-1)*(lvarGamma^U)^3*Comm(t,lvarGamma^-1)^U,v));
  else
    Add(R,Comm(lvarGamma^(q-1)*(lvarGamma^U)^3,v));
  fi;
  if n > 2 then
    Add(R,Comm(lvarGamma^U*(lvarGamma^-1)^(V^2),v));
  fi;
  if IsEvenInt(q) then
    varZ:=t;
  else
    varZ:=t*lvarGamma^(QuoInt((q+1),2));
  fi;
  #   centraliser of sigma
  OMIT:=true;
  if not OMIT then
    if n > 3 then
      Add(R,Comm(U^(V^2),sigma));
    fi;
    if n > 4 then
      Add(R,Comm(V*U*U^V,sigma));
    fi;
    if n > 2 then
      Add(R,Comm(lvarGamma^(V^2),sigma));
      Add(R,Comm(t^(V^2),sigma));
    fi;
  fi;
  if IsEvenInt(q) then
    Add(R,Comm(U^t,sigma));
  else
    Add(R,Comm(U^t*varZ^2,sigma));
  fi;
  Add(R,Comm(lvarGamma*lvarGamma^U,sigma));
  lvarR_N:=Odd_SU_PresentationForN@(n,q);
  Q:=FreeGroupOfFpGroup(lvarR_N);
  lvarR_N:= RelatorsOfFpGroup(lvarR_N);
  phi:=GroupHomomorphismByImages(Q,F,
    GeneratorsOfGroup(Q),
    [lvarGamma,t,U,V]);
  lvarR_N:=List(lvarR_N,r->ImagesRepresentative(phi,r));
  #   tau = tau^-1 in char 2
  R_SU3:=SU3Presentation@(q);
  Q:=FreeGroupOfFpGroup(R_SU3);
  R_SU3:=RelatorsOfFpGroup(R_SU3);
  if q=2 then
    phi:=GroupHomomorphismByImages(Q,F,
      GeneratorsOfGroup(Q),
      [v,v^(lvarGamma^U),lvarGamma^-1,t]);
  else
    phi:=GroupHomomorphismByImages(Q,F,
      GeneratorsOfGroup(Q),
      [v,tau^-1,lvarGamma^-1,t]);
  fi;
  R_SU3:=List(R_SU3,r->ImagesRepresentative(phi,r));
  R_SL2:=PresentationForSL2@(p,2*e:Projective:=false);
  Q:=FreeGroupOfFpGroup(R_SL2);
  R_SL2:=RelatorsOfFpGroup(R_SL2);
  # rewritten select statement
  if IsEvenInt(q) then
    W:=U;
  else
    W:=U*varZ^2;
  fi;
  phi:=GroupHomomorphismByImages(Q,F,
    GeneratorsOfGroup(Q),
    [lvarDelta,sigma,W]);
  R_SL2:=List(R_SL2,r->ImagesRepresentative(phi,r));
  #   Steinberg relations
  R4:=[];
  Add(R4,Comm(v,v^U)/(sigma^-1)^(t^U));
  if q=4 then
    Add(R4,Comm(v,v^(lvarGamma*U))/sigma^(lvarGamma^7*t^U));
    Add(R4,Comm(v^lvarGamma,sigma));
  fi;
  Add(R4,Comm(v,sigma));
  if IsOddInt(q) then
    a:=(w^(QuoInt(-(q+1),2)))/2;
    r:=LogFFE(a,w);
    rhs:=sigma^(lvarGamma^r*varZ^U)*(v^-1)^U;
  else
    a:=w^q/(w+w^q);
    r:=LogFFE(a,w);
    rhs:=sigma^(lvarGamma^r*varZ^U)*(v^U);
  fi;
  Add(R4,Comm(v,sigma^U)/rhs);
  if q=2 then
    Add(R4,Comm(v,sigma^(lvarGamma*U))/(sigma^(lvarGamma*varZ^U)
     *v^(U^(lvarGamma^-1))));
  fi;
  if n > 2 then
    Add(R4,Comm(v,sigma^V));
  fi;
  Add(R4,Comm(v,tau^U));
  #   Steinberg relations for SU(2n, q)
  R3:=[];
  Add(R3,Comm(sigma,tau));
  if IsEvenInt(q) then
    Add(R3,Comm(sigma,sigma^varZ));
  else
    Add(R3,Comm(sigma,sigma^varZ)/(tau^2)^(varZ*U));
  fi;
  if (q<>3) then
    varE:=GF(q^2);
    # Implicit generator Assg from previous line.
    w:=PrimitiveElement(varE);
    w0:=w^(q+1);
    a:=w^(2*q)+w^2;
    # was "m:=Log(w0,a);"
    m:=LogFFE(a,w0);
    Add(R3,Comm(sigma^lvarDelta,sigma^varZ)/tau^(varZ*U*lvarDelta^m))
     ;
  else
    Add(R3,Comm(sigma^lvarDelta,sigma^varZ));
  fi;
  Add(R3,Comm(sigma,tau^varZ)/(sigma^varZ*(tau^-1)^(varZ*U)));
  #   additional relation needed for SU(6, 2) -- probably only #2 required
  if (n=3 and q=2) then
    Add(R3,Comm(sigma,sigma^(U^V*lvarDelta)));
    Add(R3,Comm(sigma,sigma^(V*lvarDelta))/sigma^(V*U*lvarDelta^-1));
  fi;
  if n > 2 then
    Add(R3,Comm(sigma,sigma^(U^V)));
    Add(R3,Comm(sigma,sigma^V)/sigma^(V*U));
  fi;
  if n < 4 then
    Add(R3,Comm(tau,tau^U));
  fi;
  if n=3 then
    Add(R3,Comm(tau,sigma^V));
  fi;
  if n > 3 then
    Add(R3,Comm(sigma,sigma^(V^2)));
  fi;
  Rels:=Concatenation(R,R3,R4,R_SU3,R_SL2,lvarR_N);
  return F/Rels;
end);
