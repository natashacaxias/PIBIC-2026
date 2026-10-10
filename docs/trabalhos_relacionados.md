# Trabalhos Relacionados — rascunho v0.1

Jira: NATASHA-37. Rascunho em 10/10/2026 a partir dos fichamentos em `docs/leituras/` e da pré-triagem do corpus (IDs `Pxxxx` = `literature_review`). **Itens marcados com † foram lidos só pelo resumo**; ler o texto completo antes da versão final.

## 1. Odometria visual clássica e aprendida
A odometria visual estima o movimento próprio de forma incremental a partir de imagens, sob as hipóteses de iluminação suficiente, cena estática e com textura, e sobreposição entre frames [2]. Os métodos clássicos se dividem em baseados em features, como o ORB-SLAM2 [17] e o ORB-SLAM3 [26], que usam *bundle adjustment* sobre ORB e RANSAC para rejeitar outliers, e diretos, como o DSO [25], que minimiza o erro fotométrico e depende de calibração fotométrica. Os métodos aprendidos substituem etapas do pipeline por redes: o TartanVO [18] prevê a pose a partir de fluxo óptico, sem back-end; o DROID-SLAM [20] e o DPVO [21] combinam atualização recorrente com BA diferenciável, o primeiro denso e o segundo com patches esparsos. Os três foram treinados só no TartanAir, que é sintético, o que levanta a questão do gap de domínio para dados reais. Surveys recentes [12][14][15] documentam a migração para componentes aprendidos e representações neurais, mas tratam robustez sobretudo como iluminação e dinâmica.

## 2. Avaliação de robustez de SLAM
Bujanca et al. [13] avaliaram seis sistemas em cerca de 20 mil execuções sob movimento rápido, iluminação e dinâmica. Concluíram que sistemas esparsos são mais robustos e deixaram **clima e visibilidade limitada como lacuna explícita**. Xu et al. (2024) sintetizaram 16 perturbações de imagem sobre o Replica e mostraram que a precisão em cena limpa não prevê a robustez, mas modelaram a névoa como mistura 2D sem profundidade. O QueensCAMP [9] trouxe 16 sequências reais RGB-D com seis falhas de câmera (exposição e templates de lente quebrada, molhada, condensação e sujeira) e comparou ORB-SLAM2 (RGB-D) e TartanVO. Os resultados mostram falhas de rastreamento do ORB-SLAM2 com sujeira e condensação e uma degradação mais "suave" do TartanVO.

## 3. Degradação atmosférica e névoa sintética
O modelo de Koschmieder, com transmissão exp(−β·d), é o padrão para névoa diurna. He et al. [16] o exploraram no Dark Channel Prior para remover névoa, e Sakaridis et al. (2018) o aplicaram sobre profundidade estéreo completada para criar o Foggy Cityscapes, com MOR de 600 a 50 m e validação indireta por tarefa. Para odometria, Tan et al. (2023, P1617)† avaliaram métodos de VO com chuva em datasets reais de direção, e Ding et al. (2025, P2172)† estimam parâmetros de névoa a partir de sequências estéreo, como módulo auxiliar para SLAM.

**Trabalhos de 2026 diretamente concorrentes:**
- **SLAM Adversarial Lab — SAL** (Hefny et al., IROS 2026, P1731): implementa névoa por Koschmieder com β = 3,912/V sobre a profundidade do próprio dataset (ou estimada), com névoa heterogênea opcional e busca automática da severidade de falha. Avaliou sete sistemas (incluindo ORB-SLAM3 e DROID-SLAM) em KITTI, TUM e EuRoC. **Código aberto.**
- **Failure or Drift?** (Thomas et al., workshop NeuSLAM/ECCV 2026, P1592)†: compara corrupções sintéticas (de imagem, geométricas e compostas) com condições reais do 4Seasons em SLAM monocular clássico e aprendido. Mostra que métodos aprendidos trocam falha catastrófica por deriva e que **a ordem entre métodos depende da fidelidade física da corrupção**: proxies estruturados de chuva e névoa preservam a ordem real; um proxy simples de iluminação não.
- **Kumar et al. 2026** (P1673)†: avalia ORB-SLAM3, DPVO, DROID-SLAM, DUSt3R e MASt3R sob pouca luz, "dust haze", blur e condições combinadas (TUM, EuRoC, UMA-VI, **SubT-MRS** + dataset próprio). O ORB-SLAM3 tem 0% de rastreamento em névoa densa; o DPVO dá o melhor equilíbrio eficiência × robustez (3,1 GB).

## 4. Florestas, UAVs e Amazônia
Há datasets e métodos de VO/SLAM para floresta: FinnForest (2020, P1941)†, Windy Forest (2021, P2596)†, ForestVO (2025, P0622)†, SLAM visual-inercial para floresta (2025, P2625)† e navegação visual de UAV em floresta (2023, P2674/P2675)†. Trabalhos anteriores do grupo cobrem plataformas aéreas na Amazônia [4][5], marcos visuais em grandes áreas florestais [6] e realce de imagem em rios turvos [7]. Na pré-triagem, **nenhum trabalho avalia VO sob fumaça de queimada em floresta tropical**.

## 5. Posicionamento da proposta (a discutir com o orientador)
Com SAL, "Failure or Drift?" e Kumar et al., **a ideia de "névoa por Koschmieder para testar SLAM" não é mais original por si só**. Contribuições que continuam defensáveis:
1. **Fumaça de queimada, não névoa:** cor e densidade calibradas com fumaça real (SubT-MRS "Smoke Room") e validadas por métricas sem referência. Os trabalhos acima tratam névoa ou "dust haze".
2. **Combinação de degradações reais de lente (QueensCAMP) com fumaça** no mesmo protocolo, incluindo TartanVO e DPVO.
3. **Degradação relativa à condição original de cada método**, com separação entre falha e deriva e discussão explícita do gap de domínio (TartanAir sintético × QueensCAMP real indoor).
4. **Dataset piloto amazônico** com estudo de caso descritivo.
5. **Reuso do SAL:** avaliar adotar o SAL como infraestrutura (perturbações e busca de severidade) e concentrar o esforço em 1–4. Isso reduz risco de cronograma e aumenta a comparabilidade com a literatura.

## Pendências
- Ler na íntegra: SAL, "Failure or Drift?", Kumar et al., Tan et al. e ForestVO.
- Verificar se o TartanAir contém névoa ou fumaça (impacta o argumento de gap de domínio).
- Atualizar a afirmação de originalidade da proposta no relatório parcial.
