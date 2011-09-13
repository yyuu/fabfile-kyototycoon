# fabfile-kyototycoon

## Overview

Fabric recipe to install Kyoto Tycoon.


## Requirements

* Fabric

You may need other packages from Kyoto Tycoon.


## Operations

Install required packages.

  % pip install -r packages.txt


And then try to "setup" to build and upload binaries.

  % fab -H localhost setup


## Known problems

* you must setup an account "deploy" on target host first.
* source host and target host should have binary compatibility.
