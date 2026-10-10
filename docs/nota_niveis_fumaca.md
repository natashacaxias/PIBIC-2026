# Nota técnica: níveis de fumaça para cena interna

Jira: NATASHA-40 (NATASHA-8). 10/10/2026. **Corrige** a observação inicial do `plano_inicial.md` (§4.3), que dizia que a fumaça leve "quase não altera a imagem".

## Contexto
A proposta define três níveis por visibilidade meteorológica, V = 60 / 20 / 6 m (β = 3,912/V, limiar de contraste de 2%). O QueensCAMP foi gravado numa sala de 5 × 7,5 × 3 m, então as profundidades ficam tipicamente entre ~0,5 e ~6 m, muito menores que as distâncias para as quais V foi pensada.

## Transmissão resultante
Numa faixa ilustrativa de profundidade uniforme entre 0,5 e 6 m:

| Nível | V (m) | β (m⁻¹) | MOR 5% (m) | t(1 m) | t(3 m) | t(5 m) | **t̄ [0,5; 6] m** |
|---|---|---|---|---|---|---|---|
| leve | 60 | 0,065 | 46,0 | 0,94 | 0,82 | 0,72 | **0,81** |
| moderada | 20 | 0,196 | 15,3 | 0,82 | 0,56 | 0,38 | **0,56** |
| densa | 6 | 0,652 | 4,6 | 0,52 | 0,14 | 0,04 | **0,20** |

A fumaça leve mistura em média ~19% de luz atmosférica à imagem. É fraca, mas visível. **Os três níveis cobrem bem o intervalo útil (t̄ de 0,8 a 0,2).** Para comparação, os níveis do SAL (200 / 50 / 20 / 10 m) dariam t̄ = 0,94 / 0,78 / 0,56 / 0,34 na mesma sala: os dois mais leves quase não degradam um ambiente interno.

## Alternativa considerada: definir os níveis pela transmissão média
Fixar t̄ = 0,75 / 0,50 / 0,25 daria V ≈ 43 / 17 / 7,4 m, valores próximos dos da proposta. **Não há ganho que justifique trocar.**

## Recomendação
1. **Manter V = 60 / 20 / 6 m.** As unidades físicas são interpretáveis e comparáveis com a literatura (SAL também usa V em metros).
2. **Relatar a transmissão média medida em cada sequência**, que o `emulate_sequence.py` já grava em `smoke_meta.json`. Isso permite correlacionar a degradação da VO com t̄ e não só com V.
3. **Declarar a convenção:** V com limiar de 2% (Koschmieder). Quem usa MOR (5%, OMM), como o Sakaridis, chega a valores ~23% menores.
4. **Validar na máquina do laboratório** com os histogramas reais de profundidade (`dataset.py inspect`) e comparar com frames reais do SubT-MRS ("Smoke Room") por métricas sem referência (NATASHA-12).

## Funções de apoio (`smoke_emulation/koschmieder.py`)
- `mean_transmission(depth_m, beta)`: t̄ de um quadro.
- `beta_for_mean_transmission(depth_m, alvo)`: β que produz o t̄ desejado (para a alternativa acima, se for adotada).
