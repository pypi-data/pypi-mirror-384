#  File converted from Magma code -- requires editing and checking
#  Magma -> GAP converter, version 0.5, 11/5/18 by AH


InstallGlobalFunction(OmegaGenerators@,function(d,q)
local lvarDelta,varE,F,MA,U,V,varZ,gens,n,sigma,tau,w,one;
  Assert(1,IsOddInt(d));
  Assert(1,IsOddInt(q));
  if d=3 then
    return ClassicalStandardGenerators("Omega",3,q:
      PresentationGenerators:=false);
  fi;
  n:=QuoInt(d,2);
  Assert(1,n > 1);
  F:=GF(q);
  one:=One(F);
  varZ:=IdentityMat(d,F);
  varZ[1][1]:=0*one;
  varZ[1][2]:=1*one;
  varZ[2][1]:=1*one;
  varZ[2][2]:=0*one;
  varZ[d][d]:=-1*one;
  w:=PrimitiveElement(F);
  lvarDelta:=IdentityMat(d,F);
  lvarDelta[1][1]:=w^-1;
  lvarDelta[2][2]:=w;
  lvarDelta[3][3]:=w^1;
  lvarDelta[4][4]:=w^-1;
  #lvarDelta:=lvarDelta*FORCEOne(GL(d,F)); ## Not needed FORCE
  tau:=IdentityMat(d,F);
  tau[1][1]:=1*one;
  tau[1][2]:=1*one;
  tau[1][d]:=1*one;
  tau[d][2]:=2*one;
  tau[d][d]:=1*one;
  sigma:=IdentityMat(d,F);
  sigma[1][1]:=1*one;
  sigma[1][3]:=1*one;
  sigma[4][2]:=-1*one;
  sigma[4][4]:=1*one;
  varE:=ClassicalStandardGenerators("Omega",d,q:
    PresentationGenerators:=false);
  U:=varE[5];
  V:=varE[4];
  gens:=[lvarDelta,varZ,tau,sigma,U,V];
  return gens;
end);

BindGlobal("Omega_PresentationForN1@",function(n)
local F,R,R1,Rels,S,U,V,varZ,phi;
  Assert(1,n > 1);
  F:=FreeGroup("Z","U","V");
  F:=Group(StraightLineProgGens(GeneratorsOfGroup(F)));
  varZ:=F.1;
  U:=F.2;
  V:=F.3;
  R:=SignedPermutations@(n);
  S:=FreeGroupOfFpGroup(R);
  R:=RelatorsOfFpGroup(R);
  phi:=GroupHomomorphismByImages(S,F, GeneratorsOfGroup(S), [U,V]);
  R:=List(R,r->ImagesRepresentative(phi,r));
  R1:=[];
  if n > 2 then
    Add(R1,Comm(varZ,U^V));
  fi;
  if n > 3 then
    Add(R1,Comm(varZ,V*U^-1));
  fi;
  Add(R1,varZ^2);
  Add(R1,Comm(varZ,U^2));
  Add(R1,Comm(varZ,varZ^U));
  R1 := Concatenation(R1, R);
  return F/R1;
end);

#Omega_OrderN1:=function(n)
#return 2^(2*n-1)*Factorial(n);
#end;

BindGlobal("Omega_PresentationForN@",function(n,q)
local lvarDelta,F,OMIT,R,R1,Rels,S,U,V,varZ,phi;
  F:=FreeGroup("Delta","Z","U","V");
  F:=Group(StraightLineProgGens(GeneratorsOfGroup(F)));
  lvarDelta:=F.1;
  varZ:=F.2;
  U:=F.3;
  V:=F.4;
  R:=Omega_PresentationForN1@(n);
  S:=FreeGroupOfFpGroup(R);
  R:=RelatorsOfFpGroup(R);
  phi:=GroupHomomorphismByImages(S,F, GeneratorsOfGroup(S), [varZ,U,V]);
  R:=List(R,r->ImagesRepresentative(phi, r));
  R1:=[];
  if n > 3 then
    Add(R1,Comm(lvarDelta,U^(V^2)));
    Add(R1,Comm(lvarDelta,lvarDelta^(V^2)));
  fi;
  if n > 4 then
    Add(R1,Comm(lvarDelta,V*U*U^V));
  fi;
  if n > 2 then
    Add(R1,Comm(lvarDelta,varZ^(V^2)));
    Add(R1,lvarDelta*lvarDelta^V/lvarDelta^(V*U));
    Add(R1,Comm(lvarDelta,lvarDelta^V));
    Add(R1,Comm(lvarDelta,(U^2)^V));
  fi;
  Add(R1,lvarDelta^U*lvarDelta);
  OMIT:=true;
  if not OMIT then
    Add(R1,lvarDelta^(QuoInt((q-1),2))/U^2);
  fi;
  Add(R1,lvarDelta^(varZ*varZ^U)*lvarDelta);
  if n=2 then
    Add(R1,Comm(lvarDelta,lvarDelta^varZ));
  fi;
  Rels:=Concatenation(R1,R);
  return F/Rels;
end);

#Omega_OrderN:=function(n,q)
#return (q-1)^n*2^(n-1)*Factorial(n);
#end;

BindGlobal("Setup_OmegaPresentation@",function(d,q)
local lvarDelta,F,I,R1,R2,R3,R4,R5,R6,Rels,S,U,V,W,varZ,b,e,f,n,p,phi,
  sigma,tau,w,x;

  Assert(1,IsOddInt(d));
  Assert(1,IsOddInt(q));
  n:=QuoInt(d,2);
  Assert(1,n > 1);
  F:=GF(q);
  w:=PrimitiveElement(F);
  e := Factors(q);
  if Size(DuplicateFreeList(e)) > 1 then
    f := false;
  else
    f := true;
    p := e[1];
    e := Size(e);
  fi;
  F:=FreeGroup("Delta","Z","tau","sigma","U","V");
  F:=Group(StraightLineProgGens(GeneratorsOfGroup(F)));
  lvarDelta:=F.1;
  varZ:=F.2;
  tau:=F.3;
  sigma:=F.4;
  U:=F.5;
  V:=F.6;
  R3:=[];
  #   additional relation needed for q = p to express Delta as word in sigma
  #  and U
  if IsPrimeInt(q) then
    b:=Int(1/w); 
    w:=Int(w);
    Add(R3,lvarDelta/((sigma^U)^(w-w^2)*sigma^(b)*(sigma^U)^((w-1))
     *sigma^-1));
  fi;
  if e=1 then
    R1:=Omega_PresentationForN1@(n);
    S:=FreeGroupOfFpGroup(R1);
    R1:=RelatorsOfFpGroup(R1);
    phi:=GroupHomomorphismByImages(S,F, GeneratorsOfGroup(S), [varZ,U,V]);
  else
    R1:=Omega_PresentationForN@(n,q);
    S:=FreeGroupOfFpGroup(R1);
    R1:=RelatorsOfFpGroup(R1);
    phi:=GroupHomomorphismByImages(S,F,GeneratorsOfGroup(S),
      [lvarDelta,varZ,U,V]);
  fi;
  R1:=List(R1,r->ImagesRepresentative(phi, r));
  R2:=PresentationForSL2@(p,e:Projective:=false);
  S:=FreeGroupOfFpGroup(R2);
  R2:=RelatorsOfFpGroup(R2);
  if e=1 then
    phi:=GroupHomomorphismByImages(S,F, GeneratorsOfGroup(S), [sigma,U]);
  else
    phi:=GroupHomomorphismByImages(S,F, GeneratorsOfGroup(S),
      [lvarDelta,sigma,U]);
  fi;
  R2:=List(R2,r->ImagesRepresentative(phi, r));
  if e > 1 then
    Add(R3,Comm(sigma,lvarDelta^(varZ^U)));
  fi;
  #   centraliser of tau
  R5:=[];
  if n > 2 then
    Add(R5,Comm(tau,U^V));
    if e > 1 then
      Add(R5,Comm(tau,lvarDelta^V));
    fi;
  fi;
  if n > 3 then
    Add(R5,Comm(tau,V*U^-1));
  fi;
  Add(R5,Comm(tau,U^2*varZ^U));
  if e > 1 and n=2 then
    Add(R5,Comm(tau,lvarDelta*lvarDelta^varZ));
  fi;
  R6:=[];
  R6:=PresentationForSL2@(p,e:Projective:=true);
  S:=FreeGroupOfFpGroup(R6);
  R6:=RelatorsOfFpGroup(R6);
  if e=1 then
    phi:=GroupHomomorphismByImages(S,F,
      GeneratorsOfGroup(S),
      [tau,varZ]);
  else
    x:=lvarDelta*lvarDelta^(varZ^U);
    phi:=GroupHomomorphismByImages(S,F,
      GeneratorsOfGroup(S),
      [x,tau,varZ]);
  fi;
  R6:=List(R6,r->ImagesRepresentative(phi, r));
  #   Steinberg relations
  R4:=[];
  if n > 2 then
    Add(R4,Comm(sigma,sigma^V)/(sigma^(V*U^-1)));
    Add(R4,Comm(sigma,sigma^(V*U^-1)));
    W:=U^(V*U^-1);
    Add(R4,Comm(sigma,sigma^W));
    #   new relation June 2018
    Add(R4,Comm(sigma,tau^(V^2)));
  fi;
  if n > 3 then
    Add(R4,Comm(sigma,sigma^(V^2)));
  fi;
  Add(R4,Comm(sigma,sigma^(varZ^U)));
  Add(R4,Comm(tau,tau^U)/(sigma^(varZ^U))^2);
  Add(R4,Comm(sigma,tau));
  Add(R4,Comm(sigma^varZ,tau)/(sigma*tau^(varZ*U)));
  #   Omega(7, 3) has multiplicator of order 6
  if d=7 and q=3 then
    Add(R3,Comm(tau,sigma^V));
  fi;
  Rels:=Concatenation(R1,R2,R3,R4,R5,R6);
  return F/Rels;
end);

#   word for Delta in Sp(4, 9) generated by 5 specific elements
BindGlobal("SpecialWordForDelta@",function()
local G,w1,w10,w103,w104,w105,w106,w107,w108,w109,w11,w12,w13,w14,w15,w16,
   w17,w18,w19,w2,w20,w21,w22,w23,w24,w25,w26,w27,w28,w29,w3,w30,w31,w32,
   w33,w34,w35, w36,w37,w38,w39,w4,w45,w5,w52,w57,w58,w59,w6,w60,w61,w7,
   w8,w9;

  G:=FreeGroup(5);
  G:=Group(StraightLineProgGens(GeneratorsOfGroup(G)));
  w10:=G.4*G.5;
  w103:=w10*G.5;
  w7:=G.3*G.1;
  w52:=G.4*w7;
  w6:=G.2*G.4;
  w57:=G.1*w6;
  w4:=G.2^2;
  w58:=w57*w4;
  w59:=w52*w58;
  w26:=G.3^-1;
  w45:=G.2*w26;
  w32:=G.1^-2;
  w60:=w45*w32;
  w61:=w59*w60;
  w104:=w103*w61;
  w105:=w104*w61;
  w106:=w105*G.1;
  w107:=w106*G.1;
  w108:=w107*G.1;
  w1:=G.4*G.3;
  w2:=G.5*w1;
  w3:=w2*w1;
  w5:=G.3*w4;
  w8:=w6*w7;
  w9:=w8*G.4;
  w11:=w9*w10;
  w12:=w5*w11;
  w13:=w3*w12;
  w14:=G.2*G.1;
  w15:=w14*w2;
  w16:=w15*w9;
  w17:=w9*w16;
  w18:=w13*w17;
  w19:=w18*w5;
  w20:=G.5^-1;
  w21:=G.1^-1;
  w22:=w20*w21;
  w23:=G.4^-1;
  w24:=G.2*w23;
  w25:=w22*w24;
  w27:=w26*w21;
  w28:=w20*w23;
  w29:=w27*w28;
  w30:=w25*w29;
  w31:=G.2*w20;
  w33:=w31*w32;
  w34:=w23*w21;
  w35:=w23*G.2;
  w36:=w34*w35;
  w37:=w33*w36;
  w38:=w30*w37;
  w39:=w19*w38;
  w109:=w108*w39;
  return w109;
end);

#   word for Delta for q = 1 mod 4 and q not equal to 9
BindGlobal("WordForDelta@",function(d,q)
local A,B,C,Delta2,varE,F,I,Special_OmegaStandardToPresentation,
   U,V,W,varZ,a,b,c,e,sigma,tau,w,w_Delta,words;

  Special_OmegaStandardToPresentation:=function(d,q)
  local U,V,W,varZ,delta,p,s,sigma,t,tau;
    W:=FreeGroup("s","t","delta","U","V");
    W:=Group(StraightLineProgGens(GeneratorsOfGroup(W)));
    s:=W.1;
    t:=W.2;
    delta:=W.3;
    U:=W.5;
    V:=W.4;
    # rewritten select statement
    if d mod 4=3 then
      tau:=t^V;
    else
      tau:=(t^-1)^V;
    fi;
    varZ:=s^V;
    p:=Characteristic(GF(q));
    sigma:=Comm(tau^(varZ*U),tau^(QuoInt((p+1),2)));
    return [Comm(delta^V,U),varZ,tau,sigma,U,V];
  end;

  W:=FreeGroup("Delta2","Z","tau","sigma","U","V");
  W:=Group(StraightLineProgGens(GeneratorsOfGroup(W)));
  #   Delta2 = Delta^2
  Delta2:=W.1;
  varZ:=W.2;
  tau:=W.3;
  sigma:=W.4;
  U:=W.5;
  V:=W.6;
  F:=GF(q);
  e:=Size(F);
  w:=PrimitiveElement(F);
  varE:=Basis(Field(w^4));
  # was "c:=Eltseq((-w^3)*FORCEOne(varE));"
  c:=Coefficients(varE, (-w^3));
  c:=List(c,Int);
  b:=Coefficients(varE, (1-w));
  b:=List(b,Int);
  a:=Coefficients(varE, (-w^-1+1));
  a:=List(a,Int);

  C:=Product(List([0..e-1],i->(sigma^(Delta2^i*U))^c[i+1]));
  B:=Product(List([0..e-1],i->(sigma^(Delta2^i*sigma^U))^b[i+1]));
  A:=Product(List([0..e-1],i->(sigma^(Delta2^i))^a[i+1]));
  w_Delta:=C*Delta2*sigma^U*B*A;
  words:=Special_OmegaStandardToPresentation(d,q);
  # was "w_Delta:=Evaluate(w_Delta,words);"
  w_Delta:=List(w_Delta, w-> MappedWord(w, GeneratorsOfGroup(W), words));
  return w_Delta;
end);

#   express presentation generators as words in standard generators
InstallGlobalFunction(OmegaStandardToPresentation@,
function(d,q)
local lvarDelta,U,V,W,varZ,delta,gens,p,s,sigma,t,tau,fgens;
  W:=FreeGroup("s","t","delta","U","V");
  W:=Group(StraightLineProgGens(GeneratorsOfGroup(W)));
  s:=W.1;
  t:=W.2;
  delta:=W.3;
  U:=W.5;
  V:=W.4;
  if d mod 4=3 then
    tau:=t^V;
  else
    tau:=(t^-1)^V;
  fi;
  varZ:=s^V;
  p:=Characteristic(GF(q));
  sigma:=Comm(tau^(varZ*U),tau^(QuoInt((p+1),2)));
  #   need to sort out Delta
  if q mod 4=3 then
    lvarDelta:=U^2*Comm(delta^V,U)^(QuoInt((q+1),4));
  elif q=9 then
    gens:=[Comm(delta^V,U),s^V,U,tau,sigma];
    lvarDelta:=SpecialWordForDelta@();
    fgens:=GeneratorsOfGroup(FamilyObj(lvarDelta)!.wholeGroup);
    # was "lvarDelta:=Evaluate(lvarDelta,gens);"
    lvarDelta:=List(lvarDelta, w-> MappedWord(w, fgens, gens));
  else
    lvarDelta:=WordForDelta@(d,q);
    #   ensure Delta is in the correct FreeGroup
    fgens:=GeneratorsOfGroup(FamilyObj(lvarDelta)!.wholeGroup);
    # was "lvarDelta:=Evaluate(lvarDelta,List([1..5],i->W.i));"
    lvarDelta:=List(lvarDelta,w->MappedWord(w,fgens,
       GeneratorsOfGroup(W){[1..5]}));
  fi;
  return [lvarDelta,varZ,tau,sigma,U,V];
end);

#   express standard generators as words in presentation generators
BindGlobal("OmegaPresentationToStandard@",
function(d,q)
local lvarDelta,U,V,W,varZ,sigma,t,tau;
  W:=FreeGroup("Delta","Z","tau","sigma","U","V");
  W:=Group(StraightLineProgGens(GeneratorsOfGroup(W)));
  lvarDelta:=W.1;
  varZ:=W.2;
  tau:=W.3;
  sigma:=W.4;
  U:=W.5;
  V:=W.6;
  # rewritten select statement
  if d mod 4=3 then
    t:=tau^(V^-1);
  else
    t:=(tau^-1)^(V^-1);
  fi;
  #   return [s, t, delta, V, U]
  return [varZ^(V^-1),t,Comm(varZ,lvarDelta^-1)^(V^-1),V,U];
end);

#   relations are on presentation generators;
#  convert to relations on standard generators
BindGlobal("OmegaConvertToStandard@",
function(d,q,Rels)
local A,B,C,T,U,W,tau,gens;
  A:=OmegaStandardToPresentation@(d,q);
  # was "Rels:=Evaluate(Rels,A);"
  gens:=GeneratorsOfGroup(FamilyObj(Rels)!.wholeGroup);
  Rels:=List(Rels, w-> MappedWord(w, gens, A));
  B:=OmegaPresentationToStandard@(d,q);
  # was "C:=Evaluate(B,A);"
  gens:=GeneratorsOfGroup(FamilyObj(B)!.wholeGroup);
  C:=List(B, w-> MappedWord(w, gens, A));
  #U:=Universe(C);
  #W:=Universe(Rels);
  U:=FamilyObj(C)!.wholeGroup;
  W:=FamilyObj(Rels)!.wholeGroup;
  tau:=GroupHomomorphismByImages(U,W,
    GeneratorsOfGroup(U),GeneratorsOfGroup(W));
  T:=List([1..Size(GeneratorsOfGroup(W))],i->W.i^-1*tau(C[i]));
  Rels:=Concatenation(Rels,T);
  return W/Rels;
end);

InstallGlobalFunction(OmegaPresentation@,function(d,q)
local gens,P,Presentation,Q,R,Rels,S;
  Presentation:=ValueOption("Presentation");
  if Presentation=fail then
    Presentation:=false;
  fi;
  Assert(1,IsOddInt(d) and d > 1);
  Assert(1,IsOddInt(q));
  if d=3 then
    R:=ClassicalStandardPresentation("SL",2,q:Projective:=true,
      PresentationGenerators:=false);
    gens:=FreeGeneratorsOfFpGroup(R);
    R:=RelatorsOfFpGroup(R);
    Q:=FreeGroup(5);
    Q:=Group(StraightLineProgGens(GeneratorsOfGroup(Q)));
    # was "R:=Evaluate(R,List([1,1,2,3],i->Q.i));" . This required the new variable "gens"
    R:=List(R, w -> MappedWord(w, gens, GeneratorsOfGroup(Q){[1,1,2,3]}));
    Add(R,Q.4);
    Add(R,Q.5);
    return Q/R;
  fi;
  R:=Setup_OmegaPresentation@(d,q);
  P:=FreeGroupOfFpGroup(R);
  R:=RelatorsOfFpGroup(R);
  if Presentation then
    return P/R;
  fi;
  Rels:=OmegaConvertToStandard@(d,q,R);
  S:=FreeGroupOfFpGroup(Rels);
  Rels:=RelatorsOfFpGroup(Rels);
  Rels:=Filtered(Rels,w->w<>w^0);
  return S/Rels;
end);
