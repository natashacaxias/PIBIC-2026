# Ambiente da máquina do laboratório

Jira: NATASHA-9 (ambiente) e NATASHA-25 (spike da GPU). Preparado em 10/10/2026 **sem acesso à máquina**: os passos abaixo ainda não foram executados. Ao rodar, anotar as versões reais na seção "Registro".

## Requisitos
| Item | Requisito | Por quê |
|---|---|---|
| SO | Ubuntu 22.04 | proposta |
| Driver NVIDIA | **≥ 570** | primeira série com suporte à Blackwell (RTX 50xx, sm_120) |
| Docker + NVIDIA Container Toolkit | atual | cada algoritmo roda no seu container |
| Disco | ~97 GB (QueensCAMP *Full*) + ~38 GB (fumaça) + imagens Docker (~25 GB) | |
| Python no host | 3.10+ com `experiments/requirements.txt` | orquestração e avaliação (evo) |

## Por que containers
- **ORB-SLAM2** só compila sem dor no ambiente original (Ubuntu 18.04, OpenCV 3.2, Pangolin 0.5).
- **DPVO, DROID-SLAM e TartanVO** precisam de CUDA ≥ 12.8 e PyTorch 2.7 para gerar kernels sm_120. As versões originais (CUDA 10–12.1, PyTorch 1.4–2.3) **não rodam na RTX 5070 Ti**.
- Cada imagem guarda `pip freeze` e fixa o commit do algoritmo.

## Passo a passo
```bash
# 1. Repositório e ambiente do host
git clone https://github.com/natashacaxias/PIBIC-2026.git && cd PIBIC-2026/experiments
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python -m unittest discover -s tests          # 10 testes, sem GPU

# 2. Imagens (a do DPVO compila extensões CUDA: ~20–40 min)
docker build -t pibic/dpvo:0ac95b6       algorithms/dpvo
docker build -t pibic/tartanvo:ec2ecc3   algorithms/tartanvo
docker build -t pibic/orbslam2:f2e6f51   algorithms/orbslam2
# docker build -t pibic/droidslam:2dfd39f algorithms/droidslam   # só se o DPVO falhar

# 3. Spike da GPU (NATASHA-25)
bash scripts/check_gpu.sh pibic/dpvo:0ac95b6
bash scripts/check_gpu.sh pibic/tartanvo:ec2ecc3
```

## Riscos conhecidos e saídas
| Sintoma | Causa provável | O que fazer |
|---|---|---|
| `no kernel image is available for execution on the device` | PyTorch ou extensão sem sm_120 | conferir `TORCH_CUDA_ARCH_LIST="12.0"` e rebuild sem cache |
| falha no `torch-scatter` | sem roda pronta para torch 2.7 + cu128 | o Dockerfile já cai para compilação do código-fonte; se falhar, testar `torch==2.8` com a roda do PyG correspondente |
| erro do cupy no TartanVO (NVRTC) | cupy sem NVRTC 12.8 | `pip install "cupy-cuda12x[ctk]"` na imagem |
| `weights_only` ao carregar `.pth`/`.pkl` | PyTorch ≥ 2.6 | já tratado com `TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD=1` |
| ORB-SLAM2 trava no fim | thread de loop | o patch mantém a thread viva; se travar, conferir com `docker logs` |
| link do Dropbox/Box/Drive fora do ar | pesos dos modelos | baixar manualmente e copiar para a imagem (`docker cp` ou `COPY`) |

**Se nada compilar em sm_120:** usar outra GPU do laboratório (Ampere/Ada com CUDA 12.1) com as versões originais dos autores, ou rodar só o DPVO e o TartanVO via Docker oficial deles. Registrar a decisão no Jira (NATASHA-25).

## Registro (preencher na máquina)
| Item | Versão |
|---|---|
| Driver NVIDIA | |
| Docker / NVIDIA Container Toolkit | |
| `torch.__version__` / `torch.version.cuda` (imagem DPVO) | |
| Arquiteturas compiladas (`get_arch_list`) | |
| Tempo por quadro DPVO / TartanVO (seq. 09) | |
| Pico de memória DPVO / TartanVO | |
