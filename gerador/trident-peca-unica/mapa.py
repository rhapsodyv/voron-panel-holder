"""Edge map of the one-piece Trident with the lock (pieces built by gerador/peca_unica_b3d.py): the Trident's faces,
corners and lengths (gerador/trident/mapa.py), each edge's covers made one-piece, split A (the user's choice,
2026-11-01): the corners where the Trident's corners are, with no hook and no lock; the middle where its middle cover
is, with the hook and the lock at its middle. The doors keep the Trident with the lock's separate clips (built there).
"""
import herdar
from bordas import colocacoes  # noqa: F401  (shared placement)

_tri = herdar.de('trident', 'mapa')
herdar.copiar(_tri, globals())

# the Trident's middle cover -> the one-piece middle in its place
MEIOS = {'tampa-parede-h': 'meio-parede-h', 'tampa-base-h': 'meio-base-h', 'tampa-parede-v': 'meio-parede-v'}
# faces built so far: the first big test (2026-11-01), then the top (the user: "gera os stls do topo da trident também")
FACES = ('lateral-esquerda', 'topo')

# The middles keep the Trident covers' 45 deg corner wedge (none on the bottom edges, as tampa-base). A middle goes in
# moved out by the hook and its clearance (1.1) and slides back; at a frame corner that is into the other face's
# side, where that face's cover has its wedge (1.5 past the corner, the two meeting on the diagonal), so with that
# face already on, the middle going in meets it. The user (2026-11-01): "a cunha não vai ser problema ali não, pode
# manter ela". peca_unica_b3d.conferir reports it (cunhas_entrando). Edges with another face past their corner:
BORDAS_SEM_VIZINHO = ('base',)

# The lock slides +z in a middle's frame (s, d, a x n, bordas.colocacoes). On a vertical edge it slides down, so
# gravity keeps it locked: where +z points up the middle is mirrored (-espelho), and so are its slider and cap.
