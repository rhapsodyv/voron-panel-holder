"""Edge map of the Voron V0.2: which pieces go on each panel edge and corner, and where.

PECAS   straight pieces: (profile from perfis.PROFILES, length expression). Cover middles carry a
        scarf joint at both ends: they are extruded joint_scarf longer on each side and the extra
        is cut at 45° (only the top joint_scarf of the cover overlaps the corner leg).
CANTOS  L corner pieces: two legs, A and B, each (cover profile, clip profile cut out of the corner,
        clip offset along s, distance from the corner where that edge's clips start, scarf joint).
PEGA    which leg of each corner carries the finger grip.
DOBRADICA  hinge corners: variants of a base corner with a knuckle on the hinge edge's leg.
faces() list of faces with their edges and corners.

Coordinates are the official V0.2 CAD's (mm). An edge's slot line is given by a fixed point (the
axis coordinate is ignored), its axis, the run interval along the axis, the outward normal n of
the face and the direction a toward the frame's outer edge. A straight piece's local frame is
(x, y, z) = (s, d, along the edge), placed with columns (a, n, a x n). A corner's local frame is
(x, y, z) = (along leg A, along leg B, d), with its origin at the outer corner of the cover frame.

The Voron logo (from v11) sits on the top hat front's middle cover.
"""

H1, H2 = 'clip_run_h / 6', 'clip_run_h / 3'
V1, V2 = 'clip_run_v / 3 - idle_cut', 'clip_run_v / 3'

PECAS = {
    'clip-padrao-h1': ('clip-padrao', H1),
    'clip-padrao-h2': ('clip-padrao', H2),
    'clip-padrao-v1': ('clip-padrao', V1),
    'clip-padrao-v2': ('clip-padrao', V2),
    'clip-padrao-th': ('clip-padrao', 'clip_run_th'),
    'clip-parede-h1': ('clip-parede', H1),
    'clip-parede-h2': ('clip-parede', H2),
    'clip-u-h1': ('clip-u', H1),
    'clip-u-h2': ('clip-u', H2),
    'clip-u-idle': ('clip-u', 'idle_cut'),
    'clip-u-fora-h1': ('clip-u-fora', H1),               # rear bottom: the U's wall is the outer face
    'clip-u-fora-h2': ('clip-u-fora', H2),
    'clip-u-fino-h1': ('clip-u-fino', H1),               # rear top: thinner U end wall
    'clip-u-fino-h2': ('clip-u-fino', H2),
    'clip-porta-h1': ('clip-porta', H1),
    'clip-porta-h2': ('clip-porta', H2),
    'clip-porta-lateral-v1': ('clip-porta-lateral', V1),
    'clip-porta-lateral-v2': ('clip-porta-lateral', V2),
    'clip-porta-dobradica-v1': ('clip-porta-dobradica', V1),
    'clip-porta-dobradica-v2': ('clip-porta-dobradica', V2),
    'tampa-parede-h': ('tampa-parede', 'frame_width - 2 * cover_corner'),
    'tampa-parede-v': ('tampa-parede', 'body_height + top_overhang - 2 * cover_corner'),
    'tampa-simples-h': ('tampa-simples', 'frame_width - 2 * cover_corner'),
    'tampa-u-fora-h': ('tampa-u-fora', 'frame_width - 2 * cover_corner'),   # rear bottom, over clip-u-fora
    'tampa-parede-v-puxador': ('tampa-parede', 'body_height + top_overhang - 2 * cover_corner'),   # door, latch side
    'tampa-parede-h-logo': ('tampa-parede', 'frame_width - 2 * cover_corner'),   # top hat front: pocket for the logo
    'clip-h': ('clip-h', 'rear_h_half * 2 / 3'),          # rear middle bar, three per bar
    'tampa-h': ('tampa-h', 'rear_h_half'),                 # its cover, two halves (outer end meets the vertical cover)
}

# leg = (cover profile, clip profile cut out, clip offset along s, where the clips start, scarf joint)
_PAREDE_H = ('tampa-parede', 'clip-padrao', '0 mm', 'frame_size', True)        # horizontal edge: clips stop at the posts
_PAREDE_V = ('tampa-parede', 'clip-padrao', '0 mm', 'clip_end_gap', True)      # vertical edge
_PAREDE_V_TH = ('tampa-parede', 'clip-padrao', '0 mm', 'clip_end_gap', False)  # top hat vertical: no middle, no joint
_TOPO_LATERAL = ('tampa-simples', 'clip-parede', 'top_overhang', 'frame_size', True)
_TOPO_PORTA = ('tampa-simples', 'clip-u', '0 mm', 'frame_size', True)
_TOPO_TRAS = ('tampa-simples', 'clip-u-fino', '0 mm', 'frame_size', True)    # rear top: over clip-u-fino
# rear bottom, rear_drop below the frame: bottom leg over clip-u-fora (its wall kept where no clip runs),
# vertical leg rear_drop longer, its clips starting where the post starts
_BASE_TRAS_H = ('tampa-u-fora-canto', 'clip-u-fora', '0 mm', 'frame_size', True)
_BASE_TRAS_V = ('tampa-parede', 'clip-padrao', '0 mm', 'clip_end_gap + rear_drop', True, 'cover_corner + rear_drop')

CANTOS = {
    'canto-parede-hv': (_PAREDE_H, _PAREDE_V),
    'canto-parede-vh': (_PAREDE_V, _PAREDE_H),
    'canto-parede-hh': (_PAREDE_H, _PAREDE_H),
    'canto-topo-lateral-hv': (_TOPO_LATERAL, _PAREDE_V),
    'canto-topo-lateral-vh': (_PAREDE_V, _TOPO_LATERAL),
    'canto-topo-porta-hv': (_TOPO_PORTA, _PAREDE_V),
    'canto-topo-porta-vh': (_PAREDE_V, _TOPO_PORTA),
    'canto-topo-traseira-hv': (_TOPO_TRAS, _PAREDE_V),
    'canto-topo-traseira-vh': (_PAREDE_V, _TOPO_TRAS),
    'canto-tophat-hv': (_PAREDE_H, _PAREDE_V_TH),
    'canto-tophat-vh': (_PAREDE_V_TH, _PAREDE_H),
    'canto-traseira-base-hv': (_BASE_TRAS_H, _BASE_TRAS_V),
    'canto-traseira-base-vh': (_BASE_TRAS_V, _BASE_TRAS_H),
}

# leg with the finger grip (lip + undercut pocket): the leg on the horizontal edge, as in v11; the
# top hat lid's corners are all the same part, so its grips run round the lid, one per edge
PEGA = {
    'canto-parede-hv': 'A',
    'canto-parede-vh': 'B',
    'canto-parede-hh': 'A',
    'canto-topo-lateral-hv': 'A',
    'canto-topo-lateral-vh': 'B',
    'canto-topo-porta-hv': 'A',
    'canto-topo-porta-vh': 'B',
    'canto-topo-traseira-hv': 'A',
    'canto-topo-traseira-vh': 'B',
    'canto-tophat-hv': 'A',
    'canto-tophat-vh': 'B',
    'canto-traseira-base-hv': 'A',
    'canto-traseira-base-vh': 'B',
}

# hinge corners: the door turns on an M3 screw through two knuckles at each end of the hinge edge, the
# side's at the corner (it holds the screw, head in a counterbore at the corner) and the door's next
# to it (it turns on the screw). Variant -> (base corner, leg on the hinge edge, knuckle profile).
DOBRADICA = {
    'canto-lateral-dobradica-base': ('canto-parede-hv', 'B', 'no-lateral'),
    'canto-lateral-dobradica-topo': ('canto-topo-lateral-vh', 'A', 'no-lateral'),
    'canto-porta-dobradica-base': ('canto-parede-vh', 'A', 'no-porta'),
    'canto-porta-dobradica-topo': ('canto-topo-porta-hv', 'B', 'no-porta'),
}
for _nome, (_base, _, _) in DOBRADICA.items():
    CANTOS[_nome] = CANTOS[_base]
    PEGA[_nome] = PEGA[_base]


def _h4(profile):
    """Horizontal edge: half, full, full, half (the clip joints never meet the cover joints)."""
    return [f'{profile}-h1', f'{profile}-h2', f'{profile}-h2', f'{profile}-h1']


def _v(profile):
    """Vertical edge, bottom to top: short, full, full, then the U piece over the gantry."""
    return [f'{profile}-v1', f'{profile}-v2', f'{profile}-v2', 'clip-u-idle']


def faces(v):
    """v: parameter values in mm (from Fusion). Returns the face list."""
    W, D, fs = v['frame_width'] / 2, v['frame_depth'] / 2, v['frame_size']
    so = fs / 2
    z0 = v['frame_z0']
    zt = z0 + v['body_height']                       # top of the gantry rail
    ztop = zt + v['top_overhang']                    # top line of the panel frames
    zth0 = zt + v['tophat_gap']
    zth1 = zth0 + v['tophat_height']
    gap = v['clip_end_gap']
    run_h_x = (-(W - fs), W - fs)
    run_h_y = (-(D - fs), D - fs)
    run_v = (z0 + gap, ztop - gap)
    run_th = (zth0 + gap, zth1 - gap)
    mid_v = (z0 + ztop) / 2
    X, Y, Z = (1, 0, 0), (0, 1, 0), (0, 0, 1)
    neg = lambda u: tuple(-c for c in u)   # noqa: E731

    def edge(name, axis, run, point, a, pieces, cover=None, shift='0 mm', centre=0.0, logo=False):
        return {'nome': name, 'eixo': axis, 'run': run, 'ponto': point, 'a': a, 'pecas': pieces,
                'tampa': cover, 'desloc': shift, 'centro_tampa': centre, 'logo': logo}

    # rear: both stock sheets uncut (185 + 63 cover the body's 248): the bottom edge comes rear_drop
    # below the frame (clip-u-fora, its wall the outer face), the lower sheet stands on that wall, the H
    # bar sits rear_sheet_play above it, and the upper sheet has the same play up to the top U (clip-u-fino)
    z_b = z0 - v['rear_drop']
    z_h = z_b + v['u_outer_wall'] + v['rear_lower_sheet'] + v['rear_sheet_play'] + v['h_web'] / 2
    h_half = v['rear_h_half']

    def corner(kind, point, dir_a, dir_b, variant=None):
        """kind: corner family; leg A runs along dir_a (the horizontal edge), leg B along dir_b.
        variant: a DOBRADICA corner used here in place of the family's plain one."""
        return {'tipo': kind, 'ponto': point, 'a': dir_a, 'b': dir_b, 'variante': variant}

    out = []
    for sx, label in ((1, 'lateral-direita'), (-1, 'lateral-esquerda')):
        n = (sx, 0, 0)
        x = sx * W
        out.append({'nome': label, 'n': n, 'bordas': [
            edge('base', 'Y', run_h_y, (x, 0, z0 + so), neg(Z), _h4('clip-padrao'), 'tampa-parede-h'),
            edge('topo', 'Y', run_h_y, (x, 0, zt - so), Z, _h4('clip-parede'), 'tampa-simples-h', 'top_overhang'),
            edge('frente', 'Z', run_v, (x, -(D - so), 0), neg(Y), _v('clip-padrao'), 'tampa-parede-v', centre=mid_v),
            edge('tras', 'Z', run_v, (x, D - so, 0), Y, _v('clip-padrao'), 'tampa-parede-v', centre=mid_v),
        ], 'cantos': [
            corner('canto-parede', (x, sy * D, z0), (0, -sy, 0), Z,
                   'canto-lateral-dobradica-base' if (sx, sy) == (1, -1) else None) for sy in (1, -1)
        ] + [
            corner('canto-topo-lateral', (x, sy * D, ztop), (0, -sy, 0), neg(Z),
                   'canto-lateral-dobradica-topo' if (sx, sy) == (1, -1) else None) for sy in (1, -1)
        ]})

    out.append({'nome': 'porta', 'n': neg(Y), 'bordas': [
        edge('base', 'X', run_h_x, (0, -D, z0 + so), neg(Z), _h4('clip-porta'), 'tampa-parede-h'),
        edge('topo', 'X', run_h_x, (0, -D, ztop - so), Z, _h4('clip-u'), 'tampa-simples-h'),
        edge('dobradica', 'Z', run_v, (W - so, -D, 0), X, _v('clip-porta-dobradica'), 'tampa-parede-v', centre=mid_v),
        edge('puxador', 'Z', run_v, (-(W - so), -D, 0), neg(X), _v('clip-porta-lateral'), 'tampa-parede-v-puxador', centre=mid_v),
    ], 'cantos': [
        corner('canto-parede', (sx * W, -D, z0), (-sx, 0, 0), Z,
               'canto-porta-dobradica-base' if sx == 1 else None) for sx in (1, -1)
    ] + [
        corner('canto-topo-porta', (sx * W, -D, ztop), (-sx, 0, 0), neg(Z),
               'canto-porta-dobradica-topo' if sx == 1 else None) for sx in (1, -1)
    ]})

    # rear: one frame (like the door: U clips top and bottom, nothing behind them) with the middle H bar
    out.append({'nome': 'traseira', 'n': Y, 'bordas': [
        edge('base', 'X', run_h_x, (0, D, z_b + so), neg(Z), _h4('clip-u-fora'), 'tampa-u-fora-h'),
        edge('topo', 'X', run_h_x, (0, D, ztop - so), Z, _h4('clip-u-fino'), 'tampa-simples-h'),
        edge('direita', 'Z', run_v, (W - so, D, 0), X, _v('clip-padrao'), 'tampa-parede-v', centre=mid_v),
        edge('esquerda', 'Z', run_v, (-(W - so), D, 0), neg(X), _v('clip-padrao'), 'tampa-parede-v', centre=mid_v),
        edge('meio', 'X', (-h_half, h_half), (0, D, z_h), neg(Z), ['clip-h'] * 3),
    ], 'cantos': [
        corner('canto-traseira-base', (sx * W, D, z_b), (-sx, 0, 0), Z) for sx in (1, -1)
    ] + [
        corner('canto-topo-traseira', (sx * W, D, ztop), (-sx, 0, 0), neg(Z)) for sx in (1, -1)
    ], 'tampas_h': [((0, D, z_h), neg(Z)), ((0, D, z_h), Z)]})   # from the centre out: +X half, -X half

    # top hat sides: normal, horizontal axis of the face, its half width
    for label, n, horiz, half in (('tophat-frente', neg(Y), 'X', W), ('tophat-tras', Y, 'X', W),
                                  ('tophat-direita', X, 'Y', D), ('tophat-esquerda', neg(X), 'Y', D)):
        face_off = tuple(c * (D if horiz == 'X' else W) for c in n)
        h = X if horiz == 'X' else Y
        run_top = run_h_x if horiz == 'X' else run_h_y

        def at(s_along, z):
            p = list(face_off)
            p['XYZ'.index(horiz)] = s_along
            p[2] = z
            return tuple(p)
        out.append({'nome': label, 'n': n, 'bordas': [
            edge('topo', horiz, run_top, at(0, zth1 - so), Z, _h4('clip-padrao'),
                 'tampa-parede-h-logo' if label == 'tophat-frente' else 'tampa-parede-h', logo=label == 'tophat-frente'),
            edge('canto+', 'Z', run_th, at(half - so, 0), h, ['clip-padrao-th']),
            edge('canto-', 'Z', run_th, at(-(half - so), 0), neg(h), ['clip-padrao-th']),
        ], 'cantos': [
            corner('canto-tophat', at(sg * half, zth1), tuple(-sg * c for c in h), neg(Z)) for sg in (1, -1)
        ]})

    out.append({'nome': 'tophat-tampo', 'n': Z, 'bordas': [
        edge('direita', 'Y', run_h_y, (W - so, 0, zth1), X, _h4('clip-padrao'), 'tampa-parede-h'),
        edge('esquerda', 'Y', run_h_y, (-(W - so), 0, zth1), neg(X), _h4('clip-padrao'), 'tampa-parede-h'),
        edge('tras', 'X', run_h_x, (0, D - so, zth1), Y, _h4('clip-padrao'), 'tampa-parede-h'),
        edge('frente', 'X', run_h_x, (0, -(D - so), zth1), neg(Y), _h4('clip-padrao'), 'tampa-parede-h'),
    ], 'cantos': [
        corner('canto-parede-hh', (sx * W, sy * D, zth1), (-sx, 0, 0), (0, -sy, 0)) for sx in (1, -1) for sy in (1, -1)
    ]})
    for f in out:
        f['dobradica'] = DOBRADICA      # hinge corner variants, checked by the shared placement
    return out


from bordas import _cross, colocacoes  # noqa: E402,F401  (shared placement)
