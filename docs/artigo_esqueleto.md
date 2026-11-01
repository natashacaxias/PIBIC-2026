# Artigo — rascunho v0.2 (31/10/2026)

Jira: NATASHA-20. **Template e venue a definir com o orientador**: a proposta cita SIBGRAPI, LARS/SBR e WRE. Verificar os prazos e o limite de páginas no site de cada evento antes de fixar o escopo.

**Estado deste rascunho.** Os números abaixo foram conferidos em 31/10 contra `experiments/results/{metrics,summary,stats_*}.csv` (3.350 execuções avaliadas: 2.720 da matriz principal, 112 da fumaça extrema e 518 do DCP, 68 do piloto e 450 do completo). Referências usam a numeração da proposta (lista em `docs/relatorio_parcial.md` e `docs/leituras/README.md`); o que não tem número ali está marcado **[ref a conferir]**. Marcadores **[PENDENTE]** dependem de dado que ainda não existe. Decisões de análise que ainda não passaram pelo orientador estão em `docs/protocolo_experimental.md` §10 (provisórias).

## Título provisório
*Smoke, Lenses and Learned Odometry: A Statistically Grounded Robustness Study of Classical and Deep Visual Odometry under Real Lens Failures and Physically Calibrated Smoke*
(alternativa em português para o WRE/LARS: "Fumaça, lentes e odometria visual: robustez de métodos clássicos e aprendidos sob degradações representativas da Amazônia")

## Mensagem central (uma frase)
Fumaça emulada, mesmo densa (transmissão média 0,32), custa pouco aos métodos aprendidos (degradação mediana do ATE de +5,7% no DPVO e +2,6% no TartanVO) mas elimina o rastreamento do ORB-SLAM2 (0% de sucesso, RGB-D e monocular), enquanto as falhas de lente fazem o contrário: os métodos aprendidos continuam rastreando e derivam (+68% a +564%), e o modo de falha muda com o tipo de degradação (perda de rastreamento no ORB-SLAM2, deriva nos aprendidos). *(Provisória: a parte "validada contra fumaça real" é de uma só sequência real; o gap de domínio depende da coleta de campo.)*

## Resumo (rascunho)
A odometria visual é essencial para a navegação de veículos autônomos em florestas, mas degradações ópticas como fumaça de queimadas e falhas de lente comprometem seu funcionamento. Avaliamos o ORB-SLAM2 (monocular e RGB-D), o TartanVO e o DPVO nas 16 sequências do QueensCAMP sob seis falhas de câmera e três níveis de fumaça emulada fisicamente sobre profundidade medida, com a fumaça comparada a fumaça real do SubT-MRS. Em 2.720 execuções com repetições e testes pareados com correção de Bonferroni, o DPVO e o TartanVO mantêm 100% de sucesso na fumaça, inclusive numa condição extrema (transmissão média 0,15), e perdem de +68% a +564% de precisão nas falhas de lente; o ORB-SLAM2 não rastreia na fumaça densa em nenhuma das 160 execuções. Nas 16 sequências, o pré-processamento com Dark Channel Prior devolveu o rastreamento ao ORB-SLAM2 RGB-D na fumaça densa (sucesso de 0% para 62,5%, contra 68,8% sem fumaça), com ATE 11% acima do da imagem limpa nas sequências recuperadas, mas não ao monocular (de 0% para 8,8%), que ainda perde metade do sucesso na imagem limpa (32,5% para 16,3%). Código, configurações e resultados estarão em **[URL: repositório ainda privado, NATASHA-21]**.

## Estrutura (6–8 páginas)
| Seção | Conteúdo | Fonte no repositório | Tamanho |
|---|---|---|---|
| 1. Introdução | motivação SAGRES-Pro e Amazônia; lacuna; 3–4 contribuições numeradas | `relatorio_parcial.md` §1, `analise_concorrentes_2026.md` §3 | 0,75 p |
| 2. Trabalhos relacionados | VO clássica/aprendida; robustez; névoa sintética; concorrentes de 2026 | `trabalhos_relacionados.md` | 0,75 p |
| 3. Emulação de fumaça e validação | modelo, níveis, profundidade, cor da fumaça; validação contra o SubT-MRS | `nota_niveis_fumaca.md`, `smoke_emulation/` | 1 p |
| 4. Protocolo experimental | dados, métodos, configuração justa (escala, stride, loop), repetições, métricas, estatística | `protocolo_experimental.md` | 1 p |
| 5. Resultados | reprodução do QueensCAMP; robustez por condição; falha × deriva; fumaça extrema; DCP; custo | `experiments/results/` | 2 p |
| 6. Discussão | fidelidade da fumaça; implicações para o SAGRES-Pro; limitações | — | 0,75 p |
| 7. Conclusão | — | — | 0,25 p |

---

## Texto por seção (rascunho)

### 1. Introdução
*(esboço; texto final depende da posição de originalidade, ver `trabalhos_relacionados.md` §5)*
- Motivação: navegação de UAV/UGV em floresta amazônica, onde a fumaça de queimada e a sujeira, a umidade e a condensação na lente são frequentes (SAGRES-Pro; ver `relatorio_parcial.md` §1). **[PENDENTE: números de queimadas, só com fonte conferida]**
- Lacuna: Bujanca et al. [13] deixam clima e visibilidade limitada como lacuna; o QueensCAMP [9] mede falhas de lente mas não fumaça; os trabalhos de 2026 com névoa por Koschmieder (SAL, "Failure or Drift?", Kumar et al.) tratam névoa ou "dust haze" (`trabalhos_relacionados.md` §3).
- Contribuições (ver abaixo).

### 2. Trabalhos relacionados
Resumo de `docs/trabalhos_relacionados.md` (v0.1, ainda com itens lidos só pelo resumo, marcados †). Para o artigo, ler na íntegra SAL, "Failure or Drift?", Kumar et al., Tan et al. e ForestVO antes de citar (NATASHA-37).

### 3. Emulação de fumaça e validação
**Modelo.** Koschmieder homogêneo, I = J·t + A·(1−t), t = exp(−β·d), β = 3,912/V, com a profundidade medida do QueensCAMP (limitada a 10 m) e A = (0,8; 0,8; 0,8). Os buracos da profundidade reprojetada (50% dos pixels, em média) são preenchidos por dilatação 3×3 com o vizinho mais distante; trocar essa política por *inpainting* muda a transmissão média em até 0,03 nos três níveis principais (`nota_niveis_fumaca.md`).

**Níveis.** V = 60 / 20 / 6 m dão transmissão média (16 sequências) de **0,87 / 0,68 / 0,32**; mais um nível exploratório de V = 3 m (0,145, mediana).

**Validação contra fumaça real** (SubT-MRS, uma sequência; razão fumaça/limpo, cada cena contra a sua linha de base):

| | contraste | bordas | pontos ORB |
|---|---|---|---|
| real, rala | 0,47–0,50 | 0,41–0,46 | 0,19–0,24 |
| real, densa | **0,33** | **0,11** | **0,013** |
| sintética leve | 0,87 | 0,77 | 0,82 |
| sintética moderada | 0,75 | 0,52 | 0,49 |
| sintética densa | **0,40** | **0,09** | **0,066** |
| sintética extrema | 0,15 | 0,00 | 0,00 |

A densa sintética reproduz a perda de contraste e de bordas da real densa; a leve e a moderada são mais brandas que a fumaça rala real (cuja densidade é desconhecida); a extrema é mais severa que qualquer trecho real. O estimador de luz atmosférica do DCP dá 0,70–0,80 nos quadros reais e sustenta A = 0,8. **Limites:** uma sequência real, outra cena e outra câmera; sem SSIM (não há quadro limpo alinhado); BRISQUE não rodado (`piq` não instalado); cor da fumaça real (cinza-azulada ou amarronzada) difere da sintética (cinza-clara).

### 4. Protocolo experimental
Resumo de `protocolo_experimental.md` §2–§6 e §10. Pontos que o artigo precisa dizer:
- **Configuração justa entre paradigmas:** loop closure desligado no ORB-SLAM2 (patch `ORBSLAM2_NO_LOOP`), DPVO com stride 1 e sem loop closure, TartanVO com passos normalizados; 5 repetições (ORB-SLAM2, DPVO) e 2 (TartanVO, determinístico).
- **Matriz:** 16 sequências × 10 condições × 4 métodos = 2.720 execuções, Docker em GPU Blackwell, versões e commit em cada `meta.json`.
- **Métricas:** taxa de rastreamento, ATE RMSE com alinhamento **Sim(3) para todos** (decisão de trabalho; SE(3) e escala por passo gravados para sensibilidade), RPE (Δ = 1 s), latência, memória de GPU. Uma execução **falha** se cai, dá timeout ou rastreia < 50%; o ATE só agrega execuções que não falharam.
- **Critério de robustez relativo:** rastreamento ≥ 80% em ≥ 75% das sequências **e** degradação mediana do ATE ≤ 50% da própria condição original (o critério absoluto da proposta, ATE < 0,3 m, é inatingível na original: 0 de 16 sequências para o TartanVO no artigo do QueensCAMP). Com X = 25%, 50% ou 100%, 38 das 40 combinações mantêm o veredito.
- **Estatística:** unidade = sequência (mediana das repetições, n = 16 pareado), Wilcoxon pareado, r bisserial de postos, IC 95% bootstrap (10.000), Bonferroni por família; testes com < 6 pares não recebem p.

### 5. Resultados

**5.1 Reprodução do QueensCAMP (Tab. 1).** Com Sim(3), o TartanVO fica a 1,03× do artigo (mediana das 16 sequências; erro relativo mediano 12%; Spearman 0,76). O ORB-SLAM2 RGB-D fica a 1,04× nas 11 sequências com valor no artigo e rastreamento ≥ 50% na nossa execução (17%; Spearman 0,92). **Lacuna:** o RGB-D perde o rastreamento nas sequências 02 (19% rastreado; artigo 0,24 m), 14 (3%; 0,52 m) e 15 (cai depois de reset, nas 5 sementes; 0,56 m), e não há valor do artigo para 08 e 10; a causa não foi investigada.

| Seq | TartanVO artigo | TartanVO nosso | RGB-D artigo | RGB-D nosso (execuções válidas) | RGB-D rastreado |
|---|---|---|---|---|---|
| 01 | 0,87 | 1,01 | 0,15 | 0,18 (5/5) | 1,00 |
| 02 | 0,38 | 0,39 | 0,24 | – (0/5) | 0,19 |
| 03 | 0,90 | 0,74 | 0,10 | 0,10 (5/5) | 1,00 |
| 04 | 1,13 | 0,98 | 0,66 | 0,44 (5/5) | 1,00 |
| 05 | 0,80 | 0,88 | 0,97 | 0,89 (5/5) | 1,00 |
| 06 | 0,63 | 0,52 | 0,53 | 0,69 (5/5) | 1,00 |
| 07 | 0,63 | 0,45 | 0,63 | 0,71 (5/5) | 1,00 |
| 08 | 0,70 | 0,74 | – | – (0/5) | 0,09 |
| 09 | 0,45 | 0,50 | 0,15 | 0,15 (5/5) | 1,00 |
| 10 | 0,57 | 0,59 | – | – (0/5) | 0,12 |
| 11 | 0,55 | 0,67 | 0,16 | 0,15 (5/5) | 1,00 |
| 12 | 0,75 | 1,02 | 0,24 | 0,15 (5/5) | 0,57 |
| 13 | 0,61 | 0,78 | 0,27 | 0,33 (5/5) | 1,00 |
| 14 | 0,94 | 0,94 | 0,52 | – (0/5) | 0,03 |
| 15 | 0,97 | 0,96 | 0,56 | – (0/5) | 0,00 |
| 16 | 0,63 | 0,62 | 0,29 | 0,39 (5/5) | 1,00 |

ATE em metros, mediana das sementes das execuções válidas. Fonte: `results/metrics.csv`, condição `original`.

**5.2 Taxa de sucesso (Tab. 2).** Execução com status `ok` e rastreamento ≥ 50% (`protocolo_experimental.md` §10.3):

| % | DPVO | TartanVO | ORB-SLAM2 RGB-D | ORB-SLAM2 mono |
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

\* 75 das 80 execuções de `wet` do RGB-D são marcadas degeneradas (a trajetória quase não anda).

**5.3 Robustez e degradação (Tab. 3, Fig. 2).** Pelo critério relativo, **DPVO e TartanVO são robustos** à original, sub e superexposição e aos três níveis de fumaça, e **não** a quebra, lente molhada, condensação e sujeira; **nenhuma variante do ORB-SLAM2 é robusta a nenhuma condição** (a cobertura de rastreamento já não atinge 75% na original: 62,5% das sequências no RGB-D e 12,5% no monocular). Degradação mediana do ATE contra a própria original (Sim(3), %):

| | breakage | wet | condensation | dirt | smoke_leve | smoke_moderada | smoke_densa |
|---|---|---|---|---|---|---|---|
| DPVO | 457 | 533 | 287 | 564 | 2,4 | −0,1 | 5,7 |
| TartanVO | 81 | 112 | 103 | 68 | −0,5 | 0,4 | 2,6 |
| ORB-SLAM2 RGB-D | 372 | 430 | 277 | 138 | 5,0 | 10,9 | sem ATE |
| ORB-SLAM2 mono | 1787 | sem ATE | sem ATE | 434 | 32,4 | 14,0 | sem ATE |

(mono: o ATE vem de poucas sequências com rastreamento ≥ 50%, ver Tab. 2; não é ranqueado.) Dos 36 testes contra a original (Wilcoxon pareado, Bonferroni), **9 são significativos: as 4 falhas de lente no DPVO e no TartanVO (8) e a lente molhada no ORB-SLAM2 RGB-D**; nenhuma condição de fumaça difere significativamente da original em DPVO e TartanVO. Entre métodos, só 3 dos 54 pares são significativos (DPVO pior que TartanVO em `breakage`, `dirt` e `wet`). ATE absoluto na original (Sim(3), mediana das sequências): DPVO 0,25 m, TartanVO 0,74 m.

**5.4 Falha × deriva.** O ORB-SLAM2 falha (perde o rastreamento ou não inicializa: fumaça densa 0% de sucesso; sujeira e condensação; ver Tab. 2); o DPVO e o TartanVO continuam rastreando (rastreamento 1,0) e acumulam erro (Tab. 3). A exceção do DPVO é `wet` e `condensation`, onde 18 execuções terminam com a trajetória parada e são contadas como perda de rastreamento (`protocolo_experimental.md` §10.4).

**5.5 Fumaça extrema, V = 3 m (exploratória, DPVO e TartanVO).** 112/112 execuções `ok`, nenhuma trajetória parada: **não há ponto de quebra** até transmissão 0,09. O custo é de precisão: degradação mediana +23,6% no DPVO (+5,7% na densa; Bonferroni 0,015) e +13,0% no TartanVO (+2,6%; Bonferroni 6,1e-5; as 16 sequências pioram). No DPVO é desigual: 3 sequências passam de +100% (06 +695%, 05 +317%, 15 +129%) e a correlação entre a transmissão média e a degradação é ρ = −0,70 (p = 0,003, n = 16); no TartanVO não há relação (ρ = −0,31, p = 0,25).

**5.6 Dehazing (DCP; Tab. 6; exploratória, só ORB-SLAM2).** Taxa de sucesso (execuções válidas / 80; 16 sequências × 5 sementes), sem e com DCP:

| ORB-SLAM2 | original | moderada | densa |
|---|---|---|---|
| RGB-D | 55 → 50 (68,8% → 62,5%) | 50 → 49 (62,5% → 61,3%) | **0 → 50 (0% → 62,5%)** |
| monocular | 26 → 13 (32,5% → 16,3%) | 11 → 11 (13,8% → 13,8%) | 0 → 7 (0% → 8,8%) |

*RGB-D:* na densa o DCP devolve o rastreamento em 10 das 11 sequências em que o método rastreia na original (50/55 execuções, contra 55/55); a 16 não volta e também falha com o DCP sem fumaça. As 5 sequências que já falham na original (02, 08, 10, 14, 15) continuam sem execução válida. O erro, porém, não volta ao da imagem limpa: nas 10 sequências recuperadas o ATE passa de 0,255 para 0,324 m (diferença percentual mediana +11%, 8 de 10 piores; p = 0,014 sem correção, comparação pós-hoc). Na imagem limpa o ATE não muda (0,255 → 0,252 m, p = 0,557), mas o sucesso cai 6,3 pontos por causa da seq. 16, e na moderada não há efeito (p = 0,131; Bonferroni 0,262). *Monocular:* o DCP não recupera o método na densa (7/80, em duas sequências; 27 das 80 execuções ainda não inicializam) e o prejudica na imagem limpa (o sucesso cai pela metade; 4 das 7 sequências que rastreavam perdem todas as execuções). *DPVO e TartanVO:* só o piloto da seq. 09 (n = 1), sem efeito fora da variação das sementes; como mantêm 100% de sucesso, não há falha a corrigir e o DCP completo não foi rodado neles. O DCP é, portanto, uma mitigação para o RGB-D na fumaça densa, não uma correção geral (hipótese de `protocolo_experimental.md` §10.7 parcialmente confirmada). `results/stats_dcp.csv`.

**5.7 Custo (Tab. 4).** Medianas na condição original: DPVO 29,3 ms por quadro (pico de GPU 710 MiB); TartanVO 22,1 ms com 8 CPUs e 80,3 ms com 2 (237 MiB); ORB-SLAM2 12,9 ms (RGB-D) e 9,5 ms (mono), só tracking. Os tempos não são comparáveis entre famílias (o ORB-SLAM2 mede só o tracking) e o do TartanVO depende do `--cpus` do container.

### 6. Discussão (esboço)
- **Por que a fumaça quase não afeta os métodos aprendidos e destrói o ORB-SLAM2:** a fumaça densa reduz os pontos ORB a ~6% da cena limpa (Tab. de validação), o que inviabiliza inicialização e rastreamento por *features*; os métodos aprendidos usam fluxo óptico ou *patches* aprendidos e continuam produzindo pose, com custo de precisão que só aparece na extrema. **[hipótese, não testada aqui: não medimos o que o DPVO e o TartanVO usam para continuar rastreando. Ressalva: o TartanAir, onde ambos foram treinados, inclui clima simulado com névoa (`trabalhos_relacionados.md` §6); não sabemos se as trajetórias com névoa entraram no treino, então a robustez à fumaça pode vir do treino e não do desenho do método]**
- **Por que as falhas de lente invertem o quadro:** o template de lente é estático no quadro e contamina o fluxo/patches com uma estrutura fixa que não se move com a cena; os métodos aprendidos derivam. **[hipótese, não testada]**
- **Implicações para o SAGRES-Pro:** em fumaça, um front-end aprendido mantém a navegação com perda moderada; sujeira e umidade na lente são o risco maior. **[PENDENTE: gap de domínio com dados de campo, NATASHA-13/14; sem eles não afirmar nada sobre a Amazônia]**
- **Limitações (ver abaixo).**

### 7. Conclusão
**[PENDENTE: escrever depois de 5.6 completo e de a mensagem central ser confirmada com o orientador.]**

---

## Figuras e tabelas planejadas
| # | Conteúdo | Gerada por | Estado |
|---|---|---|---|
| Fig. 1 | Exemplos: original, 3 níveis de fumaça, 1 falha de lente, fumaça real do SubT-MRS | montagem manual; `results/figures/smoke_real_vs_sintetica.png` existe (quadros reais **fora do git**, licença não declarada) | falta a montagem final (usar só quadros sintéticos no repositório) |
| Fig. 2 | Mapa de calor da degradação do ATE (método × condição) | `figures.py` → `degradacao_heatmap` | gerada |
| Fig. 3 | Erro cumulativo em original / molhada / fumaça densa | `figures.py` → `erro_cumulativo` | gerada |
| Fig. 4 | Rastreamento por condição | `figures.py` → `rastreamento` | gerada |
| Fig. 5 | Trajetórias GT × estimativa em um caso ilustrativo | `figures.py --trajectory` | gerada (`trajetoria_dpvo_09_original_s0`) |
| Tab. 1 | Reprodução do QueensCAMP | `results/metrics.csv` | acima (5.1) |
| Tab. 2 | Taxa de sucesso | `results/summary.csv` | acima (5.2) |
| Tab. 3 | Degradação, robustez e testes | `stats_report.md` | acima (5.3) |
| Tab. 4 | Latência e memória | `metrics.csv` | acima (5.7) |
| Tab. 5 | Fumaça sintética × real | `validate_smoke.py` / `nota_niveis_fumaca.md` | acima (3) |
| Tab. 6 | DCP: taxa de sucesso do ORB-SLAM2 sem e com dehazing | `results/stats_dcp.csv`, `metrics.csv` | acima (5.6) |

## Contribuições (rascunho, ajustar após a reunião)
1. Um protocolo de avaliação com **configuração justa entre paradigmas** (escala, stride, loop closure) e **análise estatística pareada** com repetições, aberto e reproduzível em Docker para GPUs Blackwell.
2. **Fumaça emulada sobre profundidade medida e comparada a fumaça real**, combinada às falhas de lente do QueensCAMP.
3. Evidência de **como a degradação se manifesta** (falha × deriva) em ORB-SLAM2, TartanVO e DPVO, e da utilidade (ou não) do dehazing clássico.
4. ~~Estudo de caso descritivo com dados coletados na Amazônia~~ **[PENDENTE: depende da coleta de campo, NATASHA-13/14; sem os dados, remover a contribuição]**.

## Limitações a declarar
1. **Fumaça homogênea e indoor:** Koschmieder com β constante, sem heterogeneidade, em cenas internas do QueensCAMP; a validação usa uma só sequência real, de outra cena e câmera.
2. **Fumaça leve e moderada são mais brandas que a fumaça rala real**; a extrema é mais severa que qualquer trecho real (Seção 3).
3. **Reprodução incompleta do ORB-SLAM2 RGB-D:** sequências 02, 14 e 15 não rastreiam, causa não investigada; 35 execuções caem por *segfault* depois de reset do mapa (também com loop closure ligado; `protocolo_experimental.md` §10.2) e entram como perda de rastreamento.
4. **ORB-SLAM2 monocular:** 68% das execuções não têm resultado válido já na original; o ATE vem de poucas sequências e o método não é ranqueado.
5. **TartanVO:** só 2 repetições (determinístico); tempo por quadro depende de `--cpus`.
6. **Alinhamento Sim(3) para todos** (decisão de trabalho, a confirmar): o veredito de robustez não muda com SE(3) no RGB-D nem com escala por passo nos monoculares; a magnitude muda (ex.: TartanVO em `breakage`, 81% com Sim(3) e 233% com escala por passo).
7. **Condições exploratórias** (extrema, DCP) ficam fora das famílias de Bonferroni. O DCP foi avaliado só no ORB-SLAM2 (DPVO e TartanVO só numa sequência), em um dataset, com estimativa de A por sequência e sem ajuste de parâmetros; o ATE pós-hoc do RGB-D recuperado não foi pré-registrado; a seq. 16 (o DCP quebra o RGB-D mesmo sem fumaça) e a piora do monocular na imagem limpa não foram investigadas.
8. **Não feito:** análise por estrato (dinâmicas, pouca luz, estáticas); BRISQUE; pico de RAM por execução; gap de domínio (TartanAir sintético × real).
9. As decisões de §10 do protocolo foram tomadas sem revisão do orientador.

## Pendências para fechar o artigo
- ~~DCP completo em ORB-SLAM2 (NATASHA-43) → 5.6 e Resumo~~ feito em 01/11; falta decidir com o orientador se o DCP entra na mensagem central e na conclusão, e investigar a seq. 16.
- Confirmação do orientador: venue, mensagem central, decisões de §10 (NATASHA-23).
- Referências **[ref a conferir]**: Koschmieder, Umeyama, SAL, "Failure or Drift?", Kumar et al.; texto de trabalhos relacionados ainda com itens lidos só pelo resumo (NATASHA-37).
- Dados de campo e EKF (NATASHA-13/14): bloqueio externo (coleta física).
