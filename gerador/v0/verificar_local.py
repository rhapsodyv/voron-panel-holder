"""Check the v12 profiles against the Misumi slot and against v11, without Fusion.

Usage: python3 gerador/v0/verificar_local.py [saida.png]
"""
import json
import os
import sys

from shapely import affinity
from shapely.geometry import LineString, Polygon
from shapely.ops import polygonize, unary_union

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(1, os.path.dirname(HERE))     # shared perfis.py
from parametros import PARAMS  # noqa: E402
from perfis import PROFILES, param_values, polygon  # noqa: E402

# clip -> (cover, cover shift along s, v11 counterpart, has a fin in the slot)
SETS = {
    'clip-padrao': ('tampa-parede', 0.0, 'B18', True),
    'clip-parede': ('tampa-simples', 'top_overhang', 'B19', True),
    'clip-u': ('tampa-parede', 0.0, 'B20', False),
    'clip-porta': ('tampa-parede', 0.0, 'B21', True),
    'clip-porta-lateral': ('tampa-parede', 0.0, None, True),
    'clip-porta-dobradica': ('tampa-parede', 0.0, None, True),
}
COVER_V11 = {'tampa-parede': 'tampa-parede', 'tampa-simples': 'tampa-4.0'}


def from_segs(segs):
    lines = [LineString(s) for s in segs if len(s) > 1]
    faces = sorted(polygonize(unary_union(lines)), key=lambda p: -p.area)
    res = None
    for i, f in enumerate(faces):
        depth = sum(1 for g in faces[:i] if g.contains(f.representative_point()))
        res = f if res is None else (res.union(f) if depth % 2 == 0 else res.difference(f))
    return res.buffer(0)


def diff_lines(new, old):
    out = []
    a, b = new.difference(old), old.difference(new)
    out.append(f'só no v12 {a.area:6.3f} mm² · só no v11 {b.area:6.3f} mm² · distância máx. {new.hausdorff_distance(old):.2f} mm')
    for tag, g0 in (('removido', b), ('novo', a)):
        for g in [g for g in getattr(g0, 'geoms', [g0]) if g.area > 0.02]:
            x0, y0, x1, y1 = g.bounds
            out.append(f'    {tag} em s {x0:.2f}…{x1:.2f}, d {y0:.2f}…{y1:.2f} ({g.area:.2f} mm²)')
    return out


def main():
    vals = param_values(PARAMS)
    ref = json.load(open(os.path.join(HERE, 'referencia', 'misumi_1515.json')))
    v11 = json.load(open(os.path.join(HERE, 'referencia', 'v11_secoes.json')))['perfis']
    misumi = from_segs(ref['segs'])
    P = {n: Polygon(polygon(n, vals)) for n in PROFILES}
    ok = True
    print('perfis:')
    for n, p in P.items():
        print(f'  {n:22s} válido={p.is_valid} área={p.area:6.2f} mm²')
        ok &= p.is_valid
    acr = P['acrilico-ref']
    for clip, (cover, shift, old, fin) in SETS.items():
        sh = vals[shift] if isinstance(shift, str) else shift
        cv = affinity.translate(P[cover], xoff=sh)
        c = P[clip]
        print(f'\n{clip} + {cover}' + (f' (deslocada {sh:g} mm)' if sh else ''))
        if fin:
            tip = min(y for _, y in c.exterior.coords)
            print(f'  clip × perfil Misumi {c.intersection(misumi).area:.4f} mm² · ponta em d {tip:.2f} (fundo em -{vals["slot_depth"]:g})')
        print(f'  clip × tampa {c.intersection(cv).area:.4f} mm² · clip × acrílico {c.intersection(acr).area:.3f} mm² · tampa × acrílico {cv.intersection(acr).area:.4f} mm²')
        if old:
            print('  em relação ao v11 ' + old + ': ' + '\n'.join(diff_lines(c, from_segs(v11[old]))))
    for cover, old in COVER_V11.items():
        print(f'\n{cover} em relação ao v11 {old}: ' + '\n'.join(diff_lines(P[cover], from_segs(v11[old]))))

    # door swing, hinge side: rotate the arc-fin clip about the pin (opening = clockwise)
    pin = (vals['door_pin_s'], vals['door_pin_d'])
    c = P['clip-porta-dobradica']
    worst = max(affinity.rotate(c, -a, origin=pin).intersection(misumi).area for a in [i * 0.5 for i in range(0, 91)])
    print(f'\nporta, lado da dobradiça: maior sobreposição com o perfil ao abrir de 0 a 45°: {worst:.4f} mm²')
    ok &= worst < 0.01

    if len(sys.argv) > 1:
        draw(sys.argv[1], P, misumi, v11, vals)
    return ok


def draw(path, P, misumi, v11, vals):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon as MPoly
    fig, axs = plt.subplots(2, 4, figsize=(21, 10))
    for ax, (clip, (cover, shift, old, fin)) in zip(axs.flat, SETS.items()):
        sh = vals[shift] if isinstance(shift, str) else shift
        if clip != 'clip-u':
            for p in getattr(misumi, 'geoms', [misumi]):
                ax.add_patch(MPoly(list(p.exterior.coords), fc='#dcdcdc', ec='#666', lw=.5))
                for h in p.interiors:
                    ax.add_patch(MPoly(list(h.coords), fc='white', ec='#666', lw=.4))
        acr = P['acrilico-ref'] if clip != 'clip-u' else affinity.translate(P['acrilico-ref'], xoff=4.0)
        for poly, col in ((acr, '#a8dcff'), (affinity.translate(P[cover], xoff=sh), '#7aa6e6'), (P[clip], '#4caf50')):
            ax.add_patch(MPoly(list(poly.exterior.coords), fc=col, ec='k', lw=.6, alpha=.85))
        if old:
            o = from_segs(v11[old])
            ax.add_patch(MPoly(list(o.exterior.coords), fc='none', ec='#d62728', lw=.8, ls='--'))
        if clip == 'clip-porta-dobradica':
            from matplotlib.patches import Circle
            ax.add_patch(Circle((vals['door_pin_s'], vals['door_pin_d']), 1.5, fc='white', ec='k'))
            for a in (8, 16, 25):
                r = affinity.rotate(P[clip], -a, origin=(vals['door_pin_s'], vals['door_pin_d']))
                ax.add_patch(MPoly(list(r.exterior.coords), fc='#4caf50', ec='none', alpha=.18))
        ax.set_xlim(-12, 14); ax.set_ylim(-7, 10); ax.set_aspect('equal'); ax.grid(True, lw=.2)
        ax.set_title(f'{clip} + {cover}' + (f' (+{sh:g})' if sh else '') + (f'   · v11 {old} tracejado' if old else ''), fontsize=9)
    ax = axs.flat[6]
    axs.flat[7].axis('off')
    ax.add_patch(MPoly(list(P['tampa-simples'].exterior.coords), fc='#7aa6e6', ec='k', lw=.6))
    o = from_segs(v11['tampa-4.0'])
    ax.add_patch(MPoly(list(o.exterior.coords), fc='none', ec='#d62728', lw=.8, ls='--'))
    ax.set_xlim(-12, 14); ax.set_ylim(-7, 10); ax.set_aspect('equal'); ax.grid(True, lw=.2)
    ax.set_title('tampa-simples · v11 tampa 4,0 tracejado', fontsize=9)
    fig.suptitle('Perfis do panel-holder-v12 no rasgo Misumi 1515', fontsize=11)
    fig.tight_layout()
    fig.savefig(path, dpi=130)


if __name__ == '__main__':
    sys.exit(0 if main() else 1)
