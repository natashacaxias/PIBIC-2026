# Emulação de fumaça (Koschmieder)

Protótipo da etapa 2 da proposta (Jira NATASHA-11).

```
I(x) = J(x)·t(x) + A·(1 − t(x)),   t(x) = exp(−β·d(x)),   V = 3,912 / β
```

| nível | V alvo | β (1/m) |
|---|---|---|
| leve | 60 m | 0,0652 |
| moderada | 20 m | 0,1956 |
| densa | 6 m | 0,6520 |

## Uso

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python -m unittest discover -s tests
.venv/bin/python transmission_table.py 1 2 3 5 8
```

```python
from koschmieder import apply_smoke, beta_from_visibility
hazy = apply_smoke(rgb, depth_m, beta_from_visibility(20.0))
```

`depth_m` deve estar em metros: converta pelo fator de escala do QueensCAMP antes.

## Pendências

- Leitura de imagens/profundidade do QueensCAMP (formato e fator de escala a confirmar).
- Inpainting dos buracos de profundidade (hoje: preenchidos com a profundidade máxima).
- Calibração de A e dos níveis com frames reais do SubT-MRS (SSIM/BRISQUE, NATASHA-12).
- Integração ao pipeline de falhas do QueensCAMP com sementes versionadas.

Ver discussão sobre os níveis em ambiente interno em `docs/plano_inicial.md` (4.3).
