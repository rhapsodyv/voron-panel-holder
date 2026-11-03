"""What sits at each panel edge of the Trident, read from the reference CAD (Fusion "Trident_Assembly", a 250).

Runs inside Fusion with the CAD open. Two regions per edge, along the slot line:
  fora   in front of the face, where the clip block and the cover go (d 0.3..9, s -13..13 mm)
  rasgo  inside the slot, where the fin goes (d -6..-0.3, s -2.9..2.9 mm)
caixas(): coarse pass with bounding boxes (referencia/obstaculos_250.json).
exatos(face): exact pass for one face, intersecting each flagged body with the region box
              (referencia/obstaculos_250_<face>.json). One face per call: the booleans are slow.
Coordinates are the CAD's (mm): frame x -400..10, y -10..400, z -520..-20, rear = +y.
"""
import json
import os
import time

import adsk.core
import adsk.fusion

HERE = os.path.dirname(os.path.abspath(__file__))
REF = os.path.join(HERE, 'referencia')

# face: (normal axis, normal sign, plane), edges: name -> (along axis, (axis, value) of the slot centre)
FACES = {
    'lateral-direita': (0, 1, 10.0, {'frente': (2, (1, 0.0)), 'tras': (2, (1, 390.0)), 'base': (1, (2, -510.0)), 'topo': (1, (2, -30.0))}),
    'lateral-esquerda': (0, -1, -400.0, {'frente': (2, (1, 0.0)), 'tras': (2, (1, 390.0)), 'base': (1, (2, -510.0)), 'topo': (1, (2, -30.0))}),
    'traseira': (1, 1, 400.0, {'direita': (2, (0, 0.0)), 'esquerda': (2, (0, -390.0)), 'meio': (2, (0, -195.0)),
                               'base': (0, (2, -510.0)), 'topo': (0, (2, -30.0))}),
    'topo': (2, 1, -20.0, {'direita': (1, (0, 0.0)), 'esquerda': (1, (0, -390.0)), 'frente': (0, (1, 0.0)), 'tras': (0, (1, 390.0))}),
    'frente': (1, -1, -10.0, {'direita': (2, (0, 0.0)), 'esquerda': (2, (0, -390.0)), 'meio': (2, (0, -195.0)),
                              'base': (0, (2, -510.0)), 'topo': (0, (2, -30.0))}),
}
REGIONS = {'fora': (0.3, 9.0, -13.0, 13.0), 'rasgo': (-6.0, -0.3, -2.9, 2.9)}
IGNORE = ('M5x16 BHCS',)        # frame corner screws, at the rail ends inside the posts


def _design():
    app = adsk.core.Application.get()
    doc = next(d for d in app.documents if d.name.startswith('Trident_Assembly'))
    return adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))


def _box(face, edge, region, along=None):
    ni, ns, plane, edges = FACES[face]
    ax, (pa, pv) = edges[edge]
    d0, d1, s0, s1 = REGIONS[region]
    lo, hi = [-1e4] * 3, [1e4] * 3
    if along:
        lo[ax], hi[ax] = along
    lo[pa], hi[pa] = pv + s0, pv + s1
    lo[ni], hi[ni] = sorted((plane + ns * d0, plane + ns * d1))
    return lo, hi, ax


def exatos(face):
    """Exact intersections for the edges of one face (bodies the coarse pass flagged)."""
    t = time.time()
    design = _design()
    tbm = adsk.fusion.TemporaryBRepManager.get()
    coarse = json.load(open(os.path.join(REF, 'obstaculos_250.json')))
    wanted = {}
    for key, hits in coarse.items():
        f, e = key.split('/')
        if f != face:
            continue
        for region, name, grp, a0, a1 in hits:
            if name not in IGNORE:
                wanted.setdefault(name, []).append((e, region, a0, a1))
    occs = [o for o in design.rootComponent.allOccurrences
            if o.component.name in wanted and not o.fullPathName.startswith('Panels:')]
    out = {}
    for occ in occs:
        name = occ.component.name
        for e, region, a0, a1 in wanted[name]:
            lo, hi, ax = _box(face, e, region, (a0 - 1, a1 + 1))
            centre = adsk.core.Point3D.create(*[(lo[k] + hi[k]) / 20 for k in range(3)])
            box = adsk.core.OrientedBoundingBox3D.create(centre, adsk.core.Vector3D.create(1, 0, 0), adsk.core.Vector3D.create(0, 1, 0),
                                                         (hi[0] - lo[0]) / 10, (hi[1] - lo[1]) / 10, (hi[2] - lo[2]) / 10)
            for b in occ.bRepBodies:
                bb = b.boundingBox
                mn, mx = bb.minPoint.asArray(), bb.maxPoint.asArray()
                if not all(mn[k] * 10 < hi[k] and mx[k] * 10 > lo[k] for k in range(3)):
                    continue
                tb = tbm.copy(b)
                if not tbm.booleanOperation(tb, tbm.createBox(box), adsk.fusion.BooleanTypes.IntersectionBooleanType):
                    continue
                if tb.volume * 1000 < 0.05:
                    continue
                bi = tb.boundingBox
                ext = [round(bi.minPoint.asArray()[ax] * 10, 1), round(bi.maxPoint.asArray()[ax] * 10, 1)]
                key = f'{e}|{region}|{occ.fullPathName.split(":")[0]}|{name}'
                prev = out.get(key)
                out[key] = {'vol': round(tb.volume * 1000 + (prev['vol'] if prev else 0), 1),
                            'ao_longo': [min(ext[0], prev['ao_longo'][0]), max(ext[1], prev['ao_longo'][1])] if prev else ext}
    json.dump(out, open(os.path.join(REF, f'obstaculos_250_{face}.json'), 'w'), indent=1, ensure_ascii=False)
    for k, v in sorted(out.items()):
        print(f'  {face}/{k}: {v["ao_longo"][0]}..{v["ao_longo"][1]} ({v["vol"]} mm³)')
    print(f'exatos {face}: {len(out)} achados, {time.time() - t:.1f} s')
    return out
