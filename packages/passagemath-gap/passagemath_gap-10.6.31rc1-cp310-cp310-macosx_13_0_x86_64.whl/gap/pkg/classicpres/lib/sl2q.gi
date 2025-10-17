#   Campbell, Robertson, Williams J. Austral. Math. Soc. 1990
#   Campbell and Robertson, BLMS 1980
#   generators for SL(2, p^e) 

# Generators for SL_2(p^e)
BindGlobal("SL2Generators@",function(p,e)
local F,varZ,delta,tau,w;
  F:=GF(p^e);
  w:=PrimitiveElement(F);
  delta:=[[w^-1,0],[0,w^1]]*One(F);
  tau:=[[1,1],[0,1]]*One(F);
  varZ:=[[0,1],[-1,0]]*One(F);
  if e=1 then
    return [tau,varZ];
  else
    return [delta,tau,varZ];
  fi;
end);

#   presentation for SL(2, p^e); p odd
#   Projective = true: return presentation for PSL
BindGlobal("SL2_odd@",function(p,e)
local B,bas,I,K,Projective,Q,Rels,U,c,delta,f,i,m,q,tau,tau1,w,gens;
  Projective:=ValueOption("Projective");
  if Projective=fail then
    Projective:=false;
  fi;
  q:=p^e;
  K:=GF(q);
  w:=PrimitiveElement(K);

  Q:=FreeGroup("delta","tau","U");
  Q:=Group(StraightLineProgGens(GeneratorsOfGroup(Q)));
  gens:=GeneratorsOfGroup(Q);
  delta:=gens[1];
  tau:=gens[2];
  U:=gens[3];
  Rels:=[];

  # write w as linear combination of powers of w^2

  bas:=List([0..e-1],x->w^x);
  bas:=Basis(K,bas);
  c:=List([0..e-1],x->w^(2*x));
  c:=List(c,x->Coefficients(bas,x));

  bas:=ListWithIdenticalEntries(e,Zero(K));
  bas[2]:=One(K);
  c:=SolutionMat(c,bas);
  c:=List(c,Int);

  tau1:=Product(List([0..e-1],i->(tau^(delta^(i)))^c[i+1]));

  Rels:=Concatenation(Rels,[tau^p,Comm(tau,tau1),Comm(tau1,tau^delta),(tau1*U*delta)^3]);
  if Projective then
    Rels:=Concatenation(Rels,[(tau*U)^3,(U*delta)^2,U^2,delta^(QuoInt((q-1),2))]);
  else
    Rels:=Concatenation(Rels,[(tau*U^-1)^3/U^2,(U*delta)^2/U^2,U^4,delta^(QuoInt((q-1),2))/U^2]);
  fi;
  #if IsSquare(1+w^1) then
  m:=LogFFE(1+w,w);
  if IsEvenInt(m) then
    m:=m/2;
    Add(Rels,tau^(delta^m)/(tau*tau1));
    Add(Rels,tau1^(delta^m)/(tau1*tau^delta));
  else
    m:=LogFFE(1+w^-1,w);
    m:=m/2;
    Add(Rels,tau1^(delta^m)/(tau*tau1));
    Add(Rels,tau^(delta^(m+1))/(tau1*tau^delta));
  fi;
  f:=MinimalPolynomial(GF(p),w);
  c:=CoefficientsOfUnivariatePolynomial(f);
  c:=List(c,Int);
  B:=[tau,tau1];
  for i in [2..e] do
    B[i+1]:=B[i-1]^delta;
  od;
  Add(Rels,Product(List([0..e],i->B[i+1]^c[i+1])));
  return Q/Rels;
end);

#   special presentation for SL(2, p^e) when p^e mod 4 = 3
BindGlobal("SL2_special@",function(p,e)
local B,bas,I,K,Projective,Q,Rels,U,c,delta,f,i,m,q,r,tau,tau1,w,gens;
  Projective:=ValueOption("Projective");
  if Projective=fail then
    Projective:=false;
  fi;
  q:=p^e;
  K:=GF(q);
  w:=PrimitiveElement(K);

  #if IsSquare(1+w^1) then
  m:=LogFFE(1+w,w);
  if IsEvenInt(m) then
    m:=m/2;
    r:=QuoInt((q+1),4);
  else
    #m:=Log(w^2,(1+w^-1));
    m:=LogFFE(1+w^-1,w)/2;
    r:=QuoInt((q-3),4);
  fi;
  Q:=FreeGroup("delta","tau","U");
  Q:=Group(StraightLineProgGens(GeneratorsOfGroup(Q)));
  gens:=GeneratorsOfGroup(Q);
  delta:=gens[1];
  tau:=gens[2];
  U:=gens[3];

  Rels:=[Comm(tau,tau^(delta^(QuoInt((q+1),4)))),
    tau^(delta^m)/Comm(tau^-1,delta^r)];
  if Projective then
    Rels:=Concatenation(Rels,[(tau*U)^3,(U*delta)^2,U^2,delta^(QuoInt((q-1),2))/tau^p]);
  else
    Rels:=Concatenation(Rels,[(tau*U^-1)^3/U^2,(U*delta)^2/U^2,U^4,
            delta^(QuoInt((q-1),2))/(tau^p*U^2)]);
  fi;

  # write w as linear combination of powers of w^2

  bas:=List([0..e-1],x->w^x);
  bas:=Basis(K,bas);
  c:=List([0..e-1],x->w^(2*x));
  c:=List(c,x->Coefficients(bas,x));

  bas:=ListWithIdenticalEntries(e,Zero(K));
  bas[2]:=One(K);
  c:=SolutionMat(c,bas);
  c:=List(c,Int);

  tau1:=Product(List([0..e-1],i->(tau^(delta^(i)))^c[i+1]));

  f:=MinimalPolynomial(GF(p),w^1);
  c:=CoefficientsOfUnivariatePolynomial(f);
  c:=List(c,Int);
  B:=[tau,tau1];
  for i in [2..e] do
    B[i+1]:=B[i-1]^delta;
  od;
  Add(Rels,Product(List([0..e],i->B[i+1]^c[i+1])));
  return Q/Rels;
end);

#   presentation for SL(2, 2^e) where e > 1 
BindGlobal("SL2_even@",function(p,e)
local B,varE,F,I,Rels,U,c,delta,f,i,m,q,tau,u,w,gens;
  Assert(1,p=2);
  q:=2^e;
  varE:=GF(2,e);
  w:=PrimitiveElement(varE);
  F:=FreeGroup("delta","tau","U");
  F:=Group(StraightLineProgGens(GeneratorsOfGroup(F)));
  gens:=GeneratorsOfGroup(F);
  delta:=gens[1];
  tau:=gens[2];
  U:=gens[3];
  B:=[tau];
  for i in [1..e] do
    B[i+1]:=B[i]^delta;
  od;
  f:=MinimalPolynomial(GF(2),w^2);
  c:=CoefficientsOfUnivariatePolynomial(f);
  u:=List(c,Int);
  m:=LogFFE(1+w^2,w^2);
  Rels:=[Product(List([0..e],i->B[i+1]^u[i+1])),(U*tau)^3,U^2,(U*delta)^2,
    tau^2,(tau*delta)^(q-1),tau^(delta^m)*Comm(tau,delta)^-1];
  return F/Rels;
end);

# #   Zassenhaus presentation for SL (2, p) where p is not 17 
# Zassenhaus:=function(p)
# if p=2 then
#     return SubGroup(s,t,[s^p=1,t^2,(s*t)^3]);
#   elif p=3 then
#     return SubGroup(s,t,[s^p=1,t^4,(t*s^-1*t^-1*s^-1*t*s^-1)]);
#   elif p<>17 then
#     return SubGroup(s,t,[s^p=(s*t)^3,Tuple([t^2,s]),t^4,(s^2*t*s^(QuoInt((p^2+1)
#      ,2))*t)^3]);
#   fi;
# end;

#   Campbell Robertson presentation for SL(2, p)
# CR:=function(p)
# local F,G,k,x,y;
#   if p=2 then
#     return SubGroup(s,t,[s^2=1,t^2,(s*t)^3]);
#   fi;
#   k:=QuoInt(p,3);
#   F:=FreeGroup(2);
#   # Implicit generator Assg from previous line.
#   y:=F.1;
#   x:=F.2;
#   G:=F/[x^2/((x*y)^3),
#     (x*y^4*x*y^(QuoInt((p+1),2)))^2*y^p*x^(2*k)];
#   return G;
# end;

#   Campbell Robertson presentation for SL(2, p) modified for our generators 
BindGlobal("Modified_CR@",function(p)
local F,Projective,Rels,a,b,k,r;
  Projective:=ValueOption("Projective");
  if Projective=fail then
    Projective:=false;
  fi;
  F:=FreeGroup("a","b");
  F:=Group(StraightLineProgGens(GeneratorsOfGroup(F)));
  # Implicit generator Assg from previous line.
  a:=F.1;
  b:=F.2;
  if p=2 then
    return F/[a^2,b^2,(a*b)^3];
  fi;
  r:=p mod 3;
  k:=QuoInt(p,3);
  if r=1 then
    Rels:=[b^-2*(b*(a*b^2))^3,(b*(a*b^2)^4*b*(a*b^2)^(QuoInt((p+1),2)))
     ^2*(a*b^2)^p*b^(2*k)];
  else
    Rels:=[b^2*(b^-1*a)^3,(b^-1*a^4*b^-1*a^(QuoInt((p+1),2)))^2*a^p*(b^-1)^(2*k)
     ];
  fi;
  if Projective then
    Rels:=Concatenation(Rels,[b^2]);
  fi;
  return F/Rels;
end);

#   presentation for SL(2, p^e) 
InstallGlobalFunction(PresentationForSL2@,function(p,e)
local Projective,Q,R;
  Projective:=ValueOption("Projective");
  if Projective=fail then
    Projective:=false;
  fi;
  if e=1 then
    R:=Modified_CR@(p:Projective:=Projective);
  elif IsEvenInt(p) then
    R:=SL2_even@(p,e);
  elif p^e mod 4=3 then
    R:=SL2_special@(p,e:Projective:=Projective);
  else
    R:=SL2_odd@(p,e:Projective:=Projective);
  fi;
  return R;
end);

#  
BindGlobal("TestPresSL2@",function()
local p,e,R,X,Y,G;
  for p in [2,3,5,7,11,13,17,19,23,29,31] do
    for e in [1..Maximum(2,LogInt(100,p))] do
      Print("p,e=",p,",",e,"\n");
      R := PresentationForSL2@(p, e);
      X := SL2Generators@(p, e);
      Y := List(RelatorsOfFpGroup(R),x->MappedWord(x,FreeGeneratorsOfFpGroup(R),X));
      if not ForAll(Y,IsOne) then Error("rels");fi;
      G:=Group(X);
      if Size(G)<>Size(SL(2,p^e)) then Error("matgrpsize");fi;
      if Size(G)<>Size(R) then Error("pressize");fi;
    od;
  od;
end);

