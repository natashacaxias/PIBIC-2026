# DPVO para RTX 5070 Ti (Blackwell, sm_120): CUDA 12.8 + PyTorch 2.7 (cu128).
# Build: docker build -t pibic/dpvo:0ac95b6 experiments/algorithms/dpvo
FROM nvidia/cuda:12.8.1-devel-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive \
    PIP_NO_CACHE_DIR=1 \
    TORCH_CUDA_ARCH_LIST="12.0" \
    TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD=1

RUN apt-get update && apt-get install -y --no-install-recommends \
        python3 python3-pip python3-dev git wget unzip ca-certificates libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install torch==2.7.1 torchvision==0.22.1 --index-url https://download.pytorch.org/whl/cu128
# torch-scatter: tenta a roda pronta do PyG; se não houver para cu128, compila do código-fonte.
RUN pip3 install torch-scatter -f https://data.pyg.org/whl/torch-2.7.0+cu128.html \
    || pip3 install --no-build-isolation torch-scatter
RUN pip3 install "numpy==1.26.4" tensorboard numba tqdm einops pypose kornia plyfile evo opencv-python-headless yacs

RUN git clone --recursive https://github.com/princeton-vl/DPVO.git /opt/DPVO \
    && cd /opt/DPVO && git checkout 0ac95b656d1fda91c271d2a106460d19ad966fc7 && git submodule update --init --recursive
WORKDIR /opt/DPVO
# PyTorch >= 2.7 removeu Tensor::type() nos dispatches; o código original do DPVO ainda o usa.
# dpvo/loop_closure não tem __init__.py no repositório, então o find_packages() a deixa de fora.
RUN wget -q https://gitlab.com/libeigen/eigen/-/archive/3.4.0/eigen-3.4.0.zip \
    && unzip -q eigen-3.4.0.zip -d thirdparty && rm eigen-3.4.0.zip \
    && find dpvo -name '*.cu' -exec sed -i -E 's/(AT_DISPATCH_[A-Z_]*\(\s*[A-Za-z0-9_]+)\.type\(\)/\1.scalar_type()/' {} + \
    && find dpvo \( -name '*.cu' -o -name '*.cpp' \) -exec sed -i -E 's/(DISPATCH_GROUP_AND_FLOATING_TYPES\([A-Za-z0-9_]+,\s*[A-Za-z0-9_]+)\.type\(\)/\1.scalar_type()/' {} + \
    && sed -i 's/::detail::scalar_type(the_type)/the_type/' dpvo/lietorch/include/dispatch.h \
    && touch dpvo/loop_closure/__init__.py \
    && pip3 install --no-build-isolation .
# Só os pesos (o script oficial também baixa ~2 GB de dados de teste que não usamos).
RUN wget -q -O models.zip "https://www.dropbox.com/scl/fo/2g6e134ruh1acmaye5bmy/AK0DY9WLZ25elq-7N7sJcB0/models.zip?rlkey=4j336vcc4h324j4p4ji3ppl0t" \
    && unzip -q models.zip && rm models.zip && ls -l *.pth

RUN pip3 freeze > /opt/pip-freeze.txt
COPY pose_chain.py run_dpvo.py /opt/
ENTRYPOINT ["python3", "/opt/run_dpvo.py"]
