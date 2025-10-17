# Edited and checked 11/7/19 by MW

BindGlobal("SignedOdd@",function(d)
local Rels,S,u,v;
  S:=FreeGroup(2);
  S:=Group(StraightLineProgGens(GeneratorsOfGroup(S)));
  u:=S.1;
  v:=S.2;
  Rels:=Concatenation([u^4,(u^2)^(v*u)*u^2*(u^2)^v,v^d,(u*v)^(d-1),(u*v^-1*u*v)
   ^3],List([2..QuoInt(d,2)],j->Comm(u,v^-j*u*v^j)));
  return S/Rels;
end);

BindGlobal("SignedEven@",function(d)
local R,Rels,S,u,v;
  S:=FreeGroup(2);
  S:=Group(StraightLineProgGens(GeneratorsOfGroup(S)));
  u:=S.1;
  v:=S.2;
  if d=2 then
    Rels:=[u^4,u*v^-1];
    return S/Rels;
  fi;
  Rels:=Concatenation([u^4,(u^2)^(v*u)*u^2*(u^2)^v,(u*v^-1*u*v)^3]
   ,List([2..QuoInt(d,2)],j->Comm(u,v^-j*u*v^j)));
  R:=[v^d/(u*v)^(d-1),Comm(v^d,u),v^(2*d)];
  Rels:=Concatenation(Rels,R);
  return S/Rels;
end);

#   presentation for group of signed permutation matrices of rank d and det 1
BindGlobal("SignedPermutations@",function(d)
Assert(1,d > 1);
  if IsEvenInt(d) then
    return SignedEven@(d);
  else
    return SignedOdd@(d);
  fi;
end);

BindGlobal("OrderSigned@",function(d)
  return 2^(d-1)*Factorial(d);
end);
