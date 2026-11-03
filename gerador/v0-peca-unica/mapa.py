"""Edge map of the V0 in one piece with the lock (pieces built by gerador/peca_unica_v0_b3d.py): the V0's faces, corners
and lengths (gerador/v0/mapa.py), each edge's covers made one-piece as on the one-piece Trident
(gerador/trident-peca-unica/mapa.py): a corner where the V0 has its corner, a middle where it has its middle cover, with
the lock at the middle's middle; the middle's ends pass over the corners' legs on the 45 deg scarf.

The top hat's sides (2026-11-01, the user: "pode gerar a parte de lateral do top hat da v0, pra eu testar"): their
verticals have no middle (the corner's vertical leg covers the 80), so no middle's scarf holds that leg down. It carries a
lock of its own at the post's middle, sliding down, where the V0 with the lock has it (gerador/v0-trava: "meio de cada
vertical de 80, na perna vertical do canto"). Three locks a side: the top middle's and the two corners'.
"""
import herdar

_v0 = herdar.de('v0', 'mapa')
herdar.copiar(_v0, globals())

# the V0's middle cover -> the one-piece middle in its place
MEIOS = {'tampa-parede-h': 'meio-parede-h', 'tampa-parede-h-logo': 'meio-parede-h'}   # the front's: no logo yet
# corners with the lock on their leg without a middle, built as the -hv: the vertical is its leg B, where sliding down
# is right-handed in the lock's frame. The -vh is its mirror across x = y, with the mirrored slider and cap
CANTOS_TRAVA = {'canto-tophat-hv': 'canto-tophat-vh'}
# export name -> the face built: the four top hat sides are the same pieces (in the V0 the front's middle also carries the
# Voron logo, not ported here)
FACES = {'tophat-lateral': 'tophat-direita'}
