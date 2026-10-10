# DROID-SLAM (alternativa ao DPVO) para CUDA 12.8 + PyTorch 2.7 (RTX 5070 Ti, sm_120).
# O README oficial diz "tested up to torch 2.7". Precisa de >= 11 GB de GPU no demo.
# Build: docker build -t pibic/droidslam:2dfd39f experiments/algorithms/droidslam
FROM nvidia/cuda:12.8.1-devel-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive \
    PIP_NO_CACHE_DIR=1 \
    TORCH_CUDA_ARCH_LIST="12.0" \
    TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD=1

RUN apt-get update && apt-get install -y --no-install-recommends \
        python3 python3-pip python3-dev git ca-certificates libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install torch==2.7.1 torchvision==0.22.1 torchaudio==2.7.1 --index-url https://download.pytorch.org/whl/cu128
RUN git clone --recursive https://github.com/princeton-vl/DROID-SLAM.git /opt/DROID-SLAM \
    && cd /opt/DROID-SLAM && git checkout 2dfd39f0dcad44012ca7bbb8aa70b55edbfa9c99 && git submodule update --init --recursive
WORKDIR /opt/DROID-SLAM
RUN pip3 install "numpy<2" tqdm evo scipy gdown opencv-python-headless pyyaml \
    && pip3 install --no-build-isolation thirdparty/lietorch thirdparty/pytorch_scatter \
    && pip3 install --no-build-isolation -e .
RUN gdown 1PpqVt1H4maBa_GbPJp4NwxRsd9jk-elh -O /opt/DROID-SLAM/droid.pth

RUN pip3 freeze > /opt/pip-freeze.txt
COPY run_droid.py /opt/run_droid.py
ENTRYPOINT ["python3", "/opt/run_droid.py"]
