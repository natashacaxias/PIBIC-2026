# Automação da revisão bibliográfica — VO/Visual SLAM

Versão 0.3: coleta, preparação/validação de extrações e saída final XLSX, baseada em `arquitetura_revisao_bibliografica_vo_slam.md`.
Python 3.9 ou superior. Coleta e revisão usam a biblioteca padrão; PDF e validação
usam `requirements.txt`. A saída XLSX usa o runtime Node e Artifact Tool do Codex,
sem instalar dependências JavaScript no projeto.

## O que funciona

- Consultas dos oito temas originais, com anos mínimos próprios e limite de resultados.
- Coletores Crossref e arXiv com paginação, espera entre chamadas e tentativas em falhas temporárias.
- Respostas brutas imutáveis por execução, consulta, filtros, horário, URL e hash de integridade.
- Corpus persistente SQLite, IDs internos P0001 etc. e proveniência por busca.
- Deduplicação por identificador; título normalizado exige mesmo primeiro autor e ano e ausência de conflito de identificadores.
- Preprint e publicação permanecem separados; não há fusão automática de versões.
- Fila de revisão em Markdown, corpus JSON e referências RIS para importar no Zotero.
- Decisão humana com justificativa, preservada nas buscas seguintes.
- Falhas parciais ficam registradas, mantêm os resultados já coletados e retornam código de saída 1.

## Executar

No terminal, entre nesta pasta:

```bash
cd '/Users/natashacaxias/PIBIC/PIBIC 2026/literature_review'
python3 review.py search --dry-run --pilot --limit 3
python3 review.py search --pilot --limit 3
```

O piloto executa somente as duas primeiras combinações consulta/base. Com a configuração
padrão, busca `"visual odometry" survey` no Crossref e no arXiv. É um teste operacional;
não constitui o piloto científico de 16 artigos proposto na arquitetura.

Buscar um tema:

```bash
python3 review.py search --theme atmospheric_optical --limit 20
```

Buscar todos os temas (pode levar vários minutos e gerar muitos candidatos):

```bash
python3 review.py search
```

Opcionalmente, identifique o contato para o Crossref com a variável de ambiente
`CROSSREF_MAILTO`. Não é necessário para começar; `.env` não é carregado automaticamente.
Execute apenas um processo de coleta por vez, para respeitar os intervalos das fontes.

## Resultados

- `data/corpus.sqlite3`: base persistente. Faça backup dela juntamente com `data/runs`.
- `data/runs/<execução>/raw/`: respostas originais e auditoria de cada consulta.
- `data/runs/<execução>/summary.json`: contagens, falhas e consultas limitadas.
- `data/runs/<execução>/config.json`: configuração usada na execução.
- `data/runs/<execução>/exports/revisao.md`: fila de leitura humana.
- `data/runs/<execução>/exports/papers.json`: corpus acumulado, com fontes e decisões.
- `data/runs/<execução>/exports/bibliography.ris`: referências para Zotero.

Os campos `new` e `duplicates` descrevem a ingestão da execução, incluindo reconsultas
de trabalhos já presentes. Não devem ser apresentados como contagens PRISMA finais.
`limit_reached` informa que o teto impediu a coleta de todos os resultados reportados.
Os arquivos exportados por execução são retratos do corpus acumulado naquele momento.

Registrar uma decisão efetivamente tomada pelo revisor:

```bash
python3 review.py review P0001 INCLUDE --reason 'Justificativa da leitura do título e resumo'
python3 review.py export
```

A exportação atualizada fica em `exports/`. O comando de revisão atualiza a decisão
atual do artigo; esta versão não mantém histórico de alterações de decisão.
Nenhum artigo é excluído da base. Todos começam em `SCREEN_PENDING`.

## Configuração e interpretação

`config/search_queries.json` contém todas as consultas transcritas da arquitetura.
JSON foi escolhido para dispensar instalação de um parser YAML. O ano final permanece
explicitamente em 2026; altere-o quando atualizar o protocolo de pesquisa.

No Crossref, a consulta usa busca textual no título (`query.title`), ordenada por
relevância (`score`), sem garantia de semântica booleana ou
frase exata. No arXiv, os termos/frases são ligados por AND no campo `all`, com filtro
pela data de submissão. As duas estratégias não são equivalentes; a consulta enviada
fica na auditoria. A sintaxe de entrada aceita termos e frases entre aspas, não uma
expressão booleana arbitrária. Temas de origem não são classificação científica.
Crossref é usado nesta entrega como coletor inicial e normalizador, não como cobertura
completa. Resultados irrelevantes devem ser avaliados pelo revisor.

A deduplicação de título é conservadora. Variações de nome, ano ou título podem manter
duplicatas; comparar preprint/publicação e candidatos fuzzy será uma etapa posterior.
Resumos e outros campos ausentes ficam nulos; resultados científicos não são inferidos.

## Próximas etapas da arquitetura

Ainda não implementados: OpenAlex, Semantic Scholar e bases institucionais; importação
RIS/BibTeX; classificação assistida; relações entre versões; snowballing; aquisição de
PDFs fora do arXiv; OCR; chamada automática a LLM; tabelas específicas de métodos,
corrupções, datasets e métricas; relatório PRISMA e agendamento. O schema e o prompt originais foram copiados para `config/`
e agora são usados pelo módulo de extração. O corpus de metadados **não** pretende validar contra o schema de
extração do artigo, pois são modelos de etapas diferentes.

A atualização atual repete as consultas e adiciona registros inéditos ao corpus. Não
há ainda filtro incremental por data de atualização da base. Não há tarefas agendadas.

## Verificação

```bash
.venv/bin/python -m unittest discover -s tests -v
```

Testes cobrem IDs estáveis, decisões preservadas, enriquecimento, conflito de DOI,
separação de versões, paginação, tradução de consultas e preservação de resposta inválida.
Não dependem da rede. O piloto real verifica separadamente a conectividade.

Documentação oficial consultada em 20/09/2026:

- Crossref: https://www.crossref.org/documentation/retrieve-metadata/rest-api/
- Crossref, parâmetros e paginação: https://github.com/CrossRef/rest-api-doc
- arXiv: https://info.arxiv.org/help/api/user-manual.html


## Preparação e validação de extrações — versão 0.2

Instale as dependências em ambiente isolado (o ambiente deste projeto já está instalado):

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-lock.txt
```

O arquivo lock registra as versões verificadas nesta entrega. `requirements.txt`
contém os intervalos compatíveis para manutenção futura.

Baixar um PDF público vinculado a um registro arXiv:

```bash
.venv/bin/python extraction.py fetch-arxiv P0004
```

O comando informa o caminho do PDF. Ele usa o identificador do corpus, preserva a
versão arXiv quando consta no registro e grava URL, data e hash do download. Não usa
sessões institucionais. Respostas HTML e arquivos acima de 50 MiB são recusados.

Preparar um PDF local autorizado, substituindo o caminho abaixo pelo arquivo:

```bash
.venv/bin/python extraction.py prepare P0004 /caminho/para/paper.pdf
```

Cada preparação cria um pacote separado em `data/papers/P0004/bundles/<id>/`, com:

- PDF original e texto de cada página física em `pages.json` e `article.txt`;
- cópias do schema e prompt originais e metadados do corpus;
- `extraction_prompt.txt`, com texto completo, identidade e instruções de evidência;
- `manifest.json`, com hashes, número de páginas e avisos de extração de texto.

PDFs sem texto são interrompidos e sinalizados para OCR. Páginas com pouco texto
são assinaladas para inspeção visual. Texto extraível não garante preservação de
colunas, tabelas, fórmulas ou imagens. Confira o PDF para resultados quantitativos.

A geração semântica do JSON **ainda não está conectada a uma API de LLM**. O pacote
fica pronto para análise assistida com o schema. O prompt pede dois arquivos:

1. `extraction.json`: objeto que segue exatamente o schema fornecido.
2. `claim_links.json`: vínculos de afirmações centrais para evidências, por exemplo:

```json
{"/paper/main_contribution": ["E001"], "/paper/main_results/0": ["E002"]}
```

O segundo arquivo resolve a ausência de `evidence_refs` no núcleo do schema, sem
alterar o original. Não preencha extrações com dados supostos para passar na validação.

Validar sem alterar o corpus, substituindo os caminhos:

```bash
.venv/bin/python extraction.py validate /caminho/do/pacote /caminho/extraction.json --links /caminho/claim_links.json
```

Validar e arquivar uma tentativa com identificação do modelo/versão ou responsável:

```bash
.venv/bin/python extraction.py accept /caminho/do/pacote /caminho/extraction.json --links /caminho/claim_links.json --producer 'responsável ou modelo/versão'
python3 review.py export
```

O validador verifica JSON Schema Draft 2020-12, identidade do artigo, evidências
repetidas/inexistentes, vínculos do núcleo e módulos, páginas físicas e integridade
dos arquivos preparados. Este perfil exige páginas inteiras entre 1 e o total do
PDF, embora o schema geral permita strings/ausência de página. Limitações do revisor
exigem vínculo a uma evidência marcada `reviewer_inference`.

Toda tentativa é preservada em `attempts/<id>/`, com JSON recebido, vínculos,
produtor, hashes e relatório. Tentativas inválidas ficam `EXTRACTION_INVALID`.
Tentativas válidas ficam `EXTRACTED` e geram tabelas JSON de artigos, evidências,
vínculos e módulos. A última tentativa válida do pacote é preservada quando outra
falha. Um novo pacote inicia novo ciclo, sem herdar extração de outro PDF/schema.

**EXTRACTED significa que estrutura e vínculos passaram na validação. Não confirma
veracidade científica nem revisão humana.** Nenhum comando deste módulo altera a
decisão de inclusão/exclusão. A exportação do corpus mostra o estado de extração
separadamente. A análise semântica de citações/paráfrases permanece pendente.

Documentação das dependências:

- https://pypdf.readthedocs.io/en/stable/user/extract-text.html
- https://python-jsonschema.readthedocs.io/en/stable/validate/

## Saída final XLSX — versão 0.3

O formato final da automação é XLSX. Para atualizar a planilha a partir do corpus:

```bash
.venv/bin/python review.py export
```

Arquivo padrão:
`outputs/01a0bf7f-97f2-7032-a298-538c664b2f94/revisao_bibliografica.xlsx`.

As execuções de `search` também geram `revisao_bibliografica.xlsx` dentro da pasta
da execução. Os arquivos JSON, RIS e Markdown continuam como apoio. O XLSX padrão
da pasta `outputs` é atualizado com `export`; a planilha de cada busca é histórica.

Opções:

```bash
.venv/bin/python review.py export --xlsx-output /caminho/resultado.xlsx
.venv/bin/python review.py export --previews
.venv/bin/python review.py search --pilot --limit 3 --no-xlsx
```

`--no-xlsx` também está disponível em `export`, para operar apenas com os formatos
de apoio em ambientes sem o runtime de planilhas. A geração não usa instalação
global de pacotes. Fora deste computador, configure `LITERATURE_NODE` e
`LITERATURE_NODE_MODULES` para o executável e diretório de pacotes do runtime.

Abas do arquivo:

- **Resumo:** contagens calculadas por fórmulas e interpretação dos estados.
- **Artigos:** metadados, origem temática, decisão humana e estado de extração.
- **Resumos:** texto original completo, dividido em trechos numerados sem truncar.
- **Sintese:** campos das extrações validadas, com texto, números e booleanos separados.
- **Evidencias:** afirmações, suporte, página física e fonte do artigo.
- **Buscas:** consultas, filtros, datas, totais, limites e falhas, inclusive históricas.
- **Proveniencia:** vínculo entre cada artigo e as consultas que o recuperaram.

As tabelas têm filtros e painéis fixos. As contagens são recalculadas antes da
exportação e conferidas contra o snapshot da base. Extrações alteradas após a
validação bloqueiam a exportação. Somente a última tentativa válida do pacote
atual alimenta as abas científicas. Enquanto não houver extrações válidas, essas
abas não recebem exemplos ou resultados inventados.

O XLSX é uma saída da automação. Edições feitas nele não são importadas de volta
para SQLite nesta versão. Use `review.py review` para registrar a decisão humana
e execute `export` novamente. Resumos, metadados e evidências mantêm links de origem.

A verificação desta entrega incluiu 30 testes, inspeção visual das sete abas,
reação das fórmulas a uma alteração temporária de triagem e leitura do XLSX salvo
para conferir valores calculados, filtros e painéis. O arquivo foi validado pelo
Artifact Tool e pela leitura OpenXML; não foi aberto no aplicativo Microsoft Excel.
