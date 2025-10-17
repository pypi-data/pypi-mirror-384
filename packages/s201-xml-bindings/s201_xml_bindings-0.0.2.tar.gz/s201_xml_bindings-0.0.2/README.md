# The Python S-201 XML Bindings Package

A python package implementing the XML bindings for the IALA S-201 data product
specification

## Introduction

This Python package provides language bindings for the IALA S-201 data product, 
making it easier for developers to work with S-100 datasets. These bindings
allow developers to programmatically interact with S-100-compliant datasets
and data models, supporting the creation of applications that need to process,
validate, and manipulate S-201 data.

The S-201 belongs to the S-100 framework family, a standard developed by the
International Hydrographic Organization (IHO), is the framework for electronic
navigational charts, hydrographic data, and other maritime-related geospatial
information. These bindings are designed to facilitate integration of S-100
data into modern applications without the complexity of directly handling
S-100 specifications.

***!!!BE CAREFUL!!!***

This software is only intended for test purposes and should ***NOT BE USED IN ANY
PRODUCTION*** environment.

## S-201 XML - Python Classes Generation

To generate the package you can run the **xsdata** generation command using the
config provided in the repo.

```bash
xsdata generate ../../../specifications/s-201/2.0.0/S-201.xsd --package grad.s201 --config .xsdata.xml --debug
```

Note that the configuration is fixed so that all the geneted classes are placed
under a single file. This handles the circular dependency issues. The you can
include generated **grad.s201** package into your software to parse and render
S-201 XML files.

## Packaging the Project

You can follow the great tutorial about packaging python projects [here](https://packaging.python.org/en/latest/tutorials/packaging-projects/)

## License
Distributed under the Apache License. See LICENSE.md for more information.

## Contact
Nikolaos Vastardis - Nikolaos.Vastardis@gla-rad.org