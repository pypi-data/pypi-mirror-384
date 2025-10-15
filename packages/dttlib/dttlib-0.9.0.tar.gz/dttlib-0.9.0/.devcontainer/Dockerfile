FROM debian:bullseye-slim
ENV DEBIAN_FRONTEND=noninteractive
RUN apt update
RUN apt install -y python3-pip
#RUN curl -LsSf https://astral.sh/uv/install.sh | sh
RUN pip install uv
RUN apt-get install -y wget
RUN wget https://apt.ligo-wa.caltech.edu/debian/pool/bullseye-unstable/cdssoft-release-bullseye/cdssoft-release-bullseye.deb
RUN apt install ./cdssoft-release-bullseye.deb
RUN apt update
RUN apt install -y nds2-client-dev
RUN apt install -y gcc clang libclang-dev fftw3-dev libsasl2-dev rapidjson-dev cmake
RUN apt install -y pkgconf
RUN apt install -y libglib2.0-dev
#ARG LIBCDS_VER=0.1.4
#ADD https://git.ligo.org/cds/software/cr_tools/libcds/-/archive/${LIBCDS_VER}/libcds-${LIBCDS_VER}.tar.gz /libcds/libcds.tar.gz
#RUN cd /libcds && tar xvf libcds.tar.gz && cd libcds* && mkdir .build && cd .build && cmake .. && make -j install
ARG GDSSIGP_VER=1.0.3
ADD https://git.ligo.org/cds/software/gds-sigp/-/archive/${GDSSIGP_VER}/gds-sigp-${GDSSIGP_VER}.tar.gz /gds-sigp/gds-sigp.tar.gz
RUN cd /gds-sigp && tar xvf gds-sigp.tar.gz && cd gds-sigp* && mkdir .build && cd .build && cmake -DCMAKE_INSTALL_PREFIX=/usr .. && make -j install
RUN apt-get -y install git curl
RUN apt-get install -y nano krb5-user

RUN apt-get install -y python3-venv

# needed for exports
RUN apt-get install -y libhdf5-dev

RUN groupadd -g 45517 erik.vonreis
RUN useradd -ms /bin/bash -u 45517 -g 45517 erik.vonreis

ADD https://sh.rustup.rs /home/erik.vonreis/rustup.sh
RUN chown 45517:45517 /home/erik.vonreis/rustup.sh

USER erik.vonreis
RUN sh /home/erik.vonreis/rustup.sh -y
RUN bash -c "source ~/.cargo/env && rustup default stable && cargo install cargo-bundle-licenses"

