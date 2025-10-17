InstallGlobalFunction(Internal_StandardPresentationForOmega@,function(d,K)
#  -> ,GrpSLP ,[ ,]  return standard presentation for Omega ( d , q )
local Presentation,Projective,Type,q;
  Projective:=ValueOption("Projective");
  if Projective=fail then
    Projective:=false;
  fi;
  Presentation:=ValueOption("Presentation");
  if Presentation=fail then
    Presentation:=false;
  fi;
  Type:=ValueOption("Type");
  if Type=fail then
    Type:="Omega+";
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

  if Type="Omega" then
      if not IsOddInt(d) and d >= 3 then
      Error("Degree must be odd and at least 3");
    fi;
    if not IsOddInt(q) then
      Error("Field size must be odd");
    fi;
    return OmegaPresentation@(d,q:Projective:=Projective,
      Presentation:=Presentation);
  elif Type="Omega+" then
      if not IsEvenInt(d) and d >= 4 then
      Error("Degree must be even and at least 4");
    fi;
    return
     PlusPresentation@(d,q:Projective:=Projective,Presentation:=Presentation);
  elif Type="Omega-" then
      if not IsEvenInt(d) and d >= 4 then
      Error("Degree must be even and at least 4");
    fi;
    return
     MinusPresentation@(d,q:Projective:=Projective,Presentation:=Presentation);
  else
    Error("Invalid input");
  fi;
end);
