#  File converted from Magma code -- requires editing and checking
#  Magma -> GAP converter, version 0.5, 11/5/18 by AH

InstallGlobalFunction(SLGenerators@,function(d,q)
local MA,S,V,e,f,i,p;
  if d=2 then
    #p:=PrimeBase(q);
    p:=Factors(q)[1];
    e:=LogInt(q,p);
    if q<>p^e then Error("<q> is not a prime power");fi;
    return SL2Generators@(p,e);
  fi;
  S:=ShallowCopy(ClassicalStandardGenerators("SL",d,q:
    PresentationGenerators:=false));
  f:=GF(q);
  V:=NullMat(d,d,f);
  for i in [1..d-1] do
    V[i][i+1]:=One(f);
  od;
  V[d][1]:=(-One(f))^(d-1);
  V:=ImmutableMatrix(f,V);
  S[2]:=V;
  S[4]:=S[4]^-1;
  return S;
end);

#   presentation for extension of direct product of
#   d - 1 copies of Z_{q - 1} by a copy of Sym (d)
BindGlobal("PresentationForN@",function(d,q)
local F,OMIT,R,Rels,S,U,V,delta,tau;
  F:=FreeGroup("U","V","delta");
  F:=Group(StraightLineProgGens(GeneratorsOfGroup(F)));
  U:=F.1;
  V:=F.2;
  delta:=F.3;
  if IsEvenInt(q) then
    R:=PresentationForSn@(d);
    S:=FreeGroupOfFpGroup(R);
    R:=RelatorsOfFpGroup(R);
  else
    R:=SignedPermutations@(d);
    S:=FreeGroupOfFpGroup(R);
    R:=RelatorsOfFpGroup(R);
  fi;
  tau:=GroupHomomorphismByImages(S,F,GeneratorsOfGroup(S),[U,V]);
  R:=List(R,r->ImagesRepresentative(tau,r));
  Rels:=[];
  if d > 3 then
    Add(Rels,Comm(delta,U^(V^2)));
  fi;
  if d > 4 then
    Add(Rels,Comm(delta,V*U*U^V));
  fi;
  Add(Rels,delta*delta^V/delta^(V*U));
  Add(Rels,Comm(delta,delta^V));
  if d > 3 then
    Add(Rels,Comm(delta,delta^(V^2)));
  fi;
  OMIT:=true;
  if not OMIT then
    Add(Rels,delta^U/delta^-1);
    if IsEvenInt(q) then
      Add(Rels,delta^(q-1));
    else
      Add(Rels,delta^(QuoInt((q-1),2))/U^2);
    fi;
  fi;
  Rels:=Concatenation(Rels,R);
  return F/Rels;
end);

#SL_Order_NSubgroup:=function(d,q)
#  return (q-1)^(d-1)*Factorial(d);
#end;

#   return presentation for SL(d, q)
BindGlobal("SLPresentation@",function(d,q)
local F,I,R1,R2,Rels,S,U,V,a,b,delta,e,f,p,phi,tau,w,wm1;
  Assert(1,d > 2);
  #p:=PrimeBase(q);
  p:=Factors(q)[1];
  e:=LogInt(q,p);
  if q<>p^e then Error("<q> is not a prime power");fi;
  F:=FreeGroup("U","V","tau","delta");
  F:=Group(StraightLineProgGens(GeneratorsOfGroup(F)));
  U:=F.1;
  V:=F.2;
  tau:=F.3;
  delta:=F.4;
  Rels:=[];
  #   we don't need delta if e = 1 but it makes presentation consistent for all
  #  q
  if e=1 then
    w:=PrimitiveElement(GF(p));
    a:=Int(w-w^2);
    b:=Int(w-1);
    wm1:=Int(w^-1);
    Add(Rels,delta^-1*(tau^a)^U*tau^(wm1)*(tau^b)^U*tau^-1);
  fi;
  if IsPrimeInt(q) then
    if q=2 then
      R1:=PresentationForSn@(d);
      S:=FreeGroupOfFpGroup(R1);
      R1:=RelatorsOfFpGroup(R1);
    else
      R1:=SignedPermutations@(d);
      S:=FreeGroupOfFpGroup(R1);
      R1:=RelatorsOfFpGroup(R1);
    fi;
    phi:=GroupHomomorphismByImages(S,F,GeneratorsOfGroup(S),[U,V]);
  else
    R1:=PresentationForN@(d,q);
    S:=FreeGroupOfFpGroup(R1);
    R1:=RelatorsOfFpGroup(R1);
    phi:=GroupHomomorphismByImages(S,F,GeneratorsOfGroup(S),[U,V,delta]);
  fi;
  R1:=List(R1,r->ImagesRepresentative(phi,r));
  R2:=PresentationForSL2@(p,e:Projective:=false);
  S:=FreeGroupOfFpGroup(R2);
  R2:=RelatorsOfFpGroup(R2);
  if e=1 then
    phi:=GroupHomomorphismByImages(S,F,GeneratorsOfGroup(S),[tau,U]);
  else
    phi:=GroupHomomorphismByImages(S,F,GeneratorsOfGroup(S),[delta,tau,U]);
  fi;
  R2:=List(R2,r->ImagesRepresentative(phi,r));
  #   centraliser of tau
  if d > 3 then
    Add(Rels,Comm(tau,U^(V^2)));
  fi;
  if d > 4 then
    if e > 1 then
      Add(Rels,Comm(tau,V*U*U^V));
    else
      Add(Rels,Comm(tau,V*U^-1*(U^-1)^V));
    fi;
  fi;
  if e > 1 then
    Add(Rels,Comm(tau,delta*(delta^2)^V));
    if d > 3 then
      Add(Rels,Comm(tau,delta^(V^2)));
    fi;
  fi;
  #   Steinberg relations
  Add(Rels,Comm(tau,tau^V)/tau^(U^V));
  Add(Rels,Comm(tau,tau^(U^V)));
  Add(Rels,Comm(tau,tau^(U*V)));
  if d > 3 then
    Add(Rels,Comm(tau,tau^(V^2)));
  fi;
  #   one additional relation needed for this special case
  if d=3 and q=4 then
    Add(Rels,Comm(tau,tau^(delta*V))/tau^(delta*U^V));
    #   Append (~Rels, (tau, tau^(delta * U^V)) = 1);
    #   Append (~Rels, (tau, tau^(delta * U * V)) = 1);
  fi;
  Rels:=Concatenation(Rels,R1,R2);
  return F/Rels;
end);

#  ///////////////////////////////////////////////////////////////////////
#     Short presentation for SL(d, q)                                   //
#                                                                       //
#     Input two parameters to compute this presentation of SL(d, q)     //
#       d = dimension                                                   //
#       q = field order                                                 //

#     November 2017
#  ///////////////////////////////////////////////////////////////////////

#   construct generator of centre as SLP in presentation generators
BindGlobal("SLGeneratorOfCentre@",
function(d,q,W)
local U,V,delta,m,z;
  Assert(1,d > 2);
  m:=QuoInt((d-1)*(q-1),Gcd(d,q-1));
  U:=W.1;
  V:=W.2;
  delta:=W.4;
  z:=(delta*U*V^-1)^m;
  return z;
end);

#   express presentation generators as words in standard generators 
BindGlobal("SLStandardToPresentation@",
function(d,q)
local P,S,U,V,V_p,delta,tau;
  S:=FreeGroup("U","V","tau","delta");
  S:=Group(StraightLineProgGens(GeneratorsOfGroup(S)));
  if d=2 then
    if IsPrimeInt(q) then
      P:=[S.3,S.2,One(S),One(S)];
    else
      P:=[S.4^-1,S.3,S.2,One(S)];
    fi;
    return P;
  fi;
  U:=S.1;
  V:=S.2;
  tau:=S.3;
  delta:=S.4;
  if IsOddInt(d) and IsOddInt(q) then
    V_p:=V^-1*(U^-1*V)^(d-1);
  else
    V_p:=V^(d-1);
  fi;
  return [U,V_p,tau,delta^-1];
end);

#   express standard generators as words in presentation generators 
BindGlobal("SLPresentationToStandard@",
function(d,q)
local I,P,S,U,V,V_s,delta,tau,w,x,y;
  if d=2 then
    if IsPrimeInt(q) then
      P:=FreeGroup(2);
      P:=Group(StraightLineProgGens(GeneratorsOfGroup(P)));
      w:=PrimitiveElement(GF(q));
      x:=Int(w^-1)-1;
      y:=Int(w^-2-w^-1);
      U:=P.2;
      tau:=P.1;
      delta:=(tau^-1*(tau^x)^U*tau^(Int(w))*(tau^-y)^U)^-1;
      S:=[P.2,P.2,P.1,delta];
    else
      P:=FreeGroup(3);
      P:=Group(StraightLineProgGens(GeneratorsOfGroup(P)));
      S:=[P.3,P.3,P.2,P.1^-1];
    fi;
    return S;
  fi;
  P:=FreeGroup(4);
  P:=Group(StraightLineProgGens(GeneratorsOfGroup(P)));
  U:=P.1;
  V:=P.2;
  tau:=P.3;
  delta:=P.4;
  if IsOddInt(d) and IsOddInt(q) then
    V_s:=(V*U^-1)^(d-1)*V^-1;
  else
    V_s:=V^(d-1);
  fi;
  return [U,V_s,tau,delta^-1];
end);

#   relations are on presentation generators;
#  convert to relations on 4 standard generators 
BindGlobal("SLConvertToStandard@",
function(d,q,Rels)
local A,B,C,T,U,W,tau,gens;
  A:=SLStandardToPresentation@(d,q);
  # was "Rels:=Evaluate(Rels,A);"
  gens:=GeneratorsOfGroup(FamilyObj(Rels)!.wholeGroup);
  Rels:=List(Rels, w -> MappedWord(w, gens, A));
  B:=SLPresentationToStandard@(d,q);
  # was "C:=Evaluate(B,A);"
  gens:=GeneratorsOfGroup(FamilyObj(B)!.wholeGroup);
  C:=List(B, w -> MappedWord(w, gens, A));
  U:=FamilyObj(C)!.wholeGroup;
  W:=FamilyObj(Rels)!.wholeGroup;
  tau:=GroupHomomorphismByImages(U,W,
    GeneratorsOfGroup(U),GeneratorsOfGroup(W));
  T:=List([1..Length(GeneratorsOfGroup(W))],
    i->W.(i)^-1*ImagesRepresentative(tau,C[i]));
  Rels:=Concatenation(Rels,T);
  return W/Rels;
end);

InstallGlobalFunction(Internal_StandardPresentationForSL@,function(d,K)
#  -> ,GrpSLP ,[ ,]  return standard presentation for SL ( d , K ) ; if
#  projective , then return standard presentation for PSL ( d , K )
local P,Presentation,Projective,R,Rels,S,e,p,q,z;
  Presentation:=ValueOption("Presentation");
  if Presentation=fail then
    Presentation:=false;
  fi;
  Projective:=ValueOption("Projective");
  if Projective=fail then
    Projective:=false;
  fi;
  if not d > 1 then
    Error("Degree must be at least 2");
  fi;

  if IsInt(K) then
    if not IsPrimePowerInt(K) then
      Error("<q> must be a prime power");
    fi;
    q:=K;
    K:=GF(q);
  else
    if not IsField(K) and IsFinite(K) then 
      Error("<K> must be a finite field");
    fi;
    q:=Size(K);
  fi;

  p:=Characteristic(K);
  e:=LogInt(Size(K),p);
  if d=2 then
    R:=PresentationForSL2@(p,e:Projective:=Projective);
    P:=FreeGroupOfFpGroup(R);
    R:=RelatorsOfFpGroup(R);
  else
    R:=SLPresentation@(d,q);
    P:=FreeGroupOfFpGroup(R);
    R:=RelatorsOfFpGroup(R);
    if Projective and Gcd(d,q-1) > 1 then
      z:=SLGeneratorOfCentre@(d,q,P);
      R:=Concatenation(R,[z]);
    fi;
  fi;
  if Presentation then
    return P/R;
  fi;
  Rels:=SLConvertToStandard@(d,q,R);
  P:=FreeGroupOfFpGroup(Rels);
  Rels:=RelatorsOfFpGroup(Rels);
  Rels:=Filtered(Rels,w->w<>w^0);
  return P/Rels;
end);

