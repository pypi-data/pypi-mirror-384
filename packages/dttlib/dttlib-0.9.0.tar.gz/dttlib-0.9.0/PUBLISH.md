# Publish to PyPi

Requires Docker

## building the container

dttlib is published to pypi from a customized container that
has the necessary third-party C libraries.



To build this container run `docker build -t dtt-build:deb pypi_build/dttbuild_debian`

This script adds several libraries to the container, including two LIGO libraries
that are compiles from source: libcds and gds-sigp

The version of these two libraries is set in the script.  Edit the
pypi_build/dttbuild_debian/Dockerfile, or pass `--build-arg LIBCDS_VER=...` or `--build-arg GDSSIGP_VER=...` to `docker build ...`

## Build all artifacts

delete everything in the `wheels` directory.

Then run ./pypi_build.sh

## Publish the wheels

`./pypi_upload.sh`

The source is too big to publish.




