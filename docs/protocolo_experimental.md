# Protocolo experimental — v0.1 (rascunho para aprovação)

Jira: NATASHA-26. Escrito em 10/10/2026 a partir das leituras (`docs/leituras/`) e do código dos algoritmos. **Os itens marcados com [decidir] precisam do orientador.** A implementação está em `experiments/`.

## 1. Perguntas
1. **Reprodução:** reproduzimos os números do QueensCAMP para ORB-SLAM2 (RGB-D) e TartanVO? (objetivo específico 1)
2. **Robustez relativa:** quanto cada método degrada, **em relação à sua própria condição original**, sob as 6 falhas de lente e os 3 níveis de fumaça?
3. **Falha × deriva:** a degradação aparece como perda de rastreamento ou como deriva acumulada? (Thomas et al., 2026)

## 2. Métodos e configuração
| ID | Método | Entrada | Configuração | Repetições |
|---|---|---|---|---|
| `orbslam2_mono` | ORB-SLAM2 (f2e6f51) | monocular | **loop closure desligado** (patch `ORBSLAM2_NO_LOOP`), 1000 ORB, ritmo de tempo real | 5 |
| `orbslam2_rgbd` | ORB-SLAM2 | RGB-D | igual, profundidade em mm; **configuração do artigo do QueensCAMP** | 5 |
| `tartanvo` | TartanVO (python3, ec2ecc3) | monocular | crop central 640×448, intrínsecos do QueensCAMP, passos normalizados | 2 |
| `dpvo` | DPVO (0ac95b6) | monocular | `config/default.yaml`, **stride 1** (o demo usa 2), sem loop closure | 5 |
| `droidvo` | DROID-SLAM (2dfd39f) | monocular | só frontend (BA global desligado), stride 1. **Reserva:** só se o DPVO não compilar | 5 |

**Por que repetir o ORB-SLAM2:** RANSAC e threads tornam o resultado não determinístico, e os próprios autores usam mediana de 5. O DPVO amostra patches aleatórios (mediana de 5 no artigo). O TartanVO é determinístico na inferência; 2 execuções só confirmam isso.

## 3. Condições (10) e dados
- **Originais e falhas do QueensCAMP (7):** original, subexposição (γ = 2), superexposição (γ = 0,5), quebra, molhada, condensação, sujeira. Já vêm prontas no download *Full Sequence*.
- **Fumaça (3):** Koschmieder homogêneo com V = 60 / 20 / 6 m (β = 3,912/V), A = (0,8; 0,8; 0,8) provisório e buracos de profundidade preenchidos por dilatação (`smoke_emulation/`). A transmissão média de cada sequência fica registrada (ver `docs/nota_niveis_fumaca.md`).
- **Baseline com dehazing (Sprint 8, NATASHA-17):** DCP aplicado às 3 condições de fumaça **e à original** (controle do efeito do DCP sem fumaça).
- **16 sequências.** Analisar também por estrato: dinâmicas (01, 04–07), pouca luz (14–16) e estáticas.

## 4. Métricas
| Métrica | Como |
|---|---|
| Taxa de rastreamento | quadros com pose associada ao ground truth / quadros de entrada |
| ATE RMSE | monocular: **Sim(3)** [decidir: ou escala por passo]; RGB-D: **SE(3)** |
| ATE com escala por passo | todos os monoculares; **obrigatória para o TartanVO** (ver abaixo) |
| RPE | Δ = 1 s (15 quadros): translação (m e % do deslocamento) e rotação (°) |
| Latência | ms por quadro (média e mediana), medida dentro do wrapper |
| Memória GPU | pico do `torch.cuda.max_memory_allocated` + amostragem do `nvidia-smi` |

**Escala do TartanVO:** sem o arquivo de poses, a translação de cada passo tem magnitude arbitrária (a perda de treino é até-escala). O script oficial, e provavelmente o QueensCAMP, **substitui a norma de cada passo pela do ground truth**. Um Sim(3) com escala única não resolve isso. Por isso o `evaluate.py` calcula a "ATE com escala por passo" para todos os monoculares (a mesma ajuda para todos). Nos testes sintéticos, essa métrica amplifica ruído quadro a quadro, então **não deve ser a única métrica**.

**Falha × deriva:** uma execução é **falha** se o processo cai ou dá timeout, ou se o rastreamento fica abaixo de 50% (mesma regra do QueensCAMP). ATE e RPE só são agregados nas execuções que não falharam. A taxa de falha é reportada à parte.

## 5. Critério de robustez [decidir]
O critério da proposta, "ATE < 0,3 m e rastreamento > 80% em ≥ 75% das sequências", é **inatingível na condição original**: no artigo do QueensCAMP o ORB-SLAM2 RGB-D fica abaixo de 0,3 m em 8 de 16 sequências e o TartanVO em **0 de 16**. Proposta:
- **Principal (relativo):** o método é robusto a uma condição se (i) rastreamento ≥ 80% em ≥ 75% das sequências **e** (ii) a mediana da degradação do ATE em relação à própria condição original for ≤ X% (sugestão: X = 50).
- **Secundário (absoluto):** manter ATE < 0,3 m apenas como informação descritiva.

## 6. Estatística (etapa 5 da proposta)
- **Unidade de análise:** sequência (mediana das repetições), n = 16 pareado.
- **Comparação entre métodos por condição:** Wilcoxon pareado sobre a **degradação relativa**, com correção de Bonferroni e IC 95% por bootstrap (10.000 reamostragens).
- **Efeito de cada condição dentro do método:** Wilcoxon pareado entre original e condição.

## 7. Custo estimado
| Método | Horas (10 condições) | Recurso |
|---|---|---|
| DPVO (~60 fps, 5 rep.) | ~6,6 h | GPU |
| TartanVO (~25 fps, 2 rep.) | ~6,3 h | GPU |
| ORB-SLAM2 mono (tempo real, 5 rep.) | ~26 h | CPU |
| ORB-SLAM2 RGB-D (tempo real, 5 rep.) | ~26 h | CPU |

São **2.720 execuções**. As de GPU e as de CPU podem rodar em paralelo (dois `run_matrix.py` com `--algorithms` diferentes). Para a fumaça gerada, reservar ~38 GB de disco. **Medir o tempo real no spike (NATASHA-25) e corrigir a tabela.**

## 8. Reprodutibilidade
- Versões fixadas: commits dos algoritmos, imagens Docker com `pip freeze` em `/opt/pip-freeze.txt`, commit deste repositório em cada `meta.json`.
- Sementes registradas; logs completos por execução; crashes contados (Bujanca et al. relatam segfault > 10% no ORB-SLAM2).
- Dados, trajetórias e resultados ficam fora do git (`/data/...`); os resultados finais vão para o repositório aberto no fim do projeto (NATASHA-21).

## 9. Decisões pendentes
1. Métrica principal dos monoculares: Sim(3) ou escala por passo.
2. Critério de robustez relativo e o valor de X.
3. Manter o ORB-SLAM2 em ritmo de tempo real (fiel aos exemplos oficiais, ~53 h) ou sem ritmo (mais rápido; o mapeamento local pode ficar para trás).
4. Adotar o SLAM Adversarial Lab (Koschmieder já implementado) ou manter o módulo próprio; ver `docs/trabalhos_relacionados.md`.
