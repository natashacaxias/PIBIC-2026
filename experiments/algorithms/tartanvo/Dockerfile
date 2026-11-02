# TartanVO (branch python3) portado para CUDA 12.8 + PyTorch 2.7 (RTX 5070 Ti, sm_120).
# O código original foi testado com PyTorch 1.4 / CUDA 10; a correlação do PWC-Net usa cupy.
# Build: docker build -t pibic/tartanvo:ec2ecc3 experiments/algorithms/tartanvo
FROM nvidia/cuda:12.8.1-devel-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive \
    PIP_NO_CACHE_DIR=1 \
    TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD=1

RUN apt-get update && apt-get install -y --no-install-recommends \
        python3 python3-pip git wget ca-certificates libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install torch==2.7.1 torchvision==0.22.1 --index-url https://download.pytorch.org/whl/cu128
RUN pip3 install "numpy==1.26.4" "cupy-cuda12x>=13.4,<14" opencv-python-headless matplotlib scipy

RUN git clone -b python3 https://github.com/castacks/tartanvo.git /opt/tartanvo \
    && cd /opt/tartanvo && git checkout ec2ecc38b590ff27b76cc7818cf198d6420dce4b
# cupy >= 13 removeu cupy.cuda.compile_with_cache, que a correlação do PWC-Net usa.
# RawModule faz o mesmo; o lru_cache evita recompilar o kernel a cada quadro (o original memoizava com cupy.util.memoize).
RUN cd /opt/tartanvo/Network/PWC \
    && sed -i 's/return cupy\.cuda\.compile_with_cache(strKernel)\.get_function(strFunction)/return cupy.RawModule(code=strKernel).get_function(strFunction)/' correlation.py \
    && sed -i 's/^# @cupy\.util\.memoize(for_each_device=True)$/@functools.lru_cache(maxsize=None)/' correlation.py \
    && sed -i '1i import functools' correlation.py \
    && grep -n 'RawModule\|lru_cache\|^import functools' correlation.py
# scipy >= 1.6 renomeou Rotation.as_dcm/from_dcm para as_matrix/from_matrix.
RUN find /opt/tartanvo -name '*.py' -exec sed -i 's/\.as_dcm()/.as_matrix()/g; s/\.from_dcm(/.from_matrix(/g' {} +
RUN mkdir -p /opt/tartanvo/models \
    && wget -q https://cmu.box.com/shared/static/t1a5u4x6dxohl89104dyrsiz42mvq2sz.pkl -O /opt/tartanvo/models/tartanvo_1914.pkl

RUN pip3 freeze > /opt/pip-freeze.txt
COPY run_tartanvo.py /opt/run_tartanvo.py
WORKDIR /opt/tartanvo
ENTRYPOINT ["python3", "/opt/run_tartanvo.py"]
