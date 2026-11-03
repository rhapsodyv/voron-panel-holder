"""The one-piece Trident with the lock, built in build123d instead of Fusion (machine trident-peca-unica; the user,
2026-11-01: "se quiser fazer essa nova versão da peça inteira com trava com o build123d ao invés do fusion, também
pode"). The same parameter table, profiles (perfis) and lock geometry (geometria_trava) as the Fusion generator,
evaluated without Fusion; each function ports the construir.py step it names.

Split A (the user's support joint, 2026-11-01): on each edge a corner + a middle + a corner, where the Trident has
its covers. The middle is the chosen coupon's piece (config.PECA: one thick leg with the hook on the acrylic's
side, the window, the neck's slot, the dot) with the lock at its middle; its ends pass over the corners' legs on
the Trident's 45 deg scarf, which holds them down and lets the middle slide its 1.1 across the edge to lock. The
corners have no hook and no lock and go in straight (config.CANTOS_FARPA: the barbed split fin, else the solid fin).
Since lock v8 (config.PERNA_LISA, faces v2) the middle's leg is plain and the hook is on the slider, so the middles go
in straight too, with the panel.

Frames, mm: a straight piece (x, y, z) = (s, d, along the edge), as bordas.colocacoes places it; a corner (x, y, z)
= (along leg A, along leg B, d), its origin at the outer corner. Everything prints lying, the outer face (d = top)
on the bed, with the user's support for the base under the acrylic (peca_unica_trava's 'suporte').

Run with the venv that has build123d (from the repository root):
  .venv-b3d/bin/python gerador/peca_unica_b3d.py cupom               the coupon again, against its Fusion STEP
  .venv-b3d/bin/python gerador/peca_unica_b3d.py lateral-esquerda    build, check and export that face (-v<FACES_VERSAO>)
  .venv-b3d/bin/python gerador/peca_unica_b3d.py kit-v8              lock v8's test kit (the hook on the slider)
  .venv-b3d/bin/python gerador/peca_unica_b3d.py kit-v9              thinner sliders for v8 (config.GANCHO_CURSOR_V9)
"""
import json
import math
import os
import struct
import sys
import time

import build123d as bd

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import geometria_trava  # noqa: E402
import herdar  # noqa: E402
import perfis  # noqa: E402

MAQUINA = 'trident-peca-unica'
config = herdar.de(MAQUINA, 'config')
parametros = herdar.de(MAQUINA, 'parametros')
mapa = herdar.de(MAQUINA, 'mapa')

V7 = os.path.join(REPO, 'stl', 'trident-provas-peca-unica-trava-v7')     # the final slider and cap
V6 = os.path.join(REPO, 'stl', 'trident-provas-peca-unica-trava-v6')     # the chosen coupon
DISCO = os.path.join(REPO, 'stl', 'trident-provas-peca-unica-trava-v5', 'trava-indicador-1x.stl')


# ---------------------------------------------------------------- values
MUDANCAS = {}     # parameter -> expression, over every evaluation below (the web configurator's changed parameters)


def valores(changes=None):
    """The parameter table evaluated with some expressions changed (construir._vals_with), and MUDANCAS over them."""
    changes = {**(changes or {}), **MUDANCAS}
    vals, late = {}, {}
    for _, n, e, _, _ in parametros.PARAMS:
        if n in changes:
            try:
                vals[n] = perfis.evaluate(changes[n], vals)
                continue
            except NameError:
                late[n] = changes[n]
        vals[n] = perfis.evaluate(e, vals)
    for n, e in list(late.items()) + [(n, e) for n, e in changes.items() if n not in vals]:
        vals[n] = perfis.evaluate(e, vals)
    return vals


def valores_trava(aperto=None):
    """The middles' values: the chosen coupon's piece and the final slider (their fin_inset, 0.03, sets the hook
    and the tongue); aperto replaces peca_unica_gancho_aperto."""
    ch = {**config.PECA_UNICA_VARIANTES[config.PECA], **config.TRAVA_VARIANTES[config.TRAVA]}
    if aperto is not None:
        ch['peca_unica_gancho_aperto'] = aperto
    return valores(ch)


def _avaliar(pts, v):
    out = [(perfis.evaluate(s, v), perfis.evaluate(d, v)) for s, d in pts]
    return [p for i, p in enumerate(out) if math.dist(p, out[i - 1]) > 1e-6]


# ---------------------------------------------------------------- geometry helpers
def _prisma(pts, eixos, a, b):
    """Prism of the polygon pts, pairs in the two axes eixos names ('xy', 'yz', 'xz'), from a to b along the third."""
    i, j = 'xyz'.index(eixos[0]), 'xyz'.index(eixos[1])
    k = 3 - i - j

    def p3(u, w):
        c = [0.0, 0.0, 0.0]
        c[i], c[j], c[k] = u, w, a
        return bd.Vector(*c)
    pts = [p for n, p in enumerate(pts) if math.dist(p, pts[n - 1]) > 1e-6]
    face = bd.Face(bd.Wire.make_polygon([p3(u, w) for u, w in pts], close=True))
    d = [0, 0, 0]
    d[k] = 1
    return bd.extrude(face, amount=b - a, dir=tuple(d))


def _caixa(x, y, z):
    (x0, x1), (y0, y1), (z0, z1) = x, y, z
    return bd.Pos((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2) * bd.Box(x1 - x0, y1 - y0, z1 - z0)


def _cilindro(eixo, centro, diametro, a, b):
    """Cylinder along axis eixo ('x', 'y' or 'z') from a to b, its axis through centro (the other two coordinates)."""
    k = 'xyz'.index(eixo)
    c = list(centro)
    c.insert(k, (a + b) / 2)
    rot = {'x': bd.Rot(0, 90, 0), 'y': bd.Rot(90, 0, 0), 'z': bd.Rot(0, 0, 0)}[eixo]
    return bd.Pos(*c) * rot * bd.Cylinder(diametro / 2, b - a)


def _solido(shape):
    """The shape as one solid (booleans hand back compounds); fails if it fell apart."""
    sol = shape.solids()
    if len(sol) != 1:
        raise RuntimeError(f'{len(sol)} sólidos: a peça se partiu')
    return sol[0]


def _xyz(p):
    return (p.X, p.Y, p.Z)


def _normal_fora(part, face, m):
    """face's normal at m pointing out of part (a face a boolean made can come reversed)."""
    n = face.normal_at(m)
    return n * -1 if part.is_inside(m + n * 0.05) else n


def _faces_da_aresta(part, edge):
    return [f for f in part.faces() if any(edge.is_same(e) for e in f.edges())]


def chanfro_mesa(part, eixo, valor, dist, so_contorno=False, pular=None):
    """construir._chanfro_mesa: dist on the edges of the flat faces lying on the plane eixo = valor (the bed), less those
    whose other face already leans 45 deg or flatter from the bed or lies lower than the chamfer under the edge's
    middle, circles (the dot) and edges whose midpoint pular() accepts; so_contorno: each face's outer loop only.
    Chamfered on the part itself (bd.chamfer chamfers the edges' topo_parent, which can be an older state of the part:
    in clips_b3d the doors' cover came back without its handle), each result checked: the volume removed must fit a
    chamfer of those edges and the box must stay (2026-11-02, from clips_b3d, checked against Fusion's STLs).
    All at once, else edge by edge; an edge OpenCascade refuses (the side knuckle's end at the corner, beside the 0.15
    notch) is cut as Fusion chamfers it (_chanfro_manual). Returns (part, done, failed)."""
    k = 'xyz'.index(eixo)

    def achar(p):
        out = []
        for f in p.faces():
            if f.geom_type != bd.GeomType.PLANE or any(abs(_xyz(vx)[k] - valor) > 1e-3 for vx in f.vertices()):
                continue
            for e in (f.outer_wire().edges() if so_contorno else f.edges()):
                if e.geom_type == bd.GeomType.CIRCLE:
                    continue
                mm = e.position_at(0.5)
                outra = [g for g in _faces_da_aresta(p, e) if not g.is_same(f)]
                if outra:
                    nf, ng = _normal_fora(p, f, mm), _normal_fora(p, outra[0], mm)
                    if nf.dot(ng) > 0.6:
                        continue
                    # the other face lower than the chamfer under the edge's middle (the 0.15 notch between a hinge
                    # knuckle and the cover's chamfer; there the face can run on, merged, deeper at an end)
                    ug = (nf - ng * nf.dot(ng)).normalized() * -1
                    if abs(_xyz(ug)[k]) > 1e-6 and not outra[0].is_inside(mm + ug * ((dist - 2e-3) / abs(_xyz(ug)[k]))):
                        continue
                if pular and pular(_xyz(mm)):
                    continue
                if all((mm - m2).length > 1e-3 for m2, _, _ in out):
                    out.append((mm, e, f))
        return out

    def confere(antes, depois, arestas):
        perda = _volume(antes) - _volume(depois)
        b0, b1 = antes.bounding_box(), depois.bounding_box()
        caixa = _xyz(b0.min) + _xyz(b0.max), _xyz(b1.min) + _xyz(b1.max)
        return (-1e-6 <= perda <= sum(e.length for e in arestas) * dist * dist * 0.6 + 0.05
                and all(abs(a - b) <= dist + 1e-3 for a, b in zip(*caixa)))

    achadas = achar(part)
    if not achadas:
        return part, 0, 0
    try:
        r = _solido(part.chamfer(dist, None, [e for _, e, _ in achadas]))
        if confere(part, r, [e for _, e, _ in achadas]):
            return _sadio(r), len(achadas), 0
    except Exception:
        pass

    def mesma(e0, e2):
        """e2 is what is left of e0 (a neighbour's chamfer shortens a straight edge: its midpoint moves)."""
        if e0.geom_type != bd.GeomType.LINE or e2.geom_type != bd.GeomType.LINE:
            return (e0.position_at(0.5) - e2.position_at(0.5)).length < 1e-3
        a, t = e0.position_at(0), (e0.position_at(1) - e0.position_at(0)).normalized()
        fora = lambda p: ((p - a) - t * (p - a).dot(t)).length            # noqa: E731
        p0, p1 = e2.position_at(0), e2.position_at(1)
        u = sorted(((p0 - a).dot(t), (p1 - a).dot(t)))
        return fora(p0) < 1e-4 and fora(p1) < 1e-4 and min(u[1], e0.length) - max(u[0], 0.0) > 1e-4

    feitas = falhas = 0
    for _, e0, _ in achadas:
        acha = [(e, f) for _, e, f in achar(part) if mesma(e0, e)]
        if not acha:
            continue                              # taken by a neighbour's chamfer
        e, f = acha[0]
        r = None
        for tenta in (lambda: _solido(part.chamfer(dist, None, [e])), lambda: _chanfro_manual(part, e, f, dist)):
            try:
                r = tenta()
            except Exception:
                r = None
            if r is not None and confere(part, r, [e0]):       # its whole length: a neighbour's chamfer shortened e
                break
            r = None
        if os.environ.get('CLIPS_DEBUG'):
            print('    chanfro', [round(c, 3) for c in _xyz(e.position_at(0))], [round(c, 3) for c in _xyz(e.position_at(1))],
                  'feito' if r is not None else 'FALHOU', flush=True)
        if r is None:
            falhas += 1
        else:
            part, feitas = _sadio(r), feitas + 1
    return part, feitas, falhas


def _volume_malha(shape, tol=0.001):
    """The volume of the shape's own triangulation (exact on plane faces)."""
    import numpy as np
    vs, ts = shape.tessellate(tol, 0.05)
    v = np.array([(p.X, p.Y, p.Z) for p in vs])[np.array(ts)]
    return float(np.einsum('ij,ij->i', v[:, 0], np.cross(v[:, 1], v[:, 2])).sum() / 6)


def _volume(shape):
    """The volume, from the triangulation when OpenCascade's B-rep sum disagrees (see _sadio)."""
    a = shape.volume
    b = _volume_malha(shape)
    return a if abs(a - b) < 1e-3 + 1e-6 * abs(b) else b


def _sadio(shape):
    """The shape, or, when its B-rep volume disagrees with its own triangulation, a solid rebuilt from that
    triangulation (plane faces only): a chamfer over a chain of edges shorter than itself (the cap's concave crest,
    0.25 segments under 0.4) comes out right in its mesh (the same as Fusion's) but with a B-rep whose volume is 1.5 off
    and on which booleans fail."""
    import tempfile
    if abs(shape.volume - _volume_malha(shape)) < 1e-3 + 1e-6 * shape.volume:
        return shape
    if any(f.geom_type != bd.GeomType.PLANE for f in shape.faces()):
        raise RuntimeError('sólido com volume inconsistente e faces curvas: não dá para refazer pela malha')
    with tempfile.TemporaryDirectory() as d:
        bd.export_stl(shape, os.path.join(d, 'x.stl'), tolerance=0.001, angular_tolerance=0.05)
        return stl_solido(os.path.join(d, 'x.stl'))


def _chanfro_manual(part, e, f, dist):
    """An equal-distance chamfer of a straight edge e between the plane face f and another plane face, cut as a prism:
    the triangle dist along each face from the edge, along the edge's line, bounded at each end by the planes of the
    other faces meeting there, on the edge's side (so it ends flush on a notch's wall, mitres against a chamfered
    neighbour at a concave corner, and runs on under a face that slopes away, as Fusion's)."""
    if e.geom_type != bd.GeomType.LINE:
        return None
    a, b = e.position_at(0), e.position_at(1)
    t = (b - a).normalized()
    mm = e.position_at(0.5)
    outra = [g for g in _faces_da_aresta(part, e) if not g.is_same(f)]
    if len(outra) != 1 or outra[0].geom_type != bd.GeomType.PLANE:
        return None
    g = outra[0]
    nf, ng = _normal_fora(part, f, mm), _normal_fora(part, g, mm)
    uf = (ng - nf * ng.dot(nf)).normalized() * -1
    ug = (nf - ng * nf.dot(ng)).normalized() * -1
    p0 = a - t * 20
    tri = bd.Face(bd.Wire.make_polygon([p0, p0 + uf * dist, p0 + ug * dist], close=True))
    corte = bd.extrude(tri, amount=(b - a).length + 40, dir=_xyz(t))
    for vx in (a, b):
        for h in part.faces():
            if h.is_same(f) or h.is_same(g) or h.geom_type != bd.GeomType.PLANE or all((bd.Vector(*_xyz(w)) - vx).length > 1e-5 for w in h.vertices()):
                continue
            nh = h.normal_at()
            lado = nh.dot(mm - vx)
            if abs(lado) < 1e-6:
                continue
            nh = nh * (1 if lado > 0 else -1)
            corte = corte & (bd.Location(bd.Plane(origin=_xyz(vx), z_dir=_xyz(nh))) * bd.Pos(0, 0, 200) * bd.Box(400, 400, 400))
    return _solido(part - corte)


def stl_solido(caminho):
    """A Fusion STL as a solid (its triangles sewn into a shell), for booleans against the port."""
    from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeSolid, BRepBuilderAPI_Sewing
    from OCP.ShapeFix import ShapeFix_Solid
    from OCP.StlAPI import StlAPI_Reader
    from OCP.TopAbs import TopAbs_SHELL
    from OCP.TopExp import TopExp_Explorer
    from OCP.TopoDS import TopoDS, TopoDS_Shape
    sh = TopoDS_Shape()
    StlAPI_Reader().Read(sh, caminho)
    costura = BRepBuilderAPI_Sewing(1e-4)
    costura.Add(sh)
    costura.Perform()
    ex, ms = TopExp_Explorer(costura.SewedShape(), TopAbs_SHELL), BRepBuilderAPI_MakeSolid()
    while ex.More():
        ms.Add(TopoDS.Shell(ex.Current()))
        ex.Next()
    fix = ShapeFix_Solid(ms.Solid())
    fix.Perform()
    # the coplanar triangles merged into faces: booleans against the port then find the shared faces
    from OCP.ShapeUpgrade import ShapeUpgrade_UnifySameDomain
    u = ShapeUpgrade_UnifySameDomain(fix.Solid(), True, True, True)
    u.Build()
    return _solido(bd.Shape.cast(u.Shape()))


# ---------------------------------------------------------------- profiles
def perfil_corpo(v, cunha=True):
    """perfis.PECA_UNICA without its fin (the hook leg or the corner's fin go under it); cunha False: no corner wedge
    (the bottom edges, as perfis.TAMPA_BASE)."""
    pts = perfis.PECA_UNICA[len(perfis._solid_fin()):]
    if not cunha:
        pts = [p for p in pts if p not in (('frame_size / 2 + wall_width / 2', 'wall_width / 2'), ('frame_size / 2', 'wall_width'))]
    return _avaliar(pts, v)


def perna_gancho(v):
    """construir.peca_unica_trava's hook leg (hk): one thick leg on the acrylic's side, fixed to the base, with the hook
    peca_unica_gancho past the opening and its top slope peca_unica_gancho_aperto above the lip's corner."""
    g = geometria_trava.geo(v)
    so, gancho, gf = g['so'], v['peca_unica_gancho'], v['peca_unica_gancho_folga']
    wl = g['lingueta'][0]
    sr, lip, tip = -(so - gf), v['slot_lip'], v['slot_depth'] - v['fin_tip_clearance']
    sb = gf + v.get('peca_unica_gancho_aperto', -gf)
    return [(wl, 0.0), (wl, -tip), (sr, -tip), (sr, -lip - 2 * (gancho + gf) - 0.5 + sb), (-(so + gancho), -lip - (gancho + gf) - 0.5 + sb),
            (-(so + gancho), -lip - (gancho + gf) + sb), (sr, -lip + sb), (sr, 0.0)]


def rasgo_haste(v):
    """construir.peca_unica_trava's neck slot, (s, z) in the coupon's frame (peca_unica_rasgo_folga 2: wide only where
    the neck sits open)."""
    g = geometria_trava.geo(v)
    gancho, gf = v['peca_unica_gancho'], v['peca_unica_gancho_folga']
    modo = round(v.get('peca_unica_rasgo_folga', 1))
    if modo != 2:
        raise ValueError(f'peca_unica_rasgo_folga {modo}: só o 2 (o da peça escolhida) está portado')
    fl_ = gancho + 2 * gf
    (h0, h1), (p0, p1) = (g['hs'][0], max(g['hs'][1], g['wo'])), g['path']
    zw = g['hz'][1] + g['win'][1] - (g['z0'] + g['lk']) + v['trava_entrada_comprimento'] + 0.3
    return [(h0 - fl_, p0), (h1, p0), (h1, p1), (h0, p1), (h0, zw + fl_), (h0 - fl_, zw)]


def aletas(v, farpa):
    """A corner's fin, polygons (s, d): the doors' solid fin, or the clips' two barbed legs (perfis._leg_right and its
    mirror) at v's fin_inset."""
    if not farpa:
        return [_avaliar(perfis._solid_fin(), v)]
    perna = _avaliar(perfis._leg_right(), v)
    return [perna, [(-s, d) for s, d in reversed(perna)]]


# ---------------------------------------------------------------- the middle (hook + lock)
def perna_lisa(v):
    """Lock v8's leg (config.GANCHO_CURSOR): the hook leg without its hook, the same faces to the lip and the tongue."""
    g = geometria_trava.geo(v)
    sr, wl, tip = -(g['so'] - v['peca_unica_gancho_folga']), g['lingueta'][0], v['slot_depth'] - v['fin_tip_clearance']
    return [(wl, 0.0), (wl, -tip), (sr, -tip), (sr, 0.0)]


def boia(v):
    """How far the slider floats in, open (the neck slot's wide part): the hook and its clearance at each side."""
    return v['peca_unica_gancho'] + 2 * v['peca_unica_gancho_folga']


def meio(L, cunha=True, cupom=False, lisa=False):
    """A middle, L long between the corners, the lock at its middle (the lock coupon's frame moved by 'desloc' along
    it). Extruded joint_scarf longer at each end and cut there on the 45 deg scarf (construir.pecas): its top passes
    joint_scarf over the corner's leg. cunha False: no corner wedge (the bottom edges, as the Trident's tampa-base).
    cupom: the coupon instead (peca_unica_comprimento, flat ends, the wedge all along, its grooves), to check the port
    against its Fusion STEP. lisa: lock v8's plain leg (perna_lisa), with a 45 deg ramp at the window's far end that
    pushes the floating tongue out (boia) as it slides to lock, and no grooves. Returns dict(peca, suporte, desloc, ...)."""
    v = valores_trava()
    v0 = valores_trava(config.APERTO_LONGE)
    g = geometria_trava.geo(v)
    top, T = g['top'], g['T']
    js = 0.0 if cupom else v['joint_scarf']
    Lc = v['peca_unica_comprimento']
    Lt = Lc if cupom else L + 2 * js
    # the lock in the middle: the cap's whole range, open to locked, centred
    desloc = 0.0 if cupom else Lt / 2 - (g['cap_z'][0] + g['cap_z'][1] + g['c']) / 2
    peca = _prisma(perfil_corpo(v, cunha or cupom), 'xy', 0.0, Lt)
    # the hook leg along the piece, none in the window; the wedge only over the coupon's length (config.APERTO_LONGE elsewhere)
    w0, w1 = desloc + g['win'][0], desloc + g['win'][1]
    a0, a1 = (0.0, Lt) if cupom else (desloc, desloc + Lc)
    trechos = [(js, a0, v0), (a0, w0, v), (w1, a1, v), (a1, Lt - js, v0)]
    for za, zb, vv in trechos:
        if zb - za > 1e-6:
            peca = peca + _prisma(perna_lisa(vv) if lisa else perna_gancho(vv), 'xy', za, zb)
    if lisa:
        # the ramp, from the floating tongue's inner face at the window's end to the leg's face, through the leg's depth
        wl, r = g['lingueta'][0], boia(v)
        peca = peca - _prisma([(wl - r - 1, w1 - 1), (wl + 1, w1 + r + 1), (wl + 1, w1 - 1)], 'xz', -v['slot_depth'] - 1, 0.0)
    # the neck's slot, from the frame face through the piece
    peca = peca - _prisma([(s, z + desloc) for s, z in rasgo_haste(v)], 'xz', 0.0, top + 1)
    # the dot (the disc trava-indicador fills it)
    (si, zi), di, dp = g['ind'], v['trava_indicador_diametro'], v['trava_indicador_profundidade']
    peca = peca - _cilindro('y', (si, zi + desloc), di, top - dp, top + 1)
    if not cupom:
        # the scarf at both ends (construir.pecas: cut below the cover's recess and at 45 deg above it)
        rec = T + v['cover_recess']
        for pts in ([(js, -12.0), (js, rec), (-2.0, top + 2), (-2.0, -12.0)],
                    [(Lt - js, -12.0), (Lt - js, rec), (Lt + 2, top + 2), (Lt + 2, -12.0)]):
            peca = peca - _prisma([(d, z) for z, d in pts], 'yz', -60.0, 60.0)
    peca = _solido(peca)
    peca, feitas, falhas = chanfro_mesa(peca, 'y', top, v['trava_chanfro_mesa'],
                                        pular=lambda m: math.hypot(m[0] - si, m[2] - zi - desloc) < di / 2 + 0.2)
    if cupom and not lisa:
        # its grooves, after the chamfer as in Fusion
        for i in range(config.PECA_UNICA_MARCAS.get(config.PECA, 0)):
            za = Lc - 4 - 2.5 * i
            peca = _solido(peca - _caixa((-8.0, 5.0), (top - 0.6, top + 1), (za, za + 1)))
    return dict(peca=peca, suporte=suporte_meio(v, Lt, js, None if cupom else peca), desloc=desloc, comprimento=Lt, chanfro=(feitas, falhas), v=v, g=g)


def suporte_meio(v, Lt, js, peca=None):
    """construir.peca_unica_trava's 'suporte' along a straight piece Lt long: a wall standing on the bed suporte_folga
    in front of the cover's inner edge and past both ends, up to the base's underside, and a one-layer lamina from its
    top to the base's edge and ends (the base ends js in from the piece's ends, under the scarf). With the piece, the
    lamina's second layer (_lamina_topo)."""
    T, top = v['panel_frame_spacing'] + v['panel_thickness'], v['panel_frame_spacing'] + v['panel_thickness'] + v['cover_height']
    ceil, lam = T - v['peca_unica_vao'], v['suporte_lamina']
    gf, pw = v['suporte_folga'], v['suporte_parede']
    s_in = -(v['frame_size'] / 2 + v['cover_overlap'])
    sw = (s_in - gf - pw, s_in - gf)
    zw = (-gf - pw, Lt + gf + pw)
    stop = -v['slot_opening'] / 2 + v['panel_edge_clearance']
    base0 = -(v['frame_size'] / 2 - v['base_inset'])
    caixas = [(sw, (ceil, top), zw),
              ((sw[0], stop), (ceil, top), (zw[0], -gf)),
              ((sw[0], stop), (ceil, top), (Lt + gf, zw[1])),
              ((sw[0], base0), (ceil - lam, ceil), zw),
              ((sw[0], stop), (ceil - lam, ceil), (zw[0], js)),
              ((sw[0], stop), (ceil - lam, ceil), (Lt - js, zw[1]))]
    out = None
    for c in caixas:
        out = _caixa(*c) if out is None else out + _caixa(*c)
    if peca is not None:
        out = out + _lamina_topo(v, [c for c in caixas if c[1] == (ceil - lam, ceil)], peca, 1)
    return _solido(out)


def _lamina_topo(v, laminas, peca, k):
    """The laminas' second layer (the user, 2026-11-02: "tem que fazer essa bridge ter 2 camadas, porem 1 camada só onde
    encosta na nossa peça... assim vai ficar mais facil de remover"): on the one-layer laminas (boxes, d along axis k)
    up to suporte_lamina_topo thick, except within suporte_lamina_contato of the piece across, where they stay one
    layer to break off (the piece's slab at that height moved that far along both axes across and the diagonals)."""
    lam, lt, w = v['suporte_lamina'], v['suporte_lamina_topo'], v['suporte_lamina_contato']
    out = None
    for c in laminas:
        c = list(c)
        c[k] = (c[k][0] - (lt - lam), c[k][0])           # above it as it prints (d down from the bed)
        out = _caixa(*c) if out is None else out + _caixa(*c)
    lo, hi = [-500.0] * 3, [500.0] * 3
    lo[k], hi[k] = laminas[0][k][0] - (lt - lam) - 0.05, laminas[0][k][0] + 0.05
    laje = peca & _caixa(*zip(lo, hi))
    a, b = [i for i in range(3) if i != k]
    for da in (-w, 0.0, w):
        for db in (-w, 0.0, w):
            if da or db:
                t = [0.0] * 3
                t[a], t[b] = da, db
                out = out - laje.moved(bd.Location(tuple(t)))
    return out


# ---------------------------------------------------------------- the corners (no hook, no lock)
def _perna(leg, fn):
    """Map a leg's (u along it, w in from the outer line) to the corner frame's (x, y): leg A along x, B along y."""
    return (lambda u, w: fn(u, w)) if leg == 'A' else (lambda u, w: fn(w, u))


def canto(nome):
    """A corner (mapa.CANTOS: the Trident's L of two legs, cover_corner long, mitred at 45 deg) in one piece:
    construir._canto_etapa's legs (each its edge's one-piece body), the scarf at each leg's end (the middle passes
    over it), the fin from where the clips started (frame_size on a horizontal edge, clip_end_gap on a vertical one),
    the finger grip (mapa.PEGA) and the side's hinge knuckle (mapa.DOBRADICA). Solid fin, or config.CANTOS_FARPA:
    the clips' barbed split fin at the machine's fin_inset. Returns dict(peca, suporte, ...)."""
    v = valores()                     # the machine's values: its fin_inset for the barbed fin
    T, top = v['panel_frame_spacing'] + v['panel_thickness'], v['panel_frame_spacing'] + v['panel_thickness'] + v['cover_height']
    fs, js, ext = v['frame_size'], v['joint_scarf'], 2.0
    pernas = mapa.CANTOS[nome]
    J = [perfis.evaluate(p[5] if len(p) > 5 else 'cover_corner', v) for p in pernas]
    cunha = [p[0] != 'tampa-base' for p in pernas]
    if any(p[0] not in ('tampa-parede', 'tampa-base') for p in pernas):
        raise ValueError(f'{nome}: só pernas de parede e de base estão portadas ({[p[0] for p in pernas]})')
    for p in pernas:
        if not p[4]:
            raise ValueError(f'{nome}: perna sem junta com um meio')
    corpo = None
    for i, leg in enumerate('AB'):
        sec = [(fs / 2 - s, d) for s, d in perfil_corpo(v, cunha[i])]          # (w, d)
        if leg == 'A':
            perna = _prisma(sec, 'yz', -ext, J[0])
            perna = perna - _prisma([(-4, -4), (40, 40), (-4, 40)], 'xy', -20, 20)
        else:
            perna = _prisma(sec, 'xz', -ext, J[1])
            perna = perna - _prisma([(-4, -4), (40, -4), (40, 40)], 'xy', -20, 20)
        corpo = perna if corpo is None else corpo + perna
    if not all(cunha):
        # a leg without the corner wedge ends flush with its outer line: trim the other leg's wedge past it
        corpo = corpo - _caixa((-4, 0), (-4, 0), (-20, 20))
    # the scarf at each leg's end: the middle's top passes joint_scarf over it
    rec = T + v['cover_recess']
    corte = [(J[0], rec), (J[0] + 1, rec), (J[0] + 1, top + 2), (J[0] - js - 2, top + 2)]
    corpo = corpo - _prisma(corte, 'xz', -30, 30)
    corte = [(J[1], rec), (J[1] + 1, rec), (J[1] + 1, top + 2), (J[1] - js - 2, top + 2)]
    corpo = corpo - _prisma(corte, 'yz', -30, 30)
    # the fin, from where the edge's clips started to the leg's end
    farpa = nome in config.CANTOS_FARPA
    for i, leg in enumerate('AB'):
        u0 = perfis.evaluate(pernas[i][3], v)
        for pol in aletas(v, farpa):
            sec = [(fs / 2 - s, d) for s, d in pol]
            corpo = corpo + (_prisma(sec, 'yz', u0, J[0]) if leg == 'A' else _prisma(sec, 'xz', u0, J[1]))
    pega = mapa.PEGA.get(nome)
    if pega:
        corpo = _pega(corpo, v, pega)
    if nome in mapa.DOBRADICA:
        corpo = _dobradica(corpo, v, nome)
    corpo = _solido(corpo)
    corpo, feitas, falhas = chanfro_mesa(corpo, 'z', top, v['bed_chamfer'], so_contorno=True)
    return dict(peca=corpo, suporte=suporte_canto(v, J, corpo), comprimento=J, chanfro=(feitas, falhas), farpa=farpa, v=v)


def _pega(corpo, v, leg):
    """construir._grip: near the corner the outer chamfer filled up into a lip, and under it a pocket with a 45 deg
    roof cut into the outer face, for a fingertip to pull the panel with."""
    T = v['panel_frame_spacing'] + v['panel_thickness']
    top = T + v['cover_height']
    cc, ww, gd, glc = v['cover_cut'], v['wall_width'], v['grip_depth'], v['grip_lip_chamfer']
    ch0 = top - cc
    end = v['grip_from'] + v['grip_length']
    lip_end = end + v['grip_lip_margin']
    roof = top - glc
    gf_ = v['grip_from']

    def secao(pts, comprimento):            # (w, d) along the leg, from the corner
        return _prisma(pts, 'yz', 0, comprimento) if leg == 'A' else _prisma(pts, 'xz', 0, comprimento)

    def lado(pts):                          # (u, d), across the leg
        return _prisma(pts, 'xz', -20, 20) if leg == 'A' else _prisma(pts, 'yz', -20, 20)

    def topo(pts):                          # (u, w), through the height
        return _prisma(pts if leg == 'A' else [(w, u) for u, w in pts], 'xy', -20, 20)
    labio = secao([(0, ch0 - 0.5), (0, roof), (glc, top), (cc + 0.5, top)], lip_end + cc + 1) & \
        lado([(0, ch0 - 0.5), (0, ch0), (cc, top), (lip_end, top), (lip_end + cc + 0.5, ch0 - 0.5)])
    rebaixo = secao([(-1, ww), (gd / 2, ww), (gd, ww + gd / 2), (gd, roof - gd), (0, roof), (-1, roof)], end + 2) & \
        topo([(gf_ - 1, -1), (end + 1, -1), (end - gd - 0.5, gd + 0.5), (gf_ + gd + 0.5, gd + 0.5)])
    return corpo + labio - rebaixo


def _dobradica(corpo, v, nome):
    """construir._hinge for a side corner (no-lateral): the knuckle from the corner over hinge_side_len, the screw's
    hole along it with the head's counterbore at the corner end, and the wedge cut away where the door's knuckle sits."""
    _, leg, no = mapa.DOBRADICA[nome]
    if no != 'no-lateral':
        raise ValueError(f'{nome}: só o nó da lateral está portado')
    fs = v['frame_size']
    sec = [(fs / 2 - s, d) for s, d in _avaliar(perfis.NO_LATERAL, v)]
    L = v['hinge_side_len']
    corpo = corpo + (_prisma(sec, 'yz', 0, L) if leg == 'A' else _prisma(sec, 'xz', 0, L))
    pin_s, pin_d = (perfis.evaluate(e, v) for e in perfis.PINO_LATERAL)
    w = fs / 2 - pin_s
    eixo = 'x' if leg == 'A' else 'y'
    corpo = corpo - _cilindro(eixo, (w, pin_d), v['hinge_hole_side'], -1, L + 1)
    corpo = corpo - _cilindro(eixo, (w, pin_d), v['hinge_head_d'], -1, v['hinge_head_depth'])
    door_end = v['hinge_side_len'] + v['hinge_gap'] + v['hinge_door_len']
    a, b = v['hinge_side_len'], door_end + v['door_pin_s'] - fs / 2 + 1
    pts = [(a, -3), (b, -3), (b, 0), (a, 0)]
    return corpo - _prisma(pts if leg == 'A' else [(w_, u) for u, w_ in pts], 'xy', -20, 20)


def suporte_canto(v, J, peca=None):
    """suporte_meio along the corner's inner L: the wall in front of the cover's inner edge on both legs, past both
    leg ends, and the laminas from its top to the base's edges and ends (the base ends at each leg's end). With the
    piece, the laminas' second layer (_lamina_topo)."""
    T, top = v['panel_frame_spacing'] + v['panel_thickness'], v['panel_frame_spacing'] + v['panel_thickness'] + v['cover_height']
    fs = v['frame_size']
    ceil, lam = T - v['peca_unica_vao'], v['suporte_lamina']
    gf, pw = v['suporte_folga'], v['suporte_parede']
    w_in = fs / 2 + (fs / 2 + v['cover_overlap'])                        # the cover's inner edge, in from the outer line
    ws = (w_in + gf, w_in + gf + pw)
    w_stop = fs / 2 - (-v['slot_opening'] / 2 + v['panel_edge_clearance'])
    w_base = fs / 2 + (fs / 2 - v['base_inset'])
    ja, jb = J[0] + gf + pw, J[1] + gf + pw
    caixas = [((ws[0], ja), ws, (ceil, top)), (ws, (ws[0], jb), (ceil, top)),
              ((J[0] + gf, ja), (w_stop, ws[1]), (ceil, top)), ((w_stop, ws[1]), (J[1] + gf, jb), (ceil, top)),
              ((w_base, ja), (w_base, ws[1]), (ceil - lam, ceil)), ((w_base, ws[1]), (w_base, jb), (ceil - lam, ceil)),
              ((J[0], ja), (w_stop, ws[1]), (ceil - lam, ceil)), ((w_stop, ws[1]), (J[1], jb), (ceil - lam, ceil))]
    out = None
    for c in caixas:
        out = _caixa(*c) if out is None else out + _caixa(*c)
    if peca is not None:
        out = out + _lamina_topo(v, [c for c in caixas if c[2] == (ceil - lam, ceil)], peca, 2)
    return _solido(out)


# ---------------------------------------------------------------- a face
def pecas_da_face(nome):
    """The face's one-piece pieces in place: list of dict(nome, tipo 'meio' or 'canto', borda, local, quadro), quadro
    (origin, x, y, z) the piece frame's placement (bordas.colocacoes), local the name built (a mirrored middle shares
    its frame with the normal one)."""
    v = valores()
    f = next(x for x in mapa.faces(v) if x['nome'] == nome)
    bordas = {e['nome']: e for e in f['bordas']}
    comp = {n: perfis.evaluate(e, v) for n, (_, e) in mapa.PECAS.items()}
    out = []
    for peca, o, x, y, z, borda in mapa.colocacoes(v, comp, f):
        if peca in mapa.MEIOS:
            espelho = bordas[borda]['eixo'] == 'Z' and z[2] > 0
            out.append(dict(nome=mapa.MEIOS[peca] + ('-espelho' if espelho else ''), tipo='meio', borda=borda, quadro=(o, x, y, z),
                            comprimento=comp[peca], espelho=espelho, cunha=mapa.PECAS[peca][0] != 'tampa-base'))
        elif borda == 'canto':
            out.append(dict(nome=peca, tipo='canto', borda=borda, quadro=(o, x, y, z)))
    return out


def construir_face(nome):
    """Build every piece of the face (each distinct one once): name -> dict(peca, suporte, ...), in its own frame."""
    feitas = {}
    for p in pecas_da_face(nome):
        if p['nome'] in feitas:
            continue
        t = time.time()
        if p['tipo'] == 'meio':
            r = meio(p['comprimento'], p['cunha'], lisa=config.PERNA_LISA)
            if p['espelho']:
                plano = bd.Plane.XY.offset(r['comprimento'] / 2)
                r['peca'], r['suporte'] = (_solido(bd.mirror(r[k], plano)) for k in ('peca', 'suporte'))
        else:
            r = canto(p['nome'])
        r['tempo'] = time.time() - t
        feitas[p['nome']] = r
    return feitas


def _local(quadro):
    o, x, _, z = quadro
    return bd.Location(bd.Plane(origin=o, x_dir=x, z_dir=z))


def _mover(shape, quadro, ds=0.0):
    """shape from its piece frame to the machine, moved ds along its x (a middle's s: out, to go in past the lip)."""
    if ds:
        shape = bd.Pos(ds, 0, 0) * shape
    return shape.moved(_local(quadro))


ENTRANDO = (0.5, 2.0, 4.0)   # mm out of the frame, going in straight (lock v8)


def _vol(a, b):
    x = a & b
    return 0.0 if x is None else sum(s.volume for s in x.solids())


# ---------------------------------------------------------------- checks
def perfil_2020():
    """The Misumi 2020 section (referencia/misumi_2020.json) centred on the member's axis, its four lips opened from
    the CAD's 6.0 to the user's measured slot_opening (6.35)."""
    perfil = json.load(open(os.path.join(HERE, MAQUINA, 'referencia', 'misumi_2020.json')))['loops'][0]
    perfil = [(u, w + 10.0) for u, w in perfil]
    so = valores()['slot_opening'] / 2

    def abre(a, b):
        return (math.copysign(so, a), b) if abs(abs(a) - 3.0) < 1e-6 and 8.0 - 1e-6 <= abs(b) <= 10.0 + 1e-6 else (a, b)
    perfil = [abre(u, w) for u, w in perfil]
    return [(b, a) for a, b in (abre(w, u) for u, w in perfil)]


def frame_face(nome):
    """The face's frame members (referencia/frame_350.json) as extrusions of the Misumi 2020 section
    (referencia/misumi_2020.json): the ones whose outer face lies on the face's plane."""
    ref = os.path.join(HERE, MAQUINA, 'referencia')
    perfil = perfil_2020()
    v = valores()
    f = next(x for x in mapa.faces(v) if x['nome'] == nome)
    n = f['n']
    k = [abs(c) for c in n].index(1)
    if k == 2:
        plano = v['frame_z0'] + (v['body_height'] if n[2] > 0 else 0.0)
    else:
        plano = n[k] * (v['frame_width'] if k == 0 else v['frame_depth']) / 2
    out = []
    for m in json.load(open(os.path.join(ref, 'frame_350.json')))['membros']:
        bb = m['bb']
        if abs(bb[k + 3 * (n[k] > 0)] - plano) > 1e-6:
            continue
        a = 'XYZ'.index(m['eixo'])
        c = [(bb[i] + bb[i + 3]) / 2 for i in range(3)]
        i, j = [q for q in range(3) if q != a]
        eixos = 'xyz'[i] + 'xyz'[j]
        out.append((m['nome'], _prisma([(c[i] + u, c[j] + w) for u, w in perfil], eixos, bb[a], bb[a + 3])))
    return out


def cunhas_vizinhas(nome):
    """The other faces' covers' wedges past this face's corners, along the edges with another face (every edge but
    mapa.BORDAS_SEM_VIZINHO): the Trident's _WEDGE seen from this face, the triangle (10, 0) (11.5, 1.5) (13, 0) in
    (s, d), along the whole edge."""
    v = valores()
    f = next(x for x in mapa.faces(v) if x['nome'] == nome)
    fs, ww = v['frame_size'], v['wall_width']
    tri = [(fs / 2, 0.0), (fs / 2 + ww / 2, ww / 2), (fs / 2 + ww, 0.0)]
    out = []
    for e in f['bordas']:
        if e['nome'] in mapa.BORDAS_SEM_VIZINHO:
            continue
        k = 'XYZ'.index(e['eixo'])
        n, a = f['n'], e['a']
        t = bd.Vector(*a).cross(bd.Vector(*n))
        o = list(e['ponto'])
        o[k] = v['frame_z0'] + v['body_height'] / 2 if k == 2 else 0.0      # the edge's middle, the prism past both ends
        L = max(v['frame_width'], v['frame_depth'], v['body_height'])
        out.append((e['nome'], _prisma(tri, 'xy', -L, L).moved(bd.Location(bd.Plane(origin=tuple(o), x_dir=a, z_dir=(t.X, t.Y, t.Z))))))
    return out


def conferir(nome, feitas):
    """Interference of the face's pieces in place (mm³): with each other and with the frame, locked and with each middle
    moved out to go in; the middles with the other faces' wedges (cunhas_vizinhas: the corners don't move, and by the
    door's hinge its wedge is cut away for the side's knuckle), in place and going in (mapa: with that face already on,
    a middle going in meets its wedge; the user: not a problem there); and the lock's travel in one middle (the final
    slider and cap, their Fusion STEPs, in the coupon's frame). config.PERNA_LISA (lock v8): every piece goes in
    straight with the panel, out along the face's normal by ENTRANDO (the worst one counts; the pieces don't move
    against each other), and the lock is v8's (conferir_v8, with the frame member under the middle)."""
    lista = pecas_da_face(nome)
    frame = frame_face(nome)
    cunhas = cunhas_vizinhas(nome)
    vt = valores_trava()
    lisa = config.PERNA_LISA
    entra = vt['peca_unica_gancho'] + vt['peca_unica_gancho_folga']
    # one key per place (a face can repeat a piece: the top's four middles and corners)
    chave = {id(p): f"{p['nome']} ({p['borda']})" if p['tipo'] == 'meio' else f"{p['nome']} ({i + 1})" for i, p in enumerate(lista)}
    no_lugar = {chave[id(p)]: _mover(feitas[p['nome']]['peca'], p['quadro']) for p in lista}
    meios = {chave[id(p)] for p in lista if p['tipo'] == 'meio'}
    if lisa:
        nf = next(x for x in mapa.faces(valores()) if x['nome'] == nome)['n']
        aberto = {n: [bd.Pos(*(k * c for c in nf)) * s for k in ENTRANDO] for n, s in no_lugar.items()}
    else:
        aberto = {chave[id(p)]: [_mover(feitas[p['nome']]['peca'], p['quadro'], entra)] for p in lista if p['tipo'] == 'meio'}
    res = {'frame': {}, 'frame_entrando': {}, 'cunhas': {}, 'cunhas_entrando': {}, 'entre_pecas': {}, 'entre_pecas_entrando': {}, 'curso': {}}
    for n in no_lugar:
        res['frame'][n] = round(sum(_vol(no_lugar[n], m) for _, m in frame), 3)
        if n in aberto:
            res['frame_entrando'][n] = round(max(sum(_vol(a, m) for _, m in frame) for a in aberto[n]), 3)
        if n in meios:
            res['cunhas'][n] = round(sum(_vol(no_lugar[n], c) for _, c in cunhas), 3)
            res['cunhas_entrando'][n] = round(max(sum(_vol(a, c) for _, c in cunhas) for a in aberto[n]), 3)
    nomes = list(no_lugar)
    for i, a in enumerate(nomes):
        for b in nomes[i + 1:]:
            res['entre_pecas'][f'{a} × {b}'] = round(_vol(no_lugar[a], no_lugar[b]), 3)
            for x, y in ((a, b), (b, a)):
                if x in aberto and not lisa:
                    res['entre_pecas_entrando'][f'{x} (entrando) × {y}'] = round(_vol(aberto[x][0], no_lugar[y]), 3)
    # the lock's travel, in the first normal middle's own frame (the lock coupon's, moved by desloc)
    m = next(p for p in lista if p['tipo'] == 'meio' and not p['espelho'])
    r = feitas[m['nome']]
    res['curso_meio'] = m['nome']
    if lisa:
        del res['entre_pecas_entrando'], res['curso']
        cursor, capa, queda = trava_v8()
        res['trava'] = {'queda': queda, **conferir_v8(r, {config.CURSOR_V8: dict(cursor=cursor)}, capa, queda,
                                                      fr=frame_cupom(-10.0, r['comprimento'] + 10.0), z=r['desloc'])}
        return res
    cursor = _solido(bd.import_step(os.path.join(V7, 'trava-cursor-final.step')))
    capa = _solido(bd.import_step(os.path.join(V7, 'trava-capa-final.step')))
    c = r['g']['c']
    for i in range(int(round(c)) + 1):
        dz = r['desloc'] + c * i / round(c)
        res['curso'][f'{i * c / round(c):.0f} mm'] = (round(_vol(r['peca'], bd.Pos(0, 0, dz) * cursor), 3),
                                                     round(_vol(r['peca'], bd.Pos(0, 0, dz) * capa), 3))
    return res


# ---------------------------------------------------------------- export
def _deitada(shape, tipo, top):
    """The piece as it prints, the outer face (d = top) at Z = 0: a middle's (s, d, z) -> (z, -s, top - d), as
    construir.peca_unica_exportar; a corner's (x, y, d) -> (x, -y, top - d)."""
    if tipo == 'meio':
        plano = bd.Plane(origin=(0, 0, top), x_dir=(0, -1, 0), z_dir=(1, 0, 0))
    else:
        plano = bd.Plane(origin=(0, 0, top), x_dir=(1, 0, 0), z_dir=(0, 0, -1))
    return shape.moved(bd.Location(plano))


def _stl_espelho(origem, destino):
    """A binary STL mirrored in X (the lock's slider and cap for a mirrored middle): x -> -x, each facet's order turned."""
    with open(origem, 'rb') as fh:
        dados = fh.read()
    n = struct.unpack('<I', dados[80:84])[0]
    out = bytearray(dados[:84])
    for i in range(n):
        reg = dados[84 + 50 * i: 134 + 50 * i]
        f = list(struct.unpack('<12f', reg[:48]))
        f[0], f[3], f[6], f[9] = -f[0], -f[3], -f[6], -f[9]
        f[6:9], f[9:12] = f[9:12], f[6:9]
        out += struct.pack('<12f', *f) + reg[48:50]
    with open(destino, 'wb') as fh:
        fh.write(out)


def exportar(nome, feitas, pasta):
    """Each piece as it prints (piece and support in one body, lying, outer face at Z = 0), a STEP of each with the two
    bodies apart, the lock's parts (the final slider and cap of v7, mirrored where a middle is, the v5 disc; with
    config.PERNA_LISA the slider config.CURSOR_V8 of kit v8), and quantidades.json."""
    os.makedirs(pasta, exist_ok=True)
    lista = pecas_da_face(nome)
    qtd = {}
    for p in lista:
        qtd[p['nome']] = qtd.get(p['nome'], 0) + 1
    top = valores()['panel_frame_spacing'] + valores()['panel_thickness'] + valores()['cover_height']
    tipos = {p['nome']: p['tipo'] for p in lista}
    for n, r in feitas.items():
        junto = _deitada(_solido(r['peca'] + r['suporte']), tipos[n], top)
        bd.export_stl(junto, os.path.join(pasta, f'{n}-{qtd[n]}x.stl'), tolerance=0.005, angular_tolerance=0.1)
        peca, sup = _deitada(r['peca'], tipos[n], top), _deitada(r['suporte'], tipos[n], top)
        peca.label, sup.label = n, 'suporte'
        bd.export_step(bd.Compound([peca, sup]), os.path.join(pasta, f'{n}.step'))
    meios = [p for p in lista if p['tipo'] == 'meio']
    normais, espelhos = sum(not p['espelho'] for p in meios), sum(p['espelho'] for p in meios)
    for parte in ('cursor', 'capa'):
        stl = os.path.join(V7, f'trava-{parte}-final-2x.stl')
        if parte == 'cursor' and config.PERNA_LISA:
            stl = os.path.join(V8, f'trava-cursor-{config.CURSOR_V8}-1x.stl')
        if normais:
            with open(stl, 'rb') as a, open(os.path.join(pasta, f'trava-{parte}-{normais}x.stl'), 'wb') as b:
                b.write(a.read())
            qtd[f'trava-{parte}'] = normais
        if espelhos:
            _stl_espelho(stl, os.path.join(pasta, f'trava-{parte}-espelho-{espelhos}x.stl'))
            qtd[f'trava-{parte}-espelho'] = espelhos
    with open(DISCO, 'rb') as a, open(os.path.join(pasta, f'trava-indicador-{len(meios)}x.stl'), 'wb') as b:
        b.write(a.read())
    qtd['trava-indicador'] = len(meios)
    with open(os.path.join(pasta, 'quantidades.json'), 'w') as fh:
        json.dump(dict(sorted(qtd.items())), fh, indent=1, ensure_ascii=False)
    return qtd


# ---------------------------------------------------------------- lock v8: the hook on the slider
V8 = os.path.join(REPO, 'stl', 'trident-provas-peca-unica-trava-v8')
FOLGA_FUNDO = 0.3


def _cursor_v7():
    return _solido(bd.import_step(os.path.join(V7, 'trava-cursor-final.step')))


def _capa_v7():
    return _solido(bd.import_step(os.path.join(V7, 'trava-capa-final.step')))


def folga_encaixe(cursor, capa, passo=0.01):
    """How far the cap lifts off the stub's top before its lips catch the stub's flares (its socket's play along d),
    against what they share where they sit (the slider's printing tab through the cap)."""
    base, d = _vol(cursor, capa), 0.0
    while _vol(cursor, bd.Pos(0, d + passo, 0) * capa) <= base + 1e-4:
        d += passo
    return round(d, 3)


def cursor_gancho(aperto, marcas, queda):
    """Lock v8's slider: v7's final one (its STEP: the coupon's frame, open) with peca_unica_gancho of hook on the
    tongue's outer face, under the outer lip once the leg's ramp has pushed it out: 45 deg slopes above and below and
    0.5 straight between them, as the piece's hook was. Its top slope passes the lip's corner queda + aperto above it,
    so it pulls the slider down queda (the cap onto the cover, then its socket onto the stub's flares) and aperto is
    left squeezed. The tongue's inner front corner at 45 deg, as the leg's ramp. On the stub, v7's 2 grooves filled
    and marcas cut in their place, 1.5 apart (3 fit on the stub's foot)."""
    v = valores_trava()
    g = geometria_trava.geo(v)
    so, G, lip, r = g['so'], v['peca_unica_gancho'], v['slot_lip'], boia(v)
    wl, wr = g['lingueta']
    z0, zl = g['z0'], g['z0'] + g['lk']
    t = -lip + queda + aperto
    cur = _cursor_v7()
    # the hook, from 0.5 inside the tongue, its slopes through (wr, t) and (wr, t - 2G - 0.5)
    # (its rear end, on the bed, with the joint's bed chamfer, 0.2: v7's edges there already have theirs)
    e = 0.5
    gancho = _prisma([(wr - e, t + e), (so + G, t - G), (so + G, t - G - 0.5), (wr - e, t - 2 * G - 0.5 - e)], 'xy', z0, zl)
    gancho = bd.chamfer(gancho.edges().filter_by_position(bd.Axis.Z, z0 - 1e-3, z0 + 1e-3), v['trava_chanfro_encaixe'])
    cur = cur + gancho
    cur = cur - _prisma([(wl - 1, zl - r - 1), (wl + r + 1, zl + 1), (wl - 1, zl + 1)], 'xz', -v['slot_depth'] - 1, 0.0)
    # the keel: the slot's floor only pushes up, so below the hook it keeps clear of the cavity by the drop and
    # FOLGA_FUNDO (the lying piece prints up to 0.15 thin, and the slider then goes that much further down)
    fundo = frame_cupom().moved(bd.Location((0, queda + FOLGA_FUNDO, 0))) & _caixa((-10, 10), (-20, t - 2 * G - 1.0), (-10, 60))
    cur = cur - fundo
    gap, th = g['gap'], v['trava_toco_altura']
    sf = g['wo'] - g['tl'] + g['fh']
    gd = min(0.6, (g['tl'] - 2 * g['fh']) / 3)
    v7 = config.TRAVA_MARCAS.get(config.TRAVA, 0)
    for i in range(v7):
        zm = g['zc'] + (i - (v7 - 1) / 2) * 2.0
        cur = cur + _caixa((sf, sf + gd + 0.01), (gap, gap + th), (zm - 0.5, zm + 0.5))
    zc = (g['tz'][0] + g['tz'][1]) / 2
    for i in range(marcas):
        zm = zc + (i - (marcas - 1) / 2) * 1.5
        cur = cur - _caixa((sf - 1, sf + gd), (gap, gap + th + 1), (zm - 0.5, zm + 0.5))
    return dict(cursor=_solido(cur), t=t)


def trava_v8():
    """The faces' lock since v8: the slider config.CURSOR_V8 (its STEP from the kit), v7's cap, and how far the slider
    drops to lock (the cap onto the cover, then its socket onto the stub)."""
    capa = _capa_v7()
    queda = round(valores_trava()['trava_folga_capa'] + folga_encaixe(_cursor_v7(), capa), 3)
    return _solido(bd.import_step(os.path.join(V8, f'trava-cursor-{config.CURSOR_V8}.step'))), capa, queda


def frame_cupom(a=-10.0, b=60.0):
    """A 2020 member under the coupon, in its frame: the slot centred at s = 0, the outer face at d = 0."""
    return _prisma([(u, w - 10.0) for u, w in perfil_2020()], 'xy', a, b)


def conferir_v8(r, cursores, capa, queda, fr=None, z=0.0):
    """Lock v8 in the coupon's frame (mm³). The piece in place and going in straight; each slider open (floated in,
    boia), going in with the piece, along its travel (the ramp pushing it out after the window's clearance) and
    locked (down queda: then only the hook's squeeze meets the lip); the cap open and locked (on the cover).
    fr: the frame member under the piece (the coupon's by default); z: where the lock's frame starts along it (a
    middle's desloc)."""
    v, g = r['v'], r['g']
    fr = frame_cupom() if fr is None else fr
    peca, c, b = r['peca'], g['c'], boia(r['v'])
    fj = v['trava_folga_janela']
    res = {'peca × frame': round(_vol(peca, fr), 3),
           'peca entrando × frame': {f'+{k}': round(_vol(bd.Pos(0, k, 0) * peca, fr), 3) for k in (0.5, 1, 2, 4, 6)}}
    m = lambda s, x, y=0.0, w=0.0: bd.Pos(x, y, z + w) * s  # noqa: E731
    for n, cu in cursores.items():
        k = cu['cursor']
        o = res[n] = {}
        o['aberto × frame'] = round(_vol(m(k, -b), fr), 3)
        o['aberto × peça'] = round(_vol(m(k, -b), peca), 3)
        o['entrando × frame'] = {f'+{e}': round(_vol(m(k, -b, e), fr), 3) for e in (0.5, 1, 2, 4, 6)}
        o['curso × peça'] = {}
        for i in range(int(c * 4) + 1):
            dz = i / 4
            ds = -b + min(max(dz - fj, 0.0), b)
            o['curso × peça'][f'{dz:.2f}'] = round(_vol(m(k, ds, 0.0, dz), peca), 3)
        o['travado × frame (o aperto do gancho)'] = round(_vol(m(k, 0.0, -queda, c), fr), 3)
        o['travado × peça'] = round(_vol(m(k, 0.0, -queda, c), peca), 3)
        o['travado × capa (a orelha do cursor passa por ela)'] = round(_vol(m(k, 0.0, -queda, c), m(capa, 0.0, -v['trava_folga_capa'], c)), 3)
    res['capa aberta × peça'] = round(_vol(m(capa, -b), peca), 3)
    res['capa travada × peça'] = round(_vol(m(capa, 0.0, -v['trava_folga_capa'], c), peca), 3)
    return res


def kit_v8(pasta=V8):
    """Lock v8's test kit: the coupon with the plain leg, the three sliders of config.GANCHO_CURSOR, checked, exported
    (the piece lying with its support, the sliders as v7's on their rear end, STEPs; v7's cap is reused)."""
    t0 = time.time()
    r = meio(None, cupom=True, lisa=True)
    capa = _capa_v7()
    queda = round(r['v']['trava_folga_capa'] + folga_encaixe(_cursor_v7(), capa), 3)
    cursores = {n: cursor_gancho(a, mk, queda) for n, (a, mk) in config.GANCHO_CURSOR.items()}
    res = {'queda': queda, 'chanfro_peca': r['chanfro'],
           'gancho_topo': {n: round(c['t'], 3) for n, c in cursores.items()}, **conferir_v8(r, cursores, capa, queda)}
    os.makedirs(pasta, exist_ok=True)
    with open(os.path.join(pasta, 'conferencia.json'), 'w') as fh:
        json.dump(res, fh, indent=1, ensure_ascii=False)
    top = r['g']['top']
    nome = 'peca-unica-perna-lisa'
    bd.export_stl(_deitada(_solido(r['peca'] + r['suporte']), 'meio', top), os.path.join(pasta, f'{nome}-1x.stl'),
                  tolerance=0.005, angular_tolerance=0.1)
    peca, sup = _deitada(r['peca'], 'meio', top), _deitada(r['suporte'], 'meio', top)
    peca.label, sup.label = nome, 'suporte'
    bd.export_step(bd.Compound([peca, sup]), os.path.join(pasta, f'{nome}.step'))
    qtd = {nome: 1}
    for n, c in cursores.items():
        bd.export_stl(c['cursor'], os.path.join(pasta, f'trava-cursor-{n}-1x.stl'), tolerance=0.002, angular_tolerance=0.1)
        bd.export_step(c['cursor'], os.path.join(pasta, f'trava-cursor-{n}.step'))
        qtd[f'trava-cursor-{n}'] = 1
    with open(os.path.join(pasta, 'quantidades.json'), 'w') as fh:
        json.dump(qtd, fh, indent=1, ensure_ascii=False)
    print(json.dumps(res, indent=1, ensure_ascii=False))
    print(f'{pasta}: {qtd}; {time.time() - t0:.0f} s')
    return r, cursores, res


V9 = os.path.join(REPO, 'stl', 'trident-provas-peca-unica-trava-v9')


def kit_v9(pasta=V9):
    """Thinner sliders for lock v8 (config.GANCHO_CURSOR_V9): only the sliders, checked on v8's coupon as kit v8, with
    the faces' gancho-020 (its kit STEP) alongside to compare the squeeze; the piece and v7's cap are reused."""
    t0 = time.time()
    r = meio(None, cupom=True, lisa=True)
    capa = _capa_v7()
    queda = round(r['v']['trava_folga_capa'] + folga_encaixe(_cursor_v7(), capa), 3)
    cursores = {n: cursor_gancho(a, mk, queda) for n, (a, mk) in config.GANCHO_CURSOR_V9.items()}
    v8 = _solido(bd.import_step(os.path.join(V8, f'trava-cursor-{config.CURSOR_V8}.step')))
    refeito = cursor_gancho(*config.GANCHO_CURSOR[config.CURSOR_V8], queda)['cursor']
    res = {'queda': queda, 'gancho_topo': {n: round(c['t'], 3) for n, c in cursores.items()},
           f'{config.CURSOR_V8} refeito × kit v8 (só aqui, só no kit, mm³)': (round(refeito.volume - _vol(refeito, v8), 4),
                                                                              round(v8.volume - _vol(v8, refeito), 4)),
           **conferir_v8(r, {**cursores, f'{config.CURSOR_V8} (o das faces)': dict(cursor=v8)}, capa, queda)}
    os.makedirs(pasta, exist_ok=True)
    with open(os.path.join(pasta, 'conferencia.json'), 'w') as fh:
        json.dump(res, fh, indent=1, ensure_ascii=False)
    qtd = {}
    for n, c in cursores.items():
        bd.export_stl(c['cursor'], os.path.join(pasta, f'trava-cursor-{n}-1x.stl'), tolerance=0.002, angular_tolerance=0.1)
        bd.export_step(c['cursor'], os.path.join(pasta, f'trava-cursor-{n}.step'))
        qtd[f'trava-cursor-{n}'] = 1
    with open(os.path.join(pasta, 'quantidades.json'), 'w') as fh:
        json.dump(qtd, fh, indent=1, ensure_ascii=False)
    print(json.dumps(res, indent=1, ensure_ascii=False))
    print(f'{pasta}: {qtd}; {time.time() - t0:.0f} s')
    return r, cursores, res


# ---------------------------------------------------------------- command line
def _cupom():
    r = meio(None, cupom=True)
    ref = sorted(bd.import_step(os.path.join(V6, f'peca-unica-trava-{config.PECA}.step')).solids(), key=lambda s: -s.volume)
    for n, a, b in (('peça', r['peca'], ref[0]), ('suporte', r['suporte'], ref[1])):
        print(f'{n}: build123d {a.volume:.3f} mm³, Fusion {b.volume:.3f}; só aqui {(a - b).volume:.4f}, só no Fusion {(b - a).volume:.4f}')


def main(args):
    if not args or args[0] == 'cupom':
        _cupom()
        return
    if args[0] == 'kit-v8':
        kit_v8(*args[1:])
        return
    if args[0] == 'kit-v9':
        kit_v9(*args[1:])
        return
    nome = args[0]
    versao = config.FACES_VERSAO
    pasta = args[1] if len(args) > 1 else os.path.join(REPO, 'stl', f'{config.STL_PREFIX}{nome}-v{versao}')
    t = time.time()
    feitas = construir_face(nome)
    for n, r in feitas.items():
        print(f'{n}: {r["peca"].volume:.0f} mm³ (+ suporte {r["suporte"].volume:.0f}), chanfro de mesa {r["chanfro"]}, {r["tempo"]:.1f} s')
    res = conferir(nome, feitas)
    conf = f'conferencia-{nome}.json' if versao == 1 else f'conferencia-{nome}-v{versao}.json'
    with open(os.path.join(REPO, 'gerador', MAQUINA, conf), 'w') as fh:
        json.dump(res, fh, indent=1, ensure_ascii=False)
    for k, d in res.items():
        if k == 'trava':
            print(f'trava: {json.dumps(d, ensure_ascii=False)}')
        elif isinstance(d, dict):
            nz = {a: b for a, b in d.items() if (b != 0.0 if not isinstance(b, tuple) else any(b))}
            print(f'{k}: {len(d)} casos, não zerados {nz if nz else "nenhum"}')
    qtd = exportar(nome, feitas, pasta)
    print(f'exportado em {pasta}: {qtd}; {time.time() - t:.0f} s')


if __name__ == '__main__':
    main(sys.argv[1:])
