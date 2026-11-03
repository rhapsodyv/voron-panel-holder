"""Placement of the pieces of one face, shared by the machine maps (gerador/<machine>/mapa.py).

A straight piece's local frame is (x, y, z) = (s, d, along the edge), placed with columns (a, n, a x n).
A corner's local frame is (x, y, z) = (along leg A, along leg B, d), with its origin at the outer corner
of the cover frame. Corner variants (e.g. hinge corners) come from the map's DOBRADICA table.
"""


def _cross(u, w):
    return (u[1] * w[2] - u[2] * w[1], u[2] * w[0] - u[0] * w[2], u[0] * w[1] - u[1] * w[0])


def colocacoes(v, comprimentos, face):
    """Placements for one face: list of (component, origin, x axis, y axis, z axis, edge), mm.

    comprimentos: straight piece name -> length in mm (the cover length without the scarves).
    """
    out = []
    n = face['n']
    scarf = v['joint_scarf']
    for e in face['bordas']:
        k = 'XYZ'.index(e['eixo'])
        a = e['a']
        t = _cross(a, n)
        forward = t[k] > 0
        pos = e['run'][0]
        for name in e['pecas']:
            L = comprimentos[name]
            start = pos if forward else pos + L
            o = list(e['ponto'])
            o[k] = start
            out.append((name, tuple(o), a, n, t, e['nome']))
            pos += L
        if e['tampa']:
            half = comprimentos[e['tampa']] / 2 + scarf       # the middle is extruded scarf longer each side
            shift = v[e['desloc']] if e['desloc'] in v else 0.0
            centre = e.get('centro_tampa', 0.0)
            start = centre - half if forward else centre + half
            o = [e['ponto'][i] + shift * a[i] for i in range(3)]
            o[k] = start
            out.append((e['tampa'], tuple(o), a, n, t, e['nome']))
            if e.get('logo'):
                out.append(('logo-voron', tuple(o), a, n, t, e['nome']))   # same frame as its cover
        for name in e.get('extras', ()):
            # a piece of its own in the edge's frame (x = s, y = d, z along), origin on the slot centre
            # line at the cover's centre (e.g. the Trident's bowden plug in the rear sheet's notch)
            o = list(e['ponto'])
            o[k] = e.get('centro_tampa', 0.0)
            out.append((name, tuple(o), a, n, t, e['nome']))
    for o, a in face.get('tampas_h', []):
        out.append(('tampa-h', o, a, n, _cross(a, n), 'meio'))
    for c in face.get('cantos', []):
        ua, ub = c['a'], c['b']
        kind = c['tipo']
        if kind.endswith('-hh'):
            if _cross(ua, ub) != tuple(n):
                ua, ub = ub, ua
            name = kind
        elif _cross(ua, ub) == tuple(n):
            name = f'{kind}-hv'
        else:
            ua, ub = ub, ua
            name = f'{kind}-vh'
        if c.get('variante'):
            assert face.get('dobradica', {})[c['variante']][0] == name, (c['variante'], name)
            name = c['variante']
        out.append((name, c['ponto'], ua, ub, tuple(n), 'canto'))
    return out
