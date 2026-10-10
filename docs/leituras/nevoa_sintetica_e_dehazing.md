# Névoa sintética, Koschmieder e Dark Channel Prior

- **Jira:** NATASHA-38 (refs. [16] e complementares)
- **Lido em:** 2026-10-10

## Modelo de Koschmieder (base comum)
I(x) = J(x)·t(x) + A·(1 − t(x)),  t(x) = exp(−β·d(x)).

**Visibilidade.** Existem duas convenções e **é preciso declarar qual se usa**:
- limiar de contraste de 2% (Koschmieder): V = 3,912/β. É a da proposta e a do SAL.
- limiar de 5% (MOR da OMM): MOR = 2,996/β. É a do Sakaridis.

**Hipóteses:** meio homogêneo, espalhamento isotrópico, A constante (válido de dia), sem distinção física entre fumaça e névoa.

## He, Sun & Tang — Dark Channel Prior (TPAMI 33(12), 2011) — ref. [16]
- **Dark channel:** mínimo sobre os canais RGB e sobre um patch (15×15 nos resultados). Em imagens externas sem névoa, ~90% dos pixels têm dark channel < 25 (estatística sobre 5.000 imagens).
- **Luz atmosférica A:** pegar os **0,1% de pixels mais brilhantes do dark channel** e, entre eles, o de maior intensidade na imagem.
- **Transmissão:** t̃ = 1 − ω·dark(I/A), com **ω = 0,95** (mantém um pouco de névoa, para efeito de profundidade). Depois refinamento por *soft matting* (a versão posterior usa *guided filter*).
- **Recuperação:** J = (I − A)/max(t, t₀) + A, com **t₀ = 0,1**.
- **Limitações:** a prior falha quando o objeto é parecido com a luz atmosférica (**parede branca, chão claro**) e quando o modelo físico não vale.
- **Para o PIBIC:** o QueensCAMP é indoor e tem superfícies claras, onde o DCP tende a "ver" névoa inexistente e escurecer a imagem. Por isso convém aplicar o DCP **também na condição original** como controle, para separar o efeito do dehazing do efeito da fumaça.
- **Verificado na implementação (`smoke_emulation/dcp.py`, 10/10/2026):** numa cena rasa com fumaça sintética (até 4 m, β = 0,3), o estimador de A escolheu um pixel ainda colorido pela cena, (0,58; 0,83; 0,58) em vez de 0,8 cinza. Com profundidade até 20 m, onde há região opaca, acertou A com erro menor que 0,05. Em ambiente interno, o DCP tende a gerar dominante de cor; isso precisa ser discutido no artigo.

## Sakaridis, Dai & Van Gool — Foggy Cityscapes (IJCV 2018, arXiv:1708.07819)
- **Precedente direto da etapa 2:** névoa sintética via Koschmieder sobre profundidade **de estéreo**, com buracos e ruído.
- **Tratamento da profundidade:** superpixels SLIC + ajuste de planos por RANSAC para completar os buracos; mostram que vizinho mais próximo gera artefatos. A transmissão é suavizada com *guided filter* (raio 20, μ = 10⁻³). A é estimada pelo dark channel.
- **Níveis:** β ∈ {0,005; 0,01; 0,02; 0,03; 0,06} m⁻¹, ou seja, MOR ≈ 600 a 50 m (cenas externas, profundidade de dezenas de metros).
- **Validação:** **indireta**, pelo ganho em segmentação em névoa real (Foggy Driving). Não fazem estudo de realismo da névoa.
- **Limitações declaradas:** homogeneidade é uma hipótese forte; cenas ensolaradas com sombras não parecem névoa real.

## Xu et al. — Customizable Perturbation Synthesis / Robust-SLAM (arXiv:2402.08125, 2024)
- **16 perturbações de imagem** (ruído, blur, clima, pós-processamento) em 3 severidades, mais perturbações de profundidade e de trajetória, sobre o Replica.
- **A névoa é uma mistura 2D com cinza constante, sem profundidade.** A emulação da proposta é fisicamente mais fiel.
- **Achados:** perturbações ambientais e blur são as mais nocivas; métodos neurais/RGB-D foram mais robustos que o ORB-SLAM3; **a precisão em cena limpa não prevê a robustez**.

## Hefny, Dantu & Ko — SLAM Adversarial Lab (IROS 2026, arXiv:2603.17165)
- **Implementa o mesmo modelo da proposta:** Koschmieder com β = 3,912/V, profundidade do próprio dataset RGB-D (ou estéreo/monocular estimada) e ruído procedural opcional em β para névoa heterogênea.
- Busca automaticamente a severidade em que cada SLAM falha.
- Código aberto: https://github.com/sfu-rsl/SLAMAdversarialLab
- **Impacto:** reduz a originalidade da "névoa por Koschmieder" e **pode ser reutilizado** em vez de reimplementar. Ver `docs/trabalhos_relacionados.md`.
