import fs from 'node:fs/promises';
import path from 'node:path';
import { Workbook, SpreadsheetFile } from '@oai/artifact-tool';

const [input, output, previewFlag] = process.argv.slice(2);
const data = JSON.parse(await fs.readFile(input, 'utf8'));
const wb = Workbook.create();
const sheets = {};
const names = ['Resumo', 'Artigos', 'Resumos', 'Sintese', 'Evidencias', 'Buscas', 'Proveniencia'];
for (const name of names) sheets[name] = wb.worksheets.add(name);
const ink = '#243746', blue = '#234C6A', pale = '#EEF3F7';
function col(n) { let s=''; for(n++;n;n=Math.floor((n-1)/26))s=String.fromCharCode(65+(n-1)%26)+s; return s; }
function literal(value) {
  if (typeof value==='string') {
    if (value.length>32700) throw new Error('Texto excede o limite de célula Excel; divida o campo antes de exportar.');
    return /^[=+@-]/.test(value) ? "'"+value : value;
  }
  return value ?? null;
}
function table(name, title, headers, rows, widths, opts={}) {
  const sh=sheets[name], end=col(headers.length-1), last=Math.max(6,rows.length+5);
  sh.showGridLines=false;
  sh.getRange(`A1:${end}${last}`).format.font={name:'Arial',size:10,color:ink};
  sh.getRange(`A1:${end}${last}`).format.verticalAlignment='center';
  sh.getRange('A2').values=[[title]];
  sh.getRange('A2').format.font={name:'Arial',size:14,bold:true,color:ink};
  sh.getRange(`A3:${end}3`).format.borders={bottom:{style:'thin',color:'#B5C7D3'}};
  sh.getRange(`A5:${end}5`).values=[headers];
  sh.getRange(`A5:${end}5`).format={fill:blue,font:{name:'Arial',size:10,bold:true,color:'#FFFFFF'},wrapText:true,rowHeight:34,horizontalAlignment:'center',verticalAlignment:'center'};
  widths.forEach((w,i)=>{sh.getRange(`${col(i)}1:${col(i)}${last}`).format.columnWidth=w;});
  if(rows.length) {
    sh.getRange(`A6:${end}${last}`).values=rows.map(row=>row.map(literal));
    sh.getRange(`A6:${end}${last}`).format.rowHeight=opts.height||54;
    sh.getRange(`A6:${end}${last}`).format.wrapText=true;
    const t=sh.tables.add(`A5:${end}${last}`,true,`Tb${name}`);
    t.style='TableStyleMedium2'; t.showFilterButton=true;
    // Aplicar o cabeçalho depois do estilo nativo da tabela.
    sh.getRange(`A5:${end}5`).format.fill=blue;
    sh.getRange(`A5:${end}5`).format.font={name:'Arial',size:10,bold:true,color:'#FFFFFF'};
  } else {
    sh.getRange('A7').values=[['Nenhum registro validado disponível nesta etapa.']];
    sh.getRange('A7').format.font={name:'Arial',size:10,color:'#657580',italic:true};
  }
  sh.freezePanes.freezeRows(5); sh.freezePanes.freezeColumns(1);
  for(const i of opts.dates||[]) if(rows.length) {
    sh.getRange(`${col(i)}6:${col(i)}${last}`).values=rows.map(row=>[row[i]?new Date(row[i]):null]);
    sh.getRange(`${col(i)}6:${col(i)}${last}`).setNumberFormat('dd/mm/yyyy hh:mm');
  }
  return sh;
}
table('Artigos','Artigos e triagem',
  ['ID','Título','Ano','Autores','Publicação','DOI','arXiv','Tipo','Bases','Temas da busca','Decisão humana','Justificativa','Extração','Última tentativa','Revisão das evidências','URL da fonte','Descoberta (UTC)','Triagem (UTC)'],
  data.papers,[12,65,9,46,36,32,20,20,20,40,19,50,27,27,25,48,23,23],{height:78,dates:[16,17]});
table('Resumos','Resumos por artigo', ['ID','Trecho','Resumo original','URL da fonte'],data.abstracts,[12,10,110,48],{height:110});
table('Sintese','Síntese das extrações validadas', ['ID','Grupo','Campo no schema','Valor textual','Valor numérico','Valor lógico','Evidências do núcleo','URL da fonte'],data.synthesis,[12,23,58,95,20,18,27,48],{height:90});
table('Evidencias','Evidências das extrações validadas', ['ID','Evidência','Tipo','Afirmação','Citação ou paráfrase','Página PDF','Seção','Tabela','Figura','Tipo de suporte','URL da fonte','Produtor da extração'],data.evidence,[12,15,18,65,90,14,30,18,18,24,48,32],{height:110});
table('Buscas','Histórico das buscas', ['Execução','Base','Tema','Consulta','Ano inicial','Ano final','Início (UTC)','Estado','Coletados','Novos','Já presentes','Total informado pela base','Limite atingido','Erro','Consulta enviada (URL)'],data.searches,[35,18,36,58,14,14,23,18,14,12,16,22,18,65,95],{height:64,dates:[6]});
table('Proveniencia','Origem de cada registro', ['ID','Execução','Base','Tema','Consulta','Arquivo bruto'],data.provenance,[12,35,18,36,58,27],{height:54});
const summary=sheets.Resumo;
summary.tabColor=blue; summary.showGridLines=false;
summary.getRange('A1:F30').format.font={name:'Arial',size:10,color:ink};
summary.getRange('A1:A30').format.columnWidth=43;
summary.getRange('B1:B30').format.columnWidth=17;
summary.getRange('C1:C30').format.columnWidth=4;
summary.getRange('D1:D30').format.columnWidth=100;
summary.getRange('A2').values=[['Revisão bibliográfica VO / Visual SLAM']];
summary.getRange('A2').format.font={name:'Arial',size:14,bold:true,color:ink};
summary.getRange('A3:D3').format.borders={bottom:{style:'thin',color:'#B5C7D3'}};
summary.getRange('A4').values=[['Atualização (UTC)']];
summary.getRange('B4').values=[[new Date(data.created_at)]];
summary.getRange('B4').setNumberFormat('dd/mm/yyyy hh:mm');
summary.getRange('A6:B6').values=[['Indicador','Quantidade']];
summary.getRange('A6:B6').format={fill:blue,font:{name:'Arial',size:10,bold:true,color:'#FFFFFF'},rowHeight:28};
const last=Math.max(6,data.papers.length+5);
const evLast=Math.max(6,data.evidence.length+5);
const metrics=[
 ['Candidatos no corpus',`=COUNTA('Artigos'!A6:A${last})`],
 ['Triagem pendente',`=COUNTIFS('Artigos'!K6:K${last},"PENDENTE")`],
 ['Incluídos pelo revisor',`=COUNTIFS('Artigos'!K6:K${last},"INCLUDE")`],
 ['Dúvidas na triagem',`=COUNTIFS('Artigos'!K6:K${last},"MAYBE")`],
 ['Excluídos pelo revisor',`=COUNTIFS('Artigos'!K6:K${last},"EXCLUDE")`],
 ['Extrações pendentes',`=COUNTIFS('Artigos'!M6:M${last},"EXTRACTION_PENDING")`],
 ['Extrações validadas',`=COUNTIFS('Artigos'!M6:M${last},"EXTRACTED")`],
 ['Evidências registradas',`=COUNTA('Evidencias'!A6:A${evLast})`],
];
summary.getRange('A7:A14').values=metrics.map(x=>[x[0]]);
summary.getRange('B7:B14').formulas=metrics.map(x=>[x[1]]);
summary.getRange('A7:B14').format.rowHeight=28;
summary.getRange('B7:B14').setNumberFormat('0');
summary.getRange('B7:B14').format.font={name:'Arial',size:10,bold:true,color:ink};
summary.getRange('D6').values=[['Como interpretar']];
summary.getRange('D6').format.font={name:'Arial',size:10,bold:true,color:ink};
const notes=[
 'O corpus contém candidatos. A inclusão depende da decisão humana registrada.',
 'Temas indicam a consulta de origem, não uma classificação científica confirmada.',
 'EXTRACTED indica validação de estrutura e vínculos. A revisão científica segue pendente.',
 'Sem extração validada, as abas Síntese e Evidências permanecem sem registros.',
 'Campos vazios significam informação ausente. Zero nos indicadores é uma contagem real.',
 'O XLSX é um retrato da base. Alterações no Excel não são importadas automaticamente.',
 'Buscas repetidas contam novamente registros já presentes. Esses totais não são PRISMA.',
 'Resumos longos são divididos em trechos numerados, preservando o texto original.',
];
summary.getRange('D7:D14').values=notes.map(n=>[n]);
summary.getRange('D7:D14').format.wrapText=true;
summary.getRange('A7:D14').format.rowHeight=35;
summary.getRange('D16').values=[['As fontes estão nas linhas de dados. Use os filtros das tabelas para localizar artigos.']];
summary.getRange('D16').format.wrapText=true;
summary.getRange('D16').format.rowHeight=32;
const themes=[['fundamentals_taxonomy','Fundamentos e taxonomia'],['classical_geometric','Métodos clássicos e geométricos'],
 ['deep_vo_slam','Deep learning para VO / SLAM'],['robustness_corruptions','Robustez e corrupções'],
 ['atmospheric_optical','Degradações atmosféricas e ópticas'],['datasets_benchmarks','Datasets e benchmarks'],
 ['metrics_protocol','Métricas e protocolos'],['forest_uav_amazon','Florestas, UAVs e Amazônia']];
summary.getRange('A18').values=[['Cobertura das consultas por tema']];
summary.getRange('A18').format.font={name:'Arial',size:10,bold:true,color:ink};
summary.getRange('A20:B20').values=[['Tema de origem','Candidatos']];
summary.getRange('A20:B20').format={fill:blue,font:{name:'Arial',size:10,bold:true,color:'#FFFFFF'},rowHeight:28};
summary.getRange('A21:A28').values=themes.map(t=>[t[1]]);
summary.getRange('B21:B28').formulas=themes.map(t=>[`=COUNTIFS('Artigos'!J6:J${last},"*${t[0]}*")`]);
summary.getRange('A21:B28').format.rowHeight=27;
summary.getRange('B21:B28').setNumberFormat('0');
summary.getRange('D20').values=[['Cobertura não equivale a inclusão científica. Um artigo pode aparecer em vários temas.']];
summary.getRange('D20').format.wrapText=true;
summary.getRange('D21').values=[['Consulte a aba Buscas para identificar consultas limitadas, esgotadas ou com falha.']];
summary.getRange('D21').format.wrapText=true;
if(data.papers.length){
 sheets.Artigos.getRange(`K6:K${last}`).conditionalFormats.add('containsText',{text:'PENDENTE',format:{fill:'#FFF0CF',font:{color:'#805300'}}});
 sheets.Artigos.getRange(`M6:M${last}`).conditionalFormats.add('containsText',{text:'INVALID',format:{fill:'#FCE4E2',font:{color:'#A52424'}}});
}
// Testar a reação das contagens a uma alteração e restaurar o snapshot.
if(data.papers.length){
 const original=data.papers[0][10];
 const included=data.papers.filter(r=>r[10]==='INCLUDE').length;
 sheets.Artigos.getRange('K6').values=[['INCLUDE']];
 const recalculated=summary.getRange('B9').values[0][0];
 if(recalculated!==included+(original==='INCLUDE'?0:1))throw new Error('Resumo não reagiu à alteração de triagem');
 sheets.Artigos.getRange('K6').values=[[original]];
}
wb.recalculate();
const expected=[data.papers.length,data.papers.filter(r=>r[10]==='PENDENTE').length,
 data.papers.filter(r=>r[10]==='INCLUDE').length,data.papers.filter(r=>r[10]==='MAYBE').length,
 data.papers.filter(r=>r[10]==='EXCLUDE').length,data.papers.filter(r=>r[12]==='EXTRACTION_PENDING').length,
 data.papers.filter(r=>r[12]==='EXTRACTED').length,data.evidence.length];
const actual=summary.getRange('B7:B14').values.map(r=>r[0]);
if(JSON.stringify(actual)!==JSON.stringify(expected)) throw new Error(`Contagens divergentes: ${JSON.stringify({actual,expected})}`);
const coverage=summary.getRange('B21:B28').values.map(r=>r[0]);
const expectedCoverage=themes.map(t=>data.papers.filter(r=>r[9].split(', ').includes(t[0])).length);
if(JSON.stringify(coverage)!==JSON.stringify(expectedCoverage))throw new Error('Cobertura por tema divergente do corpus');
const inspected=await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!',options:{useRegex:true,maxResults:20},summary:'Verificação das fórmulas'});
console.log(inspected.ndjson);
await fs.mkdir(path.dirname(output),{recursive:true});
if(previewFlag==='--previews'){
 const previewDir=path.join(path.dirname(output),'previews'); await fs.mkdir(previewDir,{recursive:true});
 for(const name of names){
   const ranges=name==='Resumo'?['A1:D29']:name==='Artigos'?['A1:D9','K5:P9']:name==='Buscas'?['A1:D8','G5:N8']:['A1:D9'];
   for(let i=0;i<ranges.length;i++){
     const image=await wb.render({sheetName:name,range:ranges[i],scale:1,format:'png'});
     await fs.writeFile(path.join(previewDir,`${name}_${i}.png`),new Uint8Array(await image.arrayBuffer()));
   }
 }
}
const file=await SpreadsheetFile.exportXlsx(wb);
await file.save(output);
await fs.writeFile(output.replace(/\.xlsx$/i,'.verification.json'),JSON.stringify({created_at:data.created_at,sheets:names,counts:actual,coverage,formulaScan:inspected.ndjson},null,2));
console.log(`XLSX: ${output}`);
