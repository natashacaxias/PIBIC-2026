# Protocolo experimental — v0.2 (decisões de trabalho de 31/10)

Jira: NATASHA-26. Escrito em 10/10/2026 a partir das leituras (`docs/leituras/`) e do código dos algoritmos. Os itens marcados com [decidir] foram decididos em 31/10, depois da matriz completa, como decisões de trabalho da Natasha, **com Claude no papel de orientador** (§10). A execução não espera revisão: cada decisão traz os dados que a sustentam e como reverter. O orientador de verdade ainda não as revisou. A implementação está em `experiments/`.

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
| Latência | ms por quadro (média por execução), medida dentro do wrapper; no ORB-SLAM2 é só o tracking (`track_ms` do `frames.csv`, sem as threads de mapeamento) |
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
5. As decisões de trabalho de §10 seguem valendo; o orientador pode revisá-las depois (todas são reversíveis).

## 10. Decisões de 31/10 depois da matriz completa (adotadas como decisões de trabalho, sem revisão do orientador)
Decisões de trabalho tomadas com Claude no papel de orientador, a pedido da Natasha, a partir dos dados das 2720 execuções, e seguidas sem esperar revisão. O orientador de verdade ainda não as viu: cada uma diz o que a sustenta e o que muda se ele discordar.

**Status em 01/11.** A Natasha delegou a decisão de adotá-las ("você tem autonomia para essas decisões"), então ficam **adotadas** como decisões de trabalho do projeto, sem aprovação do orientador. Se ele discordar de alguma, `evaluate.py`, `stats_analysis.py` e `figures.py` recalculam tudo em cerca de 5 min e os números do artigo saem de `results/`.

### 10.1 Alinhamento: Sim(3) para todos os algoritmos
**Evidência (reprodução do QueensCAMP, condição original, mediana das sementes por sequência):**

| | alinhamento | razão mediana nosso/artigo | erro relativo mediano | Spearman | sequências |
|---|---|---|---|---|---|
| TartanVO | **Sim(3)** | **1,03** | **12%** | 0,76 | 16 |
| TartanVO | escala por passo | 0,59 | 41% | 0,76 | 16 |
| ORB-SLAM2 RGB-D | **Sim(3)** | **1,04** | **17%** | 0,92 | 11 |
| ORB-SLAM2 RGB-D | SE(3) | 1,31 | 31% | 0,87 | 11 |

As 11 sequências são as que têm valor no artigo e rastreamento ≥ 50% na nossa execução, a mesma regra que os autores aplicam. (A primeira versão desta tabela incluía 13 sequências porque contava o ATE de execuções com rastreamento < 50%: Sim(3) 1,00 / 24% / 0,68 e SE(3) 1,17 / 33% / 0,64. Corrigido em 31/10, ao montar a Tab. 1 do artigo; a conclusão não muda, o Sim(3) continua mais perto do artigo.)

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
- Para achar o ponto de quebra dos métodos aprendidos, foi adicionado o nível exploratório `smoke_extrema` (V = 3 m) só para DPVO e TartanVO (ORB-SLAM2 já falha em 100% na densa). Fica fora das famílias de Bonferroni (`evaluation.exploratory_conditions`; resultados em `stats_exploratory.csv`). Rodou em 31/10 (NATASHA-41): 112 execuções, 16 sequências.

**Resultado da fumaça extrema (31/10).** Transmissão média por sequência 0,09–0,21 (mediana 0,145; a densa vai de 0,24 a 0,42). Nenhum dos dois métodos quebra: **112 de 112 execuções `ok` com rastreamento 1,0, nenhuma trajetória parada.** O custo é de precisão (ATE Sim(3), mediana das medianas por sequência, contra a original):

| algoritmo | original | densa | extrema | degradação mediana densa → extrema | extrema contra original (Wilcoxon, Bonferroni entre as duas) |
|---|---|---|---|---|---|
| DPVO | 0,250 m | 0,243 m | 0,329 m | +5,7% → **+23,6%** (de −18% a +695% por sequência) | p = 0,0076, p_Bonf = 0,015, r = 0,74 |
| TartanVO | 0,742 m | 0,761 m | 0,888 m | +2,6% → **+13,0%** (de +0,1% a +65%; as 16 sequências pioram) | p = 3,1e-5, p_Bonf = 6,1e-5, r = 1,0 |

No DPVO o efeito é muito desigual: 3 sequências passam de +100% (06: +695%, 05: +317%, 15: +129%) e 21 das 80 execuções têm ATE acima do dobro da mediana da original da própria sequência; a correlação entre t̄ da extrema e a degradação é ρ = −0,70 (p = 0,003, n = 16). No TartanVO não há relação com t̄ (ρ = −0,31, p = 0,25). **Ponto de quebra não alcançado** com t̄ ≥ 0,09. Não vou adicionar níveis mais densos: na validação com fumaça real (`nota_niveis_fumaca.md`) a extrema já tem contraste (0,15 contra 0,33 do trecho denso real) e bordas (0 contra 0,11) mais baixos que a fumaça real medida, e pontos ORB na mesma ordem (≈ 0), então níveis abaixo disso perdem relevância física. Falha de infraestrutura registrada: uma execução do DPVO (08, semente 1) terminou com "CUDA launch timed out" (Xid 8, watchdog da GPU, 13:46 de 31/10); o log foi guardado em `/data/matrix_logs/falha_xid8_dpvo_08_extrema_seed1.*` e a execução foi refeita com `--retry-failed` (ok).

### 10.7 Condições com DCP: piloto na seq. 09 e escopo da execução completa
As 4 condições `dcp_*` ficaram desligadas até um **piloto na seq. 09** (4 condições, 4 algoritmos, 68 execuções, concluído em 31/10; NATASHA-42, sob o NATASHA-17). Motivo: o ORB-SLAM2 já falha em 100% na fumaça densa (o DCP precisa recuperar o rastreamento para mostrar efeito) e o DCP não deveria ser gerado antes de fechar os níveis de fumaça (§10.6).

**Resultado do piloto (n = 1 sequência, só direção; `stats_dcp.csv`).** ATE Sim(3) em metros, mediana das sementes (taxa de sucesso = execuções com rastreamento ≥ 50% e ATE, em 5 sementes; TartanVO tem 2, determinísticas):

| algoritmo | original → com DCP | leve → com DCP | moderada → com DCP | densa → com DCP |
|---|---|---|---|---|
| ORB-SLAM2 RGB-D | 0,151 → 0,157 (5/5 → 5/5) | 0,157 → 0,165 | 0,137 → 0,162 | **sem ATE (5/5 `tracking_lost`) → 0,154 (5/5 ok)** |
| ORB-SLAM2 mono | 0,548 → 0,425 (5/5 → 4/5) | 0,163 → 0,295 (5/5 → 4/5) | 0,233 → 0,338 (4/5 → 5/5) | **0/5 → 0/5 (`not_initialized` 5/5 nos dois)** |
| DPVO | 0,232 → 0,260 | 0,243 → 0,222 | 0,217 → 0,254 | 0,231 → 0,248 |
| TartanVO | 0,503 → 0,482 | 0,498 → 0,469 | 0,540 → 0,465 | 0,519 → 0,369 |

Leitura: (1) **o DCP devolve o rastreamento ao ORB-SLAM2 RGB-D na fumaça densa** (de 0/5 para 5/5, ATE no nível da original, 0,154 contra 0,151) e não estraga a imagem sem fumaça (+4%: 0,151 → 0,157); na moderada o RGB-D paga 18% (0,137 → 0,162, faixas das sementes sem sobreposição). (2) **O monocular não é recuperado**: continua sem inicializar na densa; nas outras condições a seq. 09 varia entre sementes mesmo sem DCP (ATE da original de 0,06 a 0,82 m entre as 5 sementes), então as diferenças de ~0,1 m não são interpretáveis com uma sequência. (3) DPVO: todas as diferenças dentro da variação das sementes (ex.: densa 0,14–0,31 sem DCP, 0,17–0,29 com). (4) TartanVO: −29% na densa (0,519 → 0,369) em 2 sementes determinísticas de uma sequência; a degradação dele na densa é só +2,6% na matriz inteira, então há pouco a recuperar e isso não conclui nada. A geração: A estimado pelo DCP por sequência, 0,82–0,83 na densa e 0,96 no `dcp_original` da seq. 09 (`dcp_meta.json`).

**Decisão (31/10, provisória, registrada antes de lançar): executar o DCP completo só para o ORB-SLAM2 (mono e RGB-D), nas condições `dcp_original`, `dcp_smoke_moderada` e `dcp_smoke_densa`, 16 sequências × 5 sementes = 480 execuções (450 além do piloto), cerca de 12 h de ORB-SLAM2 em série; em 2 fatias em paralelo, estimativa de 6 a 7 h.** Em vez das 1088 do plano original (17 h). Razões: o único efeito do DCP no piloto está no ORB-SLAM2, e é exatamente onde ele pode mudar uma conclusão do artigo (RGB-D densa: 0% de sucesso na matriz); DPVO e TartanVO têm 100% de sucesso em todos os níveis de fumaça, inclusive na extrema, então o DCP não tem falha a corrigir neles e o piloto não mostra efeito; `dcp_smoke_leve` fica de fora porque a leve muda pouco em relação à original (sucesso do RGB-D 64% contra 69%; do mono 24% contra 33%; DPVO e TartanVO 100%) e o piloto não mostra efeito nela. Hipótese fixada antes da execução: na densa, o `dcp_smoke_densa` eleva a taxa de sucesso do RGB-D de 0% para algo próximo da taxa da original (69% nas 16 sequências, limitada pelas falhas de reprodução das sequências 02, 14 e 15) e o monocular continua sem inicializar; o custo na imagem limpa (`dcp_original` contra original) é pequeno. Métrica principal: taxa de sucesso e fração rastreada; o ATE entra pareado por sequência quando houver ≥ 6 pares. Análise em `stats_dcp.csv` (cada `dcp_X` contra o seu `X`). As condições `dcp_*` seguem em `exploratory_conditions` (a análise é pós-piloto e restrita a um algoritmo, então não entra nas famílias principais), com Bonferroni só entre elas.

**Resultado do DCP completo (01/11, 480 execuções do ORB-SLAM2 em `dcp_original`, `dcp_smoke_moderada` e `dcp_smoke_densa`; NATASHA-43; `stats_dcp.csv`).** A geração terminou às 16:49 e a execução às 01:19 (8 h 30 min, contra a estimativa de 6 a 7 h: ela partia dos 97 s da seq. 09 e a média no monocular das seq. 01–07 foi de 169 s). Nenhuma falha de infraestrutura (sem Xid, sem OOM, sem `--retry-failed`); 3.350 execuções avaliadas no total. Sucesso = `ok`, rastreamento ≥ 50% e ATE (execuções válidas / execuções; 16 sequências × 5 sementes):

| algoritmo | condição | sem DCP | com DCP |
|---|---|---|---|
| ORB-SLAM2 RGB-D | original | 55/80 (68,8%) | 50/80 (62,5%) |
| ORB-SLAM2 RGB-D | moderada | 50/80 (62,5%) | 49/80 (61,3%) |
| ORB-SLAM2 RGB-D | densa | **0/80 (0%)** | **50/80 (62,5%)** |
| ORB-SLAM2 mono | original | 26/80 (32,5%) | 13/80 (16,3%) |
| ORB-SLAM2 mono | moderada | 11/80 (13,8%) | 11/80 (13,8%) |
| ORB-SLAM2 mono | densa | 0/80 (0%) | 7/80 (8,8%) |

Contra a hipótese fixada antes de rodar (acima), item por item:

1. **RGB-D na densa: confirmada.** De 0% para 62,5%, contra 68,8% da original. Das 11 sequências em que o RGB-D rastreia na original, 10 voltam a ter execuções válidas (01, 03, 04, 05, 06, 07, 09, 11, 12, 13; 50/55 = 90,9% contra 55/55 na original; fração rastreada mediana de 0,11 para 1,00). A que não volta é a 16, que também falha em `dcp_original` (ver 3). As 5 sequências sem execução válida na original continuam 0/25 com DCP em todas as condições; elas são **02, 08, 10, 14 e 15** (a hipótese citava só 02, 14 e 15, mas o 69% já contava as falhas de 08 e 10, então a comparação com 69% vale como está). Como a densa sem DCP não tem nenhum ATE válido, não há pares e o teste do ATE pareado (≥ 6 pares) não se aplica a ela.
2. **Monocular: parcial.** Não volta ao nível da original (32,5%): de 0/80 para 7/80 (8,8%), todas nas sequências 01 (2/5) e 03 (5/5). "Continua sem inicializar" vale só em parte: `not_initialized` cai de 41/80 para 27/80 e 53/80 execuções inicializam, mas 46 das 53 rastreiam menos de 50% (fração rastreada mediana de 0,000 para 0,073). O ATE das 7 válidas é só descritivo (§10.3): na seq. 03 vai de 0,15 a 1,53 m entre as sementes.
3. **Custo na imagem limpa: parcial.** *RGB-D:* o ATE pareado em 10 sequências não muda (mediana 0,255 → 0,252 m, diferença percentual mediana por sequência 0,0%, Wilcoxon p = 0,557, Bonferroni 1,0), mas o sucesso cai 6,3 pontos (55 → 50) e toda a queda é a seq. 16 (5/5 → 0/5, fração rastreada de 1,00 para 0,35); a fração rastreada também cai nas seq. 01 (1,00 → 0,79), 04 (→ 0,88) e 13 (→ 0,84), sem perder execuções válidas. *Monocular:* o custo não é pequeno: o sucesso cai pela metade (26/80 → 13/80) e, das 7 sequências com execução válida na original, 4 perdem todas (05, 07, 11, 16); na seq. 03 o ATE vai de 0,233 para 1,083 m. Mecanismo não investigado.

Na **moderada** o DCP não tem efeito mensurável: RGB-D 50 → 49/80, ATE pareado em 10 sequências mediana −6,1% (0,261 → 0,256 m), p = 0,131 (Bonferroni 0,262); monocular 11/80 → 11/80 (`tracking_lost` de 4 para 0, `not_initialized` de 10 para 18).

*Análise pós-hoc, não pré-registrada, só descritiva:* nas 10 sequências recuperadas do RGB-D na densa, o ATE com DCP é maior que o da imagem limpa: 0,255 → 0,324 m (mediana; diferença percentual mediana por sequência +11%, de −9% a +41%, 8 de 10 piores; Wilcoxon p = 0,014 sem correção) e +25% contra `dcp_original` (p = 0,027 sem correção). O rastreamento volta, mas o erro não volta ao da imagem sem fumaça.

**Veredito: hipótese parcialmente confirmada.** O resultado principal (RGB-D na densa) se confirma; o monocular não é recuperado e o DCP o prejudica na imagem limpa; no RGB-D o custo na imagem limpa é pequeno no ATE e se concentra numa sequência (16). Fica registrado como mitigação para o RGB-D, não como correção geral. Limites: um dataset (QueensCAMP), um estimador de A por sequência e os parâmetros do DCP sem ajuste, só o ORB-SLAM2 (DPVO e TartanVO só no piloto), e a seq. 16 não foi investigada. As 10 execuções do RGB-D da seq. 15 (moderada e densa) terminaram em `tracking_lost` com código 139 (*segfault* depois de reset do mapa, §10.2), igual às da origem. Nada foi mudado na hipótese nem nas métricas depois de ver o resultado.

**Diagnóstico do custo do DCP na imagem limpa (01/11, depois do resultado acima; amostra de 1 quadro a cada 25).** (1) O DCP escurece a imagem sem fumaça: a luminância média cai de 125–130 para 57–69 em oito das nove sequências medidas (01, 02, 03, 04, 05, 09, 11, 13; 16: 110 → 66), porque A estimado fica alto (0,85–1,00) e t̄ fica em 0,58–0,65. (2) A quantidade de *keypoints* ORB não cai em média (razão 0,92 a 1,17, FAST limiar 20, 1000 pontos). (3) **Seq. 16, RGB-D:** entre os quadros ~415 e ~450 a câmera passa por um trecho quase preto já na imagem original (luminância 8–14, até 48% dos pixels ≤ 5, 0 a 8 *keypoints* nos quadros 418–428). A fração rastreada fica em 0,35 (= quadro ~424 de 1.202) em `dcp_original` (0,352 a 0,353 nas 5 sementes), `underexposure` (0,34), `smoke_leve` (0,35) e `smoke_moderada` (0,34), e em 1,00 na original e na `overexposure`. Depois do trecho escuro, o quadro 480 tem 374 *keypoints* na original, 179 com DCP e 68 na subexposição. Na seq. 16 o DCP age de forma parecida com a subexposição: a hipótese é que o que quebra é o escurecimento, não uma falha própria do dehazing (testada abaixo). Nas seq. 01, 04 e 13 (fração rastreada com DCP 0,79, 0,88 e 0,84) o padrão não é igual ao da subexposição (1,00, 1,00 e 0,25), então o escurecimento sozinho não explica esses três. Não investigado: o monocular.

**Teste exploratório de normalização de exposição (registrado em 01/11 antes de gerar e rodar).** Hipótese: se o custo do DCP no RGB-D na imagem limpa vem do escurecimento, um único ganho por sequência que devolve a luminância média da entrada (`exposure_match: "sequence"` em `smoke_emulation/dcp.py`; mediana de luminância de entrada / luminância de saída em 1 quadro a cada 10; a saída padrão do DCP não muda, conferido bit a bit na seq. 09) elimina a perda. Condições novas `dcpn_original` e `dcpn_smoke_densa` (exploratórias, fora das famílias de Bonferroni), só ORB-SLAM2 RGB-D, sequências 01, 04, 13 e 16 (as que perderam rastreamento com o DCP) mais 03 e 09 como controle, 5 sementes: 60 execuções. As sequências foram escolhidas pelo problema observado, então o teste não estima o efeito da normalização nas 16. Valem 30 execuções por condição (6 sequências × 5): original 30/30 válidas; `dcp_original` 25/30 (a seq. 16 tem 0/5); `dcp_smoke_densa` 25/30 (idem). **Critérios:** (a) `dcpn_original` **confirma** se tiver ≥ 29/30 válidas e fração rastreada mediana ≥ 0,95 na seq. 16; **refuta** se tiver ≤ 25/30; **parcial** entre os dois. (b) `dcpn_smoke_densa` tem de manter ≥ 25/30 válidas; se a seq. 16 voltar, melhora. Não testado: monocular, o ganho por quadro, outros parâmetros do DCP (ômega, t0).

**Resultado do teste de normalização de exposição (01/11; 60 execuções, todas `ok`, sem falha de infraestrutura; NATASHA-44).** ORB-SLAM2 RGB-D, sequências 01, 03, 04, 09, 13 e 16, 5 sementes (execuções válidas / 30 por condição): original 30/30; `dcp_original` 25/30; **`dcpn_original` 30/30**; `dcp_smoke_densa` 25/30; **`dcpn_smoke_densa` 25/30**. Contra os critérios gravados antes de rodar:

- **(a) `dcpn_original`: confirma.** 30/30 válidas (critério ≥ 29/30) e fração rastreada 1,00 nas 5 sementes da seq. 16 (ATE de 0,336 a 0,396 m; original 0,386 m). A fração rastreada também volta a 1,00 nas seq. 01, 04 e 13 (com o DCP simples eram 0,79, 0,88 e 0,84). ATE pareado nas 6 sequências: 0,255 → 0,221 m (mediana; diferença percentual mediana −5,5%; 1 das 6 pior; Wilcoxon p = 0,156), sem custo mensurável; nos controles 03 e 09 o ATE não muda (0,104 → 0,103; 0,151 → 0,143). **Leitura:** o custo do DCP simples na imagem limpa do RGB-D vem do escurecimento; um ganho único por sequência o elimina nas quatro sequências afetadas, inclusive 01, 04 e 13, onde a subexposição da matriz não reproduzia o padrão (então a subexposição não imita o DCP em todas as sequências).
- **(b) `dcpn_smoke_densa`: cumpre o mínimo e não melhora.** 25/30, no limite do critério (≥ 25/30). A composição muda: a seq. 16 passa de 0/5 para 1/5 (uma semente com fração rastreada 0,71; as outras quatro ficam em 0,34) e a seq. 04 de 5/5 para 4/5. Nas 5 sequências comuns (01, 03, 04, 09, 13) o ATE vai de 0,201 (DCP simples) para 0,203 m (−2% de diferença mediana por sequência) e continua +14% acima da original (0,176 m). Na fumaça densa o ganho não muda o resultado do DCP completo acima; o motivo de a seq. 16 continuar perdendo o rastreamento nesse caso não foi investigado.
- **Custo da normalização:** o ganho (1,66 a 2,25) satura a imagem: 6 a 14% dos pixels ≥ 250 na imagem limpa e 13 a 24% na densa (amostra de 1 em 60 quadros), contra 0,1 a 1,9% na original limpa.
- **Limites:** 6 sequências escolhidas pelo problema observado (duas são controles), 5 sementes, só RGB-D; o monocular não foi testado; o ganho é global por sequência, não por quadro. Não é uma estimativa do efeito nas 16 sequências.

**Decisão:** o resultado oficial do DCP é o do DCP simples (acima); a normalização fica registrada como explicação do custo na imagem limpa do RGB-D, não como substituta, porque não melhora a fumaça densa e satura a imagem.

**Custo do DCP no ORB-SLAM2 monocular na imagem limpa: o que os dados já mostram e teste registrado em 02/11 antes de gerar e rodar (NATASHA-46).** O mono cai de 26/80 execuções válidas na original para 13/80 em `dcp_original`. Por sequência (válidas de 5, original → DCP): 01 3→4, 03 5→5, 05 1→0, 07 5→0, 09 5→4, 11 5→0, 16 2→0; as outras 9 ficam em 0→0. **Dez das 13 execuções perdidas estão nas sequências 07 e 11.** O estado de rastreamento por quadro (`frames.csv`) mostra dois mecanismos diferentes: (i) na **07** a inicialização passa do quadro 112 para o 582 nas 5 sementes e a fração rastreada cai de 0,70 para 0,44 a 0,50, ou seja, atravessa o limiar de 0,5; o último quadro rastreado é parecido (1596 a 1732 contra 1728 a 1754), então o efeito é de **inicialização tardia** sobre um limiar; (ii) na **11** a inicialização passa do quadro 101 para o 140, o rastreamento se perde entre os quadros 501 e 528 nas 5 sementes (mesmo trecho, então depende do conteúdo e não do acaso) e **não reinicializa até o fim (quadro 1437)**; na original 4 das 5 sementes não perdem o rastreamento. As **05 e 16 já são bimodais na original** (05: fração rastreada 0,02 a 0,03 em 4 sementes e 0,73 em uma; 16: 0,52 em duas sementes, no limiar, e 0,00 a 0,19 nas outras), então o 1→0 e o 2→0 não são confiáveis como perda. Medição fora do SLAM (ORB com 1000 pontos como na configuração, pares de quadros a 3 de distância, seq. 11): nos quadros 500 e 520 a luminância média vai de 126 e 122 (original) para 57 e 53 (DCP), o desvio padrão de 41 e 40 para 32 e 32, os pontos ORB de 628 e 831 para 455 e 482, e os pares consistentes pela matriz fundamental de 241 e 313 para 180 e 152; na janela 440 a 580 o DCP mantém 0,5 a 0,8 dos pares da original. Isto é descritivo, em 1 sequência.

**Hipótese (registrada antes de gerar e rodar):** a perda do mono em 07 e 11 vem do mesmo escurecimento do RGB-D (menos contraste, menos cantos detectados em trechos que já têm pouca textura), então o ganho de exposição por sequência (`exposure_match: "sequence"`, código inalterado) a elimina. **Teste:** `dcpn_original` gerado para as sequências 05, 07 e 11 (01, 03, 09 e 16 já existem, ganhos de 1,66 a 2,25), ORB-SLAM2 monocular, sequências 01, 03, 05, 07, 09, 11 e 16, 5 sementes = 35 execuções, só imagem limpa, mesma configuração de `orbslam2_mono`. **Critério principal** nas sequências 07 e 11 juntas (10 execuções; original 10/10, DCP simples 0/10): **confirma** se `dcpn_original` tiver ≥ 8/10 válidas; **refuta** se ≤ 2/10; **parcial** entre 3 e 7. Também gravo, por execução, o quadro de inicialização e o último quadro rastreado: na 11 a hipótese prevê que a perda por volta do quadro 500 desaparece (como a fração rastreada é contínua, vale mais que o limiar). As outras cinco sequências não entram no critério: 05 e 16 são bimodais na original; 01, 03 e 09 servem de controle para ver se o ganho cria perda nova (esperado: ≥ 11/15 válidas, a original e o DCP simples têm 13/15). **Não testado:** fumaça no monocular, ganho por quadro, outros parâmetros do DCP, DPVO e TartanVO (sem perda com o DCP). Se refutar, as próximas explicações (não testadas aqui) são variação de quadro a quadro da transmissão e amplificação de ruído nos trechos escuros. As sequências foram escolhidas pelo problema observado, então o teste não estima o efeito nas 16.

### 10.8 Critério de robustez: X = 50% mantido
Variando X entre 25%, 50% e 100% (`stats_analysis.py --max-degradation`), **38 das 40 combinações algoritmo × condição mantêm o veredito**. As duas que mudam são o TartanVO em `breakage` (81% de degradação mediana) e `dirt` (68%), que só viram robustas com X = 100. O 50% fica no meio de uma faixa estável (nenhum veredito muda entre 25% e 50%), então a escolha não decide nenhuma conclusão do artigo.

### 10.9 Latência e memória (31/10)
O `evaluate.py` não preenchia a latência das 1600 execuções do ORB-SLAM2 (o wrapper não grava `mean_ms_per_frame`); agora ela sai do `frames.csv`. A coluna de memória de GPU do ORB-SLAM2 passou a ficar vazia (CPU só; o valor era ruído do host). Medianas das execuções `ok` na condição original:

| algoritmo | ms por quadro | memória de GPU (pico, MiB) | observação |
|---|---|---|---|
| DPVO | 29,3 (p90 30,4) | 710 | |
| TartanVO | **22,1** com 8 CPUs (n = 6), **80,3** com 2 CPUs (n = 26) | 237 | o tempo depende do `--cpus` do container (8, 4 ou 2); só compare no mesmo valor |
| ORB-SLAM2 RGB-D | 12,9 | n/a | só tracking, CPU |
| ORB-SLAM2 mono | 9,5 | n/a | só tracking, CPU |

Os valores não são comparáveis entre as famílias (o DPVO e o TartanVO medem a inferência inteira; o ORB-SLAM2, só o tracking). O pico de RAM por execução não foi gravado; as medidas do spike (`ambiente.md`) são ~2 GiB no DPVO, ~1 GiB no TartanVO e ~0,4 GiB no ORB-SLAM2.

### 10.10 Análise por estrato (01/11; descritiva, NATASHA-45)
Estratos pelos atributos de `datasets.md`: **dinâmicas** (01, 04, 05, 06, 07; 5 sequências), **pouca luz** (14, 15, 16; 3) e **estáticas** (as outras 8). Sem testes: com 3, 5 e 8 sequências por estrato e sem correção possível, só descrição, a partir de `metrics.csv` (execuções válidas / execuções).

| condição original | dinâmicas | pouca luz | estáticas |
|---|---|---|---|
| ORB-SLAM2 RGB-D | 25/25 | **5/15** | 25/40 |
| ORB-SLAM2 mono | 9/25 | 2/15 | 15/40 |
| TartanVO | 10/10 | 6/6 | 16/16 |
| DPVO | 25/25 | 15/15 | 40/40 |

- **Pouca luz explica parte das falhas de reprodução do RGB-D (§10.1):** 14 e 15 são sequências de pouca luz (a 16, a terceira, rastreia na original); as outras três sequências sem execução válida (02, 08, 10) são estáticas, então a pouca luz não explica tudo. O RGB-D na fumaça leve e na moderada mantém 25/25 nas dinâmicas e 25/40 nas estáticas, e cai para 1/15 e 0/15 na pouca luz (contra 5/15 na original).
- **DPVO e TartanVO:** 100% de sucesso nos três estratos em quase todas as condições (exceções do DPVO: `condensation`, 67% na pouca luz; `wet`, 92% nas dinâmicas e 72% nas estáticas, as trajetórias paradas de §10.4). A degradação do ATE na fumaça é a mesma ordem de grandeza nos três estratos, exceto o DPVO na densa na pouca luz (+35%, contra +6% e +5%): isso vem da seq. 15 (+190%), enquanto a 16 melhora (−24%) e a 14 sobe 36%; com n = 3 não é efeito de estrato.
- Nas falhas de lente a degradação do ATE do DPVO é maior nas estáticas (+620% a +1013% em `breakage`, `condensation`, `dirt` e `wet`) que nas dinâmicas (+89% a +560%); a razão é relativa à original de cada sequência, então depende também do ATE-base, e a comparação não foi corrigida. O monocular quase não tem pares válidos para comparar (§10.3).
- Não se concluiu nada sobre o efeito de "estático × dinâmico" nos métodos aprendidos: o que se vê é consistente com não haver diferença sistemática, com n pequeno.
