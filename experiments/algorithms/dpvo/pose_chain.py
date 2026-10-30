"""get_pose do DPVO sem recursão.

No DPVO oficial, `get_pose(t)` de um quadro que o filtro de movimento descartou chama `get_pose` do quadro anterior,
e assim por diante até um keyframe. Quando muitos quadros seguidos são descartados (por exemplo, gotas na lente que
quase não mudam a imagem), a cadeia passa de 1000 níveis e o `terminate()` morre com RecursionError antes de gravar
a trajetória. Esta versão percorre a mesma cadeia num laço e faz as mesmas multiplicações, na mesma ordem.
"""


def iterative_get_pose(SE3):
    def get_pose(self, t):
        deltas = []
        while t not in self.traj:
            t, dP = self.pg.delta[t]
            deltas.append(dP)
        pose = SE3(self.traj[t])
        for dP in reversed(deltas):
            pose = dP * pose
        return pose

    return get_pose
