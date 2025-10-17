#     This file belongs to ALCO: Tools for Algebraic Combinatorics.
#     Copyright (C) 2024, Benjamin Nasmith

#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.

#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.

#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <https://www.gnu.org/licenses/>.

# Cyclotomic tools

BindGlobal( "EisensteinIntegers", Objectify( NewType(
    CollectionsFamily(CyclotomicsFamily),
    IsEisensteinIntegers and IsAttributeStoringRep ),
    rec() ) );

SetLeftActingDomain( EisensteinIntegers, Integers );
SetName( EisensteinIntegers, "EisensteinIntegers" );
SetString( EisensteinIntegers, "EisensteinIntegers" );
SetIsLeftActedOnByDivisionRing( EisensteinIntegers, false );
SetSize( EisensteinIntegers, infinity );
SetGeneratorsOfRing( EisensteinIntegers, [ E(3) ] );
SetGeneratorsOfLeftModule( EisensteinIntegers, [ 1, E(3) ] );
SetIsFinitelyGeneratedMagma( EisensteinIntegers, false );
SetUnits( EisensteinIntegers, Set([ -1, 1, -E(3), E(3), -E(3)^2, E(3)^2 ] ));
SetIsWholeFamily( EisensteinIntegers, false );

InstallMethod( \in,
    "for Eisenstein integers",
    IsElmsColls,
    [ IsCyc, IsEisensteinIntegers ],
    function( cyc, EisensteinIntegers )
    return IsCycInt( cyc ) and 3 mod Conductor( cyc ) = 0;
    end );

InstallMethod( IsEisenInt, 
    "for cyclotomics", 
    [ IsCyc ],
    function(x) 
        return x in EisensteinIntegers;
    end);

InstallMethod( Basis,
    "for Eisenstein integers (delegate to `CanonicalBasis')",
    [ IsEisensteinIntegers ], CANONICAL_BASIS_FLAGS,
    CanonicalBasis );

InstallMethod( CanonicalBasis,
    "for Eisenstein integers",
    [ IsEisensteinIntegers ],
    function( EisensteinIntegers )
    local B;

    B:= Objectify( NewType( FamilyObj( EisensteinIntegers ),
                                IsFiniteBasisDefault
                            and IsCanonicalBasis
                            and IsCanonicalBasisEisensteinIntegersRep ),
                   rec() );
    SetUnderlyingLeftModule( B, EisensteinIntegers );
    SetIsIntegralBasis( B, true );
    SetBasisVectors( B, Immutable( [ 1, E(3) ] ) );
    B!.conductor:= 3;
    B!.zumbroichbase := [ 0, 1 ];

    # Return the basis.
    return B;
    end );

InstallMethod( Coefficients,
    "for the canonical basis of Eisenstein integers",
    [ IsCanonicalBasisEisensteinIntegersRep,
      IsCyc ], 0,
    function( B, v )
        return Coefficients(Basis(CF(3), BasisVectors(B)), v);
    end );

BindGlobal( "KleinianIntegers", Objectify( NewType(
    CollectionsFamily(CyclotomicsFamily),
    IsKleinianIntegers and IsAttributeStoringRep ),
    rec() ) );

SetLeftActingDomain( KleinianIntegers, Integers );
SetName( KleinianIntegers, "KleinianIntegers" );
SetString( KleinianIntegers, "KleinianIntegers" );
SetIsLeftActedOnByDivisionRing( KleinianIntegers, false );
SetSize( KleinianIntegers, infinity );
SetGeneratorsOfRing( KleinianIntegers, [ 1, EB(7) ] );
SetGeneratorsOfLeftModule( KleinianIntegers, [ 1, EB(7) ] );
SetIsFinitelyGeneratedMagma( KleinianIntegers, false );
SetUnits( KleinianIntegers, Set([ -1, 1 ] ));
SetIsWholeFamily( KleinianIntegers, false );

InstallMethod( IsKleinInt, 
    "for cyclotomics", 
    [ IsCyc ],
    function(x)
        if DegreeOverPrimeField(Field(Union(Basis(KleinianIntegers), [x]))) > 2 then 
            return false;
        fi; 
        return ForAll(Coefficients(Basis(KleinianIntegers), x), IsInt);
    end);

InstallMethod( \in,
    "for Kleinian integers",
    IsElmsColls,
    [ IsCyc, IsKleinianIntegers ],
    function( cyc, KleinianIntegers )
        return IsKleinInt( cyc );
    end );

InstallMethod( Basis,
    "for Kleinian integers (delegate to `CanonicalBasis')",
    [ IsKleinianIntegers ], CANONICAL_BASIS_FLAGS,
    CanonicalBasis );

InstallMethod( CanonicalBasis,
    "for Kleinian integers",
    [ IsKleinianIntegers ],
    function( KleinianIntegers )
    local B;

    B:= Objectify( NewType( FamilyObj( KleinianIntegers ),
                                IsFiniteBasisDefault
                            and IsCanonicalBasis
                            and IsCanonicalBasisKleinianIntegersRep ),
                   rec() );
    SetUnderlyingLeftModule( B, KleinianIntegers );
    SetIsIntegralBasis( B, true );
    SetBasisVectors( B, Immutable( [ 1, EB(7) ] ) );
    return B;
    end );

InstallMethod( Coefficients,
    "for the canonical basis of IcosianRing",
    [ IsCanonicalBasisKleinianIntegersRep,
      IsCyc ], 0,
    function( B, v )
        return Coefficients(Basis(Field(EB(7)), BasisVectors(B)), v);
    end );


# Quaternion tools

InstallMethod( Trace, 
    "for a quaternion",
    [ IsQuaternion and IsSCAlgebraObj ],
    quat -> ExtRepOfObj(quat + ComplexConjugate(quat))[1]
    );

InstallMethod( Norm, 
    "for a quaternion",
    [ IsQuaternion and IsSCAlgebraObj ],
    quat -> ExtRepOfObj(quat*ComplexConjugate(quat))[1]
    );

BindGlobal( "QuaternionD4Basis", Basis(QuaternionAlgebra(Rationals),
    List([  [  -1/2,  -1/2,  -1/2,   1/2 ],
            [  -1/2,  -1/2,   1/2,  -1/2 ],
            [  -1/2,   1/2,  -1/2,  -1/2 ],
            [     1,     0,     0,     0 ] ], x -> ObjByExtRep(FamilyObj(One(QuaternionAlgebra(Rationals))),x)
        )) );

BindGlobal( "HurwitzIntegers", Objectify( NewType(
    CollectionsFamily(FamilyObj(QuaternionAlgebra(Rationals))),
    IsHurwitzIntegers and IsRingWithOne and IsQuaternionCollection and IsAttributeStoringRep ),
    rec() ) );

SetLeftActingDomain( HurwitzIntegers, Integers );
SetName( HurwitzIntegers, "HurwitzIntegers" );
SetString( HurwitzIntegers, "HurwitzIntegers" );
SetIsLeftActedOnByDivisionRing( HurwitzIntegers, false );
SetSize( HurwitzIntegers, infinity );
SetGeneratorsOfRing( HurwitzIntegers, AsList(QuaternionD4Basis));
SetGeneratorsOfLeftModule( HurwitzIntegers, AsList(QuaternionD4Basis) );
SetIsWholeFamily( HurwitzIntegers, false );
SetIsAssociative( HurwitzIntegers, false );

InstallMethod( Units, 
    "For Hurwitz integers", 
    [ IsHurwitzIntegers ],
    function(O)
        return Closure(Basis(O), \*);
    end);

InstallMethod( IsHurwitzInt, 
    "for Quaternions", 
    [ IsQuaternion ],
    function(x) 
        return ForAll(Coefficients(Basis(HurwitzIntegers), x), IsInt);
    end);

InstallMethod( \in,
    "for integers",
    [ IsQuaternion, IsHurwitzIntegers ], 10000,
    function( n, Integers )
    return IsHurwitzInt( n );
    end );

InstallMethod( Basis,
    "for Hurwitz integers (delegate to `CanonicalBasis')",
    [ IsHurwitzIntegers ], CANONICAL_BASIS_FLAGS,
    CanonicalBasis );


InstallMethod( CanonicalBasis,
    "for Hurwitz integers",
    [ IsHurwitzIntegers ],
    function( HurwitzIntegers )
    local B;
    B:= Objectify( NewType( FamilyObj( HurwitzIntegers ),
                                IsFiniteBasisDefault
                            and IsCanonicalBasis
                            and IsQuaternionCollection
                            and IsCanonicalBasisHurwitzIntegersRep ),
                   rec() );
    SetUnderlyingLeftModule( B, HurwitzIntegers );
    SetIsIntegralBasis( B, true );
    SetBasisVectors( B, Immutable( BasisVectors(QuaternionD4Basis)));
    # Return the basis.
    return B;
    end );

InstallMethod( Coefficients,
    "for the canonical basis of HurwitzIntegers",
    [ IsCanonicalBasisHurwitzIntegersRep,
      IsQuaternion ], 0,
    function( B, v )
        return SolutionMat(List(B, ExtRepOfObj), ExtRepOfObj(v));
    end );

# Icosian and Golden Field Tools

InstallGlobalFunction( GoldenModSigma, function(q)
    # Check that q belongs to the quadratic field containing Sqrt(5).
    if not q in NF(5,[1,4]) then return fail; fi;
    # Compute the coefficients in the basis [1,(1-Sqrt(5))/2] and return the 1 coefficient.
    return Coefficients(Basis(NF(5,[1,4]), [1, (1-Sqrt(5))/2]), q)[1];
end );

BindGlobal( "IcosianH4Generators", Basis(QuaternionAlgebra(Field(Sqrt(5))),
    List([  [ 0, -1, 0, 0 ], 
            [ 0, -1/2*E(5)^2-1/2*E(5)^3, 1/2, -1/2*E(5)-1/2*E(5)^4 ],
            [ 0, 0, -1, 0 ], 
            [ -1/2*E(5)-1/2*E(5)^4, 0, 1/2, -1/2*E(5)^2-1/2*E(5)^3 ] ], 
        x -> ObjByExtRep(FamilyObj(One(QuaternionAlgebra(Field(Sqrt(5))))),x)
        )) );


BindGlobal( "IcosianRing", Objectify( NewType(
    CollectionsFamily(FamilyObj(QuaternionAlgebra(Rationals))),
    IsIcosianRing and IsRingWithOne and IsQuaternionCollection and IsAttributeStoringRep ),
    rec() ) );

SetLeftActingDomain( IcosianRing, Integers );
SetName( IcosianRing, "IcosianRing" );
SetString( IcosianRing, "IcosianRing" );
SetIsLeftActedOnByDivisionRing( IcosianRing, false );
SetSize( IcosianRing, infinity );
SetGeneratorsOfRing( IcosianRing, AsList(IcosianH4Generators));
SetGeneratorsOfLeftModule( IcosianRing, AsList(IcosianH4Generators) );
SetIsWholeFamily( IcosianRing, false );
SetIsAssociative( IcosianRing, false );

InstallMethod( Units, 
    "For Icosians", 
    [ IsIcosianRing ],
    function(O)
        return Closure(Basis(O), \*);
    end);

InstallMethod( IsIcosian, 
    "for Quaternions", 
    [ IsQuaternion ],
    function(x) 
        return ForAll(Coefficients(Basis(IcosianRing), x), y -> 
                    ForAll(Coefficients(Basis(NF(5,[1,4]), [1, (1-Sqrt(5))/2]), y), IsInt)
            );
    end);

InstallMethod( \in,
    "for integers",
    [ IsQuaternion, IsIcosianRing ], 10000,
    function( n, Integers )
    return IsIcosian( n );
    end );

InstallMethod( Basis,
    "for Icosians (delegate to `CanonicalBasis')",
    [ IsIcosianRing ], CANONICAL_BASIS_FLAGS,
    CanonicalBasis );


InstallMethod( CanonicalBasis,
    "for Icosians",
    [ IsIcosianRing ],
    function( IcosianRing )
    local B;
    B:= Objectify( NewType( FamilyObj( IcosianRing ),
                                IsFiniteBasisDefault
                            and IsCanonicalBasis
                            and IsQuaternionCollection
                            and IsCanonicalBasisIcosianRingRep ),
                   rec() );
    SetUnderlyingLeftModule( B, IcosianRing );
    SetIsIntegralBasis( B, true );
    SetBasisVectors( B, Immutable( BasisVectors(IcosianH4Generators)));
    # Return the basis.
    return B;
    end );

InstallMethod( Coefficients,
    "for the canonical basis of IcosianRing",
    [ IsCanonicalBasisIcosianRingRep,
      IsQuaternion ], 0,
    function( B, v )
        return SolutionMat(List(B, ExtRepOfObj), ExtRepOfObj(v));
    end );

# Function to construct an octonion algebra in a standard basis (i.e. e[1]*e[2] = e[4], and cycle indices). 
InstallGlobalFunction( OctonionAlgebra, function( F )
    local e, stored, filter, T, A;
    # Arguments checking
    if not IsField(F) then 
        Error( "usage: OctonionAlgebra( <F> ) for a field <F>." );
    fi;
    e:= One( F );
    if e = fail then
      Error( "<F> must have an identity element" );
    fi;
    # Generators in the right family may be already available.
    stored := GET_FROM_SORTED_CACHE( OctonionAlgebraData, [ Characteristic(F), FamilyObj( F ) ],
        function()
            # Construct a filter describing element properties,
            # which will be stored in the family.
            filter:= IsSCAlgebraObj and IsOctonion;
            # if HasIsAssociative( F ) and IsAssociative( F ) then
            #     filter:= filter and IsAssociativeElement;
            # fi;
            T := [ [ [ [ 8 ], [ -1 ] ], [ [ 4 ], [ 1 ] ], [ [ 7 ], [ 1 ] ], [ [ 2 ], [ -1 ] ], [ [ 6 ], [ 1 ] ], 
                    [ [ 5 ], [ -1 ] ], [ [ 3 ], [ -1 ] ], [ [ 1 ], [ 1 ] ] ], 
                [ [ [ 4 ], [ -1 ] ], [ [ 8 ], [ -1 ] ], [ [ 5 ], [ 1 ] ], [ [ 1 ], [ 1 ] ], [ [ 3 ], [ -1 ] ], 
                    [ [ 7 ], [ 1 ] ], [ [ 6 ], [ -1 ] ], [ [ 2 ], [ 1 ] ] ], 
                [ [ [ 7 ], [ -1 ] ], [ [ 5 ], [ -1 ] ], [ [ 8 ], [ -1 ] ], [ [ 6 ], [ 1 ] ], [ [ 2 ], [ 1 ] ], 
                    [ [ 4 ], [ -1 ] ], [ [ 1 ], [ 1 ] ], [ [ 3 ], [ 1 ] ] ], 
                [ [ [ 2 ], [ 1 ] ], [ [ 1 ], [ -1 ] ], [ [ 6 ], [ -1 ] ], [ [ 8 ], [ -1 ] ], [ [ 7 ], [ 1 ] ], 
                    [ [ 3 ], [ 1 ] ], [ [ 5 ], [ -1 ] ], [ [ 4 ], [ 1 ] ] ], 
                [ [ [ 6 ], [ -1 ] ], [ [ 3 ], [ 1 ] ], [ [ 2 ], [ -1 ] ], [ [ 7 ], [ -1 ] ], [ [ 8 ], [ -1 ] ], 
                    [ [ 1 ], [ 1 ] ], [ [ 4 ], [ 1 ] ], [ [ 5 ], [ 1 ] ] ], 
                [ [ [ 5 ], [ 1 ] ], [ [ 7 ], [ -1 ] ], [ [ 4 ], [ 1 ] ], [ [ 3 ], [ -1 ] ], [ [ 1 ], [ -1 ] ], 
                    [ [ 8 ], [ -1 ] ], [ [ 2 ], [ 1 ] ], [ [ 6 ], [ 1 ] ] ], 
                [ [ [ 3 ], [ 1 ] ], [ [ 6 ], [ 1 ] ], [ [ 1 ], [ -1 ] ], [ [ 5 ], [ 1 ] ], [ [ 4 ], [ -1 ] ], 
                    [ [ 2 ], [ -1 ] ], [ [ 8 ], [ -1 ] ], [ [ 7 ], [ 1 ] ] ], 
                [ [ [ 1 ], [ 1 ] ], [ [ 2 ], [ 1 ] ], [ [ 3 ], [ 1 ] ], [ [ 4 ], [ 1 ] ], [ [ 5 ], [ 1 ] ], 
                    [ [ 6 ], [ 1 ] ], [ [ 7 ], [ 1 ] ], [ [ 8 ], [ 1 ] ] ], 0, Zero(F) ];
            # Construct the algebra.
            A:= AlgebraByStructureConstantsArg([ F, T, "e" ], filter );
            SetFilterObj( A, IsAlgebraWithOne );
            SetFilterObj( A, IsOctonionAlgebra );
            return A;
        end );
        A:= AlgebraWithOne( F, CanonicalBasis( stored ), "basis" );
        SetGeneratorsOfAlgebra( A, GeneratorsOfAlgebraWithOne( A ) );
        SetIsFullSCAlgebra( A, true );
        SetFilterObj( A, IsOctonionAlgebra );
    # Return the octonion algebra.
    return A;
    end );

InstallMethod( Trace,
    "for an octonion",
    [ IsOctonion and IsSCAlgebraObj ],
    oct -> 2*ExtRepOfObj(oct)[8] 
    );

InstallMethod( Norm,
    "for an octonion",
    [ IsOctonion and IsSCAlgebraObj ],
    oct -> ExtRepOfObj(oct)*ExtRepOfObj(oct) 
    );

InstallMethod( Norm,
    "for an octonion list",
    [ IsOctonionCollection ],
    function(vec)
        return Sum(List(vec, Norm) );
    end );

InstallMethod( ComplexConjugate,
    "for an octonion",
    [ IsOctonion and IsSCAlgebraObj ],
    oct -> One(oct)*Trace(oct) - oct
    );  

InstallMethod( RealPart,
    "for an octonion",
    [ IsOctonion and IsSCAlgebraObj ],
    oct -> (1/2)*Trace(oct)*One(oct)
    );

# Avoiding use of ImaginaryPart for octonions since the built in GAP quaternion version of this command is easily misunderstood. 

# InstallMethod( ImaginaryPart,
#     "for an octonion",
#     [ IsOctonion and IsSCAlgebraObj ],
#     oct -> oct - RealPart(oct)
#     );

# Octonion arithmetic tools

BindGlobal( "OctonionE8Basis", Basis(OctonionAlgebra(Rationals),
    List(
        [[ -1/2, 0, 0, 0, 1/2, 1/2, 1/2, 0 ], 
    [ -1/2, -1/2, 0, -1/2, 0, 0, -1/2, 0 ], 
    [ 0, 1/2, 1/2, 0, -1/2, 0, -1/2, 0 ], 
    [ 1/2, 0, -1/2, 1/2, 1/2, 0, 0, 0 ],
    [ 0, -1/2, 1/2, 0, -1/2, 0, 1/2, 0 ], 
    [ 0, 1/2, 0, -1/2, 1/2, -1/2, 0, 0 ], 
    [ -1/2, 0, -1/2, 1/2, -1/2, 0, 0, 0 ], 
    [ 1/2, 0, 0, -1/2, 0, 1/2, 0, -1/2 ] ], 
        x -> ObjByExtRep(FamilyObj(One(OctonionAlgebra(Rationals))),x)
        )) );       

BindGlobal( "OctavianIntegers", Objectify( NewType(
    CollectionsFamily(FamilyObj(OctonionAlgebra(Rationals))),
    IsOctavianIntegers and IsRingWithOne and IsOctonionCollection and IsAttributeStoringRep ),
    rec() ) );

SetLeftActingDomain( OctavianIntegers, Integers );
SetName( OctavianIntegers, "OctavianIntegers" );
SetString( OctavianIntegers, "OctavianIntegers" );
SetIsLeftActedOnByDivisionRing( OctavianIntegers, false );
SetSize( OctavianIntegers, infinity );
SetGeneratorsOfRing( OctavianIntegers, AsList(OctonionE8Basis));
SetGeneratorsOfLeftModule( OctavianIntegers, AsList(OctonionE8Basis) );
SetIsWholeFamily( OctavianIntegers, false );
SetIsAssociative( OctavianIntegers, false );

InstallMethod( Units, 
    "For octavian integers", 
    [ IsOctavianIntegers ],
    function(O)
        return Closure(Basis(O), \*);
    end);

InstallMethod( IsOctavianInt, 
    "for Octonions", 
    [ IsOctonion ],
    function(x) 
        return ForAll(Coefficients(Basis(OctavianIntegers), x), IsInt);
    end);

InstallMethod( \in,
    "for integers",
    [ IsOctonion, IsOctavianIntegers ], 10000,
    function( n, Integers )
    return IsOctavianInt( n );
    end );

InstallMethod( Basis,
    "for Octavian integers (delegate to `CanonicalBasis')",
    [ IsOctavianIntegers ], CANONICAL_BASIS_FLAGS,
    CanonicalBasis );


InstallMethod( CanonicalBasis,
    "for Octavian integers",
    [ IsOctavianIntegers ],
    function( OctavianIntegers )
    local B;
    B:= Objectify( NewType( FamilyObj( OctavianIntegers ),
                                IsFiniteBasisDefault
                            and IsCanonicalBasis
                            and IsOctonionCollection
                            and IsCanonicalBasisOctavianIntegersRep ),
                   rec() );
    SetUnderlyingLeftModule( B, OctavianIntegers );
    SetIsIntegralBasis( B, true );
    SetBasisVectors( B, Immutable( BasisVectors(OctonionE8Basis)));
    # Return the basis.
    return B;
    end );

InstallMethod( Coefficients,
    "for the canonical basis of OctavianIntegers",
    [ IsCanonicalBasisOctavianIntegersRep,
      IsOctonion ], 0,
    function( B, v )
        return SolutionMat(List(B, ExtRepOfObj), ExtRepOfObj(v));
    end );

InstallMethod( \mod, 
    "For an octonion integer", 
    [IsOctonion, IsPosInt], 0,
    function(a,m)
        local coeffs;
        coeffs := Coefficients(Basis(OctavianIntegers), a); 
        if not ForAll(coeffs, IsInt) then 
            return fail;
        fi; 
        return LinearCombination(Basis(OctavianIntegers),  coeffs mod m);
    end );

# Potentially replace the function below with a method.

# InstallMethod( OctonionToRealVector, 
#     "For an octonion basis and vector",
#     [ IsBasis, IsRowVector ], 0,
#     function(basis, x)
#         if IsHomogeneousList(Flat(AsList(Basis), x)) and 
#             IsOctonionCollection(x) 
#         then 
#             return Flat(List(x, y -> Coefficients(basis, y)) );
#         fi;
#         return fail;
#     end );

InstallGlobalFunction( OctonionToRealVector,
    function(arg, x) 
    # In the case of an octonion basis return the concatenated octonion basis expansion.
    if IsBasis(arg) and IsOctonionCollection(UnderlyingLeftModule(arg)) and IsOctonionCollection(x) then 
        return Concatenation(List(x, y -> Coefficients(arg, y)) );
    fi;
    return fail;
    end );

InstallMethod( Coefficients, 
    "For an octonion lattice basis and an octonion vector",
    [ IsOctonionLatticeBasis, IsOctonionCollection ], 0,
    function(basis, x)
        local L;
        L := UnderlyingLeftModule(basis);
        if x in L then 
            # return OctonionToRealVector(UnderlyingLeftModule(basis), x);
            return SolutionMat(LLLReducedBasisCoefficients(L),
            OctonionToRealVector((UnderlyingOctonionRingBasis(L)), x));
        fi;
        return fail;
    end );

InstallGlobalFunction( RealToOctonionVector,
    function(arg, x)
        local n, temp;
        # In the case of an octonion basis convert each length of 8 into an octonion,
        # Check length of coefficient vector.
        if IsBasis(arg) and IsOctonionCollection(UnderlyingLeftModule(arg)) then
            if Length(x) mod 8 = 0 and IsHomogeneousList(x) then 
                n := Length(x)/8;
                temp := List([1..n], m -> x{[(m-1)*8+1 .. m*8]} );;
                return List(temp, y -> LinearCombination(arg, y) );
            fi;
        fi;
        return fail;
    end );

InstallGlobalFunction( VectorToIdempotentMatrix, 
    function(x)
        local temp;
        if not IsHomogeneousList(x) or not IsAssociative(x) or not (IsCyc(x[1]) or IsQuaternion(x[1]) or IsOctonion(x[1])) then 
            return fail;
        fi;
        if IsAssociative(x) then 
            temp := TransposedMat([ComplexConjugate(x)])*[x];
            return temp/Trace(temp );
        fi; 
        return fail;
    end );

InstallGlobalFunction( WeylReflection, 
    function(r,x)
        local R;
        R := VectorToIdempotentMatrix(r );
        if R = fail or not IsHomogeneousList(Flat([r,x])) then 
            return fail; 
        fi;
        return x - 2*x*R;
    end );


# Jordan Algebra Tools

InstallMethod( Rank, 
    "for a Jordan Algebra",
    [ IsJordanAlgebra ],
    J -> JordanRank(J)
    );

InstallMethod( JordanRank, 
    "for a Jordan algebra element",
    [ IsJordanAlgebraObj ],
    j -> JordanRank(FamilyObj(j)!.fullSCAlgebra)
    );

InstallMethod( Rank, 
    "for a Jordan algebra element",
    [ IsJordanAlgebraObj ],
    j -> JordanRank(j)
    );

InstallMethod( JordanDegree, 
    "for a Jordan algebra element",
    [ IsJordanAlgebraObj ],
    j -> JordanDegree(FamilyObj(j)!.fullSCAlgebra)
    );

InstallMethod( Degree, 
    "for a Jordan Algebra",
    [ IsJordanAlgebra ],
    J -> JordanDegree(J)
    );

InstallMethod( Degree, 
    "for a Jordan algebra element",
    [ IsJordanAlgebraObj ],
    j -> JordanDegree(j)
    );

InstallMethod( Trace,
    "for a Jordan algebra element",
    [ IsJordanAlgebraObj and IsSCAlgebraObj ],
    # j -> (Rank(j)/Dimension(FamilyObj(j)!.fullSCAlgebra))*Trace(AdjointMatrix(Basis(FamilyObj(j)!.fullSCAlgebra), j))
    j -> ExtRepOfObj(j)*JordanBasisTraces(FamilyObj(j)!.fullSCAlgebra) 
    );

InstallMethod( Norm,
    "for a Jordan algebra element",
    [ IsJordanAlgebraObj and IsSCAlgebraObj ],
    j -> Trace(j^2)/2
    );

InstallGlobalFunction( GenericMinimalPolynomial, 
    function(x)
        local p, prx, p1xr, r, j, qjx;
        p := [-Trace(x)];
        p1xr := [-Trace(x)];
        r := 1;
        repeat 
            r := r + 1;
            Append(p1xr, [-Trace(x^r)] ); 
            prx := (1/r)*(p1xr[r] + Sum(List([1..r-1], j -> 
                p1xr[r-j]*p[j]
            )) );
            Append(p, [prx] );
        until r = Rank(x );
        p := Reversed(p );
        Append(p, [1] );
        return p;
    end );

InstallMethod( Determinant,
    "for a Jordan algebra element",
    [ IsJordanAlgebraObj and IsSCAlgebraObj ],
    j -> ValuePol(GenericMinimalPolynomial(j), 0)*(-1)^Rank(j) 
    );

InstallMethod( JordanAdjugate, 
    "for a Jordan algebra element",
    [ IsJordanAlgebraObj ],
    function(j) return (-1)^(1+Rank(j))*ValuePol(ShiftedCoeffs(GenericMinimalPolynomial(j), -1), j ); end
    );

InstallMethod( IsPositiveDefinite, 
    "for a Jordan algebra element",
    [ IsJordanAlgebraObj ],
    function(j) local temp; 
        temp := GenericMinimalPolynomial(j ); 
        if 0 in temp then return false; fi;
        temp := Reversed(temp );
        temp := List([0..Rank(j)], n -> temp[n+1]*(-1)^n > 0 );
        if Set(temp) = [true] then return true; fi;
        return false;
    end );

# Function to construct basis matrices for a Hermitian simple Euclidean Jordan algebra.
InstallGlobalFunction( HermitianJordanAlgebraBasis, function(rho, comp_alg_basis)
    local d, C, F, peirce, conj, mat, frame, realbasis;
    # Ensure that the rank and degree are correct.
    if not (IsInt(rho) and rho > 1 and IsBasis(comp_alg_basis)) then 
        return fail; 
    fi;
    d := Length(comp_alg_basis);
    if (not d in [1,2,4,8]) or (d = 8 and rho > 3) then 
        return fail; 
    fi;
    # Record the composition algebra over F.
    C := UnderlyingLeftModule(comp_alg_basis);
    F := LeftActingDomain(C);
    # Require that F is either integers or a field of characteristic zero.
    if not (IsIntegers(F) or (IsField(F) and Characteristic(F) = 0)) then 
        return fail;
    fi;
    # It is possible that the d = 1 or 2 cases do not involve quaternions or octonion SCAlgebra objects. 
    if not (IsOctonionCollection(C) or IsQuaternionCollection(C)) then 
        # Only real and complex cases remain, which must be quadratic extensions of some number field. 
        if d > 2 then 
            return fail; 
        fi;
        # Rule out subfields of the rationals for d = 2:
        if d = 2 and Set(comp_alg_basis, x -> RealPart(x) = x ) = [true]
            then return fail;
        fi;
    fi;
    # Define a function to construct a single entry Hermitian matrix.
    mat := function(n,x)
        local temp; 
        if Length(n) <> 2 then return fail; fi;
        temp := Zero(x)*IdentityMat( rho );
        temp[n[1]][n[2]] := x;
        temp[n[2]][n[1]] := ComplexConjugate( x );
        return temp;
    end;
    # Construct the diagonal matrices. 
    frame := Concatenation(List(IdentityMat(rho), x -> List([One(C)], r -> DiagonalMat(x)*r)) );
    # Construct the off-diagonal matrices.
    peirce := List(Combinations([1..rho],2), n -> List(comp_alg_basis, x -> mat(n,x)) );
    # Return the matrices. 
    return Concatenation(frame, Concatenation(peirce) );
end );

# Function to convert a Hermitian matrix to a vector, or coefficients of a vector, in a Jordan algebra. 
InstallGlobalFunction( HermitianMatrixToJordanCoefficients, function(mat, comp_alg_basis)
    local temp, rho, d, i, basis;
    # Verify that the input is a Hermitian matrix.
    if not IsMatrix(mat) and mat = TransposedMat(ComplexConjugate(mat)) then return fail; fi;
    # Ensure that the second input is a basis. 
    if not IsBasis(comp_alg_basis) then return fail; fi;
    # Record basic parameters. 
    basis := comp_alg_basis;
    rho := Length(DiagonalOfMat(mat) );
    d := Size(basis); 
    # Define a temporary list of coefficients.
    temp := []; 
    # Determine the coefficients due to the diagonal components of the matrix.
    for i in [1..rho] do 
        if IsQuaternionCollection(comp_alg_basis) or IsOctonionCollection(comp_alg_basis) then  
            Append(temp, [Trace(mat[i][i])/2] );
        elif IsCyclotomicCollection(comp_alg_basis) then 
            Append(temp, [RealPart(mat[i][i])]);
        else
            Display("Here"); 
            return fail;
        fi;
    od;
    # Find the off-diagonal coefficients next.
    for i in Combinations([1..rho],2) do
        # if not (IsQuaternionCollection(comp_alg_basis) or IsOctonionCollection(comp_alg_basis) ) and LeftActingDomain(UnderlyingLeftModule(comp_alg_basis)) = Integers then     
        #     Append(temp, Coefficients(Basis(Rationals,[1]), mat[i[1]][i[2]]) );
        # else 
        #     Append(temp, Coefficients(basis, mat[i[1]][i[2]]) );
        # fi;
        Append(temp, Coefficients(basis, mat[i[1]][i[2]]) );
    od;
    # Return the coefficients.
    return temp;
end );

# Function to convert a Hermitian matrix into a Jordan algebra vector. 
InstallGlobalFunction( HermitianMatrixToJordanVector, function(mat, J)
    local temp;
    # Verify that the second argument is a Jordan algebra with an off-diagonal basis defined. 
    if not (IsJordanAlgebra(J) and HasJordanOffDiagonalBasis(J)) then 
        return fail; 
    fi;
    # Verify that the matrix entries belong to the algebra spanned by the off-diagonal basis. 
    if not IsHomogeneousList(Flat([mat, JordanOffDiagonalBasis(J)])) then return fail; fi;
    # Compute the coefficients, if possible.
    temp := HermitianMatrixToJordanCoefficients(mat, JordanOffDiagonalBasis(J) );
    if temp = fail then return temp; fi;
    # Return the coefficients in J-vector form.
    return LinearCombination(Basis(J), temp );
end );

# Function to construct Jordan algebra of Hermitian type.
InstallGlobalFunction( HermitianSimpleJordanAlgebra, function(rho, comp_alg_basis, F...)
    local jordan_basis, C, K, T, temp, coeffs, algebra, filter, n, m, z, l;
    # Ensure inputs are correct by computing basis vectors:
    if Length(F) > 1 then 
        return fail; 
    fi;
    jordan_basis := HermitianJordanAlgebraBasis(rho, comp_alg_basis );
    if jordan_basis = fail then 
        return jordan_basis; 
    fi;
    # Record the composition algebra over F.
    C := UnderlyingLeftModule(comp_alg_basis);
    K := LeftActingDomain(C);
    if Length(F) = 0 and IsSubset(Rationals, K) then 
        K := Rationals;
    fi;
    # Ensure that the optional field argument contains the left acting domain of the basis. 
    if Length(F) = 1 then
        F := F[1]; 
        if not (IsField(F) or IsIntegers(F)) then 
            return fail;  
        elif IsField(F) and not IsSubset(F, K) then 
            return fail;
        fi;
        K := F;
    fi;
    # Define an empty structure constants table.
    T := EmptySCTable(Size(jordan_basis), Zero(K) );
    # Compute the structure constants.
    for n in [1..Size(jordan_basis)] do 
        for m in [1..Size(jordan_basis)] do 
            z := (1/2)*(jordan_basis[n]*jordan_basis[m] + jordan_basis[m]*jordan_basis[n] );
            # z := (jordan_basis[n]*jordan_basis[m] + jordan_basis[m]*jordan_basis[n] );
            temp := HermitianMatrixToJordanCoefficients(z, comp_alg_basis );
            coeffs := [];
            for l in [1..Size(jordan_basis)] do 
                if temp[l] <> 0 then 
                    Append(coeffs, [temp[l], l] );
                fi;
            od;
            SetEntrySCTable( T, n, m, coeffs );
        od;
    od;
    # Construct the algebra.
    filter:= IsSCAlgebraObj and IsJordanAlgebraObj;
    algebra := AlgebraByStructureConstantsArg([K, T], filter );
    SetFilterObj( algebra, IsJordanAlgebra );
    SetFilterObj( algebra, IsAlgebraWithOne);
    # Assign various attributes to the algebra.
    SetJordanRank( algebra, rho );
    SetJordanDegree( algebra, Length(comp_alg_basis) );
    SetJordanMatrixBasis( algebra, jordan_basis );
    SetJordanOffDiagonalBasis( algebra, comp_alg_basis );
    SetJordanHomotopeVector( algebra, One(algebra) );
    SetJordanBasisTraces( algebra, List(Basis(algebra), 
        j -> (Rank(j)/Dimension(FamilyObj(j)!.fullSCAlgebra))*Trace(AdjointMatrix(Basis(FamilyObj(j)!.fullSCAlgebra), j)))
        );
    return algebra;
end );

InstallGlobalFunction( JordanSpinFactor,  function(gram_mat)
    local result, T, n, m, z, temp, coeffs, filter;
    if not IsMatrix(gram_mat) or Inverse(gram_mat) = fail or gram_mat <> TransposedMat(gram_mat) then 
        Display("Usage: JordanSpinFactor(G) requires <G> to be a positive definite symmetric matrix.");
        return fail; 
    fi;
    result := rec( );
    result.F := Field(Flat(gram_mat) );
    result.rho := 2;
    result.d := DimensionsMat(gram_mat)[1]-1;
    # Construct the algebra.
    T := EmptySCTable(result.d + 2, Zero(0) );
    SetEntrySCTable(T, 1, 1, [1, 1] );
    for m in [2..result.d + 2] do 
        SetEntrySCTable(T, m, 1, [1, m] );
        SetEntrySCTable(T, 1, m, [1, m] );
    od;
    for n in [2..result.d + 2] do 
        for m in [2..result.d + 2] do
            SetEntrySCTable( T, n, m, [gram_mat[n-1][m-1], 1] );
        od;
    od;
    filter:= IsSCAlgebraObj and IsJordanAlgebraObj;
    result.algebra := AlgebraByStructureConstantsArg([result.F, T], filter );
    SetFilterObj( result.algebra, IsJordanAlgebra );
    SetFilterObj( result.algebra, IsAlgebraWithOne);
    SetJordanRank( result.algebra, result.rho );
    SetJordanDegree( result.algebra, result.d );
    SetJordanHomotopeVector( result.algebra, One(result.algebra) );
    SetJordanBasisTraces( result.algebra, List(Basis(result.algebra), 
        j -> (Rank(j)/Dimension(FamilyObj(j)!.fullSCAlgebra))*Trace(AdjointMatrix(Basis(FamilyObj(j)!.fullSCAlgebra), j)))
        );
    return result.algebra;
end );

InstallMethod( JordanAlgebraGramMatrix, 
    "for a Jordan algebra",
    [ IsJordanAlgebra ],
    j -> List(Basis(j), x -> List(Basis(j), y -> Trace(x*y)))
    );

InstallGlobalFunction( JordanHomotope , function(ring, u, label...)
    local result, temp, filter, T, n, m, z, l, coeffs;
    if not IsJordanAlgebra(ring) then return fail; fi;
    result := rec( );
    result.rho := Rank(ring );
    result.d := Degree(ring );
    result.F := LeftActingDomain(ring );
    T := EmptySCTable(Dimension(ring), Zero(result.F) );
    for n in Basis(ring) do 
        for m in Basis(ring) do 
            z := n*(u*m) + (n*u)*m - u*(n*m );
            temp := Coefficients(Basis(ring), z );
            coeffs := [];
            for l in [1..Dimension(ring)] do 
                if temp[l] <> Zero(temp[l]) then 
                    Append(coeffs, [temp[l], l] );
                fi;
            od;
            SetEntrySCTable( T, Position(Basis(ring), n), Position(Basis(ring), m), coeffs );
        od;
    od;
    filter:= IsSCAlgebraObj and IsJordanAlgebraObj;
    if Length(label) > 0 and IsString(label[1]) then 
        result.algebra := AlgebraByStructureConstantsArg([result.F, T, label[1]], filter );
    else 
        result.algebra := AlgebraByStructureConstantsArg([result.F, T], filter );
    fi;
    SetFilterObj( result.algebra, IsJordanAlgebra );
    if Inverse(u) <> fail then 
        SetFilterObj( result.algebra, IsAlgebraWithOne);
    fi;
    SetJordanRank( result.algebra, result.rho );
    SetJordanDegree( result.algebra, result.d );
    if HasJordanMatrixBasis( result.algebra) then 
        SetJordanMatrixBasis( result.algebra, JordanMatrixBasis(ring) );
    fi;
    if HasJordanOffDiagonalBasis(result.algebra) then 
        SetJordanOffDiagonalBasis( result.algebra, JordanOffDiagonalBasis(ring) );
    fi;
    SetJordanHomotopeVector( result.algebra, u );
    SetJordanBasisTraces( result.algebra, List(Basis(result.algebra), 
        j -> (Rank(j)/Dimension(FamilyObj(j)!.fullSCAlgebra))*Trace(AdjointMatrix(Basis(FamilyObj(j)!.fullSCAlgebra), j)))
        );
    return result.algebra;
end );

InstallGlobalFunction( SimpleEuclideanJordanAlgebra, function(rho, d, args...)
    local temp, F;
    temp := rec( );
    if not (IsInt(d) and IsInt(rho)) then return fail; fi;
    if rho < 2 then return fail; fi; 
    if rho > 2 and not d in [1,2,4,8] then return fail; fi;
    if d = 8 and rho > 3 then return fail; fi;
    if rho = 2 then 
        if Length(args) = 0 then 
            return JordanSpinFactor(IdentityMat(d+1) );
            elif IsMatrix(args[1]) and DimensionsMat(args[1]) = [d+1, d+1] and TransposedMat(args[1]) = args[1] and Inverse(args[1]) <> fail then 
                return JordanSpinFactor(args[1] );
        elif d in [1,2,4,8] and IsBasis(args[1]) and Size(args[1]) = d then 
            return HermitianSimpleJordanAlgebra(rho, args[1] );
        else
            Display("Usage: SimpleEuclideanJordanAlgebra(2, d [, args]) where <args> is either empty, a symmetric invertible matrix, or when <d> = 1,2,4,8 <args> can also be a basis for a composition algebra."); 
            return fail;
        fi;
    fi;

    if Length(args) = 0 then
        if d = 8 then 
            return HermitianSimpleJordanAlgebra(rho, Basis(OctonionAlgebra(Rationals)) );
        elif d = 4 then 
            return HermitianSimpleJordanAlgebra(rho, Basis(QuaternionAlgebra(Rationals)) );
        elif d = 2 then 
            return HermitianSimpleJordanAlgebra(rho, Basis(CF(4), [1, E(4)]) );
        elif d = 1 then 
            return HermitianSimpleJordanAlgebra(rho, Basis(Rationals, [1]) );
        fi;
    elif IsBasis(args[1]) and Size(args[1]) = d then 
        return HermitianSimpleJordanAlgebra(rho, args[1] );
    else 
        return fail;
    fi;
end );

# Albert Algebra tools

InstallGlobalFunction( AlbertAlgebra, function( F )
    local e, i, j, k, jordan_basis, stored, filter, T, A;
    # Arguments checking
    if not IsField(F) then 
        Error( "usage: AlbertAlgebra( <F> ) for a field <F>." );
    fi;
    e:= One( F );
    if e = fail then
      Error( "<F> must have an identity element" );
    fi;
    # Generators in the right family may be already available.
    stored := GET_FROM_SORTED_CACHE( AlbertAlgebraData, [ Characteristic(F), FamilyObj( F ) ],
        function()
            filter:= IsSCAlgebraObj and IsJordanAlgebraObj and IsAlbertAlgebraObj;
            T := [ [ [ [ 26, 27 ], [ 1, 1 ] ], [ [  ], [  ] ], [ [  ], [  ] ], [ [  ], [  ] ], [ [  ], [  ] ], 
      [ [  ], [  ] ], [ [  ], [  ] ], [ [  ], [  ] ], [ [ 24 ], [ -1/2 ] ], [ [ 20 ], [ -1/2 ] ], 
      [ [ 23 ], [ -1/2 ] ], [ [ 18 ], [ 1/2 ] ], [ [ 22 ], [ -1/2 ] ], [ [ 21 ], [ 1/2 ] ], 
      [ [ 19 ], [ 1/2 ] ], [ [ 17 ], [ -1/2 ] ], [ [ 16 ], [ -1/2 ] ], [ [ 12 ], [ 1/2 ] ], 
      [ [ 15 ], [ 1/2 ] ], [ [ 10 ], [ -1/2 ] ], [ [ 14 ], [ 1/2 ] ], [ [ 13 ], [ -1/2 ] ], 
      [ [ 11 ], [ -1/2 ] ], [ [ 9 ], [ -1/2 ] ], [ [  ], [  ] ], [ [ 1 ], [ 1/2 ] ], 
      [ [ 1 ], [ 1/2 ] ] ], 
  [ [ [  ], [  ] ], [ [ 26, 27 ], [ 1, 1 ] ], [ [  ], [  ] ], [ [  ], [  ] ], [ [  ], [  ] ], 
      [ [  ], [  ] ], [ [  ], [  ] ], [ [  ], [  ] ], [ [ 20 ], [ 1/2 ] ], [ [ 24 ], [ -1/2 ] ], 
      [ [ 21 ], [ -1/2 ] ], [ [ 17 ], [ -1/2 ] ], [ [ 19 ], [ 1/2 ] ], [ [ 23 ], [ -1/2 ] ], 
      [ [ 22 ], [ 1/2 ] ], [ [ 18 ], [ -1/2 ] ], [ [ 12 ], [ -1/2 ] ], [ [ 16 ], [ -1/2 ] ], 
      [ [ 13 ], [ 1/2 ] ], [ [ 9 ], [ 1/2 ] ], [ [ 11 ], [ -1/2 ] ], [ [ 15 ], [ 1/2 ] ], 
      [ [ 14 ], [ -1/2 ] ], [ [ 10 ], [ -1/2 ] ], [ [  ], [  ] ], [ [ 2 ], [ 1/2 ] ], 
      [ [ 2 ], [ 1/2 ] ] ], 
  [ [ [  ], [  ] ], [ [  ], [  ] ], [ [ 26, 27 ], [ 1, 1 ] ], [ [  ], [  ] ], [ [  ], [  ] ], 
      [ [  ], [  ] ], [ [  ], [  ] ], [ [  ], [  ] ], [ [ 23 ], [ 1/2 ] ], [ [ 21 ], [ 1/2 ] ], 
      [ [ 24 ], [ -1/2 ] ], [ [ 22 ], [ -1/2 ] ], [ [ 18 ], [ -1/2 ] ], [ [ 20 ], [ 1/2 ] ], 
      [ [ 17 ], [ -1/2 ] ], [ [ 19 ], [ -1/2 ] ], [ [ 15 ], [ -1/2 ] ], [ [ 13 ], [ -1/2 ] ], 
      [ [ 16 ], [ -1/2 ] ], [ [ 14 ], [ 1/2 ] ], [ [ 10 ], [ 1/2 ] ], [ [ 12 ], [ -1/2 ] ], 
      [ [ 9 ], [ 1/2 ] ], [ [ 11 ], [ -1/2 ] ], [ [  ], [  ] ], [ [ 3 ], [ 1/2 ] ], 
      [ [ 3 ], [ 1/2 ] ] ], 
  [ [ [  ], [  ] ], [ [  ], [  ] ], [ [  ], [  ] ], [ [ 26, 27 ], [ 1, 1 ] ], [ [  ], [  ] ], 
      [ [  ], [  ] ], [ [  ], [  ] ], [ [  ], [  ] ], [ [ 18 ], [ -1/2 ] ], [ [ 17 ], [ 1/2 ] ], 
      [ [ 22 ], [ 1/2 ] ], [ [ 24 ], [ -1/2 ] ], [ [ 23 ], [ -1/2 ] ], [ [ 19 ], [ -1/2 ] ], 
      [ [ 21 ], [ 1/2 ] ], [ [ 20 ], [ -1/2 ] ], [ [ 10 ], [ 1/2 ] ], [ [ 9 ], [ -1/2 ] ], 
      [ [ 14 ], [ -1/2 ] ], [ [ 16 ], [ -1/2 ] ], [ [ 15 ], [ 1/2 ] ], [ [ 11 ], [ 1/2 ] ], 
      [ [ 13 ], [ -1/2 ] ], [ [ 12 ], [ -1/2 ] ], [ [  ], [  ] ], [ [ 4 ], [ 1/2 ] ], 
      [ [ 4 ], [ 1/2 ] ] ], [ [ [  ], [  ] ], [ [  ], [  ] ], [ [  ], [  ] ], [ [  ], [  ] ], 
      [ [ 26, 27 ], [ 1, 1 ] ], [ [  ], [  ] ], [ [  ], [  ] ], [ [  ], [  ] ], 
      [ [ 22 ], [ 1/2 ] ], [ [ 19 ], [ -1/2 ] ], [ [ 18 ], [ 1/2 ] ], [ [ 23 ], [ 1/2 ] ], 
      [ [ 24 ], [ -1/2 ] ], [ [ 17 ], [ -1/2 ] ], [ [ 20 ], [ -1/2 ] ], [ [ 21 ], [ -1/2 ] ], 
      [ [ 14 ], [ -1/2 ] ], [ [ 11 ], [ 1/2 ] ], [ [ 10 ], [ -1/2 ] ], [ [ 15 ], [ -1/2 ] ], 
      [ [ 16 ], [ -1/2 ] ], [ [ 9 ], [ 1/2 ] ], [ [ 12 ], [ 1/2 ] ], [ [ 13 ], [ -1/2 ] ], 
      [ [  ], [  ] ], [ [ 5 ], [ 1/2 ] ], [ [ 5 ], [ 1/2 ] ] ], 
  [ [ [  ], [  ] ], [ [  ], [  ] ], [ [  ], [  ] ], [ [  ], [  ] ], [ [  ], [  ] ], 
      [ [ 26, 27 ], [ 1, 1 ] ], [ [  ], [  ] ], [ [  ], [  ] ], [ [ 21 ], [ -1/2 ] ], 
      [ [ 23 ], [ 1/2 ] ], [ [ 20 ], [ -1/2 ] ], [ [ 19 ], [ 1/2 ] ], [ [ 17 ], [ 1/2 ] ], 
      [ [ 24 ], [ -1/2 ] ], [ [ 18 ], [ -1/2 ] ], [ [ 22 ], [ -1/2 ] ], [ [ 13 ], [ 1/2 ] ], 
      [ [ 15 ], [ -1/2 ] ], [ [ 12 ], [ 1/2 ] ], [ [ 11 ], [ -1/2 ] ], [ [ 9 ], [ -1/2 ] ], 
      [ [ 16 ], [ -1/2 ] ], [ [ 10 ], [ 1/2 ] ], [ [ 14 ], [ -1/2 ] ], [ [  ], [  ] ], 
      [ [ 6 ], [ 1/2 ] ], [ [ 6 ], [ 1/2 ] ] ], 
  [ [ [  ], [  ] ], [ [  ], [  ] ], [ [  ], [  ] ], [ [  ], [  ] ], [ [  ], [  ] ], 
      [ [  ], [  ] ], [ [ 26, 27 ], [ 1, 1 ] ], [ [  ], [  ] ], [ [ 19 ], [ -1/2 ] ], 
      [ [ 22 ], [ -1/2 ] ], [ [ 17 ], [ 1/2 ] ], [ [ 21 ], [ -1/2 ] ], [ [ 20 ], [ 1/2 ] ], 
      [ [ 18 ], [ 1/2 ] ], [ [ 24 ], [ -1/2 ] ], [ [ 23 ], [ -1/2 ] ], [ [ 11 ], [ 1/2 ] ], 
      [ [ 14 ], [ 1/2 ] ], [ [ 9 ], [ -1/2 ] ], [ [ 13 ], [ 1/2 ] ], [ [ 12 ], [ -1/2 ] ], 
      [ [ 10 ], [ -1/2 ] ], [ [ 16 ], [ -1/2 ] ], [ [ 15 ], [ -1/2 ] ], [ [  ], [  ] ], 
      [ [ 7 ], [ 1/2 ] ], [ [ 7 ], [ 1/2 ] ] ], 
  [ [ [  ], [  ] ], [ [  ], [  ] ], [ [  ], [  ] ], [ [  ], [  ] ], [ [  ], [  ] ], 
      [ [  ], [  ] ], [ [  ], [  ] ], [ [ 26, 27 ], [ 1, 1 ] ], [ [ 17 ], [ -1/2 ] ], 
      [ [ 18 ], [ -1/2 ] ], [ [ 19 ], [ -1/2 ] ], [ [ 20 ], [ -1/2 ] ], [ [ 21 ], [ -1/2 ] ], 
      [ [ 22 ], [ -1/2 ] ], [ [ 23 ], [ -1/2 ] ], [ [ 24 ], [ 1/2 ] ], [ [ 9 ], [ -1/2 ] ], 
      [ [ 10 ], [ -1/2 ] ], [ [ 11 ], [ -1/2 ] ], [ [ 12 ], [ -1/2 ] ], [ [ 13 ], [ -1/2 ] ], 
      [ [ 14 ], [ -1/2 ] ], [ [ 15 ], [ -1/2 ] ], [ [ 16 ], [ 1/2 ] ], [ [  ], [  ] ], 
      [ [ 8 ], [ 1/2 ] ], [ [ 8 ], [ 1/2 ] ] ], 
  [ [ [ 24 ], [ -1/2 ] ], [ [ 20 ], [ 1/2 ] ], [ [ 23 ], [ 1/2 ] ], [ [ 18 ], [ -1/2 ] ], 
      [ [ 22 ], [ 1/2 ] ], [ [ 21 ], [ -1/2 ] ], [ [ 19 ], [ -1/2 ] ], [ [ 17 ], [ -1/2 ] ], 
      [ [ 25, 27 ], [ 1, 1 ] ], [ [  ], [  ] ], [ [  ], [  ] ], [ [  ], [  ] ], [ [  ], [  ] ], 
      [ [  ], [  ] ], [ [  ], [  ] ], [ [  ], [  ] ], [ [ 8 ], [ -1/2 ] ], [ [ 4 ], [ -1/2 ] ], 
      [ [ 7 ], [ -1/2 ] ], [ [ 2 ], [ 1/2 ] ], [ [ 6 ], [ -1/2 ] ], [ [ 5 ], [ 1/2 ] ], 
      [ [ 3 ], [ 1/2 ] ], [ [ 1 ], [ -1/2 ] ], [ [ 9 ], [ 1/2 ] ], [ [  ], [  ] ], 
      [ [ 9 ], [ 1/2 ] ] ], [ [ [ 20 ], [ -1/2 ] ], [ [ 24 ], [ -1/2 ] ], [ [ 21 ], [ 1/2 ] ], 
      [ [ 17 ], [ 1/2 ] ], [ [ 19 ], [ -1/2 ] ], [ [ 23 ], [ 1/2 ] ], [ [ 22 ], [ -1/2 ] ], 
      [ [ 18 ], [ -1/2 ] ], [ [  ], [  ] ], [ [ 25, 27 ], [ 1, 1 ] ], [ [  ], [  ] ], 
      [ [  ], [  ] ], [ [  ], [  ] ], [ [  ], [  ] ], [ [  ], [  ] ], [ [  ], [  ] ], 
      [ [ 4 ], [ 1/2 ] ], [ [ 8 ], [ -1/2 ] ], [ [ 5 ], [ -1/2 ] ], [ [ 1 ], [ -1/2 ] ], 
      [ [ 3 ], [ 1/2 ] ], [ [ 7 ], [ -1/2 ] ], [ [ 6 ], [ 1/2 ] ], [ [ 2 ], [ -1/2 ] ], 
      [ [ 10 ], [ 1/2 ] ], [ [  ], [  ] ], [ [ 10 ], [ 1/2 ] ] ], 
  [ [ [ 23 ], [ -1/2 ] ], [ [ 21 ], [ -1/2 ] ], [ [ 24 ], [ -1/2 ] ], [ [ 22 ], [ 1/2 ] ], 
      [ [ 18 ], [ 1/2 ] ], [ [ 20 ], [ -1/2 ] ], [ [ 17 ], [ 1/2 ] ], [ [ 19 ], [ -1/2 ] ], 
      [ [  ], [  ] ], [ [  ], [  ] ], [ [ 25, 27 ], [ 1, 1 ] ], [ [  ], [  ] ], [ [  ], [  ] ], 
      [ [  ], [  ] ], [ [  ], [  ] ], [ [  ], [  ] ], [ [ 7 ], [ 1/2 ] ], [ [ 5 ], [ 1/2 ] ], 
      [ [ 8 ], [ -1/2 ] ], [ [ 6 ], [ -1/2 ] ], [ [ 2 ], [ -1/2 ] ], [ [ 4 ], [ 1/2 ] ], 
      [ [ 1 ], [ -1/2 ] ], [ [ 3 ], [ -1/2 ] ], [ [ 11 ], [ 1/2 ] ], [ [  ], [  ] ], 
      [ [ 11 ], [ 1/2 ] ] ], [ [ [ 18 ], [ 1/2 ] ], [ [ 17 ], [ -1/2 ] ], [ [ 22 ], [ -1/2 ] ], 
      [ [ 24 ], [ -1/2 ] ], [ [ 23 ], [ 1/2 ] ], [ [ 19 ], [ 1/2 ] ], [ [ 21 ], [ -1/2 ] ], 
      [ [ 20 ], [ -1/2 ] ], [ [  ], [  ] ], [ [  ], [  ] ], [ [  ], [  ] ], 
      [ [ 25, 27 ], [ 1, 1 ] ], [ [  ], [  ] ], [ [  ], [  ] ], [ [  ], [  ] ], [ [  ], [  ] ], 
      [ [ 2 ], [ -1/2 ] ], [ [ 1 ], [ 1/2 ] ], [ [ 6 ], [ 1/2 ] ], [ [ 8 ], [ -1/2 ] ], 
      [ [ 7 ], [ -1/2 ] ], [ [ 3 ], [ -1/2 ] ], [ [ 5 ], [ 1/2 ] ], [ [ 4 ], [ -1/2 ] ], 
      [ [ 12 ], [ 1/2 ] ], [ [  ], [  ] ], [ [ 12 ], [ 1/2 ] ] ], 
  [ [ [ 22 ], [ -1/2 ] ], [ [ 19 ], [ 1/2 ] ], [ [ 18 ], [ -1/2 ] ], [ [ 23 ], [ -1/2 ] ], 
      [ [ 24 ], [ -1/2 ] ], [ [ 17 ], [ 1/2 ] ], [ [ 20 ], [ 1/2 ] ], [ [ 21 ], [ -1/2 ] ], 
      [ [  ], [  ] ], [ [  ], [  ] ], [ [  ], [  ] ], [ [  ], [  ] ], [ [ 25, 27 ], [ 1, 1 ] ], 
      [ [  ], [  ] ], [ [  ], [  ] ], [ [  ], [  ] ], [ [ 6 ], [ 1/2 ] ], [ [ 3 ], [ -1/2 ] ], 
      [ [ 2 ], [ 1/2 ] ], [ [ 7 ], [ 1/2 ] ], [ [ 8 ], [ -1/2 ] ], [ [ 1 ], [ -1/2 ] ], 
      [ [ 4 ], [ -1/2 ] ], [ [ 5 ], [ -1/2 ] ], [ [ 13 ], [ 1/2 ] ], [ [  ], [  ] ], 
      [ [ 13 ], [ 1/2 ] ] ], [ [ [ 21 ], [ 1/2 ] ], [ [ 23 ], [ -1/2 ] ], [ [ 20 ], [ 1/2 ] ], 
      [ [ 19 ], [ -1/2 ] ], [ [ 17 ], [ -1/2 ] ], [ [ 24 ], [ -1/2 ] ], [ [ 18 ], [ 1/2 ] ], 
      [ [ 22 ], [ -1/2 ] ], [ [  ], [  ] ], [ [  ], [  ] ], [ [  ], [  ] ], [ [  ], [  ] ], 
      [ [  ], [  ] ], [ [ 25, 27 ], [ 1, 1 ] ], [ [  ], [  ] ], [ [  ], [  ] ], 
      [ [ 5 ], [ -1/2 ] ], [ [ 7 ], [ 1/2 ] ], [ [ 4 ], [ -1/2 ] ], [ [ 3 ], [ 1/2 ] ], 
      [ [ 1 ], [ 1/2 ] ], [ [ 8 ], [ -1/2 ] ], [ [ 2 ], [ -1/2 ] ], [ [ 6 ], [ -1/2 ] ], 
      [ [ 14 ], [ 1/2 ] ], [ [  ], [  ] ], [ [ 14 ], [ 1/2 ] ] ], 
  [ [ [ 19 ], [ 1/2 ] ], [ [ 22 ], [ 1/2 ] ], [ [ 17 ], [ -1/2 ] ], [ [ 21 ], [ 1/2 ] ], 
      [ [ 20 ], [ -1/2 ] ], [ [ 18 ], [ -1/2 ] ], [ [ 24 ], [ -1/2 ] ], [ [ 23 ], [ -1/2 ] ], 
      [ [  ], [  ] ], [ [  ], [  ] ], [ [  ], [  ] ], [ [  ], [  ] ], [ [  ], [  ] ], 
      [ [  ], [  ] ], [ [ 25, 27 ], [ 1, 1 ] ], [ [  ], [  ] ], [ [ 3 ], [ -1/2 ] ], 
      [ [ 6 ], [ -1/2 ] ], [ [ 1 ], [ 1/2 ] ], [ [ 5 ], [ -1/2 ] ], [ [ 4 ], [ 1/2 ] ], 
      [ [ 2 ], [ 1/2 ] ], [ [ 8 ], [ -1/2 ] ], [ [ 7 ], [ -1/2 ] ], [ [ 15 ], [ 1/2 ] ], 
      [ [  ], [  ] ], [ [ 15 ], [ 1/2 ] ] ], 
  [ [ [ 17 ], [ -1/2 ] ], [ [ 18 ], [ -1/2 ] ], [ [ 19 ], [ -1/2 ] ], [ [ 20 ], [ -1/2 ] ], 
      [ [ 21 ], [ -1/2 ] ], [ [ 22 ], [ -1/2 ] ], [ [ 23 ], [ -1/2 ] ], [ [ 24 ], [ 1/2 ] ], 
      [ [  ], [  ] ], [ [  ], [  ] ], [ [  ], [  ] ], [ [  ], [  ] ], [ [  ], [  ] ], 
      [ [  ], [  ] ], [ [  ], [  ] ], [ [ 25, 27 ], [ 1, 1 ] ], [ [ 1 ], [ -1/2 ] ], 
      [ [ 2 ], [ -1/2 ] ], [ [ 3 ], [ -1/2 ] ], [ [ 4 ], [ -1/2 ] ], [ [ 5 ], [ -1/2 ] ], 
      [ [ 6 ], [ -1/2 ] ], [ [ 7 ], [ -1/2 ] ], [ [ 8 ], [ 1/2 ] ], [ [ 16 ], [ 1/2 ] ], 
      [ [  ], [  ] ], [ [ 16 ], [ 1/2 ] ] ], 
  [ [ [ 16 ], [ -1/2 ] ], [ [ 12 ], [ -1/2 ] ], [ [ 15 ], [ -1/2 ] ], [ [ 10 ], [ 1/2 ] ], 
      [ [ 14 ], [ -1/2 ] ], [ [ 13 ], [ 1/2 ] ], [ [ 11 ], [ 1/2 ] ], [ [ 9 ], [ -1/2 ] ], 
      [ [ 8 ], [ -1/2 ] ], [ [ 4 ], [ 1/2 ] ], [ [ 7 ], [ 1/2 ] ], [ [ 2 ], [ -1/2 ] ], 
      [ [ 6 ], [ 1/2 ] ], [ [ 5 ], [ -1/2 ] ], [ [ 3 ], [ -1/2 ] ], [ [ 1 ], [ -1/2 ] ], 
      [ [ 25, 26 ], [ 1, 1 ] ], [ [  ], [  ] ], [ [  ], [  ] ], [ [  ], [  ] ], [ [  ], [  ] ], 
      [ [  ], [  ] ], [ [  ], [  ] ], [ [  ], [  ] ], [ [ 17 ], [ 1/2 ] ], [ [ 17 ], [ 1/2 ] ], 
      [ [  ], [  ] ] ], [ [ [ 12 ], [ 1/2 ] ], [ [ 16 ], [ -1/2 ] ], [ [ 13 ], [ -1/2 ] ], 
      [ [ 9 ], [ -1/2 ] ], [ [ 11 ], [ 1/2 ] ], [ [ 15 ], [ -1/2 ] ], [ [ 14 ], [ 1/2 ] ], 
      [ [ 10 ], [ -1/2 ] ], [ [ 4 ], [ -1/2 ] ], [ [ 8 ], [ -1/2 ] ], [ [ 5 ], [ 1/2 ] ], 
      [ [ 1 ], [ 1/2 ] ], [ [ 3 ], [ -1/2 ] ], [ [ 7 ], [ 1/2 ] ], [ [ 6 ], [ -1/2 ] ], 
      [ [ 2 ], [ -1/2 ] ], [ [  ], [  ] ], [ [ 25, 26 ], [ 1, 1 ] ], [ [  ], [  ] ], 
      [ [  ], [  ] ], [ [  ], [  ] ], [ [  ], [  ] ], [ [  ], [  ] ], [ [  ], [  ] ], 
      [ [ 18 ], [ 1/2 ] ], [ [ 18 ], [ 1/2 ] ], [ [  ], [  ] ] ], 
  [ [ [ 15 ], [ 1/2 ] ], [ [ 13 ], [ 1/2 ] ], [ [ 16 ], [ -1/2 ] ], [ [ 14 ], [ -1/2 ] ], 
      [ [ 10 ], [ -1/2 ] ], [ [ 12 ], [ 1/2 ] ], [ [ 9 ], [ -1/2 ] ], [ [ 11 ], [ -1/2 ] ], 
      [ [ 7 ], [ -1/2 ] ], [ [ 5 ], [ -1/2 ] ], [ [ 8 ], [ -1/2 ] ], [ [ 6 ], [ 1/2 ] ], 
      [ [ 2 ], [ 1/2 ] ], [ [ 4 ], [ -1/2 ] ], [ [ 1 ], [ 1/2 ] ], [ [ 3 ], [ -1/2 ] ], 
      [ [  ], [  ] ], [ [  ], [  ] ], [ [ 25, 26 ], [ 1, 1 ] ], [ [  ], [  ] ], [ [  ], [  ] ], 
      [ [  ], [  ] ], [ [  ], [  ] ], [ [  ], [  ] ], [ [ 19 ], [ 1/2 ] ], [ [ 19 ], [ 1/2 ] ], 
      [ [  ], [  ] ] ], [ [ [ 10 ], [ -1/2 ] ], [ [ 9 ], [ 1/2 ] ], [ [ 14 ], [ 1/2 ] ], 
      [ [ 16 ], [ -1/2 ] ], [ [ 15 ], [ -1/2 ] ], [ [ 11 ], [ -1/2 ] ], [ [ 13 ], [ 1/2 ] ], 
      [ [ 12 ], [ -1/2 ] ], [ [ 2 ], [ 1/2 ] ], [ [ 1 ], [ -1/2 ] ], [ [ 6 ], [ -1/2 ] ], 
      [ [ 8 ], [ -1/2 ] ], [ [ 7 ], [ 1/2 ] ], [ [ 3 ], [ 1/2 ] ], [ [ 5 ], [ -1/2 ] ], 
      [ [ 4 ], [ -1/2 ] ], [ [  ], [  ] ], [ [  ], [  ] ], [ [  ], [  ] ], 
      [ [ 25, 26 ], [ 1, 1 ] ], [ [  ], [  ] ], [ [  ], [  ] ], [ [  ], [  ] ], [ [  ], [  ] ], 
      [ [ 20 ], [ 1/2 ] ], [ [ 20 ], [ 1/2 ] ], [ [  ], [  ] ] ], 
  [ [ [ 14 ], [ 1/2 ] ], [ [ 11 ], [ -1/2 ] ], [ [ 10 ], [ 1/2 ] ], [ [ 15 ], [ 1/2 ] ], 
      [ [ 16 ], [ -1/2 ] ], [ [ 9 ], [ -1/2 ] ], [ [ 12 ], [ -1/2 ] ], [ [ 13 ], [ -1/2 ] ], 
      [ [ 6 ], [ -1/2 ] ], [ [ 3 ], [ 1/2 ] ], [ [ 2 ], [ -1/2 ] ], [ [ 7 ], [ -1/2 ] ], 
      [ [ 8 ], [ -1/2 ] ], [ [ 1 ], [ 1/2 ] ], [ [ 4 ], [ 1/2 ] ], [ [ 5 ], [ -1/2 ] ], 
      [ [  ], [  ] ], [ [  ], [  ] ], [ [  ], [  ] ], [ [  ], [  ] ], [ [ 25, 26 ], [ 1, 1 ] ], 
      [ [  ], [  ] ], [ [  ], [  ] ], [ [  ], [  ] ], [ [ 21 ], [ 1/2 ] ], [ [ 21 ], [ 1/2 ] ], 
      [ [  ], [  ] ] ], [ [ [ 13 ], [ -1/2 ] ], [ [ 15 ], [ 1/2 ] ], [ [ 12 ], [ -1/2 ] ], 
      [ [ 11 ], [ 1/2 ] ], [ [ 9 ], [ 1/2 ] ], [ [ 16 ], [ -1/2 ] ], [ [ 10 ], [ -1/2 ] ], 
      [ [ 14 ], [ -1/2 ] ], [ [ 5 ], [ 1/2 ] ], [ [ 7 ], [ -1/2 ] ], [ [ 4 ], [ 1/2 ] ], 
      [ [ 3 ], [ -1/2 ] ], [ [ 1 ], [ -1/2 ] ], [ [ 8 ], [ -1/2 ] ], [ [ 2 ], [ 1/2 ] ], 
      [ [ 6 ], [ -1/2 ] ], [ [  ], [  ] ], [ [  ], [  ] ], [ [  ], [  ] ], [ [  ], [  ] ], 
      [ [  ], [  ] ], [ [ 25, 26 ], [ 1, 1 ] ], [ [  ], [  ] ], [ [  ], [  ] ], 
      [ [ 22 ], [ 1/2 ] ], [ [ 22 ], [ 1/2 ] ], [ [  ], [  ] ] ], 
  [ [ [ 11 ], [ -1/2 ] ], [ [ 14 ], [ -1/2 ] ], [ [ 9 ], [ 1/2 ] ], [ [ 13 ], [ -1/2 ] ], 
      [ [ 12 ], [ 1/2 ] ], [ [ 10 ], [ 1/2 ] ], [ [ 16 ], [ -1/2 ] ], [ [ 15 ], [ -1/2 ] ], 
      [ [ 3 ], [ 1/2 ] ], [ [ 6 ], [ 1/2 ] ], [ [ 1 ], [ -1/2 ] ], [ [ 5 ], [ 1/2 ] ], 
      [ [ 4 ], [ -1/2 ] ], [ [ 2 ], [ -1/2 ] ], [ [ 8 ], [ -1/2 ] ], [ [ 7 ], [ -1/2 ] ], 
      [ [  ], [  ] ], [ [  ], [  ] ], [ [  ], [  ] ], [ [  ], [  ] ], [ [  ], [  ] ], 
      [ [  ], [  ] ], [ [ 25, 26 ], [ 1, 1 ] ], [ [  ], [  ] ], [ [ 23 ], [ 1/2 ] ], 
      [ [ 23 ], [ 1/2 ] ], [ [  ], [  ] ] ], 
  [ [ [ 9 ], [ -1/2 ] ], [ [ 10 ], [ -1/2 ] ], [ [ 11 ], [ -1/2 ] ], [ [ 12 ], [ -1/2 ] ], 
      [ [ 13 ], [ -1/2 ] ], [ [ 14 ], [ -1/2 ] ], [ [ 15 ], [ -1/2 ] ], [ [ 16 ], [ 1/2 ] ], 
      [ [ 1 ], [ -1/2 ] ], [ [ 2 ], [ -1/2 ] ], [ [ 3 ], [ -1/2 ] ], [ [ 4 ], [ -1/2 ] ], 
      [ [ 5 ], [ -1/2 ] ], [ [ 6 ], [ -1/2 ] ], [ [ 7 ], [ -1/2 ] ], [ [ 8 ], [ 1/2 ] ], 
      [ [  ], [  ] ], [ [  ], [  ] ], [ [  ], [  ] ], [ [  ], [  ] ], [ [  ], [  ] ], 
      [ [  ], [  ] ], [ [  ], [  ] ], [ [ 25, 26 ], [ 1, 1 ] ], [ [ 24 ], [ 1/2 ] ], 
      [ [ 24 ], [ 1/2 ] ], [ [  ], [  ] ] ], 
  [ [ [  ], [  ] ], [ [  ], [  ] ], [ [  ], [  ] ], [ [  ], [  ] ], [ [  ], [  ] ], 
      [ [  ], [  ] ], [ [  ], [  ] ], [ [  ], [  ] ], [ [ 9 ], [ 1/2 ] ], [ [ 10 ], [ 1/2 ] ], 
      [ [ 11 ], [ 1/2 ] ], [ [ 12 ], [ 1/2 ] ], [ [ 13 ], [ 1/2 ] ], [ [ 14 ], [ 1/2 ] ], 
      [ [ 15 ], [ 1/2 ] ], [ [ 16 ], [ 1/2 ] ], [ [ 17 ], [ 1/2 ] ], [ [ 18 ], [ 1/2 ] ], 
      [ [ 19 ], [ 1/2 ] ], [ [ 20 ], [ 1/2 ] ], [ [ 21 ], [ 1/2 ] ], [ [ 22 ], [ 1/2 ] ], 
      [ [ 23 ], [ 1/2 ] ], [ [ 24 ], [ 1/2 ] ], [ [ 25 ], [ 1 ] ], [ [  ], [  ] ], [ [  ], [  ] ] 
     ], [ [ [ 1 ], [ 1/2 ] ], [ [ 2 ], [ 1/2 ] ], [ [ 3 ], [ 1/2 ] ], [ [ 4 ], [ 1/2 ] ], 
      [ [ 5 ], [ 1/2 ] ], [ [ 6 ], [ 1/2 ] ], [ [ 7 ], [ 1/2 ] ], [ [ 8 ], [ 1/2 ] ], 
      [ [  ], [  ] ], [ [  ], [  ] ], [ [  ], [  ] ], [ [  ], [  ] ], [ [  ], [  ] ], 
      [ [  ], [  ] ], [ [  ], [  ] ], [ [  ], [  ] ], [ [ 17 ], [ 1/2 ] ], [ [ 18 ], [ 1/2 ] ], 
      [ [ 19 ], [ 1/2 ] ], [ [ 20 ], [ 1/2 ] ], [ [ 21 ], [ 1/2 ] ], [ [ 22 ], [ 1/2 ] ], 
      [ [ 23 ], [ 1/2 ] ], [ [ 24 ], [ 1/2 ] ], [ [  ], [  ] ], [ [ 26 ], [ 1 ] ], [ [  ], [  ] ] 
     ], [ [ [ 1 ], [ 1/2 ] ], [ [ 2 ], [ 1/2 ] ], [ [ 3 ], [ 1/2 ] ], [ [ 4 ], [ 1/2 ] ], 
      [ [ 5 ], [ 1/2 ] ], [ [ 6 ], [ 1/2 ] ], [ [ 7 ], [ 1/2 ] ], [ [ 8 ], [ 1/2 ] ], 
      [ [ 9 ], [ 1/2 ] ], [ [ 10 ], [ 1/2 ] ], [ [ 11 ], [ 1/2 ] ], [ [ 12 ], [ 1/2 ] ], 
      [ [ 13 ], [ 1/2 ] ], [ [ 14 ], [ 1/2 ] ], [ [ 15 ], [ 1/2 ] ], [ [ 16 ], [ 1/2 ] ], 
      [ [  ], [  ] ], [ [  ], [  ] ], [ [  ], [  ] ], [ [  ], [  ] ], [ [  ], [  ] ], 
      [ [  ], [  ] ], [ [  ], [  ] ], [ [  ], [  ] ], [ [  ], [  ] ], [ [  ], [  ] ], 
      [ [ 27 ], [ 1 ] ] ], 1, Zero(F) ]; 
            # Construct the algebra.
            A:= AlgebraByStructureConstantsArg([F, T, "i1", "i2", "i3", "i4", "i5", "i6", "i7", "i8", 
            "j1", "j2", "j3", "j4", "j5", "j6", "j7", "j8", 
            "k1", "k2", "k3", "k4", "k5", "k6", "k7", "k8", 
            "ei", "ej", "ek"], filter );
            SetFilterObj( A, IsAlgebraWithOne );
            SetFilterObj( A, IsJordanAlgebra );
            SetJordanRank( A, 3 );
            SetJordanDegree( A, 8 );
            SetJordanOffDiagonalBasis( A, Basis(OctonionAlgebra(Rationals)) );
            SetJordanHomotopeVector( A, One(A) );
            SetJordanBasisTraces( A, List(Basis(A), 
                j -> (Rank(j)/Dimension(FamilyObj(j)!.fullSCAlgebra))*Trace(AdjointMatrix(Basis(FamilyObj(j)!.fullSCAlgebra), j)))
            );
            return A;
        end );
        A:= AlgebraWithOne( F, CanonicalBasis( stored ), "basis" );
        SetGeneratorsOfAlgebra( A, GeneratorsOfAlgebraWithOne( A ) );
        SetIsFullSCAlgebra( A, true );
        SetFilterObj( A, IsJordanAlgebra );
        SetFilterObj( A, IsAlgebraWithOne);
        SetJordanRank( A, 3 );
        SetJordanDegree( A, 8 );
        SetJordanOffDiagonalBasis( A, Basis(OctonionAlgebra(Rationals)) );
        SetJordanHomotopeVector( A, One(A) );
        SetJordanBasisTraces( A, List(Basis(A), 
            j -> (Rank(j)/Dimension(FamilyObj(j)!.fullSCAlgebra))*Trace(AdjointMatrix(Basis(FamilyObj(j)!.fullSCAlgebra), j)))
        );
        jordan_basis := HermitianJordanAlgebraBasis(3, CanonicalBasis(OctonionAlgebra(Rationals)) );
        e := jordan_basis{[1..3]};
        i := jordan_basis{[20..27]};
        j := ComplexConjugate(jordan_basis{[12..19]});
        k := jordan_basis{[4..11]};
        jordan_basis := Concatenation([i,j,k,e]);
        SetJordanMatrixBasis( A, jordan_basis );
        return A;
    end );

InstallGlobalFunction( HermitianMatrixToAlbertVector, 
    function(mat)
        local temp;
        if not IsMatrix(mat) or not DimensionsMat(mat) = [3,3] or not IsSubset(OctonionAlgebra(Rationals), Flat(mat)) then 
            return fail;
        fi;
        if ComplexConjugate(TransposedMat(mat)) <> mat then 
            return fail;
        fi;
        temp := HermitianMatrixToJordanCoefficients(mat, Basis(OctonionAlgebra(Rationals)));
        temp := Concatenation([temp{[20..27]}, -temp{[12..18]}, temp{[19]}, temp{[4..11]}, temp{[1..3]}]);
        return LinearCombination(Basis(AlbertAlgebra(Rationals)), temp);
    end);

InstallGlobalFunction( AlbertVectorToHermitianMatrix, 
    function(vec)
        if not IsAlbertAlgebraObj(vec) then return fail; fi;
        return LinearCombination(JordanMatrixBasis(AlbertAlgebra(Rationals)), ExtRepOfObj(vec));
    end);



# See Faraut and Koranyi p. 32
InstallMethod( JordanQuadraticOperator, 
     "for a Jordan algebra element",
    [ IsJordanAlgebraObj ],
    function(j)
        return 2*AdjointMatrix(CanonicalBasis(FamilyObj(j)!.fullSCAlgebra), j)^2 - AdjointMatrix(CanonicalBasis(FamilyObj(j)!.fullSCAlgebra), j^2); 
    end);

InstallMethod( JordanQuadraticOperator, 
     "for a pair of Jordan algebra elements",
    [ IsJordanAlgebraObj, IsJordanAlgebraObj ],
    function(j, k)
        return 2*j*(j*k) - (j^2)*k; 
    end);

InstallMethod( JordanTripleSystem,
    "for three Jordan algebra elements",
    [IsJordanAlgebraObj, IsJordanAlgebraObj, IsJordanAlgebraObj],
    {x,y,z} -> x*(y*z) + (x*y)*z - (x*z)*y
    );

# T-Design Tools

InstallGlobalFunction( JacobiPolynomial, function(k, a, b)
    local temp, a1, a2, a3, a4, n, x;
    if not IsInt(k) and k > -1 then 
        return fail;
    fi; 
    if not (IsPolynomial(a) or (IsRat(a) and a > -1)) then 
        return fail;
    fi;
    if not (IsPolynomial(b) or (IsRat(b) and a > -1)) then 
        return fail;
    fi;  
    n := k - 1;
    a1 := 2*(n+1)*(n+a+b+1)*(2*n+a+b );
    a2 := (2*n+a+b+1)*(a^2 - b^2 );
    a3 := (2*n + a + b)*(2*n + a + b + 1)*(2*n + a + b + 2 );
    a4 := 2*(n+a)*(n+b)*(2*n+a+b+2 );
    x := [0,1];
    if k = 0 then 
        return [1];
    elif k = -1 then 
        return [0];
    elif k = 1 then 
        return (1/2)*[a-b,(a+b+2)];
    fi;
    return ProductCoeffs([a2/a1, a3/a1], JacobiPolynomial(k-1,a,b))-(a4/a1)*JacobiPolynomial(k-2,a,b );
end );

InstallGlobalFunction( Q_k_epsilon, function(k, epsilon, rank, degree, x) 
    local temp, p, poch, N, m;
    if k = 0 and epsilon = 0 then return 1+0*x; fi;
    m := degree/2;
    N := rank*m;
    p := ValuePol(JacobiPolynomial(k, N-m-1, m-1+epsilon), 2*x - 1 );
    poch := function(a,n)
        if n = 1 then return a;
        elif n =  0 then return 1;
        elif n < 0 then return 0;
        fi;
        return Product(List([1..n], b -> a + b -1) );
    end;
    temp := poch(N, k + epsilon - 1)*poch(N-m, k)*(2*k + N + epsilon - 1 );
    temp := temp/(Factorial(k)*poch(m,k+epsilon) );
    return temp*p/Value(p, [x], [1] );
end );

InstallGlobalFunction( R_k_epsilon, function(k, epsilon, rank, degree, x)
    local temp, n;
    temp := 0*x;
    for n in [0..k] do 
        temp := temp + Q_k_epsilon(n, epsilon, rank, degree, x );
    od;
    return temp;
end );

InstallGlobalFunction( JordanDesignByParameters, function(rank, degree)
    local obj, F, x;
    # Check that the inputs match a Jordan primitive idempotent space    
    if not IsInt(rank) or rank < 2 then return fail; fi;
    if rank > 2 and not degree in [1,2,4,8] then return fail; fi;
    if degree = 8 and rank > 3 then return fail; fi; 
    # Create the object
    obj := Objectify(NewType(NewFamily( "Design"), IsJordanDesign and IsComponentObjectRep, rec()), rec() );
    SetFilterObj(obj, IsAttributeStoringRep );
    # Assign rank and degree attributes.
    SetJordanDesignRank(obj, rank );
    SetJordanDesignDegree(obj, degree );
    # Assign Spherical or Projective filters.
    if rank = 2 then 
        SetFilterObj(obj, IsSphericalJordanDesign );
    fi;
    if degree in [1,2,4,8] then 
        SetFilterObj(obj, IsProjectiveJordanDesign );
    fi;
    return obj;
end );

InstallMethod( PrintObj,
    "for a design",
    [ IsJordanDesign ],
    function(x)
    local text;
    Print( "<design with rank ", JordanDesignRank(x), " and degree ", JordanDesignDegree(x), ">" );
   end );

InstallMethod(JordanDesignQPolynomials,
    "Generic method for designs",
    [ IsJordanDesign ],
    function(D)
        local x, temp;
        x := Indeterminate(Rationals, "x" );
        temp := function(k)
            if IsInt(k) and k > -1 then 
                return CoefficientsOfUnivariatePolynomial((Q_k_epsilon(k, 0, JordanDesignRank(D), JordanDesignDegree(D), x)) );
            fi;
            return fail;
        end;
        return temp;
    end );

InstallMethod( JordanDesignConnectionCoefficients,
    "Generic method for designs",
    [ IsJordanDesign ],
    function(D)
        local temp;
        temp := function(s)
            local x, Q, V, basis, mat, k, i;
            x := Indeterminate(Rationals, "x" );
            Q := List([0..s], i -> Q_k_epsilon(i,0, JordanDesignRank(D), JordanDesignDegree(D), x) );
            V := VectorSpace(Rationals, Q );
            basis := Basis(V, Q );
            mat := [];
            for k in [0..s] do 
                Append(mat, [
                    Coefficients(basis, x^k)
                ] );
            od;
            return mat;
        end;
        return temp; 
    end );

InstallMethod( JordanDesignAddAngleSet, 
    "for designs",
    [ IsJordanDesign, IsList ],
    function(D, A)
        if not (ForAll(A, IsCyc) and 
            ForAll(A, x -> ComplexConjugate(x) = x) and
            ForAll(A, x -> not IsRat(x) or (x < 1 and x >= 0)))
        then 
            return fail;
        fi;  
        SetJordanDesignAngleSet(D, Set(A) );
        SetFilterObj(D, IsJordanDesignWithAngleSet );
        # Assign Positive Indicator Coefficients filter if applicable.
        if [true] = Set(JordanDesignNormalizedIndicatorCoefficients(D), x -> x > 0) then 
            SetFilterObj(D, IsJordanDesignWithPositiveIndicatorCoefficients );
        fi;
        return D; 
    end );

InstallGlobalFunction( JordanDesignByAngleSet,  function(rank, degree, A)
    local obj, F, x;
    obj := JordanDesignByParameters(rank, degree );
    if obj = fail then return obj; fi;
    # Test the angle set:
    if not (ForAll(A, IsCyc) and 
            ForAll(A, x -> ComplexConjugate(x) = x) and
            ForAll(A, x -> not IsRat(x) or (x < 1 and x >= 0)))
    then 
            return fail;
    fi; 
    # Assign angle set.
    SetJordanDesignAngleSet(obj, Set(A) );
    SetFilterObj(obj, IsJordanDesignWithAngleSet ); 
    # Assign Positive Indicator Coefficients filter if applicable.
    if [true] = Set(JordanDesignNormalizedIndicatorCoefficients(obj), x -> x > 0) then 
        SetFilterObj(obj, IsJordanDesignWithPositiveIndicatorCoefficients );
    fi;
    return obj;
end );

InstallMethod( PrintObj,
    "for a design with angle set",
    [ IsJordanDesignWithAngleSet ],
    function(x)
    local text;
    Print( "<design with rank ", JordanDesignRank(x), ", degree ", JordanDesignDegree(x), ", and angle set ", JordanDesignAngleSet(x), ">" );
   end );

InstallMethod( JordanDesignNormalizedAnnihilatorPolynomial,
    "generic method for designs",
    [ IsJordanDesignWithAngleSet ],
    function(D)
    local x, F, A;
    A := JordanDesignAngleSet(D );
    x := Indeterminate(Field(A), "x" );
    F := Product(List(A, a -> (x - a)/(1-a)) );
    return CoefficientsOfUnivariatePolynomial(F );
    end );

InstallMethod( JordanDesignNormalizedIndicatorCoefficients,
    "generic method for designs",
    [ IsJordanDesignWithAngleSet ],
    function(D)
    local x, r, d, Q, F, V, basis;
    r := JordanDesignRank(D );
    d := JordanDesignDegree(D );
    x := Indeterminate(Field(JordanDesignAngleSet(D)), "x" );
    Q := k -> Q_k_epsilon(k, 0, r, d, x );
    F := ValuePol(JordanDesignNormalizedAnnihilatorPolynomial(D), x );
    V := VectorSpace(Field(JordanDesignAngleSet(D)), List([0..Degree(F)], Q) );
    basis := Basis(V, List([0..Degree(F)], Q) );  
    return Coefficients(basis, F );
    end );

InstallMethod( JordanDesignSpecialBound,
    "generic method for designs",
    [ IsJordanDesignWithAngleSet and IsJordanDesignWithPositiveIndicatorCoefficients ],
    function(D)
    if Filtered(JordanDesignNormalizedIndicatorCoefficients(D), x -> x < 0) <> [] then 
        return fail; 
    fi;
    return 1/JordanDesignNormalizedIndicatorCoefficients(D)[1];
    end );

InstallMethod( JordanDesignAddCardinality, 
    "for designs with angle sets",
    [ IsJordanDesignWithAngleSet, IsInt ],
    function(D, v)
        local obj;
        SetJordanDesignCardinality(D, v );
        SetFilterObj(D, IsJordanDesignWithCardinality );
        if JordanDesignSpecialBound(D) = JordanDesignCardinality(D) then 
            SetFilterObj(D, IsSpecialBoundJordanDesign );
            JordanDesignStrength(D );
        fi;
        return D; 
    end );

InstallMethod( PrintObj,
    "for a design with cardinality",
    [ IsJordanDesignWithCardinality ],
    function(x)
        Print( "<design with rank ", JordanDesignRank(x), ", degree ", JordanDesignDegree(x), ", cardinality ", JordanDesignCardinality(x), ", and angle set ", JordanDesignAngleSet(x), ">" );
   end );

InstallMethod( JordanDesignStrength, 
    "method for designs with positive indicator coefficients",
    [ IsJordanDesignWithPositiveIndicatorCoefficients and IsJordanDesignWithCardinality and IsSpecialBoundJordanDesign ],
    function(D)
        local s, i, t, e;
        s := Size(JordanDesignAngleSet(D) );
        for i in [0..s] do 
            if JordanDesignIndicatorCoefficients(D)[i+1] = 1 then 
                t := s + i;
            fi;
        od;
        SetFilterObj(D, IsJordanDesignWithStrength );
        if 0 in JordanDesignAngleSet(D) then 
            e := 1;
        else 
            e := 0;
        fi;
        # Check for tightness, etc
        if t = 2*s - e then
            SetFilterObj(D, IsTightJordanDesign );
            return t;
        fi;
        if t >= 2*s - 2 then
            SetFilterObj(D, IsAssociationSchemeJordanDesign );
            return t;
        fi;
        return t;
    end );

InstallMethod( JordanDesignAnnihilatorPolynomial, 
    "generic method for designs",
    [ IsJordanDesignWithAngleSet and IsJordanDesignWithCardinality ],
    function(D)
        return JordanDesignCardinality(D)*JordanDesignNormalizedAnnihilatorPolynomial(D );
    end );

InstallMethod( JordanDesignIndicatorCoefficients, 
    "generic method for designs",
    [ IsJordanDesignWithAngleSet and IsJordanDesignWithCardinality ],
    function(D)
        return JordanDesignCardinality(D)*JordanDesignNormalizedIndicatorCoefficients(D );
    end );

InstallMethod( PrintObj,
    "for a design with angle set and strength",
    [IsJordanDesignWithAngleSet and IsJordanDesignWithStrength],
    function(x)
    local text;
    Print( "<", JordanDesignStrength(x), "-design with rank ", JordanDesignRank(x), ", degree ", JordanDesignDegree(x), ", cardinality ", JordanDesignCardinality(x), ", and angle set ", JordanDesignAngleSet(x), ">" );
   end );

InstallMethod( PrintObj,
    "for a tight design",
    [IsTightJordanDesign],
    function(x)
        Print( "<Tight ", JordanDesignStrength(x), "-design with rank ", JordanDesignRank(x), ", degree ", JordanDesignDegree(x), ", cardinality ", JordanDesignCardinality(x), ", and angle set ", JordanDesignAngleSet(x), ">" );
   end );

InstallMethod( JordanDesignSubdegrees, 
    "method for a regular scheme design",
    [ IsRegularSchemeJordanDesign and IsJordanDesignWithCardinality and IsJordanDesignWithAngleSet ],
    function(D)
        local rank, degree, v, A, f, s, mat, vec, i;
        v := JordanDesignCardinality(D );
        A := JordanDesignAngleSet(D );
        rank := JordanDesignRank(D );
        degree := JordanDesignDegree(D );
        s := Size(A );
        f := JordanDesignConnectionCoefficients(D)(s );
        # f := ConnectionCoefficients(rank, degree, s );
        mat := [];
        vec := [];
        for i in [0..s-1] do;
            Append(mat, [
                List(Set(A), a -> a^i)
            ] );
            Append(vec, [v*f[i+1][1] - 1] );
        od;
        return SolutionMat(TransposedMat(mat), vec );
    end );

InstallMethod( JordanDesignIntersectionNumbers, 
    "method for an association scheme design",
    [ IsAssociationSchemeJordanDesign ],
    function(D)
        local rank, degree, v, A, F, s, delta, mat, vec, i, j, temp, p, result, gamma, Convolution;
        v := JordanDesignCardinality(D );
        A := JordanDesignAngleSet(D );
        rank := JordanDesignRank(D );
        degree := JordanDesignDegree(D );
        s := Size(A );
        Convolution := function(rank, degree, i, j, x)
            local f, temp, q, y;
            y := Indeterminate(Rationals, "x" );
            q := JordanDesignQPolynomials(D );
            q := k -> ValuePol(JordanDesignQPolynomials(D)(k), y );
            f := JordanDesignConnectionCoefficients(D)(Maximum(i,j) );
            # f := ConnectionCoefficients(rank, degree, Maximum(i,j) );
            temp := List([0..Minimum(i,j)], k -> f[i+1][k+1]*f[j+1][k+1]*q(k) );
            temp := Sum(temp );
            temp := ValuePol(CoefficientsOfUnivariatePolynomial(temp), x );
            return temp;
        end;
        result := [];
        for gamma in A do 
            F := {i,j} -> Convolution(rank, degree, i, j, gamma );
            mat := [];
            vec := [];
            if gamma = 1 then delta := 1; else delta := 0; fi;
            for i in [0..s-1] do 
                for j in [0..s-1] do 
                    Append(mat, [
                        List(Tuples(A,2), a -> a[1]^i *a[2]^j)
                    ] );
                    Append(vec, [v*F(i,j) - gamma^i - gamma^j + delta] );
                    # Append(vec, [v*F(i,j)] );
                od;
            od;
            temp := SolutionMat(TransposedMat(mat), vec );
            p := [];
            for i in [0..s-1] do  
                Append(p, [temp{[1+i*s..s+i*s]}] );
            od;
            Append(result, [p] );
        od;
        for i in [1..s] do 
            result[i] := result[i]+IdentityMat(s+1)*0;
            result[i][i][s+1] := 1;
            result[i][s+1][i] := 1;
        od;
        # degree := DiagonalMat(Subdegrees(rank, degree, v, A)) + IdentityMat(s+1)*0;
        degree := DiagonalMat(JordanDesignSubdegrees(D)) + IdentityMat(s+1)*0;
        degree[s+1][s+1] := 1;
        Append(result, [degree] );
        return result;
    end );

InstallMethod( JordanDesignReducedAdjacencyMatrices, 
    "method for an association scheme design",
    [ IsAssociationSchemeJordanDesign ],
    function(D)
        local s;
        s := Size(JordanDesignAngleSet(D) );
        return List([1..s+1], i -> List([1..s+1], j -> List([1..s+1], k -> JordanDesignIntersectionNumbers(D)[k][i][j])) );
    end );


InstallMethod( JordanDesignBoseMesnerAlgebra, 
    "method for an association scheme design",
    [ IsAssociationSchemeJordanDesign ],
    function(D)
        local p, T, basis, space, coeffs, i, j, k;
        p := JordanDesignReducedAdjacencyMatrices(D );
        space := VectorSpace(Rationals, p );
        basis := Basis(space, p );
        T := EmptySCTable(Length(p), 0, "symmetric" );
        for i in [1..Length(p)] do 
            for j in [1..Length(p)] do 
                coeffs := Coefficients(basis, p[i]*p[j] );
                SetEntrySCTable(T, i, j, Flat(
                    List([1..Length(coeffs)], n -> 
                        [coeffs[n], n]
                    )
                    ) );
            od;
        od;
        return AlgebraByStructureConstants(Rationals, T, "A" );
    end );

InstallMethod( JordanDesignBoseMesnerIdempotentBasis,
    "method for a tight t-design",
    [ IsAssociationSchemeJordanDesign ],
    function(D)
        local i, A, s, v, temp, idempotents, epsilon, final;
        A := JordanDesignAngleSet(D );
        v := JordanDesignCardinality(D );
        s := Size(A );
        if 0 in A then 
            epsilon := 1;
        else 
            epsilon := 0;
        fi;
        idempotents := [];
        # The 0th idempotent
        final := Sum(Basis(JordanDesignBoseMesnerAlgebra(D)))/v;
        # The 1 to s-1 idempotents.
        for i in [1..s-1] do 
            temp := Sum(List([1..s], k -> ValuePol(JordanDesignQPolynomials(D)(i), A[k])*Basis(JordanDesignBoseMesnerAlgebra(D))[k]) ); 
            temp := temp + ValuePol(JordanDesignQPolynomials(D)(i), 1)*Basis(JordanDesignBoseMesnerAlgebra(D))[s + 1];
            temp := temp/v;
            Append(idempotents, [temp] );
        od;
        # The s idempotent.
        temp := One(idempotents) - Sum(idempotents) - final;
        Append(idempotents, [temp] );
        # The 0th idempotent.
        Append(idempotents, [final] );
        idempotents := Basis(JordanDesignBoseMesnerAlgebra(D), idempotents );
        return idempotents;
    end );


InstallMethod( JordanDesignFirstEigenmatrix, 
    "method for a design with association scheme",
    [ IsAssociationSchemeJordanDesign ],
    function(D)
        return List(CanonicalBasis(JordanDesignBoseMesnerAlgebra(D)), x -> Coefficients(JordanDesignBoseMesnerIdempotentBasis(D), x) );
    end );

InstallMethod( JordanDesignSecondEigenmatrix, 
    "method for a design with association scheme",
    [ IsAssociationSchemeJordanDesign ],
    function(D)
        return List(JordanDesignBoseMesnerIdempotentBasis(D), x -> Coefficients(CanonicalBasis(JordanDesignBoseMesnerAlgebra(D)), x))*JordanDesignCardinality(D );
    end );

InstallMethod( JordanDesignMultiplicities, 
    "method for a design with association scheme",
    [ IsAssociationSchemeJordanDesign ],
    function(D)
        local Q, zero; 
        Q := JordanDesignSecondEigenmatrix(D );
        zero := Size(JordanDesignAngleSet(D)) + 1;
        return List([1..zero], i -> Q[i][zero] );
    end );

InstallMethod( DesignValencies, 
    "method for a design with association scheme",
    [ IsAssociationSchemeJordanDesign ],
    function(D)
        local Pmat, zero; 
        Pmat := JordanDesignFirstEigenmatrix(D );
        zero := Size(JordanDesignAngleSet(D)) + 1;
        return List([1..zero], i -> Pmat[i][zero] );
    end );

InstallMethod( JordanDesignKreinNumbers, 
    # Definition in bannai_algebraic_2021 Theorem 2.23, page 61
    "method for a design with association scheme",
    [ IsAssociationSchemeJordanDesign ],
    function(D)
        local s, temp, mat, i, j, k, l, test;
        s := Size(JordanDesignAngleSet(D) );
        temp := [];
        for l in [1..s+1] do
            mat := List([1..s+1], i ->
                List([1..s+1], j -> 
                    (JordanDesignMultiplicities(D)[i]*JordanDesignMultiplicities(D)[j]/JordanDesignCardinality(D))
                    *
                    Sum(
                        List([1..s+1], v ->
                            (1/DesignValencies(D)[v]^2)*
                            JordanDesignFirstEigenmatrix(D)[v][i]*JordanDesignFirstEigenmatrix(D)[v][j]*ComplexConjugate(JordanDesignFirstEigenmatrix(D)[v][l])
                        )
                    )
                )
            );
            Append(temp, [mat] );
        od;
        # Test the result using theorem 2.22(7) on page 59.
        for i in [1..s+1] do 
            for j in [1..s+1] do
                for l in [1..s+1] do 
                    test := JordanDesignSecondEigenmatrix(D)[i][l]*JordanDesignSecondEigenmatrix(D)[j][l] = Sum(List([1..s+1], k -> temp[k][i][j]*JordanDesignSecondEigenmatrix(D)[k][l]) );
                    if test = false then return fail; fi;
                od;
            od;
        od;
        # If test passes, then return the result.
        return temp;     
    end );


# Leech Lattice Tools

InstallGlobalFunction( IsLeechLatticeGramMatrix, function(G)
# Using the classification of integral unimodular lattices, the Leech lattice is the rank 24 unimodular lattice with minimal norm 4.
    local shortest;
    # Confirm M is a basis for a 24 dimensional lattice.
    if not 
        (   
            IsOrdinaryMatrix(G) and 
            DimensionsMat(G) = [24,24] and 
            TransposedMat(G) = G and 
            ForAll(Flat(G), IsInt)
        )
      then 
        return false;
    fi;
    # Confirm integral lattice (i.e. the lattice is a sublattice of the dual lattice):
    if not Set(Flat(G), IsInt) = [true] then 
        return false;
    fi;
    # Confirm unimodular (i.e. the dual lattice is also a sublattice of the lattice );
    if not Determinant(G) = 1 then 
        return false;
    fi;
    # Confirm no vectors shorter than 4.
    shortest := ShortestVectors(G,3).norms;
    if not shortest = [] then 
        return false;
    fi;
    return true;
end );

InstallGlobalFunction( IsGossetLatticeGramMatrix, function(G)
# Using the classification of integral unimodular lattices, the Gosset lattice is the rank 8 unimodular lattice with minimal norm 2.
    local shortest;
    # Confirm M is a basis for a 8 dimensional lattice.
    if not 
        (   
            IsOrdinaryMatrix(G) and 
            DimensionsMat(G) = [8,8] and 
            TransposedMat(G) = G and 
            ForAll(Flat(G), IsInt)
        )
      then 
        return false;
    fi;
    # Confirm integral lattice (i.e. the lattice is a sublattice of the dual lattice):
    if not Set(Flat(G), IsInt) = [true] then 
        return false;
    fi;
    # Confirm unimodular (i.e. the dual lattice is also a sublattice of the lattice );
    if not Determinant(G) = 1 then 
        return false;
    fi;
    # Confirm no vectors shorter than 2.
    shortest := ShortestVectors(G,1).norms;
    if not shortest = [] then 
        return false;
    fi;
    return true;
end );

BindGlobal( "MOGLeechLatticeGeneratorMatrix", [
    [8,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0],
    [4,4,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0],
    [4,0,4,0, 0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0],
    [4,0,0,4, 0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0],
    [4,0,0,0, 4,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0],
    [4,0,0,0, 0,4,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0],
    [4,0,0,0, 0,0,4,0, 0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0],
    [2,2,2,2, 2,2,2,2, 0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0],
    [4,0,0,0, 0,0,0,0, 4,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0],
    [4,0,0,0, 0,0,0,0, 0,4,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0],
    [4,0,0,0, 0,0,0,0, 0,0,4,0, 0,0,0,0, 0,0,0,0, 0,0,0,0],
    [2,2,2,2, 0,0,0,0, 2,2,2,2, 0,0,0,0, 0,0,0,0, 0,0,0,0],
    [4,0,0,0, 0,0,0,0, 0,0,0,0, 4,0,0,0, 0,0,0,0, 0,0,0,0],
    [2,2,0,0, 2,2,0,0, 2,2,0,0, 2,2,0,0, 0,0,0,0, 0,0,0,0],
    [2,0,2,0, 2,0,2,0, 2,0,2,0, 2,0,2,0, 0,0,0,0, 0,0,0,0],
    [2,0,0,2, 2,0,0,2, 2,0,0,2, 2,0,0,2, 0,0,0,0, 0,0,0,0],
    [4,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0, 4,0,0,0, 0,0,0,0],
    [2,0,2,0, 2,0,0,2, 2,2,0,0, 0,0,0,0, 2,2,0,0, 0,0,0,0],
    [2,0,0,2, 2,2,0,0, 2,0,2,0, 0,0,0,0, 2,0,2,0, 0,0,0,0],
    [2,2,0,0, 2,0,2,0, 2,0,0,2, 0,0,0,0, 2,0,0,2, 0,0,0,0],
    [0,2,2,2, 2,0,0,0, 2,0,0,0, 2,0,0,0, 2,0,0,0, 2,0,0,0],
    [0,0,0,0, 0,0,0,0, 2,2,0,0, 2,2,0,0, 2,2,0,0, 2,2,0,0],
    [0,0,0,0, 0,0,0,0, 2,0,2,0, 2,0,2,0, 2,0,2,0, 2,0,2,0],
   [-3,1,1,1, 1,1,1,1, 1,1,1,1, 1,1,1,1, 1,1,1,1, 1,1,1,1]
    ]);

BindGlobal( "MOGLeechLatticeGramMatrix",
    List(MOGLeechLatticeGeneratorMatrix, x -> 
        List(MOGLeechLatticeGeneratorMatrix, y -> 
            x*y/8
            )
        )
    );

InstallGlobalFunction( OctonionLatticeByGenerators, function(gens, args...)
    local   A,      # The underlying octonion ring.
            B,      # The underlying octonion ring basis.
            G,      # The octonion gram matrix.
            obj;    # The resulting lattice object
    # Check that the inputs are correct (a list of equal length lists of octonions from the same algebra implementation in GAP).    
    if 
        not IsOctonionCollColl(gens) or # Needs to be a collection of octonion lists.
        not IsHomogeneousList(Flat([gens, args])) or # Ensure that the octonions belong to the same octonion algebra. 
        Length(Set(gens, Length)) > 1 # The lists need to be equal length 
    then 
        Display( "Usage: OctonionLatticeByGenerators( <gens> [, <G>[, <B>]]) where <gens> is a list of equal length octonion lists, optional <G> is a suitable octonion gram matrix, and optional <B> is a basis for the underlying octonion algebra." );
        return fail; 
    fi;
    # Construct the Z-module.
    obj := FreeLeftModule(Integers, gens );

    # Determine the octonion algebra.
    A := FamilyObj(One(Flat(gens)))!.fullSCAlgebra;
    SetUnderlyingOctonionRing(obj, A );
    # Determine the prefered basis for the octonion algebra.
    if Length(args) = 2 then 
        B := Basis(A, AsList(args[2]));
        SetUnderlyingOctonionRingBasis(obj, B);
    else 
        SetUnderlyingOctonionRingBasis(obj, CanonicalBasis(A));
    fi;
    # If no octonion gram matrix is supplied, provide the half the identity matrix.
    if Length(args) = 0 then 
        SetOctonionGramMatrix(obj, IdentityMat(Length(gens[1]))*One(A)/2 );
    else 
        G := args[1];
        if 
            not IsMatrix(G) or DimensionsMat(gens)[2] <> DimensionsMat(G)[1] 
        then
            Display( "Usage: OctonionLatticeByGenerators( <gens> [, <G>]) where <gens> is a list of equal length octonion lists and optional argument <G> is a suitable octonion gram matrix." );
            return fail;
        fi;
        SetOctonionGramMatrix(obj, G );
    fi;
    # Assign appropriate filters.
    SetFilterObj(obj, IsRowModule );
    SetFilterObj(obj, IsOctonionLattice );
    # Convert the generators into coefficient lists according to the canonical octonion ring basis.
    SetGeneratorsAsCoefficients(obj, 
        List(GeneratorsOfLeftOperatorAdditiveGroup(obj), x -> 
            OctonionToRealVector(UnderlyingOctonionRingBasis(obj), x)
        )
    );
    # Compute the LLLReducedBasisVectors.
    SetLLLReducedBasisCoefficients(obj, LLLReducedBasis(obj, GeneratorsAsCoefficients(obj)).basis );

    return obj;
end );

InstallMethod( ScalarProduct, 
    "for an octonion lattice",
    [ IsOctonionLattice, IsRowVector, IsRowVector ],
    function(L, x, y)
        local a, b, G;
        G := OctonionGramMatrix(L);
        # If x and y are octonion vectors
        if Length(Set([x,y,G], Length)) = 1 and 
            IsOctonionCollection(x) and 
            IsOctonionCollection(y) 
        then 
                return Trace( x*G*ComplexConjugate(y) );
        fi;
        # If x and y are coefficient vectors
        if IsHomogeneousList(Flat([x,y,GeneratorsAsCoefficients(L)])) and 
            Length(x) = Rank(L) and 
            Length(y) = Rank(L)
        then 
            a := RealToOctonionVector(UnderlyingOctonionRingBasis(L), x );
            b := RealToOctonionVector(UnderlyingOctonionRingBasis(L), y );
            return Trace( a*G*ComplexConjugate(b) );
        fi;
        # Otherwise return fail;
        return fail;
    end );

InstallMethod( GramMatrix,
    "For an octonion lattice", 
    [IsOctonionLattice], 
    function(L)
        return List(LLLReducedBasisCoefficients(L), x ->  List(LLLReducedBasisCoefficients(L), y -> ScalarProduct(L,x,y)) );
    end );

InstallMethod( Rank,
    "For an octonion lattice",
    [IsOctonionLattice],
    function(L)
        return Dimension(L);
    end );

InstallMethod( Dimension,
    "For an octonion lattice",
    [IsOctonionLattice],
    function(L)
        return Rank( GeneratorsAsCoefficients(L) );
    end );

InstallMethod( CanonicalBasis,
    "for an octonion lattice",
    [ IsOctonionLattice ],
    function( L )
    local B;
    B:= Objectify( NewType( FamilyObj( L ),
                                IsFiniteBasisDefault
                            and IsCanonicalBasis
                            and IsOctonionLatticeBasis
                            and IsAttributeStoringRep ),
                   rec() );
    SetUnderlyingLeftModule( B, L );
    SetUnderlyingOctonionRing( B, UnderlyingOctonionRing( L ) );
    return B;
    end );

InstallMethod( Basis,
    "for an octonion lattice",
    [ IsOctonionLattice ],
    CanonicalBasis );

InstallMethod( BasisVectors,
    "for canonical basis of a full row module",
    [ IsCanonicalBasis and IsOctonionLatticeBasis ],
    function( B )
        return List(LLLReducedBasisCoefficients(UnderlyingLeftModule( B ) ), 
            x -> RealToOctonionVector(UnderlyingOctonionRingBasis(UnderlyingLeftModule( B )), x)
        );
    end );

# Maybe include this function in a future release. Needs work.

# InstallMethod( TotallyIsotropicCode,
#     "For an octonion lattice",
#     [ IsOctonionLattice ],
#     function(L)
#         local lll_basis;
#         lll_basis := LLLReducedBasisCoefficients(L);
#         if Set(Flat(lll_basis), IsInt) = [true] and Set(Flat(GramMatrix(L)*Z(2))) = [Z(2)*0] then 
#             return VectorSpace(GF(2), lll_basis*Z(2) );
#         fi;
#         return fail;
#     end );

InstallMethod( \in,
    "for and octonion vector and lattice.",
    IsElmsColls,
    [ IsOctonionCollection and IsRowVector, IsOctonionLattice ],
    function( x, L )
        local A;
        A := FamilyObj(One(x))!.fullSCAlgebra;
        if A = UnderlyingOctonionRing(L) then 
            x := OctonionToRealVector(UnderlyingOctonionRingBasis(L), x );
            return ForAll(SolutionMat(LLLReducedBasisCoefficients(L), x), IsInt);
        fi;
        return fail;
    end );

InstallMethod( IsSublattice,
    "For octonion lattices",
    [ IsOctonionLattice, IsOctonionLattice ],
    function(L1, L2)
        if UnderlyingOctonionRing(L1) = UnderlyingOctonionRing(L2) then 
            if UnderlyingOctonionRingBasis(L1) = UnderlyingOctonionRingBasis(L2) then 
                return IsSublattice(LLLReducedBasisCoefficients(L1), LLLReducedBasisCoefficients(L2) );
            else 
                return ForAll(BasisVectors(Basis(L2)), x -> x in L1);
            fi;
        fi;
        return fail;
    end );

InstallMethod( IsSubset,
    "For octonion lattices",
    IsIdenticalObj,
    [ IsOctonionLattice, IsOctonionLattice ],
        IsSublattice
    );

InstallMethod( \=, 
    "For octonion lattices",
    IsIdenticalObj,
    [ IsOctonionLattice, IsOctonionLattice ],
    function(L1, L2)
        if IsSublattice(L1, L2) and IsSublattice(L2, L1) then 
            return true;
        fi;
        return false;
    end );

# Closure Functions

InstallGlobalFunction( Closure, function(gens, mult_func, opt...)
    local temp, l, closure_step;
    closure_step := function(gens, mult_func, opt...)
        local temp, x, y, z, pair, pairchooser;
        temp := Set(gens);
        if Length(opt) > 0 and opt[1] = true then 
            pairchooser := UnorderedTuples;
        else 
            pairchooser := Tuples;
        fi;
        for pair in pairchooser(gens,2) do
            x := pair[1];
            y := pair[2];
            z := mult_func(x,y );
            if not (z in temp) then
                AddSet(temp,z );
            fi;
        od;
        return Set(temp );
    end;
    if not IsHomogeneousList(gens) then return fail; fi;
    temp := Set(gens );
    l := 0;
    while Length(temp) <> l do
        l := Length(temp );
        if Length(opt) > 0 and opt[1] = true then
            temp := closure_step(temp,mult_func, true );
        else 
            temp := closure_step(temp,mult_func );
        fi;
    od;
    return Set(temp );
end );

InstallGlobalFunction( RandomElementClosure, function(gens, mult_func, opt...)
    local r, temp, N, n, prior, print_yes;
    temp := ShallowCopy(gens );
    if not IsHomogeneousList(gens) then return fail; fi;
    if Length(opt) > 0 then 
        N := opt[1];
        if Length(opt) > 1 then 
            print_yes := true;
        else 
            print_yes := false;
        fi;
    else 
        N := 1;
        print_yes := false;
    fi;
    n := 0;
    repeat 
        prior := ShallowCopy(temp );
        r := Random(temp );
        temp := Union(temp, List(temp, x -> mult_func(r,x)) );
        if print_yes then 
            Display(Length(temp) );
        fi;
        if temp = prior then 
            n := n+1;
        else 
            n := 0;
        fi;
    until n >= N;
    return temp;
end );

InstallGlobalFunction( RandomOrbitOnSets, function(a_set, start, f, opt...)
    local temp, r, same, limit, print, len;
    if not IsHomogeneousList(Flat([a_set, start])) then return fail; fi;
    if Length(opt)>0 then 
        limit := opt[1];
    else 
        limit := 2;
    fi;
    if Length(opt)>1 then 
        print := true;
    else 
        print := false;
    fi;
    temp := ShallowCopy(start );
    r := Random(a_set );
    same := 0;
    repeat 
        len := Length(temp );
        r := Random(a_set );
        temp := Union(temp, List(temp, x -> f(r,x)) );
        if len = Length(temp) then 
            same := same + 1;
        else 
            same := 0;
        fi;
        if print then 
            Display(len );
        fi;
    until same >= limit;
    return temp;
end );