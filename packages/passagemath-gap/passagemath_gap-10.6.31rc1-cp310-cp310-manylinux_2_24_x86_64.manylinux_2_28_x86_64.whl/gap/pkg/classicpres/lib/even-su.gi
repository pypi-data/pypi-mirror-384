#  File converted from Magma code -- requires editing and checking
#  Magma -> GAP converter, version 0.5, 11/5/18 by AH

#   this agrees with paper definition of psi
BindGlobal("EvenSUGenerators@",function(d,q)
local lvarDelta,S,T,U,V,varZ,delta,sigma,tau;
  Assert(1,IsEvenInt(d));
  S:=ClassicalStandardGenerators("SU",d,q:
    PresentationGenerators:=false);
  varZ:=S[1];
  varZ:=varZ^-1;
  V:=S[2];
  tau:=S[3];
  tau:=tau^-1;
  delta:=S[4];
  delta:=delta^-1;
  U:=S[5];
  sigma:=S[6];
  sigma:=sigma^(V^2);
  lvarDelta:=S[7]^(V^2);
  lvarDelta:=lvarDelta^-1;
  T:=[varZ,V,tau,delta,U,sigma,lvarDelta];
  return T;
end);

BindGlobal("Thm71@",function(n,q)
local lvarDelta,F,OMIT,R,Rels,S,U,V,tau;
  Rels:=[];
  if n=2 then
    F:=FreeGroup("Delta","U");
    F:=Group(StraightLineProgGens(GeneratorsOfGroup(F)));
    lvarDelta:=F.1;
    U:=F.2;
    R:=[];
    Add(Rels,U^2);
  else
    F:=FreeGroup("Delta","U","V");
    F:=Group(StraightLineProgGens(GeneratorsOfGroup(F)));
    lvarDelta:=F.1;
    U:=F.2;
    V:=F.3;
    R:=PresentationForSn@(n);
    S:=FreeGroupOfFpGroup(R);
    R:=RelatorsOfFpGroup(R);
    tau:=GroupHomomorphismByImages(S,F, GeneratorsOfGroup(S), [U,V]);
    R:=List(R,r->ImagesRepresentative(tau,r));
    if n > 3 then
      Add(Rels,Comm(lvarDelta,U^(V^2)));
      Add(Rels,Comm(lvarDelta,lvarDelta^(V^2)));
    fi;
    if n > 4 then
      Add(Rels,Comm(lvarDelta,V*U*U^V));
    fi;
    Add(Rels,lvarDelta*lvarDelta^V/(lvarDelta^(V*U)));
    Add(Rels,Comm(lvarDelta,lvarDelta^V));
  fi;
  OMIT:=true;
  if not OMIT then
    Add(Rels,lvarDelta^U/(lvarDelta^-1));
    Add(Rels,lvarDelta^(q^2-1));
  fi;
  Rels:=Concatenation(Rels,R);
  return F/Rels;
end);

#OrderThm71:=function(n,q)
#return (q^2-1)^(n-1)*Factorial(n);
#end;

BindGlobal("Thm72@",function(n,q)
local lvarDelta,F,OMIT,R,Rels,S,U,V,delta,tau;
  F:=FreeGroup("Delta","U","V","delta");
  F:=Group(StraightLineProgGens(GeneratorsOfGroup(F)));
  lvarDelta:=F.1;
  U:=F.2;
  V:=F.3;
  delta:=F.4;
  Rels:=[];
  R:=Thm71@(n,q);
  S:=FreeGroupOfFpGroup(R);
  R:=RelatorsOfFpGroup(R);
  if n=2 then
    Add(Rels,U/V);
    tau:=GroupHomomorphismByImages(S,F, GeneratorsOfGroup(S), [lvarDelta,U]);
  else
    tau:=GroupHomomorphismByImages(S,F, GeneratorsOfGroup(S), [lvarDelta,U,V]);
  fi;
  R:=List(R,r->ImagesRepresentative(tau,r));
  OMIT:=true;
  if not OMIT then
    Add(Rels,delta^(q-1));
  fi;
  if n > 2 then
    Add(Rels,Comm(delta,U^V));
    Add(Rels,Comm(delta,lvarDelta^V));
  fi;
  Add(Rels,Comm(delta,lvarDelta));
  if n > 3 then
    Add(Rels,Comm(delta,V*U));
  fi;
  Add(Rels,lvarDelta^(q+1)/(delta*(delta^-1)^U));
  Rels:=Concatenation(Rels,R);
  return F/Rels;
end);

#OrderThm72:=function(n,q)
#return (q-1)*(q^2-1)^(n-1)*Factorial(n);
#end;

BindGlobal("SU_PresentationForN@",function(n,q)
local lvarDelta,F,OMIT,R,Rels,S,U,V,varZ,delta,tau;
  F:=FreeGroup("Delta","U","V","delta","Z");
  F:=Group(StraightLineProgGens(GeneratorsOfGroup(F)));
  lvarDelta:=F.1;
  U:=F.2;
  V:=F.3;
  delta:=F.4;
  varZ:=F.5;
  R:=Thm72@(n,q);
  S:=FreeGroupOfFpGroup(R);
  R:=RelatorsOfFpGroup(R);
  tau:=GroupHomomorphismByImages(S,F,
    GeneratorsOfGroup(S), [lvarDelta,U,V,delta]);
  R:=List(R,r->ImagesRepresentative(tau,r));
  Rels:=[];
  OMIT:=true;
  if not OMIT then
    if IsOddInt(q) then
      Add(Rels,varZ^2/(delta^(QuoInt((q-1),2))));
    else
      Add(Rels,varZ^2);
    fi;
    Add(Rels,delta^varZ*delta);
  fi;
  if n > 2 then
    Add(Rels,Comm(varZ,U^V));
    Add(Rels,Comm(varZ,lvarDelta^V));
  fi;
  if n > 3 then
    Add(Rels,Comm(varZ,V*U));
  fi;
  Add(Rels,Comm(varZ,varZ^U));
  Add(Rels,delta/Comm(lvarDelta^-1,varZ));
  if n=2 then
    Add(Rels,Comm(delta,varZ^U));
  fi;
  Rels:=Concatenation(Rels,R);
  return F/Rels;
end);

#OrderSU_N:=function(n,q)
#return 2^n*(q-1)*(q^2-1)^(n-1)*Factorial(n);
#end;

BindGlobal("EvenSUPresentation@",function(d,q)
local
   lvarDelta,varE,F,I,OMIT,R,R1,R2,R3,R4,Rels,S,U,V,W,varZ,a,delta,e,eta,f,m,n,p,
   phi,sigma,tau,w,w0,x,y;

  Assert(1,Size(DuplicateFreeList(Factors(q))) = 1);
  Assert(1,IsEvenInt(d) and d > 2);
  n:=QuoInt(d,2);
  e := Factors(q);
  if Size(DuplicateFreeList(e)) > 1 then
      f := false;
  else
      f := true;
      p := e[1];
      e := Size(e);
  fi;
  F:=FreeGroup("Z","V","tau","delta","U","sigma","Delta");
  F:=Group(StraightLineProgGens(GeneratorsOfGroup(F)));
  varZ:=F.1;
  V:=F.2;
  tau:=F.3;
  delta:=F.4; U:=F.5;
  sigma:=F.6;
  lvarDelta:=F.7;
  R:=[];
  R4:=SU_PresentationForN@(n,q);
  S:=FreeGroupOfFpGroup(R4);
  R4:=RelatorsOfFpGroup(R4);
  eta:=GroupHomomorphismByImages(S,F,
    GeneratorsOfGroup(S), [lvarDelta,U,V,delta,varZ]);

  R4:=List(R4,r->ImagesRepresentative(eta,r));
  #   centraliser of sigma
  if n > 3 then
    Add(R,Comm(U^(V^2),sigma));
  fi;
  if n > 4 then
    Add(R,Comm(V*U*U^V,sigma));
  fi;
  if n > 3 and IsOddInt(q) then
    Add(R,Comm(lvarDelta^(V^2),sigma));
  fi;
  if n=3 and IsOddInt(q) then
    Add(R,Comm(delta^(V^2),sigma));
  fi;
  if n > 2 then
    Add(R,Comm(varZ^(V^2),sigma));
    Add(R,Comm(lvarDelta*(lvarDelta^2)^V,sigma));
  fi;
  if n=2 then
    if IsEvenInt(q) then
      Add(R,Comm(delta*delta^U,sigma));
    else
      Add(R,Comm(lvarDelta^(QuoInt((q+1),2))*delta^-1,sigma));
    fi;
  fi;
  Add(R,Comm(varZ*U*varZ^-1,sigma));
  #   centraliser of tau
  if n > 2 then
    Add(R,Comm(U^V,tau));
  fi;
  if n=2 and IsOddInt(q) then
    Add(R,Comm(delta^U,tau));
  fi;
  if n > 2 then
    Add(R,Comm(lvarDelta^V,tau));
  fi;
  #   V*U is needed to generate centraliser of tau but relation not needed
  OMIT:=true;
  if not OMIT then
    if n > 3 then
      Add(R,Comm(V*U,tau));
    fi;
  fi;
  Add(R,Comm(varZ^U,tau));
  Add(R,Comm(lvarDelta^2*delta^-1,tau));
  R1:=PresentationForSL2@(p,e:Projective:=false);
  S:=FreeGroupOfFpGroup(R1);
  R1:=RelatorsOfFpGroup(R1);
  if e=1 then
    phi:=GroupHomomorphismByImages(S,F, GeneratorsOfGroup(S), [tau,varZ]);
    #   need to express delta as word in <tau, Z> = SL(2, p)
    w:=PrimitiveElement(GF(p));
    x:=Int(w^-1)-1;
    y:=Int(w^-2-w^-1);
    Add(R,delta/(tau^-1*(tau^x)^varZ*tau^(Int(w))*(tau^-y)^varZ));
  else
    phi:=GroupHomomorphismByImages(S,F,GeneratorsOfGroup(S),[delta,tau,varZ]);
  fi;
  R1:=List(R1,r->ImagesRepresentative(phi,r));
  # rewritten select statement
  if IsEvenInt(q) then
    W:=U;
  else
    W:=U*varZ^2;
  fi;
  R2:=PresentationForSL2@(p,2*e:Projective:=false);
  S:=FreeGroupOfFpGroup(R2);
  R2:=RelatorsOfFpGroup(R2);
  phi:=GroupHomomorphismByImages(S,F,GeneratorsOfGroup(S),[lvarDelta,sigma,W]);
  R2:=List(R2,r->ImagesRepresentative(phi,r));
  #   Steinberg relations
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
    # was  "w:=varE.1;"
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
  if n=2 and q=3 then
    Add(R3,tau/Comm((sigma^-1)^(U*varZ),sigma)^lvarDelta);
  fi;
  Rels:=Concatenation(R,R1,R2,R3,R4);
  return F/Rels;
end);
