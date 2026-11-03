"""Voron Trident 350 (frame Misumi HFSB5-2020): what the shared generator needs to know about this machine.

The reference CAD (Fusion "Trident_Assembly", project Voron) is a Trident 250: same height, frame
100 mm narrower and shallower. Its topology is used; lengths come from parametros.py (350).
"""
NOME = 'Voron Trident 350'
DOC_NAME = 'trident-panel-holder-v1'     # Fusion document (project Voron, folder Panel-Holder)
FRAME_JSON = 'frame_350.json'            # frame members, scaled from the CAD's 250 (referencia/)
PERFIL_JSON = 'perfil_2020_usuario.json'  # the CAD's section (misumi_2020.json) with the user's measured 6.35 slot opening
FRAME_COMPONENT = 'frame-trident'
REF_COMPONENT = 'ref-perfil-2020'
STL_PREFIX = 'trident-'
LOGO_JSON = None
PUXADOR = ('tampa-porta-centro-v', 'dentro')   # handle like the V0's, on each door's centre cover, facing in

# test coupons (v8): v7 eased the long clip, but it is still hard to put in and very hard to take out.
# The lip bends the leg 2 mm from its root (the lip's thickness): a short, stiff lever, so the leg's
# thickness (stiffness ~ thickness cubed) eases both ways; a barb face closer to vertical (less wedge)
# eases taking it out; barb stretches cut the length that bends. Squeeze 0.2 and barb 0.3 as the
# standard; length of a real clip-padrao-h1 (78.3). Grooves on the dovetail top (MARCAS) tell them apart.
_H1 = 'clip_run_h / 6'
_FINAS = {'fin_leg': '0.75 mm', 'fin_tip_leg': '0.6 mm'}
# 3, reprint: the first had a 0.38 wall near the tip (the leg leans in there) and the slicer dropped it;
# tip 0.6 and the inner face's straight part to 4.2 give 0.48, root still 0.6 (where the lip bends it)
_MUITO_FINAS = {'fin_leg': '0.6 mm', 'fin_tip_leg': '0.6 mm', 'fin_inner_straight': '4.2 mm'}
_FACE30 = {'fin_barb_angle': '30 deg'}
VARIANTES = {
    'clip-padrao': {},
    'clip-m1-pernas-finas': {'test_length': _H1, **_FINAS},
    'clip-m2-finas-30': {'test_length': _H1, **_FINAS, **_FACE30},
    'clip-m3-muito-finas-30': {'test_length': _H1, **_MUITO_FINAS, **_FACE30},
    'clip-m4-finas-30-trechos': {'test_length': _H1, **_FINAS, **_FACE30, 'fin_anchor_length': '10 mm'},
    # v8 result: none has play; 2 and 4 start to feel right, 3 failed to print (being reprinted). 5 eases
    # it about as much as 3 with the printable 0.75 legs: smaller barb (peak 0.3 -> 0.2) and squeeze 0.15
    'clip-m5-finas-30-farpa-02': {'test_length': _H1, **_FINAS, **_FACE30, 'fin_barb': '0.2 mm', 'fin_squeeze': '0.15 mm'},
}
MARCAS = {'clip-m1-pernas-finas': 1, 'clip-m2-finas-30': 2, 'clip-m3-muito-finas-30': 3, 'clip-m4-finas-30-trechos': 4,
          'clip-m5-finas-30-farpa-02': 5}
# v10 clips: 3 and 5 still too hard both ways (2 and 4 started to feel right). Force has to be low per mm:
# a short coupon may feel loose, 50 cm of clip will not. All below 4, every leg wall >= 0.46. Marks go on
# from 6 so no two printed clips share a count.
_RAIZ05 = {'fin_leg': '0.5 mm', 'fin_tip_leg': '0.6 mm', 'fin_inner_straight': '4.2 mm'}
_RAIZ06 = {'fin_leg': '0.6 mm', 'fin_tip_leg': '0.6 mm', 'fin_inner_straight': '4.2 mm'}
_FACE20 = {'fin_barb_angle': '20 deg', 'fin_barb': '0.2 mm', 'fin_squeeze': '0.15 mm'}
VARIANTES.update({
    'clip-m6-raiz-05': {'test_length': _H1, **_RAIZ05, **_FACE30},
    'clip-m7-face-20': {'test_length': _H1, **_RAIZ06, **_FACE20},
    'clip-m8-raiz-05-face-20': {'test_length': _H1, **_RAIZ05, **_FACE20},
    'clip-m9-trechos': {'test_length': _H1, **_RAIZ06, **_FACE30, 'fin_anchor_length': '10 mm'},
})
MARCAS.update({'clip-m6-raiz-05': 6, 'clip-m7-face-20': 7, 'clip-m8-raiz-05-face-20': 8, 'clip-m9-trechos': 9})

# v11 clips: one knob, as the user asked: the standard clip with the legs moved toward the slot centre
# (fin_inset per side). v7's "pernas-625" was 0.05 (still hard). Marks keep counting: 10 and 11.
VARIANTES.update({
    'clip-m10-recolhe-010': {'test_length': _H1, 'fin_inset': '0.1 mm'},
    'clip-m11-recolhe-015': {'test_length': _H1, 'fin_inset': '0.15 mm'},
})
MARCAS.update({'clip-m10-recolhe-010': 10, 'clip-m11-recolhe-015': 11})

# v12 clips: v10/v11 result: 9 (barb stretches) best, 10/11 (legs moved in) hard and loose once in, the rest
# too tight; and the barb stretches wear (photo: shaved, stress-whitened). The legs do not flex: the 2020
# lip is 2 mm, so the barb pushes 2 mm from the root and a 1 mm leg bent 0.3 there would strain ~11%; the
# barb yields instead. Relief (fin_relief): each leg's root goes 2 mm up into the 3 mm base, lever 2 -> 4 mm,
# stiffness x0.12, strain 2.8% (2.1% with 0.75 legs). Standard otherwise, barb all along (stretches
# concentrate the wear). The old clips are done: marks restart at 1.
VARIANTES.update({
    'clip-a1-alivio-2': {'test_length': _H1, 'fin_relief': '2 mm'},
    'clip-a2-alivio-2-finas': {'test_length': _H1, 'fin_relief': '2 mm', **_FINAS},
})
MARCAS.update({'clip-a1-alivio-2': 1, 'clip-a2-alivio-2-finas': 2})
# v13: the user's idea, the leg only 0.4 thick from the root to about its middle (fin_neck, 2.8 down), then
# 45 deg out to the standard 1.0; standard otherwise. Same strain as the V0's legs (~4.5% passing the barb),
# with the 2020 wedge kept (no play). Mark 3 (v12's 1 and 2 may be printed).
# The slicer left the neck clip's barb hollow: below the 0.4 neck the leg was 1.35 wide at the barb, one
# 0.4 perimeter loop covers ~0.8 and leaves a hollow core. Now the whole leg is 0.4 (tip 0.6, inner face
# straight to 4.2 for the 0.4 wall at the tip): at most 0.75 wide at the barb, one loop fills it. Mark 4.
VARIANTES['clip-p4-perna-04'] = {'test_length': _H1, 'fin_leg': '0.4 mm', 'fin_tip_leg': '0.6 mm', 'fin_inner_straight': '4.2 mm'}
MARCAS['clip-p4-perna-04'] = 4
# The V0's leg at 2x (the 2020 lip is 2 mm, the V0's 1 mm) with the real 6.35 opening, never tested: v1-v4
# had the V0 legs but sized for a 6.0 opening, and the barb was lost in the extra 0.175 a side. Standard 1.0
# leg; V0 barb 0.06 -> 0.12, starting 0.2 -> 0.4 below the lip over a 0.2 -> 0.4 ramp: no wedge (the panel
# pulls the clip out against the lip once assembled, as on the V0). Mark 5.
VARIANTES['clip-p5-v0-escalado'] = {'test_length': _H1, 'fin_barb': '0.12 mm', 'fin_barb_gap': '0.4 mm', 'fin_barb_ramp': '0.4 mm'}
MARCAS['clip-p5-v0-escalado'] = 5
# v14, from v13's result: 5 (V0 at 2x) is the best in and out but has a little play once in; 4 (0.4 legs +
# wedge) is good too, but its thin legs look like they will tire. 6 = 5 whose barb face touches the lip
# corner (squeeze 0.06, face at 23 deg like the V0's, starting 0.26 above the lip foot): no play, still
# easy. 7 = 4 with 0.5 legs; strain grows with thickness for the same bend, so it bends 20% less (barb
# 0.24, squeeze 0.16) to strain the same as 4 (3% in, 4.5% passing); at most 0.79 wide (not hollow).
VARIANTES['clip-p6-v0-aperto'] = {'test_length': _H1, 'fin_barb': '0.12 mm', 'fin_squeeze': '0.06 mm', 'fin_barb_angle': '23 deg'}
VARIANTES['clip-p7-perna-05'] = {'test_length': _H1, 'fin_leg': '0.5 mm', 'fin_tip_leg': '0.6 mm', 'fin_inner_straight': '4.2 mm',
                                 'fin_barb': '0.24 mm', 'fin_squeeze': '0.16 mm'}
MARCAS['clip-p6-v0-aperto'] = 6
MARCAS['clip-p7-perna-05'] = 7

# v9 covers: the clip is very hard to slide into the cover (pliers barely pull it out). Besides the dovetail
# flanks (0.05), the cover touched the clip with no gap on two flat faces: the wall's inner face (6.7 tall)
# and the shoulder next to the dovetail (5.3 wide); a printed cavity comes out smaller. Three covers at the
# h1 length, 1 to 3 grooves on the outer face: flank clearance / wall-and-shoulder clearance.
_TAMPAS = {
    'tampa-t1-folga-010': ('0.1 mm', '0.15 mm'),
    'tampa-t2-folga-015': ('0.15 mm', '0.2 mm'),
    'tampa-t3-folga-020': ('0.2 mm', '0.3 mm'),
}
for _i, (_n, (_dc, _cc)) in enumerate(_TAMPAS.items(), 1):
    VARIANTES[_n] = {'_perfil': 'tampa-parede', 'test_length': _H1, 'dovetail_clearance': _dc, 'cover_clip_clearance': _cc}
    MARCAS[_n] = _i
PROVAS = ['clip-padrao', *MARCAS, 'tampa-parede']
CONJUNTOS = [('clip-padrao', 'tampa-parede', '0 mm', '0 mm', True)] + [
    (name, 'tampa-parede', '0 mm', '0 mm', True) for name in MARCAS if name.startswith('clip')] + [
    ('clip-padrao', name, '0 mm', '0 mm', True) for name in _TAMPAS]

# Sliding lock (trava_deslizante): variants of the slider and its cap, built beside the standard ones
# ('trava-cursor-<name>', 'trava-capa-<name>') and fitting the same clip and cover, so the stem (set by
# their slots) stays; marked with TRAVA_MARCAS grooves (cap underside near the rear end, slider stub's far end).
# A variant that only changes the slider (trava_folga_haste) is built with parte='cursor' and uses the standard cap.
TRAVA_VARIANTES = {'folga-005': {'trava_folga_haste': '0.05 mm'}}   # v8: neck 2.9 in the 3.0 slots (the standard has 0)
# a cap-only variant (parte='capa') changes trava_folga_toco; the 2026-10-29 round (encaixe-005/010/015, marks
# 1-3) chose 0.15, now the standard. A cap's marks take the place of the standard cap's trava_capa_sulcos (3), so
# a cap variant needs a count other than 3
TRAVA_MARCAS = {'folga-005': 1}

