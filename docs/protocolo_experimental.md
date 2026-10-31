# Protocolo experimental — v0.2 (decisões de 31/10 a confirmar com o orientador)

Jira: NATASHA-26. Escrito em 10/10/2026 a partir das leituras (`docs/leituras/`) e do código dos algoritmos. Os itens marcados com [decidir] foram decididos em 31/10, depois da matriz completa, a pedido da Natasha e **com Claude no papel de orientador** (§10); são decisões provisórias, com os dados que as sustentam, e **precisam ser confirmadas pelo orientador de verdade**. A implementação está em `experiments/`.

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
- **Baseline com dehazing (Sprint 8, NATASHA-17):** DCP (patch 15, ω = 0,95, t₀ = 0,1, guided filter r = 60) aplicado às 3 condições de fumaça **e à original** (controle do efeito do DCP sem fumaça). São 4 condições `dcp_*` desligadas por padrão no `experiment.json`. **A é estimado uma vez por sequência** (mediana), para não introduzir oscilação de brilho entre quadros. Limitação conhecida: em cena interna rasa nenhuma região fica opaca, e a estimativa de A puxa a cor da cena (verificado nos testes de `smoke_emulation/tests/test_dcp.py`). Implementação em `smoke_emulation/dcp.py`; geração com `dataset.py dehaze`.
- **16 sequências.** Analisar também por estrato: dinâmicas (01, 04–07), pouca luz (14–16) e estáticas.

## 4. Métricas
| Métrica | Como |
|---|---|
| Taxa de rastreamento | quadros com pose associada ao ground truth / quadros de entrada |
| ATE RMSE | **Sim(3) para todos os algoritmos** (decisão de 31/10, §10.1); SE(3) no RGB-D (`ate_se3_m`) e escala por passo nos monoculares (`ate_stepscale_m`) ficam gravados para a análise de sensibilidade |
| ATE com escala por passo | todos os monoculares, secundária (ver abaixo) |
| RPE | Δ = 1 s (15 quadros): translação (m e % do deslocamento) e rotação (°) |
| Latência | ms por quadro (média e mediana), medida dentro do wrapper |
| Memória GPU | pico do `torch.cuda.max_memory_allocated` + amostragem do `nvidia-smi` |

**Escala do TartanVO:** sem o arquivo de poses, a translação de cada passo tem magnitude arbitrária (a perda de treino é até-escala). O script oficial **substitui a norma de cada passo pela do ground truth**, e um Sim(3) com escala única não corrige isso. Mesmo assim, nas 16 sequências o Sim(3) fica a 1,03x do artigo (mediana) e a escala por passo a 0,59x (§10.1), então o QueensCAMP provavelmente usou Sim(3). O `evaluate.py` calcula a "ATE com escala por passo" para todos os monoculares como análise de sensibilidade. Nos testes sintéticos, essa métrica amplifica ruído quadro a quadro.

**Falha × deriva:** uma execução é **falha** se o processo cai ou dá timeout, ou se o rastreamento fica abaixo de 50% (mesma regra do QueensCAMP). ATE e RPE só são agregados nas execuções que não falharam (`evaluate.py`, `min_tracked_for_ate = 0,5`; antes de 31/10 só o `status` era conferido, e o ATE de um trecho de 12% da trajetória aparecia como melhor que o da original). A fração rastreada conta as falhas como 0. A taxa de sucesso (`success_rate`: `ok` e rastreamento ≥ 50%) é reportada à parte.

## 5. Critério de robustez [decidir]
O critério da proposta, "ATE < 0,3 m e rastreamento > 80% em ≥ 75% das sequências", é **inatingível na condição original**: no artigo do QueensCAMP o ORB-SLAM2 RGB-D fica abaixo de 0,3 m em 8 de 16 sequências e o TartanVO em **0 de 16**. Proposta:
- **Principal (relativo):** o método é robusto a uma condição se (i) rastreamento ≥ 80% em ≥ 75% das sequências **e** (ii) a mediana da degradação do ATE em relação à própria condição original for ≤ X% (sugestão: X = 50).
- **Secundário (absoluto):** manter ATE < 0,3 m apenas como informação descritiva.

## 6. Estatística (etapa 5 da proposta) — implementada em `experiments/scripts/stats_analysis.py`
- **Unidade de análise:** sequência (mediana das repetições), n = 16 pareado.
- **Comparação entre métodos por condição:** Wilcoxon pareado sobre a **degradação relativa**, com correção de Bonferroni e IC 95% por bootstrap (10.000 reamostragens).
- **Efeito de cada condição dentro do método:** Wilcoxon pareado entre original e condição.
- **Famílias de Bonferroni:** (i) todos os pares de métodos × condições; (ii) métodos × condições contra a original.
- **Tamanho de efeito:** correlação bisserial de postos. Com n = 16, o menor p exato do Wilcoxon é 3,05 × 10⁻⁵, o que dá margem para Bonferroni.
- Testes com menos de 6 sequências pareadas não recebem p (o Wilcoxon bilateral não atinge 0,05).

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
1. ~~Métrica principal dos monoculares~~ → Sim(3) para todos (§10.1).
2. Critério de robustez relativo e o valor de X: usado X = 50 e o veredito não mudou com nenhum dos alinhamentos (§10.1); confirmar o valor.
3. ~~Ritmo de tempo real do ORB-SLAM2~~: mantido (a matriz inteira rodou assim, em ~43 h).
4. Adotar o SLAM Adversarial Lab (Koschmieder já implementado) ou manter o módulo próprio; ver `docs/trabalhos_relacionados.md`.
5. Restam as decisões provisórias de §10 para o orientador de verdade confirmar.

## 10. Decisões de 31/10 depois da matriz completa (provisórias)
Tomadas com Claude no papel de orientador, a pedido da Natasha, a partir dos dados das 2720 execuções. Não são do orientador de verdade: cada uma diz o que a sustenta e o que muda se ele discordar.

### 10.1 Alinhamento: Sim(3) para todos os algoritmos
**Evidência (reprodução do QueensCAMP, condição original, mediana das sementes por sequência):**

| | alinhamento | razão mediana nosso/artigo | erro relativo mediano | Spearman | sequências |
|---|---|---|---|---|---|
| TartanVO | **Sim(3)** | **1,03** | **12%** | 0,76 | 16 |
| TartanVO | escala por passo | 0,59 | 41% | 0,76 | 16 |
| ORB-SLAM2 RGB-D | **Sim(3)** | **1,00** | **24%** | 0,68 | 13 |
| ORB-SLAM2 RGB-D | SE(3) | 1,17 | 33% | 0,64 | 13 |

O script do artigo usa `correct_scale` opcional; o resultado indica que foi ligado. Um alinhamento só para todos também deixa a comparação entre métodos justa, que a nota de `docs/leituras/2024_bruno_queenscamp.md` já pedia.

**Sensibilidade:** com SE(3) no RGB-D, ou escala por passo nos monoculares, **o veredito de robustez não muda em nenhuma das 40 combinações algoritmo × condição e nenhum dos 36 testes contra a original muda de significância**. Muda a magnitude: a degradação mediana do TartanVO em `breakage` é 81% com Sim(3) e 233% com escala por passo.

**Se o orientador discordar:** trocar `evaluation.monocular_primary` / `rgbd_primary` em `config/experiment.json` e rodar `evaluate.py`, `stats_analysis.py` e `figures.py` de novo (minutos; as três métricas já estão gravadas em `metrics.csv`).

**Reprodução (issue #3):** aceita com a lacuna registrada. O ORB-SLAM2 RGB-D perde o rastreamento em sequências em que o artigo reporta valor: 02 (19% rastreado, artigo 0,24 m), 14 (3%, artigo 0,52 m) e 15 (cai depois de reset nas 5 sementes, artigo 0,56 m). Nas sequências 08 e 10 o artigo também não reporta. A causa dessas três não foi investigada (candidatas: configuração de 1000 ORB, ritmo de tempo real, o próprio reset).

### 10.2 Queda do RGB-D depois de reset do mapa: continua falha de rastreamento
As 35 execuções (09/smoke_densa e seq. 15 em 6 condições) ficam `tracking_lost`. Teste novo: rodando 09/smoke_densa e 15/original (seed 0) **com o loop closure ligado**, sem `ORBSLAM2_NO_LOOP`, a queda continua (código 139, depois de "System Reseting"). Então ela não vem da nossa configuração de VO pura. Corrigir o reset afastaria o ORB-SLAM2 do usado no artigo e na literatura (que registra segfault do ORB-SLAM2), e as 35 execuções não decidem nenhuma conclusão: a seq. 15 já falha na original, e a 09/smoke_densa mostra o ORB-SLAM2 RGB-D perdendo o rastreamento com t̄ = 0,34 (valor dessa sequência). **Limitação a declarar no artigo.** Se o orientador quiser o reset corrigido: variante do runner com `mVelocity` e `mLastFrame` zerados no reset (hipótese não testada), rodada só nessas 35 como análise de sensibilidade.

### 10.3 ORB-SLAM2 monocular: taxa de sucesso é a métrica; ATE só descritivo
Mantidas as 5 repetições; não se roda mais nada. O mono não tem execução válida (não inicializa, perde ou rastreia menos de 50%) em 68% das execuções na original, então a mediana do ATE por condição vem de poucas sequências. Regras: (i) reportar a **taxa de sucesso por execução** (tabela abaixo) e a fração rastreada, não só a mediana por sequência; (ii) o ATE do mono vai com o número de sequências (n) e só entra em teste com ≥ 6 pares; (iii) o mono **não é ranqueado** contra os outros métodos em ATE. A correção do `summarize` (§4) removeu degradações negativas que eram artefato (mono `smoke_densa` −49%, RGB-D `smoke_densa` −94%): sem execução válida, agora ficam sem valor.

| Taxa de sucesso (%, `ok` e rastreamento ≥ 50%) | DPVO | TartanVO | ORB-SLAM2 RGB-D | ORB-SLAM2 mono |
|---|---|---|---|---|
| original | 100 | 100 | 69 | 32 |
| underexposure | 100 | 100 | 56 | 29 |
| overexposure | 100 | 100 | 65 | 26 |
| breakage | 100 | 100 | 46 | 1 |
| wet | 84 | 100 | 94* | 0 |
| condensation | 94 | 100 | 16 | 0 |
| dirt | 100 | 100 | 41 | 8 |
| smoke_leve | 100 | 100 | 64 | 24 |
| smoke_moderada | 100 | 100 | 62 | 14 |
| smoke_densa | 100 | 100 | **0** | **0** |

\* No RGB-D, 75 das 80 execuções de `wet` são marcadas `degenerate` (a trajetória quase não anda): rastreiam, mas não servem. O ATE delas fica no resumo, onde aparece como erro alto (+430% em relação à original).

### 10.4 DPVO com trajetória parada
Aprovado como `tracking_lost` (18 execuções: `wet` e `condensation`). Está em `evaluate.py` (`is_static`).

### 10.5 Viés de escala de 13% do RGB-D: não é bug de calibração
A escala Sim(3) do RGB-D na original não é constante: nas 11 sequências com rastreamento ≥ 50% vai de **0,82 a 1,13 (mediana 1,07)**; a 1,13 da seq. 09 é um extremo. `fx`/`fy` do config (465,6 e 620,9) são coerentes com o resize anisotrópico de 1920×1080 para 640×480 (1397/3 e 1397 × 0,444). Sem ação. A comparação por sequência contra a própria original, que a robustez já usa, absorve isso.

### 10.6 Fumaça: manter V = 60 / 20 / 6 m; calibração do A não é bloqueio; adicionar um nível exploratório
Transmissão média medida (média dos quadros, 16 sequências; `smoke_meta.json`): **leve 0,87 (0,84–0,91), moderada 0,68 (0,60–0,76), densa 0,32 (0,24–0,42)**, mais suave que os 0,81 / 0,56 / 0,20 estimados em `nota_niveis_fumaca.md` (as profundidades reais são menores). O que as execuções mostram: o ORB-SLAM2 RGB-D vai de 62% de sucesso na moderada (t̄ 0,68) a 0% na densa (t̄ 0,32), e o DPVO e o TartanVO **não chegam a quebrar** nem na densa (+2,6% a +5,7%). Logo:
- O parâmetro **A** desloca o brilho médio; o contraste cai com t. A calibração com o SubT-MRS valida o realismo, mas não muda o t̄ por nível, e é o t̄ que governa a perda de *features*. Fica **sem bloqueio**; continua dependendo do dado do SubT-MRS (NATASHA-24).
- Para achar o ponto de quebra dos métodos aprendidos, **adicionar um nível exploratório `smoke_extrema` (V = 3 m, t̄ a medir) só para DPVO e TartanVO** (ORB-SLAM2 já falha em 100% na densa). Fica fora das famílias de Bonferroni da análise principal. Custo estimado: 16 sequências × 7 execuções, algumas horas de GPU. **Não foi executado**; subtarefa NATASHA-41.

### 10.7 Condições com DCP: piloto na seq. 09 antes de qualquer execução em massa
As 4 condições `dcp_*` (272 execuções cada, **1088 no total, cerca de 17 h**) ficam desligadas. Primeiro um **piloto na seq. 09** (gerar as 4 condições, rodar os 4 algoritmos com as repetições do protocolo), para validar a geração e ver se o DCP ajuda, piora ou é neutro; só então decidir o escopo da execução completa. Motivos: o ORB-SLAM2 já falha em 100% na fumaça densa (o DCP precisa recuperar o rastreamento para mostrar efeito), e gerar o DCP antes de fechar os níveis de fumaça (§10.6) obrigaria a repetir. Não foi executado; subtarefa NATASHA-42 (sob o NATASHA-17).
