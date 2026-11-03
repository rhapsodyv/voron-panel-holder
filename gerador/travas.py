"""The sliding lock on a machine's panels, shared by the maps of the machines with locks (gerador/v0-trava,
gerador/trident-trava): which pieces take it, where, and the frame construir.trava_pecas cuts it in.

A lock is the coupon's features (construir.trava_deslizante) cut into the clip under it and into the cover
(or a corner) over it, plus a slider, a cap and a dot disc in place, open. It goes in the middle of an
edge (user, 2026-10-29), beside the clip joint nearest the middle, with the stretch of clip it changes
(geometria_trava 'trecho') trava_margem_emenda from that joint:
  horizontal edges  in the clip whose own z runs toward the joint, sliding toward it
  verticals         in the clip above the joint, sliding DOWN to lock (its weight keeps it locked)
  one-clip verticals (the V0's top hat)  the cap's whole run, open to locked, centred on the vertical,
                    sliding down
A lock whose frame (s out, d out of the face, sliding direction) is left-handed takes the mirrored pieces
(-espelho: clip, cover, slider and cap are the mirror images of the others). On an edge whose cover sits
further out than the slot (desloc, the V0 sides' top edge) the cap is trava-capa-topo (variant 'topo').
"""
import perfis
import geometria_trava
from bordas import _cross, colocacoes as _colocacoes


def aplicar(faces, v, travas, pecas):
    """faces: the machine's faces(v); travas: {face: edge names with a lock}; pecas: the map's PECAS,
    which must hold the '-trava' and '-trava-espelho' pieces. Puts them in place of the plain ones and
    lists each lock in face['travas']: its origin (the coupon's s = d = z = 0, on the slot line), the edge
    frame (a, n, t = a x n), the sliding direction, whether it is mirrored, and the edge's cover shift."""
    g = geometria_trava.geo(v)
    t1 = g['trecho'][1]
    m = v['trava_margem_emenda']
    run_mid = (g['cap_z'][0] + g['cap_z'][1] + g['c']) / 2      # middle of the cap's run, open to locked
    for face in faces:
        locks = []
        for e in face['bordas']:
            if e['nome'] not in travas.get(face['nome'], ()):
                continue
            n, a, k = face['n'], e['a'], 'XYZ'.index(e['eixo'])
            t = _cross(a, n)
            fwd = t[k] > 0
            L = [perfis.evaluate(pecas[p][1], v) for p in e['pecas']]
            starts = [e['run'][0] + sum(L[:i]) for i in range(len(L))]
            slide = t if e['eixo'] != 'Z' else (0, 0, -1)
            if len(L) == 1:
                i = 0
                x0 = (e['run'][0] + e['run'][1]) / 2 + run_mid * -slide[k]
            else:
                mid = (e['run'][0] + e['run'][1]) / 2
                j = min(range(1, len(L)), key=lambda q: abs(starts[q] - mid))      # the joint nearest the middle
                if e['eixo'] != 'Z':
                    i = j - 1 if fwd else j          # the clip whose z runs toward the joint
                    x0 = starts[j] - (m + t1) * t[k]
                else:
                    i = j                            # the clip above the joint
                    x0 = starts[j] + m + t1
            esp = sum(p * q for p, q in zip(t, slide)) < 0
            suf = '-trava-espelho' if esp else '-trava'
            e['pecas'] = list(e['pecas'])
            e['pecas'][i] += suf
            if e['tampa']:
                e['tampa'] += suf
            for p in e['pecas'][i:i + 1] + ([e['tampa']] if e['tampa'] else []):
                assert p in pecas, p
            o = list(e['ponto'])
            o[k] = x0
            locks.append({'borda': e['nome'], 'origem': tuple(o), 'a': a, 'n': n, 't': t, 'slide': slide, 'espelho': esp,
                          'desloc': v[e['desloc']] if e['desloc'] in v else 0.0})
        face['travas'] = locks
    return faces


def colocacoes(v, comprimentos, face):
    """The face's pieces (bordas.colocacoes), then each lock's slider, cap and dot disc, open. All in the
    edge frame (a, n, a x n) at the lock's origin: a mirrored lock's slider and cap are mirrored parts;
    the disc is round, so the standard one moves to the mirrored dot, and out with a shifted cover."""
    out = _colocacoes(v, comprimentos, face)
    ind = geometria_trava.geo(v)['ind'][1]
    for tv in face.get('travas', []):
        o, a, n, t = tv['origem'], tv['a'], tv['n'], tv['t']
        esp = '-espelho' if tv['espelho'] else ''
        out.append((f'trava-cursor{esp}', o, a, n, t, 'trava'))
        out.append(('trava-capa-topo' if tv['desloc'] else f'trava-capa{esp}', o, a, n, t, 'trava'))
        dz, ds = (-2 * ind if tv['espelho'] else 0.0), tv['desloc']
        out.append(('trava-indicador', tuple(o[i] + dz * t[i] + ds * a[i] for i in range(3)), a, n, t, 'trava'))
    return out


def quadros(v, faces, pecas, cantos):
    """{piece: {'parte': 'clip' or 'tampa', 'perfil': its profile (None for a corner), 'topo': bool,
    'quadro': (origin, s axis, d axis, sliding axis)}}: each lock piece's lock frame in the piece's own
    coordinates, mm; the same wherever the piece goes (checked). faces: the map's faces(v)."""
    L = {k: perfis.evaluate(expr, v) for k, (_, expr) in pecas.items()}
    out = {}
    for face in faces:
        locks = face['travas']
        for name, o, x, y, z, edge in _colocacoes(v, L, face):
            if '-trava' not in name:
                continue
            if name in cantos:      # the lock on the corner's leg: the nearest one
                tv = min(locks, key=lambda q: sum((q['origem'][i] - o[i]) ** 2 for i in range(3)))
            else:
                tv = next(q for q in locks if q['borda'] == edge)

            def loc(u):
                return tuple(round(sum(r[i] * u[i] for i in range(3)), 6) + 0.0 for r in (x, y, z))
            fr = (loc([tv['origem'][i] - o[i] for i in range(3)]), loc(tv['a']), loc(tv['n']), loc(tv['slide']))
            if name in out and any(abs(p - q) > 1e-3 for P, Q in zip(out[name]['quadro'], fr) for p, q in zip(P, Q)):
                raise ValueError(f'{name}: a trava cai em lugares diferentes da peça ({out[name]["quadro"]} / {fr})')
            out[name] = {'parte': 'clip' if name.startswith('clip') else 'tampa', 'perfil': pecas[name][0] if name in pecas else None,
                         'topo': bool(tv['desloc']), 'quadro': fr}
    return out
