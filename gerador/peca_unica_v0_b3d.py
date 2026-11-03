"""The V0 in one piece with the lock, built in build123d (machine v0-peca-unica; the user, 2026-11-01: "o que acha de
gerar agora uma copia desse novo projeto em build123d para a v0?", "essa trava ficou boa"). For now lock v8's test kit in
the 1515 slot (ideias-trava/v0-peca-unica-trava-v8.png): the coupon piece with the plain leg, the sliders of
config.GANCHO_CURSOR and the cap, all built here (the Trident's slider and cap came from Fusion STEPs, and this slider's
lower half is new). The build123d helpers and lock v8's checks are peca_unica_b3d's.

What the 1515 changes (opening 3.0, lip 1.0 with a 0.25 round, the acrylic over the slot up to its stop at -0.5):
  - the opening is the leg (peca_unica_perna, 1.2) and the tongue (1.7); the hook (1.0) under the outer lip;
  - the slider floats in open by the hook and two clearances (1.2), so its neck can't sit over the acrylic: locked it is
    1.2 out of the stop, and open it reaches the stop, where the V0 lock's neck sits;
  - the tongue and the neck meet under the acrylic, where the slider widens (the band: its outer shoulder over the lip,
    trava_ombro_folga above the face once it has dropped; its top trava_degrau_folga under the base). The base under the
    acrylic is open only over the window, where the band sits open;
  - the cap: the Trident's final shape at the V0's width, its outer edge on the flat top's when locked.

Coupon frame (s, d, z) as the Trident's: s across (+ out), d out of the frame face, z along; the slider and the cap are
built open in z and locked in s (open = moved -boia), as kit v8 on the Trident.

  .venv-b3d/bin/python gerador/peca_unica_v0_b3d.py kit-v1     build, check and export stl/provas-peca-unica-trava-v1

Then the faces (mapa.py), as the one-piece Trident's: a corner + a middle + a corner on each edge, the middle with the
lock at its middle and its ends over the corners' legs on the 45 deg scarf. The top hat sides' verticals have no middle,
so the corner's vertical leg carries a lock of its own (mapa.CANTOS_TRAVA).

  .venv-b3d/bin/python gerador/peca_unica_v0_b3d.py tophat-lateral   build, check and export a top hat side
"""
import json
import math
import os
import sys
import time

import build123d as bd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import geometria_trava  # noqa: E402
import herdar  # noqa: E402
import perfis  # noqa: E402
import peca_unica_b3d as pu  # noqa: E402

MAQUINA = 'v0-peca-unica'
config = herdar.de(MAQUINA, 'config')
parametros = herdar.de(MAQUINA, 'parametros')
mapa = herdar.de(MAQUINA, 'mapa')
KIT = os.path.join(pu.REPO, 'stl', 'provas-peca-unica-trava-v1')
DISCO = os.path.join(pu.REPO, 'stl', 'provas-trava-v3', 'trava-indicador-1x.stl')


MUDANCAS = {}     # parameter -> expression, over the table (the web configurator's changed parameters)


def valores():
    """The parameter table evaluated (an expression naming a later parameter waits for it, as peca_unica_b3d.valores),
    MUDANCAS in place of the table's expressions."""
    vals, late = {}, []
    for _, n, e, _, _ in parametros.PARAMS:
        e = MUDANCAS.get(n, e)
        try:
            vals[n] = perfis.evaluate(e, vals)
        except NameError:
            late.append((n, e))
    for n, e in late + [(n, e) for n, e in MUDANCAS.items() if n not in vals and n not in dict(late)]:
        vals[n] = perfis.evaluate(e, vals)
    return vals


def secao_1515():
    """The 1515's section (referencia, the official V0.2 CAD) in the coupon's frame: its top slot is centred at s = 0
    and its outer face is at d = 0 there already."""
    return [tuple(p) for p in json.load(open(os.path.join(HERE, MAQUINA, 'referencia', config.PERFIL_JSON)))['loops'][0]]


def frame_cupom(a=-10.0, b=60.0):
    return pu._prisma(secao_1515(), 'xy', a, b)


def quina_aba(so):
    """Where a 45 deg slope down and out (s + d constant) first meets the outer lip's rounded corner: min of s + d."""
    return min(s + d for s, d in secao_1515() if so - 0.01 <= s <= so + 0.6 and -1.6 <= d <= -0.4)


def geo(v):
    """Lock v8's geometry in the 1515 slot (mm, coupon frame): geometria_trava's along the edge (window, neck, stub,
    travel, the cap's run, the dot's z) and, across it, the leg, the tongue, the hook, the neck out of the acrylic, the
    band that joins them under it, the slots, the cap and the drop."""
    g = geometria_trava.geo(v)
    so, gf, G = g['so'], v['peca_unica_gancho_folga'], v['peca_unica_gancho']
    B = G + 2 * gf                                        # the slider's float, open
    sr = -(so - gf)                                       # the leg's inner face, gf off the inner lip
    wl = sr + v['peca_unica_perna']                       # the leg's outer face = the tongue's inner one
    if wl - B < sr - 1e-6:
        raise ValueError(f'a perna ({v["peca_unica_perna"]}) é mais estreita que o cursor solto ({B})')
    stop = -so + v['panel_edge_clearance']                # the acrylic's edge comes at most to its stop
    n0 = stop + B                                         # the neck, locked: open it reaches the stop
    n1 = n0 + v['trava_pescoco_largura']
    queda = v['trava_folga_capa'] + v['trava_folga_toco']  # the cap onto the cover, then its socket's 45 deg flanks onto the stub
    base = g['T'] - v['peca_unica_vao']                   # the base's top, under the acrylic
    # the slots, open to locked: wide where the neck sits open and as long as the stub's flared top that comes up
    # through it there, then 45 deg out to the locked neck, as the leg's ramp pushes it
    zw = max(g['hz'][1] + v['trava_folga_janela'], g['tz'][1] + v['trava_toco_aba']) + v['trava_folga_rasgo']
    p0, p1 = g['path']

    def fenda(h0):
        return [(h0 - B, p0), (n1, p0), (n1, p1), (h0, p1), (h0, zw + B), (h0 - B, zw)]
    # the cap, as wide as the V0's, its outer edge on the flat top's when locked (open it is B further in)
    fo = v['frame_size'] / 2 - v['cover_cut']
    cap_s = (fo - v['trava_capa_largura'], fo)
    if cap_s[0] - B < -(v['frame_size'] / 2 + v['cover_overlap']) + v['cover_cut'] - 1e-6:
        raise ValueError('a capa aberta sai do topo plano da tampa')
    return dict(g, B=B, sr=sr, wl=wl, wr=so, stop=stop, n0=n0, n1=n1, queda=queda, base=base, zw=zw,
                ombro=queda + v['trava_ombro_folga'], degrau=base - v['trava_degrau_folga'],
                fenda=fenda(n0), canal=fenda(wl - v['trava_folga_rasgo']), cap_s=cap_s,
                ind=((cap_s[0] + cap_s[1]) / 2, g['cap_z'][1] + g['c'] / 2),
                tip=v['slot_depth'] - v['fin_tip_clearance'])


# ---------------------------------------------------------------- the piece
def _trava(corpo, v, g, za, zb, loc=None):
    """Lock v8 into a piece's body, in the coupon's frame (moved by loc into the piece's): the neck's slot through it,
    the band's channel under the acrylic (through the base over the window), the dot, then the plain leg from za to zb
    (the coupon's z) but the window, and the ramp at the window's far end."""
    m = (lambda s: s) if loc is None else (lambda s: s.moved(loc))  # noqa: E731
    top, B = g['top'], g['B']
    wl, sr, (w0, w1) = g['wl'], g['sr'], g['win']
    corpo = corpo - m(pu._prisma(g['fenda'], 'xz', -1.0, top + 1))
    corpo = corpo - m(pu._prisma(g['canal'], 'xz', -1.0, g['base'] + 0.01))
    (si, zi), di, dp = g['ind'], v['trava_indicador_diametro'], v['trava_indicador_profundidade']
    corpo = corpo - m(pu._cilindro('y', (si, zi), di, top - dp, top + 1))
    # the leg after the slots (the band's channel reaches 0.1 over its face next to the tongue)
    perna = [(wl, 0.0), (wl, -g['tip']), (sr, -g['tip']), (sr, 0.0)]
    for a, b in ((za, w0), (w1, zb)):
        corpo = corpo + m(pu._prisma(perna, 'xy', a, b))
    # the ramp at the window's far end, from the floating tongue's inner face to the leg's outer one
    return corpo - m(pu._prisma([(wl - B - 1, w1 - 1), (wl + 1, w1 + B + 1), (wl + 1, w1 - 1)], 'xz', -v['slot_depth'] - 1, 0.0))


def peca(v, g):
    """The coupon (peca_unica_comprimento), lying frame aside: the one-piece profile at the V0's sizes, the lock (_trava),
    the bed chamfer, and the support. Returns dict(peca, suporte, chanfro)."""
    L, top = v['peca_unica_comprimento'], g['top']
    corpo = _trava(pu._prisma(pu.perfil_corpo(v), 'xy', 0.0, L), v, g, 0.0, L)
    (si, zi), di = g['ind'], v['trava_indicador_diametro']
    corpo, feitas, falhas = pu.chanfro_mesa(pu._solido(corpo), 'y', top, v['trava_chanfro_mesa'],
                                            pular=lambda m: math.hypot(m[0] - si, m[2] - zi) < di / 2 + 0.2)
    return dict(peca=corpo, suporte=pu.suporte_meio(v, L, 0.0), chanfro=(feitas, falhas))


# ---------------------------------------------------------------- the slider and the cap
def cursor(v, g, aperto, marcas, orelha=True):
    """The slider (construir.trava_deslizante's, with the final stub), its lower half v8's in the 1515: the tongue
    from the leg to the outer lip, the band under the acrylic, the neck and the stub out of it; the hook on the tongue's
    outer face, its top slope queda + aperto past the lip's corner (quina_aba); the tongue's inner front corner at 45
    deg as the ramp; the keel clear of the slot's floor; marcas grooves on the stub's inner face (inside the cap's
    socket); the bed chamfer on its rear end and the one-layer tab (orelha). Returns dict(cursor, t)."""
    z0, lk, hz, tz, kr, gap = g['z0'], g['lk'], g['hz'], g['tz'], g['kr'], g['gap']
    th, fl = v['trava_toco_altura'], v['trava_toco_aba']
    so, G, B, wl, wr, n0, n1 = g['so'], v['peca_unica_gancho'], g['B'], g['wl'], g['wr'], g['n0'], g['n1']
    d0, d1, zl = -v['slot_depth'], -v['trava_lingueta_topo'], z0 + lk
    pc = min(v['trava_pescoco_chanfro'], tz[0] - hz[0])
    frente = [(tz[1], gap), (tz[1] + fl, gap + fl), (tz[1] + fl, gap + th)]
    tras = [(tz[0] - kr, gap + th), (tz[0] - kr, gap + kr), (tz[0], gap)]
    lado = [(z0, d0), (zl, d0), (zl, d1), (hz[1], d1), (hz[1], gap)] + frente + tras + [(hz[0] + pc, gap), (hz[0], gap - pc)]
    cur = pu._prisma([(d, z) for z, d in lado], 'yz', wl, n1)
    zt = tz[1] + fl + 1
    # out of the acrylic above the band; in the opening below it
    cur = cur - pu._caixa((wl - 1, n0), (g['degrau'], gap + th + 1), (z0 - 1, zt))
    cur = cur - pu._caixa((wr, n1 + 1), (d0 - 1, g['ombro']), (z0 - 1, zt))
    # the inner front corner at 45 deg, B: it meets the leg's ramp
    cur = cur - pu._prisma([(wl - 1, zl - B - 1), (wl + B + 1, zl + 1), (wl - 1, zl + 1)], 'xz', d0 - 1, 0.0)
    # the keel: the slot's floor only pushes up, so it ends the drop and trava_fundo_folga above it, flat, its outer
    # corner cut at 45 deg along the chord of the floor's round (the 1515's floor is flat between ±1.0); the round's
    # polyline itself left near-tangent edges the bed chamfer couldn't take
    t = quina_aba(so) - wr + g['queda'] + aperto
    kb, rr = d0 + g['queda'] + v['trava_fundo_folga'], so - 1.0
    cur = cur - pu._prisma([(wl - 1, kb), (so - rr, kb), (so + 1, kb + rr + 1), (so + 1, d0 - 1), (wl - 1, d0 - 1)], 'xy', z0 - 1, zt)
    cur = pu._solido(cur)
    # on its rear end: trava_chanfro_mesa, the stub's flat base trava_chanfro_encaixe
    # (edge by edge, a chamfer moves its neighbours' midpoints and chanfro_mesa skips them: again until none is left;
    # the shoulder's, next to the tongue's at a concave corner, OpenCascade won't take: cut by hand after)
    fino = lambda m: m[1] > gap - 0.5  # noqa: E731
    k, om = v['trava_chanfro_mesa'], g['ombro']
    ombro = lambda m: abs(m[1] - om) < 1e-3 and m[0] > wr  # noqa: E731
    a = fa = 0
    for _ in range(4):
        cur, x, fa = pu.chanfro_mesa(cur, 'z', z0, k, pular=lambda m: fino(m) or ombro(m))
        a += x
        if not x:
            break
    cur, b, fb = pu.chanfro_mesa(cur, 'z', z0, v['trava_chanfro_encaixe'], pular=lambda m: not fino(m))
    cur = pu._solido(cur - pu._prisma([(om - 1, z0 - 1), (om + k + 1, z0 - 1), (om - 1, z0 + k + 1)], 'yz', wr, n1 + 1))
    # the hook, 0.5 into the tongue, 45 deg slopes and 0.5 straight, its rear end with the joint's bed chamfer
    e = 0.5
    gancho = pu._prisma([(wr - e, t), (wr, t), (so + G, t - G), (so + G, t - G - 0.5), (wr, t - 2 * G - 0.5), (wr - e, t - 2 * G - 0.5)],
                        'xy', z0, zl)
    gancho = bd.chamfer(gancho.edges().filter_by_position(bd.Axis.Z, z0 - 1e-3, z0 + 1e-3), v['trava_chanfro_encaixe'])
    cur = cur + gancho
    # the grooves, 1.5 apart on the stub's foot, 1 wide and 0.6 deep
    zm0 = (tz[0] + tz[1]) / 2
    for i in range(marcas):
        zm = zm0 + (i - (marcas - 1) / 2) * 1.5
        cur = cur - pu._caixa((n0 - 1, n0 + 0.6), (gap, gap + th + 1), (zm - 0.5, zm + 0.5))
    if orelha:
        # the tab off the stub's flat base (the user's "auto brim"), its break trava_orelha_recuo inside the face the
        # cap's socket sits on
        ol, oh = v['trava_orelha_comprimento'], v['trava_orelha_altura']
        r, dt = oh + v['trava_orelha_recuo'], gap + th
        cur = cur - pu._prisma([(dt - r - 1, z0 - 1), (dt + 1, z0 - 1), (dt + 1, z0 + r + 1)], 'yz', wl - 1, n1 + 1)
        ins = v['trava_chanfro_encaixe'] + 0.1
        cur = cur + pu._caixa((n0 + ins, n1 - ins), (gap + kr + 0.05, dt + ol), (z0, z0 + oh))
    return dict(cursor=pu._solido(cur), t=t, chanfro=(a + b, fa + fb))


def capa(v, g):
    """construir.trava_deslizante's cap with the final stub's socket (both lips straight): the crest over the neck,
    concave flanks, flat ends, its socket open on the outer edge and blind at the stub's inner face, the corners at 45
    deg seen from above, trava_capa_sulcos grooves under its rear end, the bed chamfer on its inner end."""
    (c0, c1), (s0, s1) = g['cap_z'], g['cap_s']
    gap, top, zc, tz, kr = g['gap'], g['top'], g['zc'], g['tz'], g['kr']
    th, fl = v['trava_toco_altura'], v['trava_toco_aba']
    rim, crest = gap + v['trava_capa_aba'], top + v['trava_capa_crista']
    ch, cw, cc = v['trava_capa_chanfro'], v['trava_capa_crista_largura'] / 2, v['trava_capa_concavo']
    n = max(4, round(cc / 0.25))
    sobe = [(zc - cw - cc * (1 - i / n), rim + (crest - rim) * (i / n) ** 2) for i in range(n + 1)]
    lado = ([(c0, gap), (c0, rim - ch), (c0 + ch, rim)] + sobe + [(2 * zc - z, d) for z, d in reversed(sobe)] +
            [(c1 - ch, rim), (c1, rim - ch), (c1, gap)])
    cap = pu._prisma([(d, z) for z, d in lado], 'yz', s0, s1)
    ft, le = v['trava_folga_toco'], v['trava_capa_labio']
    frente = [(tz[1] + le + ft, gap - 1), (tz[1] + le + ft, gap + le), (tz[1] + fl + ft, gap + fl)]
    enc = [(tz[0] - le - ft, gap - 1)] + frente + [(tz[1] + fl + ft, gap + th), (tz[0] - kr - ft, gap + th),
                                                   (tz[0] - kr - ft, gap + kr), (tz[0] - le - ft, gap + le)]
    cap = cap - pu._prisma([(d, z) for z, d in enc], 'yz', g['n0'], s1 + 1)
    k = v['trava_capa_canto']
    for se, ss in ((s0, -1), (s1, 1)):
        for ze, sz in ((c0, -1), (c1, 1)):
            cap = cap - pu._prisma([(se - ss * (k + 1), ze + sz), (se + ss, ze - sz * (k + 1)), (se + ss, ze + sz)], 'xz', gap - 1, crest + 1)
    for i in range(round(v['trava_capa_sulcos'])):
        zm = c0 + 3 + 2.0 * i
        cap = cap - pu._caixa((s0 - 1, s1 + 1), (gap - 1, gap + 0.6), (zm - 0.5, zm + 0.5))
    cap, feitas, falhas = pu.chanfro_mesa(pu._solido(cap), 'x', s0, v['trava_chanfro_mesa'])
    return dict(capa=cap, chanfro=(feitas, falhas))


# ---------------------------------------------------------------- checks and the kit
def conferir(v, g, r, cursores, cap, fr=None):
    """Lock v8's checks (peca_unica_b3d.conferir_v8, on the 1515 member under the coupon; the sliders without their
    tab), and the V0's own: the acrylic with its edge at the stop (the piece, each slider open, along the travel and
    locked, the cap), each slider going in from below at the open position (the panel off the frame), and the cap's
    lift play on the stub, measured, against the drop the hook was drawn for. A face's piece comes in its lock's frame,
    fr the member under it there."""
    fr = frame_cupom() if fr is None else fr
    sem = {n: dict(cursor=c['sem_orelha']) for n, c in cursores.items()}
    res = {'queda': g['queda'], 'folga_encaixe_medida': pu.folga_encaixe(next(iter(sem.values()))['cursor'], cap),
           **pu.conferir_v8(dict(r, v=v, g=g), sem, cap, g['queda'], fr=fr)}
    acr = pu._caixa((-30.0, g['stop']), (g['base'], g['T']), (-10.0, 60.0))
    B, c, fj = g['B'], g['c'], v['trava_folga_janela']
    res['acrílico (borda no batente) × peça'] = round(pu._vol(r['peca'], acr), 3)
    for n, k in sem.items():
        k = k['cursor']
        o = res[n]
        o['acrílico × cursor no curso'] = round(max(pu._vol(bd.Pos(-B + min(max(dz - fj, 0.0), B), 0, dz) * k, acr)
                                                  for dz in [i / 2 for i in range(int(2 * c) + 1)]), 3)
        o['entrando por baixo × peça'] = {f'-{e}': round(pu._vol(bd.Pos(-B, -e, 0) * k, r['peca']), 3) for e in (1, 2, 4, 8, 13)}
    res['acrílico × capa aberta e travada'] = (round(pu._vol(bd.Pos(-B, 0, 0) * cap, acr), 3),
                                               round(pu._vol(bd.Pos(0, -v['trava_folga_capa'], c) * cap, acr), 3))
    return res


def _capa_deitada(cap, s0):
    """The cap as it prints, on its inner end: (s, d, z) -> (-z, d, s - s0)."""
    return bd.Pos(0, 0, -s0) * (bd.Rot(0, -90, 0) * cap)


def kit_v1(pasta=KIT):
    """Lock v8's test kit for the V0: the coupon with the plain leg, the sliders of config.GANCHO_CURSOR and one cap,
    checked and exported (the piece lying with its support; the sliders on their rear end, in the coupon's frame; the
    cap on its inner end; STEPs in the coupon's frame)."""
    t0 = time.time()
    v = valores()
    g = geo(v)
    r = peca(v, g)
    cap = capa(v, g)
    cursores = {}
    for n, (a, mk) in config.GANCHO_CURSOR.items():
        c = cursor(v, g, a, mk)
        c['sem_orelha'] = cursor(v, g, a, mk, orelha=False)['cursor']
        cursores[n] = c
    res = {'geometria': {k: (round(x, 3) if isinstance(x, float) else x) for k, x in g.items()
                         if k in ('B', 'sr', 'wl', 'wr', 'stop', 'n0', 'n1', 'queda', 'base', 'ombro', 'degrau', 'zw', 'cap_s', 'ind')},
           'quina_aba': round(quina_aba(g['so']), 3), 'gancho_topo': {n: round(c['t'], 3) for n, c in cursores.items()},
           'chanfro': {'peça': r['chanfro'], 'capa': cap['chanfro'], **{n: c['chanfro'] for n, c in cursores.items()}},
           **conferir(v, g, r, cursores, cap['capa'])}
    os.makedirs(pasta, exist_ok=True)
    with open(os.path.join(pasta, 'conferencia.json'), 'w') as fh:
        json.dump(res, fh, indent=1, ensure_ascii=False)
    top = g['top']
    nome = 'peca-unica-perna-lisa'
    bd.export_stl(pu._deitada(pu._solido(r['peca'] + r['suporte']), 'meio', top), os.path.join(pasta, f'{nome}-1x.stl'),
                  tolerance=0.005, angular_tolerance=0.1)
    peca_, sup = pu._deitada(r['peca'], 'meio', top), pu._deitada(r['suporte'], 'meio', top)
    peca_.label, sup.label = nome, 'suporte'
    bd.export_step(bd.Compound([peca_, sup]), os.path.join(pasta, f'{nome}.step'))
    qtd = {nome: 1}
    for n, c in cursores.items():
        bd.export_stl(c['cursor'], os.path.join(pasta, f'trava-cursor-{n}-1x.stl'), tolerance=0.002, angular_tolerance=0.1)
        bd.export_step(c['cursor'], os.path.join(pasta, f'trava-cursor-{n}.step'))
        qtd[f'trava-cursor-{n}'] = 1
    bd.export_stl(_capa_deitada(cap['capa'], g['cap_s'][0]), os.path.join(pasta, 'trava-capa-1x.stl'), tolerance=0.002, angular_tolerance=0.1)
    bd.export_step(cap['capa'], os.path.join(pasta, 'trava-capa.step'))
    qtd['trava-capa'] = 1
    with open(os.path.join(pasta, 'quantidades.json'), 'w') as fh:
        json.dump(qtd, fh, indent=1, ensure_ascii=False)
    print(json.dumps(res, indent=1, ensure_ascii=False))
    print(f'{pasta}: {qtd}; {time.time() - t0:.0f} s')
    return dict(v=v, g=g, r=r, cap=cap, cursores=cursores, res=res)


# ---------------------------------------------------------------- the faces
def meio(v, g, L):
    """A middle, L long between the corners, as peca_unica_b3d.meio with the plain leg: extruded joint_scarf longer at
    each end and cut there on the 45 deg scarf (its top passes over the corner's leg), the lock at its middle (the cap's
    whole run, open to locked, centred: the coupon's frame moved desloc along it), the plain leg from scarf to scarf but
    the window, the bed chamfer, the support. Returns dict(peca, suporte, desloc, loc, comprimento, chanfro)."""
    js, T, top = v['joint_scarf'], g['T'], g['top']
    Lt = L + 2 * js
    desloc = Lt / 2 - (g['cap_z'][0] + g['cap_z'][1] + g['c']) / 2
    loc = bd.Location((0, 0, desloc))
    corpo = _trava(pu._prisma(pu.perfil_corpo(v), 'xy', 0.0, Lt), v, g, js - desloc, Lt - js - desloc, loc)
    # the scarf at both ends (construir.pecas: cut below the cover's recess and at 45 deg above it)
    rec = T + v['cover_recess']
    for pts in ([(js, -12.0), (js, rec), (-2.0, top + 2), (-2.0, -12.0)],
                [(Lt - js, -12.0), (Lt - js, rec), (Lt + 2, top + 2), (Lt + 2, -12.0)]):
        corpo = corpo - pu._prisma([(d, z) for z, d in pts], 'yz', -60.0, 60.0)
    (si, zi), di = g['ind'], v['trava_indicador_diametro']
    corpo, feitas, falhas = pu.chanfro_mesa(pu._solido(corpo), 'y', top, v['trava_chanfro_mesa'],
                                            pular=lambda m: math.hypot(m[0] - si, m[2] - zi - desloc) < di / 2 + 0.2)
    return dict(peca=corpo, suporte=pu.suporte_meio(v, Lt, js, corpo), desloc=desloc, loc=loc, comprimento=Lt, chanfro=(feitas, falhas))


def canto(v, g, nome):
    """A corner with a lock (mapa.CANTOS_TRAVA) in one piece, as peca_unica_b3d.canto: the V0's L (mapa.CANTOS, legs of
    cover_corner mitred at 45 deg), each leg the one-piece body; the scarf at the end of leg A, which meets a middle (its
    end passes over it); there the doors' solid fin from where the edge's clips started; the finger grip (mapa.PEGA).
    Leg B has no middle (a top hat post), so it carries the lock, the coupon's frame turned onto it (s = fs/2 - x, d = z,
    the coupon's z = y - desloc: locking slides away from the corner, down the post) with the cap's whole run centred on
    the post: the plain leg from where the clips started but the window, the ramp, the slots, the dot. The bed chamfer
    on the outer face, the slot's edges too, as on the coupon. Returns dict(peca, suporte, desloc, loc, chanfro)."""
    fs, js, ext = v['frame_size'], v['joint_scarf'], 2.0
    T, top = g['T'], g['top']
    pernas = mapa.CANTOS[nome]
    if not pernas[0][4] or pernas[1][4]:
        raise ValueError(f'{nome}: só o canto com junta na perna A e a trava na B está portado')
    J = [perfis.evaluate(p[5] if len(p) > 5 else 'cover_corner', v) for p in pernas]
    sec = [(fs / 2 - s, d) for s, d in pu.perfil_corpo(v)]                  # (w, d)
    corpo = ((pu._prisma(sec, 'yz', -ext, J[0]) - pu._prisma([(-4, -4), (40, 40), (-4, 40)], 'xy', -20, 20)) +
             (pu._prisma(sec, 'xz', -ext, J[1]) - pu._prisma([(-4, -4), (40, -4), (40, 40)], 'xy', -20, 20)))
    rec = T + v['cover_recess']
    corpo = corpo - pu._prisma([(J[0], rec), (J[0] + 1, rec), (J[0] + 1, top + 2), (J[0] - js - 2, top + 2)], 'xz', -30, 30)
    # (a horizontal edge's clips stop at the post: the fin, part of the corner, starts peca_unica_aleta_poste off its face)
    u0 = perfis.evaluate(pernas[0][3], v) + (v['peca_unica_aleta_poste'] if pernas[0][3] == 'frame_size' else 0.0)
    for pol in pu.aletas(v, False):
        corpo = corpo + pu._prisma([(fs / 2 - s, d) for s, d in pol], 'yz', u0, J[0])
    desloc = v['tophat_height'] / 2 - (g['cap_z'][0] + g['cap_z'][1] + g['c']) / 2
    loc = bd.Location(bd.Plane(origin=(fs / 2, desloc, 0), x_dir=(-1, 0, 0), z_dir=(0, 1, 0)))
    corpo = _trava(corpo, v, g, perfis.evaluate(pernas[1][3], v) - desloc, J[1] - desloc, loc)
    corpo = pu._solido(pu._pega(corpo, v, mapa.PEGA[nome]))
    (si, zi), di = g['ind'], v['trava_indicador_diametro']
    cx, cy = fs / 2 - si, zi + desloc
    corpo, feitas, falhas = pu.chanfro_mesa(corpo, 'z', top, v['trava_chanfro_mesa'],
                                            pular=lambda m: math.hypot(m[0] - cx, m[1] - cy) < di / 2 + 0.2)
    return dict(peca=corpo, suporte=pu.suporte_canto(v, J, corpo), desloc=desloc, loc=loc, comprimento=J, chanfro=(feitas, falhas))


ESPELHO_XY = bd.Plane(origin=(0, 0, 0), x_dir=(1, 1, 0), z_dir=(1, -1, 0))   # a corner's legs swapped


def pecas_da_face(nome):
    """The face's one-piece pieces in place: list of dict(nome, tipo 'meio' or 'canto', borda, quadro, comprimento),
    quadro (origin, x, y, z) the piece frame's placement (bordas.colocacoes)."""
    v = valores()
    f = next(x for x in mapa.faces(v) if x['nome'] == nome)
    eixo = {e['nome']: e['eixo'] for e in f['bordas']}
    comp = {n: perfis.evaluate(e, v) for n, (_, e) in mapa.PECAS.items()}
    out = []
    for peca_, o, x, y, z, borda in mapa.colocacoes(v, comp, f):
        if peca_ in mapa.MEIOS:
            if eixo[borda] == 'Z':
                raise ValueError(f'{nome}: meio numa vertical (o espelho de peca_unica_b3d) ainda não portado')
            out.append(dict(nome=mapa.MEIOS[peca_], tipo='meio', borda=borda, quadro=(o, x, y, z), comprimento=comp[peca_]))
        elif borda == 'canto':
            out.append(dict(nome=peca_, tipo='canto', borda=borda, quadro=(o, x, y, z)))
    return out


def construir_face(nome):
    """Build every piece of the face once: name -> dict(peca, suporte, ...), in its own frame. A corner with the lock
    mirrored (mapa.CANTOS_TRAVA's values) is the mirror of its -hv across x = y (espelho True)."""
    v = valores()
    g = geo(v)
    espelhos = {b: a for a, b in mapa.CANTOS_TRAVA.items()}
    feitas = {}
    for p in sorted(pecas_da_face(nome), key=lambda p: p['nome'] in espelhos):
        if p['nome'] in feitas:
            continue
        t = time.time()
        if p['tipo'] == 'meio':
            r = meio(v, g, p['comprimento'])
        elif p['nome'] in mapa.CANTOS_TRAVA:
            r = canto(v, g, p['nome'])
        elif p['nome'] in espelhos:
            r = dict(feitas[espelhos[p['nome']]], espelho=True)
            r['peca'], r['suporte'] = (pu._solido(bd.mirror(r[k], ESPELHO_XY)) for k in ('peca', 'suporte'))
        else:
            raise ValueError(f'{p["nome"]}: só os cantos com trava estão portados')
        r['tempo'] = time.time() - t
        feitas[p['nome']] = r
    return feitas


def frame_face(nome):
    """The face's frame members (referencia/v0_frame.json, its group: the top hat's or the body's) whose outer face lies
    on the face's plane, as extrusions of the 1515 section. Across, each sits where the map puts its slot (the CAD's
    boxes are up to 0.06 off, and a piece's base lies on the frame face); along, the CAD's length."""
    v = valores()
    f = next(x for x in mapa.faces(v) if x['nome'] == nome)
    n, fs = f['n'], v['frame_size']
    k = [abs(c) for c in n].index(1)
    zth1 = v['frame_z0'] + v['body_height'] + v['tophat_gap'] + v['tophat_height']
    plano = zth1 if nome == 'tophat-tampo' else n[k] * (v['frame_width'] if k == 0 else v['frame_depth']) / 2
    grupo = 'top hat' if nome.startswith('tophat') else 'corpo'
    out = []
    for m in json.load(open(os.path.join(HERE, MAQUINA, 'referencia', config.FRAME_JSON)))['membros']:
        bb = m['bb']
        if m['grupo'] != grupo or abs(bb[k + 3 * (n[k] > 0)] - plano) > 0.1:
            continue
        a = 'XYZ'.index(m['eixo'])
        j = 3 - a - k
        cj = round((bb[j] + bb[j + 3]) / 2 * 2) / 2

        def p3(s, d):
            c = [0.0, 0.0, 0.0]
            c[k], c[j] = plano + n[k] * d, cj + s
            return c
        i0, i1 = sorted((k, j))
        pts = [(p3(s, d)[i0], p3(s, d)[i1]) for s, d in secao_1515()]
        out.append((m['nome'], pu._prisma(pts, 'xyz'[i0] + 'xyz'[i1], bb[a], bb[a + 3])))
    return out


def cunhas_vizinhas(nome):
    """The neighbouring faces' covers' wedges along each edge of a top hat side, from frame corner to frame corner (the
    other sides' on the posts, the lid's on top): peca_unica_b3d.cunhas_vizinhas's triangle (7.5, 0) (9, 1.5)
    (10.5, 0) in (s, d)."""
    v = valores()
    f = next(x for x in mapa.faces(v) if x['nome'] == nome)
    fs, ww = v['frame_size'], v['wall_width']
    zth1 = v['frame_z0'] + v['body_height'] + v['tophat_gap'] + v['tophat_height']
    tri = [(fs / 2, 0.0), (fs / 2 + ww / 2, ww / 2), (fs / 2 + ww, 0.0)]
    out = []
    for e in f['bordas']:
        k = 'XYZ'.index(e['eixo'])
        if k == 2:
            a, b = zth1 - v['tophat_height'], zth1
        else:
            b = (v['frame_width'] if k == 0 else v['frame_depth']) / 2
            a = -b
        t = bd.Vector(*e['a']).cross(bd.Vector(*f['n']))
        t = (round(t.X), round(t.Y), round(t.Z))
        o = list(e['ponto'])
        o[k] = 0.0
        pr = pu._prisma(tri, 'xy', min(a * t[k], b * t[k]), max(a * t[k], b * t[k]))       # the prism's z runs along t
        out.append((e['nome'], pr.moved(bd.Location(bd.Plane(origin=tuple(o), x_dir=e['a'], z_dir=t)))))
    return out


def conferir_face(nome, feitas, v, g):
    """Interference of the face's pieces in place (mm³): with the frame, in place and going in straight with the panel
    (out along the face's normal by peca_unica_b3d.ENTRANDO; the worst counts), with each other, with the neighbouring
    faces' wedges (in place and going in: as on the Trident, with that face already on a piece going in meets them),
    with the acrylic (its edges at the stops, the full gap thick); and each lock in its own frame (conferir: the slider
    config.CURSOR_FACES, the cap), on the middle and on the corner -hv (the -vh is its mirror)."""
    lista = pecas_da_face(nome)
    f = next(x for x in mapa.faces(v) if x['nome'] == nome)
    nf = f['n']
    frame, cunhas = frame_face(nome), cunhas_vizinhas(nome)
    chave = {id(p): f"{p['nome']} ({p['borda']})" for p in lista}
    no_lugar = {chave[id(p)]: pu._mover(feitas[p['nome']]['peca'], p['quadro']) for p in lista}
    aberto = {n: [bd.Pos(*(k * c for c in nf)) * s for k in pu.ENTRANDO] for n, s in no_lugar.items()}
    # the acrylic: its edges at the stops of the edges that have one (the top hat side's bottom edge sits in the body's
    # top gap, past the pieces), from the base under it to the cover's underside
    stop = -g['so'] + v['panel_edge_clearance']
    k = [abs(c) for c in nf].index(1)
    lo, hi = [-200.0, -200.0, 0.0], [200.0, 200.0, 500.0]
    for e in f['bordas']:
        j = [abs(c) for c in e['a']].index(1)
        lim = e['ponto'][j] + e['a'][j] * stop
        if e['a'][j] > 0:
            hi[j] = min(hi[j], lim)
        else:
            lo[j] = max(lo[j], lim)
    face0 = e['ponto'][k]
    lo[k], hi[k] = sorted((face0 + nf[k] * g['base'], face0 + nf[k] * g['T']))
    acr = pu._caixa(*zip(lo, hi))
    # the other top hat sides' pieces, the same ones (the front's middle, with the logo in the V0, isn't mapped): at the
    # posts their corners meet this face's on the wedges' diagonal
    vizinhas = []
    if nome.startswith('tophat-') and nome != 'tophat-tampo':
        for x in mapa.faces(v):
            if x['nome'] != nome and x['nome'].startswith('tophat-') and x['nome'] != 'tophat-tampo':
                vizinhas += [pu._mover(feitas[p['nome']]['peca'], p['quadro']) for p in pecas_da_face(x['nome'])]
    res = {'frame': {}, 'frame_entrando': {}, 'entre_pecas': {}, 'cunhas': {}, 'cunhas_entrando': {}, 'acrílico': {},
           'faces_vizinhas': {}, 'faces_vizinhas_entrando': {}}
    for n, s in no_lugar.items():
        res['frame'][n] = round(sum(pu._vol(s, m) for _, m in frame), 3)
        res['frame_entrando'][n] = round(max(sum(pu._vol(a, m) for _, m in frame) for a in aberto[n]), 3)
        res['cunhas'][n] = round(sum(pu._vol(s, c) for _, c in cunhas), 3)
        res['cunhas_entrando'][n] = round(max(sum(pu._vol(a, c) for _, c in cunhas) for a in aberto[n]), 3)
        res['acrílico'][n] = round(pu._vol(s, acr), 3)
        res['faces_vizinhas'][n] = round(sum(pu._vol(s, x) for x in vizinhas), 3)
        res['faces_vizinhas_entrando'][n] = round(max(sum(pu._vol(a, x) for x in vizinhas) for a in aberto[n]), 3)
    nomes = list(no_lugar)
    for i, a in enumerate(nomes):
        for b in nomes[i + 1:]:
            res['entre_pecas'][f'{a} × {b}'] = round(pu._vol(no_lugar[a], no_lugar[b]), 3)
    a, mk = config.GANCHO_CURSOR[config.CURSOR_FACES]
    vk = dict(v, peca_unica_vao=perfis.evaluate(config.KIT_VAO, v))          # the slider and cap as kit v1 printed them
    cursores = {config.CURSOR_FACES: dict(sem_orelha=cursor(vk, geo(vk), a, mk, orelha=False)['cursor'])}
    cap = capa(vk, geo(vk))['capa']
    res['trava'] = {}
    for p in lista:
        r = feitas[p['nome']]
        if r.get('espelho') or p['nome'] in res['trava']:
            continue
        L = r['comprimento'] if p['tipo'] == 'meio' else v['tophat_height']
        fr = frame_cupom(-r['desloc'] - (10.0 if p['tipo'] == 'meio' else 0.0), L - r['desloc'] + (10.0 if p['tipo'] == 'meio' else 0.0))
        res['trava'][p['nome']] = {'desloc': round(r['desloc'], 3),
                                   **conferir(v, g, dict(peca=r['peca'].moved(r['loc'].inverse())), cursores, cap, fr=fr)}
    return res


def exportar_face(nome, feitas, pasta, top):
    """Each piece as it prints (piece and support in one body, lying, outer face at Z = 0), a STEP of each with the two
    bodies apart, the lock's parts as kit v1 printed them (the slider config.CURSOR_FACES and the cap, mirrored for the
    mirrored corners; the V0 lock's disc), and quantidades.json."""
    os.makedirs(pasta, exist_ok=True)
    lista = pecas_da_face(nome)
    qtd = {}
    for p in lista:
        qtd[p['nome']] = qtd.get(p['nome'], 0) + 1
    tipos = {p['nome']: p['tipo'] for p in lista}
    for n, r in feitas.items():
        junto = pu._deitada(pu._solido(r['peca'] + r['suporte']), tipos[n], top)
        bd.export_stl(junto, os.path.join(pasta, f'{n}-{qtd[n]}x.stl'), tolerance=0.005, angular_tolerance=0.1)
        peca_, sup = pu._deitada(r['peca'], tipos[n], top), pu._deitada(r['suporte'], tipos[n], top)
        peca_.label, sup.label = n, 'suporte'
        bd.export_step(bd.Compound([peca_, sup]), os.path.join(pasta, f'{n}.step'))
    espelhos = sum(qtd[n] for n, r in feitas.items() if r.get('espelho'))
    normais = sum(qtd[n] for n in feitas) - espelhos
    for parte, stl in (('cursor', f'trava-cursor-{config.CURSOR_FACES}-1x.stl'), ('capa', 'trava-capa-1x.stl')):
        stl = os.path.join(KIT, stl)
        with open(stl, 'rb') as a, open(os.path.join(pasta, f'trava-{parte}-{normais}x.stl'), 'wb') as b:
            b.write(a.read())
        qtd[f'trava-{parte}'] = normais
        if espelhos:
            pu._stl_espelho(stl, os.path.join(pasta, f'trava-{parte}-espelho-{espelhos}x.stl'))
            qtd[f'trava-{parte}-espelho'] = espelhos
    with open(DISCO, 'rb') as a, open(os.path.join(pasta, f'trava-indicador-{normais + espelhos}x.stl'), 'wb') as b:
        b.write(a.read())
    qtd['trava-indicador'] = normais + espelhos
    with open(os.path.join(pasta, 'quantidades.json'), 'w') as fh:
        json.dump(dict(sorted(qtd.items())), fh, indent=1, ensure_ascii=False)
    return qtd


def face(saida, pasta=None):
    """Build, check and export a face (mapa.FACES: export name -> the face): stl/peca-unica-<saida>-v<FACES_VERSAO>,
    the checks in gerador/v0-peca-unica/conferencia-<saida>[-v<FACES_VERSAO>].json."""
    nome = mapa.FACES[saida]
    pasta = pasta or os.path.join(pu.REPO, 'stl', f'peca-unica-{saida}-v{config.FACES_VERSAO}')
    t = time.time()
    v = valores()
    g = geo(v)
    feitas = construir_face(nome)
    for n, r in feitas.items():
        print(f'{n}: {r["peca"].volume:.0f} mm³ (+ suporte {r["suporte"].volume:.0f}), chanfro de mesa {r["chanfro"]}, {r["tempo"]:.1f} s')
    res = {'face': nome, 'chanfro': {n: r['chanfro'] for n, r in feitas.items() if not r.get('espelho')},
           **conferir_face(nome, feitas, v, g)}
    conf = f'conferencia-{saida}.json' if config.FACES_VERSAO == 1 else f'conferencia-{saida}-v{config.FACES_VERSAO}.json'
    with open(os.path.join(HERE, MAQUINA, conf), 'w') as fh:
        json.dump(res, fh, indent=1, ensure_ascii=False)
    for k, d in res.items():
        if k == 'trava':
            for n, x in d.items():
                print(f'trava {n}: {json.dumps(x, ensure_ascii=False)}')
        elif isinstance(d, dict):
            nz = {a: b for a, b in d.items() if b != 0.0}
            print(f'{k}: {len(d)} casos, não zerados {nz if nz else "nenhum"}')
    qtd = exportar_face(nome, feitas, pasta, g['top'])
    print(f'exportado em {pasta}: {qtd}; {time.time() - t:.0f} s')
    return feitas, res


def main(args):
    if args and args[0] == 'kit-v1':
        kit_v1(*args[1:])
        return
    if args and args[0] in mapa.FACES:
        face(*args)
        return
    print(__doc__)


if __name__ == '__main__':
    main(sys.argv[1:])
