#   usually subgroups chosen for coset enumeration are maximal of smallest index

#SetGlobalTCParameters(:CosetLimit:=10^7,Hard:=true,Print:=10^6);
#LoadPackage("ace");
#TCENUM:=ACETCENUM;

DeclareInfoClass("InfoPresTest");
SetInfoLevel(InfoPresTest,1);
SetAssertionLevel(1);

dim_limit:=20;
#   max dimension
field_limit:=100;
#   max size of field
#   Presentation = false: presentation rewritten on standard generators
#   Presentation = true: presentation listed in paper
#   Projective = true: presentation for group modulo its centre
#   do matrices satisfy presentation?
#   coset enumerations
TestSL:=function(a_list,b_list)
local DD,F,I,K,Presentation,Projective,QQ,U,V,d,delta,e,f,p,q,tau,gens,noenum;
  Projective:=ValueOption("Projective");
  if Projective=fail then
    Projective:=false;
  fi;
  Presentation:=ValueOption("Presentation");
  if Presentation=fail then
    Presentation:=true;
  fi;
  noenum:=ValueOption("noenum");
  if Projective then Info(InfoPresTest,1,"Doing Projective");fi;
  if Presentation then Info(InfoPresTest,1,"Doing Presentation");fi;
  for d in a_list do
    for q in b_list do
      DD:=d;
      QQ:=q;
      Info(InfoPresTest,1,"SL:  D = ",d,", q = ",q,", enum:",noenum<>true);
      if d=2 then
        F:=ClassicalStandardPresentation("SL",d,q:Projective:=Projective,
         PresentationGenerators:=false);
        gens:=ClassicalStandardGenerators("SL",d,q:Projective:=Projective,
         PresentationGenerators:=false);
      else
        F:=ClassicalStandardPresentation("SL",d,q:Projective:=Projective,
         PresentationGenerators:=Presentation);
        gens:=ClassicalStandardGenerators("SL",d,q:Projective:=Projective,
         PresentationGenerators:=Presentation);
      fi;

      # verify relators
      U:=FreeGeneratorsOfFpGroup(F);
      V:=List(RelatorsOfFpGroup(F),
        x->MappedWord(x,FreeGeneratorsOfFpGroup(F),gens));
      I:=Filtered([1..Length(V)],x->not IsOne(V[x]));
      if Length(I)>0 and (Projective=false or ForAny(V{I},x->x<>x^0*x[1][1])) then
        Error("Relators ",I," don't hold");
      fi;

      e := Factors(q);
      if Size(DuplicateFreeList(e)) > 1 then
          f := false;
      else
          f := true;
          p := e[1];
          e := Size(e);
      fi;
      U:=F.1;
      V:=F.2;
      tau:=F.3;
      delta:=F.4;
      if d=2 then
        K:=Subgroup(F,[tau,delta]);
      else
        #   max? subgroup containing SL(d - 1, q)
        K:=Subgroup(F,[U,tau,V*U^(V^-1),delta,delta^(V^-1),tau^(V^-1)]);
      fi;

      Assert(1,IsPerfectGroup(F));
      if noenum<>true then
        I:=Range(FactorCosetAction(F,K:max:=10^7,Wo:=10^8,Hard:=true));
        if NrMovedPoints(I) < 10^7 then
          Size(I);
          # We tested already that the simple group is a quotient
          if not IsSimpleGroup(I) then Error("not simple");fi;
          if d=2 then
            Assert(1,NrMovedPoints(I)=q+1);
          else
            Assert(1,(q^d-1) mod NrMovedPoints(I)=0);
            #   else assert Degree (I) eq (q^d - 1);
          fi;
        fi;
      fi;

    od;
  od;
  return true;
end;

TestSp:=function(list_a,list_b)
local F,I,K,Presentation,Projective,Q,R,U,V,varX,varZ,d,delta,e,f,m,p,phi,q,
   sigma,tau,words,gens,noenum;
  Projective:=ValueOption("Projective");
  if Projective=fail then
    Projective:=false;
  fi;
  Presentation:=ValueOption("Presentation");
  if Presentation=fail then
    Presentation:=true;
  fi;
  noenum:=ValueOption("noenum");
  if Projective then Info(InfoPresTest,1,"Doing Projective");fi;
  if Presentation then Info(InfoPresTest,1,"Doing Presentation");fi;
  for d in list_a do
    for q in list_b do
      Info(InfoPresTest,1,"Sp:  D = ",d,", q = ",q,", enum:",noenum<>true);
        e := Factors(q);
        if Size(DuplicateFreeList(e)) > 1 then
            f := false;
        else
            f := true;
            p := e[1];
            e := Size(e);
        fi;
      R:=ClassicalStandardPresentation("Sp",d,q:Projective:=Projective,
       PresentationGenerators:=Presentation);
      gens:=ClassicalStandardGenerators("Sp",d,q:Projective:=Projective,
       PresentationGenerators:=Presentation);
      Q:=FreeGroupOfFpGroup(R);
      R:=RelatorsOfFpGroup(R);
      F:=Q/R;

      # verify relators
      U:=FreeGeneratorsOfFpGroup(F);
      V:=List(RelatorsOfFpGroup(F),
        x->MappedWord(x,FreeGeneratorsOfFpGroup(F),gens));
      I:=Filtered([1..Length(V)],x->not IsOne(V[x]));
      if Length(I)>0 and (Projective=false or ForAny(V{I},x->x<>x^0*x[1][1])) then
        Error("Relators ",I," don't hold");
      fi;

      if Presentation then
        varZ:=F.1;
        V:=F.2;
        tau:=F.3;
        delta:=F.4;
        U:=F.5;
        sigma:=F.6;
      else
        words:=SpStandardToPresentation@(d,q);
        # was "varX:=Evaluate(words,List([1..Size(GeneratorsOfGroup(Q))],i->Q.i));"
        gens:=GeneratorsOfGroup(FamilyObj(words)!.wholeGroup);
        varX:=List(words,w->MappedWord(w, gens, GeneratorsOfGroup(Q)));
        phi:=GroupHomomorphismByImages(Q,F,
          GeneratorsOfGroup(Q),GeneratorsOfGroup(F));
        varX:=List(varX,x->ImagesRepresentative(phi,x));
        varZ:=varX[1];
        V:=varX[2];
        tau:=varX[3];
        delta:=varX[4];
        U:=varX[5];
        sigma:=varX[6];
      fi;
      if d=4 then
        K:=SubgroupNC(F,[varZ,tau,delta,delta^(V),sigma]);
      else
        m:=(QuoInt(d,2))-1;
        K:=SubgroupNC(F,
          [U,(V*U)^(V^-1),varZ,tau,delta,delta^(V^(m)),sigma,sigma^(V^(m))]);
      fi;

      Assert(1,IsPerfectGroup(F));
      if noenum<>true then
        I:=Range(FactorCosetAction(F,K:max:=10^7,Wo:=10^8,Hard:=true));
        if NrMovedPoints(I) < 10^7 then
          Size(I);
          # We tested already that the simple group is a quotient
          if not IsSimpleGroup(I) then Error("not simple");fi;
          Assert(1,Size(I)=Size(SP(d,q)) or Size(I)=QuoInt(Size(SP(d,q)),2));
        fi;
      fi;

    od;
  od;
  return true;
end;


TestPlusOdd:=function(list_a,list_b)
local lvarDelta,F,I,K,Presentation,Projective,Q,R,U,V,varX,varZ,d,phi,q,
  sigma,words,gens,noenum;

  Presentation:=ValueOption("Presentation");
  if Presentation=fail then
    Presentation:=true;
  fi;
  Projective:=ValueOption("Projective");
  if Projective=fail then
    Projective:=false;
  fi;
  noenum:=ValueOption("noenum");
  for d in list_a do
    Assert(1,IsEvenInt(d));
    for q in list_b do
      Info(InfoPresTest,1,"OplusOdd:  D = ",d,", q = ",q,", enum:",noenum<>true);
      Assert(1,IsOddInt(q));
      R:=ClassicalStandardPresentation("Omega+",d,
       q:PresentationGenerators:=Presentation,Projective:=Projective);
      Q:=FreeGroupOfFpGroup(R);
      R:=RelatorsOfFpGroup(R);
      F:=Q/R;
      if d=4 then
        K:=Subgroup(F,GeneratorsOfGroup(F){[1,3,5,6,7]});
      else
        if Presentation then
          lvarDelta:=F.1;
          sigma:=F.2;
          varZ:=F.3;
          U:=F.4;
          V:=F.5;
        else
          words:=PlusStandardToPresentation@(d,q);
          # was "varX:=Evaluate(words,List([1..Size(GeneratorsOfGroup(Q))],i->Q.i));"
          gens:=GeneratorsOfGroup(FamilyObj(words)!.wholeGroup);
          varX:=List(words,
            w-> MappedWord(w, gens, GeneratorsOfGroup(Q)));
          phi:=GroupHomomorphismByImages(Q,F,
            GeneratorsOfGroup(Q),GeneratorsOfGroup(F));
          varX:=List(varX,x->ImagesRepresentative(phi,x));
          lvarDelta:=varX[1];
          sigma:=varX[2];
          varZ:=varX[3];
          U:=varX[4];
          V:=varX[5];
        fi;
        K:=Subgroup(F, [U^V,varZ^V,sigma^V,lvarDelta^V,
          (sigma^(varZ^V))^V,V*U,sigma,lvarDelta]);
      fi;
      gens:=ClassicalStandardGenerators("Omega+",d,q:Projective:=Projective,
       PresentationGenerators:=Presentation);

      # verify relators
      U:=FreeGeneratorsOfFpGroup(F);
      V:=List(RelatorsOfFpGroup(F),
        x->MappedWord(x,FreeGeneratorsOfFpGroup(F),gens));
      I:=Filtered([1..Length(V)],x->not IsOne(V[x]));
      if Length(I)>0 and (Projective=false or ForAny(V{I},x->x<>x^0*x[1][1])) then
        Error("Relators ",I," don't hold");
      fi;

      Assert(1,IsPerfectGroup(F));
      if noenum<>true then
        I:=Range(FactorCosetAction(F,K:max:=10^7,Wo:=10^8,Hard:=true));
        Size(I);
        # We tested already that the simple group is a quotient
        if not IsSimpleGroup(I) then Error("not simple");fi;
      fi;
    od;
  od;
  return true;
end;

TestPlusEven:=function(list_a,list_b)
local lvarDelta,F,I,K,Presentation,Q,R,U,V,varX,varZ,d,delta,phi,q,sigma,
  gens,words,noenum;
  Presentation:=ValueOption("Presentation");
  if Presentation=fail then
    Presentation:=true;
  fi;
  noenum:=ValueOption("noenum");
  for d in list_a do
    Assert(1,IsEvenInt(d));
    for q in list_b do
      Info(InfoPresTest,1,"OplusEven:  D = ",d,", q = ",q,", enum:",
        noenum<>true);
      Assert(1,IsEvenInt(q));
      R:=ClassicalStandardPresentation("Omega+",d,
       q:PresentationGenerators:=Presentation);
      Q:=FreeGroupOfFpGroup(R);
      R:=RelatorsOfFpGroup(R);
      F:=Q/R;
      if d=4 then
        K:=SubgroupNC(F,GeneratorsOfGroup(F){[1,3,5,6,7]});
      else
        if Presentation then
          delta:=F.1;
          sigma:=F.2;
          varZ:=F.3;
          U:=F.4;
          V:=F.5;
        else
          words:=PlusStandardToPresentation@(d,q);
          # was "varX:=Evaluate(words,List([1..Size(GeneratorsOfGroup(Q))],i->Q.i));"
          gens:=GeneratorsOfGroup(FamilyObj(words)!.wholeGroup);
          varX:=List(words,w-> MappedWord(w, gens, GeneratorsOfGroup(Q)));
          phi:=GroupHomomorphismByImages(Q,F,
            GeneratorsOfGroup(Q),GeneratorsOfGroup(F));
          varX:=List(varX,x->ImagesRepresentative(phi,x));
          delta:=varX[1];
          sigma:=varX[2];
          varZ:=varX[3];
          U:=varX[4];
          V:=varX[5];
        fi;
        lvarDelta:=delta*(delta^-1)^U;
        K:=Subgroup(F,[U^V,varZ^V,sigma^V,lvarDelta^V,
          (sigma^(varZ^V))^V,V*U,sigma,lvarDelta]);
      fi;
      gens:=ClassicalStandardGenerators("Omega+",d,q:
       PresentationGenerators:=Presentation);

      # verify relators
      U:=FreeGeneratorsOfFpGroup(F);
      V:=List(RelatorsOfFpGroup(F),
        x->MappedWord(x,FreeGeneratorsOfFpGroup(F),gens));
      I:=Filtered([1..Length(V)],x->not IsOne(V[x]));
      if Length(I)>0 then
        Error("Relators ",I," don't hold");
      fi;

      Assert(1,IsPerfectGroup(F));
      if noenum<>true then
        I:=Range(FactorCosetAction(F,K:max:=10^7,Wo:=10^8,Hard:=true));
        Size(I);
        # We tested already that the simple group is a quotient
        if not IsSimpleGroup(I) then Error("not simple");fi;
      fi;

    od;
  od;
  return true;
end;

TestPlus:=function(list_a,list_b)
local Presentation,Projective,d,f,q;
  Presentation:=ValueOption("Presentation");
  if Presentation=fail then
    Presentation:=true;
  fi;
  Projective:=ValueOption("Projective");
  if Projective=fail then
    Projective:=false;
  fi;
  if Projective then Info(InfoPresTest,1,"Doing Projective");fi;
  if Presentation then Info(InfoPresTest,1,"Doing Presentation");fi;
  for d in list_a do
    for q in list_b do
      if IsEvenInt(q) then
        f:=TestPlusEven([d],[q]:Presentation:=Presentation);
      else
        f:=TestPlusOdd([d],[q]
         :Presentation:=Presentation,Projective:=Projective);
      fi;
    od;
  od;
  return true;
end;

TestMinus:=function(list_a,list_b)
local lvarDelta,F,I,K,Presentation,Projective,Q,R,U,V,varX,d,phi,q,
  gens,sigma,tau,words,z,noenum;
  Presentation:=ValueOption("Presentation");
  if Presentation=fail then
    Presentation:=true;
  fi;
  Projective:=ValueOption("Projective");
  if Projective=fail then
    Projective:=false;
  fi;
  noenum:=ValueOption("noenum");
  if Projective then Info(InfoPresTest,1,"Doing Projective");fi;
  if Presentation then Info(InfoPresTest,1,"Doing Presentation");fi;
  for d in list_a do
    Assert(1,IsEvenInt(d));
    for q in list_b do
      Info(InfoPresTest,1,"O-:  D = ",d,", q = ",q,", enum:",noenum<>true);
      R:=ClassicalStandardPresentation("Omega-",d, q:
        PresentationGenerators:=Presentation,Projective:=Projective);
      Q:=FreeGroupOfFpGroup(R);
      R:=RelatorsOfFpGroup(R);
      F:=Q/R;
      if d=4 then
        K:=SubgroupNC(F,GeneratorsOfGroup(F){[2..5]});
      else
        if Presentation then
          z:=F.1;
          sigma:=F.3;
          tau:=F.2;
          U:=F.5;
          lvarDelta:=F.4;
          if d=6 then
            V:=One(F);
          else
            V:=F.6;
          fi;
        else
          words:=MinusStandardToPresentation@(d,q);
          # was "varX:=Evaluate(words,List([1..Size(GeneratorsOfGroup(Q))],i->Q.i));"
          gens:=GeneratorsOfGroup(FamilyObj(words)!.wholeGroup);
          varX:=List(words,w-> MappedWord(w, gens, GeneratorsOfGroup(Q)));
          phi:=GroupHomomorphismByImages(Q,F,
            GeneratorsOfGroup(Q),GeneratorsOfGroup(F));
          varX:=List(varX,x->ImagesRepresentative(phi,x));
          z:=varX[1];
          sigma:=varX[3];
          tau:=varX[2];
          U:=varX[5];
          lvarDelta:=varX[4];
          if d=6 then
            V:=varX[1]^0;
          else
            V:=varX[6];
          fi;
        fi;
        if d=6 then
          K:=SubgroupNC(F,[lvarDelta,sigma,tau,lvarDelta^U,V*U^-1]);
        else
          K:=SubgroupNC(F,[lvarDelta,sigma,tau,lvarDelta^U,
            z^U,tau^U,U^V,V*U^-1]);
        fi;
      fi;
      gens:=ClassicalStandardGenerators("Omega-",d,q:
       PresentationGenerators:=Presentation);

      # verify relators
      U:=FreeGeneratorsOfFpGroup(F);
      V:=List(RelatorsOfFpGroup(F),
        x->MappedWord(x,FreeGeneratorsOfFpGroup(F),gens));
      I:=Filtered([1..Length(V)],x->not IsOne(V[x]));
      if Length(I)>0 and (Projective=false or ForAny(V{I},x->x<>x^0*x[1][1])) then
        Error("Relators ",I," don't hold");
      fi;

      Assert(1,IsPerfectGroup(F));
      if noenum<>true then
        I:=Range(FactorCosetAction(F,K:max:=10^7,Wo:=10^8,Hard:=true));
        Size(I);
        # We tested already that the simple group is a quotient
        if not IsSimpleGroup(I) then Error("not simple");fi;
      fi;

    od;
  od;
  return true;
end;

TestOmega:=function(list_a,list_b)
local
   lvarDelta,F,I,K,Presentation,Projective,Q,R,U,V,varX,varZ,d,phi,q,sigma,tau,
   words,gens,noenum;
  Presentation:=ValueOption("Presentation");
  if Presentation=fail then
    Presentation:=true;
  fi;
  Projective:=ValueOption("Projective");
  if Projective=fail then
    Projective:=false;
  fi;
  noenum:=ValueOption("noenum");
  for d in list_a do
    Assert(1,IsOddInt(d));
    for q in list_b do
      Info(InfoPresTest,1,"Omega:  D = ",d,", q = ",q,", enum:",noenum<>true);
      Assert(1,IsOddInt(q));
      R:=ClassicalStandardPresentation("Omega",d,q:Projective:=Projective,
       PresentationGenerators:=Presentation);
      Q:=FreeGroupOfFpGroup(R);
      R:=RelatorsOfFpGroup(R);
      F:=Q/R;
      if d=3 then
        K:=Subgroup(F,[F.2, F.3]);
      else
        if Presentation=false then
          words:=OmegaStandardToPresentation@(d,q);
          # was "varX:=Evaluate(words,List([1..Size(GeneratorsOfGroup(Q))],i->Q.i));"
          gens:=GeneratorsOfGroup(FamilyObj(words)!.wholeGroup);
          varX:=List(words,w-> MappedWord(w, gens,GeneratorsOfGroup(Q)));
          phi:=GroupHomomorphismByImages(Q,F,
            GeneratorsOfGroup(Q),GeneratorsOfGroup(F));
          varX:=List(varX,x->ImagesRepresentative(phi,x));
          lvarDelta:=varX[1];
          varZ:=varX[2];
          tau:=varX[3];
          sigma:=varX[4];
          U:=varX[5];
          V:=varX[6];
        else
          lvarDelta:=F.1;
          varZ:=F.2;
          tau:=F.3;
          sigma:=F.4;
          U:=F.5;
          V:=F.6;
        fi;
        #   SOPlus (d - 1, q).2
        K:=Subgroup(F,[lvarDelta, varZ,sigma,U,V]);
      fi;
      gens:=ClassicalStandardGenerators("Omega",d,q:
       PresentationGenerators:=Presentation);

      # verify relators
      U:=FreeGeneratorsOfFpGroup(F);
      V:=List(RelatorsOfFpGroup(F),
        x->MappedWord(x,FreeGeneratorsOfFpGroup(F),gens));
      I:=Filtered([1..Length(V)],x->not IsOne(V[x]));
      if Length(I)>0 and (Projective=false or ForAny(V{I},x->x<>x^0*x[1][1])) then
        Error("Relators ",I," don't hold");
      fi;

      Assert(1,IsPerfectGroup(F));
      if noenum<>true then
        I:=Range(FactorCosetAction(F,K:max:=10^7,Wo:=10^8,Hard:=true));
        Size(I);
        # We tested already that the simple group is a quotient
        if not IsSimpleGroup(I) then Error("not simple");fi;
      fi;
    od;
  od;
  return true;
end;

TestSUEven:=function(list_a,list_b)
local lvarDelta,F,I,K,Presentation,Projective,U,V,varZ,d,delta,n,q,sigma,
  tau,gens,noenum;

  Projective:=ValueOption("Projective");
  if Projective=fail then
    Projective:=false;
  fi;
  Presentation:=ValueOption("Presentation");
  if Presentation=fail then
    Presentation:=true;
  fi;
  noenum:=ValueOption("noenum");
  for d in list_a do
    Assert(1,IsEvenInt(d));
    n:=QuoInt(d,2);
    for q in list_b do
      Info(InfoPresTest,1,"SUeven:  D = ",d,", q = ",q,", enum:",noenum<>true);
      F:=ClassicalStandardPresentation("SU",d,q:Projective:=Projective,
       PresentationGenerators:=Presentation);
      varZ:=F.1;
      V:=F.2;
      tau:=F.3;
      delta:=F.4;
      U:=F.5;
      sigma:=F.6;
      lvarDelta:=F.7;
      if d=4 then
        #   K := sub < F | [Z, V, U, delta, sigma, tau]>;
        #   maximal x^a y^b L(2, q^2)
        K:=Subgroup(F,[V,tau,delta,sigma,lvarDelta]);
      else
        if Presentation then
          if d=6 then
            K:=Subgroup(F,[varZ,U,lvarDelta^(V^-2),sigma^(V^(n-2)),sigma]);
          else
            K:=Subgroup(F,[varZ,U,U^(V^-2)*V,lvarDelta,lvarDelta^(V^-2)
             ,delta,tau,sigma^(V^(n-2)),sigma]);
          fi;
        else
          K:=Subgroup(F,[varZ,U,U^(V^-2)
           *V,lvarDelta,delta,tau,sigma^(V^(n-2)),sigma]);
        fi;
      fi;
      gens:=ClassicalStandardGenerators("SU",d,q:
       PresentationGenerators:=Presentation);

      # verify relators
      U:=FreeGeneratorsOfFpGroup(F);
      V:=List(RelatorsOfFpGroup(F),
        x->MappedWord(x,FreeGeneratorsOfFpGroup(F),gens));
      I:=Filtered([1..Length(V)],x->not IsOne(V[x]));
      if Length(I)>0 and (Projective=false or ForAny(V{I},x->x<>x^0*x[1][1])) then
        Error("Relators ",I," don't hold");
      fi;

      Assert(1,IsPerfectGroup(F));
      if noenum<>true then
        I:=Range(FactorCosetAction(F,K:max:=10^7,Wo:=10^8,Hard:=true));
        Size(I);
        # We tested already that the simple group is a quotient
        if not IsSimpleGroup(I) then Error("not simple");fi;
      fi;

    od;
  od;
  return true;
end;

TestSUOdd:=function(list_a,list_b)
local lvarDelta,F,lvarGamma,I,K,Presentation,Projective,Q,R,U,V,varX,varZ,
   d,n,phi,q,sigma,t,tau,v,words,gens,noenum;

  Projective:=ValueOption("Projective");
  if Projective=fail then
    Projective:=false;
  fi;
  Presentation:=ValueOption("Presentation");
  if Presentation=fail then
    Presentation:=true;
  fi;
  noenum:=ValueOption("noenum");
  for d in list_a do
    Assert(1,IsOddInt(d));
    n:=QuoInt(d,2);
    for q in list_b do
      Info(InfoPresTest,1,"SUodd:  D = ",d,", q = ",q,", enum:",noenum<>true);
      if d=3 then
        R:=ClassicalStandardPresentation("SU",d,q:Projective:=Projective,
         PresentationGenerators:=true);
        Q:=FreeGroupOfFpGroup(R);
        R:=RelatorsOfFpGroup(R);
      else
        R:=ClassicalStandardPresentation("SU",d,q:Projective:=Projective,
         PresentationGenerators:=Presentation);
        Q:=FreeGroupOfFpGroup(R);
        R:=RelatorsOfFpGroup(R);
      fi;
      F:=Q/R;
      if d > 3 then
        varX:=GeneratorsOfGroup(F);
        if not Presentation then
          words:=SUStandardToPresentation@(d,q);
          gens:=GeneratorsOfGroup(FamilyObj(words)!.wholeGroup);
          varX:=List(words,x->MappedWord(x,gens,GeneratorsOfGroup(Q)));
          phi:=GroupHomomorphismByImages(Q,F,
            GeneratorsOfGroup(Q),GeneratorsOfGroup(F){[1..7]});
          varX:=List(varX,x->ImagesRepresentative(phi,x));
        fi;
        lvarGamma:=varX[1];
        t:=varX[2];
        U:=varX[3];
        V:=varX[4];
        sigma:=varX[5];
        tau:=varX[6];
        v:=varX[7];
        if IsEvenInt(q) then
          varZ:=t;
        else
          varZ:=(lvarGamma^-1)^(QuoInt((q^2+q),2))*t;
        fi;
        lvarDelta:=lvarGamma*(lvarGamma^-1)^U;
      fi;
      if d=3 then
        #   index q^3 + 1
        #   standard? K := sub<F | F.3, F.6, F.7>;
        K:=Subgroup(F,[F.1,F.3]);
      elif d=5 then
        #   p^k * SU(d-2, q)
        K:=Subgroup(F,Concatenation([lvarGamma,V*(U^(V^-1))],
          List([lvarGamma,t,tau,v],x->x^U),[sigma]));
      else
        #   d >= 7
        #   SU(d-1, q)
        #   K := sub < F | [ Z, V, U, Delta, sigma, Gamma ]>;
        #   p^k * SU(d-2, q)
        K:=Subgroup(F,Concatenation([lvarGamma,V*U,U^V],
          List([lvarGamma,t,tau,v],x->x^U),[sigma]));
      fi;

      gens:=ClassicalStandardGenerators("SU",d,q:
       PresentationGenerators:=Presentation);

      # verify relators
      U:=FreeGeneratorsOfFpGroup(F);
      V:=List(RelatorsOfFpGroup(F),
        x->MappedWord(x,FreeGeneratorsOfFpGroup(F),gens));
      I:=Filtered([1..Length(V)],x->not IsOne(V[x]));
      if Length(I)>0 and (Projective=false or ForAny(V{I},x->x<>x^0*x[1][1])) then
        Error("Relators ",I," don't hold");
      fi;

      Assert(1,IsPerfectGroup(F));
      if noenum<>true then
        I:=Range(FactorCosetAction(F,K:max:=10^7,Wo:=10^8,Hard:=true));
        Size(I);
        # We tested already that the simple group is a quotient
        if not IsSimpleGroup(I) then Error("not simple");fi;
      fi;

    od;
  od;
  return true;
end;

TestSU:=function(list_a,list_b)
local Presentation,Projective,d,f,q;
  Presentation:=ValueOption("Presentation");
  if Presentation=fail then
    Presentation:=true;
  fi;
  Projective:=ValueOption("Projective");
  if Projective=fail then
    Projective:=false;
  fi;
  if Projective then Info(InfoPresTest,1,"Doing Projective");fi;
  if Presentation then Info(InfoPresTest,1,"Doing Presentation");fi;
  for d in list_a do
    for q in list_b do
      if IsEvenInt(d) then
        f:=TestSUEven([d],[q]:Presentation:=Presentation,Projective:=Projective)
         ;
      else
        f:=TestSUOdd([d],[q]:Presentation:=Presentation,Projective:=Projective)
         ;
      fi;
    od;
  od;
  return true;
end;

BigTest:=function()
  TestSL([2],Filtered([5..15],IsPrimePowerInt):noenum);
  TestSL([3..20],Filtered([1..101],IsPrimePowerInt):noenum);
  TestSL([3,4],Filtered([2..25],IsPrimePowerInt));
  TestSL([5,6],[2..5]);
  TestSL([7,8],[2,3,4]);

  TestSp([6,8..20],Filtered([1..101],IsPrimePowerInt):noenum);
  TestSp([6],[2,3,4,5,7]);
  TestSp([8,10],[2,3,4]);

  TestPlus([6,8..20],Filtered([1..101],IsPrimePowerInt):noenum);
  TestMinus([6,8..20],Filtered([1..101],IsPrimePowerInt):noenum);

  TestPlus([6],Filtered([1..15],IsPrimePowerInt));
  TestPlus([8,10],[2,3,4]);
  TestMinus([6],Filtered([1..11],IsPrimePowerInt));
  TestMinus([8,10],[2,3,4]);

  TestOmega([3],Filtered([5,7..101],IsPrimePowerInt):noenum);
  TestOmega([5,7..19],Filtered([1,3..101],IsPrimePowerInt):noenum);
  TestOmega([3],Filtered([5,7..45],IsPrimePowerInt));
  TestOmega([5,7],Filtered([1,3..11],IsPrimePowerInt));
  TestOmega([9,11],[3]);

  TestSU([3],Filtered([3..100],IsPrimePowerInt):noenum);
  TestSU([4..10],Filtered([2..80],IsPrimePowerInt):noenum);
  TestSU([11..20],Filtered([2..15],IsPrimePowerInt):noenum);
  TestSU([3],Filtered([3..12],IsPrimePowerInt));
  TestSU([4],Filtered([2..10],IsPrimePowerInt));
  TestSU([5],[2,3,4,5,7]);
  TestSU([6,7],[2,3]);
  TestSU([8],[2]); # current simplicity test fails on SU(8,3)
end;

LittleTest:=function()
  SetInfoLevel(InfoPresTest,0);
  TestSL([3..10],Filtered([1..15],IsPrimePowerInt):noenum);
  TestSp([6,8],Filtered([1..10],IsPrimePowerInt):noenum);
  TestPlus([6,8..20],Filtered([1..10],IsPrimePowerInt):noenum);
  TestMinus([6,8..20],Filtered([1..10],IsPrimePowerInt):noenum);
  # do not test Omega in 4.11 -- the `Omega` function does not work
  if CompareVersionNumbers(GAPInfo.Version,"4.12") then
    TestOmega([3,5,7],Filtered([5,7..11],IsPrimePowerInt):noenum);
  fi;
  TestSU([3,4],Filtered([3..10],IsPrimePowerInt):noenum);
end;
