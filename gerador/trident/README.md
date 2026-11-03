# Trident 350

Documento: `trident-panel-holder-v1` (Fusion, Voron/Panel-Holder, direct modeling).

## Referência

- CAD `Trident_Assembly` (projeto Voron): é uma Trident 250. A topologia (onde ficam rasgos, portas, dobradiças, trincos) vale; as medidas da 350 saem dos parâmetros: frame 510 × 510 × 500 (horizontais 470, verticais 500, como a 250 em altura).
- `referencia/trident_frame.json`: as 15 extrusões do CAD (250). `referencia/frame_350.json`: o frame da 350 usado no documento (13 barras: 4 postes de 500, 8 barras de 470, poste central traseiro de 330; coordenadas centradas, z = 0 no pé, traseira em +y). `referencia/misumi_2020.json`: seção do HFSB5-2020, face do rasgo em y = 0.
- `obstaculos.py` + `referencia/obstaculos_250*.json`: o que o CAD tem em cada borda (na frente da face e dentro do rasgo).
- Rasgo 2020: abertura 6,0; aba 2,0; cavidade ±6,0 até 2,94 de profundidade, afunilando a 45° até ±2,94 no fundo a 6,0 (V de 0,3 no centro).
- Chapas: a mesma espessura das do V0 do usuário (2,7). Painéis originais da Trident: laterais com espuma de 3 mm e clips "6mm"; topo e traseira (opaca) com espuma de 1 mm e clips "4mm"; duas portas na frente, com dobradiças nos postes de fora, que se encontram no meio sem poste (trincos nas barras de cima e de baixo).

## Fase 1: corpos de prova do rasgo 2020

- A mesma aleta bipartida do V0, com os valores do 2020: raiz preenche a abertura de 6, pernas de 1 mm, farpa sob a aba de 2, ponta a 5,7 (0,3 do fundo).
- Três farpas para testar: `clip-padrao` (0,1 por lado), `clip-padrao-farpa-02` (0,2), `clip-padrao-farpa-03` (0,3), com a `tampa-parede`. STLs em `stl/trident-provas-v1`.
- Conferido no Fusion: nenhuma interferência com o perfil; só a pré-carga de 0,1 da nervura na chapa.

## Fase 2: montagem completa (v1)

6 faces, 145 peças (144 nas bordas + o passa-bowden), 17 componentes de canto. Mesmas regras do V0: tampa de cada borda em 3, clips em 4 (meio, inteiro, inteiro, meio), cantos em L com meia-esquadria.

| face | bordas | observação |
|---|---|---|
| laterais | base `tampa-base-h`, topo `tampa-parede-h`, frente e trás `tampa-parede-v` | na frente, os cantos têm o nó da dobradiça da porta |
| traseira | igual às laterais | o poste central de trás fica atrás da chapa, sem clips |
| topo | 4 bordas `tampa-parede-h`, cantos `canto-parede-hh` | |
| portas | base e topo `clip-porta-d*` (aleta maciça), dobradiça `clip-porta-dobradica-*` (aleta em arco), centro `clip-u-centro-*` (sem aleta, não há poste) | chapa original de 241,5 × 473 |

- `tampa-base` (nova): a tampa com parede, sem a cunha, para as bordas de baixo (não há top hat embaixo).
- Portas: cada uma com `door_width` = 254,75 (metade do frame menos `door_gap` de 0,5 no meio). Os clips de cima e de baixo começam `frame_size` depois do centro, onde termina o clip em U, como se ali houvesse um poste. O centro da tampa de cima e de baixo fica no meio da porta.
- Portas com a chapa original (`door_sheet_width` 241,5, medida no CAD: 191,5 na 250 + 50). As originais se encontram no meio, sem folga, então:
  - centro: peças `clip-u-centro-*` (perfil `clip-u-fora`), um U cuja parede de fora (`u_outer_wall` 2,5) é a face da porta; a tampa (`tampa-u-fora`) não tem parede e fica por cima dela. A chapa fica a `u_outer_clearance` (0,5) da parede, a 3,25 do meio do frame;
- Vedação entre as portas: `door_gap` de 0,5 (era 1). Numa fresta estreita o fluxo é laminar e cai com o cubo da folga: ~8 vezes menos que com 1 mm, e as portas continuam abrindo cada uma por si (no giro, a borda do meio sai para fora, quase perpendicular à face). Se as peças impressas empenarem e roçarem, é só voltar o parâmetro.
  - dobradiça: batente e rabo-de-andorinha `door_hinge_shift` (2,75, calculado) mais para fora (`clip-porta-dobradica`, `tampa-parede-dobradica`); a chapa vai até o centro do rasgo. Por fora as peças não mudam, e o giro continua limpo.
- Dobradiças: as mesmas do V0 (pino M3, nó de meio disco concêntrico ao pino), pino a `frame_size/2 + 4,25` do centro do rasgo. `verificar_dobradica.py trident` passa limpo de 0 a 120°.

Verificado no Fusion:

- interferência peça × frame: nenhuma nas 6 faces;
- entre faces: nenhuma;
- giro das duas portas (`giro_porta`) a 15, 45, 90 e 110°, contra a lateral do mesmo lado e a outra porta: nenhuma interferência;
- chapa de 241,5 × 473 posta em cada porta (centrada, encostada no meio, encostada na dobradiça, embaixo e em cima): só a pré-carga de 0,1 da nervura. Folga total de 1,5 na largura (1 na dobradiça, 0,5 no centro) e 1,5 na altura;
- traseira com a chapa original de 483 × 473 e o recorte do exaustor: só a pré-carga de 0,1; o passa-bowden encosta no clip da borda de cima também só pela nervura (as verificações mostram isso como pré-carga).

## Chapas

A borda da chapa fica a 3 do centro do rasgo (batente a 2 mais 1 de folga).

| face | chapa (mm) | original da 350 (aprox.) |
|---|---|---|
| laterais e traseira | 484 × 474 | 483 × 473: serve |
| topo | 484 × 484 | 483 × 483: serve |
| portas | 241,5 × 473 | 241,5 × 473: a original |

As medidas das originais da 350 saem do CAD da 250 (+100 na largura e na profundidade).

## Tampas mais altas e encaixe sobre o clip

- `cover_height` 5 (era 4, como no V0): a parede da tampa sobre o canal do rabo-de-andorinha passa de 1,0 para 2,0. A tampa fica a 9,3 da face do perfil.
- `dovetail_inset` 0 (era 2, herdado do V0): o rabo-de-andorinha do clip fica todo sobre o corpo do clip, em vez de pendurado 1 mm sobre a chapa; o pescoço que o liga ao clip passa de ~2,1 para ~4,0. No V0 (1515) não há espaço para isso.
- Conferido: perfis válidos, sem sobreposição clip × tampa nem chapa × tampa; giro das portas limpo em 2D (até `cover_height` 6) e em 3D a 15, 45, 90 e 110°; interferência limpa nas 6 faces e entre faces.
- Corpos de prova novos em `stl/trident-provas-v2` (a tampa da v2 não encaixa nos clips da v1; as farpas são as mesmas).

## Afastamento de 3 mm (como a espuma das laterais)

- As laterais originais ficam sobre espuma de 3 mm. No CAD da Trident, além da face lateral do frame só ficam as juntas XY e os carros do Z (que se movem), 0,3 mm para fora, alguns M3 a 0,25 e os suportes dos motores do Z a 0,1. Com 1,6 de base a chapa ficava a 1,3 mm deles; o usuário preferiu os 3 mm do original.
- `panel_frame_spacing` 3 (era 1,6; vale para todas as faces): a chapa a 3 da face, folga de 2,7 como o original; tudo acima sobe 1,4 (topo da tampa a 10,7).
- `base_inset` 1: a base do clip sob a chapa começa 1 mm antes da borda de dentro do perfil (perfis.BASE_START), longe dos carros do Z e das juntas XY que passam rente à borda do poste.
- Espuma colada nos clips: não usada (a vedação na borda já é rígida e contínua; espuma sob a chapa brigaria com o travamento da tampa).
- Toda a Trident regerada e conferida (só as pré-cargas projetadas, nada entre faces, giro das portas limpo). Lateral direita para imprimir em `stl/trident-lateral-direita-v1` (24 peças, com quantidades).

## Folgas mínimas (como no V0, revisão c)

- `dovetail_clearance` 0,05 por flanco (era 0) e `panel_preload` 0,05 (era 0,1), os mesmos valores do V0. A tampa imprime de face para baixo, e os flancos da ranhura saem em degraus de camada: com camadas de 0,2, cada degrau avança até 0,06 (flanco de 30°) e 0,08 (flanco de 40°) além da linha. Com folga 0, esses degraus raspavam no clip ao longo de toda a tampa, que aqui chega a 330 mm. Com a folga, a tampa pode subir ~0,07 antes de os flancos encostarem, e a chapa fica justa sem forçá-la contra eles.
- Toda a Trident regerada (145 peças) e conferida: só as pré-cargas projetadas (cunha de 0,2 na aba, nervura de 0,05 no passa-bowden), nada entre faces, giro das duas portas limpo a 15/45/90/110°. Lateral direita em `stl/trident-lateral-direita-v2`, com a quantidade no nome de cada arquivo; a v1 ficou marcada como substituída.
- Lateral esquerda em `stl/trident-lateral-esquerda-v1` (mesmos valores; clips e tampas retas iguais aos da direita, só os cantos são espelhados).

## Rasgo do frame do usuário: 6,35

- O usuário mediu o rasgo do frame dele: 6,3 a 6,4 (o Misumi HFSB5-2020 do CAD tem 6,0). `slot_opening` passou para 6,35, e a referência do perfil virou `referencia/perfil_2020_usuario.json` (a seção do CAD com a abertura dos 4 rasgos alargada; o resto igual, porque aba e fundo não foram medidos).
- Era isso que deixava folga na v4: a sobra de ~0,175 por lado comia o aperto da cunha e deixava as pernas soltas de lado. Com 6,35, as pernas enchem a abertura e a cunha aperta de verdade. Batentes e rabos-de-andorinha andaram 0,175 junto (`-slot_opening/2`); o batente da dobradiça não muda (a fórmula de `door_hinge_shift` compensa).
- Farpa 0,45, aperto padrão 0,3 (`fin_barb_gap` -0,3). Corpos de prova em `stl/trident-provas-v5` com 0,2, 0,3 e 0,4. Toda a Trident regerada e conferida: interferência só a pré-carga projetada, nada entre faces, giro das portas limpo.

## Aperto x força para tirar (v5 → v6)

- v5: nenhuma folga (aperto da cunha 0,2 a 0,4), mas muito apertado para entrar e a perna quebrava ao tirar. São dois parâmetros diferentes: o aperto da face de 45° no canto da aba tira a folga; quanto a farpa passa da abertura (`fin_barb`) é o quanto a perna dobra para entrar e sair. A v4 passava ~0,225 do rasgo real e entrava e saía bem; a v5, 0,45.
- v6: aperto 0,2 (`fin_barb_gap` -0,25 com `fin_root_clearance` 0,05 de folga lateral por lado), `fin_barb` 0,3; corpos de prova em `stl/trident-provas-v6` com 0,25, 0,3 e 0,35.

## Clip comprido: força para pôr e tirar (v7)

- Com a lateral inteira, o clip padrão (farpa 0,3, aperto 0,2) ficou muito duro para pôr e tirar: o corpo de prova tem 20 mm e o clip, de 78 a 165, então a força cresce com o comprimento.
- Encaixada, a perna fica dobrada pelo aperto, a face de 45° contra o canto da aba. Para entrar e sair ela dobra até a largura da farpa, e é esse pico que pesa. A farpa precisa passar do aperto com folga, senão o canto da aba fica na ponta dela e o clip perde o encaixe.
- Três provas no comprimento do `clip-padrao-h1` (78,3), em `stl/trident-provas-v7`:
  - `clip-h1-pernas-625`: `fin_root_clearance` 0,1 e `fin_barb` 0,25, as pernas recolhidas 0,05 por lado como num rasgo de 6,25. Pico 0,25, aperto 0,15. `slot_opening` continua 6,35 (é a medida real; batentes e rabos-de-andorinha dependem dela).
  - `clip-h1-farpa-025`: `fin_barb` 0,25. Pico 0,25, aperto 0,2.
  - `clip-h1-trechos`: o perfil padrão, com a farpa só em trechos de `fin_anchor_length` 10 (um em cada ponta, os outros espaçados por igual, no máximo `fin_anchor_gap` 45 entre eles; aqui são 3). Entre eles, as pernas ficam sem farpa (`perfis.barb_cut`) e entram livres. Vale para as peças de verdade quando `fin_anchor_length` > 0 (hoje 0: farpa no clip inteiro).
- `perfil()` agora reavalia a tabela inteira com as mudanças da variante. Na v6, só `fin_barb` mudava e a rampa ficava com o valor do padrão: as variantes 0,25 e 0,35 saíram com a face a 40,6° e 48,8° e aperto de 0,164 e 0,236.

## Clip mais frouxo para colocar e tirar (v8)

- Resultado da v7: os três melhoraram, mas ainda estavam difíceis de colocar e muito difíceis de tirar. Também não dava para saber qual era qual: agora cada variante leva entalhes no topo do rabo-de-andorinha (`config.MARCAS`, 1 a 4, etapa `_marca` de `perfil()`).
- A aba do rasgo tem 2 mm, então a farpa dobra a perna a 2 mm da raiz, uma alavanca curta e dura. Na rigidez, a espessura entra ao cubo; o ângulo da face da farpa pesa só ao tirar, porque é nela que a aba empurra quando o clip sai.
- A face da farpa agora sai de dois parâmetros: `fin_squeeze` (aperto horizontal no canto da aba, 0,2) e `fin_barb_angle` (da vertical, 45°). `fin_barb_gap` e `fin_barb_ramp` são calculados deles (os mesmos −0,25 e 0,35 de antes).
- Provas em `stl/trident-provas-v8`, no comprimento do h1, com aperto 0,2 e farpa 0,3 (estimativa de força para colocar / tirar em relação ao padrão):
  - 1 marca, `clip-m1-pernas-finas`: `fin_leg` 0,75, `fin_tip_leg` 0,6 (~0,4 / ~0,4);
  - 2 marcas, `clip-m2-finas-30`: pernas de 0,75 e face a 30° (~0,4 / ~0,25);
  - 3 marcas, `clip-m3-muito-finas-30`: pernas de 0,6/0,5 e face a 30° (~0,2 / ~0,12);
  - 4 marcas, `clip-m4-finas-30-trechos`: pernas de 0,75, face a 30° e farpa em 3 trechos de 10 mm (~0,15 / ~0,1).
- Resultado: nenhum ficou com folga; o 2 e o 4 já começam a ficar bons; o 3 falhou na impressão (o usuário vai reimprimir). Critério do usuário: a força é por comprimento. Um pedaço curto pode parecer meio solto, mas 50 cm de clip não ficam soltos; e, se a força total for alta, as outras partes do encaixe (rabo-de-andorinha, cantos) quebram antes de o clip sair do trilho.
  - 5 marcas, `clip-m5-finas-30-farpa-02`, para ir com a reimpressão do 3: pernas de 0,75 (imprimem bem), face a 30°, `fin_barb` 0,2 e `fin_squeeze` 0,15 (~0,28 / ~0,16, perto do 3). Alivia pela farpa, não pela perna.
- O 3 falhou porque a ponta das pernas sumia no fatiador (gerador classic, perímetro de 0,4). Ali a perna é inclinada, e a parede, medida de lado, tinha 0,38, embora a ponta tivesse 0,5 na horizontal. Regra do usuário: a parede das pernas deve ter pelo menos 0,4. `perfis.leg_min_wall` mede a parede de lado, e `perfil()`/`pecas()` recusam um clip abaixo de `fin_min_wall` (0,4). O 3 foi refeito com ponta 0,6 e `fin_inner_straight` 4,2: parede mínima 0,48, raiz ainda 0,6. Paredes atuais: padrão 0,63; 1, 2 e 4: 0,47; 5: 0,46. O V0 tem 0,396 (pernas de 0,5/0,4 do v11, já impressas).

## Trava deslizante (corpo de prova)

- Ideia do usuário: em vez de tudo na pressão dos clips, poucas travas de dois estados por painel (com várias travas, cada uma tem que ficar sozinha no estado em que foi deixada). Uma peça só, botão e lingueta: aberta, a lingueta fica num trecho do clip sem pernas; deslizando, entra no vão entre as pernas, que não conseguem mais dobrar para dentro, e o clip não sai.
- Descartados no caminho: o T de 1/4 de volta (feio), a pega e o botão que só soltam enquanto seguros (precisaria abrir todas ao mesmo tempo), e pino com articulação pequena ou trilho (em plástico impresso, folgas de décimos, desgaste e fluência no ABS quente).
- `trava_deslizante()` monta o corpo de prova com os parâmetros `trava_*`: clip padrão de 40 com a janela sem pernas e o rasgo da haste aberto numa ponta, tampa com o rasgo, e o cursor (lingueta de 4,15 no vão de 4,25, haste de 2,4, botão de 8 × 10 × 2,5). Conferido: o cursor percorre os 12 mm sem tocar no clip nem na tampa. STLs em `stl/trident-provas-trava-v1`. Ainda sem o clique das duas posições.
- v2 (pedido do usuário): depois do trecho sem pernas, as pernas recomeçam na raiz e descem a 45°, para o clip impresso em pé (sobre a ponta em que o rasgo abre) não precisar de suporte; completas a 5,7 mm da janela. Curso de 12 para 16 mm, para a lingueta travada ficar toda entre pernas completas. STLs em `stl/trident-provas-trava-v2`.
- v3 (pedidos do usuário): o cursor é uma peça chata, com lingueta, haste (`trava_haste` 2,4) e botão rentes do mesmo lado (+s), e imprime deitado sobre ele, com os três na mesa; em pé quebraria entre camadas. Lingueta com bico (`trava_entrada` 1,2 por lado em `trava_entrada_comprimento` 3: ponta de 1,75). O rasgo do clip fica rente à face de dentro das pernas desse lado, sem cortar a raiz delas. Ao longo do rasgo, o flanco de fora do rabo-de-andorinha virava uma lasca solta e foi removido; ali a tampa segura pelo flanco de dentro. STLs em `stl/trident-provas-trava-v3`.
- Para ajustes à mão, as três peças da v3 saíram em STEP (`stl/trident-provas-trava-v3/*.step`) e foram abertas no documento `trava-deslizante-v3` (Voron/Panel-Holder, paramétrico). O que o usuário mudar lá não volta sozinho para o gerador: levar de volta para `trava_deslizante()` e os parâmetros `trava_*`.
- v4 (pedido do usuário: a parte de fora integrada à tampa e o rasgo todo escondido, com um botão de crista como os de chave deslizante). Para esconder o rasgo aberta e travada, o botão precisa de 2 × curso + haste + folgas + sobra nas pontas. Por isso o curso caiu de 16 para 10: as pernas voltam a 45° do lado da ponta, o clip imprime em pé pela outra ponta, e travada a lingueta só precisa sair da janela.
  - O botão é uma capa separada (`trava-capa`, 27,4 × 14, crista de 3, abas côncavas, centrada no topo plano da tampa), que desliza de lado num toco em rabo-de-andorinha da trava. Peça única, o botão só cresceria para dentro do lado da mesa da trava (máximo de 7,2 centrado).
  - A trava entra de cima, com a tampa já no clip, por uma abertura do tamanho da lingueta no meio do curso, na tampa e no clip (ali o clip fica sem nada entre as pernas e sem rabo-de-andorinha). Nada chega à ponta, então a trava pode ficar em qualquer ponto de uma tampa. Aberta ou travada, parte da lingueta fica debaixo do clip e a trava não sai.
  - `trava_deslizante(parte)` constrói uma peça por chamada. `trava_conferir('curso' | 'entrada' | 'capa')` move cópias temporárias pelo curso, pela descida e pela entrada da capa, e mede a sobreposição: tudo 0 no passo de 0,5. Travada e levantada 1 mm, a trava bate no clip. STLs e STEPs em `stl/trident-provas-trava-v4`.
  - Revisão para imprimir sem suporte (pedido do usuário, antes de imprimir a v4): bico a 45° (`trava_entrada_comprimento` = `trava_entrada`); no clip, a ponta de cada abertura do lado da janela (o lado de cima na impressão em pé) volta a 45° a partir do topo da base debaixo do acrílico (`_box_rampa`), e ao lado do rasgo a abertura também recua a 45° a partir dessa base. Assim cada camada que recomeça o miolo e o rabo-de-andorinha apoia na de baixo. Os testes continuam zerados e a trava continua presa aberta e travada. Os arquivos da v4 foram regravados. Depois (também pedido do usuário): `trava_chanfro_mesa` 0,4 nas arestas que encostam na mesa, contra o pé de elefante (`_chanfro_mesa`). Ficam na ponta z = L do clip (menos as pernas, finas demais na ponta), na face de fora da tampa, no lado +s do cursor e na face de baixo da capa. Esta última é a orientação que o usuário usa: capa com a face de baixo na mesa, não de lado. Arestas cuja face vizinha já é a 45° ou mais deitada ficam sem (a ponta do cursor, as bordas da tampa).

## V0 com aperto e perna de 0,5 (v14)

- Resultado da v13: o 5 (V0 em escala 2×) é o melhor para colocar e tirar, mas encaixado tem uma pequena folga; o 4 (perna de 0,4 com cunha) também é bom, mas as pernas finas parecem que vão cansar.
- 6, a partir do 5: a face da farpa (23°, como a do V0) passa a encostar no canto da aba, com `fin_squeeze` 0,06 (começa 0,26 acima do pé da aba). Perna de 1,0 e farpa de 0,12, como o 5.
- 7, a partir do 4: perna de 0,5 dobrando 20% menos (farpa 0,24, aperto 0,16). Para a mesma dobra, a deformação cresce com a espessura; assim ela fica igual à do 4 (3% encaixado, 4,5% passando), com o dobro da rigidez. Largura máxima 0,79.
- Provas em `stl/trident-provas-v14`, marcas 6 e 7.
- Escolhido o 6 (2026-10-24): `fin_barb` 0,12, `fin_squeeze` 0,06, `fin_barb_angle` 23°, perna de 1,0. Clips regerados e conferidos (só o aperto de 0,06 da farpa na aba, nada entre faces). Lateral esquerda completa em `stl/trident-lateral-esquerda-v3` (tampas e cantos iguais aos da v2).
- Exportadas também a lateral direita completa (`stl/trident-lateral-direita-v4`, tampas e cantos iguais aos da v3) e as duas portas (`stl/trident-porta-direita-v1`, `stl/trident-porta-esquerda-v1`; peças retas iguais nas duas, só os cantos mudam). Dobradiça: 2 × M3x30 DIN 912 por porta (até 31,1 mm sob a cabeça; rosqueia no nó da lateral, gira no da porta). A aleta maciça (5,95 no rasgo de 6,35), a aleta em arco e o clip em U do centro ainda não foram testados impressos.

## Pescoço de 0,4 na perna (v13)

- Ideia do usuário: a perna com só 0,4 da raiz até o meio, para o ABS flexionar fácil. `fin_neck` (espessura do pescoço, padrão = `fin_leg`, sem pescoço) e `fin_neck_length` (2,8 a partir da raiz; depois alarga a 45° até `fin_leg`). Afina pelo lado de dentro; a face de fora, a farpa e o aperto não mudam.
- Com 0,4: rigidez ~×0,06, deformação ~4,5% para a farpa passar e ~3% encaixado, o mesmo nível das pernas do V0 (perna de 0,5, aba de 1, farpa de 0,06). Parede mínima 0,40.
- Prova em `stl/trident-provas-v13`. A primeira (marca 3, pescoço só até 2,8) saiu oca no fatiador: abaixo do pescoço a perna voltava a 1,35 na farpa, e um contorno de 0,4 cobre ~0,8. Substituída pela marca 4: a perna inteira com 0,4 (`fin_leg` 0,4, ponta 0,6, face de dentro reta até 4,2), no máximo 0,75 na farpa, parede mínima 0,40.
- Marca 5, `clip-p5-v0-escalado`: o V0 em escala 2× com o canal real de 6,35 (perna 1,0, farpa 0,12, começando 0,4 abaixo da aba numa rampa de 0,4, sem cunha). Nunca testado: as provas v1–v4 tinham a perna do V0, mas com a farpa calculada para 6,0, e a folga vinha daí. Sozinho no perfil deve ter ~0,4 de folga axial; montado, a chapa puxa o clip para fora contra a aba, como no V0. Recomeçar das pernas do V0 escaladas foi discutido: as primeiras provas da Trident (v1–v3) já eram essas pernas e tinham a folga para cima e para baixo; o pescoço mantém o aperto que tirou essa folga e dá à perna a flexibilidade da do V0.
- O alívio da v12 (marcas 1 e 2) não muda nada do que segura o acrílico (nervura, batente, tampa): só solta a perna dentro da base. Desenho em `trident-alivio-pernas.png`.

## Pernas que flexionam: alívio na raiz (v12)

- Resultado da v10/v11: o 9 (farpa em trechos) foi o melhor, sem folga e mais fácil; o 10 e o 11 (pernas recolhidas) continuaram duros e ficaram com folga encaixados; os outros, muito apertados. E as farpas dos trechos gastam (foto: raspadas, esbranquiçadas).
- Diagnóstico: as pernas não flexionam. A aba do 2020 tem 2 mm e a perna nascia na face do perfil, então a farpa empurrava a ~2 mm da raiz: para dobrar 0,3 ali, uma perna de 1 mm teria ~11% de deformação (o ABS escoa a 2–3%). Quem cedia era a farpa.
- `fin_relief`: a raiz de cada perna sobe para dentro da base, entre um sulco de `fin_relief_gap` (0,6) por fora e o vão entre as pernas por dentro. Com 2 mm (a base tem 3: sobra 1 mm de ponte sob a chapa), o braço vai de 2 para 4 mm: rigidez ×0,12, deformação ~2,8% (2,1% com perna de 0,75). Com 0, o perfil é o de antes (o esboço pula os pontos repetidos).
- Provas em `stl/trident-provas-v12`, padrão com farpa no comprimento todo: marca 1, alívio 2 com perna de 1,0; marca 2, alívio 2 com perna de 0,75. As marcas recomeçam (as provas antigas já deram resultado).

## Um ajuste só: pernas recolhidas (v11)

- O usuário pediu para parar de multiplicar alternativas: o ajuste é a distância entre as pernas. `fin_inset` (0 no padrão) desloca a perna inteira (raiz, farpa e ponta) em direção ao centro do rasgo, por lado: a dobra para entrar e sair e o aperto no canto da aba caem os dois na mesma medida.
- A v7 "pernas-625" era 0,05 por lado (ainda dura). Provas em `stl/trident-provas-v11`, o resto igual ao padrão: marca 10 com 0,10 por lado (dobra 0,20, aperto 0,10) e marca 11 com 0,15 (dobra 0,15, aperto 0,05).

## Clips ainda mais soltos (v10)

- Resultado da v8: o 3 (reimpresso) e o 5 ainda entram e saem mais duros do que o usuário quer; o 2 e o 4 estavam começando a ficar bons.
- Quatro provas abaixo do 4 na estimativa, em `stl/trident-provas-v10`, marcas 6 a 9 (a numeração continua para nenhum clip impresso repetir): 6, raiz 0,5 e face a 30°; 7, raiz 0,6, face a 20°, farpa 0,2, aperto 0,15; 8, raiz 0,5 com face a 20°, farpa 0,2, aperto 0,15; 9, o 3 com farpa só em 3 trechos de 10 mm. Paredes das pernas de pelo menos 0,46.

## Clip preso na tampa (v9)

- Com as peças longas, o clip quase não entra na tampa nem no canto (com alicate, mal sai). A folga do rabo-de-andorinha (0,05) só valia para os flancos: a tampa encostava no clip sem folga na face de dentro da parede (6,7 de altura, s = 7,0) e no ombro ao lado do rabo-de-andorinha (5,3 de largura, d = 6,7). Cavidade impressa sai menor e o ombro da tampa (impressa de face para baixo) é superfície de topo; o atrito soma com o comprimento encaixado.
- Novo `cover_clip_clearance` (0 por enquanto): afasta a parede e o ombro das tampas (e dos nós da dobradiça) do clip. Com 0, todos os perfis ficam idênticos aos de antes (conferido nas duas máquinas).
- Três tampas de teste no comprimento do h1, em `stl/trident-provas-v9` (1 a 3 entalhes na face de fora): flancos / parede e ombro = 0,10/0,15, 0,15/0,20, 0,20/0,30. Variantes de tampa usam `'_perfil': 'tampa-parede'` em `config.VARIANTES`.
- Depois de escolher: com mais folga nos flancos, a tampa pode subir até ~1,4 × a folga antes de os flancos pegarem; se a chapa ficar solta, subir `panel_preload` junto.
- Resultado: a tampa 1 (0,10 nos flancos, 0,15 na parede e no ombro) ficou boa. Adotada (`dovetail_clearance` 0,1, `cover_clip_clearance` 0,15); toda a Trident regerada e conferida (só as pré-cargas projetadas, nada entre faces, giro das portas limpo até 170°). Tampas e cantos das laterais em `stl/trident-lateral-direita-v3` e `stl/trident-lateral-esquerda-v2`; os clips saem depois do teste dos clips.

## Pino da dobradiça na metade da altura da tampa

- O nó da lateral imprimia com uma face de 18,6° (7,5 mm) e outra de 15° a 2,4 mm da mesa: o pino tinha ficado na posição do V0 (4,15 e 4,25 da quina), mas a tampa da Trident é mais alta (base de 3 e tampa de 5: topo a 10,7). O nó (raio até a face do outro painel menos `hinge_clearance`) terminava 2,4 abaixo do topo, e uma reta fechava o perfil.
- Agora `door_pin_s` = borda + 5,45 e `door_pin_d` = 5,45, a metade de (10,7 + 0,2), como no V0: os dois nós chegam ao topo da tampa (a mesa), sobra só uma rampa de 0,7 mm junto da mesa. Parede em volta do furo: lateral 2,4 → 3,6; porta 2,2 → 3,5. `door_arc_outer` 16,5 → 18 mantém a raiz da aleta em arco onde estava no rasgo (-1,7 a 0,9).
- Conferido: giro em 2D limpo até 180°, aleta fechada sem tocar o poste; no Fusion, as duas portas limpas a 15, 45, 90, 110, 150 e 170°, interferência e entre faces limpas. Mudam os 8 cantos com dobradiça e os clips `clip-porta-dobradica-*`.

## Farpa em cunha (folga para cima e para baixo)

- Nos corpos de prova, o clip encaixado sobe e desce no rasgo (vídeo do usuário). A farpa antiga começava 0,2 abaixo da aba (`fin_barb_gap` 0,2) e saía só 0,1 (`fin_barb`), com a face quase vertical: o clip tinha 0,2 de folga livre e a farpa de 0,1 quase some na impressão.
- Agora: `fin_barb` 0,4, face de 45° (`fin_barb_ramp` = `fin_barb`) que começa 0,2 acima do pé da aba (`fin_barb_gap` -0,2). Com a base encostada, a face ainda aperta o canto de baixo da aba em 0,2: a perna fica levemente flexionada e a cunha puxa a base contra o perfil. Diferenças de impressão só mudam onde a cunha para na rampa. `fin_barb_end` 1: a farpa termina mais alto, e a rampa de entrada da ponta fica a ~40°.
- A pressão lateral da v3 (`fin_lip_preload`, pernas inclinadas) não era o problema: voltou a 0 (o parâmetro continua).
- Corpos de prova em `stl/trident-provas-v4` com o aperto da cunha em 0,1, 0,2 e 0,3. Nas verificações, o aperto aparece como pré-carga (`aleta apertando a aba do rasgo`).

## Puxador das portas

- Um por porta, no meio da altura, na tampa do meio da borda do centro: o mesmo do V0 (`construir.puxador()`), mas para dentro (`config.PUXADOR = ('tampa-porta-centro-v', 'dentro')`). As portas se encontram no meio, então a aba passa da borda de dentro da tampa, sobre a chapa da própria porta: `handle_reach` 4, trecho cheio de `handle_length` 30, rampas de `handle_taper` 6, sulco em V no topo perto da borda.
- A aba fica rente ao topo da tampa (preenche o chanfro de dentro), então a tampa continua imprimindo com a face de fora inteira na mesa, como no V0. Sob a aba, até a chapa, ficam 2 mm.
- Conferido: interferência limpa nas portas e entre faces; giro das duas portas limpo a 15, 45, 90 e 110°.

## Passa-bowden (traseira)

O usuário não tem o filtro de exaustão. A chapa traseira original tem o recorte do exaustor no meio da borda de cima (CAD: 147 de largura, `exhaust_notch_width`; da borda da chapa até 42,5 abaixo, `exhaust_notch_depth`; cantos de baixo r 3,5). Antes, duas placas impressas (colmeia por dentro, lisa por fora) fechavam o recorte, com o conector pneumático de PTFE 4 mm no meio e o braço roxo do tubo parafusado na placa de dentro.

`passa-bowden` (`construir.passa_bowden()`) substitui a placa de fora e se adapta aos clips:
- tampão com a espessura da chapa (2,7) que preenche o recorte (folga de 0,3, cantos de baixo chanfrados de 3 para livrar o raio de 3,5); a borda de cima dele fica sob o clip e a tampa da borda de cima, como o resto da chapa;
- aba de fora de 2,4 sobre a chapa, 8 nos lados e embaixo, parando 0,5 antes da tampa da borda de cima;
- furo de 10,2 para o conector (1/8" BSP do BOM original, ~9,7, ou M10), com a porca por dentro apertando a placa de colmeia do usuário, que continua com o braço. Posição: `bowden_hole_x` (0, meio) e `bowden_hole_up` (16 acima do fundo do recorte).
- montado pela lista `extras` da borda de cima da traseira (`mapa.EXTRAS`), no referencial da borda.

## Fora desta versão

- Suporte do carretel (no poste de trás à direita) e tela (na saia da frente, fora das bordas dos painéis).
- Puxador e logo (no V0 ficam no meio da porta e no top hat).

## Próximo

- Testar as laterais e as portas impressas (principalmente os clips da porta, ainda não testados); depois exportar a traseira e o topo com os valores finais.
- Conferir o conector do bowden (rosca) e a placa de colmeia de dentro (precisa ser lisa do lado da chapa).
- Exportar os STLs da Trident.
- v5 (usuário: cursor e capa absurdamente frágeis, o rabo-de-andorinha entre eles não imprimia: toco de 1 mm, abrindo 0,6 por lado com folga de 0,1, e lábios abaixo do bico de 0,4, ainda comidos pelo chanfro de mesa). O toco fica em cima da tampa e não passa pela abertura, então foi alargado (`trava_toco_largura` 7, a partir do lado da mesa) e passou a ter 1,6 de altura, 0,8 por lado e folga de 0,15. A haste tem 6 mm (era 4) e fica centrada no trecho da lingueta com largura cheia, atrás do bico. A capa tem abas de 2 (era 1) e crista de 4 com 5 de topo plano, o que deixa 1,3 de teto sobre o encaixe; ela mede 29,4. Testes zerados, trava presa aberta e travada. Arquivos em `stl/trident-provas-trava-v5`.
- Variante robusta da v5 (usuário: cursor e capa mais robustos ainda e o cursor mais justo, estava folgado dos lados). Construída por `trava_deslizante(variante='robusta')` com `config.TRAVA_VARIANTES`/`TRAVA_MARCAS`, como `trava-cursor-robusta` e `trava-capa-robusta`. Ela serve no mesmo clip e na mesma tampa: os rasgos deles fixam a haste e o curso, então só cresce o que fica acima da tampa.
  - Toco 2 × 1,0 × 9, com 8 de comprimento (`trava_toco_comprimento`, 1 mm além da haste de cada lado). Capa com abas de 2,6 e crista de 4,6 (topo plano de 7).
  - Mais gorda: o cursor imprime deitado, então as larguras vão em camadas. A lingueta passa de 4,15 (que sai 4,0 ou 4,2 conforme o fatiador) para 4,2, e a haste de 2,4 para 2,6, ou seja, 21 e 13 camadas de 0,2 a partir da face da mesa. Fica 0,025 por lado entre as pernas e no rasgo do clip.
  - Uma marca, na ponta do toco e na face de baixo da capa. Testes zerados; deslocada 0,1 de lado, a trava já bate no clip. Arquivos na mesma pasta da v5.
- v6 (ideias do usuário). A trava em duas partes pode entrar por baixo, pelo lado do frame, com o painel fora da impressora: a lingueta sobe pela janela sem pernas e só o pescoço atravessa o clip e a tampa. Somem as aberturas de entrada, e a folga do rasgo cai para 0,1. Com a v5 o usuário viu a lingueta mal encostando nas pernas: a farpa só passa 0,12 da aba, e uma lingueta de 4,15 que sai com 4,0 deixa 0,125 de cada lado.
  - Lingueta de 4,2 descendo até 4,4, onde as pernas começam a fechar (`trava_lingueta_fundo`). Embaixo, uma quilha a 45° até o fundo do rasgo do perfil (`trava_quilha_fundo`), para a trava apoiar no frame.
  - Almofadas de 0,1 nas pernas no trecho travado (`trava_reforco_*`), que deixam 0,075 de aperto por lado.
  - Pescoço de 3,0 (`trava_haste`; era 2,4 na v5 e 2,6 no primeiro rascunho da v6). Ele cresce para dentro até sobrar 1,2 de parede do clip até o batente do acrílico; para fora já encosta na linha das pernas.
  - O rabo-de-andorinha da capa fica na ponta do pescoço, da largura dele (`trava_toco_largura` = `trava_haste`), abrindo no comprimento. Por isso o rasgo é 0,8 mais comprido atrás. O encaixe da capa abre do lado de fora.
  - `trava_conferir('entrada')` agora testa a entrada por baixo, na posição aberta. Testes zerados, fora o aperto das almofadas (2,2 mm³ travada, só ali). A variante robusta da v5 saiu do config, porque o toco largo dela não passa pelos rasgos. Arquivos em `stl/trident-provas-trava-v6`; corte em `ideias-trava/trava-v6-corte.png`.
- v7, pelas medidas da v6 impressa (paquímetro, primeira camada 0,2, sem compensações no fatiador). Pescoço 2,9 para 3,0, lingueta 4,05 para 4,2, rasgos 3,1 para 3,125 (clip) e 3,2 (tampa), vão nas almofadas 4,1 para 4,05 e sem almofada 4,2 para 4,25.
  - A trava deitada sai 0,1 a 0,15 mais baixa na face de cima, e as almofadas de 0,1 saíram com ~0,05. O pescoço mais largo da v6 não mudou o jogo porque os rasgos crescem com ele.
  - Rasgos sem folga do lado de dentro (`trava_folga_rasgo_dentro` 0): o afinamento da trava vira o jogo, ~0,1.
  - A lingueta ganha uma camada do lado de cima da impressão (`trava_lingueta_extra` 0,2), só na faixa das almofadas, para apertar ~0,15 nelas sem forçar a perna perto da raiz nem a ponta dela. No modelo isso aparece como sobreposição de 0,075 (+s) e 0,275 (−s) nas almofadas, de propósito.
  - A capa não muda. Arquivos em `stl/trident-provas-trava-v7`.
- v7 impressa: primeira versão boa da trava, para o usuário. v8 (ideias do usuário): encaixes casados pela orientação de impressão, em vez de folgas que compensam a impressora.
  - O cursor imprime de costas, em pé sobre a ponta de trás. As camadas continuam ao longo do pescoço; em pé sobre a quilha ou o toco ele quebraria entre camadas. As larguras da lingueta e do pescoço saem em XY, como os rasgos e o vão das pernas. Saem as almofadas, a camada extra e `trava_folga_rasgo_dentro`. A lingueta tem a largura do vão (`trava_folga_lingueta` 0, 4,25) e os rasgos a do pescoço (3,0). `trava_folga_rasgo` ficou só nas pontas dos rasgos.
  - Para imprimir assim sem suporte, o pescoço e o toco começam rentes à ponta de trás da lingueta, e o rabo-de-andorinha só abre na frente (`trava_toco_aba`). Atrás ele é reto, apoiado na mesa. A capa continua presa, porque para sair por cima ela teria que andar contra o lado reto. Com isso a capa ficou com 29,2.
  - Capa sem folga no encaixe (`trava_folga_toco` 0; com 0,15 ela dançava). É o único encaixe com eixos diferentes: o comprimento do toco sai em Z no cursor e em XY na capa.
  - Folga do pescoço tirada do cursor (`trava_folga_haste`): o padrão tem 0, e a variante `folga-005` (marca 1, sulco na face de dentro do toco) tem 0,05 por lado. Os dois servem no mesmo clip, na mesma tampa e na mesma capa (`trava_conferir` usa a capa padrão quando a variante não tem a sua).
  - O usuário queria as pernas lisas, com a medida do canal, já que a trava segura. A primeira ideia, pernas recolhidas que a lingueta empurra de volta, foi descartada: elas ficariam dobradas o tempo todo enquanto travadas, numa câmara a 50–60 °C. Ficou a farpa só onde a lingueta fica travada, mais `trava_farpa_sobra` de cada lado (22 a 32). Nos outros trechos as pernas são lisas (`perfis.barb_cut`).
  - Círculo de aberta/travada (ideia do usuário). É um rebaixo de `trava_indicador_diametro` 5 × `trava_indicador_profundidade` 0,4 no topo da tampa, à frente da capa aberta, no meio do curso. Aberta ele aparece inteiro, com 2,5 até a capa; travada a capa cobre ele com 2,5 de sobra. O disco `trava-indicador` enche o rebaixo, para imprimir em outra cor como o logo, e o chanfro de mesa pula a borda do círculo.
  - Corrigido: a marca das variantes ia para o lado da lingueta, onde não havia toco, e não cortava nada. Agora fica na face de dentro do toco.
  - Testes zerados para os dois cursores. As peças só encostam: deslocado 0,05 de lado, o cursor padrão já interfere no clip e na tampa, e a capa deslocada 0,05 no curso interfere no toco. Levantada 1 mm, aberta ou travada, a trava bate no clip. Arquivos em `stl/trident-provas-trava-v8`; imagens em `ideias-trava/trava-v8-proposta.png` e `trava-v8.png`.
- v9 (ideia do usuário: manter o rabo-de-andorinha dos dois lados com um /\ no começo dele). A ponta de trás do toco virou um /\ a 45° (`trava_toco_aba_tras` 1). A metade de baixo é o flanco do rabo-de-andorinha, que segura o lábio da capa; a de cima volta a 45° até o topo. A ponta do /\ encosta na mesa com o cursor de costas, e cada face fica a 45°, então imprime sem suporte. Um flanco comum, como o da frente (22° da horizontal), ficaria em balanço.
  - O pé do toco começa 1 mm depois da ponta de trás (`trava_toco_comprimento` agora é até onde ele vai). O rasgo não muda, porque a ponta do /\ fica rente à ponta de trás do pescoço. O encaixe da capa segue o mesmo /\.
  - Revisão (pedido do usuário): o chanfro de mesa no rabo-de-andorinha caiu para 0,2 (`trava_chanfro_encaixe`, `_chanfro_encaixe`): a boca do encaixe da capa e o topo do pescoço embaixo do lábio. Com 0,4, a regra das faces a 45° não pulava a ponta aguda do lábio, e o chanfro comia ~0,4 dele. Sem chanfro nenhum, o pé de elefante prenderia o encaixe, que não tem folga. Cursores e capa regravados na mesma pasta.
  - Testes zerados para os dois cursores. A capa levantada 0,3 bate no toco, parada ou deslocada 0,5 para qualquer lado: segura dos dois lados. Clip, tampa e disco iguais aos da v8. Arquivos em `stl/trident-provas-trava-v9`; corte em `ideias-trava/trava-v9-toco.png`.
- v10 (ideia do usuário, desenhada sobre o corte da v9): sem a volta do /\. O flanco de trás desce a 45° do pé do toco até a mesa, e o resto da ponta de trás do toco fica plano na mesa: uma base de 1 × 3 em vez de um gume. O rascunho tinha o flanco a ~30° da horizontal; ficou a 45° porque é a face de baixo dele na impressão, e mais deitado ele cederia onde o lábio da capa apoia. O lábio da capa é o mesmo. Testes zerados, e a capa levantada 0,3 bate no toco. Arquivos em `stl/trident-provas-trava-v10`; corte em `ideias-trava/trava-v10-toco.png`.
- v11 (resultado da v10: quase 100%; o lábio de trás da capa, no lado da base plana, ficou fino e quase arrebentando, embora a capa encaixe firme): a capa passa a imprimir de lado, em pé sobre a ponta de dentro, com o encaixe aberto para cima; a geometria é a mesma, e o chanfro de 0,4 foi para essa ponta. Com a face de baixo na mesa, o lábio (1 × 1 a 45°) eram cinco camadas de 0,9 · 0,7 · 0,5 · 0,3 · 0,1, as duas de cima mais finas que um filete; e a altura do encaixe (2,0) saía em camadas, com teto em ponte de 6,8, contra a do toco em XY no cursor: o teto saía baixo, o toco empurrava a capa para cima e o flanco a 45° empurrava o lábio. De lado, cada camada é o corte do encaixe: o lábio sai inteiro e a altura do encaixe sai em XY, como a do toco. Testes zerados com os dois cursores. Só a capa muda: `stl/trident-provas-trava-v11`; desenho em `ideias-trava/trava-v11-capa.png`.
- v12 (pedido do usuário): a base plana da ponta de trás do toco cai pela metade, de 1 × 3 para 0,5 × 3. O toco continua com 2 de altura; o flanco de trás a 45° passa de 1 para 1,5 (`trava_toco_aba_tras`), então o pé do toco no pescoço fica com 4,5 (era 5) e o lábio de trás da capa cresce de 1 × 1 para 1,5 × 1,5. Testes zerados com os dois cursores; a capa levantada 0,3 bate no toco. Cursores e capa em `stl/trident-provas-trava-v12` (clip, tampa e disco os da v8); corte em `ideias-trava/trava-v12-toco.png`.
- v13 (ideia do usuário): o lábio de trás da capa termina reto, com 0,5 de altura, a 1,0 da ponta de trás (`trava_capa_labio`), em vez de em gume no pé do toco. Na ponta que saiu, mais fina que 0,5, um filete de 0,4 não entra: o centro dele, a 0,2 das duas faces, para justamente a 1,0. O cursor não muda e fica um vão de 0,5 × 0,5 no pé do flanco. Enchê-lo no cursor daria uma face a mais de encosto no curso, que com o cursor de costas seria uma ponte. Testes zerados com os dois cursores; a capa levantada 0,3 ainda bate no toco. Só a capa muda: `stl/trident-provas-trava-v13`; corte em `ideias-trava/trava-v13-labio.png`.
- v14 (ideia do usuário: um "auto brim"): os cursores saem com uma orelha de uma camada na mesa (`trava_orelha_comprimento` 5, `trava_orelha_altura` 0,2), saindo da base plana do toco para fora, além do topo dele, com 2,4 de largura (o toco menos `trava_chanfro_encaixe` + 0,1 de cada lado, longe dos chanfros dos lados, que passam pelos rasgos). O usuário tira antes de montar. A aresta de fora da base leva um chanfro de 0,4 (a orelha mais `trava_orelha_recuo`), e a orelha sai do pé dele: a quebra fica no topo da orelha, 0,2 para dentro da face onde assenta o teto do encaixe da capa. `trava_sem_orelha()` dá uma cópia sem ela; `trava_conferir` usa essa cópia (a orelha entraria na capa). Testes zerados com os dois cursores. Cursores em `stl/trident-provas-trava-v14` (capa da v13); desenho em `ideias-trava/trava-v14-orelha.png`.
- v15 (ideia do usuário, riscando a linha no corte da v12): o rabo-de-andorinha sobe de 2,0 para 2,7 (`trava_toco_altura`), com o flanco da frente no mesmo ângulo, 22° (`trava_toco_aba` 0,8 → 1,1). Atrás fica o flanco de 45° até 1,5 e o mesmo lábio da capa; a base plana do toco na mesa cresce de 0,5 × 3 para 1,2 × 3. A capa fica com 1,7 de teto embaixo da crista (era 2,4) e 1,3 sobre o canto da frente do toco, onde a crista começa a descer; o encaixe só ocupa 6,4 dos 14 da capa. 3,0 deixaria 0,9 nesse canto. Testes zerados com os dois cursores; levantada 0,3, a capa bate no toco com 1,8 / 4,5 / 4,3 mm³ (eram 1,5 / 3,2 / 3,3). Cursores e capa em `stl/trident-provas-trava-v15`; corte em `ideias-trava/trava-v15-toco.png`.
- v16 (ideia do usuário): a ponta de cima do pescoço, atrás, embaixo do lábio da capa, também cai a 45°, do pé do toco até a mesa (`trava_pescoco_chanfro` = `trava_toco_aba_tras`, 1,5; 0 = reto). O lábio ficava preso sem folga entre o topo do pescoço e o flanco, enquanto o teto do encaixe também assentava no topo do toco: dois apoios para baixo, e uma variação da impressão apertava a capa. Agora a capa só se apoia no topo do toco, e o lábio só encosta no flanco, com 0,5 a 1,5 de vão embaixo. Impresso, é um /\ a 45° dos dois lados, 1,5 acima da mesa, sem ponte. A aresta de mesa do topo do pescoço sumiu (chanfros 10/0 e 12/0). Testes zerados; abaixada 0,05, a capa só bate no topo do toco (1,03 mm³; eram 1,15). Cursores em `stl/trident-provas-trava-v16` (capa da v15); desenho em `ideias-trava/trava-v16-pescoco.png`.
- 2026-10-28: a mesma trava gerada para a V0 (`gerador/v0/README.md`, `stl/provas-trava-v1`). Para isso o ângulo da quilha virou parâmetro (`trava_quilha_angulo`, 45° aqui, nada muda), a lasca do rabo-de-andorinha vai até a parede e o sulco de marca tem no máximo um terço da largura do toco (aqui continua 0,6).
- 2026-10-29: para a v3 da V0, o pescoço pode alargar acima da base do clip (`trava_pescoco_largura`, `trava_folga_degrau`). Aqui `trava_pescoco_largura` = `trava_haste` e o toco segue a ele: sem degrau, nada muda.
- 2026-10-29, v17 (pedido do usuário: "uma leve folga" no rabo-de-andorinha, do lado da capa): os flancos do encaixe da capa recuam `trava_folga_toco` ao longo do curso; o teto continua no topo do toco (antes a folga também subia o teto, e foi assim que 0,15 dançou na v8, com a capa deitada). Três capas, variantes só de capa (`encaixe-005/010/015`, 1/2/3 sulcos); o padrão passou a 0,10 até o resultado. Mesmos números da V0 v4: ±f no curso, sobe f, levantada 0,3 ainda bate (parada 1,2 / 0,7 / 0,4 mm³; deslocada 0,5, de 3,2 a 4,1). `stl/trident-provas-trava-v17` (só as capas; o resto é da v16), `ideias-trava/trava-capa-folga.png`.
  - Resultado (2026-10-29, impresso na V0 v4, com o cursor sem folga): ficou 0,15. Como o toco e o encaixe são iguais, é o padrão aqui também; a `trava-capa` foi refeita e as variantes de capa saíram do `config.py`. A v16 da Trident ainda não teve resultado. Sem clique de posição (usuário, 2026-10-29): a pressão da capa já segura a trava firme aberta e travada. Os 3 sulcos de baixo ficam na capa padrão (`trava_capa_sulcos`, novo; usuário: ajudam a segurar e fazem um barulhinho ao deslizar). As marcas de uma variante de capa tomam o lugar deles, então ela precisa de outra contagem. A `trava-capa` é idêntica à `encaixe-015` (volume e faces).

## Chanfro de mesa nas peças de produção (2026-10-26)

- Pedido do usuário: chanfro de 0,4 nas arestas que encostam na mesa, contra o pé de elefante (`bed_chamfer` 0,4; na V0 fica 0, já impressa). O passo é `chanfro_mesa()`, que roda depois de `pecas`, `puxador`, `logo` e `cantos` (está no `construir_tudo`). Ele marca o componente e não repete; `pecas` e `cantos` refazem a peça sem a marca.
  - Clips imprimem em pé: chanfro nas duas pontas, menos na aleta (ela flexiona no rasgo e é fina demais na ponta).
  - Tampas e cantos imprimem com a face de fora na mesa: chanfro no contorno dessa face, sem os rebaixos dentro dela (o do logo leva encaixe rente).
  - Também pedido do usuário: a aresta cuja face vizinha já é a 45° ou mais deitada não leva chanfro, nem a de face vizinha mais baixa que o chanfro (o entalhe de 0,15 entre o nó da dobradiça e o chanfro da tampa). Nas tampas e nos cantos quase todo o contorno já é o chanfro de 3 mm ou a emenda a 45°; sobram as pontas das tampas do meio (o gume agudo da emenda), o puxador e as pontas dos nós da dobradiça.
- Toda a Trident foi conferida depois disso: só as pré-cargas de projeto, nada mais. Laterais e portas foram regravadas em `stl/trident-lateral-direita-v5`, `-esquerda-v4`, `stl/trident-porta-direita-v2` e `-esquerda-v2`. Traseira e topo continuam sem exportar.
