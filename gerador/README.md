# Gerador do panel holder

Gera no Fusion (projeto Voron, pasta Panel-Holder) o panel holder de cada impressora a partir dos perfis e do mapa de bordas em Python. Documentos em direct modeling: os valores vivem em Python; para mudar uma folga, edite e gere de novo.

```
gerador/
  construir.py     comum: todas as etapas (peças, cantos, faces, verificações, exportação)
  perfis.py        comum: perfis como polígonos de expressões nos parâmetros
  bordas.py        comum: onde vai cada peça de uma borda (clips em 4, tampa em 3, variantes de dobradiça)
  geometria_trava.py  comum: a geometria da trava deslizante, sem Fusion (corpo de prova, peças e mapas)
  herdar.py        comum: uma máquina feita sobre outra herda config, parametros e mapa dela
  verificar_dobradica.py  comum: giro da porta em 2D, fora do Fusion (python3 verificar_dobradica.py v0|trident)
  fusion/          scripts do Fusion, um por máquina (gerar_v0, gerar_trident)
  v0/              Voron V0.2 (frame 1515): config.py, parametros.py, mapa.py, referencia/, verificadores locais
  v0-trava/        a V0 com as travas nos painéis (documento panel-holder-trava-v1); só diz o que muda
  trident/         Voron Trident 350 (frame 2020): config.py, parametros.py, mapa.py, referencia/
  trident-trava/   a Trident com as travas nos painéis (documento trident-panel-holder-trava-v1)
  trident-peca-unica/  a Trident em peça única com trava, feita no build123d (peca_unica_b3d.py)
  v0-peca-unica/   a V0 em peça única com a trava v8, feita no build123d (peca_unica_v0_b3d.py)
  travas.py        comum: onde vai a trava nas bordas e o referencial dela em cada peça (mapas com trava)
  clips_b3d.py     os projetos com clipes (v0, v0-trava, trident, trident-trava) no build123d, sem o Fusion
```

O configurador web (site estático que roda o `clips_b3d.py` no navegador) fica em `web/`; ver `web/README.md`.

- `config.py`: documento do Fusion, arquivos de referência, nome do componente do frame, corpos de prova.
- `parametros.py`: os valores (geometria do frame e do rasgo, escolhas de projeto, folgas de impressão).
- `mapa.py`: faces, bordas, peças e cantos daquela máquina; `EXTRAS`, peças avulsas montadas no referencial de uma borda (a lista `extras` da borda), como o passa-bowden da Trident.

## Rodar no Fusion

Tudo de uma vez: adicione `fusion/gerar_v0` ou `fusion/gerar_trident` em *Utilities > Scripts and Add-Ins* e rode. O resumo sai em *Text Commands*.

Uma etapa pelo script do MCP (uma etapa por chamada: o limite de tempo das chamadas trava o Fusion):

```python
import sys, importlib
sys.path.insert(0, '/Users/victor/Development/voron-panel-holder/gerador')
import construir; importlib.reload(construir)
def run(_context):
    construir.usar('trident')      # ou 'v0' (o padrão)
    construir.perfil('clip-padrao')
```

## Regras

- Componentes gerados são apagados e refeitos pela etapa que os gera. Não edite esses componentes à mão.
- Particularidades do direct modeling tratadas no código: corte que não encontra material dá erro (vira aviso); `combineFeatures.add` não devolve a feature; `addExistingComponent` compõe a matriz com a primeira ocorrência (`_place` reaplica pelo proxy da raiz); corpos ocultos ficam de fora de cortes (o componente `pecas` fica visível); ocorrências de um mesmo componente podem se deslocar (o frame de referência é feito de corpos, e `montar` confere a posição de cada ocorrência contra o mapa e corrige a deriva). As peças e os cantos ficam na origem, dentro de `pecas`.
- Pelo MCP, um script que dá erro é desfeito inteiro.
- Clips com aleta bipartida (`perfis.SPLIT_FIN`) podem ter a farpa só em trechos: `fin_anchor_length` > 0 (com `fin_anchor_gap`) corta a farpa entre eles, nas peças e nos corpos de prova. Variantes de corpo de prova (`config.VARIANTES`) reavaliam a tabela de parâmetros inteira, inclusive `test_length`.
- Parede mínima: `perfis.leg_min_wall` mede a parede das pernas da aleta de lado (perto da ponta a perna é inclinada, e a parede fica mais fina que a largura na horizontal); `perfil()` e `pecas()` recusam um clip abaixo de `fin_min_wall` (0,4 por padrão), que o fatiador apagaria.
- Corpos de prova de teste levam marcas: `config.MARCAS` {nome: n} corta n entalhes no topo da peça (o rabo-de-andorinha de um clip), perto de uma ponta, para distinguir as variantes impressas.
- Perfis de U: `clip-u` (comum), `clip-u-fora` (a parede do U é a face de fora: centro das portas da Trident, base da traseira do V0) com `tampa-u-fora`/`tampa-u-fora-canto`, e `clip-u-fino` (fundo mais fino: topo da traseira do V0).
- `usar(maquina)` recarrega `bordas` e `geometria_trava`; um reload do `construir` volta ao `v0`.
- Trava nas peças (`v0-trava`, `trident-trava`, com `travas.py`): o `mapa.py` põe as peças `-trava` nas bordas, e `mapa.trava_pecas(v)` dá, para cada uma, o referencial da trava nas coordenadas da peça (conferido igual em todo lugar onde ela vai). A ordem é `pecas([...])` e `cantos([...])` (as peças sem trava), `trava_pecas()` (corta a trava; recusa uma peça já cortada), `trava_deslizante(parte='capa', variante='topo')`, `trava_espelho()` (cursor e capa espelhados) e `montar()`, que põe cursor, capa e disco de cada trava, abertos. `interferencia` trata a orelha do cursor contra a capa como pré-carga (ela sai antes de montar).
- Verificações: `interferencia(face)`, `entre_faces(faces)`, `giro_porta(graus, face=...)`, `lista()`; `exportar_stl(nomes, pasta)` grava em `stl/`; `exportar_faces(faces, pasta)` exporta as peças das faces montadas. Cada arquivo leva a quantidade no nome (`clip-h-3x.stl`), e `quantidades.json` lista as mesmas contagens.
- Cores (`cores()`): tampas e cantos lilás, clips azul claro, frame cinza.
- Chanfro de mesa (`chanfro_mesa()`, `bed_chamfer`): chanfra as arestas que encostam na mesa, contra o pé de elefante. Nos clips são as duas pontas, menos a aleta; nas tampas e nos cantos, o contorno da face de fora. Fica sem a aresta cuja face vizinha já é a 45° ou mais deitada, ou é mais baixa que o chanfro. Roda depois de `pecas`, `puxador`, `logo` e `cantos`, e marca o componente para não repetir.

O histórico do V0 (fases, decisões, verificações) está em `v0/README.md`; o da V0 com trava, em `v0-trava/README.md`; o da Trident, em `trident/README.md`; o da Trident com trava, em `trident-trava/README.md`.

## No build123d, sem o Fusion (`clips_b3d.py`, 2026-11-02)

O usuário pediu: "passa os projetos com clipes para o build123d? a versão com e sem travas, v0 e trident". O `clips_b3d.py` refaz no build123d cada etapa do `construir.py` das quatro máquinas com clipes (`v0`, `v0-trava`, `trident`, `trident-trava`). Ele lê os mesmos `config.py`, `parametros.py`, `mapa.py`, `perfis.py`, `bordas.py`, `travas.py` e `geometria_trava.py`. As peças saem nos mesmos referenciais do Fusion, então cada STL pode substituir o do Fusion.

```bash
.venv-b3d/bin/python gerador/clips_b3d.py trident-trava face lateral-direita     # constrói, confere e exporta uma face
.venv-b3d/bin/python gerador/clips_b3d.py v0 conferir                            # as conferências do construir_tudo
.venv-b3d/bin/python gerador/clips_b3d.py trident comparar stl/trident-porta-direita-v2   # contra uma exportação do Fusion
.venv-b3d/bin/python gerador/clips_b3d.py v0-trava pecas trava-cursor tampa-parede-h-trava
```

Os comandos:
- `face` exporta em `stl/<prefixo><face>-b3d-v<n>`, sempre numa pasta nova. Os nomes e as contagens são os do `exportar_faces` (`clip-padrao-h1-8x.stl`, `quantidades.json`).
- `--mudar nome=expressão` troca um parâmetro só naquela rodada, por exemplo para refazer uma exportação antiga: `--mudar "fin_inset=0.05 mm"` refaz o topo v3 da Trident com trava.
- `conferir` grava `conferencia-b3d.json` na pasta da máquina.

O que foi portado, na ordem do `construir_tudo` e dos READMEs das máquinas com trava:
- peças retas (com as farpas por trechos e a recusa de parede fina) e a tampa-h;
- puxador, logo e o rebaixo dele, e o passa-bowden;
- cantos: pernas, clips, miolo, emendas, entalhe do dedo (com os clips da perna cortados de novo) e dobradiças;
- os cortes da trava nas peças, o cursor, a capa (e a `trava-capa-topo` da V0), o disco e os espelhos;
- o chanfro de mesa;
- a montagem das faces (`bordas.colocacoes` e `travas.colocacoes`), o frame (`frame_ref`, com o mesmo arredondamento) e as conferências: `interferencia`, `entre_faces` e `giro_porta`, com as mesmas pré-cargas.

Não foram portados: os corpos de prova (`perfil`, `VARIANTES`, `MARCAS`, `arranjar`), o clip e a tampa de prova da trava, `trava_conferir`, `cores`, o cursor com dentes e a peça única (que já está em `peca_unica_b3d.py`).

### Diferenças do OpenCascade que o port trata

- **`bd.chamfer(arestas)` chanfrava a peça errada.** Ele chanfra o `topo_parent` das arestas, que pode ser um estado antigo da peça. A tampa do puxador da Trident voltava sem o puxador. Agora o chanfro é chamado na própria peça (`peca.chamfer`), e cada resultado é conferido: o volume tirado tem que caber num chanfro daquelas arestas, e a caixa da peça não pode mudar.
- **Aresta que o OpenCascade recusa.** Na ponta do nó da dobradiça da lateral, ao lado do entalhe de 0,15, o chanfro é cortado à mão, como prisma (`_chanfro_manual`). Cada ponta do prisma é limitada pelos planos das faces que se encontram ali, do lado da aresta, e isso reproduz o Fusion.
- **Arestas uma a uma.** Quando o chanfro de tudo de uma vez falha, as arestas são refeitas uma a uma. Uma aresta encurtada pelo chanfro da vizinha é reencontrada pela reta dela, e o limite de volume usa o comprimento original.
- **Face vizinha mais baixa que o chanfro.** Ela é medida embaixo do meio da aresta, não pelos vértices da face inteira. No OpenCascade, a parede do entalhe de 0,15 se funde com a borda do lábio do entalhe do dedo e desce até 0,4 numa ponta.
- **Volume da B-rep errado.** O chanfro sobre a crista côncava da capa (segmentos de 0,25 contra um chanfro de 0,4) sai certo na malha, igual ao Fusion, mas com o volume da B-rep 1,5 mm³ errado e booleanas que falham. Nesses casos o sólido é refeito pela própria malha (`_sadio`), já que todas as faces são planas.

### Conferido contra o Fusion (2026-11-02)

`comparar` transforma cada STL do Fusion em sólido (os triângulos coplanares juntados) e faz booleanas com tolerância nos dois sentidos. Se a booleana falha (malha contra malha, nas capas refeitas), ele compara cortes em 75 planos.

Comparado contra:
- **Trident:** `trident-lateral-direita-v5`, `-esquerda-v4`, `trident-porta-direita-v2` e `-esquerda-v2`.
- **Trident com trava:** `trident-trava-lateral-esquerda-v1` e `trident-trava-topo-v3` (com `--mudar "fin_inset=0.05 mm"`).
- **V0:** `traseira-v13c` e `porta-clips-v13c`.
- **V0 com trava:** `trava-v1`.
- **Do Fusion aberto, numa pasta temporária, as peças que nunca tinham sido exportadas:**
  - do `panel-holder-trava-v1`: os 22 componentes restantes da V0 (cantos com entalhe e dobradiça, logo, tampa do logo, puxador, clips padrão e de parede) e o frame;
  - da Trident: o passa-bowden, o canto do topo com miolo e o frame.

Resultado: tudo igual. Só sobram:
- a facetação dos furos redondos no STL (furos da dobradiça, passa-bowden e círculo da trava), até 0,9 mm³ em fatias de 0,006 mm;
- as capas, que nos cortes diferem no máximo 0,0007 mm².

Os frames batem membro a membro. A `tophat-lateral-v12` não bate porque é anterior à revisão c, que mudou as folgas.

`conferir` deu o mesmo que os READMEs registram do Fusion (detalhes em `<máquina>/conferencia-b3d.json`):

| Máquina | Cada face com o frame e entre as peças | Entre faces e portas |
|---|---|---|
| V0 | só contatos de 0,002 | nada; porta livre a 15, 45, 90 e 110° |
| V0 com trava | contatos de 0,002 e a orelha do cursor na capa (0,2) | o mesmo |
| Trident | só o aperto de 0,06 da farpa na aba e a nervura no passa-bowden | o mesmo, nas duas portas |
| Trident com trava | a orelha do cursor e a nervura (com `fin_inset` 0,07 a perna não aperta mais a aba) | o mesmo |

Tempos: 27 s (V0), 50 s (V0 com trava), 43 s (Trident) e 61 s (Trident com trava).

Peça única:
- **O chanfro antigo** (`bd.chamfer`) foi conferido e chanfrou as peças certas. Mas ele deixava sem chanfro as arestas que o OpenCascade recusava: a ponta do nó da dobradiça nos cantos da lateral da Trident (0,7 mm³, na `trident-peca-unica-lateral-esquerda-v1`) e uma aresta da ponta de trás do cursor da V0 (0,16 mm³, na face de fora da lingueta).
- **O chanfro conferido** passou do `clips_b3d.py` para o `peca_unica_b3d.py` (`chanfro_mesa`, `_chanfro_manual`, `_sadio`, `stl_solido`), a pedido do usuário. O `clips_b3d.py` usa o de lá.
- **Refeitas com os dois chanfros**, todas as outras peças únicas saem iguais: as faces da Trident e da V0, a peça do kit v8 e a capa da V0. As próximas exportações saem com essas duas arestas chanfradas. As exportações da V0 copiam o cursor e a capa do kit impresso, então só um kit refeito teria o cursor novo.
