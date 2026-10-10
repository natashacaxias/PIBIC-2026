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
.venv/bin/python -m unittest discover -s tests          # 16 testes
.venv/bin/python transmission_table.py 1 2 3 5 8
# sequência inteira (profundidade PNG uint16 em mm → --depth-scale 1000):
.venv/bin/python emulate_sequence.py --rgb-dir RGB --depth-dir DEPTH --out-dir SAIDA --level moderada
```

```python
from koschmieder import apply_smoke, beta_from_visibility, mean_transmission
hazy = apply_smoke(rgb, depth_m, beta_from_visibility(20.0))
```

- **Buracos de profundidade:** preenchidos por dilatação 3×3 iterativa (o vizinho mais distante, ou seja, o fundo). O que sobra recebe a maior profundidade válida.
- **Metadados:** `smoke_meta.json` registra V, β, A, escala, transmissão média (média e percentis), fração de buracos e o hash do código. O processo é determinístico.
- **Orquestração:** `experiments/scripts/dataset.py smoke` aplica as três condições a todas as sequências.

## Pendências
- Rodar em sequências reais do QueensCAMP e conferir visualmente (máquina do laboratório).
- Calibrar a luz atmosférica A com frames reais do SubT-MRS (NATASHA-12).
- Validar realismo com métricas sem referência (BRISQUE, contraste, dark channel) contra fumaça real (NATASHA-12).

Justificativa dos níveis: `docs/nota_niveis_fumaca.md`.
