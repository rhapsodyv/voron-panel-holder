# Trident com trava (trident-panel-holder-trava-v1)

A Trident 350 (`gerador/trident`) com a trava deslizante nos painéis, num documento próprio: o `trident-panel-holder-trava-v1` (projeto Voron, pasta Panel-Holder) é uma cópia da `trident-panel-holder-v1` (v41), que ficou como estava. Os arquivos daqui herdam os da Trident (`herdar.py`) e só dizem o que muda. A colocação e a construção da trava são as da V0 com trava (`gerador/travas.py`, `construir.trava_pecas`).

## v1 (2026-10-30): 16 travas no meio das bordas

| Face | Travas |
|---|---|
| laterais | 4 cada, no meio de cada borda |
| traseira | 4, no meio de cada borda (aqui toda borda tem rasgo atrás, diferente da V0) |
| topo | 4, no meio de cada borda |
| portas | 0 |

- A emenda dos clips cai no meio de cada borda (clips h1 + h2 + h2 + h1 e v1 + v2 + v2 + v1). Horizontais: trava no h2 cujo z corre para o meio, desliza para o meio; capa de 221,4 a 260,6 do canto, círculo a 255,6. Verticais: no v2 de cima (250–414,7), trava descendo; capa de 244,4 a 283,6 acima do frame, círculo a 249,4.
- Peças: `clip-padrao-h2-trava` (10), `clip-padrao-v2-trava` e `-espelho` (3 + 3), `tampa-base-h-trava` (3), `tampa-parede-h-trava` (7), `tampa-parede-v-trava` e `-espelho` (3 + 3), mais `trava-cursor`/`-espelho`, `trava-capa`/`-espelho` e `trava-indicador`. Nenhum canto muda.
- Ordem no Fusion: `pecas([...])`, `trava_pecas()`, `chanfro_mesa([...])` (o chanfro de mesa da Trident; o rasgo e o círculo ficam sem, por serem laços de dentro da face de fora), `trava_espelho()`, `montar([...])`.
- Cursor e capa: os da prova da Trident v16 com a capa de 0,15 (v17, medida escolhida na V0). A parte de baixo (lingueta, quilha, janela, rasgo da tampa) é a da prova v10, impressa na Trident e aprovada; a de cima (toco e encaixe, v11–v16) é igual à da V0, impressa e aprovada lá (a capa só é mais larga, 14 em vez de 10).

Conferido: clips perdem 624,2 mm³ e tampas 100,8 mm³ cada, em um só corpo; `interferencia` nas 4 faces só com as pré-cargas de sempre e a orelha do cursor; `entre_faces` de laterais × portas, traseira × laterais e topo × lateral direita, e as peças das travas do topo, da traseira e da lateral esquerda contra as faces vizinhas e as portas: nenhuma (a conferência de faces inteiras com o topo leva ~47 s, perto do limite do MCP); `giro_porta` das duas portas limpo a 170°; a 190° encostam as dobradiças (0,34), não as capas.

STLs (só as peças da trava): `stl/trident-trava-v1`, com o LEIA-ME de montagem. O topo completo, com as travas (36 peças; o primeiro topo da Trident exportado com os valores finais), para o usuário imprimir e testar: `stl/trident-trava-topo-v1` (`exportar_faces(['topo'], ...)`; clips h1/h2 idênticos aos da `trident-lateral-direita-v5`, peças da trava às da `trident-trava-v1`). Olhando de cima, as quatro travas do topo fecham no sentido horário.

## v2 (2026-10-31): pernas 0,03 mais soltas e cantos do topo fechados

- O topo impresso (`stl/trident-trava-topo-v1`) entrava firme demais no frame. `fin_inset` passa de 0 para 0,03 aqui (`parametros.py`; a Trident sem trava fica com 0): a perna inteira recolhe 0,03 por lado, a dobra para passar a aba cai de 0,12 para 0,09 e o aperto encaixado de 0,06 para 0,03.
- A lingueta da trava tinha a largura exata do vão das pernas; com as pernas recolhidas, travada ela as abriria de volta (e o ABS cede no calor da câmara). `geometria_trava.geo` agora tira `fin_inset` do vão: lingueta de 4,19 (era 4,25), rasgos do pescoço 0,03 para dentro. Cursor, capa, clips e tampas com trava regerados; o corpo de prova da trava também, e `trava_conferir` (curso, entrada, capa) deu zero.
- Cantos: em cima do montante, onde os clips não chegam, o canto era oco entre a tampa e o frame (5,7 a 8,8 mm), ligado à câmara pelos canais do montante e por baixo do acrílico; lá a fumaça só tinha a borda de fora do canto para segurar. Novo passo `miolo` de `construir.cantos` (parâmetros `canto_miolo` 1 e `canto_miolo_folga` 0,2, só nesta máquina): do batente do acrílico até a parede de fora, do frame até 1 mm abaixo da face de fora da tampa, até 0,2 antes da ponta dos clips. Só entra onde os clips das duas pernas começam depois do batente, ou seja, nos cantos do topo (`canto-parede-hh`, +1778 mm³); nas laterais e na traseira a perna vertical tem clip a 3 mm do canto, que já ocupa esse espaço, e as portas não mudam.
- Regerados e conferidos: os clips padrão (h1, h2, v1, v2 e os com trava), as tampas com trava e `canto-parede-hh`, com o chanfro de mesa; `interferencia` nas 4 faces só com o aperto das pernas na aba (agora 0,03), o da nervura no passa-bowden e a orelha do cursor. Documento salvo numa versão nova.
- STLs: o topo completo em `stl/trident-trava-topo-v2` (36 peças, LEIA-ME, `canto-v1-v2.png`). A lateral, a traseira e as peças de trava da `stl/trident-trava-v1` ainda são da v1 (pernas e trava antigas): reexportar antes de imprimir essas faces.

## Peça única com trava, corpo de prova (2026-10-31)

Ideia do usuário: o clip e a tampa numa peça só, impressa deitada com a face de fora na mesa. A prova v1, sem trava (`stl/trident-provas-peca-unica-v1`, feita à mão no documento "Untitled"), imprimiu bem: base inteira embaixo do acrílico, vão de 2,8 (o teto numa troca de camada), aleta maciça das portas e o suporte do usuário, uma parede de pé na mesa e uma lâmina de uma camada até a borda da base.

`construir.peca_unica_trava()` (partes `'peca'` e `'suporte'`, uma por chamada) faz a prova com a trava, no lugar da prova da trava e com o mesmo cursor, a mesma capa e o mesmo disco. O perfil é `perfis.PECA_UNICA`. Ele não está em `PROFILES`, porque as outras máquinas não têm os parâmetros `peca_unica_*`.

- **Por que pernas:** a trava segura porque a lingueta impede as pernas de dobrar para dentro. A aleta maciça não tem pernas, então só no trecho da trava ela vira as pernas do clip, com o mesmo perfil e a mesma farpa (`fin_inset` 0,03). A farpa fica só embaixo da parte larga da lingueta travada (25,5–29,8).
- **Por que a fenda:** deitada, uma perna presa pela raiz dobraria entre as camadas. Uma fenda de `peca_unica_fenda` (1 mm, Z 10,6–11,6: começa `peca_unica_fenda_topo` 0,1 dentro da peça, porque a face do frame fica no meio de uma camada) solta a perna da peça.
  - A perna fica presa só num pilar de `peca_unica_pilar` (1) junto da janela e na aleta maciça.
  - Ela dobra `peca_unica_dobra` (3) de cada lado da farpa, como uma viga presa nas duas pontas, dentro da camada: ~1,8%, contra ~3,9% da perna do clip em pé.
  - A face de baixo da perna imprime como ponte de 10,3 mm.
- **Suporte:** corpo `suporte`, feito com corpos temporários e somado como corpo. Um join que encosta na peça (as lâminas encostam) funde os dois, mesmo com os corpos participantes.
  - É a parede da v1 na frente, mais paredes depois das duas pontas (pedido do usuário), do lado do acrílico até o batente.
  - Leva lâminas do topo das paredes até a borda e as pontas da base.
  - Parâmetros: `suporte_parede` 1,6, `suporte_folga` 0,6, `suporte_lamina` 0,2.
- **Conferido:**
  - `trava_conferir(..., fixas=('peca-unica-trava',))` (novo argumento; o padrão continua clip + tampa): entrada, curso e capa, tudo zero.
  - Travada, 0,05 para o lado já bate nas duas pernas.
  - O volume da peça (9283,13) bate com o cálculo fora do Fusion (9283,26 com os chanfros aproximados).
- **Exportação:** `peca_unica_exportar(pasta)` gera o STL deitado, com a peça e o suporte juntos, e o STEP do componente. Os arquivos estão em `stl/trident-provas-peca-unica-trava-v1`, com LEIA-ME e `desenho.png`; o cursor, a capa e o disco são cópias dos do topo v2.

### v2: farpa mais funda, pernas mais longas e mais finas (2026-10-31)

- **O que deu errado na v1:** saía mesmo travada. A farpa passava só 0,09 da abertura, e isso some na folga, na quina arredondada da aba e no plástico que amassa.
- **O que mudou (ideia do usuário: "mais grossa onde a trava entra, e mais longa, para forçar menos"):**
  - Novos parâmetros, cujos padrões refazem a v1: `peca_unica_farpa`, `peca_unica_perna`, `peca_unica_farpa_comprimento`, `peca_unica_dobra_fim` e `peca_unica_comprimento`.
  - A v2 está em `config.PECA_UNICA_VARIANTES`: `f020`, `f030` e `f040`, com farpa de 0,2, 0,3 e 0,4. Só a farpa muda entre elas, marcada com 1 a 3 sulcos na face de fora, perto da ponta longe da janela.
  - As três têm a farpa só nos últimos 3 mm da lingueta travada, o que deixa 4,3 do pilar até ela. Têm 12 da farpa até a aleta maciça, pernas de 0,8 onde dobram (a face da lingueta fica onde estava) e 50 mm de comprimento.
- **Por que a perna pode ser mole:** travada, quem segura é a lingueta, não a mola da perna.
- **Contas** (`viga2.py`, viga presa nas duas pontas, com a farpa mais grossa que a perna):
  - Deformação na raiz do lado do pilar: v1 2,0%; f020 1,9%; f030 2,8%; f040 3,8%.
  - Força para entrar, relativa à v1: 0,25, 0,38 e 0,52.
  - Só alongar o lado da aleta não basta, porque o lado curto (o do pilar) manda. Esse lado é limitado pela lingueta: aberta, ela fica na janela; travada, ela tem que cobrir a farpa.
- **Gerar:**
  - `peca_unica_trava('peca'|'suporte', variante=...)` cria o componente `peca-unica-trava-<variante>`.
  - `peca_unica_exportar(pasta, variante=...)` exporta.
  - `trava_conferir(..., fixas=('peca-unica-trava-<variante>',))` confere: zero nas três.
- **Arquivos:** `stl/trident-provas-peca-unica-trava-v2`.

### v3: farpa longa, curso 14 (2026-10-31)

- A f040 ficou firme, mas o usuário quer a farpa longa, não um quadradinho de 3 mm. Ela só segura onde a lingueta travada fica atrás dela, e a perna precisa de ~4,5 mm de dobra entre o pilar e a farpa. Com curso 10, a lingueta travada começa logo depois do pilar. Então farpa + dobra + pilar + folga ≤ curso, e mais farpa exige mais curso.
- `config.PECA_UNICA_VARIANTES['farpa-longa']`: o _PU_V2 com farpa 0,4, curso 14, `trava_inicio` 17 (a capa aberta continua na peça) e farpa = a largura cheia da lingueta (`trava_lingueta − trava_entrada_comprimento`, 6,8, de 31 a 37,8, 4,5 do pilar). A peça tem 54 mm.
- O cursor é o mesmo. A capa cresce 2 × 4 (37,2): `TRAVA_VARIANTES['curso-14']`, componentes `trava-capa-curso-14` e `trava-cursor-curso-14` (igual ao padrão, só 4 mais para dentro, para o `trava_conferir`).
- Viga: 3,6% na raiz do pilar (f040: 3,8%), mesma força. Conferido zerado (entrada, curso a 0,5, capa). Travada, a lingueta encosta de 31,4 a 37,9.
- STLs em `stl/trident-provas-peca-unica-trava-v3`, fatiados e impressos na V0.
- v2 e v3 ficam com `fin_inset` 0,03 fixo na variante, para combinar com o cursor do topo v2.

## v3 do topo (2026-10-31): fin_inset 0,05

- Pedido do usuário: `fin_inset` de 0,03 para 0,05 (`parametros.py`). A perna inteira recolhe mais 0,02 por lado: a dobra para passar a aba cai para 0,07 e o aperto encaixado para 0,01. A lingueta passa a 4,15, e os rasgos do pescoço e o encaixe da capa andam junto.
- Regerados clips (h1, h2, v1, v2 e os com trava), tampas com trava, `trava_pecas`, chanfro de mesa, cursor, capa e corpo de prova da trava, espelhos e as quatro faces montadas. `trava_conferir` zerado. `interferencia('topo')` só tem o aperto de 0,01 e a orelha do cursor.
- STLs: `stl/trident-trava-topo-v3` (36 peças). Cantos e disco são iguais aos da v2. A lateral e a traseira não foram reexportadas.

### v4: lingueta com dentes (2026-10-31, ideia do usuário)

- Em vez de uma lingueta só, `trava_dentes` dentes (3) de `trava_dente` (4) na largura cheia, com rampas de 45° de `trava_dente_degrau` (0,55) nas pontas e partes estreitas entre eles. As pernas alternam rebaixos de 0,55 na face de dentro com trechos de farpa. Aberta, cada dente fica num rebaixo. Travada, o cursor anda meio passo e cada dente fica atrás de uma farpa. `geometria_trava.geo` tira do dente o curso (a + r + 2·`trava_dente_folga` = 5,35), a lingueta (26,5) e `dentes` (cada dente aberto).
- `_peca_unica_trechos` passou a devolver listas: `farpas`, `rebaixos` e `finas` (afinadas por fora). Na v1–v3 é uma farpa só, como antes. Com dentes não tem janela: o pilar fica logo antes do primeiro rebaixo e o cursor entra por baixo pelos rebaixos.
- Para o cursor subir por baixo:
  - nesta peça a face de dentro da perna desce reta até a ponta, que termina reta onde a rampa de fora deixa 0,5 de parede (a ponta do clip curva para dentro e batia);
  - o pescoço tem 5 mm, para caber no primeiro rebaixo;
  - a quilha fica só embaixo dos dentes, com a traseira a 45°.
- Variante `PECA_UNICA_VARIANTES['dentes']` / `TRAVA_VARIANTES['dentes']`:
  - perna de 1,0 (0,45 nos rebaixos, que é onde ela dobra);
  - dobra final de 8 e peça de 54;
  - círculo de 4 (o curso é menor que 5) e capa passando 4 do rasgo (com 1,5, as abas ficavam com 1,45, e o chanfro dos cantos entrava no côncavo e falhava): 23,9 de comprimento;
  - `trava_inicio` 11.
- Viga: ~1% de deformação, força ~6× menor que a v3. Conferido:
  - entrada, curso e capa zerados;
  - aberta com o cursor ±0,45 (pernas dobradas): nada nas pernas;
  - travada: contato nos três dentes; subir 0,6 e passar 0,2 do curso batem.
- STLs em `stl/trident-provas-peca-unica-trava-v4`, com disco de 4 mm e `desenho.png`. O G-code foi enviado à V0 sem iniciar.
- v4 de um lado só (`PECA_UNICA_VARIANTES['dentes-1lado']`, 1 sulco; pergunta do usuário: precisa de pernas dos dois lados?):
  - `peca_unica_um_lado` 1: a perna do lado do acrílico (−s) fica presa na peça pelo comprimento todo, porque a fenda só vai de −`inner` para fora, e não tem farpa;
  - cursor, capa e disco iguais aos da v4;
  - conferido: zerado; travada, os dentes encostam nas farpas de fora e na parede.

### v5: uma perna só, grossa, com gancho (2026-10-31, desenho do usuário)

- A v4 falhou na impressão: a ponte de 40 mm embaixo das pernas soltas (0,45 nos rebaixos) saiu no ar. Para o usuário, a perna tem que se apoiar na base.
- Na v5 (`PECA_UNICA_VARIANTES['gancho']`, `TRAVA_VARIANTES['gancho']`):
  - uma perna só, do lado do acrílico, de 3,075 a 1,115 do meio, presa na base pelo comprimento todo;
  - `peca_unica_gancho` 1,0: gancho com faces a 45° na peça toda, menos na janela;
  - a lingueta vai `trava_lingueta_desloc` 0,98 para fora, até 0,1 da aba de fora.
- A perna não dobra. Aberta, o cursor fica solto de lado: o rasgo do pescoço tem gancho + 2·folga = 1,2 a mais para −s, e só atravessa a base, sem cortar a perna. A peça entra deslocada 1,1 para fora e volta para enganchar. Travada, a lingueta enche o vão.
- O pescoço vai `trava_pescoco_desloc` 0,73 para fora, para o rasgo largo deixar 0,8 de parede até o batente do acrílico. O cursor ganhou `lingueta` em `geometria_trava.geo`: os lados (wl, wr) usados no corpo, na quilha, no bico, no toco e na orelha.
- Conferido zerado (entrada, curso e capa). Contra um pedaço do rasgo da Trident (feito na hora e apagado):
  - entra deslocada 1,1 sem tocar (com 1,0 raspa);
  - puxando 0,2, o gancho pega;
  - travada, a peça 0,15 para fora bate a lingueta na aba.
- STLs em `stl/trident-provas-peca-unica-trava-v5`. O G-code foi enviado à V0 sem iniciar.
- Rasgo do pescoço da v5: `peca_unica_rasgo_folga`. 1 = folga no rasgo todo (v5). 0 = só o pescoço (`gancho-estreito`, 1 sulco). 2 = folga só onde o pescoço fica aberto, até o bico centrar o cursor, e depois rampa de 45° (`gancho-folga-aberta`, 2 sulcos). Conferido:
  - na de folga só aberta, o cursor solto 1,1 trava centrando pelo bico sem bater;
  - na estreita, o cursor junto com a peça deslocada bate na aba de fora.
  - As duas foram impressas na V0.

### v6: cunha no gancho, contra o balanço (2026-10-31)

- Vídeo do usuário: a peça de 2 sulcos (`gancho-folga-aberta`) travada balança no frame. Travada, só o gancho segura, com 0,1 embaixo da aba e 0,1 de cada lado da lingueta; a face a 45° do gancho transforma a folga de lado em subida (até 0,2 no gancho, ~0,7 na borda de fora). Desenho: `ideias-trava/peca-unica-balanco.png` (com a alternativa B, a farpa do lado da lingueta, ideia do usuário, não feita).
- Na v6 (`PECA_UNICA_VARIANTES['cunha-010']` e `['cunha-020']`, 3 e 4 sulcos; o resto é a de 2 sulcos):
  - `peca_unica_gancho_aperto` (o botão do teste, 0,1 e 0,2): as faces do gancho sobem até a rampa de cima passar isto acima da quina da aba com a peça no lugar (v5: −0,1, folga);
  - `trava_lingueta_alarga` 0,1: a lingueta só cresce para fora, até encostar na aba de fora (`TRAVA_VARIANTES['cunha']`, 1 sulco no toco). Mais não dá: ao pôr a peça, o cursor solto fica só 0,1 para dentro do lugar;
  - assentada, a peça para `aperto` para fora. Ao travar, o bico da lingueta empurra a peça para o acrílico e a rampa do gancho aperta a peça contra o frame.
- Conferido contra um pedaço do rasgo (feito na hora e apagado): no lugar, o gancho entra na quina 0,18 / 0,72 mm³ (o aperto, como esperado); encostada, zero; entrando deslocada 1,1, peça e cursor solto não tocam; o bico encosta na perna em 0,55 e centra sem bater; entrada, curso e capa zerados.
- STLs em `stl/trident-provas-peca-unica-trava-v6`; a capa é a da v5. Impressa na V0 (1h11, 17,2 g).

### Final: rabo-de-andorinha reto + 45° dos dois lados (2026-11-01)

- O usuário fica com a peça de 4 sulcos (`cunha-020`).
- No cursor da v6, o lado de trás do toco (45° e depois reto) segurou a capa mais firme que o da frente (um flanco só, a 22°). Ficou reto + inclinado dos dois lados, com o toco e a capa 1 mm mais altos.
- `trava_toco_frente_reta` (novo, 0 = como antes): o flanco da frente sobe a 45° do pé do toco até abrir `trava_toco_aba` e depois fica reto até o topo. Na capa, o lábio da frente termina reto com `trava_capa_labio`, como o de trás.
- `TRAVA_VARIANTES['final']` = `cunha` mais:
  - `trava_toco_frente_reta` 1;
  - `trava_toco_aba` = `trava_toco_aba_tras` (1,5);
  - `trava_toco_altura` 3,7;
  - `trava_capa_aba` 3,6;
  - `trava_capa_crista` 5,6.
- Marcas: 2 sulcos no toco. A capa mantém os 3 sulcos funcionais, por `TRAVA_MARCAS_CAPA` (novo em `construir`: a marca só da capa, onde a variante tiver).
- Depois (usuário, desenho sobre o corte): capa com o meio plano mais largo e descida mais funda para o dedo.
  - `trava_capa_crista_largura`: 7 → 12.
  - `trava_capa_aba` fica no padrão, 2,6. O usuário achou 1,4 fino demais. A crista fica 2,8 acima das pontas (era 1,8).
  - `trava_capa_concavo`: 5 → 6,6, com ~40° na borda do plano.
  - Cada ponta tem 2,0 plana, passando do chanfro dos cantos (1,5). Com a curva começando dentro dele (côncavo 7,8), o chanfro da mesa falhou: "cannot mitre near-tangent sheet ends".
  - O plano cobre o encaixe todo, com teto de 1,7 nas duas quinas. Com o plano de 7, a quina da frente ficava com 0,97.
  - Sobra 2,0 em cima dos sulcos. A capa segue a linha que o usuário desenhou.
- A peça não muda: o rasgo vai até 29,1, e o topo do toco até 20,5.
- Conferido com a peça de 4 sulcos: entrada, curso e capa zerados.
- A capa tem folga de 0,15 para cima e ao longo da borda, igual nos dois lados.
- STLs em `stl/trident-provas-peca-unica-trava-v7`. Fatiado para a V0: 23 min, 3,4 g.

## v4 dos clips (2026-11-01): fin_inset 0,07 e a lateral esquerda

- Pedido do usuário: a lateral esquerda com `fin_inset` 0,07 nos clips (`parametros.py`; era 0,05).
- A perna inteira recolhe mais 0,02 por lado. A dobra para passar a aba cai para 0,05, e encaixada a perna fica 0,01 solta da aba: segura só pela farpa, sem aperto.
- A lingueta passa a 4,11.
- Regerados, na ordem da v3:
  - clips h1, h2, v1, v2 e os com trava;
  - tampas com trava, `trava_pecas` e chanfro de mesa;
  - cursor, capa, clip e tampa do corpo de prova;
  - espelhos;
  - as quatro faces montadas.
- As variantes da peça única fixam 0,03 e não mudam.
- `trava_conferir` deu zero. `interferencia('lateral-esquerda')` só mostra a orelha do cursor.
- STLs: `stl/trident-trava-lateral-esquerda-v1` (36 peças). Os cantos são iguais aos da `trident-lateral-esquerda-v4`.
- O documento inteiro está agora em 0,07, o topo inclusive. O topo impresso (`trident-trava-topo-v3`) tem 0,05.
