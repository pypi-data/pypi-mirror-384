# formulate

[![Actions Status][actions-badge]][actions-link]
[![Documentation Status][rtd-badge]][rtd-link]

[![PyPI version][pypi-version]][pypi-link]
[![Conda-Forge][conda-badge]][conda-link]
[![PyPI platforms][pypi-platforms]][pypi-link]

[![GitHub Discussion][github-discussions-badge]][github-discussions-link]
[![Scikit-HEP][sk-badge]](https://scikit-hep.org/)

<!-- prettier-ignore-start -->
[actions-badge]:            https://github.com/scikit-hep/formulate/workflows/unittests/badge.svg
[actions-link]:             https://github.com/Scikit-HEP/formulate/actions
[conda-badge]:              https://img.shields.io/conda/vn/conda-forge/formulate
[conda-link]:               https://github.com/conda-forge/formulate-feedstock
[github-discussions-badge]: https://img.shields.io/static/v1?label=Discussions&message=Ask&color=blue&logo=github
[github-discussions-link]:  https://github.com/Scikit-HEP/formulate/discussions
[pypi-link]:                https://pypi.org/project/formulate/
[pypi-platforms]:           https://img.shields.io/pypi/pyversions/formulate
[pypi-version]:             https://img.shields.io/pypi/v/formulate
[rtd-badge]:                https://readthedocs.org/projects/formulate/badge/?version=latest
[rtd-link]:                 https://formulate.readthedocs.io/en/latest/?badge=latest
[sk-badge]:                 https://scikit-hep.org/assets/images/Scikit--HEP-Project-blue.svg

<!-- prettier-ignore-end -->

# Formulate

Easy conversions between different styles of expressions. Formulate
currently supports converting between
[ROOT](https://root.cern.ch/doc/master/classTFormula.html) and
[numexpr](https://numexpr.readthedocs.io/en/latest/user_guide.html)
style expressions.

## Installation

Install formulate like any other Python package, ideally inside a virtual environment:

```bash
pip install formulate
```

or using conda:

```bash
conda install -c conda-forge formulate
```

(`-c conda-forge` is only needed if you don't have the `conda-forge` channel already configured)

## Roadmap and releases

For the roadmap, planned features, breaking changes and versioning please see the [roadmap](https://github.com/scikit-hep/formulate/discussions/61).

## Usage

### API

The most basic usage involves calling `from_$BACKEND` and then `to_$BACKEND`, for example when starting with a ROOT style expression:

```pycon
>>> import formulate
>>> momentum = formulate.from_root("TMath::Sqrt(X_PX**2 + X_PY**2 + X_PZ**2)")
>>> momentum
Call(function='sqrt', arguments=[BinaryOperator(operator='add', left=BinaryOperator(operator='add', left=BinaryOperator(operator='pow', left=Symbol(name='X_PX'), right=Literal(value=2)), right=BinaryOperator(operator='pow', left=Symbol(name='X_PY'), right=Literal(value=2))), right=BinaryOperator(operator='pow', left=Symbol(name='X_PZ'), right=Literal(value=2)))])
>>> momentum.to_numexpr()
'sqrt((((X_PX ** 2) + (X_PY ** 2)) + (X_PZ ** 2)))'
>>> momentum.to_root()
'TMath::Sqrt((((X_PX ** 2) + (X_PY ** 2)) + (X_PZ ** 2)))'
```

Similarly, when starting with a `numexpr` style expression:

```pycon
>>> my_selection = formulate.from_numexpr("(X_PT > 5) & ((Mu_NHits > 3) | (Mu_PT > 10))")
>>> my_selection.to_root()
'((X_PT > 5) && ((Mu_NHits > 3) || (Mu_PT > 10)))'
>>> my_selection.to_numexpr()
'((X_PT > 5) & ((Mu_NHits > 3) | (Mu_PT > 10)))'
```

### CLI

The package also provides a command-line interface for converting expressions between different styles. To use it, simply run the `formulate` command followed by the input expression and the desired output.

```bash
$ formulate --from-root '(A && B) || TMath::Sqrt(A)' --to-numexpr
((A & B) | sqrt(A))

$ formulate --from-numexpr '(A & B) | sqrt(A)' --to-root
((A && B) || TMath::Sqrt(A))

$ formulate --from-root '(A && B) || TMath::Sqrt(1.23) * e_num**1.2 + 5*pi' --variables
A
B

$ formulate --from-root '(A && B) || TMath::Sqrt(1.23) * e_num**1.2 + 5*pi' --named-constants
exp1
pi

$ formulate --from-root '(A && B) || TMath::Sqrt(1.23) * e_num**1.2 + 5*pi' --unnamed-constants
1.23
1.2
5
```
