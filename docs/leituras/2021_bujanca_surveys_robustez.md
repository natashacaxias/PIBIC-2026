# Robustez de SLAM e surveys

- **Jira:** NATASHA-33 (refs. [12][13][14][15])
- **Lido em:** 2026-10-10

## Bujanca et al., *Robust SLAM Systems: Are We There Yet?* (IROS 2021, arXiv:2109.13160) — ref. [13]
- **Sistemas:** OpenVINS, ORB-SLAM2, ORB-SLAM3 (esparsos); ElasticFusion, ReFusion, FullFusion (densos).
- **Perturbações:** movimento rápido, iluminação (exposição súbita, lanterna, noite), cenas dinâmicas e operação de longo prazo.
- **Datasets:** OpenLORIS-Scene, ETH Illumination, BONN Dynamic, EuRoC, TUM RGB-D, ICL-NUIM.
- **Protocolo:** cerca de **20 mil execuções**, **10 repetições** por experimento em 3 plataformas. Mediana do ATE-RMSE normalizada pelo comprimento da sequência. Métrica **CRT** (fração do tempo rastreando corretamente, com limiar de ATE). Controles: versões de dependências fixadas, DVFS desligado, hiperparâmetros dos autores.
- **Achados:** sistemas esparsos foram mais robustos que densos. ORB-SLAM2/3 quase não sofrem com iluminação (descritores ORB), mas falham em dinâmica severa e em corredores sem textura. **ORB-SLAM2/3 deram segfault em mais de 10% das execuções.**
- **Lacuna declarada:** clima e visibilidade limitada ficam como trabalho futuro. Esse é o espaço desta proposta.
- **Para o PIBIC:** copiar o rigor do protocolo (repetições, mediana, dependências fixadas, CRT) e tratar crashes como falha registrada.

## Tourani et al., *Visual SLAM: What Are the Current Trends and What to Expect?* (Sensors 22(23):9297, 2022; arXiv:2210.10491) — ref. [14]
- Classifica 45–50 trabalhos por sensor, ambiente, tipo de feature (manual × aprendida), dataset e objetivo.
- **Tendências:** TUM RGB-D, EuRoC e KITTI dominam a avaliação; mais da metade trata cenas dinâmicas; o ORB-SLAM é a base mais comum.
- **Desafios abertos:** custo × precisão, confiabilidade dos componentes aprendidos, ambientes sem textura e baixa iluminação. **Clima não é discutido.**

## Tosi et al., *How NeRFs and 3D Gaussian Splatting are Reshaping SLAM* (arXiv:2402.13255, v3 2025) — ref. [15]
- Taxonomia por sensor (RGB-D, RGB, LiDAR) × representação (NeRF, 3DGS, híbrida), com rastreamento acoplado ou desacoplado.
- **Para o PIBIC:** é contexto do estado da arte, mas fora do escopo experimental (métodos lentos, foco em mapeamento denso). Citar na introdução como tendência; não entra na comparação.

## Li et al., *Overview of deep learning application on visual SLAM* (Displays 74:102298, 2022, DOI 10.1016/j.displa.2022.102298) — ref. [12]
- **Acesso pago: não li o texto.** Verificar acesso pelo Portal de Periódicos CAPES/UFAM antes de citar além do nível do título.

## Síntese para a introdução
Os benchmarks clássicos (KITTI, EuRoC, TUM) não cobrem degradação óptica. A literatura de robustez anterior a 2024 cobre iluminação, dinâmica e movimento, mas deixa **clima e visibilidade como lacuna explícita** (Bujanca 2021). Essa lacuna começou a ser ocupada em 2024–2026; ver `docs/trabalhos_relacionados.md`.
