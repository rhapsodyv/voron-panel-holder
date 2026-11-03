"""Voron V0.2 with the sliding lock on the panels (2026-10-29): the V0 (gerador/v0) in a document of its
own, so panel-holder-v13 stays as it is. Only what differs is stated here."""
import herdar

herdar.copiar(herdar.de('v0', 'config'), globals())

NOME = 'Voron V0.2 com trava'
DOC_NAME = 'panel-holder-trava-v1'       # Fusion document (project Voron, folder Panel-Holder), a copy of panel-holder-v13
STL_PREFIX = 'trava-'                    # stl/trava-provas-<version>

# the cap of the sides' top edge: that cover (tampa-simples) sits top_overhang further out than the slot, so its
# cap is centred top_overhang further out over the same slider (a longer socket, open on the same side); it keeps
# the standard cap's grooves (no mark: the socket's place tells them apart)
TRAVA_VARIANTES = {**TRAVA_VARIANTES, 'topo': {'trava_capa_desloc': 'top_overhang'}}   # noqa: F821
