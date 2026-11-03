"""Edge map of the Trident with the lock: the Trident's (gerador/trident/mapa.py) plus the panel locks
(2026-10-30), placed as on the V0 (gerador/v0-trava): one lock in the middle of each edge, none on the doors.
  laterais   the middle of each of the four edges
  traseira   the middle of each of the four edges (every edge has a slot behind it, unlike the V0's rear)
  topo       the middle of each edge
  portas     none (hinged; their clips are the arc fin, the solid fin and the centre U)
How a lock is placed and built: gerador/travas.py. Every edge's middle is a clip joint here (horizontal
clips and verticals both split half, full, full, half), and every lock sits on a straight middle cover.
"""
import herdar
import travas

_tri = herdar.de('trident', 'mapa')
herdar.copiar(_tri, globals())

# face -> edges with a lock
TRAVAS = {
    'lateral-direita': ('base', 'topo', 'frente', 'tras'),
    'lateral-esquerda': ('base', 'topo', 'frente', 'tras'),
    'traseira': ('base', 'topo', 'direita', 'esquerda'),
    'topo': ('direita', 'esquerda', 'tras', 'frente'),
}

PECAS = dict(_tri.PECAS)
for _n in ('clip-padrao-h2', 'tampa-parede-h', 'tampa-base-h'):
    PECAS[f'{_n}-trava'] = _tri.PECAS[_n]
for _n in ('clip-padrao-v2', 'tampa-parede-v'):
    PECAS[f'{_n}-trava'] = PECAS[f'{_n}-trava-espelho'] = _tri.PECAS[_n]


def faces(v):
    """The Trident's faces with the lock pieces in place of the plain ones (travas.aplicar)."""
    return travas.aplicar(_tri.faces(v), v, TRAVAS, PECAS)


colocacoes = travas.colocacoes


def trava_pecas(v):
    """Each lock piece's lock frame in its own coordinates (travas.quadros), for construir.trava_pecas."""
    return travas.quadros(v, faces(v), PECAS, CANTOS)
