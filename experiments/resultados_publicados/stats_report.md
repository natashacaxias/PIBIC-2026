# Relatório estatístico

Parâmetros: bootstrap 10000 reamostragens (semente 0); robustez: rastreamento ≥ 0.8 em ≥ 75% das sequências e degradação mediana do ATE ≤ 50.0%. Testes com menos de 6 pares não têm p.

## Métodos comparados por condição (degradação relativa do ATE, %)

| condition | algorithm_a | algorithm_b | n | median_a | median_b | median_diff | ci_low | ci_high | effect_r | p | p_bonferroni |
|---|---|---|---|---|---|---|---|---|---|---|---|
| breakage | dpvo | orbslam2_mono | 1 | 772 | 1.79e+03 | -1.01e+03 | -1.01e+03 | -1.01e+03 | -1 | – | – |
| breakage | dpvo | orbslam2_rgbd | 5 | 1.78 | 372 | -173 | -1.4e+03 | 430 | -0.467 | – | – |
| breakage | dpvo | tartanvo | 16 | 457 | 81.3 | 377 | 155 | 587 | 0.897 | 0.00058 | 0.0122 |
| breakage | orbslam2_mono | orbslam2_rgbd | 0 | – | – | – | – | – | – | – | – |
| breakage | orbslam2_mono | tartanvo | 1 | 1.79e+03 | 42.8 | 1.74e+03 | 1.74e+03 | 1.74e+03 | 1 | – | – |
| breakage | orbslam2_rgbd | tartanvo | 5 | 372 | 78.1 | 311 | -42.6 | 1.32e+03 | 0.733 | – | – |
| condensation | dpvo | orbslam2_mono | 0 | – | – | – | – | – | – | – | – |
| condensation | dpvo | orbslam2_rgbd | 3 | 287 | 277 | -14 | -112 | 9.52 | -0.667 | – | – |
| condensation | dpvo | tartanvo | 15 | 287 | 108 | 169 | 33.9 | 626 | 0.767 | 0.00671 | 0.141 |
| condensation | orbslam2_mono | orbslam2_rgbd | 0 | – | – | – | – | – | – | – | – |
| condensation | orbslam2_mono | tartanvo | 0 | – | – | – | – | – | – | – | – |
| condensation | orbslam2_rgbd | tartanvo | 3 | 277 | 117 | 160 | -40.5 | 1.32e+03 | 0.667 | – | – |
| dirt | dpvo | orbslam2_mono | 4 | 605 | 434 | 384 | -349 | 882 | 0.8 | – | – |
| dirt | dpvo | orbslam2_rgbd | 8 | 679 | 138 | 415 | 251 | 738 | 0.944 | 0.0156 | 0.328 |
| dirt | dpvo | tartanvo | 16 | 564 | 68.2 | 467 | 343 | 718 | 1 | 3.05e-05 | 0.000641 |
| dirt | orbslam2_mono | orbslam2_rgbd | 3 | 596 | 625 | -453 | -531 | 829 | 0 | – | – |
| dirt | orbslam2_mono | tartanvo | 4 | 434 | 90.5 | 380 | 30.6 | 814 | 1 | – | – |
| dirt | orbslam2_rgbd | tartanvo | 8 | 138 | 65.6 | 114 | -53.1 | 500 | 0.611 | 0.148 | 1 |
| overexposure | dpvo | orbslam2_mono | 5 | 0.185 | 71.6 | -63.2 | -360 | 31.5 | -0.6 | – | – |
| overexposure | dpvo | orbslam2_rgbd | 10 | -0.372 | 3.27 | -9.93 | -14.4 | 2.51 | -0.491 | 0.193 | 1 |
| overexposure | dpvo | tartanvo | 16 | 0.612 | 0.18 | 0.668 | -2.26 | 6.83 | 0.206 | 0.495 | 1 |
| overexposure | orbslam2_mono | orbslam2_rgbd | 5 | 71.6 | 2.8 | 80.1 | -39.5 | 346 | 0.6 | – | – |
| overexposure | orbslam2_mono | tartanvo | 5 | 71.6 | 1.57 | 57.1 | -38.3 | 359 | 0.6 | – | – |
| overexposure | orbslam2_rgbd | tartanvo | 10 | 3.27 | 1.02 | 4.18 | -2.84 | 12.5 | 0.418 | 0.275 | 1 |
| smoke_densa | dpvo | orbslam2_mono | 0 | – | – | – | – | – | – | – | – |
| smoke_densa | dpvo | orbslam2_rgbd | 0 | – | – | – | – | – | – | – | – |
| smoke_densa | dpvo | tartanvo | 16 | 5.65 | 2.57 | -0.686 | -8.28 | 13.6 | 0.147 | 0.632 | 1 |
| smoke_densa | orbslam2_mono | orbslam2_rgbd | 0 | – | – | – | – | – | – | – | – |
| smoke_densa | orbslam2_mono | tartanvo | 0 | – | – | – | – | – | – | – | – |
| smoke_densa | orbslam2_rgbd | tartanvo | 0 | – | – | – | – | – | – | – | – |
| smoke_leve | dpvo | orbslam2_mono | 4 | -0.432 | 32.4 | -32.9 | -389 | 74.8 | -0.4 | – | – |
| smoke_leve | dpvo | orbslam2_rgbd | 10 | 1.28 | 4.95 | -2.4 | -7.09 | 2.56 | -0.382 | 0.322 | 1 |
| smoke_leve | dpvo | tartanvo | 16 | 2.42 | -0.529 | 1.52 | -3.31 | 5.45 | 0.118 | 0.706 | 1 |
| smoke_leve | orbslam2_mono | orbslam2_rgbd | 4 | 32.4 | -0.158 | 31.3 | -74.3 | 386 | 0.2 | – | – |
| smoke_leve | orbslam2_mono | tartanvo | 4 | 32.4 | -0.208 | 32.7 | -69.3 | 381 | 0.4 | – | – |
| smoke_leve | orbslam2_rgbd | tartanvo | 10 | 4.95 | -0.501 | 4.52 | -3.42 | 13.6 | 0.455 | 0.232 | 1 |
| smoke_moderada | dpvo | orbslam2_mono | 3 | -2.93 | 14 | -16.9 | -489 | 50.8 | -0.333 | – | – |
| smoke_moderada | dpvo | orbslam2_rgbd | 10 | -1.61 | 10.9 | -10 | -24.9 | -1.51 | -0.891 | 0.00977 | 0.205 |
| smoke_moderada | dpvo | tartanvo | 16 | -0.106 | 0.442 | -0.517 | -5.89 | 6.37 | 0.0588 | 0.86 | 1 |
| smoke_moderada | orbslam2_mono | orbslam2_rgbd | 3 | 14 | 1.25 | 1.88 | -48.5 | 486 | 0.333 | – | – |
| smoke_moderada | orbslam2_mono | tartanvo | 3 | 14 | 2.95 | 11 | -65 | 488 | 0.333 | – | – |
| smoke_moderada | orbslam2_rgbd | tartanvo | 10 | 10.9 | 0.338 | 10.2 | -0.644 | 24.9 | 0.636 | 0.084 | 1 |
| underexposure | dpvo | orbslam2_mono | 5 | -3.31 | 87.9 | -88.1 | -678 | 32.7 | -0.733 | – | – |
| underexposure | dpvo | orbslam2_rgbd | 9 | -0.248 | 1.17 | -1.42 | -20.2 | 20.3 | 0.0222 | 1 | 1 |
| underexposure | dpvo | tartanvo | 16 | -2.52 | -2.6 | -1.39 | -3.63 | 2.29 | -0.221 | 0.464 | 1 |
| underexposure | orbslam2_mono | orbslam2_rgbd | 5 | 87.9 | 2.92 | 86.7 | -35.8 | 690 | 0.733 | – | – |
| underexposure | orbslam2_mono | tartanvo | 5 | 87.9 | -1.58 | 91.2 | -35.7 | 668 | 0.733 | – | – |
| underexposure | orbslam2_rgbd | tartanvo | 9 | 1.17 | -1.58 | 0.107 | -22.2 | 19.1 | -0.0667 | 0.91 | 1 |
| wet | dpvo | orbslam2_mono | 0 | – | – | – | – | – | – | – | – |
| wet | dpvo | orbslam2_rgbd | 11 | 533 | 430 | 30.8 | -187 | 320 | 0.0606 | 0.898 | 1 |
| wet | dpvo | tartanvo | 15 | 533 | 116 | 366 | 348 | 749 | 1 | 6.1e-05 | 0.00128 |
| wet | orbslam2_mono | orbslam2_rgbd | 0 | – | – | – | – | – | – | – | – |
| wet | orbslam2_mono | tartanvo | 0 | – | – | – | – | – | – | – | – |
| wet | orbslam2_rgbd | tartanvo | 11 | 430 | 109 | 365 | 0.719 | 1.29e+03 | 0.848 | 0.00977 | 0.205 |

## Cada condição contra a original (ATE, m)

| algorithm | condition | n | median_a | median_b | median_diff | ci_low | ci_high | effect_r | p | p_bonferroni |
|---|---|---|---|---|---|---|---|---|---|---|
| dpvo | breakage | 16 | 1.36 | 0.25 | 1.09 | 0.668 | 1.53 | 0.926 | 0.000305 | 0.00732 |
| dpvo | condensation | 15 | 1.29 | 0.232 | 0.967 | 0.326 | 1.44 | 1 | 6.1e-05 | 0.00146 |
| dpvo | dirt | 16 | 1.45 | 0.25 | 1.23 | 1.08 | 1.56 | 1 | 3.05e-05 | 0.000732 |
| dpvo | overexposure | 16 | 0.266 | 0.25 | 0.00143 | -0.00135 | 0.0195 | 0.338 | 0.252 | 1 |
| dpvo | smoke_densa | 16 | 0.243 | 0.25 | 0.00979 | -0.0038 | 0.0273 | 0.412 | 0.159 | 1 |
| dpvo | smoke_leve | 16 | 0.253 | 0.25 | 0.00478 | -0.0123 | 0.0107 | 0.0882 | 0.782 | 1 |
| dpvo | smoke_moderada | 16 | 0.247 | 0.25 | -8.21e-06 | -0.0067 | 0.0105 | 0.147 | 0.632 | 1 |
| dpvo | underexposure | 16 | 0.248 | 0.25 | -0.00455 | -0.0202 | -0.000175 | -0.544 | 0.0577 | 1 |
| dpvo | wet | 15 | 1.64 | 0.232 | 1.48 | 1.23 | 1.7 | 1 | 6.1e-05 | 0.00146 |
| orbslam2_mono | breakage | 1 | 2.48 | 0.131 | 2.34 | 2.34 | 2.34 | 1 | – | – |
| orbslam2_mono | condensation | 0 | – | – | – | – | – | – | – | – |
| orbslam2_mono | dirt | 4 | 1.55 | 0.267 | 1.16 | 0.815 | 1.5 | 1 | – | – |
| orbslam2_mono | overexposure | 5 | 0.484 | 0.233 | 0.376 | -0.0778 | 1.08 | 0.6 | – | – |
| orbslam2_mono | smoke_densa | 0 | – | – | – | – | – | – | – | – |
| orbslam2_mono | smoke_leve | 4 | 0.368 | 0.267 | 0.102 | -0.384 | 0.627 | 0.2 | – | – |
| orbslam2_mono | smoke_moderada | 3 | 0.343 | 0.301 | 0.0421 | -0.315 | 1.13 | 0.333 | – | – |
| orbslam2_mono | underexposure | 5 | 0.917 | 0.233 | 0.481 | -0.0767 | 1.1 | 0.733 | – | – |
| orbslam2_mono | wet | 0 | – | – | – | – | – | – | – | – |
| orbslam2_rgbd | breakage | 5 | 1.57 | 0.334 | 1.24 | 0.562 | 1.93 | 1 | – | – |
| orbslam2_rgbd | condensation | 3 | 1.6 | 0.386 | 1.07 | 0.974 | 1.49 | 1 | – | – |
| orbslam2_rgbd | dirt | 8 | 1.05 | 0.306 | 0.622 | 0.216 | 0.941 | 0.944 | 0.0156 | 0.375 |
| orbslam2_rgbd | overexposure | 10 | 0.263 | 0.255 | 0.0118 | -0.000369 | 0.0613 | 0.709 | 0.0488 | 1 |
| orbslam2_rgbd | smoke_densa | 0 | – | – | – | – | – | – | – | – |
| orbslam2_rgbd | smoke_leve | 10 | 0.246 | 0.255 | 0.00809 | -0.0158 | 0.0648 | 0.418 | 0.275 | 1 |
| orbslam2_rgbd | smoke_moderada | 10 | 0.261 | 0.255 | 0.0162 | 0.0013 | 0.138 | 0.818 | 0.0195 | 0.469 |
| orbslam2_rgbd | underexposure | 9 | 0.202 | 0.176 | 0.00177 | -0.132 | 0.0336 | -0.2 | 0.652 | 1 |
| orbslam2_rgbd | wet | 11 | 1.66 | 0.334 | 1.43 | 1.03 | 1.98 | 1 | 0.000977 | 0.0234 |
| tartanvo | breakage | 16 | 1.29 | 0.742 | 0.51 | 0.399 | 0.814 | 1 | 3.05e-05 | 0.000732 |
| tartanvo | condensation | 16 | 1.48 | 0.742 | 0.801 | 0.703 | 0.899 | 1 | 3.05e-05 | 0.000732 |
| tartanvo | dirt | 16 | 1.25 | 0.742 | 0.453 | 0.389 | 0.633 | 1 | 3.05e-05 | 0.000732 |
| tartanvo | overexposure | 16 | 0.724 | 0.742 | 0.00199 | -0.0159 | 0.0157 | 0.0147 | 0.98 | 1 |
| tartanvo | smoke_densa | 16 | 0.761 | 0.742 | 0.0152 | -0.0207 | 0.0501 | 0.324 | 0.274 | 1 |
| tartanvo | smoke_leve | 16 | 0.736 | 0.742 | -0.00326 | -0.00751 | 0.00191 | -0.324 | 0.274 | 1 |
| tartanvo | smoke_moderada | 16 | 0.737 | 0.742 | 0.00411 | -0.00957 | 0.0162 | 0.118 | 0.706 | 1 |
| tartanvo | underexposure | 16 | 0.733 | 0.742 | -0.0171 | -0.0343 | -0.00677 | -0.632 | 0.025 | 0.599 |
| tartanvo | wet | 16 | 1.53 | 0.742 | 0.82 | 0.667 | 0.974 | 1 | 3.05e-05 | 0.000732 |

## Critério de robustez

| algorithm | condition | n_sequences | frac_sequences_tracking_ok | median_ate_degradation_pct | robust |
|---|---|---|---|---|---|
| dpvo | breakage | 16 | 1 | 457 | não |
| dpvo | condensation | 16 | 0.938 | 287 | não |
| dpvo | dirt | 16 | 1 | 564 | não |
| dpvo | original | 16 | 1 | 0 | sim |
| dpvo | overexposure | 16 | 1 | 0.612 | sim |
| dpvo | smoke_densa | 16 | 1 | 5.65 | sim |
| dpvo | smoke_leve | 16 | 1 | 2.42 | sim |
| dpvo | smoke_moderada | 16 | 1 | -0.106 | sim |
| dpvo | underexposure | 16 | 1 | -2.52 | sim |
| dpvo | wet | 16 | 0.875 | 533 | não |
| orbslam2_mono | breakage | 16 | 0 | 1.79e+03 | não |
| orbslam2_mono | condensation | 16 | 0 | – | não |
| orbslam2_mono | dirt | 16 | 0 | 434 | não |
| orbslam2_mono | original | 16 | 0.125 | 0 | não |
| orbslam2_mono | overexposure | 16 | 0.125 | 71.6 | não |
| orbslam2_mono | smoke_densa | 16 | 0 | – | não |
| orbslam2_mono | smoke_leve | 16 | 0.125 | 32.4 | não |
| orbslam2_mono | smoke_moderada | 16 | 0.0625 | 14 | não |
| orbslam2_mono | underexposure | 16 | 0.125 | 87.9 | não |
| orbslam2_mono | wet | 16 | 0 | – | não |
| orbslam2_rgbd | breakage | 16 | 0.375 | 372 | não |
| orbslam2_rgbd | condensation | 16 | 0.125 | 277 | não |
| orbslam2_rgbd | dirt | 16 | 0.375 | 138 | não |
| orbslam2_rgbd | original | 16 | 0.625 | 0 | não |
| orbslam2_rgbd | overexposure | 16 | 0.562 | 3.27 | não |
| orbslam2_rgbd | smoke_densa | 16 | 0 | – | não |
| orbslam2_rgbd | smoke_leve | 16 | 0.562 | 4.95 | não |
| orbslam2_rgbd | smoke_moderada | 16 | 0.562 | 10.9 | não |
| orbslam2_rgbd | underexposure | 16 | 0.5 | 1.17 | não |
| orbslam2_rgbd | wet | 16 | 0.938 | 430 | não |
| tartanvo | breakage | 16 | 1 | 81.3 | não |
| tartanvo | condensation | 16 | 1 | 103 | não |
| tartanvo | dirt | 16 | 1 | 68.2 | não |
| tartanvo | original | 16 | 1 | 0 | sim |
| tartanvo | overexposure | 16 | 1 | 0.18 | sim |
| tartanvo | smoke_densa | 16 | 1 | 2.57 | sim |
| tartanvo | smoke_leve | 16 | 1 | -0.529 | sim |
| tartanvo | smoke_moderada | 16 | 1 | 0.442 | sim |
| tartanvo | underexposure | 16 | 1 | -2.6 | sim |
| tartanvo | wet | 16 | 1 | 112 | não |

## Condições exploratórias (fora das famílias de Bonferroni; p ajustado só entre elas)

| algorithm | condition | n | median_a | median_b | effect_r | p | p_bonferroni | frac_sequences_tracking_ok | median_ate_degradation_pct | robust |
|---|---|---|---|---|---|---|---|---|---|---|
| dpvo | dcp_original | 1 | 0.26 | 0.232 | 1 | – | – | 1 | 11.9 | sim |
| dpvo | dcp_smoke_densa | 1 | 0.248 | 0.232 | 1 | – | – | 1 | 6.99 | sim |
| dpvo | dcp_smoke_leve | 1 | 0.222 | 0.232 | -1 | – | – | 1 | -4.54 | sim |
| dpvo | dcp_smoke_moderada | 1 | 0.254 | 0.232 | 1 | – | – | 1 | 9.25 | sim |
| dpvo | smoke_extrema | 16 | 0.329 | 0.25 | 0.735 | 0.00763 | 0.0534 | 1 | 23.6 | sim |
| orbslam2_mono | dcp_original | 3 | 0.425 | 0.233 | 0 | – | – | 0.0625 | -1.22 | não |
| orbslam2_mono | dcp_smoke_densa | 2 | 0.665 | 0.182 | 1 | – | – | 0 | 210 | não |
| orbslam2_mono | dcp_smoke_leve | 1 | 0.295 | 0.548 | -1 | – | – | 1 | -46.1 | sim |
| orbslam2_mono | dcp_smoke_moderada | 2 | 0.929 | 0.39 | 0.333 | – | – | 0.0625 | 257 | não |
| orbslam2_mono | dcpn_original | 3 | 0.299 | 0.301 | -0.333 | – | – | 0 | -27.7 | não |
| orbslam2_rgbd | dcp_original | 10 | 0.252 | 0.255 | -0.236 | 0.557 | 1 | 0.5 | 0.0308 | não |
| orbslam2_rgbd | dcp_smoke_densa | 10 | 0.324 | 0.255 | 0.855 | 0.0137 | 0.0957 | 0.562 | 11.3 | não |
| orbslam2_rgbd | dcp_smoke_leve | 1 | 0.165 | 0.151 | 1 | – | – | 1 | 9.49 | sim |
| orbslam2_rgbd | dcp_smoke_moderada | 10 | 0.256 | 0.255 | 0.2 | 0.625 | 1 | 0.562 | 3.26 | não |
| orbslam2_rgbd | dcpn_original | 6 | 0.221 | 0.255 | -0.714 | 0.156 | 1 | 1 | -5.48 | sim |
| orbslam2_rgbd | dcpn_smoke_densa | 6 | 0.195 | 0.255 | 0.333 | 0.562 | 1 | 0.833 | 10.5 | sim |
| tartanvo | dcp_original | 1 | 0.482 | 0.503 | -1 | – | – | 1 | -4.13 | sim |
| tartanvo | dcp_smoke_densa | 1 | 0.369 | 0.503 | -1 | – | – | 1 | -26.7 | sim |
| tartanvo | dcp_smoke_leve | 1 | 0.469 | 0.503 | -1 | – | – | 1 | -6.66 | sim |
| tartanvo | dcp_smoke_moderada | 1 | 0.465 | 0.503 | -1 | – | – | 1 | -7.49 | sim |
| tartanvo | smoke_extrema | 16 | 0.888 | 0.742 | 1 | 3.05e-05 | 0.000214 | 1 | 13 | sim |

## DCP contra a condição de origem (ATE pareado por sequência; taxa de sucesso das duas)

| algorithm | condition | source | n | median_a | median_b | median_diff | effect_r | p | p_bonferroni | success_rate_dcp | success_rate_source |
|---|---|---|---|---|---|---|---|---|---|---|---|
| dpvo | dcp_original | original | 1 | 0.26 | 0.232 | 0.0277 | 1 | – | – | 1 | 1 |
| dpvo | dcp_smoke_densa | smoke_densa | 1 | 0.248 | 0.231 | 0.0173 | 1 | – | – | 1 | 1 |
| dpvo | dcp_smoke_leve | smoke_leve | 1 | 0.222 | 0.243 | -0.0212 | -1 | – | – | 1 | 1 |
| dpvo | dcp_smoke_moderada | smoke_moderada | 1 | 0.254 | 0.217 | 0.037 | 1 | – | – | 1 | 1 |
| orbslam2_mono | dcp_original | original | 3 | 0.425 | 0.233 | -0.00159 | 0 | – | – | 0.163 | 0.325 |
| orbslam2_mono | dcp_smoke_densa | smoke_densa | 0 | – | – | – | – | – | – | 0.0875 | 0 |
| orbslam2_mono | dcp_smoke_leve | smoke_leve | 1 | 0.295 | 0.163 | 0.132 | 1 | – | – | 0.8 | 1 |
| orbslam2_mono | dcp_smoke_moderada | smoke_moderada | 3 | 1.52 | 0.498 | 0.153 | 1 | – | – | 0.138 | 0.138 |
| orbslam2_mono | dcpn_original | original | 3 | 0.299 | 0.301 | -0.0833 | -0.333 | – | – | 0.2 | 0.743 |
| orbslam2_rgbd | dcp_original | original | 10 | 0.252 | 0.255 | -0.000334 | -0.236 | 0.557 | 1 | 0.625 | 0.688 |
| orbslam2_rgbd | dcp_smoke_densa | smoke_densa | 0 | – | – | – | – | – | – | 0.625 | 0 |
| orbslam2_rgbd | dcp_smoke_leve | smoke_leve | 1 | 0.165 | 0.157 | 0.00803 | 1 | – | – | 1 | 1 |
| orbslam2_rgbd | dcp_smoke_moderada | smoke_moderada | 10 | 0.256 | 0.261 | -0.0338 | -0.564 | 0.131 | 0.393 | 0.613 | 0.625 |
| orbslam2_rgbd | dcpn_original | original | 6 | 0.221 | 0.255 | -0.0149 | -0.714 | 0.156 | 0.469 | 1 | 1 |
| orbslam2_rgbd | dcpn_smoke_densa | smoke_densa | 0 | – | – | – | – | – | – | 0.833 | 0 |
| tartanvo | dcp_original | original | 1 | 0.482 | 0.503 | -0.0208 | -1 | – | – | 1 | 1 |
| tartanvo | dcp_smoke_densa | smoke_densa | 1 | 0.369 | 0.519 | -0.151 | -1 | – | – | 1 | 1 |
| tartanvo | dcp_smoke_leve | smoke_leve | 1 | 0.469 | 0.498 | -0.0292 | -1 | – | – | 1 | 1 |
| tartanvo | dcp_smoke_moderada | smoke_moderada | 1 | 0.465 | 0.54 | -0.0754 | -1 | – | – | 1 | 1 |
