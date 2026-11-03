"""The clip projects (clips under covers, corners in L) built in build123d instead of Fusion: machines v0, v0-trava,
trident and trident-trava (the user, 2026-11-02: "passa os projetos com clipes para o build123d? a versão com e sem
travas, v0 e trident"). The same parameter tables, profiles (perfis), maps (mapa, bordas, travas) and lock geometry
(geometria_trava) as construir.py, evaluated without Fusion; each function ports the construir step it names, in the
same frames, so a piece comes out where Fusion's does and its STL replaces Fusion's.

Frames, mm (bordas.py): a straight piece (x, y, z) = (s, d, along the edge); a corner (x, y, z) = (along leg A, along
leg B, d), its origin at the outer corner; the lock's slider, cap and disc in the lock coupon's (s, d, z), open.
The order of construir_tudo and of the lock machines' READMEs: a straight piece, then its handle or the logo's pocket,
then the lock's cuts, then the bed chamfer; a corner's legs, clips, core (canto_miolo), scarfs, grip (and its leg's
clips again), hinge, then the lock and the chamfer.

Run with the venv that has build123d (from the repository root):
  .venv-b3d/bin/python gerador/clips_b3d.py <máquina> pecas [nome ...]       build pieces (all, without names)
  .venv-b3d/bin/python gerador/clips_b3d.py <máquina> face <face> [pasta]    build a face, check it, export its pieces
                                                                              (stl/<prefixo><face>-b3d-v<n> by default)
  .venv-b3d/bin/python gerador/clips_b3d.py <máquina> conferir [face ...]   the checks (all faces, between faces, doors)
  .venv-b3d/bin/python gerador/clips_b3d.py <máquina> comparar <pasta>      each STL of a Fusion export against its port
Any of them takes --mudar nome=expressão (repeatable), the parameter changed (an older export's values).

Checked against every Fusion export of these machines and the components never exported (gerador/README.md): the same
pieces, but for the facets of the round holes in Fusion's STLs.
"""
import json
import math
import os
import re
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
import peca_unica_b3d as pu  # noqa: E402   (geometry helpers: _prisma, _caixa, _cilindro, _solido, chanfro_mesa, _pega)

MAQUINAS = ('v0', 'v0-trava', 'trident', 'trident-trava')
FRAME = 'frame'


def valores(params, mudancas=None):
    """The parameter table evaluated with some expressions changed (construir._vals_with)."""
    mudancas = mudancas or {}
    vals, late = {}, {}
    for _, n, e, _, _ in params:
        if n in mudancas:
            try:
                vals[n] = perfis.evaluate(mudancas[n], vals)
                continue
            except NameError:
                late[n] = mudancas[n]
        vals[n] = perfis.evaluate(e, vals)
    for n, e in list(late.items()) + [(n, e) for n, e in mudancas.items() if n not in vals]:
        vals[n] = perfis.evaluate(e, vals)
    return vals


class Maquina:
    """A machine folder (config, parametros, mapa) with its values and the pieces built so far."""

    def __init__(self, nome, mudancas=None):
        if nome not in MAQUINAS:
            raise ValueError(f'máquina {nome!r}: use uma de {MAQUINAS}')
        self.nome = nome
        self.dir = os.path.join(HERE, nome)
        self.config, self.parametros, self.mapa = (herdar.de(nome, a) for a in ('config', 'parametros', 'mapa'))
        self.mudancas = dict(mudancas or {})
        self.v = valores(self.parametros.PARAMS, self.mudancas)
        self.feitas = {}
        self._quadros = None

    def ref(self, arquivo):
        return os.path.join(self.dir, 'referencia', arquivo)

    def ev(self, expr, v=None):
        return perfis.evaluate(expr, self.v if v is None else v) if isinstance(expr, str) else float(expr)

    def vals(self, mudancas):
        return valores(self.parametros.PARAMS, {**self.mudancas, **mudancas})

    @property
    def T(self):
        return self.v['panel_frame_spacing'] + self.v['panel_thickness']

    @property
    def top(self):
        return self.T + self.v['cover_height']

    def quadros(self):
        """Each lock piece's lock frame in its own coordinates (mapa.trava_pecas: travas.quadros); {} without locks."""
        if self._quadros is None:
            self._quadros = self.mapa.trava_pecas(self.v) if hasattr(self.mapa, 'trava_pecas') else {}
        return self._quadros


def poligono(m, nome, v=None):
    """A profile of perfis.PROFILES evaluated, repeated vertices dropped (a feature at 0 leaves them)."""
    v = m.v if v is None else v
    pts = [(perfis.evaluate(s, v), perfis.evaluate(d, v)) for s, d in perfis.PROFILES[nome]]
    return [p for i, p in enumerate(pts) if math.dist(p, pts[i - 1]) > 1e-6]


def _parede(m, nome, perfil):
    """construir._check_wall: refuse a split-fin clip whose leg wall is thinner than fin_min_wall."""
    if perfil not in perfis.SPLIT_FIN:
        return
    parede, minimo = perfis.leg_min_wall(perfil, m.v), m.v.get('fin_min_wall', 0.4)
    if parede < minimo - 0.005:
        raise RuntimeError(f'{nome}: parede da perna de {parede:.3f} mm, abaixo de fin_min_wall {minimo:.2f}')


# ---------------------------------------------------------------- straight pieces (construir.pecas)
def reta(m, nome):
    """A straight piece of mapa.PECAS: a clip as long as its run (the barb in stretches with fin_anchor_length), a
    cover middle joint_scarf longer at each end and cut there at 45 deg (the scarf joint), the rear middle's cover
    half (tampa-h) with its outer end along the vertical cover's inner chamfer."""
    perfil, comp = m.mapa.PECAS[nome]
    v, T = m.v, m.T
    L = m.ev(comp)
    _parede(m, nome, perfil)
    sec = poligono(m, perfil)
    if perfil == 'tampa-h':
        cc = v['cover_cut']
        corpo = pu._prisma(sec, 'xy', 0.0, L + cc + 1)
        ch0, top = T + v['cover_height'] - cc, T + v['cover_height'] + 1
        corpo = corpo - pu._prisma([(T - 1, L), (ch0, L), (top, L + top - ch0), (top, L + 10), (T - 1, L + 10)], 'yz', -30, 30)
    elif not perfil.startswith('tampa'):
        corpo = pu._prisma(sec, 'xy', 0.0, L)
        corpo = _trechos_farpa(m, corpo, perfil, L)
    else:
        js = v['joint_scarf']
        total = L + 2 * js
        corpo = pu._prisma(sec, 'xy', 0.0, total)
        rec, top = T + v['cover_recess'], T + v['cover_height'] + 2
        for pts in ([(-12, js), (rec, js), (top, -2), (-12, -2)],
                    [(-12, total - js), (rec, total - js), (top, total + 2), (-12, total + 2)]):
            corpo = corpo - pu._prisma(pts, 'yz', -30, 30)
    return pu._solido(corpo)


def _trechos_farpa(m, corpo, perfil, L):
    """construir._barb_stretches: with fin_anchor_length > 0 a split-fin clip keeps its barb only in stretches of
    that length, at most fin_anchor_gap apart (perfis.barb_cut between them)."""
    v = m.v
    a, g = v.get('fin_anchor_length', 0.0), v.get('fin_anchor_gap', 0.0)
    if perfil not in perfis.SPLIT_FIN or a <= 0 or L <= 2 * a:
        return corpo
    n = max(2, math.ceil((L + g) / (a + g) - 1e-9))
    passo = (L - a) / (n - 1)
    trechos = [(i * passo, i * passo + a) for i in range(n)]
    corte = [(perfis.evaluate(s, v), perfis.evaluate(d, v)) for s, d in perfis.barb_cut()]
    for (_, z0), (z1, _) in zip(trechos, trechos[1:]):
        for lado in (1, -1):
            corpo = corpo - pu._prisma([(lado * s, d) for s, d in corte], 'xy', z0, z1)
    return corpo


def puxador(m, corpo, nome):
    """construir.puxador on a straight cover: the ledge (the chamfer on one edge filled up and carried past it, the
    plan with its tapers) and the V groove on top, centred on the piece. config.PUXADOR's side: 'fora' past the frame
    edge (V0), 'dentro' past the cover's inner edge (the Trident's doors)."""
    _, lado = getattr(m.config, 'PUXADOR', ('tampa-parede-v-puxador', 'fora'))
    v = m.v
    L = m.ev(m.mapa.PECAS[nome][1])
    total = L + 2 * v['joint_scarf']
    zc = total / 2
    top = m.top
    ch0 = top - v['cover_cut']
    e, hr, cc = v['handle_edge_chamfer'], v['handle_reach'], v['cover_cut']
    half, hl = v['handle_length'] / 2 + v['handle_taper'], v['handle_length']
    if lado == 'fora':
        S = lambda u: v['frame_size'] / 2 + u                                   # noqa: E731
    else:
        S = lambda u: -(v['frame_size'] / 2 + v['cover_overlap']) - u          # noqa: E731
    sec = [(S(-(cc + 0.5)), top), (S(hr - e), top), (S(hr), top - e), (S(hr), ch0 + e), (S(hr - e), ch0), (S(0), ch0),
           (S(0), ch0 - 0.5), (S(-0.5), ch0 - 0.5)]
    plan = [(S(-(cc + 1)), zc - half), (S(0), zc - half), (S(hr), zc - hl / 2), (S(hr), zc + hl / 2), (S(0), zc + half),
            (S(-(cc + 1)), zc + half)]
    corpo = corpo + (pu._prisma(sec, 'xy', 0.0, total) & pu._prisma(plan, 'xz', -20, 20))
    g, gw = v['handle_groove_s'], v['handle_groove_width'] / 2
    sulco = [(g - gw, top + 1), (g - gw, top), (g, top - v['handle_groove_depth']), (g + gw, top), (g + gw, top + 1)]
    gl = v['handle_groove_length']
    return corpo - pu._prisma(sulco, 'xy', zc - gl / 2, zc + gl / 2)


def _logo_face(m, nome, y):
    """The logo's region (referencia LOGO_JSON: the hexagon less its three cuts) at height y in the cover's frame,
    centred on the cover middle nome."""
    data = json.load(open(m.ref(m.config.LOGO_JSON)))
    centro = (m.ev(m.mapa.PECAS[nome][1]) + 2 * m.v['joint_scarf']) / 2

    def fio(lp):
        return bd.Wire.make_polygon([bd.Vector(s, y, centro + a) for s, a in lp], close=True)
    return bd.Face(fio(data['externo']), [fio(f) for f in data['furos']]), data['espessura']


def logo(m, nome='tampa-parede-h-logo'):
    """construir.logo: the Voron logo, logo_thickness on the cover's outer face, in the cover's frame."""
    face, esp = _logo_face(m, nome, m.top - json.load(open(m.ref(m.config.LOGO_JSON)))['espessura'])
    return pu._solido(bd.extrude(face, amount=esp, dir=(0, 1, 0)))


def bolso_logo(m, corpo, nome='tampa-parede-h-logo'):
    """The logo's pocket in its cover, 0.01 past the outer face."""
    face, esp = _logo_face(m, nome, m.top - json.load(open(m.ref(m.config.LOGO_JSON)))['espessura'])
    return corpo - bd.extrude(face, amount=esp + 0.01, dir=(0, 1, 0))


def passa_bowden(m):
    """construir.passa_bowden (the Trident): the plug for the rear sheet's exhaust notch, its outer plate, the fitting's
    hole; in the rear top edge's frame."""
    v = m.v
    so, c, ch = v['slot_opening'] / 2, v['bowden_plug_clearance'], v['bowden_plate_chamfer']
    fundo = -(so + v['exhaust_notch_depth'])
    s0, s1, hw = fundo + c, -(so + c), v['exhaust_notch_width'] / 2 - c
    tampao = [(s1, -hw), (s1, hw), (s0 + ch, hw), (s0, hw - ch), (s0, -(hw - ch)), (s0 + ch, -hw)]
    pfs = v['panel_frame_spacing']
    corpo = pu._prisma(tampao, 'xz', pfs, pfs + v['panel_thickness'])
    p0, p1 = fundo - v['bowden_plate_overlap'], -(v['frame_size'] / 2 + v['cover_overlap'] + v['bowden_cover_gap'])
    pw = v['exhaust_notch_width'] / 2 + v['bowden_plate_overlap']
    aba = [(p1 - ch, -pw), (p1, -(pw - ch)), (p1, pw - ch), (p1 - ch, pw), (p0 + ch, pw), (p0, pw - ch), (p0, -(pw - ch)),
           (p0 + ch, -pw)]
    corpo = corpo + pu._prisma(aba, 'xz', m.T, m.T + v['bowden_plate_thickness'])
    corpo = corpo - pu._cilindro('y', (fundo + v['bowden_hole_up'], v['bowden_hole_x']), v['bowden_hole'], -20, 20)
    return pu._solido(corpo)


# ---------------------------------------------------------------- corners (construir.cantos, _canto_etapa)
def _pernas(m, nome):
    a, b = m.mapa.CANTOS[nome]
    return [(*p[:5], p[5] if len(p) > 5 else 'cover_corner') for p in (a, b)]


def _corte_clips(m, corpo, perna, clip, off, inicio, J):
    """The space of an edge's clips on a corner leg, from where they start to past the joint (clipsA, clipsB)."""
    fs = m.v['frame_size']
    sec = [(fs / 2 + m.ev(off) - s, d) for s, d in poligono(m, clip)]
    u0 = m.ev(inicio)
    return corpo - (pu._prisma(sec, 'yz', u0, J + 1) if perna == 'A' else pu._prisma(sec, 'xz', u0, J + 1))


def canto(m, nome):
    """An L corner of mapa.CANTOS: each leg its cover's profile (s from the edge's outer line), from 2 before the corner
    to the leg's length, mitred on the diagonal; a leg without the corner wedge trims the other's; less the space of
    each edge's clips; the core where no clip comes (canto_miolo); the 45 deg scarf where a middle passes over a leg's
    end; the finger grip (mapa.PEGA, then its leg's clips cut again); the hinge knuckle (mapa.DOBRADICA)."""
    v, T = m.v, m.T
    fs, ext = v['frame_size'], 2.0
    (cov_a, clip_a, off_a, ini_a, junta_a, Ja), (cov_b, clip_b, off_b, ini_b, junta_b, Jb) = _pernas(m, nome)
    Ja, Jb = m.ev(Ja), m.ev(Jb)
    perna_a = pu._prisma([(fs / 2 - s, d) for s, d in poligono(m, cov_a)], 'yz', -ext, Ja)
    perna_a = perna_a - pu._prisma([(-4, -4), (40, 40), (-4, 40)], 'xy', -20, 20)
    perna_b = pu._prisma([(fs / 2 - s, d) for s, d in poligono(m, cov_b)], 'xz', -ext, Jb)
    perna_b = perna_b - pu._prisma([(-4, -4), (40, -4), (40, 40)], 'xy', -20, 20)
    corpo = perna_a + perna_b
    if any(max(s for s, _ in poligono(m, c)) <= fs / 2 + 1e-6 for c in (cov_a, cov_b)):
        corpo = corpo - pu._caixa((-4, 0), (-4, 0), (-20, 20))
    corpo = _corte_clips(m, corpo, 'A', clip_a, off_a, ini_a, Ja)
    corpo = _corte_clips(m, corpo, 'B', clip_b, off_b, ini_b, Jb)
    if v.get('canto_miolo', 0.0) > 0:
        corpo = _miolo(m, corpo, ((('A', clip_a, off_a, ini_a, ini_b)), ('B', clip_b, off_b, ini_b, ini_a)))
    rec, top2 = T + v['cover_recess'], m.top + 2
    js = v['joint_scarf']
    if junta_a:
        corpo = corpo - pu._prisma([(Ja, rec), (Ja + 1, rec), (Ja + 1, top2), (Ja - js - 2, top2)], 'xz', -30, 30)
    if junta_b:
        corpo = corpo - pu._prisma([(Jb, rec), (Jb + 1, rec), (Jb + 1, top2), (Jb - js - 2, top2)], 'yz', -30, 30)
    perna = m.mapa.PEGA.get(nome)
    if perna:
        corpo = pu._pega(corpo, v, perna)
        corpo = (_corte_clips(m, corpo, 'A', clip_a, off_a, ini_a, Ja) if perna == 'A'
                 else _corte_clips(m, corpo, 'B', clip_b, off_b, ini_b, Jb))
    if nome in m.mapa.DOBRADICA:
        corpo = dobradica(m, corpo, nome)
    return pu._solido(corpo)


def _miolo(m, corpo, pernas):
    """The 'miolo' step: over the post, where neither leg's standard clips reach, the hollow between the cover and the
    frame filled from the acrylic stop out to the cover's wall, from the frame face to 1 under the outer face,
    canto_miolo_folga short of the clips."""
    v = m.v
    fs, folga = v['frame_size'], v['canto_miolo_folga']
    for perna, clip, off, inicio, outro in pernas:
        if clip != 'clip-padrao':
            continue
        w0 = fs / 2 + m.ev(off) - m.ev(perfis.WALL_FIT)
        w1 = fs / 2 + m.ev(off) - m.ev(perfis.STOP_STD)
        if min(m.ev(inicio), m.ev(outro)) - folga <= w1:
            continue
        fim = m.ev(inicio) - folga
        pts = [(0.0, w0), (fim, w0), (fim, w1), (0.0, w1)]
        corpo = corpo + pu._prisma(pts if perna == 'A' else [(w, u) for u, w in pts], 'xy', 0.0, m.top - 1)
    return corpo


def dobradica(m, corpo, nome):
    """construir._hinge: the knuckle on the hinge edge's leg. The side's (no-lateral): from the corner over
    hinge_side_len, the screw's hole and the head's counterbore at the corner end; the door's (no-porta): from
    hinge_side_len + hinge_gap over hinge_door_len (at the pin), its far end on a 45 deg gusset toward the cover, a free
    hole. Each one's wedge cut away where the other panel's knuckle sits."""
    _, perna, no = m.mapa.DOBRADICA[nome]
    v = m.v
    fs = v['frame_size']
    P = (lambda u, w: (u, w)) if perna == 'A' else (lambda u, w: (w, u))   # noqa: E731
    eixo = 'x' if perna == 'A' else 'y'
    W = lambda s: fs / 2 - s                                                # noqa: E731
    lado = no == 'no-lateral'
    pin_s, pin_d = (m.ev(e) for e in (perfis.PINO_LATERAL if lado else perfis.PINO_PORTA))
    inicio = 0.0 if lado else v['hinge_side_len'] + v['hinge_gap']
    fim_porta = v['hinge_side_len'] + v['hinge_gap'] + v['hinge_door_len']
    comp = v['hinge_side_len'] if lado else v['hinge_door_len'] + v['wall_width'] + v['door_pin_s'] - fs / 2 + 1
    sec = [(W(s), d) for s, d in poligono(m, no)]
    no_ = pu._prisma(sec, 'yz' if perna == 'A' else 'xz', inicio, inicio + comp)
    if not lado:
        w_pin = W(v['door_pin_s'])
        wa, wb = w_pin - 5, v['wall_width'] + 1
        ua, ub = fim_porta - 5, fim_porta + v['wall_width'] + 1 - w_pin
        longe = fim_porta + v['wall_width'] + v['door_pin_s'] + 10
        no_ = no_ - pu._prisma([P(ua, wa), P(ub, wb), P(longe, wb), P(longe, wa)], 'xy', -20, 20)
    corpo = corpo + no_
    furo = v['hinge_hole_side'] if lado else v['hinge_hole_door']
    corpo = corpo - pu._cilindro(eixo, (W(pin_s), pin_d), furo, inicio, inicio + comp + 1)
    if lado:
        corpo = corpo - pu._cilindro(eixo, (W(pin_s), pin_d), v['hinge_head_d'], inicio, inicio + v['hinge_head_depth'])
        de, ate = v['hinge_side_len'], fim_porta + v['door_pin_s'] - fs / 2 + 1
    else:
        de, ate = 0.0, v['hinge_side_len'] + v['hinge_gap']
    return corpo - pu._prisma([P(de, -3), P(ate, -3), P(ate, 0), P(de, 0)], 'xy', -20, 20)


# ---------------------------------------------------------------- the lock in the pieces (construir.trava_pecas)
def trava_corte(m, corpo, nome):
    """The lock cut into a production piece, in its lock frame from the map (travas.quadros): on a clip the coupon
    clip's window without legs, the neck's slots (leaning back at 45 deg above the base under the acrylic) and the way
    in for a wide neck; on a cover or a corner the neck's slot and the dot."""
    sp = m.quadros()[nome]
    v = m.v
    vv = m.vals(m.config.TRAVA_VARIANTES['topo']) if sp['topo'] else v     # cap and dot further out
    g = geometria_trava.geo(vv)
    ol, ex, ey, ez = sp['quadro']
    P = lambda s, d, z: tuple(ol[i] + s * ex[i] + d * ey[i] + z * ez[i] for i in range(3))   # noqa: E731
    eixo = lambda u: next(k for k in range(3) if abs(u[k]) > 0.5)                            # noqa: E731

    def caixa(s, d, z):
        pts = [P(a, b, c) for a in s for b in d for c in z]
        return pu._caixa(*[(min(p[i] for p in pts), max(p[i] for p in pts)) for i in range(3)])

    def prisma(s, dz):
        """Polygon in (d, z) at s[0], through to s[1]."""
        i = eixo(ex)
        j, k = [q for q in range(3) if q != i]
        a, b = sorted((P(s[0], 0, 0)[i], P(s[1], 0, 0)[i]))
        return pu._prisma([(P(s[0], d, z)[j], P(s[0], d, z)[k]) for d, z in dz], 'xyz'[j] + 'xyz'[k], a, b)

    def rampa(s, d, z, d_sup):
        """construir._box_rampa: the near end (z[0]) leans back toward z = 0 at 45 deg above d_sup."""
        perto = lambda dd: z[0] - max(0.0, dd - d_sup)   # noqa: E731
        return prisma(s, [(d[0], z[1]), (d[1], z[1]), (d[1], perto(d[1]))] + ([(d_sup, z[0])] if d[0] < d_sup < d[1] else []) +
                      [(d[0], perto(d[0]))])

    T, top, hs, inner, wo = g['T'], g['top'], g['hs'], g['inner'], g['wo']
    dsup, rec, fs = v['panel_frame_spacing'], v['cover_recess'], v['frame_size']
    dt = T + v['dovetail_height'] + 1
    if sp['parte'] == 'clip':
        win, fundo, s0 = g['win'], v['slot_depth'] + 1, g['so'] + v['fin_barb'] + 1
        corpo = corpo - prisma((-s0, s0), [(0.0, win[0]), (0.0, win[1]), (-fundo, win[1]), (-fundo, win[0] - fundo)])
        corpo = corpo - rampa((hs[0], inner), (0.0, dt), g['path'], dsup)
        corpo = corpo - rampa((inner if sp['perfil'] != 'clip-parede' else -fs / 2, fs / 2), (T + rec, dt), g['path'], dsup)
        if wo > inner:
            if not g['win'][0] <= g['furo'][0] < g['furo'][1] <= g['win'][1]:
                raise ValueError(f'a entrada do pescoço largo (z {g["furo"]}) sai da janela sem pernas (z {g["win"]})')
            corpo = corpo - rampa((inner, wo), (dsup, T + rec), g['path'], dsup)
            corpo = corpo - caixa((inner, wo), (-1.0, dsup + 0.5), g['furo'])
    else:
        corpo = corpo - caixa((hs[0], max(hs[1], wo)), (T - 0.1, top + 1), g['path'])
        (si, zi), di, dp = g['ind'], v['trava_indicador_diametro'], v['trava_indicador_profundidade']
        c3, j = P(si, top - dp, zi), eixo(ey)
        a, b = sorted((c3[j], c3[j] + (dp + 1) * ey[j]))
        corpo = corpo - pu._cilindro('xyz'[j], tuple(c3[q] for q in range(3) if q != j), di, a, b)
    return corpo


# ---------------------------------------------------------------- the lock's parts (construir.trava_deslizante)
def _vals_trava(m, variante):
    return m.vals(m.config.TRAVA_VARIANTES[variante]) if variante else m.v


def cursor(m, variante=None):
    """trava-cursor: one side profile (tongue, neck, dovetail stub) through the tongue's width (out to wo if wider), the
    neck and stub thinned, the step below the wide neck, the keel closing to the slot's floor, the pointed nose; bed
    chamfers on its rear end (z0, trava_chanfro_encaixe on the stub's base); then its one-layer bed tab (orelha)."""
    v = _vals_trava(m, variante)
    g = geometria_trava.geo(v)
    if g['dentes']:
        raise ValueError('cursor com dentes (trava_dentes): não está portado; as peças de produção têm uma lingueta')
    hs, hz = g['hs'], g['hz']
    z0, lk, gap = g['z0'], g['lk'], g['gap']
    th, fl = v['trava_toco_altura'], v['trava_toco_aba']
    zc, tz, tl = g['zc'], g['tz'], g['tl']
    e, fh, kr = v['trava_entrada'], g['fh'], g['kr']
    d0, d1, df = -v['trava_quilha_fundo'], -v['trava_lingueta_topo'], -v['trava_lingueta_fundo']
    tras = [(tz[0] - kr, gap + th), (tz[0] - kr, gap + kr), (tz[0], gap)]
    pc = min(v['trava_pescoco_chanfro'], tz[0] - hz[0])
    frente = [(tz[1], gap)] + ([(tz[1] + fl, gap + fl)] if v.get('trava_toco_frente_reta', 0) else []) + [(tz[1] + fl, gap + th)]
    lado = [(z0, d0), (z0 + lk, d0), (z0 + lk, d1), (hz[1], d1), (hz[1], gap)] + frente + tras + [(hz[0] + pc, gap), (hz[0], gap - pc)]
    lado = [p for i, p in enumerate(lado) if math.dist(p, lado[i - 1]) > 1e-6]
    wo, dg = g['wo'], g['dg']
    wl, wr = g['lingueta']
    wx = max(wr, wo)
    corpo = pu._prisma([(d, z) for z, d in lado], 'yz', wl, wx)
    zt = max(hz[1], tz[1] + fl) + 1
    corpo = corpo - pu._caixa((wl - 1, hs[0] + fh), (d1, gap), (hz[0] - 1, hz[1] + 1))
    if wo > wr:
        corpo = corpo - pu._caixa((wr, wx + 1), (d0 - 1, dg), (z0 - 1, zt))
    if fh > 0:
        for sa, da, db in (((hs[1], d1, dg), (wo, dg, gap + th + 1)) if wo > hs[1] else ((hs[1], d1, gap + th + 1),)):
            corpo = corpo - pu._caixa((sa - fh, wx + 1), (da, db), (z0 - 1, zt))
    elif wr > max(hs[1], wo) + 1e-6:
        corpo = corpo - pu._caixa((max(hs[1], wo), wx + 1), (d1, gap + th + 1), (z0 - 1, zt))
    if tl < wo - wl:
        corpo = corpo - pu._caixa((wl - 1, wo - tl + fh), (gap - 0.01, gap + th + 1), (z0 - 1, zt))
    elif tl > wo - wl:
        a, b = sorted((wo - tl, 0.0))
        corpo = corpo + pu._prisma([(d, z) for z, d in [(tz[1], gap), (tz[1] + fl, gap + th)] + tras], 'yz', a, b)
    if d0 < df:
        kt = math.tan(math.radians(v['trava_quilha_angulo']))
        for sg, se in ((1, wr), (-1, wl)):
            q = [(se, df), (se + sg, df), (se + sg, d0 - 1), (se - sg * (df - d0 + 1) * kt, d0 - 1)]
            corpo = corpo - pu._prisma(q, 'xy', z0 - 1, z0 + lk + 1)
    lt, ze = v['trava_entrada_comprimento'], z0 + lk
    for sg, se in ((1, wr), (-1, wl)):
        tri = [(se - sg * e, ze), (se + sg, ze), (se + sg, ze - lt * (e + 1) / e)]
        corpo = corpo - pu._prisma(tri, 'xz', d0 - 0.5, d1 + 0.5)
    marca = m.config.TRAVA_MARCAS.get(variante, 0) if variante else 0
    if marca:
        sf, gd = wo - tl + fh, min(0.6, (tl - 2 * fh) / 3)
        for i in range(marca):
            zm = zc + (i - (marca - 1) / 2) * 2.0
            corpo = corpo - pu._caixa((sf - 1, sf + gd), (gap, gap + th + 1), (zm - 0.5, zm + 0.5))
    corpo = pu._solido(corpo)
    fino = lambda p: p[1] > gap - 0.5      # noqa: E731
    corpo, *_ = pu.chanfro_mesa(corpo, 'z', z0, v['trava_chanfro_mesa'], pular=fino)
    if v['trava_chanfro_encaixe'] > 0:
        corpo, *_ = pu.chanfro_mesa(corpo, 'z', z0, v['trava_chanfro_encaixe'], pular=lambda p: not fino(p))
    ol, oh = v['trava_orelha_comprimento'], v['trava_orelha_altura']
    if ol > 0:
        r, dt = oh + v['trava_orelha_recuo'], gap + th
        tri = [(z0 - 1, dt - r - 1), (z0 - 1, dt + 1), (z0 + r + 1, dt + 1)]
        corpo = corpo - pu._prisma([(d, z) for z, d in tri], 'yz', wl - 1, wx + 1)
        ins = v['trava_chanfro_encaixe'] + 0.1
        corpo = corpo + pu._caixa((wo - tl + fh + ins, wo - fh - ins), (gap + kr + 0.05, dt + ol), (z0, z0 + oh))
    return pu._solido(corpo)


def capa(m, variante=None):
    """trava-capa: the knob (the crest over the neck, concave flanks, flat ends) over the cover's flat top, the socket
    of the stub's dovetail open on the outer edge, corners at 45 deg seen from above, the grooves underneath; the bed
    chamfer on its inner end (it prints standing on it)."""
    v = _vals_trava(m, variante)
    g = geometria_trava.geo(v)
    (c0, c1), (s0, s1) = g['cap_z'], g['cap_s']
    gap, top, zc, tz, kr = g['gap'], g['top'], g['zc'], g['tz'], g['kr']
    th, fl = v['trava_toco_altura'], v['trava_toco_aba']
    rim, crista = gap + v['trava_capa_aba'], top + v['trava_capa_crista']
    ch, cw, cc = v['trava_capa_chanfro'], v['trava_capa_crista_largura'] / 2, v['trava_capa_concavo']
    n = max(4, round(cc / 0.25))
    sobe = [(zc - cw - cc * (1 - i / n), rim + (crista - rim) * (i / n) ** 2) for i in range(n + 1)]
    lado = ([(c0, gap), (c0, rim - ch), (c0 + ch, rim)] + sobe + [(2 * zc - z, d) for z, d in reversed(sobe)] +
            [(c1 - ch, rim), (c1, rim - ch), (c1, gap)])
    corpo = pu._prisma([(d, z) for z, d in lado], 'yz', s0, s1)
    ft, le = v['trava_folga_toco'], v['trava_capa_labio']
    frente = ([(tz[1] + le + ft, gap - 1), (tz[1] + le + ft, gap + le), (tz[1] + fl + ft, gap + fl)] if v.get('trava_toco_frente_reta', 0)
              else [(tz[1] + ft, gap - 1), (tz[1] + ft, gap)])
    encaixe = [(tz[0] - le - ft, gap - 1)] + frente + [(tz[1] + fl + ft, gap + th), (tz[0] - kr - ft, gap + th),
                                                       (tz[0] - kr - ft, gap + kr), (tz[0] - le - ft, gap + le)]
    corpo = corpo - pu._prisma([(d, z) for z, d in encaixe], 'yz', g['wo'] - g['tl'], s1 + 1)
    k = v['trava_capa_canto']
    for se, ss in ((s0, -1), (s1, 1)):
        for ze, sz in ((c0, -1), (c1, 1)):
            tri = [(se - ss * (k + 1), ze + sz), (se + ss, ze - sz * (k + 1)), (se + ss, ze + sz)]
            corpo = corpo - pu._prisma(tri, 'xz', gap - 1, crista + 1)
    marca = m.config.TRAVA_MARCAS.get(variante, 0) if variante else 0
    sulcos = (getattr(m.config, 'TRAVA_MARCAS_CAPA', {}).get(variante, marca) if variante else 0) or round(v['trava_capa_sulcos'])
    for i in range(sulcos):
        zm = c0 + 3 + 2.0 * i
        corpo = corpo - pu._caixa((s0 - 1, s1 + 1), (gap - 1, gap + 0.6), (zm - 0.5, zm + 0.5))
    corpo = pu._solido(corpo)
    corpo, *_ = pu.chanfro_mesa(corpo, 'x', s0, v['trava_chanfro_mesa'])
    return pu._solido(corpo)


def indicador(m):
    """trava-indicador: the disc that fills the dot, in the coupon's frame (the standard cover's dot)."""
    g = geometria_trava.geo(m.v)
    (si, zi), di, dp = g['ind'], m.v['trava_indicador_diametro'], m.v['trava_indicador_profundidade']
    return pu._solido(pu._cilindro('y', (si, zi), di, g['top'] - dp, g['top']))


ESPELHO = bd.Plane.XY          # construir.trava_espelho: z -> -z in the coupon's frame


# ---------------------------------------------------------------- any piece by its component name
def construir(m, nome):
    """The component nome as construir builds it (cached): a straight piece or a corner with its handle, logo pocket,
    lock and bed chamfer; the logo; the bowden plug; the lock's slider, cap and disc (and their mirror images)."""
    if nome in m.feitas:
        return m.feitas[nome]
    t = time.time()
    v = m.v
    if nome in m.mapa.PECAS or nome in m.mapa.CANTOS:
        reto = nome in m.mapa.PECAS
        corpo = reta(m, nome) if reto else canto(m, nome)
        if reto and nome == getattr(m.config, 'PUXADOR', ('tampa-parede-v-puxador',))[0]:
            corpo = puxador(m, corpo, nome)
        if reto and getattr(m.config, 'LOGO_JSON', None) and nome == 'tampa-parede-h-logo':
            corpo = bolso_logo(m, corpo, nome)
        if nome in m.quadros():
            corpo = trava_corte(m, corpo, nome)
        corpo = pu._solido(corpo)
        dist = v.get('bed_chamfer', 0.0)
        if dist > 0:
            if not reto:
                corpo, *_ = pu.chanfro_mesa(corpo, 'z', m.top, dist, so_contorno=True)
            elif m.mapa.PECAS[nome][0].startswith('tampa'):
                corpo, *_ = pu.chanfro_mesa(corpo, 'y', m.top, dist, so_contorno=True)
            else:
                L = m.ev(m.mapa.PECAS[nome][1])
                for z in (0.0, L):
                    corpo, *_ = pu.chanfro_mesa(corpo, 'z', z, dist, so_contorno=True, pular=lambda p: p[1] < -1e-3)
    elif nome == 'logo-voron':
        corpo = logo(m)
    elif nome == 'passa-bowden':
        corpo = passa_bowden(m)
    elif nome in ('trava-cursor', 'trava-capa', 'trava-cursor-espelho', 'trava-capa-espelho'):
        base = nome.replace('-espelho', '')
        corpo = cursor(m) if base == 'trava-cursor' else capa(m)
        if nome != base:
            corpo = pu._solido(bd.mirror(corpo, ESPELHO))
    elif nome == 'trava-capa-topo':
        corpo = capa(m, 'topo')
    elif nome == 'trava-indicador':
        corpo = indicador(m)
    else:
        raise KeyError(f'{nome}: não é peça de {m.nome}')
    corpo = pu._solido(corpo)
    m.feitas[nome] = corpo
    print(f'  {nome}: {corpo.volume:.1f} mm³, {time.time() - t:.1f} s', flush=True)
    return corpo


def todas(m):
    """Every component the machine's faces use (straight pieces, corners, extras, the logo and the lock's parts)."""
    nomes = []
    for f in faces(m):
        for p in colocacoes(m, f['nome']):
            if p[0] not in nomes:
                nomes.append(p[0])
    return nomes


# ---------------------------------------------------------------- faces (construir.montar)
def faces(m):
    return m.mapa.faces(m.v)


def colocacoes(m, face):
    """construir.montar's placements of one face: (component, origin, x, y, z, edge), mm."""
    L = {k: m.ev(expr) for k, (_, expr) in m.mapa.PECAS.items()}
    f = next(x for x in faces(m) if x['nome'] == face)
    return m.mapa.colocacoes(m.v, L, f)


def _local(o, x, z):
    return bd.Location(bd.Plane(origin=tuple(o), x_dir=tuple(x), z_dir=tuple(z)))


def montar(m, face):
    """The face's pieces in place: list of (key, component, shape), key unique in the face."""
    out, n = [], {}
    for nome, o, x, _, z, _ in colocacoes(m, face):
        n[nome] = n.get(nome, 0) + 1
        out.append((f'{nome}:{n[nome]}', nome, construir(m, nome).moved(_local(o, x, z))))
    return out


def frame(m):
    """construir.frame_ref: the frame members of config.FRAME_JSON, the section of config.PERFIL_JSON (its largest
    loop less the loops inside it) placed as Fusion does: the box rounded to 0.1, the square from its min side."""
    return [(nome, perfil.moved(loc)) for nome, perfil, loc in membros_frame(m)]


def membros_frame(m):
    """frame's members as (name, the extrusion of its length at the origin, its placement): one extrusion per length,
    shared (the web viewer meshes each once)."""
    loops = [lp[:-1] if lp[0] == lp[-1] else lp for lp in json.load(open(m.ref(m.config.PERFIL_JSON)))['loops']]
    area = lambda lp: abs(sum(lp[i][0] * lp[i - 1][1] - lp[i - 1][0] * lp[i][1] for i in range(len(lp)))) / 2   # noqa: E731
    loops.sort(key=lambda lp: -area(lp))
    fio = lambda lp: bd.Wire.make_polygon([bd.Vector(x, y, 0) for x, y in lp], close=True)                        # noqa: E731
    secao = bd.Face(fio(loops[0]), [fio(lp) for lp in loops[1:]])
    half = m.v['frame_size'] / 2
    perfis_, out = {}, []
    for mb in json.load(open(m.ref(m.config.FRAME_JSON)))['membros']:
        comp = round(mb['comprimento'])
        k = 'XYZ'.index(mb['eixo'])
        i, j = (k + 1) % 3, (k + 2) % 3
        bb = [round(c, 1) for c in mb['bb']]
        o = [0.0, 0.0, 0.0]
        o[i], o[j], o[k] = bb[i] + half, bb[j] + 2 * half, bb[k]
        if comp not in perfis_:
            perfis_[comp] = bd.extrude(secao, amount=comp, dir=(0, 0, 1))
        u = lambda q: tuple(1.0 if r == q else 0.0 for r in range(3))   # noqa: E731
        out.append((mb.get('nome', f'perfil {comp}'), perfis_[comp], _local(o, u(i), u(k))))
    return out


# ---------------------------------------------------------------- checks (construir.interferencia, entre_faces, giro_porta)
def _comum(a, b):
    """The overlap of a and b: (mm³, depth: the thinnest side of each lump's box, the largest over the lumps)."""
    ba, bb_ = a.bounding_box(), b.bounding_box()
    (a0, a1), (b0, b1) = (pu._xyz(ba.min), pu._xyz(ba.max)), (pu._xyz(bb_.min), pu._xyz(bb_.max))
    if any(a0[i] > b1[i] + 1e-6 or b0[i] > a1[i] + 1e-6 for i in range(3)):
        return 0.0, 0.0
    x = a & b
    sol = [] if x is None else [s for s in x.solids() if s.volume > 1e-6]
    if not sol:
        return 0.0, 0.0
    fino = lambda s: min(pu._xyz(s.bounding_box().size))   # noqa: E731
    return sum(s.volume for s in sol), max(fino(s) for s in sol)


def _pre_carga(m, um, outro, prof):
    """construir._preload: the overlaps meant to be there (a clip's rib on the bowden plug, the slider's bed tab in
    its cap, the split fin pressing the slot's lip)."""
    v = m.v
    nomes = {um, outro}
    if any(n.startswith('clip-') for n in nomes) and nomes & set(getattr(m.mapa, 'EXTRAS', ())) and abs(prof - v['panel_preload']) < 0.01:
        return 'nervura na peça que faz as vezes da chapa'
    if any(n.startswith('trava-cursor') for n in nomes) and any(n.startswith('trava-capa') for n in nomes) \
            and prof <= v.get('trava_orelha_altura', 0.0) + 0.01:
        return 'orelha do cursor (sai antes de montar)'
    lip = max(v.get('fin_lip_preload', 0.0), -v.get('fin_barb_gap', 0.0))
    if lip > 0 and FRAME in nomes and any(n.startswith(('clip-padrao', 'clip-parede')) for n in nomes) and prof <= lip + 0.01:
        return 'aleta apertando a aba do rasgo'
    return None


def _pares(m, grupo_a, grupo_b=None):
    """Overlaps between the pieces of a list (each pair once) or of two lists: {(key, key): (mm³, depth, tag)}."""
    out = {}
    pares = ([(a, b) for i, a in enumerate(grupo_a) for b in grupo_a[i + 1:]] if grupo_b is None
             else [(a, b) for a in grupo_a for b in grupo_b])
    for (ka, na, sa), (kb, nb, sb) in pares:
        vol, prof = _comum(sa, sb)
        if vol > 0:
            out[(ka, kb)] = (round(vol, 4), round(prof, 3), _pre_carga(m, na, nb, prof))
    return out


def interferencia(m, face, quadro=None):
    """construir.interferencia: the face's pieces with each other and with the frame."""
    pecas = montar(m, face)
    fr = [(f'{FRAME}:{n}', FRAME, s) for n, s in (quadro or frame(m))]
    return {**_pares(m, pecas), **_pares(m, pecas, fr)}


def entre_faces(m, nomes, montadas=None):
    """construir.entre_faces: pieces of different faces."""
    montadas = montadas or {f: montar(m, f) for f in nomes}
    out = {}
    for i, a in enumerate(nomes):
        for b in nomes[i + 1:]:
            for (ka, kb), r in _pares(m, montadas[a], montadas[b]).items():
                out[(f'{a}/{ka}', f'{b}/{kb}')] = r
    return out


def giro_porta(m, graus, face='porta', montadas=None):
    """construir.giro_porta (com_frame False, as construir_tudo runs it): the door turned about its hinge pin, against
    the hinge side's panel and the other door."""
    v = m.v
    sx = -1 if face.endswith('esquerda') else 1
    px = sx * (v['frame_width'] / 2 - v['frame_size'] / 2 + v['door_pin_s'])
    py = -v['frame_depth'] / 2 - v['door_pin_d']
    rot = bd.Pos(px, py, 0) * bd.Rot(0, 0, sx * graus) * bd.Pos(-px, -py, 0)
    outras = ['lateral-direita' if sx == 1 else 'lateral-esquerda']
    nomes = [f['nome'] for f in faces(m)]
    outra = {'porta-direita': 'porta-esquerda', 'porta-esquerda': 'porta-direita'}.get(face)
    if outra in nomes:
        outras.append(outra)
    montadas = montadas or {}
    porta = [(k, n, s.moved(rot)) for k, n, s in (montadas.get(face) or montar(m, face))]
    out = {}
    for o in outras:
        for (ka, kb), r in _pares(m, porta, montadas.get(o) or montar(m, o)).items():
            out[(f'{face}/{ka}', f'{o}/{kb}')] = r
    return out


def conferir(m, nomes=None):
    """Every check of construir_tudo: each face against the frame, between faces, the doors turned 15/45/90/110."""
    t = time.time()
    todas_ = [f['nome'] for f in faces(m)]
    nomes = nomes or todas_
    quadro = frame(m)
    res = {'interferencia': {}, 'entre_faces': {}, 'giro_porta': {}}
    for f in nomes:
        res['interferencia'][f] = interferencia(m, f, quadro)
    montadas = {f: montar(m, f) for f in todas_}
    res['entre_faces'] = entre_faces(m, todas_, montadas)
    for f in [x for x in todas_ if x.startswith('porta')]:
        for a in (15, 45, 90, 110):
            res['giro_porta'][f'{f} {a}°'] = giro_porta(m, a, f, montadas)
    res['tempo'] = round(time.time() - t)
    return res


def _resumo(res):
    """Collisions (depth >= 0.05, not a meant preload), contacts and preloads of a check."""
    col, con, pre = {}, {}, {}
    for (a, b), (vol, prof, tag) in res.items():
        (pre if tag else col if prof >= 0.05 else con)[f'{a} × {b}'] = (vol, prof) + ((tag,) if tag else ())
    return col, con, pre


# ---------------------------------------------------------------- export (construir.exportar_faces)
def exportar(m, nomes_faces, pasta):
    """Each component of the faces as an STL in its own frame, named with its count across them, and quantidades.json."""
    os.makedirs(pasta, exist_ok=True)
    qtd = {}
    for f in nomes_faces:
        for p in colocacoes(m, f):
            qtd[p[0]] = qtd.get(p[0], 0) + 1
    for nome, n in qtd.items():
        bd.export_stl(construir(m, nome), os.path.join(pasta, f'{nome}-{n}x.stl'), tolerance=0.005, angular_tolerance=0.1)
    with open(os.path.join(pasta, 'quantidades.json'), 'w') as fh:
        json.dump(dict(sorted(qtd.items())), fh, indent=1, ensure_ascii=False)
    return qtd


def _pasta_nova(base):
    """stl/<base>-v<n>, the first n not taken (an export never overwrites an earlier one)."""
    n = 1
    while os.path.exists(os.path.join(REPO, 'stl', f'{base}-v{n}')):
        n += 1
    return os.path.join(REPO, 'stl', f'{base}-v{n}')


# ---------------------------------------------------------------- against Fusion's STLs
def _difuso(a, b, op):
    """a op b (BRepAlgoAPI_Cut or _Common), fuzzy (a mesh's faces lie on the B-rep's): its solids."""
    op.SetFuzzyValue(1e-4)
    return [s for s in a._bool_op((a,), (b,), op).solids() if s.volume > 1e-6]


def _so_em(a, b):
    """What a has and b lacks: (mm³, the thickest bit's thickness, 2 volume / area: a facet's sliver along a round hole
    is a few hundredths)."""
    from OCP.BRepAlgoAPI import BRepAlgoAPI_Cut
    sol = _difuso(a, b, BRepAlgoAPI_Cut())
    return sum(s.volume for s in sol), max((2 * s.volume / s.area for s in sol), default=0.0)


def diferenca(nosso, deles):
    """(what only ours has, what only theirs has, the boolean held): an empty result is also what a failed boolean
    returns, so the common volume must close the account both ways."""
    from OCP.BRepAlgoAPI import BRepAlgoAPI_Common
    (va, pa), (vf, pf) = _so_em(nosso, deles), _so_em(deles, nosso)
    comum = sum(s.volume for s in _difuso(nosso, deles, BRepAlgoAPI_Common()))
    tol = 0.01 + 1e-6 * nosso.volume
    return (va, pa), (vf, pf), abs(nosso.volume - va - comum) < tol and abs(deles.volume - vf - comum) < tol


def _triangulos_stl(caminho):
    import numpy as np
    d = open(caminho, 'rb').read()
    n = struct.unpack('<I', d[80:84])[0]
    reg = np.frombuffer(d, dtype=np.dtype([('n', '<f4', 3), ('v', '<f4', (3, 3)), ('a', '<u2')]), count=n, offset=84)
    return reg['v'].astype(float)


def _triangulos(shape, tol=0.001):
    import numpy as np
    vs, ts = shape.tessellate(tol, 0.05)
    return np.array([(p.X, p.Y, p.Z) for p in vs])[np.array(ts)]


def _secao_malha(tri, k, valor):
    """The section of a closed triangle mesh with the plane (axis k) = valor, a shapely region in the other two axes."""
    from shapely.geometry import MultiLineString
    from shapely.ops import polygonize, unary_union
    i, j = [q for q in range(3) if q != k]
    segs = []
    for t, dd in zip(tri, tri[:, :, k] - valor):
        pts = []
        for a, b in ((0, 1), (1, 2), (2, 0)):
            if (dd[a] < 0) != (dd[b] < 0):
                p = t[a] + dd[a] / (dd[a] - dd[b]) * (t[b] - t[a])
                pts.append((round(p[i], 6), round(p[j], 6)))
        if len(pts) == 2 and pts[0] != pts[1]:
            segs.append(pts)
    out = None
    for p in sorted(polygonize(unary_union(MultiLineString(segs))), key=lambda p: -p.area):
        out = p if out is None else out.symmetric_difference(p)
    return out


def secoes(nosso, caminho_stl, n=25):
    """Where the booleans fail (a solid rebuilt from its mesh against Fusion's mesh): both meshes cut by n planes across
    each axis; the largest area one section has that the other lacks (mm²)."""
    a, b = _triangulos(nosso), _triangulos_stl(caminho_stl)
    pior = 0.0
    for k in range(3):
        lo, hi = a[:, :, k].min(), a[:, :, k].max()
        for i in range(n):
            c = lo + (hi - lo) * (i + 0.5 + 0.0123) / n
            sa, sb = _secao_malha(a, k, c), _secao_malha(b, k, c)
            if sa is None or sb is None:
                pior = max(pior, (sa or sb).area if (sa or sb) is not None else 0.0)
                continue
            pior = max(pior, sa.symmetric_difference(sb).area)
    return pior


def comparar(m, pasta):
    """Each STL of a Fusion export (<name>-<n>x.stl or <name>.stl) against the same component built here: volumes and
    what each has that the other lacks (mm³, and the thickest of those bits; the hinge's holes and the dot are round
    here and facetted in the STL)."""
    out = {}
    for arq in sorted(os.listdir(pasta)):
        if not arq.endswith('.stl'):
            continue
        nome = re.sub(r'-\d+x$', '', arq[:-4])
        try:
            nosso = construir(m, nome)
        except KeyError as e:
            out[nome] = str(e)
            continue
        deles = pu.stl_solido(os.path.join(pasta, arq))
        (va, pa), (vf, pf), ok = diferenca(nosso, deles)
        out[nome] = dict(build123d=round(nosso.volume, 3), fusion=round(deles.volume, 3), so_aqui=(round(va, 3), round(pa, 3)),
                         so_no_fusion=(round(vf, 3), round(pf, 3)), booleana=ok)
        nota = ''
        if not ok:
            out[nome]['secoes_mm2'] = round(secoes(nosso, os.path.join(pasta, arq)), 4)
            nota = f'   a booleana falhou; nos cortes, no máximo {out[nome]["secoes_mm2"]:.4f} mm² de diferença'
        print(f'{nome:36s} {nosso.volume:10.2f} {deles.volume:10.2f}   só aqui {va:7.3f} ({pa:.3f})   só no Fusion {vf:7.3f} ({pf:.3f}){nota}', flush=True)
    return out


# ---------------------------------------------------------------- command line
def main(args):
    mudancas = {}
    while '--mudar' in args:
        i = args.index('--mudar')
        k, e = args[i + 1].split('=', 1)
        mudancas[k] = e
        del args[i:i + 2]
    if len(args) < 2:
        print(__doc__)
        return
    m = Maquina(args[0], mudancas)
    cmd, resto = args[1], args[2:]
    t = time.time()
    if cmd == 'pecas':
        for n in resto or todas(m):
            construir(m, n)
    elif cmd == 'face':
        face = resto[0]
        pasta = resto[1] if len(resto) > 1 else _pasta_nova(f'{m.config.STL_PREFIX}{face}-b3d')
        col, con, pre = _resumo(interferencia(m, face))
        print(f'interferência {face}: colisões {col or "nenhuma"}; pré-cargas {len(pre)}; contatos {len(con)}')
        qtd = exportar(m, [face], pasta)
        print(f'exportado em {pasta}: {qtd}')
    elif cmd == 'conferir':
        res = conferir(m, resto or None)
        ate = lambda d: f' (até {max(x[1] for x in d.values()):.3f} mm)' if d else ''   # noqa: E731
        for f, r in res['interferencia'].items():
            col, con, pre = _resumo(r)
            tags = sorted({p[-1] for p in pre.values()})
            print(f'interferência {f}: colisões {col or "nenhuma"}; pré-cargas {len(pre)}{ate(pre)} {tags}; contatos {len(con)}{ate(con)}')
        col, con, _ = _resumo(res['entre_faces'])
        print(f'entre faces: colisões {col or "nenhuma"}; contatos {len(con)}{ate(con)}')
        for a, r in res['giro_porta'].items():
            col, con, _ = _resumo(r)
            print(f'giro {a}: colisões {col or "nenhuma"}; contatos {len(con)}{ate(con)}')
        with open(os.path.join(HERE, m.nome, 'conferencia-b3d.json'), 'w') as fh:
            json.dump({k: ({f: {' × '.join(p): r for p, r in d.items()} for f, d in v.items()} if k in ('interferencia', 'giro_porta')
                           else {' × '.join(p): r for p, r in v.items()} if k == 'entre_faces' else v) for k, v in res.items()},
                      fh, indent=1, ensure_ascii=False)
        print(f'conferir: {res["tempo"]} s')
    elif cmd == 'comparar':
        res = comparar(m, resto[0])
        if len(resto) > 1:
            with open(resto[1], 'w') as fh:
                json.dump(res, fh, indent=1, ensure_ascii=False)
    else:
        print(__doc__)
        return
    print(f'{cmd}: {time.time() - t:.0f} s')


if __name__ == '__main__':
    main(sys.argv[1:])
