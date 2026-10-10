# Plano de coleta do dataset piloto amazônico — v0.1

Jira: NATASHA-13 (coleta) e NATASHA-14 (poses de referência). Rascunho de 10/10/2026, **independente do hardware**. Os itens marcados com [HW] dependem das respostas da seção 1.

## 1. Perguntas sobre o hardware (responder antes de detalhar)
1. Firmware da controladora Pixhawk: **PX4** ou **ArduPilot**? Qual versão?
2. Câmera: modelo, resolução, fps, **global ou rolling shutter**, foco fixo? Haverá câmera RGB-D (qual)?
3. Computador de bordo (Jetson, Raspberry Pi, nenhum)? Onde as imagens são gravadas?
4. A câmera aceita disparo externo (trigger por hardware) ou só gravação contínua?
5. Quem pilota e quem é o responsável pelo cadastro do drone (SISANT/ANAC) e pelas autorizações de voo (DECEA)? [verificar as exigências para o local e o peso do drone]

## 2. O que a proposta exige
- Pelo menos **6 sequências curtas (1–3 min)**: bordas de mata urbana em Manaus e áreas de alta umidade matinal.
- Pose de referência pelo **EKF do Pixhawk** (GPS + IMU), sincronizada com a câmera via **trigger MAVLink**. Em trechos com GPS degradado, **marcadores ArUco**.
- Avaliação **só com métricas relativas** (RPE, deriva %), porque o EKF tem erro absoluto de ~1–3 m. É um estudo de caso descritivo.
- **Contingência:** o trabalho continua válido sem o piloto.

## 3. Antes do campo
- [ ] **Calibração intrínseca** da câmera com tabuleiro (OpenCV) ou AprilGrid (Kalibr), na resolução e no foco usados em voo. Guardar as imagens de calibração e o resultado (`calib.yaml`) no repositório de dados.
- [ ] **Calibração câmera–IMU** (extrínseca e atraso de tempo) com Kalibr, se for usar a atitude do EKF para comparar rotações [HW].
- [ ] **Sincronização** [HW]:
  - PX4: feedback de captura (tópico `camera_capture` no ULog) ou mensagem MAVLink `CAMERA_TRIGGER`.
  - ArduPilot: mensagens `CAM`/`TRIG` no log DataFlash.
  - Sem trigger: gravar o relógio do computador de bordo e o `SYSTEM_TIME` do MAVLink e estimar o deslocamento por correlação de rotação (IMU × VO).
- [ ] **Teste em solo:** gravar 1 min parado e 1 min caminhando com o drone na mão (como no QueensCAMP) e rodar o pipeline completo antes do voo.
- [ ] **Marcadores ArUco:** imprimir 4–6 marcadores (dicionário 4x4, 20–30 cm), medir o tamanho real e fixá-los nos trechos sob dossel.

## 4. Sequências planejadas
| # | Local / condição | Duração | Objetivo |
|---|---|---|---|
| S1 | Borda de mata, céu aberto, meio-dia | 1–2 min | referência com bom GPS |
| S2 | Borda de mata, manhã úmida (névoa natural, se houver) | 1–2 min | degradação real por umidade |
| S3 | Sob dossel parcial, com ArUco | 1–2 min | GPS degradado; referência local |
| S4 | Vegetação densa, sombras fortes | 1–2 min | iluminação irregular |
| S5 | Repetição de S1 ou S2 em outro horário | 1–2 min | variabilidade |
| S6 | Trajeto com retorno ao ponto inicial | 2–3 min | deriva medida pelo fechamento do laço |

A S6 permite uma métrica independente do EKF: o erro de fechamento (distância entre o início e o fim / comprimento percorrido).

## 5. Em campo — ficha por sequência
`data/piloto/<data>_<seq>/LEIAME.txt`: data e hora, local (coordenadas), condição do céu, umidade relativa e temperatura (do termo-higrômetro ou do INMET), vento, configuração da câmera (exposição automática ou fixa), arquivo de log do Pixhawk, arquivos de vídeo/imagens, observações (lente embaçada? gotas?) e fotos da cena.

## 6. Depois do campo — processamento (NATASHA-14)
1. Extrair as imagens (PNG) e os timestamps.
2. Extrair as poses do EKF do log [HW]:
   - PX4 (ULog, `pyulog`): `vehicle_local_position` (x, y, z NED) + `vehicle_attitude` (quatérnio);
   - ArduPilot (DataFlash, `pymavlink`): `XKF1`/`POS` + `ATT`.
3. Converter para o formato **TUM** do pipeline (`t tx ty tz qx qy qz qw`, NED → ENU ou referencial da câmera) e interpolar nos instantes das imagens.
4. Montar a sequência no mesmo layout do QueensCAMP para reutilizar `experiments/` sem alterações (só um novo `config` com os intrínsecos do piloto).
5. Avaliar com RPE em metros e % do deslocamento e com o erro de fechamento (S6). **Sem ATE absoluto.**

O conversor de log para TUM será escrito depois das respostas da seção 1 (formato e tópicos dependem do firmware).
