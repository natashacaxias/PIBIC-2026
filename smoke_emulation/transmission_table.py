"""Tabela de transmissão t = exp(-beta*d) para os níveis da proposta.

Serve para checar se os níveis definidos por visibilidade (pensados para
ambiente externo) produzem degradação perceptível nas profundidades indoor
do QueensCAMP. Uso: python transmission_table.py [profundidades em metros...]
"""

import sys

from koschmieder import LEVELS_VISIBILITY_M, beta_from_visibility, transmission


def main(argv):
    depths = [float(v) for v in argv] or [1.0, 2.0, 3.0, 5.0, 8.0]
    header = "nível      V (m)   beta (1/m) | " + " ".join(f"d={d:>4.1f}m" for d in depths)
    print(header)
    print("-" * len(header))
    for name, visibility in LEVELS_VISIBILITY_M.items():
        beta = beta_from_visibility(visibility)
        values = " ".join(f"{float(transmission(d, beta)):>7.3f}" for d in depths)
        print(f"{name:<9} {visibility:>6.1f}   {beta:>9.4f}  | {values}")


if __name__ == "__main__":
    main(sys.argv[1:])
