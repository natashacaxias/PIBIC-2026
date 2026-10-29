# ORB-SLAM2 (commit f2e6f51, 2017) no ambiente em que foi testado: Ubuntu 18.04 + OpenCV 3.2 + Pangolin 0.5.
# Roda em CPU; não depende da GPU. Patches em patch_orbslam2.sh.
# Build: docker build -t pibic/orbslam2:f2e6f51 experiments/algorithms/orbslam2
FROM ubuntu:18.04

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential cmake git pkg-config ca-certificates perl \
        libeigen3-dev libopencv-dev libglew-dev libgl1-mesa-dev libegl1-mesa-dev libwayland-dev libxkbcommon-dev \
        libboost-system-dev libboost-serialization-dev libpython2.7-dev \
    && rm -rf /var/lib/apt/lists/*

RUN git clone --depth 1 --branch v0.5 https://github.com/stevenlovegrove/Pangolin.git /opt/Pangolin \
    && mkdir /opt/Pangolin/build && cd /opt/Pangolin/build \
    && cmake .. -DCMAKE_BUILD_TYPE=Release -DBUILD_EXAMPLES=OFF -DBUILD_TESTS=OFF \
    && make -j"$(nproc)" && make install && ldconfig

# O `git clone` do ORB_SLAM2 trava no pacote grande (vocabulário) em algumas redes; o tarball do commit fixo é
# equivalente e é repetido do zero até vir íntegro (o codeload não aceita retomada).
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*
RUN set -e; mkdir -p /opt/ORB_SLAM2; \
    for i in 1 2 3 4 5 6 7 8; do \
        rm -f /tmp/orb.tgz; \
        curl -fsSL --max-time 240 --connect-timeout 15 -o /tmp/orb.tgz \
            https://codeload.github.com/raulmur/ORB_SLAM2/tar.gz/f2e6f51cdc8d067655d90a78c06261378e07e8f3 \
            && gzip -t /tmp/orb.tgz && break; \
        echo "download incompleto (tentativa $i)"; \
    done; \
    gzip -t /tmp/orb.tgz && tar -xzf /tmp/orb.tgz -C /opt/ORB_SLAM2 --strip-components=1 && rm /tmp/orb.tgz
COPY patch_orbslam2.sh queenscamp_runner.cc /tmp/
RUN bash /tmp/patch_orbslam2.sh /opt/ORB_SLAM2 /tmp/queenscamp_runner.cc \
    && cd /opt/ORB_SLAM2 && bash build.sh \
    && test -x /opt/ORB_SLAM2/queenscamp_runner

ENTRYPOINT ["/opt/ORB_SLAM2/queenscamp_runner"]
