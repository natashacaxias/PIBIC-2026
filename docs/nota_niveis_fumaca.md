# Nota técnica: níveis de fumaça para cena interna

Jira: NATASHA-40 (NATASHA-8). 10/10/2026. **Corrige** a observação inicial do `plano_inicial.md` (§4.3), que dizia que a fumaça leve "quase não altera a imagem".

## Contexto
A proposta define três níveis por visibilidade meteorológica, V = 60 / 20 / 6 m (β = 3,912/V, limiar de contraste de 2%). O QueensCAMP foi gravado numa sala de 5 × 7,5 × 3 m, então as profundidades ficam tipicamente entre ~0,5 e ~6 m, muito menores que as distâncias para as quais V foi pensada.

## Transmissão resultante
Numa faixa ilustrativa de profundidade uniforme entre 0,5 e 6 m:

| Nível | V (m) | β (m⁻¹) | MOR 5% (m) | t(1 m) | t(3 m) | t(5 m) | **t̄ [0,5; 6] m** |
|---|---|---|---|---|---|---|---|
| leve | 60 | 0,065 | 46,0 | 0,94 | 0,82 | 0,72 | **0,81** |
| moderada | 20 | 0,196 | 15,3 | 0,82 | 0,56 | 0,38 | **0,56** |
| densa | 6 | 0,652 | 4,6 | 0,52 | 0,14 | 0,04 | **0,20** |

A fumaça leve mistura em média ~19% de luz atmosférica à imagem. É fraca, mas visível. **Os três níveis cobrem bem o intervalo útil (t̄ de 0,8 a 0,2).** Para comparação, os níveis do SAL (200 / 50 / 20 / 10 m) dariam t̄ = 0,94 / 0,78 / 0,56 / 0,34 na mesma sala: os dois mais leves quase não degradam um ambiente interno.

## Alternativa considerada: definir os níveis pela transmissão média
Fixar t̄ = 0,75 / 0,50 / 0,25 daria V ≈ 43 / 17 / 7,4 m, valores próximos dos da proposta. **Não há ganho que justifique trocar.**

## Recomendação
1. **Manter V = 60 / 20 / 6 m.** As unidades físicas são interpretáveis e comparáveis com a literatura (SAL também usa V em metros).
2. **Relatar a transmissão média medida em cada sequência**, que o `emulate_sequence.py` já grava em `smoke_meta.json`. Isso permite correlacionar a degradação da VO com t̄ e não só com V.
3. **Declarar a convenção:** V com limiar de 2% (Koschmieder). Quem usa MOR (5%, OMM), como o Sakaridis, chega a valores ~23% menores.
4. **Validar na máquina do laboratório** com os histogramas reais de profundidade (`dataset.py inspect`) e comparar com frames reais do SubT-MRS ("Smoke Room") por métricas sem referência (NATASHA-12).

## Funções de apoio (`smoke_emulation/koschmieder.py`)
- `mean_transmission(depth_m, beta)`: t̄ de um quadro.
- `beta_for_mean_transmission(depth_m, alvo)`: β que produz o t̄ desejado (para a alternativa acima, se for adotada).

## Validação contra fumaça real (31/10/2026, NATASHA-12)
Fonte: SubT-MRS, sequência de fumaça, `cam_0` (ver `docs/datasets.md`). Os quadros reais são recortados no centro (60%) e redimensionados para 640×480; os sintéticos são os da seq. 09 do QueensCAMP. Medianas de 60 quadros por conjunto (40 nos trechos de fumaça leve), com as funções de `smoke_emulation/image_quality.py`:

| conjunto | contraste RMS | canal escuro | densidade de bordas | entropia | pontos ORB | A estimado (DCP) |
|---|---|---|---|---|---|---|
| real, limpo (2700–5300) | 0,258 | 0,392 | 0,054 | 7,49 | 1336 | 1,00 |
| real, fumaça rala (5400–6000 e 8300–8900) | 0,121–0,128 | 0,32–0,36 | 0,022–0,025 | 6,8–6,9 | 248–321 | 0,70–0,80 |
| real, fumaça densa (6300–8100) | 0,085 | 0,491 | 0,006 | 6,38 | 17,5 | 0,74–0,76 |
| QueensCAMP original | 0,175 | 0,385 | 0,066 | 7,19 | 861 | 0,95–0,99 |
| sintética leve (V = 60 m) | 0,153 | 0,436 | 0,051 | 7,06 | 702 | 0,92–0,96 |
| sintética moderada (V = 20 m) | 0,131 | 0,518 | 0,034 | 6,72 | 424 | 0,88–0,91 |
| sintética densa (V = 6 m) | 0,070 | 0,681 | 0,006 | 5,88 | 57 | 0,82–0,83 |
| sintética extrema (V = 3 m) | 0,027 | 0,762 | 0,000 | 4,31 | 0 | 0,80 |

Cada cena tem a sua linha de base, então o que se compara é a razão fumaça/limpo:

| | contraste | bordas | pontos ORB |
|---|---|---|---|
| real, rala | 0,47–0,50 | 0,41–0,46 | 0,19–0,24 |
| real, densa | **0,33** | **0,11** | **0,013** |
| sintética leve | 0,87 | 0,77 | 0,82 |
| sintética moderada | 0,75 | 0,52 | 0,49 |
| sintética densa | **0,40** | **0,09** | **0,066** |
| sintética extrema | 0,15 | 0,00 | 0,00 |

**Leitura:**
- A **densa sintética reproduz a perda de contraste e de bordas da fumaça real densa** (0,40 contra 0,33 e 0,09 contra 0,11). Ela preserva mais pontos ORB do que a real (6,6% contra 1,3%), então é um pouco mais branda para o ORB-SLAM2 que a fumaça real mais densa.
- A **leve e a moderada sintéticas são mais brandas que a fumaça rala real** (contraste 0,87 e 0,75 contra 0,5; pontos ORB 0,82 e 0,49 contra 0,2). Os trechos de fumaça rala do SubT-MRS têm densidade desconhecida e podem ser mais densos que V = 60 e 20 m, então isto é um limite, não uma falha da emulação.
- A **extrema (V = 3 m) é mais severa que qualquer trecho real** da sequência (contraste 0,15, nenhum ponto ORB): serve como limite superior, não como realismo.
- **Luz atmosférica A = 0,8 fica.** O estimador do DCP dá 0,70–0,80 nos quadros reais de fumaça (0,74–0,76 na densa) e 0,82–0,83 na sintética densa. O A só desloca o brilho; o contraste cai com a transmissão. Na cena limpa o estimador dá ~1,0 nas duas bases (viés da cena, já conhecido).
- **Diferença visível:** a fumaça real é cinza-azulada ou amarronzada e a cena é escura (iluminada pelas lanternas da plataforma); a sintética é cinza-clara e a cena do QueensCAMP é clara. O painel `results/figures/smoke_real_vs_sintetica.png` (fora do git, por causa da licença dos quadros reais) mostra os dois lado a lado.

**Limites:** uma só sequência real, de outra cena, outra câmera (fisheye recortada) e outra iluminação; sem referência alinhada (nada de SSIM); BRISQUE não rodado (`piq` não instalado). A comparação é de ordem de grandeza.

### Sensibilidade ao preenchimento dos buracos de profundidade
Metade dos pixels de profundidade do QueensCAMP é buraco (fração média 0,50 na seq. 09), preenchidos por dilatação 3×3 (o vizinho mais distante). Em 30 quadros da seq. 09, a transmissão média e a diferença de imagem (0–255) contra o preenchimento atual, para outras duas políticas:

| V (m) | atual (dilata + máximo) | inpainting (Telea) | todo buraco = profundidade máxima |
|---|---|---|---|
| 60 | t̄ 0,880 | 0,880 (dif. 1,8) | 0,787 (dif. 7,5) |
| 20 | 0,693 | 0,697 (dif. 4,2) | 0,526 (dif. 13,3) |
| 6 | 0,347 | 0,376 (dif. 6,7) | 0,196 (dif. 12,1) |
| 3 | 0,171 | 0,238 (dif. 6,0) | 0,086 (dif. 6,8) |

**Decisão: manter o preenchimento atual.** Trocar por inpainting muda a transmissão média em até 0,03 nos três níveis principais (0,07 na extrema), bem menos que o espaçamento entre os níveis, e regenerar os 29 GB de fumaça obrigaria a repetir as 2720 execuções. A política de buracos é uma premissa: "todo buraco = máximo" daria uma fumaça bem mais densa (t̄ da densa 0,20 em vez de 0,35).

