### Process of classification

For history and science repeatability purposes, we keep _clauses_ and _formulas_ for `mace4` / `prover9`. 
Although, a complete antimagmas enumeration is already 
available in the package.

To classify all antimagmas, one can use `mace4`.

```
mace4 < ./.prover9/antimagma.in
```

To classify all antimagmas up to the isomorphism.

```
mace4 < ./.prover9/antimagma.in | interpformat standard > antimagma.interps
isofilter < antimagma.interps > antimagma.interps_uptoisomorphism
```