# Panel holder do V0.2

Gera o design do panel holder no Fusion (projeto Voron, pasta Panel-Holder) a partir dos perfis e do mapa de bordas em Python.

- **`panel-holder-v13`** (atual): direct modeling, sem timeline. Os valores vivem no `parametros.py`; para mudar uma folga, edite lá e gere de novo. Gerar tudo leva menos de um minuto.
- `panel-holder-v12`: a mesma geometria em modo paramétrico (parâmetros de usuário no Fusion, esboços cotados), fica como referência. Com ~700 features cada etapa passou a levar até 18 s e o Fusion travava. As 35 peças e os corpos de prova do v13 têm o mesmo volume e o mesmo número de faces do v12 (`referencia/v12_pecas.json`).

| Arquivo | O que é |
|---|---|
| `parametros.py` | Os valores: **geometria** (rasgo Misumi 1515 medido no CAD oficial do V0.2, chapa medida), **projeto** (escolhas) e **ajuste** (folgas de impressão, começando pelos valores do v11). |
| `perfis.py` | Cada perfil como polígono fechado de expressões `(s, d)` nos parâmetros. `s`: através da borda, 0 no centro do rasgo, + para a borda externa do frame. `d`: altura sobre a face do perfil, − para dentro do rasgo. |
| `construir.py` | Roda dentro do Fusion. `construir_tudo()` gera tudo e roda as verificações; as etapas soltas: `estado()`, `preparar()`, `referencia()`, `perfil(nome)`, `arranjar()`, `exportar_stl()`, `frame_ref()`, `pecas()`, `cantos(nomes, etapa)`, `montar()`, `lista()`, `interferencia(face)`, `entre_faces(faces)`, `giro_porta(graus)`, `puxador()`, `salvar()`. Pelo MCP, uma etapa por chamada (o limite de tempo das chamadas trava o Fusion). |
| `../fusion/gerar_v0/` | Script de Fusion que gera tudo do V0: adicione a pasta em *Utilities > Scripts and Add-Ins* e rode. O resumo sai em *Text Commands*. |
| `mapa.py` | Mapa de bordas do V0.2: peças retas (`PECAS`, perfil + comprimento paramétrico), cantos em L (`CANTOS`) e, para cada face, quais peças vão em cada borda e canto e onde fica a linha do canal. Regra de 4 clips e 3 tampas por borda. |
| `verificar_local.py` | Confere os perfis sem o Fusion: encaixe no rasgo Misumi e diferenças em relação ao v11. |
| `verificar_dobradica.py` | Gira a porta em volta do pino e confere os nós contra a lateral e o poste, sem o Fusion. |
| `referencia/` | Seção do perfil Misumi 1515 e posições do frame (CAD V0.2), seções do v11 e as seções lidas de volta do v12. |

## Perfis

| Componente | Onde vai | v11 |
|---|---|---|
| `clip-padrao` | bordas com canal livre | B18 |
| `clip-parede` | topo das laterais (tampa passa `top_overhang` do perfil) | B19 |
| `clip-u` | bordas sem nada atrás (topo da porta e da traseira) | B20 |
| `clip-porta` | base da porta (batente `door_stop_extra` mais para fora) | B21 |
| `clip-porta-lateral` | vertical da porta, lado do puxador | B18 com uma perna quebrada |
| `clip-porta-dobradica` | vertical da porta, lado da dobradiça (aleta em arco no pino) | B18 com uma perna quebrada |
| `tampa-parede` | tampa com parede e cunha de 45° | tampas de 8,3 |
| `tampa-simples` | tampa sem parede (topo das faces) | tampas de 4,0 |

## Fase 2 (peças retas)

- `frame-v0`: o frame do V0.2 (23 perfis Misumi) como referência, posicionado pelas caixas do CAD arredondadas a 0,1 mm.
- `pecas`: um componente por peça reta, com comprimento paramétrico (ex.: `clip_run_h / 3`).
- `face-*`: uma montagem por face (laterais, porta, lados do top hat, tampo) com 108 peças no total.
- Interferência por face: só contato de 0,002 mm entre peças e frame; nenhuma entre faces nos cantos.

## Fase 3 (cantos em L e juntas)

- Cada borda com tampa: canto em L, meio, canto em L. Os cantos (`CANTOS`) têm duas pernas de `cover_corner`; os meios são o resto da borda.
- Canto em L: as pernas são o perfil da tampa estendido 2 mm e cortado na diagonal (meia-esquadria), depois unidas. Tira-se o espaço dos clips de cada borda a partir de onde eles começam (`frame_size` nas horizontais, que terminam nos postes; `clip_end_gap` nas verticais).
- Quando uma perna não tem cunha (`tampa-simples`, topo do corpo), a cunha da outra perna é aparada rente à linha externa; senão a meia-esquadria a levaria 1,5 mm para dentro da cunha vertical do top hat.
- Junta tampa-canto: corte reto até `cover_recess` sobre o acrílico, depois chanfro de 45° nos `joint_scarf` de cima; o meio passa por cima da perna do canto. As verticais do top hat não têm meio nem junta.
- `cantos()` roda em três etapas (`pernas`, `clips`, `juntas`), uma por chamada (cada uma leva de 4 a 20 s). Refazer um canto apaga as ocorrências dele nas faces: rode `montar()` depois.
- Montagem: 132 peças (108 retas + 24 cantos). Interferência por face: só contato de 0,002 mm com o frame. Entre faces (`entre_faces` com as 8): nenhuma.
- Ainda não: nós da dobradiça, puxador, logo (fase 4) e a traseira.

## Fase 4, etapa 1 (entalhe para o dedo)

- Cópia paramétrica do entalhe do v11, numa perna de cada canto (`PEGA` em `mapa.py`): a da borda horizontal. Os cantos do tampo do top hat são todos a mesma peça, então os entalhes giram em volta do tampo, um por borda.
- Lábio: perto do canto, o chanfro externo da tampa é preenchido até o topo (chanfro `grip_lip_chamfer` na aresta), do canto até `grip_lip_margin` depois do rebaixo, terminando em rampa de 45°.
- Rebaixo: `grip_depth` para dentro da face externa, de `grip_from` a `grip_from + grip_length` do canto, com pontas a 45°. O fundo começa no topo da cunha (`wall_width`) e o teto sobe a 45° até o lábio.
- Etapa `pega` de `cantos()` (cerca de 10 s por canto). Ela só acrescenta features ao canto, então as faces não precisam ser remontadas.

## Fase 4, etapa 2 (dobradiças e puxador)

- Dobradiça: um parafuso M3x30 por dobradiça (embaixo e em cima, na borda da porta junto à lateral direita), passando por dois nós. O nó da lateral fica colado no canto (`hinge_side_len`), com rebaixo para a cabeça na ponta do canto, e segura o parafuso (furo `hinge_hole_side`). O nó da porta vem logo depois (`hinge_gap`, `hinge_door_len`), gira livre (furo `hinge_hole_door`) e tem a ponta reforçada a 45° em direção à tampa.
- Os nós são do v11, com uma diferença: cada um é fechado, do lado que gira, por um meio disco concêntrico ao pino, a `hinge_clearance` da face do outro painel (`perfis.NO_LATERAL` / `NO_PORTA`). No v11 as quinas dos nós roçavam 0,12–0,14 mm logo no começo da abertura. `verificar_dobradica.py` gira a porta de 0 a 120° nas três faixas da borda e confirma que o v12 passa limpo.
- Onde fica o nó de um painel, o outro perde a cunha.
- Cantos com dobradiça são variantes (`DOBRADICA` em `mapa.py`) dos cantos comuns, com a etapa `dobradica` de `cantos()`.
- Puxador: aba no meio da tampa vertical do lado do puxador (`tampa-parede-v-puxador`, etapa `puxador()`): o chanfro externo é preenchido e a aba passa `handle_reach` da borda do frame, com rampas nas pontas e um sulco em V no topo, como no v11.
- Gerado no Fusion (v12, salvo): os 4 cantos com dobradiça e a tampa com puxador, montados na porta e na lateral direita. Interferência só com contatos de 0,002 mm com o frame. `giro_porta(graus)` gira a montagem da porta em volta do pino: limpo contra a lateral a 15, 45, 90 e 110°, e as peças do lado da dobradiça passam limpas pelo frame de 5 a 90°.
- As etapas pesadas rodam em partes (`pernaA`/`pernaB`, `clipsA`/`clipsB`, `pega-labio`/`pega-rebaixo`, `dobradica-no`/`-furo`/`-cunha`, `puxador(parte='aba'|'sulco')`): com a timeline em ~700 features, cada uma leva de 3 a 18 s.
- Ainda não: logo e a traseira.

## Traseira (v13)

- Uma moldura só, presa pelos dois postes de trás como as laterais (clips com aleta no rasgo, U sem aleta sobre os drive frames). Topo e base com clips em U sem aleta (não há barra na face: a de baixo e a de cima do frame ficam 37 mm para dentro); em cima a mesma solução do topo da porta, que deixa o vão para o top hat.
- Barra do meio em H (`clip-h`, três por barra, e `tampa-h`, duas metades cuja ponta acompanha o chanfro da tampa vertical): segura a borda de cima da chapa de baixo e a de baixo da chapa de cima. A altura da barra sai de `rear_lower_sheet` (185, a chapa original) e `h_web`.
- Chapas: largura 212 (como a original); a de baixo, 185 (a original serve); a de cima, 51,5 mm (a original de 63 precisa ser cortada).
- 161 peças no total; interferência só com contatos de 0,002 mm com o frame; nenhuma entre faces; a porta gira limpa.

### Revisão b: as duas chapas originais sem corte

As originais (185 + 63) cobrem exatamente os 248 do corpo, de ponta a ponta, sem nada entre elas. Para caberem inteiras:
- **Base** (`clip-u-fora`, `tampa-u-fora-h`, cantos `canto-traseira-base-*`): a parede do U, de `u_outer_wall` 1,5, é a face de fora, e a tampa não tem parede. A borda de baixo desce `rear_drop` = 4,5 abaixo do frame (calculado dos parâmetros). O único obstáculo ali é a entrada de energia da saia, até z 43,8, que fica 0,9 abaixo. O canto tem a perna vertical `rear_drop` mais longa e os clips verticais começam onde começa o poste.
- **Barra em H**: alma `h_web` de 1,0 (era 1,5), a 183 do pé do frame.
- **Topo** (`clip-u-fino`): fundo do U de `u_end_wall_thin` 1,0 (era 1,5). O vão acima, onde fica a chapa do top hat, não muda; a porta continua com o `clip-u` comum.
- Folga de cada chapa na altura: `rear_sheet_play` 0,5. Conferido no Fusion: as duas chapas em cima e embaixo de cada vão, só a pré-carga de 0,1 da nervura; os batentes a 46,2, 231,7, 232,7 e 296,2; nenhuma interferência com o frame nem entre faces.
- O lábio do entalhe do dedo não pode entrar no espaço do clip: depois do entalhe, o canto corta de novo o espaço dos clips daquela perna (nos outros cantos esse corte não encontra nada).
- STLs em `stl/traseira-v13b` (29 peças); a `stl/traseira-v13` ficou marcada como substituída.

### Revisão c: folgas mínimas

- `dovetail_clearance` 0,05 por flanco (era 0, como no v11): só na ranhura da tampa; o macho do clip não muda. A tampa imprime de face para baixo, então os flancos da ranhura saem em degraus de camada. Com camadas de 0,2, cada degrau avança até 0,06 (flanco de 30°) e 0,08 (flanco de 40°) além da linha. Com folga 0 eram esses cantos que raspavam no clip ao deslizar a tampa.
- `panel_preload` 0,05 (era 0,1): a nervura do clip, impressa no plano da mesa, fica exata. Com a folga do rabo-de-andorinha, a tampa ainda pode subir até ~0,07 antes de os flancos encostarem (2 × 0,05 / (tan 30° + tan 40°)), então a chapa fica justa sem forçar a tampa contra os flancos.
- Canto de cima da traseira com nome próprio, `canto-topo-traseira` (com o espaço do `clip-u-fino`). Conferido no Fusion: é idêntico ao `canto-topo-porta` (mesmo volume, diferença booleana 0), porque a perna de cima não tem nada abaixo da chapa, onde os dois U diferem.
- Todo o V0 regerado (162 peças) e conferido: só contatos de 0,002 com o frame, nada entre faces, giro da porta limpo a 15/45/90/110°. STLs da traseira em `stl/traseira-v13c` (a v13b ficou marcada como substituída).

## Em uso

- 2026-10-23: imprimindo ABS no escritório com os painéis do V0 montados, o usuário não sente mais o cheiro de ABS que sentia antes. Impressão subjetiva, não medida, mas a favor da vedação por contato e labirinto, sem espuma.

## Trava deslizante (v1, 2026-10-28; v3 e v4, 2026-10-29, fechada na v4)

- A trava da Trident (v16, ver `gerador/trident/README.md`) com as medidas da V0, a pedido do usuário: mesmo `trava_deslizante()` / `trava_conferir()`, parâmetros `trava_*` em `parametros.py`, variante `folga-005` em `config.py`. Peças no documento `panel-holder-v13`; STL e STEP em `stl/provas-trava-v1`; corte de través comparando as duas em `ideias-trava/trava-v0-v1.png`.
- O pescoço e o toco ficam com 1,1 (3,0 na Trident): o acrílico passa 1,0 por cima do rasgo (batente a -0,5 do centro), e o pescoço só cabe entre a face de dentro da perna de fora (+1,0) e 0,4 de parede do clip antes do batente (`trava_haste` é essa conta). É menos que os ~1,2 da regra de encaixes impressos: a prova diz se aguenta.
- Lingueta de 2,0 (o vão das pernas), reta até 2,2; a quilha fecha a 14° (`trava_quilha_angulo`, novo; 45° na Trident) e chega ao fundo plano do rasgo com 0,6. Bico de 0,6 por lado. Capa de 10 de largura (topo plano da tampa: 12). Toco, encaixe da capa, curso, lingueta de 8, folgas e orelha iguais aos da Trident.
- No gerador, para servir às duas: a lasca do rabo-de-andorinha do clip vai até a parede (na V0 o flanco de fora passa de `slot_opening / 2 + 1`), e o sulco de marca no toco tem no máximo um terço da largura dele.
- Conferido: zero com os dois cursores; deslocado 0,05 de lado o cursor já bate no clip e na tampa; levantado 1 bate no clip; a capa levantada 0,3 bate no toco (0,6 / 1,6 / 1,5 mm³).
- v2 (ideia do usuário): sem a parede de 0,4 do clip entre o rasgo do pescoço e o acrílico, o pescoço e o toco vão a 1,5 (`trava_haste` = do batente até a face de dentro da perna de fora). A parede não fazia falta: o clip só é dividido nos 16,2 mm do rasgo, e fora dele o batente segura a chapa rígida; a borda dela fica `panel_edge_clearance` (1,0) antes do batente e no máximo encosta no pescoço. Ao longo do rasgo o rabo-de-andorinha de dentro, por cima da chapa, fica preso só nas pontas do trecho. Testes zerados; a capa levantada 0,3 bate no toco com 0,9 / 2,2 / 2,1 mm³. `stl/provas-trava-v2` (v1 marcada como substituída), `ideias-trava/trava-v0-v2.png`.
- v3 (2026-10-29, resultado da v2 e ideia do usuário): o cursor de 1,5 não parava em pé na mesa e o brim estragou o rabo-de-andorinha. Da base do clip para cima o pescoço vai a 3,0 (`trava_pescoco_largura`, novo; o toco também), avançando 1,5 para fora por cima da raiz da perna; embaixo, até 0,4 acima da base (`trava_folga_degrau`, novo), continua com `trava_haste` (1,5), porque ali se encontram o degrau da lingueta que prende o cursor (aberta, é a única coisa que segura ele), o batente do acrílico e a raiz da perna. O clip tem o rasgo largo da base para cima e a base aberta nos 3,0 só onde o cursor entra (z 12,9 a 20,2, dentro da janela sem pernas; o gerador recusa se sair dela); a tampa, o rasgo de 3,0. O toco e o encaixe ficam iguais aos da Trident; a capa não mudou. Na mesa, 30,5 mm² contra 14,3 (com a orelha), e o pescoço encosta com 2,2 em vez de 0,7. Testes zerados com os dois cursores; o degrau toca a base só abaixado 0,45; a capa levantada 0,3 bate no toco com 1,8 / 4,5 / 4,3 mm³, como na Trident. `stl/provas-trava-v3` (v2 marcada como substituída), `ideias-trava/trava-v0-v3.png`; os limites do pescoço em `ideias-trava/trava-v0-pescoco-largo.png`.
- v4 (2026-10-29, pedido do usuário: "uma leve folga" no rabo-de-andorinha, do lado da capa): os flancos do encaixe da capa recuam `trava_folga_toco` ao longo do curso, o da frente e o lábio de 45°. O teto continua no topo do toco, o único apoio para baixo, e a capa segue 0,2 acima da tampa. Antes a folga também subia o teto; com 0 isso não aparecia. Três capas, variantes só de capa (`encaixe-005/010/015`, `parte='capa'`, com 1/2/3 sulcos; `trava_conferir` usa o cursor padrão quando a variante não tem cursor). O padrão passou a 0,10 até o resultado. Com a folga f, a capa anda ±f no curso e sobe f; levantada 0,3, ainda bate (1,2 / 0,7 / 0,4 mm³). `stl/provas-trava-v4` (só as capas; o resto é da v3), `ideias-trava/trava-capa-folga.png`.
- Resultado da v4 (2026-10-29, usuário): ficou a capa de 3 sulcos (0,15), com o cursor sem folga (sem marca); o resto da v3 ficou ótimo. `trava_folga_toco` = 0,15 é o padrão nas duas máquinas (o toco e o encaixe são iguais), e as variantes de capa saíram do `config.py`. A `trava-capa` padrão foi refeita nos dois documentos. Sem clique de posição (usuário, 2026-10-29): a pressão da capa já segura a trava firme aberta e travada. Os 3 sulcos de baixo ficam na capa padrão (`trava_capa_sulcos`, novo; usuário: ajudam a segurar e fazem um barulhinho ao deslizar). As marcas de uma variante de capa tomam o lugar deles, então ela precisa de outra contagem. A `trava-capa` é idêntica à `encaixe-015` (volume e faces).

## Logo

- O logo do Voron do v11 (Body249: hexágono com três cortes, 0,4 mm) fica em `referencia/logo_voron.json`. `logo()` cria o componente `logo-voron` e o rebaixo correspondente em `tampa-parede-h-logo`, a tampa do meio da frente do top hat, perto da ponta esquerda, como no v11.
- Os dois STLs saem no mesmo sistema de coordenadas: carregue juntos no fatiador, com o logo como parte em outro filamento (a tampa imprime com a face externa na mesa, então o logo sai nas primeiras camadas).

## Regras

- Modo direto (documento novo): cada expressão é avaliada em Python com os valores do `parametros.py` e a geometria sai sem cotas. Modo paramétrico (documento com timeline, como o v12): as expressões vão para o Fusion como parâmetros de usuário e cada vértice de esboço é cotado; parâmetros que já existem no documento nunca são sobrescritos.
- Componentes gerados são apagados e refeitos pela etapa que os gera. Não edite esses componentes à mão.
- Particularidades do direct modeling tratadas no código: um corte que não encontra material dá erro (vira um aviso, ex.: clips de uma perna onde a meia-esquadria já deixou só a própria perna); `combineFeatures.add` não devolve a feature (o corpo resultante é achado pelo nome); `addExistingComponent` compõe a matriz com a posição da primeira ocorrência do componente (`_place` reaplica a matriz pelo proxy da raiz).
- Pelo MCP, um script que dá erro é desfeito inteiro.
- Direct modeling ignora corpos ocultos em cortes e combinações: o gerador deixa o componente `pecas` visível antes de cortar.
- O frame de referência é feito de corpos (um por perfil), não de ocorrências: em direct modeling as ocorrências de um mesmo componente se deslocaram sozinhas.
- Cores (`cores()`): tampas e cantos lilás, clips azul claro, frame cinza.

## Rodar no Fusion

Tudo de uma vez: o script `gerador/fusion/gerar_v0` (ou `construir.usar('v0'); construir.construir_tudo()`).

Uma etapa pelo script do MCP:

```python
import sys, importlib
sys.path.insert(0, '/Users/victor/Development/voron-panel-holder/gerador')
import construir; importlib.reload(construir)
def run(_context):
    construir.usar('v0')
    construir.cantos(['canto-parede-hv'])
```
