FROM condaforge/linux-anvil-cos7-x86_64:latest
COPY dttbuild.yaml /dttbuild.yaml
RUN /opt/conda/bin/mamba env create --yes --file /dttbuild.yaml --prefix /opt/conda/envs/dttbuild
