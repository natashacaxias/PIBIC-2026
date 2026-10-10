# Visual Odometry — Part I (Fundamentals) e Part II (Matching, Robustness, Optimization)

- **Referência:** D. Scaramuzza, F. Fraundorfer. *Visual Odometry Part I: The First 30 Years and Fundamentals.* IEEE RAM, 18(4), dez/2011. DOI 10.1109/MRA.2011.943233. F. Fraundorfer, D. Scaramuzza. *Part II.* IEEE RAM, 19(2), 2012.
- **Jira:** NATASHA-27 (ref. [2] da proposta)
- **Tema:** T1 fundamentos
- **Lido em:** 2026-10-10 (texto completo, PDF do grupo RPG/UZH)

## Problema e ideia central
VO é a estimação incremental do movimento próprio (egomotion) a partir só de câmeras. O termo foi cunhado por Nistér em 2004, por analogia com a odometria de rodas. Para funcionar, a VO pressupõe **iluminação suficiente, cena estática e com textura, e sobreposição entre frames consecutivos**. Essas são exatamente as hipóteses que fumaça, lente molhada e baixa luz quebram. Erro relativo típico de posição: 0,1–2%.

## Formulação
- Poses consecutivas se relacionam por T_k = [R_k | t_k] ∈ SE(3). A trajetória C_n é a concatenação C_n = C_{n−1}·T_n.
- O pipeline tem cinco etapas: detecção de features → correspondência (matching ou tracking) → estimação de movimento → concatenação → otimização local (*windowed bundle adjustment* nos últimos m frames).
- **VO × V-SLAM:** a VO busca consistência *local*; o SLAM busca consistência *global* (loop closure + otimização global). O SLAM é mais preciso, mas "não necessariamente mais robusto", pois um loop errado corrompe o mapa.

## Estimação de movimento (três casos)
| Caso | Entrada | Solver mínimo | Observação |
|---|---|---|---|
| 2D-2D | features nos dois frames | 5 pontos (Nistér), calibrado; 8 pontos (Longuet-Higgins) | monocular, escala desconhecida |
| 3D-3D | pontos triangulados nos dois instantes | 3 pontos | pior: incerteza da profundidade triangulada |
| 3D-2D | pontos 3D do frame anterior + projeções atuais | P3P (PnP) | o mais usado na prática |

- **Monocular:** escala só "até um fator". A distância entre os dois primeiros frames é fixada em 1, e a escala vem de outro sensor ou de restrições.
- **Estéreo** dá escala métrica, mas degenera para monocular quando a cena está muito mais longe que a baseline.
- **Keyframes:** pular frames até a incerteza dos pontos triangulados cair abaixo de um limiar. Os autores afirmam que a seleção de keyframes "deve sempre ser feita antes de atualizar o movimento".

## Parte II: robustez
- Detectores de canto (Harris, Shi-Tomasi, FAST) e de blob (SIFT, SURF, CENSURE); compromisso entre repetibilidade e custo.
- **Outliers** vêm de ruído, oclusão, *blur* e mudanças de iluminação que o modelo do descritor não cobre. Os autores chamam a rejeição de outliers de "a tarefa mais delicada da VO".
- **RANSAC:** N = log(1−p) / log(1−(1−ε)^s). N cresce exponencialmente com o tamanho s do conjunto mínimo, daí o interesse em solvers mínimos (5 → 3 → 1 ponto). **O RANSAC é não determinístico**: execuções diferentes dão soluções diferentes.
- O erro se acumula (propagação de covariância). A deriva é reduzida por pose-graph com restrições de loop ou por *windowed BA*.

## Relevância para este PIBIC
- As degradações estudadas atacam diretamente as hipóteses da VO: **fumaça** reduz contraste e textura; **lente molhada/sujeira** cria falsas correspondências (outliers); **sub/superexposição** viola a iluminação suficiente.
- O não determinismo do RANSAC justifica **repetir execuções também no ORB-SLAM2**, não só nos métodos aprendidos (ver `docs/protocolo_experimental.md`).
- A distinção VO × SLAM justifica **desabilitar o loop closure** do ORB-SLAM2 para comparar com TartanVO e DPVO, que são VO pura.

## Reprodutibilidade
Tutorial, sem código. Sugestão de código didático: implementar 2D-2D com OpenCV (`findEssentialMat` + `recoverPose`) numa sequência do QueensCAMP como exercício.
