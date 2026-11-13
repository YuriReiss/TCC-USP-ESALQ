"""Extrai texto, estrutura e imagens de um .docx sem dependencia externa."""
import re
import sys
import zipfile
from xml.etree import ElementTree as ET

W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'


def texto_paragrafo(p) -> str:
    partes = []
    for no in p.iter():
        if no.tag == W + 't':
            partes.append(no.text or '')
        elif no.tag == W + 'tab':
            partes.append('\t')
        elif no.tag in (W + 'br', W + 'cr'):
            partes.append(' ')
    return ''.join(partes)


def estilo(p) -> str:
    pr = p.find(W + 'pPr')
    if pr is None:
        return ''
    st = pr.find(W + 'pStyle')
    return st.get(W + 'val') if st is not None else ''


def main(caminho: str):
    z = zipfile.ZipFile(caminho)
    print('### ARQUIVOS DE MIDIA ###')
    for n in z.namelist():
        if n.startswith('word/media/'):
            print(f'  {n}  {z.getinfo(n).file_size/1024:.0f} KB')

    raiz = ET.fromstring(z.read('word/document.xml'))
    corpo = raiz.find(W + 'body')
    print('\n### CONTEUDO ###')
    for el in corpo:
        if el.tag == W + 'p':
            t = texto_paragrafo(el).strip()
            est = estilo(el)
            tem_img = el.find('.//' + W + 'drawing') is not None or \
                b'graphicData' in ET.tostring(el)
            if tem_img:
                print('[[IMAGEM]]')
            if t:
                print(f'[{est}] {t}' if est else t)
        elif el.tag == W + 'tbl':
            print('[[TABELA]]')
            for linha in el.findall(W + 'tr'):
                celulas = [' '.join(texto_paragrafo(p).strip()
                                    for p in c.findall(W + 'p')).strip()
                           for c in linha.findall(W + 'tc')]
                print('  | ' + ' | '.join(celulas) + ' |')
            print('[[/TABELA]]')


if __name__ == '__main__':
    main(sys.argv[1])
