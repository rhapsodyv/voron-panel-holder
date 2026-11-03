"""Voron V0.2 (frame Misumi 1515): what the shared generator needs to know about this machine."""
NOME = 'Voron V0.2'
DOC_NAME = 'panel-holder-v13'            # Fusion document (project Voron, folder Panel-Holder)
FRAME_JSON = 'v0_frame.json'             # frame members from the official CAD (referencia/)
PERFIL_JSON = 'misumi_1515.json'         # extrusion section (referencia/)
FRAME_COMPONENT = 'frame-v0'
REF_COMPONENT = 'ref-perfil-1515'        # extrusion piece next to the test coupons
STL_PREFIX = ''                          # stl/<prefix>provas-<version>
LOGO_JSON = 'logo_voron.json'

# test coupons: (clip, cover, cover shift along s, acrylic shift along s, show the extrusion piece)
PROVAS = ['clip-padrao', 'clip-parede', 'clip-u', 'clip-porta', 'clip-porta-lateral', 'clip-porta-dobradica',
          'tampa-parede', 'tampa-simples']
CONJUNTOS = [
    ('clip-padrao', 'tampa-parede', '0 mm', '0 mm', True),
    ('clip-parede', 'tampa-simples', 'top_overhang', '0 mm', True),
    ('clip-u', 'tampa-parede', '0 mm', 'u_base_width - u_end_wall - 3 mm', False),
    ('clip-porta', 'tampa-parede', '0 mm', 'door_stop_extra', True),
    ('clip-porta-lateral', 'tampa-parede', '0 mm', '0 mm', True),
    ('clip-porta-dobradica', 'tampa-parede', '0 mm', '0 mm', True),
]

# Sliding lock coupon (trava_deslizante), as on the Trident: a slider variant (parte='cursor') uses the
# standard cap; marked with TRAVA_MARCAS grooves in the stub's -s face.
TRAVA_VARIANTES = {'folga-005': {'trava_folga_haste': '0.05 mm'}}   # neck 1.4 in the 1.5 slots (the standard has 0)
# a cap-only variant (parte='capa') changes trava_folga_toco; the 2026-10-29 round (encaixe-005/010/015, marks
# 1-3) chose 0.15, now the standard. A cap's marks take the place of the standard cap's trava_capa_sulcos (3), so
# a cap variant needs a count other than 3
TRAVA_MARCAS = {'folga-005': 1}
