"""Voron Trident 350 in one piece with the lock (2026-11-01, the user: "uma cópia do projeto ... peça única e com
trava"): clip and cover together, printed lying (perfis.PECA_UNICA, the wedge hook of the chosen coupon
cunha-020), with the final slider and cap. Built on the Trident with the lock (gerador/trident-trava), in a
document of its own, so trident-panel-holder-trava-v1 stays as it is. Only what differs is stated here."""
import herdar

herdar.copiar(herdar.de('trident-trava', 'config'), globals())

NOME = 'Voron Trident 350 peça única com trava'
DOC_NAME = 'trident-panel-holder-peca-unica-v1'   # Fusion document (project Voron, folder Panel-Holder), a copy of trident-panel-holder-trava-v1
STL_PREFIX = 'trident-peca-unica-'

# The pieces are built in build123d (gerador/peca_unica_b3d.py; the user, 2026-11-01: "se quiser fazer essa nova
# versão ... com o build123d ao invés do fusion, também pode"). Split A (the user: "fica mais bonito"): corner +
# middle + corner on each edge. Only the middles have the hook and the lock, as the chosen coupon and slider:
PECA = 'cunha-020'       # PECA_UNICA_VARIANTES: the hook, the window, the neck's slot (4 grooves, aperto 0.2)
TRAVA = 'final'          # TRAVA_VARIANTES: the slider and the cap (stl/trident-provas-peca-unica-trava-v7)
# The wedge (peca_unica_gancho_aperto) only over the coupon's length around the lock (the user agreed: a 250 mm leg
# all wedged would take ~5x the coupon's force); elsewhere the hook's slope just meets the lip's corner
APERTO_LONGE = '0 mm'
# The corners have no hook and no lock (the user: "o encaixe ... pode ser simplesmente de apoio"): the middles' ends
# pass over their legs on the Trident's 45 deg scarf and hold them down, and the corners go in straight. Their fin is
# the doors' solid fin, except the side panels' front corners, which carry the door's hinge (its weight pulls the
# bottom one off the frame): there the clips' barbed split fin, at the machine's fin_inset
CANTOS_FARPA = ('canto-lat-dir-dobradica-base', 'canto-lat-dir-dobradica-topo',
                'canto-lat-esq-dobradica-base', 'canto-lat-esq-dobradica-topo')

# Lock v8 (2026-11-01, the user: "quando ela estiver presa no acrílico, não vai se mexer"): the piece can't go in
# moved out 1.1, so the hook moves from the piece's leg to the slider's tongue, under the OUTER lip. The piece's leg
# is plain, with a 45 deg ramp at the window's far end; the slider floats in open (the neck slot's 1.2, as in v6),
# the ramp pushes it out as it slides to lock, the hook's slope pulls it down, and the cap clamps the cover. The knob:
# the squeeze left once the cap sits on the cover and its socket has closed on the stub (mm), and the stub's grooves
# in place of v7's 2. The piece (no grooves) and v7's cap are the same for all three.
GANCHO_CURSOR = {'gancho-020': (0.2, 1), 'gancho-030': (0.3, 2), 'gancho-040': (0.4, 3)}

# The faces after lock v8 passed (2026-11-01, the user: "Esse design deu certo, podemos fechar até com o cursor com 1
# sulco"): the middles with the plain leg and its ramp, going in straight with the panel; the slider gancho-020 as the
# kit printed it (stl/trident-provas-peca-unica-trava-v8, its groove kept), v7's cap. FACES_VERSAO names the export
# folder (stl/trident-peca-unica-<face>-v2); v1 was the leg's hook: PERNA_LISA False and FACES_VERSAO 1 build it again.
PERNA_LISA = True
CURSOR_V8 = 'gancho-020'
FACES_VERSAO = 2

# Kit v9 (2026-11-02, the user: "da pra diminuir um pouco ele, ta meio grosso ainda. o da v0 está bom"): gancho-020
# (1 groove) is still a bit thick, and the V0's 1-groove slider squeezes 0.1. Two thinner sliders, one groove more per
# 0.05 less: 2 grooves 0.15, 3 grooves 0.10 (v8's 2 and 3 grooves, 0.3 and 0.4, go out). Nothing else changes: the
# piece and v7's cap are the ones already printed (stl/trident-provas-peca-unica-trava-v9).
GANCHO_CURSOR_V9 = {'gancho-015': (0.15, 2), 'gancho-010': (0.1, 3)}
