[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
# DTT
A frequency-domain analysis tool for LIGO data.

# C library dependencies

The following static LIGO libraries are required:

libcds
libgds-sigp

The following static third party libraries are required:
libfftw3
libglib-2.0
libstdc++

Additionally, the following dynamic libraries need
to be installed for building and running:

libsasl2
libz
libexpat

# Building as python module.

From the command line, build with 

```aiignore
maturin develop --features python,python-pipe,nds
```

