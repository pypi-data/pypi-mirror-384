#!/bin/bash
set -e
source pypi_build/py_versions.sh

rm wheels/* || true

sdist="--sdist"

for pyver in $PYVERS
do
  docker run --rm -v $(pwd):/io -u erik.vonreis -v /home/erik.vonreis/projects/rust:/rust -w /io dttlib:dev uv build $sdist --wheel --python=$pyver --out-dir wheels
  sdist=""
done

