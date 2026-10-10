# Critérios de triagem da revisão bibliográfica

Jira: NATASHA-36. Versão 1 (10/10/2026), **a validar com o orientador**.

## Pergunta da revisão
Como métodos de odometria visual clássicos e aprendidos se comportam sob degradações ópticas e atmosféricas (fumaça, névoa, lente, exposição) e como essa robustez é avaliada (datasets, métricas, protocolos)?

## Critérios de inclusão (título/resumo)
- **I1.** Trata de VO, V-SLAM ou VIO **e** de pelo menos um entre: robustez/degradação, condições atmosféricas, datasets/benchmarks, ambientes florestais/UAV, métricas de trajetória.
- **I2.** Trata de formação de imagem em meio espalhador (névoa, fumaça, neblina) ou de dehazing **aplicado a navegação ou percepção robótica**.
- **I3.** Define ou analisa métricas de avaliação de trajetória ou de qualidade de imagem usadas neste projeto.

## Critérios de exclusão
- **E1.** Não é artigo: editorial, índice, errata, sumário, material de capa.
- **E2.** Fora do escopo: não trata de VO/SLAM, nem de degradação atmosférica em imagem, nem de métricas (ex.: plasma, redes BGP, ecologia florestal sem visão computacional).
- **E3.** Usa somente LiDAR, radar ou térmica, **sem câmera RGB**. Fica como "talvez" se discutir comparação com câmera RGB sob fumaça.
- **E4.** Duplicata ou versão superada (preprint × publicação): manter a publicação e anotar a relação.

## Pré-filtro automático (`literature_review/screening.py`)
Regras por expressões regulares no título + resumo, que geram **sugestões, não decisões**:

| Grupo | Peso | Exemplos de termos |
|---|---|---|
| core | 3 | odometry, SLAM, ego-motion, visual-inertial, camera pose |
| atmos | 2 | fog, haze, dehazing, smoke, atmospheric scattering, visibility |
| robust | 2 | robust, adverse, degradation, corruption, low-light, weather, blur, lens |
| deep | 1 | deep, learning, neural, network |
| dataset | 1 | dataset, benchmark |
| field | 1 | forest, vegetation, UAV, drone, wildfire |
| metric | 1 | ATE, RPE, trajectory evaluation, SSIM, BRISQUE |

- **E1:** o título casa com padrão de não-artigo.
- **E2:** nenhum de {core, metric, atmos + imagem/câmera}.
- **I1:** pontuação ≥ 5. As demais ficam como "talvez" (M1).

### Resultado em 10/10/2026 (corpus de 3.016 candidatos)
| Sugestão | Qtde. |
|---|---|
| INCLUDE (I1) | 674 |
| MAYBE (M1) | 1.297 |
| EXCLUDE (E2) | 1.043 |
| EXCLUDE (E1) | 2 |

Só 825 registros têm resumo; o restante foi avaliado só pelo título. Amostras aleatórias conferidas: as exclusões E2 eram de fato fora do tema (microscopia, BGP, plasma, ecologia); os "talvez" são VO genérica sem robustez.

## Ordem de trabalho sugerida
1. **Núcleo (51 artigos):** INCLUDE com core + atmos. Contém os concorrentes diretos (P1731 SAL, P1592, P1673, P1617, P2164 SubT-MRS).
2. INCLUDE com core + field (109): floresta e UAV.
3. Restante dos INCLUDE, por pontuação.
4. Amostra de 10% dos EXCLUDE E2 para estimar falsos negativos e registrar a taxa.
5. MAYBE: só por *snowballing* a partir dos incluídos.

## Como registrar decisões
```bash
cd literature_review
.venv/bin/python screening.py suggest          # gera exports/triagem_sugerida.csv
# abrir o CSV e preencher decisao_humana (INCLUDE/MAYBE/EXCLUDE) e justificativa_humana
.venv/bin/python screening.py apply exports/triagem_sugerida.csv
```
Só as linhas preenchidas são gravadas, com justificativa obrigatória. A coluna `sugestao` nunca é gravada como decisão.
