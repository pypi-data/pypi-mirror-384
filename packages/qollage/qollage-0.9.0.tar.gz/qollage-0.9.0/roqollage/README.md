# roqollage

[![Crates.io](https://img.shields.io/crates/v/roqollage)](https://crates.io/crates/roqollage)
[![GitHub Workflow Status](https://github.com/HQSquantumsimulations/qollage/workflows/ci_tests/badge.svg)](https://github.com/HQSquantumsimulations/qollage/actions)
[![docs.rs](https://img.shields.io/docsrs/roqollage)](https://docs.rs/roqollage/)
![Crates.io](https://img.shields.io/crates/l/roqollage)

Typst interface for the roqoqo quantum toolkit by [HQS Quantum Simulations](https://quantumsimulations.de).

roqollage provides the circuit_to_image function that allows users translate a roqoqo circuit into a DynamicImage of the circuit's representation.  
Not all roqoqo operations have a corresponding Typst expression.  
Circuits containing operations without a corresponding expression can not be translated.

## General Notes

This software is still in the beta stage. Functions and documentation are not yet complete and breaking changes can occur.

## Contributing

We welcome contributions to the project. If you want to contribute code, please have a look at CONTRIBUTE.md for our code contribution guidelines.
