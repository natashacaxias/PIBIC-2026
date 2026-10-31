# Preparação para publicação do repositório — v0.1 (31/10/2026)

Jira: NATASHA-21. **Este documento não torna nada público e nada foi enviado para fora.** Ele registra a auditoria feita, a licença sugerida, a declaração de dados e o que falta decidir. Quem decide publicar, e quando, é a Natasha com o orientador.

## 1. Auditoria do que está versionado (31/10)
`git grep` nos arquivos versionados e `git log -p` em todo o histórico (2,2 MB), procurando chaves e *tokens* (padrões `ghp_`, `sk-`, `AKIA`, `api_key=`, `secret=`, `token=`, `password=`), e-mails, caminhos `/home/...` e endereços de rede:

| Item | Resultado |
|---|---|
| Chaves, *tokens*, senhas | **nenhum** nos arquivos nem no histórico; só `literature_review/.env.example`, sem valores |
| E-mails | nenhum |
| Caminhos pessoais (`/home/...`) | nenhum nos arquivos versionados |
| Nome do servidor (`ServidorIartes`) | aparece em `docs/ambiente.md` (2 vezes); decidir se mantém |
| Link do Jira | `README.md` aponta para o quadro NATASHA (exige login); manter ou trocar por texto |
| Tamanho | 716 KB de arquivos versionados; nenhum dado, trajetória nem imagem |

Fica fora do git por `.gitignore`: `datasets/`, `results/`, `literature_review/data|exports|outputs/`, `.venv/`, `*.docx` e os logs de build (`experiments/build_*.log`). Nos servidores: `/data/queenscamp` (104 GB), `/data/queenscamp_smoke` (33 GB), `/data/queenscamp_dcp`, `/data/pibic_runs` (execuções, 1,6 GB e crescendo) e `/data/subtmrs_raw` (9,25 GB, quadros reais do SubT-MRS).

## 2. Licença sugerida (não aplicada)
Não há arquivo `LICENSE` no repositório. Sugestão, **a confirmar com o orientador e com as regras de propriedade intelectual da UFAM/PIBIC e do SAGRES-Pro** (isto é orientação técnica, não parecer jurídico):

| Parte | Licença sugerida | Por quê |
|---|---|---|
| `experiments/` (exceto `algorithms/orbslam2/`), `smoke_emulation/`, `literature_review/` | **MIT** (ou Apache-2.0, se quiserem cláusula de patentes) | código próprio; MIT é a licença do DPVO e é simples para uso acadêmico |
| `experiments/algorithms/orbslam2/` (`patch_orbslam2.sh`, `queenscamp_runner.cc`) | **GPL-3.0-or-later**, com `LICENSE` na pasta | o runner é compilado e ligado ao ORB-SLAM2, que é GPLv3 (conferido em `/opt/ORB_SLAM2/LICENSE.txt` na imagem); o mais seguro é manter essa pasta sob a mesma licença |
| `docs/` (texto e figuras próprias) | **CC BY 4.0** | permite reuso com crédito |

Licenças dos algoritmos que as imagens Docker baixam (conferidas dentro das imagens em 31/10): ORB-SLAM2 GPLv3, TartanVO BSD 3-Clause, DPVO MIT. A do DROID-SLAM não foi conferida (a imagem é reserva e não foi construída). O repositório não redistribui o código deles; só os `Dockerfile` e os *patches*.

## 3. Declaração de dados (para o README e o artigo)
- O repositório **não contém dados**. As sequências do QueensCAMP são baixadas do site dos autores por `scripts/dataset.py download`; a licença do QueensCAMP **não foi conferida** (checar no site/artigo antes de publicar e citar corretamente).
- A **fumaça sintética** e o **dehazing** são gerados a partir do QueensCAMP por `dataset.py smoke` e `dataset.py dehaze`; as imagens geradas não são redistribuídas.
- Os **quadros reais do SubT-MRS** ficam de fora: a licença não é declarada na página dos autores (`docs/datasets.md`). Do SubT-MRS só entram métricas agregadas e o texto de validação; a Fig. 1 do artigo deve usar quadros sintéticos ou pedir permissão aos autores.
- Resultados publicáveis: os CSV agregados (`metrics.csv` 612 KB, `summary.csv` 102 KB, `stats_*.csv` e `stats_report.md`, ~30 KB) e as figuras próprias. **Trajetórias e logs das execuções ficam de fora** (volume).

## 4. O que falta antes de tornar público (checklist)
1. Orientador e UFAM aprovam publicar o código e escolhem a licença (seção 2). Depois: criar `LICENSE` na raiz e `experiments/algorithms/orbslam2/LICENSE`.
2. Conferir a licença do QueensCAMP e atualizar `docs/datasets.md` e o README.
3. Revisar o que entra: `docs/leituras/` (os fichamentos "precisam ser revisados pela Natasha antes de virar texto", `docs/leituras/README.md`), `docs/analise_concorrentes_2026.md` (avalia trabalhos de terceiros; revisar o tom), `docs/plano_inicial.md` e `docs/relatorio_parcial.md` (planejamento interno).
4. Depois que o DCP completo (NATASHA-43) fechar e o orientador confirmar as decisões de §10: rodar `evaluate.py`, `stats_analysis.py` e `figures.py` uma última vez e copiar os CSV e as figuras finais para `experiments/resultados_publicados/` (pasta nova, versionada; `results/` continua ignorado).
5. Preencher "Como citar" no README quando houver artigo ou relatório; marcar uma versão (por exemplo `v1.0`) e, se quiserem um DOI, arquivar essa versão num repositório de preprints/dados.
6. Decidir sobre o nome do servidor e o link do Jira (seção 1).
7. Só então mudar a visibilidade do repositório no GitHub. **Não feito.**
