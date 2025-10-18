# RDF Helpers

This is a python package that contains all kinds of useful functionality when building RDF applications with [RDFLib](https://rdflib.dev/):
- Various ways to manipulate RDF graphs (shortcuts, really)
- Predefined graph transformations (e.g., containers --> repeated properties)
- Templated queries (substitution not limited to RDF terms like in RDFLib with `initBindings`)
- Templated graph creation (based on SPARQL `CONSTRUCT`)
- Journaled graphs
- Label caching
- etc.

Available to install [from PyPI](https://pypi.org/project/rdfhelpers/). Documentation can be found [here](https://smasw.gitlab.io/software/rdfhelpers/).

## Changes in the 0.7.x release

Main theme: we folded `rdfproducers` into this.

Changes:
+ All old code moved into subpackage `rdfhelpers.core`.
  + `rdfhelpers.rdfhelpers` is now `rdfhelpers.core.basics`.
+ New subpackage `rdfhelpers.experimental`.
  + Class `Constructor` is not necessarily stable yet, so `rdfhelpers.constructor` became `rdfhelpers.experimental.constructor`, and the class does not get exported in the top level.
+ Added more typing annotations.
+ Attempting to call `Composable.validate()` without `pyshacl` being installed now raises an exception (earlier it merely logged a warning).
+ Added methods to `Composable` to bring it closer to the `rdflib.Graph` class.
+ New package `rdfhelpers.producers`.

## Contact

Author: Ora Lassila <ora@somanyaircraft.com>

Copyright (c) 2022-2025 Ora Lassila and [So Many Aircraft](https://www.somanyaircraft.com/)
