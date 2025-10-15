# iccore

This package is part of the [Common Tooling Project](https://ichec-handbook.readthedocs.io/en/latest/src/common_tools.html) at the [Irish Centre for High End Computing](https://www.ichec.ie).

It is a collection of common data structures, data types and low-level utilities used in other ICHEC 'common tools'.

# Features #

The package consists of:

* `data structures` (list, strings, dicts etc.) and utilities for working with them
* tooling for interacting with `system resources`, such as external processes, the filesystem and network
* basic database interaction tooling with sqmlmodel 

## Useful Data Types ##

* HPC and Networking: CPU, GPU, Process, SystemEvent, Node, ClusterAllocation, Host

## Filesystem ##

Utilities to find files with pattern matching and replace content inside files.

**CLI Example:**

You can replace all occurences of a string with another recursively in files with:

``` shell
iccore filesystem replace_in_files --target $REPLACE_DIR --search $FILE_WITH_SEARCH_TERM --replace $FILE_WITH_REPLACE_TERM 
```

The `search` and `replace` terms are read from files. This can be handy to avoid shell escape sequences - as might be needed in `sed`.

## Networking ##

Includes a:

* `HttpClient`

**CLI Example:**

You can download a file with:

``` shell
iccore network download --url $RESOURCE_URL --download_dir $WHERE_TO_PUT_DOWNLOAD
```

## Serialization ##

Tools for reading and writing ymal and json with some error handling.

# Install  #

It is available on PyPI:

``` sh
pip install iccore
```

# Copyright and License #

This software is copyright of the Irish Centre for High End Computing (ICHEC).

You may use it under the terms of GPLv3+ license. See the incluced `LICENSE.txt` file for details.
