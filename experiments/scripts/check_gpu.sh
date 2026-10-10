#!/usr/bin/env bash
# Verifica driver, Docker com GPU e suporte da RTX 5070 Ti (sm_120) no PyTorch dos containers.
# Uso: bash scripts/check_gpu.sh [imagem_pytorch]   (padrão: pibic/dpvo:0ac95b6)
set -uo pipefail
IMAGE="${1:-pibic/dpvo:0ac95b6}"

echo "== Driver NVIDIA (precisa ser >= 570 para Blackwell/sm_120)"
nvidia-smi --query-gpu=name,driver_version,memory.total,compute_cap --format=csv || { echo "nvidia-smi falhou"; exit 1; }

echo; echo "== Docker com acesso à GPU (NVIDIA Container Toolkit)"
docker run --rm --gpus all nvidia/cuda:12.8.1-base-ubuntu22.04 nvidia-smi -L || {
  echo "Docker sem GPU: instale o nvidia-container-toolkit e reinicie o Docker"; exit 1; }

echo; echo "== PyTorch dentro de ${IMAGE}"
docker run --rm --gpus all --entrypoint python3 "${IMAGE}" - <<'EOF' || { echo "imagem ${IMAGE} indisponível ou sem suporte"; exit 1; }
import torch
print("torch", torch.__version__, "cuda", torch.version.cuda)
print("arquiteturas compiladas:", torch.cuda.get_arch_list())
name = torch.cuda.get_device_name(0)
cap = torch.cuda.get_device_capability(0)
print("GPU:", name, "capability", cap)
assert f"sm_{cap[0]}{cap[1]}" in torch.cuda.get_arch_list(), "PyTorch sem kernels para esta GPU"
x = torch.randn(1024, 1024, device="cuda")
print("teste matmul ok:", float((x @ x).sum()) == float((x @ x).sum()))
EOF
echo; echo "GPU pronta."
