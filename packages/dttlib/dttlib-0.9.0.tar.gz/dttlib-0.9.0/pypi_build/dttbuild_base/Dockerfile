FROM ghcr.io/pyo3/maturin
RUN yum -y install gcc
RUN yum -y install fftw3-devel
RUN yum -y install cyrus-sasl-devel
#RUN yum -y install llvm-toolset-7-clang-devel llvm-toolset-7-clang-libs clang
ADD https://git.ligo.org/cds/software/cr_tools/libcds/-/archive/0.1.4/libcds-0.1.4.tar.gz /libcds/libcds.tar.gz
RUN cd /libcds && tar xvf libcds.tar.gz && cd libcds* && mkdir .build && cd .build && cmake .. && make -j install
ADD https://git.ligo.org/cds/software/gds-sigp/-/archive/1.0.3/gds-sigp-1.0.3.tar.gz /gds-sigp/gds-sigp.tar.gz
RUN cd /gds-sigp && tar xvf gds-sigp.tar.gz && cd gds-sigp* && mkdir .build && cd .build && cmake .. && make -j install
RUN pip3.9 install libclang
RUN yum -y install cmake
COPY build_clang.sh /build_clang.sh
ADD https://github.com/llvm/llvm-project/archive/refs/tags/llvmorg-20.1.5.tar.gz /clang/llvmorg.tar.gz
RUN cd /clang && tar xvf llvmorg.tar.gz
RUN  bash /build_clang.sh
