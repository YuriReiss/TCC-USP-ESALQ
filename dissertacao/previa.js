// Servidor local so para conferir o .docx renderizado no navegador.
// Nao ha pandoc, LibreOffice nem Word nesta maquina; docx-preview faz o render.
const http = require('http');
const fs = require('fs');
const path = require('path');

const DOCX = path.join(__dirname,
  'Alocacao de ativos e gestao de risco na B3 - Yuri dos Reis de Oliveira.docx');

const PAGINA = `<!doctype html><meta charset="utf-8">
<title>Prévia</title>
<style>body{margin:0;background:#8f8f8f}#alvo{padding:16px 0}</style>
<div id="alvo">carregando…</div>
<script src="https://cdn.jsdelivr.net/npm/jszip@3.10.1/dist/jszip.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/docx-preview@0.3.2/dist/docx-preview.min.js"></script>
<script>
fetch('/arquivo.docx').then(r => r.blob())
  .then(b => docx.renderAsync(b, document.getElementById('alvo'), null,
    { className: 'docx', inWrapper: true, breakPages: true, experimental: true }))
  .then(() => { document.title = 'ok'; })
  .catch(e => { document.getElementById('alvo').textContent = 'ERRO: ' + e; });
</script>`;

http.createServer((req, res) => {
  if (req.url.startsWith('/arquivo.docx')) {
    res.writeHead(200, { 'Content-Type': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' });
    fs.createReadStream(DOCX).pipe(res);
  } else {
    res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
    res.end(PAGINA);
  }
}).listen(8731, () => console.log('previa em http://localhost:8731'));
