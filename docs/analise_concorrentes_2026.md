# Análise dos trabalhos concorrentes de 2026 e recomendação

Jira: NATASHA-23 / NATASHA-37. 10/10/2026. Fontes: textos completos (arXiv HTML) e, no caso do SAL, o código-fonte (github.com/sfu-rsl/SLAMAdversarialLab, MIT, último push em 18/09/2026).

## 1. Resumo comparativo

| | **SAL** — Hefny et al., IROS 2026 | **Failure or Drift?** — Thomas et al., NeuSLAM@ECCV 2026 | **Kumar et al. 2026** (preprint) | **Este PIBIC** |
|---|---|---|---|---|
| Métodos | ORB-SLAM3, DROID-SLAM, DPVO, MASt3R-SLAM, GigaSLAM, VGGT-SLAM, Photo-SLAM… | **ORB-SLAM2, DPVO, DROID-SLAM** | ORB-SLAM3, DPVO, DROID-SLAM, DUSt3R, MASt3R | ORB-SLAM2 (mono e RGB-D), TartanVO, DPVO |
| Dados | KITTI, TUM, EuRoC, 7-Scenes | KITTI 00 (sintético) + 4Seasons (real) | TUM, EuRoC, UMA-VI, SubT-MRS + dataset próprio | QueensCAMP (16 seq. indoor reais) + piloto amazônico |
| Névoa/fumaça | Koschmieder, β = 3,912/V, profundidade do dataset ou Depth Anything V2, ruído opcional (heterogênea) | "geometry-aware" (3D Common Corruptions), modelo não descrito | "dust haze" com β 0,3–0,7; real (máquina de fumaça) no dataset próprio | Koschmieder homogêneo sobre profundidade real, **calibrado com fumaça real** (planejado) |
| Falhas de lente | sujeira, lente rachada, flare, blur | blur, ruído (imagecorruptions) | — | **6 falhas do QueensCAMP** |
| Repetições | não informado | **1 execução por condição** | não informado | **5 por método (sementes)** |
| Estatística | descritiva + busca de severidade de falha | descritiva, Spearman | t pareado (n não informado) | Wilcoxon + Bonferroni + bootstrap |
| Falha × deriva | busca da fronteira de falha | **separa falha (trajetória válida) de deriva** | TSR (erro < 2 m e < 30°) | separa (rastreamento ≥ 50%) |

## 2. O que cada um já cobre (e o que isso tira da proposta)
- **SAL** mostra que "aplicar Koschmieder com V em metros sobre a profundidade do dataset e rodar SLAMs" já é uma ferramenta publicada. **Não dá mais para alegar o modelo de névoa como contribuição.**
- **Failure or Drift?** já compara exatamente o trio ORB-SLAM2 × DPVO × DROID-SLAM sob névoa e chuva sintéticas e reais. Conclusões relevantes:
  - métodos aprendidos trocam falha por deriva;
  - **a fidelidade física da corrupção muda a ordem entre os métodos** (chuva e névoa preservam a ordem real; iluminação simples não).
- **Kumar et al.** mostra o ORB-SLAM3 falhando a partir de haze médio e o DPVO com o melhor custo-benefício. **Ressalva:** o texto tem inconsistências internas. A seção do SubT-MRS diz que ele "será" avaliado, mas há uma tabela com resultados nele; o "low light" de 6 lux fica fora do intervalo declarado de 10–30 lux. Citar com cautela.

## 3. O que continua original nesta proposta
1. **Fumaça de queimada calibrada e validada com fumaça real** (SubT-MRS "Smoke Room"). Ninguém calibra a aparência; o Failure or Drift? mostra justamente que a fidelidade importa. Dá para testar diretamente se a ordem entre métodos com fumaça sintética bate com a ordem em fumaça real.
2. **Ambiente interno real com profundidade medida (RGB-D)**, em vez de KITTI ou profundidade estimada. Combina as falhas de lente reais do QueensCAMP com fumaça no mesmo protocolo.
3. **TartanVO**, ausente dos três, com tratamento explícito e justo da escala.
4. **Rigor estatístico:** repetições com sementes, Wilcoxon + Bonferroni + bootstrap. O Failure or Drift? usa 1 execução e admite não medir a variância.
5. **Degradação relativa à própria condição original** e discussão do gap de domínio (treino sintético × dados reais indoor).
6. **Dataset piloto amazônico.** Nenhum dos três tem vegetação densa nem clima tropical.

## 4. Reusar o SAL? Recomendação: **não como infraestrutura principal; sim como referência e verificação cruzada**
**Contra adotar** (verificado no código):
- O adaptador TUM do SAL fixa a escala de profundidade em 5000 e os intrínsecos do freiburg (`src/datasets/tum.py`). O QueensCAMP (mm, intrínsecos da D435) exigiria um adaptador novo.
- Não tem **TartanVO nem ORB-SLAM2**. DPVO e DROID-SLAM só rodam em "TUM mono".
- Buracos de profundidade viram `max_depth_m` (100 m por padrão), ou seja, névoa total no buraco. Num ambiente interno é preciso ajustar ou preencher antes.
- É um framework grande (19 submódulos, podman/CDI, HAMi): curva de aprendizado alta para o escopo do PIBIC.

**A favor de usar como apoio:**
- **Verificação cruzada:** o modelo é o mesmo (`fog_base.py` aplica I = J·t + A(1−t) com β = 3,912/V). Dá para aplicar os dois numa mesma imagem com a mesma profundidade e confirmar que nossa emulação reproduz a deles. As diferenças esperadas são só arredondamento (eles truncam para uint8) e o tratamento de buracos.
- **Ideias para incorporar:**
  - a **busca da visibilidade crítica** (severidade em que cada método falha), como extensão barata usando o mesmo `run_matrix.py`;
  - o **registro do fator de escala do alinhamento Sim(3)** junto do ATE, como o SAL faz (útil para detectar trajetórias "encolhidas");
  - **névoa heterogênea** (ruído em β) como extensão futura.
- **Citar** SAL, Failure or Drift? e Kumar et al. na introdução e em Trabalhos Relacionados, posicionando o PIBIC pelos itens da seção 3.

## 5. Ajustes propostos ao plano
| Ajuste | Onde | Custo |
|---|---|---|
| Reescrever a frase de originalidade da proposta (fumaça calibrada + RGB-D real + rigor estatístico, e não "Koschmieder é inédito") | relatório parcial | baixo |
| **Teste de fidelidade:** comparar a ordem dos métodos em fumaça sintética × SubT-MRS real (inspirado no Failure or Drift?) | NATASHA-12 / análise | médio |
| Registrar o fator de escala do Sim(3) no `evaluate.py` | NATASHA-18 | baixo |
| Verificação cruzada da emulação contra o `fog_base.py` do SAL | NATASHA-11 | baixo |
| Busca da visibilidade crítica por método (extensão) | após a matriz principal | médio |
