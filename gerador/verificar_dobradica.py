"""Door swing at the hinge, without Fusion: rotate the door's hinge-side pieces about the pin and
check them against the side panel's pieces and the frame post, in the three bands along the edge.

  A  height of the side knuckle: side cover + side knuckle; door cover without its wedge
  B  height of the door knuckle: side cover without its wedge; door cover + door knuckle
  C  rest of the edge: both covers with their wedges

Physical section around the front post corner: x' out of the side face, y' out of the front face.
Door frame (s, d) -> (s - frame_size/2, d); side frame (s, d) -> (d, s - frame_size/2).
Opening the door turns it clockwise about the pin.

Usage: python3 gerador/verificar_dobradica.py [v0|trident] [saida.png]
"""
import json
import os
import sys

from shapely import affinity
from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union

from shapely.ops import polygonize

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from perfis import param_values, polygon  # noqa: E402

MAQ = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] in ('v0', 'trident') else 'v0'
OUT = next((a for a in sys.argv[1:] if a.endswith('.png')), None)


def _load(name, path):
    import importlib.util
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


CONFIG = _load('config', os.path.join(HERE, MAQ, 'config.py'))
PARAMS = _load('parametros', os.path.join(HERE, MAQ, 'parametros.py')).PARAMS


def from_segs(segs):
    from shapely.geometry import LineString
    lines = [LineString(s) for s in segs if len(s) > 1]
    faces = sorted(polygonize(unary_union(lines)), key=lambda p: -p.area)
    res = None
    for i, f in enumerate(faces):
        inside = sum(1 for g in faces[:i] if g.contains(f.representative_point()))
        res = f if res is None else (res.union(f) if inside % 2 == 0 else res.difference(f))
    return res.buffer(0)

ANGLES = [i * 0.5 for i in range(0, 241)]          # 0 to 120 deg


def depth(g):
    """Thinnest side of the largest overlap piece (mm), as a penetration depth."""
    parts = [p for p in getattr(g, 'geoms', [g]) if p.area > 0]
    if not parts:
        return 0.0
    r = max(parts, key=lambda p: p.area).minimum_rotated_rectangle
    xs = list(r.exterior.coords)
    sides = [Point(xs[i]).distance(Point(xs[i + 1])) for i in range(2)]
    return min(sides)


def bands(v, P, misumi):
    so = v['frame_size'] / 2
    door = lambda g: affinity.affine_transform(g, [1, 0, 0, 1, -so, 0])    # noqa: E731
    side = lambda g: affinity.affine_transform(g, [0, 1, 1, 0, 0, -so])    # noqa: E731
    wedge = box(so, -1, so + 3, v['wall_width'] + 0.5)                     # beyond the outer line, below the wedge top
    hole_side = Point(so + v['door_pin_d'], v['door_pin_s'] - so).buffer(v['hinge_hole_side'] / 2, 64)
    hole_door = Point(v['door_pin_s'], v['door_pin_d']).buffer(v['hinge_hole_door'] / 2, 64)
    cover = P['tampa-parede']
    post = door(misumi)
    side_clip, door_clip = side(P['clip-padrao']), door(P['clip-porta-dobradica'])
    return {
        'A': (unary_union([side(cover.union(P['no-lateral']).difference(hole_side)), side_clip, post]),
              unary_union([door(cover.difference(wedge)), door_clip])),
        'B': (unary_union([side(cover.difference(wedge)), side_clip, post]),
              unary_union([door(cover.union(P['no-porta']).difference(hole_door)), door_clip])),
        'C': (unary_union([side(cover), side_clip, post]),
              unary_union([door(cover), door_clip])),
    }


def main():
    v = param_values(PARAMS)
    so = v['frame_size'] / 2
    P = {n: Polygon(polygon(n, v)) for n in ('tampa-parede', 'clip-padrao', 'clip-porta-dobradica', 'no-lateral', 'no-porta')}
    misumi = from_segs(json.load(open(os.path.join(HERE, MAQ, 'referencia', CONFIG.PERFIL_JSON)))['segs'])
    pin = (v['door_pin_s'] - so, v['door_pin_d'])
    B = bands(v, P, misumi)
    ok = True
    print(f'pino em x\' {pin[0]:.2f}, y\' {pin[1]:.2f} (a partir da quina do poste); giro de 0 a {ANGLES[-1]:g}°')
    for name, (static, moving) in B.items():
        worst = (0.0, 0.0, 0.0)
        for a in ANGLES:
            inter = affinity.rotate(moving, -a, origin=pin).intersection(static)
            if inter.area > worst[1]:
                worst = (a, inter.area, depth(inter))
        tag = 'limpo' if worst[2] < 0.01 else 'ROÇA'
        print(f'  faixa {name}: {tag}, pior em {worst[0]:g}°: {worst[1]:.4f} mm², profundidade {worst[2]:.3f} mm')
        ok &= worst[2] < 0.01
    print(f'{CONFIG.NOME}: aleta em arco e nós no giro')
    if MAQ != 'v0':
        if OUT:
            draw(OUT, B, pin)
        return ok
    # v11 knuckles for comparison: octagon blocks, holes at (11.75, 4.15) side and (11.95, 4.15) door
    octo = Polygon([(4.5, 0), (12.75, 0), (15.6, 2.85), (15.6, 5.45), (12.75, 8.3), (4.5, 8.3)])
    side = lambda g: affinity.affine_transform(g, [0, 1, 1, 0, 0, -so])    # noqa: E731
    door = lambda g: affinity.affine_transform(g, [1, 0, 0, 1, -so, 0])    # noqa: E731
    pin11 = (4.15, 11.75 - so)                       # the screw sits in the side's hole
    for name, static, moving in (
            ('A (v11)', side(P['tampa-parede'].union(octo)), door(P['tampa-parede'].difference(box(so, -1, so + 3, 3.5)))),
            ('B (v11)', side(P['tampa-parede'].difference(box(so, -1, so + 3, 3.5))), door(P['tampa-parede'].union(octo)))):
        w = max(((a, depth(affinity.rotate(moving, -a, origin=pin11).intersection(static))) for a in ANGLES), key=lambda t: t[1])
        print(f'  faixa {name}: profundidade máx. {w[1]:.3f} mm em {w[0]:g}°')
    if OUT:
        draw(OUT, B, pin)
    return ok


def draw(path, B, pin):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axs = plt.subplots(1, 3, figsize=(18, 6.5))
    for ax, (name, (static, moving)) in zip(axs, B.items()):
        for g in getattr(static, 'geoms', [static]):
            ax.fill(*g.exterior.xy, color='#c8c8c8', ec='#555', lw=0.6)
            for i in g.interiors:
                ax.fill(*i.xy, color='white', ec='#555', lw=0.6)
        for a, col in ((0, '#1f77b4'), (30, '#2ca02c'), (60, '#ff7f0e'), (90, '#d62728'), (120, '#9467bd')):
            r = affinity.rotate(moving, -a, origin=pin)
            for g in getattr(r, 'geoms', [r]):
                ax.plot(*g.exterior.xy, color=col, lw=0.9, label=f'{a}°' if g is getattr(r, 'geoms', [r])[0] else None)
                for i in g.interiors:
                    ax.plot(*i.xy, color=col, lw=0.6)
        ax.plot(*pin, 'k+', ms=10)
        ax.set_xlim(-14, 16)
        ax.set_ylim(-16, 14)
        ax.set_aspect('equal')
        ax.grid(True, lw=0.3)
        ax.set_title(f'faixa {name}: cinza = lateral e poste; linhas = porta girando')
        ax.set_xlabel("x' (para fora da lateral)")
        ax.set_ylabel("y' (para fora da frente)")
        ax.legend(fontsize=8, loc='lower right')
    plt.tight_layout()
    plt.savefig(path, dpi=90)


if __name__ == '__main__':
    sys.exit(0 if main() else 1)
