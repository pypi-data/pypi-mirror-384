# IP Fabric Dynamic Attributes

Automation to create Attributes dynamically in IP Fabric.

## Overview

`ipf_dynamic_attributes` is a Python package designed to automate the creation and management of dynamic attributes in 
IP Fabric environments. It provides a flexible configuration system for defining rules, filters, and attribute mappings, 
enabling streamlined attribute synchronization and reporting.

## Features

* Define dynamic attribute rules using YAML, JSON, TOML or Python configuration.
* Support for static and calculated attribute values, including regex extraction and value mapping.
* Support for regex-based searching of device configs.
* Flexible filtering for inventory and device data. 
* Default dry-run mode for safe testing.
* Creates a pandas DataFrame for easy data manipulation and reporting.

## Requirements

* Python 3.9+
* IP Fabric version 7.2 or higher
* IP Fabric SDK version 7.2 or higher

## Installation

To install the `ipf_dynamic_attributes` package, you can use pip:

```bash
pip install ipf_dynamic_attributes
```

If you would like to output reports in Excel format, you can also install the `xlsxwriter` package:

```bash
pip install ipf_dynamic_attributes[excel]
```

## Documentation

Please refer to the [IP Fabric Dynamic Attributes Documentation](https://docs.ipfabric.io/main/integrations/dynamic-attributes/)
for detailed usage instructions, configuration examples, and advanced features.
