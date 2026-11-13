// Gerador do arquivo .docx da dissertação.
//
// Formatação conforme as normas do TCC do MBA USP/Esalq: Arial 11, espaçamento 1,5
// no corpo, recuo de primeira linha de 1,25 cm, justificado; resumo, abstract,
// legendas, tabelas e referências em espaçamento simples e sem recuo. Papel A4 com
// margens de 2,5 cm. O conteúdo textual vive em conteudo.js.
//
// Uso:  node gerarDocx.js
// O módulo "docx" está instalado fora do repositório; o caminho é resolvido abaixo.

const fs = require('fs');
const path = require('path');

const CAMINHOS_DOCX = [
  'docx',
  'C:/Users/yuri-/AppData/Local/Temp/docxbuild/node_modules/docx'
];

let D = null;
for (const c of CAMINHOS_DOCX) {
  try { D = require(c); break; } catch (e) { /* tenta o próximo */ }
}
if (!D) throw new Error('Módulo docx não encontrado. Instale com: npm install docx');

const {
  Document, Packer, Paragraph, TextRun, ImageRun, AlignmentType, BorderStyle,
  Table, TableRow, TableCell, WidthType, ShadingType, Header, Footer,
  PageNumber, PageBreak, VerticalAlign
} = D;

const C = require('./conteudo');

// --- constantes de formatação -------------------------------------------------
const FONTE = 'Arial';
const T_CORPO = 22;      // 11 pt
const T_TITULO = 24;     // 12 pt
const T_LEGENDA = 22;    // 11 pt, exigido pelas Tabelas 7 e 9 do Manual
const T_TABELA = 22;     // 11 pt, exigido pela Tabela 9 do Manual
const T_ENDERECO = 18;   // 9 pt
const T_CABECALHO = 16;  // 8 pt

const L_UMA_E_MEIA = 360;
const L_SIMPLES = 240;
const RECUO = 708;       // 1,25 cm em DXA
const LARGURA_UTIL = 9070;   // 11906 - 2 x 1418
const LARGURA_IMG = 560;     // px

// --- utilitários --------------------------------------------------------------

// Converte a marcação *negrito* em runs. O resto do texto segue sem formatação,
// já que as normas reservam o itálico a nomes científicos.
function runs(texto, opcoes = {}) {
  const base = { font: FONTE, size: opcoes.size || T_CORPO, bold: !!opcoes.bold };
  // literal: o asterisco é conteúdo (marca do autor correspondente), não marcação.
  if (opcoes.literal) return [new TextRun(Object.assign({}, base, { text: String(texto) }))];
  const saida = [];
  const partes = String(texto).split('*');
  partes.forEach((parte, i) => {
    if (parte === '') return;
    saida.push(new TextRun(Object.assign({}, base, { text: parte, bold: base.bold || i % 2 === 1 })));
  });
  return saida.length ? saida : [new TextRun(Object.assign({}, base, { text: '' }))];
}

function corpo(texto) {
  return new Paragraph({
    children: runs(texto),
    alignment: AlignmentType.JUSTIFIED,
    spacing: { line: L_UMA_E_MEIA, after: 0 },
    indent: { firstLine: RECUO }
  });
}

function semRecuo(texto, opcoes = {}) {
  return new Paragraph({
    children: runs(texto, opcoes),
    alignment: opcoes.alignment || AlignmentType.JUSTIFIED,
    spacing: { line: opcoes.line || L_SIMPLES, after: opcoes.after || 0 }
  });
}

function vazio(line = L_UMA_E_MEIA) {
  return new Paragraph({ children: [new TextRun({ font: FONTE, size: T_CORPO, text: '' })], spacing: { line } });
}

function secao(texto) {
  return new Paragraph({
    children: runs(texto, { bold: true }),
    alignment: AlignmentType.LEFT,
    spacing: { line: L_UMA_E_MEIA, before: 240, after: 120 },
    keepNext: true
  });
}

function subsecao(texto) {
  return new Paragraph({
    children: runs(texto, { bold: true }),
    alignment: AlignmentType.LEFT,
    spacing: { line: L_UMA_E_MEIA, before: 200, after: 80 },
    keepNext: true
  });
}

// Itens de lista. O recuo vem da própria definição do marcador; defini-lo também
// aqui desalinha os itens em alguns leitores.
function item(texto) {
  return new Paragraph({
    children: runs(texto),
    alignment: AlignmentType.JUSTIFIED,
    spacing: { line: L_UMA_E_MEIA, after: 0 },
    bullet: { level: 0 }
  });
}

function paragrafos(lista) {
  return lista.map(corpo);
}

// --- figuras ------------------------------------------------------------------
function figura(f) {
  const arquivo = path.resolve(__dirname, f.arquivo);
  if (!fs.existsSync(arquivo)) throw new Error('Figura ausente: ' + arquivo);
  const altura = Math.round(LARGURA_IMG * f.razao);
  return [
    new Paragraph({
      children: [new ImageRun({
        type: 'png',
        data: fs.readFileSync(arquivo),
        transformation: { width: LARGURA_IMG, height: altura }
      })],
      alignment: AlignmentType.CENTER,
      spacing: { before: 200, after: 80, line: L_SIMPLES },
      keepNext: true
    }),
    // A Tabela 7 do Manual exige a legenda abaixo da figura e justificada as margens,
    // nao centralizada.
    new Paragraph({
      children: runs(f.legenda, { size: T_LEGENDA }),
      alignment: AlignmentType.JUSTIFIED,
      spacing: { line: L_SIMPLES, after: 0 },
      keepNext: true
    }),
    new Paragraph({
      children: runs(f.fonte, { size: T_LEGENDA }),
      alignment: AlignmentType.JUSTIFIED,
      spacing: { line: L_SIMPLES, after: 200 }
    })
  ];
}

// --- tabelas ------------------------------------------------------------------
const SEM_BORDA = { style: BorderStyle.NONE, size: 0, color: 'FFFFFF' };
const LINHA = { style: BorderStyle.SINGLE, size: 6, color: '000000' };

function celula(texto, largura, opcoes = {}) {
  return new TableCell({
    width: { size: largura, type: WidthType.DXA },
    borders: {
      top: SEM_BORDA, left: SEM_BORDA, right: SEM_BORDA,
      bottom: opcoes.bottom || SEM_BORDA
    },
    shading: { type: ShadingType.CLEAR, fill: 'FFFFFF', color: 'auto' },
    verticalAlign: VerticalAlign.CENTER,
    margins: { top: 40, bottom: 40, left: 60, right: 60 },
    children: [new Paragraph({
      children: runs(texto, { size: T_TABELA, bold: !!opcoes.bold }),
      alignment: opcoes.alignment || AlignmentType.CENTER,
      spacing: { line: L_SIMPLES, after: 0 }
    })]
  });
}

function tabela(t) {
  const largura = t.larguras.reduce((a, b) => a + b, 0);

  // Sem negrito: a Tabela 9 do Manual proibe realce em negrito dentro das tabelas,
  // inclusive no cabecalho, que ja se distingue pela linha inferior.
  const cabecalho = new TableRow({
    tableHeader: true,
    children: t.cabecalho.map((txt, i) => celula(txt, t.larguras[i], { bottom: LINHA }))
  });

  // Tabela 9 do Manual: primeira coluna a esquerda, cabecalho centralizado, demais
  // celulas justificadas, exceto numeros, que vao alinhados a direita.
  const ehNumero = (txt) => /^[+-]?[\d.,]+$/.test(String(txt).trim());

  const linhas = t.linhas.map((linha, iLinha) => new TableRow({
    children: linha.map((txt, i) => celula(txt, t.larguras[i], {
      alignment: i === 0 ? AlignmentType.LEFT
        : ehNumero(txt) ? AlignmentType.RIGHT : AlignmentType.JUSTIFIED,
      bottom: iLinha === t.linhas.length - 1 ? LINHA : SEM_BORDA
    }))
  }));

  const saida = [
    new Paragraph({
      children: runs(t.titulo, { size: T_LEGENDA }),
      alignment: AlignmentType.LEFT,
      spacing: { before: 200, line: L_SIMPLES, after: 60 },
      keepNext: true
    }),
    new Table({
      columnWidths: t.larguras,
      width: { size: largura, type: WidthType.DXA },
      borders: {
        top: LINHA, bottom: SEM_BORDA, left: SEM_BORDA, right: SEM_BORDA,
        insideHorizontal: SEM_BORDA, insideVertical: SEM_BORDA
      },
      rows: [cabecalho].concat(linhas)
    }),
    new Paragraph({
      children: runs(t.fonte, { size: T_LEGENDA }),
      alignment: AlignmentType.LEFT,
      spacing: { line: L_SIMPLES, before: 60, after: 0 }
    })
  ];

  if (t.nota) {
    saida.push(new Paragraph({
      children: runs('Nota: ' + t.nota, { size: T_LEGENDA }),
      alignment: AlignmentType.JUSTIFIED,
      spacing: { line: L_SIMPLES, after: 200 }
    }));
  } else {
    saida.push(vazio(L_SIMPLES));
  }
  return saida;
}

// --- montagem do documento ----------------------------------------------------
const F = C.FIGURAS;

const capa = [
  vazio(), vazio(),
  new Paragraph({
    children: runs(C.TITULO, { bold: true, size: T_TITULO }),
    alignment: AlignmentType.CENTER,
    spacing: { line: L_UMA_E_MEIA, after: 240 }
  }),
  vazio(),
  new Paragraph({
    children: runs(C.AUTORES, { literal: true }),
    alignment: AlignmentType.CENTER,
    spacing: { line: L_UMA_E_MEIA, after: 240 }
  }),
  vazio()
].concat(C.ENDERECOS.map(e => new Paragraph({
  children: runs(e, { size: T_ENDERECO, literal: true }),
  alignment: AlignmentType.LEFT,
  spacing: { line: L_SIMPLES, after: 0 }
}))).concat([
  new Paragraph({ children: [new PageBreak()] })
]);

const abertura = [
  new Paragraph({
    children: runs(C.TITULO, { bold: true }),
    alignment: AlignmentType.CENTER,
    spacing: { line: L_SIMPLES, after: 240 }
  }),
  secao('Resumo'),
  semRecuo(C.RESUMO, { after: 120 }),
  semRecuo('*Palavras-chave:* ' + C.PALAVRAS_CHAVE, { after: 240 }),
  new Paragraph({
    children: runs(C.TITULO_EN, { bold: true }),
    alignment: AlignmentType.CENTER,
    spacing: { line: L_SIMPLES, after: 240 }
  }),
  secao('Abstract'),
  semRecuo(C.ABSTRACT, { after: 120 }),
  semRecuo('*Keywords:* ' + C.KEYWORDS, { after: 240 })
];

const introducao = [secao('1. Introdução')].concat(paragrafos(C.INTRODUCAO));

const metodologia = [secao('2. Material e métodos')]
  .concat(paragrafos(C.MET_ABERTURA))
  .concat(figura(F.arquitetura))
  .concat([subsecao('2.1. Coleta e engenharia de dados')])
  .concat(paragrafos(C.MET_COLETA))
  .concat(C.MET_ATIVOS.map(item))
  .concat(paragrafos(C.MET_COLETA_FIM))
  .concat([subsecao('2.2. Indicadores fundamentalistas e corte pela data de divulgação')])
  .concat(paragrafos(C.MET_FUNDAMENTOS))
  .concat([subsecao('2.3. Extração de atributos e agrupamento (K-Means)')])
  .concat(paragrafos(C.MET_KMEANS.slice(0, 1)))
  .concat(figura(F.kmeans))
  .concat(paragrafos(C.MET_KMEANS.slice(1)))
  .concat([subsecao('2.4. Prevenção de viés temporal: o mecanismo de anonimização')])
  .concat(paragrafos(C.MET_CAMARA))
  .concat([subsecao('2.5. Orquestração multiagente e estágio heurístico')])
  .concat(paragrafos(C.MET_AGENTES))
  .concat([subsecao('2.6. Otimização matemática determinística')])
  .concat(paragrafos(C.MET_OTIMIZACAO))
  .concat([subsecao('2.7. Modelagem para validação estatística e testes de estresse')])
  .concat(paragrafos(C.MET_VALIDACAO));

const resultados = [secao('3. Resultados e discussão')]
  .concat(paragrafos(C.RES_ABERTURA))
  .concat([subsecao('3.1. Desempenho das carteiras e o controle pelo universo de ativos')])
  .concat(paragrafos(C.RES_DESEMPENHO.slice(0, 1)))
  .concat(tabela(C.TABELA_1))
  .concat(paragrafos(C.RES_DESEMPENHO.slice(1, 3)))
  .concat(figura(F.capital))
  .concat(paragrafos(C.RES_DESEMPENHO.slice(3)))
  .concat([subsecao('3.2. Otimização matemática e métricas de risco')])
  .concat(paragrafos(C.RES_RISCO.slice(0, 1)))
  .concat(figura(F.varBeta))
  .concat(paragrafos(C.RES_RISCO.slice(1, 2)))
  .concat(figura(F.drawdown))
  .concat(paragrafos(C.RES_RISCO.slice(2)))
  .concat([subsecao('3.3. Inferência estatística: alfa, coeficiente Beta e poder do teste')])
  .concat(paragrafos(C.RES_INFERENCIA.slice(0, 1)))
  .concat(tabela(C.TABELA_2))
  .concat(paragrafos(C.RES_INFERENCIA.slice(1, 3)))
  .concat(figura(F.controle))
  .concat(paragrafos(C.RES_INFERENCIA.slice(3, 5)))
  .concat(tabela(C.TABELA_3))
  .concat(paragrafos(C.RES_INFERENCIA.slice(5)))
  .concat([subsecao('3.4. Magnitude do viés de sobrevivência no universo de ativos')])
  .concat(paragrafos(C.RES_VIES.slice(0, 1)))
  .concat(figura(F.vies))
  .concat(paragrafos(C.RES_VIES.slice(1)))
  .concat([subsecao('3.5. Verificação do determinismo da camada matemática')])
  .concat(paragrafos(C.RES_DETERMINISMO.slice(0, 1)))
  .concat(tabela(C.TABELA_4))
  .concat(paragrafos(C.RES_DETERMINISMO.slice(1)))
  .concat([subsecao('3.6. Estabilidade do resultado entre execuções')])
  .concat(paragrafos(C.RES_REPLICA.slice(0, 1)))
  .concat(tabela(C.TABELA_5))
  .concat(paragrafos(C.RES_REPLICA.slice(1)))
  .concat([subsecao('3.7. Custos de transação')])
  .concat(paragrafos(C.RES_CUSTOS))
  .concat([subsecao('3.8. Teste de estresse: simulação de Monte Carlo')])
  .concat(paragrafos(C.RES_MONTE_CARLO))
  .concat(figura(F.monteCarlo))
  .concat([subsecao('3.9. Limitações do estudo')])
  .concat(paragrafos(C.RES_LIMITACOES))
  .concat(C.LIMITACOES.map(item));

const fechamento = [secao('4. Considerações finais')]
  .concat(paragrafos(C.CONSIDERACOES))
  .concat([secao('Agradecimentos'), corpo(C.AGRADECIMENTOS), secao('Referências')])
  .concat(C.REFERENCIAS.map(r => new Paragraph({
    children: runs(r),
    alignment: AlignmentType.LEFT,
    spacing: { line: L_SIMPLES, after: 120 }
  })));

const doc = new Document({
  creator: 'Yuri dos Reis de Oliveira',
  title: C.TITULO,
  styles: {
    default: {
      document: { run: { font: FONTE, size: T_CORPO } }
    }
  },
  sections: [{
    properties: {
      titlePage: true,
      page: {
        size: { width: 11906, height: 16838 },
        margin: { top: 1418, right: 1418, bottom: 1418, left: 1418, header: 709, footer: 709 }
      }
    },
    headers: {
      first: new Header({ children: [new Paragraph('')] }),
      default: new Header({
        children: [new Paragraph({
          children: runs(C.CABECALHO, { size: T_CABECALHO }),
          alignment: AlignmentType.CENTER,
          spacing: { line: L_SIMPLES }
        })]
      })
    },
    footers: {
      first: new Footer({ children: [new Paragraph('')] }),
      default: new Footer({
        children: [new Paragraph({
          children: [new TextRun({ font: FONTE, size: T_ENDERECO, children: [PageNumber.CURRENT] })],
          alignment: AlignmentType.RIGHT,
          spacing: { line: L_SIMPLES }
        })]
      })
    },
    children: capa
      .concat(abertura)
      .concat(introducao)
      .concat(metodologia)
      .concat(resultados)
      .concat(fechamento)
  }]
});

const saida = path.resolve(__dirname, 'Alocacao de ativos e gestao de risco na B3 - Yuri dos Reis de Oliveira.docx');
Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync(saida, buffer);
  console.log('gerado: ' + saida);
  console.log('tamanho: ' + (buffer.length / 1024).toFixed(0) + ' KB');
});
