# Trident peça única com trava

A Trident 350 com o clip e a tampa numa peça só, impressa deitada, com a trava final (2026-11-01, pedido do usuário). Os arquivos daqui herdam os da Trident com trava (`gerador/trident-trava`, `herdar.py`) e só dizem o que muda.

As peças são feitas no build123d, não no Fusion (o usuário liberou: "se quiser fazer essa nova versão ... com o build123d ao invés do fusion, também pode"): `gerador/peca_unica_b3d.py`. Ele lê os mesmos parâmetros, perfis (`perfis.py`) e geometria da trava (`geometria_trava.py`) do gerador do Fusion. O corpo de prova cunha-020 refeito por ele bate com o do Fusion (mesmo volume, diferença zero). O documento `trident-panel-holder-peca-unica-v1` (projeto Voron, pasta Panel-Holder), uma cópia da `trident-panel-holder-trava-v1`, ficou sem uso.

```bash
python3 -m venv .venv-b3d && .venv-b3d/bin/pip install build123d shapely matplotlib
.venv-b3d/bin/python gerador/peca_unica_b3d.py cupom
.venv-b3d/bin/python gerador/peca_unica_b3d.py lateral-esquerda
.venv-b3d/bin/python gerador/peca_unica_b3d.py topo
```

`cupom` refaz o corpo de prova e compara com o STEP do Fusion. Com o nome de uma face, ele gera a face, confere as interferências (resultado em `conferencia-<face>.json`) e exporta para `stl/trident-peca-unica-<face>-v1`.

- Divisão A (`mapa.py`): em cada borda, canto + meio + canto, onde a Trident tem as tampas.
- Meios: o perfil da peça de 4 sulcos (`config.PECA`, `cunha-020`), com a perna grossa e o gancho do lado do acrílico na peça toda, menos na janela. A trava fica no meio da peça. A cunha do gancho (aperto 0,2) vai só nos 45 mm do corpo de prova em volta da trava; no resto, `config.APERTO_LONGE` (0). As pontas usam a emenda de 45° da Trident: o meio passa 4 mm por cima da perna do canto e o segura (a emenda de apoio, ideia do usuário).
- Meios com a cunha do canto do frame, como as tampas da Trident (os de baixo sem). Como entram 1,1 para fora, com a face vizinha já montada eles cruzam a cunha dela; o usuário disse que ali isso não é problema. A conferência mostra (`cunhas_entrando`).
- Verticais: a trava desce. O meio de trás de cada lateral é espelhado, com o cursor e a capa espelhados. No topo, as quatro travam no sentido horário, como no topo v3.
- Cantos: o L da Trident numa peça, sem gancho nem trava, com a cunha, o entalhe do dedo e o nó da dobradiça. Aleta lisa das portas; nos cantos da frente das laterais (`config.CANTOS_FARPA`, dobradiça da porta), a aleta farpada dos clips com o `fin_inset` da máquina (0,07).
- Cursor e capa: os finais (`config.TRAVA`, `stl/trident-provas-peca-unica-trava-v7`).
- Portas: os clips separados da Trident com trava, sem trava.
- Feito até agora: a lateral esquerda e o topo (`mapa.FACES`).

Trava v8 (`.venv-b3d/bin/python gerador/peca_unica_b3d.py kit-v8`, em `stl/trident-provas-peca-unica-trava-v8`). O usuário disse: "quando ela estiver presa no acrílico, não vai se mexer". Então a peça entra reta, e o gancho passa da perna da peça para a lingueta do cursor, embaixo da aba de fora.
- A perna fica lisa, com uma rampa a 45° depois da janela.
- Ao travar, a rampa empurra o cursor 1,2 para fora, e a rampa do gancho puxa ele para baixo até a capa apertar a tampa.
- Os três cursores (`config.GANCHO_CURSOR`) variam o aperto: 0,2, 0,3 e 0,4. A capa é a da v7.

A v8 passou, e o cursor escolhido é o de 1 sulco (aperto 0,2). O usuário: "Esse design deu certo, podemos fechar até com o cursor com 1 sulco".
- As faces agora saem em `stl/trident-peca-unica-<face>-v2` (`config.PERNA_LISA`, `config.CURSOR_V8`, `config.FACES_VERSAO`).
- Nelas, os meios têm a perna lisa com a rampa, e o cursor é o `gancho-020` da v8. A capa e os cantos não mudam.
- As peças entram retas, e a conferência (`conferencia-<face>-v2.json`) mede assim:
  - cada peça entrando a 0,5, 2 e 4 mm do frame;
  - a trava v8 na barra embaixo do meio.
- O v1 de cada face (gancho na perna) volta com `PERNA_LISA = False` e `FACES_VERSAO = 1`.
- Feito até agora: o topo v2. A lateral esquerda ainda está só no v1. Os meios verticais dela precisam do cursor gancho-020 espelhado, e isso ainda não foi conferido.

Cursores mais finos, v9 (2026-11-02; `.venv-b3d/bin/python gerador/peca_unica_b3d.py kit-v9`, em `stl/trident-provas-peca-unica-trava-v9`). O usuário: "da pra diminuir um pouco ele, ta meio grosso ainda. o da v0 está bom". O de 1 sulco da V0 tem aperto de 0,1.
- Os dois cursores (`config.GANCHO_CURSOR_V9`) só mudam o aperto: 0,15 com 2 sulcos e 0,10 com 3 sulcos. O resto é o `gancho-020`.
- Eles foram conferidos na peça da v8 junto com o `gancho-020`. Tudo deu zero, menos o aperto do gancho: 0,157 no 020, 0,088 no 015 e 0,039 no 010.
- Quando a prova voltar, o escolhido entra em `config.CURSOR_V8` para as próximas faces.

Mudanças gerais de 2026-11-02 (em `parametros.py` e em `peca_unica_b3d.py`, também usadas pela V0 peça única). O topo v2 e a lateral esquerda v1 já exportados ficam como estão; a próxima exportação de cada face já sai com elas.
- **Vão do acrílico:** passou de 2,8 para 3,0 (`peca_unica_vao`). O usuário: "adiciona pelo menos mais 0.1mm de folga". Deitada, o vão sai em camadas de 0,2, e 3,0 põe o teto dele numa troca de camada, a 8,0 mm da mesa.
- **Lâmina do suporte com 2 camadas:** `_lamina_topo`, `suporte_lamina_topo` 0,4. No último `suporte_lamina_contato` (1 mm) antes da peça, ela fica com 1 camada. O usuário: "tem que fazer essa bridge ter 2 camadas, porem 1 camada só onde encosta na nossa peça".
  - Só as faces passam a peça para o suporte; os corpos de prova (`cupom`) ficam como foram impressos.
- **Chanfro de mesa conferido** (`chanfro_mesa`, o do `clips_b3d.py`, a pedido do usuário). Nos cantos com dobradiça da lateral, a ponta do nó ganha o chanfro de 0,4 que o OpenCascade recusava e ficava de fora (0,7 mm³). As outras peças saem iguais. Detalhes em `gerador/README.md`.
- **Conferido sem exportar:** o topo com as duas mudanças e a trava da peça de prova com o `gancho-020`. Deu zero, menos o aperto do gancho (0,157, o mesmo). O acrílico contra a peça e contra o cursor no curso todo também deu zero.

Configurador web (2026-11-02): `peca_unica_b3d.valores()` aceita parâmetros mudados (`MUDANCAS`, que o `web/motor.py` preenche; vazio, nada muda). O site mostra as laterais, a traseira e o topo. As portas que ele mostra são as da Trident com trava. Na lateral direita, a conferência com a perna lisa (v8) mostra os cantos de dobradiça entrando com 41,6 mm³ no frame: é a farpa (`CANTOS_FARPA`) passando pela aba, que no lugar dá zero.
