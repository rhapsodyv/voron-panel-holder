"""Voron Trident 350 with the sliding lock on the panels (2026-10-30): the Trident (gerador/trident) in a
document of its own, so trident-panel-holder-v1 stays as it is. Only what differs is stated here."""
import herdar

herdar.copiar(herdar.de('trident', 'config'), globals())

NOME = 'Voron Trident 350 com trava'
DOC_NAME = 'trident-panel-holder-trava-v1'   # Fusion document (project Voron, folder Panel-Holder), a copy of trident-panel-holder-v1
STL_PREFIX = 'trident-trava-'

# One-piece lock coupon (construir.peca_unica_trava, 2026-10-31). v1 (the parameters' defaults) came out even
# locked: the barb only 0.09 past the opening. v2, one knob: the barb deeper (three variants, marked with grooves
# across the outer face near the far end); all three with longer legs, thinner where they bend, so going in
# forces less than v1 (the barb only at the far end of the locked tongue, 3 mm, and 12 mm from it to the solid fin)
_PU_V2 = {'fin_inset': '0.03 mm', 'peca_unica_perna': '0.8 mm', 'peca_unica_farpa_comprimento': '3 mm', 'peca_unica_dobra_fim': '12 mm',
          'peca_unica_comprimento': '50 mm'}
PECA_UNICA_VARIANTES = {f'f0{n}0': {**_PU_V2, 'peca_unica_farpa': f'0.{n} mm'} for n in (2, 3, 4)}
PECA_UNICA_MARCAS = {'f020': 1, 'f030': 2, 'f040': 3}
# v3: f040 held, but the user wants the barb long, not a 3 mm square. It only holds where the locked tongue backs
# it, and the legs need their bend before it, so a longer barb needs a longer travel: 10 -> 14 puts the barb under
# the whole full-width tongue (6.8 mm, 4.5 from the post) with the same slider; the cap grows twice that (a cap of
# its own, TRAVA_VARIANTES 'curso-14'), and everything starts 4 further in so the open cap stays on the piece.
# v2 and v3 keep fin_inset 0.03 (the standard went to 0.05 after them): they pair with the topo v2 slider
_CURSO_14 = {'fin_inset': '0.03 mm', 'trava_curso': '14 mm', 'trava_inicio': '17 mm'}
PECA_UNICA_VARIANTES['farpa-longa'] = {**_PU_V2, **_CURSO_14, 'peca_unica_farpa': '0.4 mm', 'peca_unica_comprimento': '54 mm',
                                       'peca_unica_farpa_comprimento': '( trava_lingueta - trava_entrada_comprimento )'}
TRAVA_VARIANTES = {**TRAVA_VARIANTES, 'curso-14': _CURSO_14}   # noqa: F821  (copied from the Trident's)
# v4 (the user's idea): the tongue as three teeth with narrow parts between them (trava_dentes). Open, the teeth sit in
# recesses of the legs; locked, they move half a pitch onto three barbs, so the barb grows (3 x 4 = 12 mm held) and the
# travel shrinks (5.35: geometria_trava), and so does the cap. The legs bend in the recesses (0.45 thick there), the far
# stretch 8 mm at full thickness; a slider and a cap of their own (TRAVA_VARIANTES 'dentes'), and the dot 4 mm (the travel
# is shorter than 5). The cap past the slot 4 at each end (not 1.5): 1.5 left flat ends of 1.45, which the corners'
# chamfers cut into the concave flanks; 24.9 long, still shorter than the standard 29.2
# The neck 5 long (not 6), so it comes up from below inside the first recess
_DENTES = {'fin_inset': '0.03 mm', 'trava_dentes': '3', 'trava_inicio': '11 mm', 'trava_capa_sobra': '4 mm',
           'trava_haste_comprimento': '5 mm'}
PECA_UNICA_VARIANTES['dentes'] = {**_PU_V2, **_DENTES, 'peca_unica_perna': 'fin_leg', 'peca_unica_farpa': '0.4 mm',
                                  'peca_unica_dobra_fim': '8 mm', 'peca_unica_comprimento': '54 mm', 'trava_indicador_diametro': '4 mm'}
TRAVA_VARIANTES['dentes'] = _DENTES
# v4b, the user's next question: are legs on both sides needed? The same as v4 (slider, cap and disc too) with only
# the outer (+s) leg; the acrylic side's is a wall fixed to the piece along its length, with no barb. 1 groove
PECA_UNICA_VARIANTES['dentes-1lado'] = {**PECA_UNICA_VARIANTES['dentes'], 'peca_unica_um_lado': '1'}
PECA_UNICA_MARCAS = {**PECA_UNICA_MARCAS, 'dentes-1lado': 1}
# v5 (the user's drawing on v4's section): one thick leg on the acrylic's side, fixed to the base, the other leg gone and
# the tongue moved out against the outer lip. The leg doesn't bend (nothing prints in the air): a hook 1 past the
# opening all along the piece; open, the slider floats aside in its slot and the piece goes in moved out 1.1;
# locked, the tongue fills the gap. The neck 0.73 further out, so its slot, 1.2 wider toward the acrylic for the
# float, keeps 0.8 of wall to the acrylic's stop; slider and cap of their own (TRAVA_VARIANTES 'gancho')
_GANCHO = {'fin_inset': '0.03 mm', 'trava_lingueta_desloc': '( fin_root_clearance + fin_leg + fin_inset - peca_unica_gancho_folga )',
           'trava_pescoco_desloc': '0.73 mm'}
PECA_UNICA_VARIANTES['gancho'] = {**_GANCHO, 'peca_unica_gancho': '1 mm'}
TRAVA_VARIANTES['gancho'] = _GANCHO
# v5b (the user: why is the neck's slot so wide? only the neck goes up through it): two variants of v5, the same leg,
# slider and cap, only the slot: 1 groove, the neck's width (no float); 2 grooves, wide only where the neck sits open
PECA_UNICA_VARIANTES['gancho-estreito'] = {**PECA_UNICA_VARIANTES['gancho'], 'peca_unica_rasgo_folga': '0'}
PECA_UNICA_VARIANTES['gancho-folga-aberta'] = {**PECA_UNICA_VARIANTES['gancho'], 'peca_unica_rasgo_folga': '2'}
PECA_UNICA_MARCAS = {**PECA_UNICA_MARCAS, 'gancho-estreito': 1, 'gancho-folga-aberta': 2}
# v6 (the user's video: the 2-groove piece rocks on the frame; locked, only the hook holds, with 0.1 under the lip and
# 0.1 at each side of the tongue, and its 45 deg face turns side play into lift): the wedge. The hook's slope goes up
# past the lip's corner (peca_unica_gancho_aperto, the knob: 0.1 and 0.2, grooves 3 and 4), and the tongue reaches the
# outer lip (a slider of its own, TRAVA_VARIANTES 'cunha', 1 groove on the stub): locking, its nose pushes the piece
# toward the acrylic and the slope pulls it onto the frame. The rest is the 2-groove v5 (its cap and disc too)
_CUNHA = {**_GANCHO, 'trava_lingueta_alarga': 'peca_unica_gancho_folga'}
TRAVA_VARIANTES['cunha'] = _CUNHA
TRAVA_MARCAS = {**TRAVA_MARCAS, 'cunha': 1}   # noqa: F821  (copied from the Trident's)
for _q in (1, 2):
    PECA_UNICA_VARIANTES[f'cunha-0{_q}0'] = {**PECA_UNICA_VARIANTES['gancho-folga-aberta'], **_CUNHA, 'peca_unica_gancho_aperto': f'0.{_q} mm'}
PECA_UNICA_MARCAS = {**PECA_UNICA_MARCAS, 'cunha-010': 3, 'cunha-020': 4}
# final (2026-11-01, the user: the 4-groove piece, cunha-020, stays): the slider and the cap of the 'cunha' with the stub's
# front flank as its rear one, 45 deg from the foot and then straight up (the rear, straight + slope, held firmer than
# the front's single slope), the same 1.5 flare, and the cap 1 taller (its flat ends and crest) for a stub 1 taller,
# so every ceiling over the socket stays. The piece doesn't change: the slot is as long as the travel, past the
# stub's wider top. 2 grooves on the stub; the cap keeps its 3 (they hold it and click), and it is 1 taller
# Then (the user, a drawing over the section): the crest's flat wider, so it covers the whole socket (its front corner
# was under the concave, 0.97 of ceiling), and a deeper fall to the ends, for the finger: the flat 7 -> 12, the ends
# back to the standard 2.6 thick (1.4 was too thin, the user), 2.8 under the crest, the concave sides 5 -> 6.6 down
# to them: the ends' flat (2.0) must reach past the corners' chamfers (1.5 from the ends), or the bed chamfer can't
# mitre the near-tangent facets of the concave against them
TRAVA_VARIANTES['final'] = {**_CUNHA, 'trava_toco_frente_reta': '1', 'trava_toco_aba': 'trava_toco_aba_tras', 'trava_toco_altura': '3.7 mm',
                            'trava_capa_crista': '5.6 mm', 'trava_capa_crista_largura': '12 mm',
                            'trava_capa_concavo': '6.6 mm'}
TRAVA_MARCAS = {**TRAVA_MARCAS, 'final': 2}
TRAVA_MARCAS_CAPA = {'final': 0}
