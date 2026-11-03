"""Edge map of the V0 with the lock: the V0's (gerador/v0/mapa.py) plus the panel locks (2026-10-29).

Where (user, 2026-10-29: one lock in the middle of each edge, none at the corners):
  laterais        the middle of each of the four edges
  traseira        the middle of each vertical (its top and bottom are U clips, without legs)
  top hat sides   the middle of each vertical, on the corner's vertical leg (the corner covers the 80)
  tampo           the middle of each edge
  porta           none
How a lock is placed and built: gerador/travas.py. Here the top hat's verticals are one clip each, so the
cap's run is centred on them, and the lock's cover is the corner (canto-tophat-trava-hv/vh); the sides' top
edge has its cover top_overhang further out, so its cap is trava-capa-topo.
"""
import herdar
import travas

_v0 = herdar.de('v0', 'mapa')
herdar.copiar(_v0, globals())

# face -> edges with a lock
TRAVAS = {
    'lateral-direita': ('base', 'topo', 'frente', 'tras'),
    'lateral-esquerda': ('base', 'topo', 'frente', 'tras'),
    'traseira': ('direita', 'esquerda'),
    'tophat-frente': ('canto+', 'canto-'),
    'tophat-tras': ('canto+', 'canto-'),
    'tophat-direita': ('canto+', 'canto-'),
    'tophat-esquerda': ('canto+', 'canto-'),
    'tophat-tampo': ('direita', 'esquerda', 'tras', 'frente'),
}

PECAS = dict(_v0.PECAS)
for _n in ('clip-padrao-h2', 'clip-parede-h2', 'tampa-parede-h', 'tampa-simples-h'):
    PECAS[f'{_n}-trava'] = _v0.PECAS[_n]
for _n in ('clip-padrao-v2', 'clip-padrao-th', 'tampa-parede-v'):
    PECAS[f'{_n}-trava'] = PECAS[f'{_n}-trava-espelho'] = _v0.PECAS[_n]
CANTOS, PEGA = dict(_v0.CANTOS), dict(_v0.PEGA)
for _k in ('hv', 'vh'):
    CANTOS[f'canto-tophat-trava-{_k}'] = _v0.CANTOS[f'canto-tophat-{_k}']
    PEGA[f'canto-tophat-trava-{_k}'] = _v0.PEGA[f'canto-tophat-{_k}']


def faces(v):
    """The V0's faces with the lock pieces in place of the plain ones (travas.aplicar); the top hat sides'
    corners carry their locks."""
    out = travas.aplicar(_v0.faces(v), v, TRAVAS, PECAS)
    for face in out:
        if face['nome'] in TRAVAS and face['nome'].startswith('tophat-') and face['nome'] != 'tophat-tampo':
            for c in face['cantos']:
                c['tipo'] = 'canto-tophat-trava'
    return out


colocacoes = travas.colocacoes


def trava_pecas(v):
    """Each lock piece's lock frame in its own coordinates (travas.quadros), for construir.trava_pecas."""
    return travas.quadros(v, faces(v), PECAS, CANTOS)
