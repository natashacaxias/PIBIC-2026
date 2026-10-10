# Estado do desenvolvimento — 20/09/2026

Implementados: coleta Crossref/arXiv, normalização, corpus SQLite, deduplicação
conservadora, proveniência, fila humana, decisões e exportação JSON/RIS.

Validação: 9 testes aprovados e pilotos reais nas duas fontes. Uma repetição
recuperou os mesmos 6 registros, com 0 novos e 6 duplicatas detectadas.

A inspeção identificou baixa pertinência da busca geral Crossref. O conector foi
refinado para busca no título ordenada por relevância. A nova execução trouxe 3
candidatos Crossref mais pertinentes e reconheceu os 3 registros arXiv existentes.
O corpus tem 9 candidatos pendentes de revisão; registros iniciais irrelevantes
foram preservados para auditoria. Não são nove artigos incluídos na revisão.

Última execução: data/runs/20260920T155456Z_8237b266/summary.json.
A primeira tentativa, impedida pela restrição de rede do ambiente, permanece
registrada. Os pilotos seguintes acessaram as APIs normalmente.

Próximo incremento: integrar outras fontes e preparar a extração validada com o
schema fornecido. Triagem científica, leitura integral, extração de evidências,
validação do schema e agendamento ainda não foram implementados.

## Incremento 0.2 — preparação e validação de extrações

Implementado em extraction.py:
- download público arXiv vinculado ao identificador do corpus, com URL/data/hash;
- leitura de PDF por página física, alerta para pouco texto e bloqueio de PDF sem texto;
- pacotes versionados com PDF, texto, metadados, schema, prompt e hashes;
- validação Draft 2020-12 com verificações de identidade, referências, páginas e vínculos;
- claim_links.json separado para dar rastreabilidade às afirmações do núcleo sem alterar o schema;
- arquivamento de tentativas válidas/ inválidas e tabelas JSON de evidências;
- estado de extração na exportação, independente da decisão humana de triagem.

Verificação: 24 testes aprovados. P0004 foi baixado do arXiv e preparado:
`data/papers/P0004/bundles/20260920T160239Z_a02eb739/`.
27 páginas, 178.482 caracteres extraídos, sem alertas automáticos de pouco texto ou título.
A inspeção do início/fim confirmou título/autores e paginação. Isso não certifica tabelas,
fórmulas ou resultados científicos. Estado: EXTRACTION_PENDING; sem extração semântica real.
Os JSONs válidos usados nos testes são fixtures sintéticas em diretórios temporários,
e não foram misturados ao corpus científico.

Dependências instaladas em .venv; versões registradas em requirements-lock.txt.

Ainda pendentes: integração automática com LLM, revisão científica de evidências,
OCR, outras fontes bibliográficas, relações entre versões, snowballing, tabelas
específicas por domínio e agendamento. Não há chave de API de LLM configurada por
este incremento nem tarefa recorrente criada.

## Incremento 0.3 — saída final XLSX

Por solicitação da usuária, o formato final é XLSX. O comando `review.py export`
gera a planilha consolidada, e `search` gera uma planilha por execução.
`--no-xlsx` mantém uma opção explícita para executar sem o runtime de planilhas.

Implementados workbook_export.py e build_workbook.mjs, usando o Artifact Tool do
runtime compartilhado, sem dependências JavaScript locais. O snapshot preserva
resumos completos, decisões humanas, tipos numéricos/lógicos e rastreabilidade.
Somente extrações previamente validadas e com hashes intactos alimentam resultados.

Sete abas: Resumo, Artigos, Resumos, Sintese, Evidencias, Buscas e Proveniencia.
Arquivo: outputs/01a0bf7f-97f2-7032-a298-538c664b2f94/revisao_bibliografica.xlsx.

Verificação: 30 testes. Fórmulas recalculadas e comparadas à base. Teste de alteração
temporária de triagem com restauração. Inspeção visual das abas e leitura do XLSX
salvo para valores em cache, ausência de erros, filtros e congelamento de painéis.
Não houve teste no aplicativo Microsoft Excel.

Estado científico permanece: 9 candidatos, 9 triagens pendentes, 1 pacote preparado,
0 extrações semânticas validadas. Não houve nova busca nem inclusão científica neste
incremento. A geração semântica por LLM e a importação de decisões feitas no XLSX
ainda não estão conectadas.

## Incremento 0.4 — pré-triagem por regras (10/10/2026)

- `screening.py suggest` aplica os critérios de `docs/criterios_triagem.md` (expressões regulares
  no título/resumo, com pesos) e grava `exports/triagem_sugerida.csv`. **Sugestões, não decisões.**
- `screening.py apply CSV` grava só as linhas com `decisao_humana` preenchida, com justificativa
  obrigatória, pela mesma função `record_review` usada por `review.py review`.
- Corpus em 10/10: 3.016 candidatos (busca completa de 20/09 + atualização de 10/10, +8).
  Sugestões: 674 INCLUDE, 1.297 MAYBE, 1.045 EXCLUDE; núcleo prioritário (VO/SLAM + atmosférico): 51.
- Testes: 33 aprovados.
