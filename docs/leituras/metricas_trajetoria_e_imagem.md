# Métricas de trajetória e de qualidade de imagem

- **Jira:** NATASHA-39 (refs. [19][23][24] + complementares)
- **Lido em:** 2026-10-10

## Sturm et al. — TUM RGB-D benchmark (IROS 2012)
- **RPE** mede o erro do movimento relativo num intervalo fixo Δ, ou seja, a **deriva**. É a métrica indicada para **VO**. Com Δ = 1 dá a deriva por frame; Δ = fps dá a deriva por segundo. Também é possível tirar a média sobre todos os Δ.
- **ATE**: alinha a estimativa ao ground truth (método fechado de Horn) e calcula o RMSE das posições. É mais indicada para **SLAM** e é fácil de visualizar.
- O RPE inclui rotação e translação e é ≥ ATE. Os autores relatam que **ATE e RPE são fortemente correlacionados** e que a ordem entre métodos raramente muda.
- Profundidade do TUM: PNG 16 bits com **fator 5000** (diferente da RealSense, que usa mm → 1000).

## Zhang & Scaramuzza — *A Tutorial on Quantitative Trajectory Evaluation for VO/VIO* (IROS 2018)
| Configuração | Alinhamento |
|---|---|
| Monocular | **Similaridade Sim(3)** (7 GL) |
| Estéreo / RGB-D | **Corpo rígido SE(3)** (6 GL) |
| Visual-inercial | 4 GL (posição + yaw) |

- **ATE é sensível ao momento do erro:** um erro de rotação no início da trajetória gera ATE maior que o mesmo erro no fim. Por isso recomendam também o **erro relativo** sobre sub-trajetórias de comprimentos fixos.
- **Recomendação:** reportar os dois.

## evo (Grupp) — ferramenta da proposta [19]
- `evo_ape tum gt.txt est.txt -a` → SE(3) (Umeyama); `-as` → **Sim(3)**; `-s` → só escala; `--align_origin` → só alinha a origem.
- `evo_rpe ... --delta 1 --delta_unit f` (frames) ou `m` (metros); `-r trans_part` ou `-r angle_deg`.
- **O `evaluate.py` do QueensCAMP** usa `align=True` + `align_origin=True` e `correct_scale` opcional; RPE com Δ = 1 frame. **Reproduzir exatamente isso** ao validar os números do artigo.

## SSIM — Wang et al. (TIP 2004) [23]
- Métrica **com referência**: compara luminância, contraste e estrutura entre duas imagens **alinhadas**. Vai de 0 a 1 (1 = idêntica).
- **Uso correto aqui:** medir quanto cada nível de fumaça sintética degrada um frame em relação ao frame limpo correspondente. Isso é possível porque temos o par (limpo, com fumaça).
- **Uso incorreto:** comparar a fumaça sintética com frames reais do SubT-MRS, porque não há par alinhado.

## BRISQUE — Mittal, Moorthy & Bovik (TIP 2012) [24]
- Métrica **sem referência**: usa estatísticas de cena natural (coeficientes MSCN) num modelo treinado com notas humanas. Escore ~0–100, **menor = melhor qualidade percebida**.
- **Uso aqui:** comparar a **distribuição** de BRISQUE dos frames sintéticos com a dos frames reais de fumaça (SubT-MRS), por exemplo com o teste KS ou a distância entre histogramas. Complementar com **contraste RMS** e **média do dark channel**, que medem diretamente a "névoa" da imagem.
- **Implementação sugerida:** `piq` (PyTorch) ou `opencv-contrib` (`cv2.quality.QualityBRISQUE`, que precisa dos arquivos de modelo). Fixar a versão, porque implementações dão escores diferentes.

## Recomendações para o protocolo
1. Monocular → `evo_ape -as` e `evo_rpe -as`. ORB-SLAM2 RGB-D → `-a`.
2. Reportar ATE-RMSE, RPE (translação e rotação, Δ = 1 s) e **taxa de rastreamento**.
3. Separar **falha** (perda de rastreamento) de **deriva**, como em "Failure or Drift?" (Thomas et al., 2026).
