"""Voron V0.2 in one piece with the lock (2026-11-01, the user: "o que acha de gerar agora uma copia desse novo projeto
em build123d para a v0?", "essa trava ficou boa"): the one-piece Trident (gerador/trident-peca-unica) on the V0, built
in build123d only (gerador/peca_unica_v0_b3d.py). Built on the V0 with the lock (gerador/v0-trava), so its slider's
neck, stub and cap sizes carry over. Only what differs is stated here."""
import herdar

herdar.copiar(herdar.de('v0-trava', 'config'), globals())

NOME = 'Voron V0.2 peça única com trava'
STL_PREFIX = ''                          # stl/provas-peca-unica-trava-<version>, as the V0's lock coupons

# Lock v8 of the one-piece Trident in the 1515 slot (ideias-trava/v0-peca-unica-trava-v8.png, the user: "Sim, vamos
# fazer um kit de prova pra v0 nesse formato"): the piece's leg plain, the hook on the slider's tongue under the outer
# lip, the slider floating in open and pushed out by the leg's ramp to lock; the Trident's final stub and cap (both
# flanks 45 deg + straight, 1 taller), the V0's cap width. The knob, as on the Trident: the squeeze left once the cap
# sits on the cover and its socket has closed on the stub (mm), with the stub's grooves. The 1515's lip is thinner
# and rounded (0.25), so one step below the Trident's choice (0.2) and one above
GANCHO_CURSOR = {'gancho-010': (0.1, 1), 'gancho-020': (0.2, 2), 'gancho-030': (0.3, 3)}

# The faces after kit v1 passed (2026-11-01, the user: "a trava da v0 funcionou, até com o cursor com 1 sulco!"): the
# slider gancho-010 and the cap as the kit printed them (stl/provas-peca-unica-trava-v1). FACES_VERSAO names the export
# folder (stl/peca-unica-<face>-v<FACES_VERSAO>); v2 (2026-11-02): the acrylic's gap 3.0 and the support's two-layer
# lamina (parametros.py)
CURSOR_FACES = 'gancho-010'
FACES_VERSAO = 2

# Kit v1's slider and cap were built with the acrylic's gap as it was then (peca_unica_vao 2.8; 3.0 since 2026-11-02):
# the faces' checks build them with it, as they print (the slider's band under the acrylic sits 0.2 nearer it)
KIT_VAO = '2.8 mm'
