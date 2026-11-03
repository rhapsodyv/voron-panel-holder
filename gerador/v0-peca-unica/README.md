# V0 peça única com trava

A V0 com o clip e a tampa numa peça só e a trava v8 da Trident (`gerador/trident-peca-unica`), feita só no build123d (2026-11-01). O usuário perguntou: "o que acha de gerar agora uma copia desse novo projeto em build123d para a v0?". Os arquivos daqui herdam os da V0 com trava (`gerador/v0-trava`) e só dizem o que muda. `referencia` é um link para a da V0.

```bash
.venv-b3d/bin/python gerador/peca_unica_v0_b3d.py kit-v1
```

O comando refaz o kit de prova em `stl/provas-peca-unica-trava-v1`: a peça de 45 mm com a perna lisa, os três cursores de `config.GANCHO_CURSOR` e a capa. Ele também confere tudo (`conferencia.json`). O desenho da ideia é `ideias-trava/v0-peca-unica-trava-v8.png`.

A trava v8 no rasgo 1515 (abertura 3,0, aba 1,0 com raio 0,25, o acrílico até o batente em −0,5):
- **Perna e lingueta:** a perna lisa tem 1,2 (`peca_unica_perna`) e a lingueta 1,7. O gancho é de 1,0 embaixo da aba de fora, e a cavidade vai até 2,85.
- **Pescoço:** aberto, o cursor fica solto 1,2 para dentro, então o pescoço fica fora do acrílico. Travado, vai de 0,7 a 3,7; aberto, fica rente ao batente.
- **Degrau embaixo do acrílico:** ali o cursor alarga para 3,9 e une a lingueta ao pescoço.
  - O ombro fica `trava_ombro_folga` acima do frame depois de descer.
  - O topo fica `trava_degrau_folga` abaixo da base.
  - A base embaixo do acrílico fica aberta só na janela.
- **Quilha:** tem o fundo plano `trava_fundo_folga` acima do fundo do rasgo e um chanfro a 45° pela corda do arredondado.
- **Toco e capa:** os finais da Trident (os dois flancos a 45° e retos, toco de 3,7), com a capa da largura da V0 (10). Travada, a capa fica rente à borda do topo plano.
- **Cursor e capa:** são construídos aqui, a partir do `construir.trava_deslizante` do Fusion.
- **Variantes:** os cursores variam o aperto: 0,1, 0,2 e 0,3, com 1, 2 e 3 sulcos no toco.

O kit de prova v1 foi impresso na V0 em 2026-11-01 e funcionou. O usuário: "a trava da v0 funcionou, até com o cursor com 1 sulco!". As faces usam o `gancho-010` (`config.CURSOR_FACES`). As peças da V0 cabem na mesa dela: cantos de 77, meios de ~82 e ~103.

## Lado do top hat, v1 (2026-11-01)

O usuário: "pode gerar a parte de lateral do top hat da v0, pra eu testar".

```bash
.venv-b3d/bin/python gerador/peca_unica_v0_b3d.py tophat-lateral
```

O comando constrói, confere e exporta um lado do top hat (`tophat-direita`; os quatro são as mesmas peças) em `stl/peca-unica-tophat-lateral-v1`. As conferências vão para `conferencia-tophat-lateral.json`.

- **Mapa (`mapa.py`):** é o da V0 com a divisão da Trident em peça única: canto, meio e canto. O meio de cima tem a trava no meio.
- **Verticais do top hat:** não têm meio, porque o canto cobre os 80. Nada seguraria essa perna, então ela leva a própria trava no meio do poste, descendo, onde a trava da V0 estava (`mapa.CANTOS_TRAVA`).
  - O `-hv` é construído com a trava na perna B. Nele, descer é destro no referencial da trava.
  - O `-vh` é o espelho dele em x = y, com o cursor e a capa espelhados.
  - São 3 travas por lado.
- **Cantos:**
  - a perna horizontal tem a aleta lisa das portas a partir de `peca_unica_aleta_poste` (0,5) depois do poste;
  - a perna vertical tem a perna lisa da trava, a janela, a rampa, os rasgos e o círculo (`_trava`, a mesma do corpo de prova);
  - o entalhe para o dedo fica na perna horizontal, e o chanfro de mesa vai na face de fora e no rasgo.
- **Conferências (`conferir_face`):**
  - frame (perfis onde o mapa põe os rasgos, porque o CAD tem o top hat 0,05 acima), no lugar e entrando reto;
  - entre as peças, contra o acrílico nos batentes, contra as cunhas vizinhas e contra as peças dos outros lados do top hat;
  - cada trava no referencial dela (`conferir` do kit).
  - Tudo deu zero, menos o aperto do gancho (0,123).
- **Embaixo:** a perna vertical termina 0,3 acima da tampa do topo do corpo, como na V0.
- **Falta:** o logo da frente (no meio de cima do `tophat-frente`), o tampo e as faces do corpo.

## Lado do top hat, v2 (2026-11-02)

São as peças da v1 com duas mudanças gerais que o usuário pediu. Elas também valem para a Trident peça única (`peca_unica_b3d.py`).
- **Vão do acrílico 3,0** (`peca_unica_vao`, era 2,8). O usuário: "adiciona pelo menos mais 0.1mm de folga".
  - Deitada, o vão sai em camadas de 0,2. Com 3,0, o teto dele fica a 7,0 mm da mesa, numa troca de camada.
  - A base embaixo do acrílico fica com 1,3.
- **Cursor e capa:** continuam os do kit v1. A conferência os constrói com o vão de 2,8 (`config.KIT_VAO`), como foram impressos.
- **Lâmina do suporte com 2 camadas** (`suporte_lamina_topo` 0,4). No último `suporte_lamina_contato` (1 mm) antes da peça, ela fica com 1 camada. O usuário: "tem que fazer essa bridge ter 2 camadas, porem 1 camada só onde encosta na nossa peça".
- **Saída:**
  - as peças em `stl/peca-unica-tophat-lateral-v2`;
  - as conferências em `conferencia-tophat-lateral-v2.json`: tudo zero, menos o aperto do gancho (0,123);
  - no G-code, a ponte (7,2 mm) sai numa camada só, e a segunda camada (7,4) fica a 1,0 mm da base.

Chanfro de mesa conferido (2026-11-02, o do `clips_b3d.py`, agora em `peca_unica_b3d.chanfro_mesa`): refeitas, as peças das faces e a capa saem iguais. O cursor ganha o chanfro de 0,4 numa aresta da ponta de trás, na face de fora da lingueta (0,16 mm³), que antes falhava. As faces continuam copiando o cursor e a capa do kit v1 impresso.

Configurador web (2026-11-02): `peca_unica_v0_b3d.valores()` aceita parâmetros mudados (`MUDANCAS`, que o `web/motor.py` preenche; vazio, nada muda). O mapa põe o meio também no lugar da tampa do logo (`tampa-parede-h-logo`), então a frente do top hat sai com as mesmas peças dos outros lados, ainda sem o logo.
