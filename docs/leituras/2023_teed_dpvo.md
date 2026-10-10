# Deep Patch Visual Odometry (DPVO)

- **Referência:** Z. Teed, L. Lipson, J. Deng. NeurIPS 2023. arXiv:2208.04726
- **Jira:** NATASHA-31 (ref. [21])
- **Tema:** T3 deep learning
- **Lido em:** 2026-10-10 (texto completo, ar5iv)

## Problema e ideia central
VO monocular aprendida que rastreia **patches esparsos** em vez de fluxo denso. Um operador recorrente revisa as trajetórias dos patches, e um BA diferenciável atualiza poses e profundidades. Os autores defendem que a correspondência por patches é mais eficiente e mais robusta que o fluxo denso.

## Método
- **Patches em posições aleatórias** (96 por frame no padrão, 48 no modo *Fast*). A amostragem aleatória superou SIFT, ORB, SuperPoint e pixels de alto gradiente.
- Treino supervisionado no TartanAir: 240 mil iterações, ~3,5 dias numa RTX 3090.
- VO pura: **sem loop closure nem BA global**.

## Avaliação (ATE médio, Sim(3) no evo)
- TartanAir test: 0,21 (DROID-SLAM 0,33).
- EuRoC: 0,105 (DROID-VO 0,186).
- TUM-RGBD (monocular): 0,089.
- ICL-NUIM: 0,097.
- **Mediana de 5 execuções** com conjuntos aleatórios de patches diferentes.

## Custo
| Configuração | FPS | Memória GPU |
|---|---|---|
| DPVO padrão | ~60 | 4,9 GB |
| DPVO Fast | ~120 | 2,5 GB |
| DROID-VO | ~40 | 8,7 GB |

## Relevância para este PIBIC
- **Método recente prioritário da proposta.** A memória de 4,9 GB cabe com folga na RTX 5070 Ti (16 GB).
- **A aleatoriedade dos patches justifica as 5 repetições com sementes distintas**, que é exatamente o protocolo dos autores. É preciso fixar a semente (`torch`, `numpy`, `random`) e registrá-la.
- A avaliação é monocular com Sim(3), consistente com a proposta de usar comparação monocular.
- **Hipótese para o artigo:** a amostragem aleatória de patches pode ser mais robusta a degradações localizadas (sujeira, gotas) do que detectores de features, porque não "persegue" cantos criados pela degradação.

## Reprodutibilidade
- Código: https://github.com/princeton-vl/DPVO (MIT). Exige CUDA, extensões compiladas e Eigen. Os autores indicam CUDA 11/12 → **verificar sm_120** no spike (NATASHA-25).
