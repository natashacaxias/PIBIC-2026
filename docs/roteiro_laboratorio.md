# Roteiro do laboratório

Roteiro prático para a máquina com a RTX 5070 Ti. Detalhes técnicos em [`../experiments/README.md`](../experiments/README.md) e [`ambiente.md`](ambiente.md).

**Meta do primeiro dia:** GPU funcionando e uma execução válida do DPVO na sequência 09.

## Antes de ir
- [ ] Usuário na máquina com `sudo` (ou alguém que tenha) e acesso à internet.
- [ ] ~160 GB livres no total (~30 GB bastam no primeiro dia).
- [ ] Usar `tmux` para os processos longos não morrerem se a conexão cair.

## Primeiro dia

### 1. Conferir a máquina (5 min)
```bash
nvidia-smi              # driver precisa ser >= 570
docker --version
df -h
```
Se o Docker não enxergar a GPU: instalar o *NVIDIA Container Toolkit* (precisa de sudo).

### 2. Clonar o repositório e rodar os testes (10 min)
```bash
git clone https://github.com/natashacaxias/PIBIC-2026.git
cd PIBIC-2026/experiments
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python -m unittest discover -s tests
```

### 3. Montar a imagem do DPVO primeiro (20–40 min, a mais arriscada)
Rodar dentro do tmux:
```bash
docker build -t pibic/dpvo:0ac95b6 algorithms/dpvo 2>&1 | tee build_dpvo.log
```

### 4. Enquanto a imagem monta, baixar a sequência 09 (~4,2 GB)
```bash
.venv/bin/python scripts/dataset.py download --dest /data/queenscamp_raw --sequences 09 --kind full
# extrair em /data/queenscamp/09 e então:
.venv/bin/python scripts/dataset.py inspect /data/queenscamp/09
```

### 5. Preencher o `config/experiment.json` com o que o `inspect` mostrar
- [ ] `depth_dir`, `timestamps_file`, `groundtruth_file`.
- [ ] `rgb_dir` de cada falha (os campos `PREENCHER_...`).
- [ ] `depth_scale`: o valor cuja mediana de profundidade fica entre 1 e 5 m.
- [x] **Intrínsecos — não reescalar.** O `rgb_camera_info.txt` do site **já está em 640×480** (K = fx 465,63; fy 620,89; cx 323,66; cy 234,40), com o resize anisotrópico de 1920×1080 aplicado (fx×3 e fy÷0,444 dão ambos ≈ 1397). Usar os valores como estão; aplicar `640/1920` e `480/1080` de novo contaria a escala duas vezes.

### 6. Testar a GPU
```bash
bash scripts/check_gpu.sh pibic/dpvo:0ac95b6
```
Tem que terminar com "GPU pronta". Se aparecer `no kernel image`, mandar o log.

### 7. Piloto: uma única execução
```bash
.venv/bin/python scripts/run_matrix.py --algorithms dpvo --sequences 09 --conditions original --max-runs 1
.venv/bin/python scripts/evaluate.py
.venv/bin/python scripts/figures.py --trajectory /data/pibic_runs/dpvo/09/original/seed0
```
- [ ] `results/metrics.csv`: `status = ok` e fração rastreada perto de 1.
- [ ] Figura da trajetória com formato parecido com o do ground truth.

## Se sobrar tempo

### 8. Imagens do TartanVO e do ORB-SLAM2 + reprodução do QueensCAMP
```bash
docker build -t pibic/tartanvo:ec2ecc3 algorithms/tartanvo 2>&1 | tee build_tartanvo.log
docker build -t pibic/orbslam2:f2e6f51 algorithms/orbslam2 2>&1 | tee build_orbslam2.log
.venv/bin/python scripts/run_matrix.py --algorithms orbslam2_rgbd tartanvo --sequences 09 \
    --conditions original underexposure overexposure breakage wet condensation dirt
.venv/bin/python scripts/evaluate.py
```
Referência do artigo na sequência 09, condição original: **ORB-SLAM2 RGB-D = 0,15 m** e **TartanVO = 0,45 m**. Para o TartanVO, comparar com a coluna `ate_stepscale_m`. A tabela completa está em [`leituras/2024_bruno_queenscamp.md`](leituras/2024_bruno_queenscamp.md).

### 9. Gerar a fumaça e olhar as imagens
```bash
.venv/bin/python scripts/dataset.py smoke --sequences 09
```
Abrir alguns quadros dos três níveis e anotar a transmissão média que aparece na saída.

## O que anotar e mandar
- [ ] Tabela "Registro" do [`ambiente.md`](ambiente.md): driver, torch, arquiteturas, tempo por quadro e memória.
- [ ] Commit e push do `config/experiment.json` preenchido (nomes reais das pastas e intrínsecos).
- [ ] Se algo falhar: `build_*.log` ou o `stdout.log` da pasta da execução.
- [ ] Comentário no Jira (NATASHA-9, 10, 24, 25) com o que funcionou.

## Depois que o piloto funcionar
```bash
.venv/bin/python scripts/dataset.py download --dest /data/queenscamp_raw --kind full   # ~93 GB restantes
.venv/bin/python scripts/dataset.py smoke
# no tmux, GPU e CPU em paralelo (~13 h de GPU e ~53 h de CPU):
.venv/bin/python scripts/run_matrix.py --algorithms dpvo tartanvo > gpu.log 2>&1
.venv/bin/python scripts/run_matrix.py --algorithms orbslam2_mono orbslam2_rgbd > cpu.log 2>&1
# ao final:
.venv/bin/python scripts/evaluate.py && .venv/bin/python scripts/stats_analysis.py && .venv/bin/python scripts/figures.py
```
Se cair, é só rodar o mesmo comando de novo: execuções concluídas são puladas.

## Cuidados
- Não rodar duas matrizes de GPU ao mesmo tempo: isso distorce o tempo e a memória medidos.
- Dados, trajetórias e resultados ficam em `/data`, nunca no git.
- Não mudar o `config` no meio de uma matriz sem fazer commit; o `meta.json` de cada execução registra o commit usado.
