# Ambiente da máquina do laboratório

Jira: NATASHA-9 (ambiente), NATASHA-25 (spike da GPU) e NATASHA-10 (algoritmos). Preparado em 10/10/2026 sem acesso à máquina e validado em 29/10/2026 no servidor do laboratório (ServidorIartes). As versões reais estão na seção "Registro" e os problemas encontrados em "Problemas encontrados no primeiro dia".

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
.venv/bin/python -m unittest discover -s tests          # 20 testes, sem GPU

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

## Problemas encontrados no primeiro dia
| Sintoma | Causa | Correção |
|---|---|---|
| `docker run --gpus all`: "failed to discover GPU vendor from CDI" | NVIDIA Container Toolkit ausente | instalado o toolkit 1.20.1 (precisa de sudo) |
| DPVO não compila: `no suitable conversion function from "const at::DeprecatedTypeProperties"` | PyTorch ≥ 2.7 removeu `Tensor::type()`, que o código original usa nos dispatches (`altcorr` e `lietorch`) | `sed` no Dockerfile troca `.type()` por `.scalar_type()` antes do `pip install` |
| DPVO falha no primeiro import: `No module named 'dpvo.loop_closure'` | a pasta não tem `__init__.py` no repositório, e o `find_packages()` a omite | `touch dpvo/loop_closure/__init__.py` no Dockerfile |
| `check_gpu.sh` dizia "GPU pronta" sem rodar o PyTorch | `docker run` sem `-i` não repassava o script ao Python | `-i` no `docker run` |
| TartanVO: `compile_with_cache` não existe | cupy 13 removeu `cupy.cuda.compile_with_cache`, usado nos kernels de correlação do PWC-Net | `cupy.RawModule(code=...)` no `correlation.py`, com `lru_cache` no lugar do memoize comentado |
| TartanVO: `as_dcm`/`from_dcm` não existem | o scipy atual os renomeou | `as_matrix`/`from_matrix` em todos os `.py` da imagem |
| ORB-SLAM2: o `git clone` do repositório trava | o pacote grande (vocabulário) para no meio em algumas redes e não é retomável | tarball do commit fixo (codeload), baixado do zero até vir íntegro (`gzip -t`), até 8 tentativas |
| ORB-SLAM2: includes inseridos no meio do `Optimizer.cc` | o arquivo começa com BOM UTF-8 | o patch remove o BOM antes de inserir `unistd.h` e `cstdlib` |
| `run_matrix.py`: a pasta de saída fica com dono root | o Docker cria como root a origem de montagem que não existe | `run_matrix.py` cria as pastas antes de montar |
| ORB-SLAM2 monocular na seq. 14 (original): código 139 e sem `trajectory_tum.txt` | o sistema ficou em NOT_INITIALIZED em todos os 831 quadros, sem keyframe, e o `SaveTrajectoryTUM` lê `vpKFs[0]` de um vetor vazio | é falha de rastreamento: `run_matrix.py` grava `status = not_initialized` (fração rastreada 0) quando todos os quadros do `frames.csv` ficam no estado 1 |

A profundidade tem mediana de 0,607 m e 49% de zeros, mas `depth_scale = 1000` está certo: o ORB-SLAM2 RGB-D reproduz o artigo (ATE 0,151 m com Sim3, escala 1,13), e um erro de unidade daria uma escala de ordens de grandeza.

Servidor compartilhado e matriz de ~55 h: a matriz limita cada container (`--memory` sem swap, `--cpus`, `--pids-limit`, `--cpu-shares 512`, sem core dump) e, antes de cada execução, espera sem abortar o host ficar dentro dos limites (CPU ≤ 85 °C, GPU ≤ 83 °C, RAM disponível ≥ 12 GiB, disco livre ≥ 100 GiB, GPU com ≥ 10 GB livres). Passados 360 min fora dos limites ela para e é retomável. `touch /data/pibic_runs/STOP` faz parar depois da execução em curso. Os valores vêm de `resources` no `config/experiment.json`, medidos na seq. 14: DPVO 2 GiB de RAM, 1 núcleo, 3,3 GB de GPU, ~180 W e 60 °C; TartanVO 1 GiB e todos os núcleos que tiver (com 8 a CPU chegou a 90 °C e com 4 a 91 °C junto de 2 fatias de ORB-SLAM2, então o teto dele é 2); ORB-SLAM2 0,4 GiB e ~0,6 núcleo por processo (4 em paralelo: ~3 núcleos e picos de 91 °C na CPU; a primeira medição, de 0,2 núcleo, pegou só o fim da execução).

**Como rodar a matriz sem forçar a máquina** (`bash scripts/matrix.sh start 2 | status | stop`): uma fila de GPU (TartanVO e depois DPVO, um processo de GPU por vez por causa do histórico de travamentos do driver) e 2 fatias do ORB-SLAM2 em CPU (`run_matrix.py --shard K/N`, estável entre reinícios). Estimativa: GPU ~20 h (DPVO ~15 h, TartanVO ~5 h) e ORB-SLAM2 ~30 h com 2 fatias (serial seriam ~59 h; com 3 fatias, ~20 h), então a matriz leva cerca de 30 h usando de 2 a 5 dos 24 núcleos. Os containers do ORB-SLAM2 não passam pelo runtime da NVIDIA. Teste de paralelismo (seq. 09, original): o RGB-D deu o mesmo com 4 em paralelo (ATE 0,318 e 0,339 m) e sozinho (0,312 a 0,339 m); o monocular varia muito de uma execução para outra mesmo sozinho (fração rastreada 0,59 a 0,85, ATE de 0,06 a 1,43 m em 6 execuções), então a concorrência não aparece acima desse ruído.

## Registro
Máquina: ServidorIartes, Ubuntu 24.04, 24 núcleos, 62 GB de RAM. O host é Ubuntu 24.04; as imagens usam Ubuntu 22.04 e 18.04.

| Item | Versão |
|---|---|
| GPU | RTX 5070 Ti, 16 GB, capability 12.0 |
| Driver NVIDIA | 595.99.02 (CUDA 13.2 no driver) |
| Docker / NVIDIA Container Toolkit | 29.9.2 / 1.20.1 |
| `torch.__version__` / `torch.version.cuda` (imagens DPVO e TartanVO) | 2.7.1+cu128 / 12.8 |
| Arquiteturas compiladas (`get_arch_list`) | sm_75, sm_80, sm_86, sm_90, sm_100, sm_120, compute_120 |
| Tempo por quadro DPVO (seq. 09, original, seed 0) | média 29,7 ms, mediana 31,8 ms (1284 quadros, 46,5 s no total) |
| Tempo por quadro TartanVO (seq. 09, original, seed 0) | média 22,5 ms, mediana 16,5 ms (1284 quadros, 35,7 s no total) |
| Pico de memória da GPU DPVO | 701 MiB alocados pelo PyTorch; 2531 MiB vistos pelo `nvidia-smi` acima da linha de base |
| Pico de memória da GPU TartanVO | 237 MiB alocados pelo PyTorch |
| Piloto DPVO seq. 09, original, seed 0 | `status = ok`, fração rastreada 1,0, ATE 0,232 m (Sim3, escala 0,214), RPE 0,384 m |
| Piloto TartanVO seq. 09, original, seed 0 | `status = ok`, fração rastreada 1,0, ATE 0,234 m (escala por passo) e 0,503 m (Sim3) |
| Piloto ORB-SLAM2 RGB-D seq. 09, original (5 sementes, mediana) | fração rastreada 1,0, ATE 0,321 m (SE3) e 0,151 m (Sim3, escala 1,13); 96 s por execução com `--realtime` |
| Piloto ORB-SLAM2 monocular seq. 09, original, seed 0 | `status = ok`, fração rastreada 0,588, ATE 0,060 m (Sim3, escala 3,23, só nos quadros rastreados) |
