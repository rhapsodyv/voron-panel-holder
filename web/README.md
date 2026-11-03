# Configurador web do panel holder (site estático)

O gerador roda no navegador, sem servidor que execute código. Ele cobre os projetos com clipes (`gerador/clips_b3d.py`: V0, V0 com trava, Trident e Trident com trava) e a peça única, que sempre tem trava:
- **Trident** (`peca_unica_b3d.py`): as laterais, a traseira e o topo. As portas são as da Trident com trava, com clipes, como no projeto.
- **V0** (`peca_unica_v0_b3d.py`): os quatro lados do top hat. As faces do corpo e o tampo ainda não existem, e a frente sai sem o logo. O site é só um conjunto de arquivos, servido por qualquer hospedagem de arquivos (GitHub Pages, Cloudflare Pages, Netlify) ou, no Mac, por `python3 -m http.server`.

- **O motor:** o Python roda no Pyodide (Python compilado para WebAssembly), num Web Worker. O build123d roda sobre o [OCP.wasm](https://github.com/yeicor/OCP.wasm), que é o OpenCascade compilado para WebAssembly.
- **O gerador:** os mesmos `.py` e JSON do `gerador/`, copiados para `web/gerador/`.
- **Faces prontas:** todas as faces com os valores padrão (peças, frame, conferência e ZIP dos STLs) vão geradas de antemão para `web/pre/`. Assim o site abre na hora, e o motor só é necessário quando um parâmetro muda.

## Rodar no Mac

```bash
python3 web/empacotar.py
```

```bash
.venv-b3d/bin/python web/motor.py pre-gerar
```

```bash
python3 -m http.server 8766 --bind 127.0.0.1 --directory web
```

Depois abra `http://127.0.0.1:8766` no Chrome. Refaça os dois primeiros passos sempre que o gerador ou os parâmetros mudarem: `empacotar.py` copia o gerador, e `pre-gerar` refaz as faces prontas (alguns minutos).

## Publicar

O GitHub Pages publica sozinho a cada push na `main` (`.github/workflows/pages.yml`): roda o `empacotar.py` e sobe a pasta `web/`. O `pre/` vai no git, porque precisa do build123d e leva minutos; o `gerador/` e o `stl/` daqui ficam fora, porque o workflow os copia. Então, antes do push, refaça o `pre-gerar` se o gerador ou os parâmetros mudaram. Em outra hospedagem, publique a pasta `web/` inteira, depois dos dois passos acima. Quem abrir o site consegue ver o código do gerador, porque ele é baixado. O Pyodide e os pacotes vêm das CDNs públicas (jsDelivr e PyPI), pelos endereços fixos do `pyodide-lock.json`.

## Arquivos

| Arquivo | O que é |
|---|---|
| `index.html`, `estilo.css`, `app.js` | A página, em inglês: máquina, face, parâmetros, vista 3D (three.js), conferência e ZIP. A escolha fica no link, para compartilhar. |
| `campos.js` | O que a página mostra em inglês: os parâmetros para o usuário (nome, explicação, em que máquinas), os nomes das máquinas e das faces, e as frases das conferências. |
| `motor.js` | O Web Worker: carrega o Pyodide pela trava, copia o gerador e atende a página. |
| `motor.py` | O lado Python: catálogo, montar uma face (malhas e posições, as travas da peça única travadas), conferir, ZIP. Também roda no Mac, para testar (`.venv-b3d/bin/python web/motor.py trident-trava topo`) e para gerar `pre/` (`pre-gerar [máquinas]`). |
| `stl/` | Os arquivos dos kits de trava impressos que o gerador da peça única lê (cursor, capa e disco), copiados pelo `empacotar.py`. |
| `pyodide-lock.json` | As versões e os endereços fixos dos 53 pacotes: build123d 0.13.0, OCP.wasm 8.0.1 e as dependências. Sem a trava, o instalador do OCP.wasm leva uns 35 s consultando o PyPI a cada visita. |
| `trava.html` | Refaz o `pyodide-lock.json` (para mudar de versão). |
| `empacotar.py` | Copia o gerador para `gerador/` e os kits da trava para `stl/`, e lista os arquivos em `gerador/arquivos.json`. |
| `gerador/`, `stl/`, `pre/` | Gerados pelos passos acima; não edite à mão. Só o `pre/` vai no git. |

Peça única no site:
- **Parâmetros:** os dois geradores aceitam parâmetros mudados pelo `MUDANCAS`, que o site preenche. Sem mudanças, saem iguais.
- **ZIP:** é o da exportação do gerador. As peças vêm deitadas, com o suporte, com os STEP e com as peças da trava.
- **Conferência:** é a do próprio gerador, por grupo, mostrando o que não deu zero. São de projeto:
  - o aperto do gancho;
  - a orelha do cursor na capa;
  - nos cantos de dobradiça da Trident, a farpa passando pela aba ao entrar (41,6 mm³ entrando, zero no lugar).

## Medido no Chrome (2026-11-02, Mac)

- **O motor gera as mesmas peças que o Mac:** os volumes batem até a segunda casa (clip, tampa, canto com dobradiça, tampa do puxador, cursor e capa).
- **Mudar parâmetros funciona:**
  - com `fin_inset` em 0,05, o cursor saiu com 408 mm³, como no Mac;
  - com `handle_reach` em 6, a tampa do puxador da porta saiu com 28.252 mm³, como no Mac.
- **Configuração padrão:** a face aparece em menos de 1 s depois de aberta a página, pelas faces prontas de `pre/` (3,9 MB no total, só a máquina escolhida é baixada).
- **Tempos:**

| Etapa | Tempo |
|---|---|
| Motor pronto | de 30 s a mais de 2 min, mesmo com o cache (variou entre as aberturas) |
| Uma face, na primeira vez | 12 a 30 s |
| Conferir | uns 10 s |
| ZIP | menos de 1 s |

- **Download:** na primeira visita, uns 63 MB, sendo 23 MB do OpenCascade.
- **Por que demora a carga:** o OpenCascade (25 MB de WebAssembly) é compilado de novo a cada abertura, e o import do build123d (que puxa scipy, scikit-learn e IPython) leva uns 40 s. Por isso a configuração padrão vem pronta.

## Parâmetros na tela (2026-11-02)

A tela mostra só os parâmetros que fazem sentido para quem vai imprimir (`campos.js`). Eles aparecem com nome e explicação em inglês e com um campo numérico, que aceita ponto ou vírgula. O resto da tabela de cada máquina são decisões de projeto e fica em "Advanced", fechado, pelos nomes do gerador e com expressões.

| Grupo | Parâmetros | Máquinas |
|---|---|---|
| Panel and frame | `panel_thickness`, `panel_frame_spacing`, `slot_opening`, `panel_edge_clearance` | clipes |
| Panel and frame | `peca_unica_vao` | peça única |
| Print fit | `fin_inset`, `dovetail_clearance`, `cover_clip_clearance` | clipes |
| Print fit | `door_fin_clearance` | todas |
| Print fit | `hinge_hole_side`, `hinge_hole_door`, `bed_chamfer` | clipes e Trident peça única |
| Lock | `trava_folga_toco`, `trava_orelha_comprimento` | clipes com trava |
| Print support | `suporte_lamina_contato`, `suporte_folga` | peça única |

A peça única fica com poucos parâmetros. O cursor e a capa dela são os dos kits impressos (o gerador copia os arquivos), então mudar a abertura do rasgo, a altura do painel ou as folgas dos clipes desencontraria a trava.
