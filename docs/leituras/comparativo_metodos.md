# Tabela comparativa dos métodos de VO

Jira: NATASHA-32. Fontes: fichamentos desta pasta (lidos em 10/10/2026). "Proposta" indica o papel de cada método no PIBIC.

| Método | Paradigma | Entrada usada nos artigos | Treino | Back-end | Determinismo | GPU (artigo) | Código / licença | Proposta |
|---|---|---|---|---|---|---|---|---|
| ORB-SLAM2 (2017) | Clássico, features ORB + BA | mono, estéreo, **RGB-D** | — | BA local + loop + BA global | **Não** (RANSAC, threads); autores usam mediana de 5 execuções | CPU | raulmur/ORB_SLAM2, GPLv3 | Baseline clássico, **loop desligado** |
| ORB-SLAM3 (2021) | Clássico, features + Atlas multi-mapa | mono, estéreo, RGB-D, ±IMU | — | idem + fusão de mapas | Não | CPU | UZ-SLAMLab/ORB_SLAM3, GPLv3 | Extensão opcional |
| DSO (2018) | Clássico **direto** esparso | mono (+calib. fotométrica) | — | janela deslizante (7 KF) | Quase (multithread) | CPU | JakobEngel/dso, GPLv3 | Extensão (sensível a rolling shutter) |
| TartanVO (2020) | Aprendido: fluxo (PWC-Net) + rede de pose | mono, pares de frames | TartanAir (sintético) | **nenhum** (frame a frame) | Sim na inferência | ~40 ms/par em GTX 1080 | castacks/tartanvo | Método aprendido do QueensCAMP |
| DROID-SLAM (2021) | Aprendido: GRU + Dense BA | mono, estéreo, RGB-D | TartanAir mono | BA global + loop | Quase | frontend 8 GB; até 24 GB | princeton-vl/DROID-SLAM, BSD-3 | Alternativa ao DPVO (usar só como VO) |
| DPVO (2023) | Aprendido: patches esparsos + BA diferenciável | mono | TartanAir | janela (VO pura) | **Não** (patches aleatórios); mediana de 5 execuções | **4,9 GB**, ~60 FPS | princeton-vl/DPVO, MIT | Método recente prioritário |

## Leituras para a comparação

1. **Escala:** TartanVO, DPVO, DSO e o ORB-SLAM2 monocular só estimam a trajetória **até a escala** → alinhamento Sim(3). O ORB-SLAM2 RGB-D dá escala métrica → SE(3). O QueensCAMP comparou ORB-SLAM2 **RGB-D** com TartanVO (monocular): os dois números não são comparáveis diretamente.
2. **Back-end:** só o ORB-SLAM2/3 e o DROID-SLAM têm loop/BA global. Para a comparação "VO pura" da proposta, desligar o loop do ORB-SLAM2 e usar o DROID-SLAM sem backend global.
3. **Repetições:** ORB-SLAM2 e DPVO são não determinísticos e os próprios autores usam mediana de 5. TartanVO é determinístico na inferência; uma execução basta, mas convém confirmar com 2 sementes.
4. **Domínio de treino:** todos os aprendidos foram treinados só no TartanAir (sintético). O QueensCAMP é real e indoor. Isso justifica usar a degradação **relativa** à condição original de cada método.
5. **Memória:** o DPVO (4,9 GB) cabe na RTX 5070 Ti (16 GB) com folga; o DROID-SLAM completo pode não caber.
