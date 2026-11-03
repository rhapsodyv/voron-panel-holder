"""Edge map of the Voron Trident 350: which pieces go on each panel edge and corner, and where.

Coordinates: centred frame, z = 0 at the frame's foot, rear = +y (referencia/frame_350.json).
Every edge here has a 2020 slot behind it (checked on the reference CAD, referencia/obstaculos_250_*.json).
PECAS / CANTOS / PEGA / faces(v) as in v0/mapa.py; placement is shared (gerador/bordas.py).
Each edge: covers corner + middle + corner (cover_corner legs), clips half + full + full + half.
Bottom edges take a cover without the corner wedge (the skirt sits right below the frame).
Front: two doors hinged on the outer posts (knuckles from the V0: side knuckle on the side panel's
corner, door knuckle on the door's), meeting at the centre with door_gap and no post. Door edges: hinge
side with the arc fin, top and bottom with the solid fin (it slides along the rail slot as the door
turns), centre with the U clip (nothing behind), covers without the wedge at the bottom and centre.
The doors take the stock sheets (door_sheet_width, they meet at the centre): the centre U clip owns
the outer wall (clip-u-centro pieces, profile clip-u-fora, cover without the wall on top) and the hinge side moves its acrylic stop
and dovetail out by door_hinge_shift (clip-porta-dobradica, tampa-parede-dobradica).
The user has no exhaust filter: the stock rear sheet's exhaust notch (top centre) takes the bowden plug
(passa-bowden, construir.passa_bowden), placed in the rear top edge's frame.
"""
from bordas import colocacoes  # noqa: F401  (shared placement)

H1, H2 = 'clip_run_h / 6', 'clip_run_h / 3'
V1, V2 = 'clip_run_v / 6', 'clip_run_v / 3'

D1, D2 = 'door_clip_run / 6', 'door_clip_run / 3'

# pieces of their own (not a profile along an edge), placed by an edge's 'extras'
EXTRAS = ('passa-bowden',)

PECAS = {
    'clip-padrao-h1': ('clip-padrao', H1),
    'clip-padrao-h2': ('clip-padrao', H2),
    'clip-padrao-v1': ('clip-padrao', V1),
    'clip-padrao-v2': ('clip-padrao', V2),
    'tampa-parede-h': ('tampa-parede', 'frame_width - 2 * cover_corner'),
    'tampa-base-h': ('tampa-base', 'frame_width - 2 * cover_corner'),
    'tampa-parede-v': ('tampa-parede', 'body_height - 2 * cover_corner'),
    # doors
    'clip-porta-d1': ('clip-porta', D1),
    'clip-porta-d2': ('clip-porta', D2),
    'clip-porta-dobradica-v1': ('clip-porta-dobradica', V1),
    'clip-porta-dobradica-v2': ('clip-porta-dobradica', V2),
    'clip-u-centro-v1': ('clip-u-fora', V1),
    'clip-u-centro-v2': ('clip-u-fora', V2),
    'tampa-porta-topo-h': ('tampa-parede', 'door_width - 2 * door_corner'),
    'tampa-porta-base-h': ('tampa-base', 'door_width - 2 * door_corner'),
    'tampa-porta-dobradica-v': ('tampa-parede-dobradica', 'body_height - 2 * door_corner'),
    'tampa-porta-centro-v': ('tampa-u-fora', 'body_height - 2 * door_corner'),   # with the handle (construir.puxador)
}

# leg = (cover profile, clip profile cut out, clip offset along s, where the clips start, scarf joint)
_PAREDE_H = ('tampa-parede', 'clip-padrao', '0 mm', 'frame_size', True)     # horizontal edge: clips stop at the posts
_BASE_H = ('tampa-base', 'clip-padrao', '0 mm', 'frame_size', True)         # bottom edge, no wedge
_PAREDE_V = ('tampa-parede', 'clip-padrao', '0 mm', 'clip_end_gap', True)   # vertical edge

# doors: corner legs door_corner long; horizontal leg A, vertical leg B in the -hv orientation
_P_TOPO = ('tampa-parede', 'clip-porta', '0 mm', 'frame_size', True, 'door_corner')
_P_BASE = ('tampa-base', 'clip-porta', '0 mm', 'frame_size', True, 'door_corner')
_P_DOBRA = ('tampa-parede-dobradica', 'clip-porta-dobradica', '0 mm', 'clip_end_gap', True, 'door_corner')
_P_CENTRO = ('tampa-u-fora-canto', 'clip-u-fora', '0 mm', 'clip_end_gap', True, 'door_corner')
_FAMILIAS = {   # corner families of the doors: (horizontal leg, vertical leg)
    'canto-porta-dobra-base': (_P_BASE, _P_DOBRA),
    'canto-porta-dobra-topo': (_P_TOPO, _P_DOBRA),
    'canto-porta-centro-base': (_P_BASE, _P_CENTRO),     # top and bottom clips stop frame_size before the
    'canto-porta-centro-topo': (_P_TOPO, _P_CENTRO),     # centre's U clip, as they stop at a post
}

CANTOS = {
    'canto-parede-hv': (_PAREDE_H, _PAREDE_V),
    'canto-parede-vh': (_PAREDE_V, _PAREDE_H),
    'canto-base-hv': (_BASE_H, _PAREDE_V),
    'canto-base-vh': (_PAREDE_V, _BASE_H),
    'canto-parede-hh': (_PAREDE_H, _PAREDE_H),
}
for _fam, (_h, _v) in _FAMILIAS.items():
    CANTOS[f'{_fam}-hv'] = (_h, _v)
    CANTOS[f'{_fam}-vh'] = (_v, _h)
# finger grip on the horizontal edge's leg (the top's corners are all one part: one grip per edge)
PEGA = {name: ('A' if name.endswith('-hv') or name.endswith('-hh') else 'B') for name in CANTOS}

# hinge corners: variant -> (base corner, leg on the hinge edge, knuckle profile). Each door turns on its
# outer post: the side panel's front corners carry the side knuckles, the door's hinge corners the door's.
DOBRADICA = {
    'canto-lat-dir-dobradica-base': ('canto-base-hv', 'B', 'no-lateral'),
    'canto-lat-dir-dobradica-topo': ('canto-parede-vh', 'A', 'no-lateral'),
    'canto-lat-esq-dobradica-base': ('canto-base-vh', 'A', 'no-lateral'),
    'canto-lat-esq-dobradica-topo': ('canto-parede-hv', 'B', 'no-lateral'),
    'canto-porta-dir-dobradica-base': ('canto-porta-dobra-base-vh', 'A', 'no-porta'),
    'canto-porta-dir-dobradica-topo': ('canto-porta-dobra-topo-hv', 'B', 'no-porta'),
    'canto-porta-esq-dobradica-base': ('canto-porta-dobra-base-hv', 'B', 'no-porta'),
    'canto-porta-esq-dobradica-topo': ('canto-porta-dobra-topo-vh', 'A', 'no-porta'),
}
for _nome, (_base, _, _) in DOBRADICA.items():
    CANTOS[_nome] = CANTOS[_base]
    PEGA[_nome] = PEGA[_base]
# the door hinge families are only used through their hinge variants
for _fam in ('canto-porta-dobra-base', 'canto-porta-dobra-topo'):
    for _o in ('-hv', '-vh'):
        CANTOS.pop(_fam + _o)
        PEGA.pop(_fam + _o)


def _h4(profile):
    return [f'{profile}-h1', f'{profile}-h2', f'{profile}-h2', f'{profile}-h1']


_D4 = ['clip-porta-d1', 'clip-porta-d2', 'clip-porta-d2', 'clip-porta-d1']   # a door's top and bottom


def _v4(profile):
    return [f'{profile}-v1', f'{profile}-v2', f'{profile}-v2', f'{profile}-v1']


def faces(v):
    """v: parameter values in mm. Returns the face list."""
    W, D, fs = v['frame_width'] / 2, v['frame_depth'] / 2, v['frame_size']
    so = fs / 2
    z0 = v['frame_z0']
    z1 = z0 + v['body_height']
    gap = v['clip_end_gap']
    run_h_x = (-(W - fs), W - fs)
    run_h_y = (-(D - fs), D - fs)
    run_v = (z0 + gap, z1 - gap)
    mid_v = (z0 + z1) / 2
    X, Y, Z = (1, 0, 0), (0, 1, 0), (0, 0, 1)
    neg = lambda u: tuple(-c for c in u)   # noqa: E731

    def edge(name, axis, run, point, a, pieces, cover=None, centre=0.0, extras=()):
        return {'nome': name, 'eixo': axis, 'run': run, 'ponto': point, 'a': a, 'pecas': pieces,
                'tampa': cover, 'desloc': '0 mm', 'centro_tampa': centre, 'logo': False, 'extras': extras}

    def corner(kind, point, dir_a, dir_b, variant=None):
        return {'tipo': kind, 'ponto': point, 'a': dir_a, 'b': dir_b, 'variante': variant}

    g = v['door_gap'] / 2
    run_d = (g + fs, W - fs)                         # right door's top and bottom clips (x)
    mid_d = (g + W) / 2

    out = []
    for sx, label in ((1, 'lateral-direita'), (-1, 'lateral-esquerda')):
        x = sx * W
        out.append({'nome': label, 'n': (sx, 0, 0), 'bordas': [
            edge('base', 'Y', run_h_y, (x, 0, z0 + so), neg(Z), _h4('clip-padrao'), 'tampa-base-h'),
            edge('topo', 'Y', run_h_y, (x, 0, z1 - so), Z, _h4('clip-padrao'), 'tampa-parede-h'),
            edge('frente', 'Z', run_v, (x, -(D - so), 0), neg(Y), _v4('clip-padrao'), 'tampa-parede-v', centre=mid_v),
            edge('tras', 'Z', run_v, (x, D - so, 0), Y, _v4('clip-padrao'), 'tampa-parede-v', centre=mid_v),
        ], 'cantos': [corner('canto-base', (x, sy * D, z0), (0, -sy, 0), Z,
                             None if sy == 1 else f"canto-lat-{'dir' if sx == 1 else 'esq'}-dobradica-base") for sy in (1, -1)]
                   + [corner('canto-parede', (x, sy * D, z1), (0, -sy, 0), neg(Z),
                             None if sy == 1 else f"canto-lat-{'dir' if sx == 1 else 'esq'}-dobradica-topo") for sy in (1, -1)]})

    # doors: sx = +1 the right door (hinge on the right front post), -1 the left one
    for sx, label in ((1, 'porta-direita'), (-1, 'porta-esquerda')):
        lado = 'dir' if sx == 1 else 'esq'
        run = run_d if sx == 1 else (-run_d[1], -run_d[0])
        xc = sx * mid_d
        out.append({'nome': label, 'n': neg(Y), 'bordas': [
            edge('base', 'X', run, (0, -D, z0 + so), neg(Z), _D4, 'tampa-porta-base-h', centre=xc),
            edge('topo', 'X', run, (0, -D, z1 - so), Z, _D4, 'tampa-porta-topo-h', centre=xc),
            edge('dobradica', 'Z', run_v, (sx * (W - so), -D, 0), (sx, 0, 0), _v4('clip-porta-dobradica'),
                 'tampa-porta-dobradica-v', centre=mid_v),
            edge('centro', 'Z', run_v, (sx * (g + so), -D, 0), (-sx, 0, 0), _v4('clip-u-centro'), 'tampa-porta-centro-v', centre=mid_v),
        ], 'cantos': [
            corner('canto-porta-dobra-base', (sx * W, -D, z0), (-sx, 0, 0), Z, f'canto-porta-{lado}-dobradica-base'),
            corner('canto-porta-dobra-topo', (sx * W, -D, z1), (-sx, 0, 0), neg(Z), f'canto-porta-{lado}-dobradica-topo'),
            corner('canto-porta-centro-base', (sx * g, -D, z0), (sx, 0, 0), Z),
            corner('canto-porta-centro-topo', (sx * g, -D, z1), (sx, 0, 0), neg(Z)),
        ]})

    out.append({'nome': 'traseira', 'n': Y, 'bordas': [
        edge('base', 'X', run_h_x, (0, D, z0 + so), neg(Z), _h4('clip-padrao'), 'tampa-base-h'),
        edge('topo', 'X', run_h_x, (0, D, z1 - so), Z, _h4('clip-padrao'), 'tampa-parede-h', extras=EXTRAS),
        edge('direita', 'Z', run_v, (W - so, D, 0), X, _v4('clip-padrao'), 'tampa-parede-v', centre=mid_v),
        edge('esquerda', 'Z', run_v, (-(W - so), D, 0), neg(X), _v4('clip-padrao'), 'tampa-parede-v', centre=mid_v),
    ], 'cantos': [corner('canto-base', (sx * W, D, z0), (-sx, 0, 0), Z) for sx in (1, -1)]
               + [corner('canto-parede', (sx * W, D, z1), (-sx, 0, 0), neg(Z)) for sx in (1, -1)]})

    out.append({'nome': 'topo', 'n': Z, 'bordas': [
        edge('direita', 'Y', run_h_y, (W - so, 0, z1), X, _h4('clip-padrao'), 'tampa-parede-h'),
        edge('esquerda', 'Y', run_h_y, (-(W - so), 0, z1), neg(X), _h4('clip-padrao'), 'tampa-parede-h'),
        edge('tras', 'X', run_h_x, (0, D - so, z1), Y, _h4('clip-padrao'), 'tampa-parede-h'),
        edge('frente', 'X', run_h_x, (0, -(D - so), z1), neg(Y), _h4('clip-padrao'), 'tampa-parede-h'),
    ], 'cantos': [corner('canto-parede-hh', (sx * W, sy * D, z1), (-sx, 0, 0), (0, -sy, 0)) for sx in (1, -1) for sy in (1, -1)]})
    for f in out:
        f['dobradica'] = DOBRADICA
    return out
