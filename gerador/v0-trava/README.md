# V0 com trava (panel-holder-trava-v1)

A V0 (`gerador/v0`) com a trava deslizante nos painéis, num documento próprio: o `panel-holder-trava-v1` (projeto Voron, pasta Panel-Holder) é uma cópia da `panel-holder-v13`, que ficou como estava. Os arquivos daqui herdam os da V0 (`herdar.py`) e só dizem o que muda.

## v1 (2026-10-29/30): 22 travas no meio das bordas

Onde (usuário: uma trava no meio de cada borda, nenhuma nos cantos):

| Face | Travas | Onde |
|---|---|---|
| laterais | 4 cada | meio de cada borda |
| traseira | 2 | meio de cada vertical (em cima e embaixo são clips em U, sem pernas) |
| top hat, 4 lados | 2 cada | meio de cada vertical de 80, na perna vertical do canto |
| tampo do top hat | 4 | meio de cada borda |
| porta | 0 | |

- O meio de uma borda tem uma emenda de clips (horizontais: no meio, a 115 do canto; verticais: a 116,3 acima do frame). A trava fica ao lado dela, com o trecho de clip que ela muda (`geometria_trava` `trecho`: 6,2 a 32 no referencial do corpo de prova) a `trava_margem_emenda` (3) da emenda.
- Bordas horizontais: no clip inteiro cujo z corre para o meio; desliza para o meio. Capa de 81,4 a 120,6 do canto (aberta a 81,4–110,6), círculo a 115,6.
- Verticais das laterais e da traseira: no clip de cima (116,3–198); trava descendo, para o peso segurar travada. Capa de 111,4 a 150,6 acima do frame (aberta a 121,4–150,6), círculo a 116,4.
- Top hat: o curso inteiro da capa centrado na vertical; trava descendo. Capa de 20,4 a 59,6 do canto de cima.
- Uma trava cujo referencial (s para fora, d para fora da face, sentido de travar) é canhoto leva peças espelhadas (`-espelho`: clip, tampa, cursor e capa). É o caso de metade das verticais (descer é o mesmo sentido nas duas laterais, que são o espelho uma da outra).
- Borda de cima das laterais: a tampa-simples fica `top_overhang` (3) para fora do rasgo, então a capa é a `trava-capa-topo` (`trava_capa_desloc`, variante `topo`): centrada no topo plano dela, com o encaixe 3 mm mais comprido para o lado aberto. No `clip-parede`, o rabo-de-andorinha sai inteiro sobre o rasgo (o flanco de dentro viraria uma lasca solta).
- Os clips com trava mantêm a farpa padrão fora da janela (no corpo de prova a farpa era só onde a lingueta fica travada).

Conferido no Fusion: as peças-base são iguais às da V0 (volume e faces); cada tampa e canto perde 66,2 mm³ (rasgo e círculo; tampa-simples 66,9), cada clip padrão 427,8 mm³ (clip-parede 546,3); `interferencia` em todas as faces só com contatos de 0,002 e a orelha do cursor contra a capa; `entre_faces` de todas as faces: nenhuma; `giro_porta`: limpa até 180°; a 190° as dobradiças já se encostam (0,12), e a capa da vertical da frente da lateral direita só seria tocada depois de 200°.

STLs (só as peças da trava): `stl/trava-v1`, com o LEIA-ME de montagem.
