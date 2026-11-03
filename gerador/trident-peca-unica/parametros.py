"""Parameters of the one-piece Trident with the lock: the Trident with the lock's (gerador/trident-trava/parametros.py)."""
import herdar

herdar.copiar(herdar.de('trident-trava', 'parametros'), globals())

# 2026-11-02, the user: "tem que adicionar uma leve folga onde vai o acrilico... adiciona pelo menos mais 0.1mm de folga",
# and on the support: "tem que fazer essa bridge ter 2 camadas, porem 1 camada só onde encosta na nossa peça"
_VAO = ('projeto', 'peca_unica_vao', '3.0 mm', 'mm', 'Peça única: vão do acrílico, da face da tampa até a base embaixo dele: a chapa de 2,7 com 0,3 de folga (era 2,8; o usuário pediu pelo menos mais 0,1). Deitada, o vão sai em camadas de 0,2: com 2,9 o teto dele cairia no meio de uma; com 3,0 fica em 10,7 − 2,7 = 8,0 mm da mesa, numa troca de camada')
PARAMS = [_VAO if n == 'peca_unica_vao' else (g, n, e, u, c) for g, n, e, u, c in PARAMS] + [   # noqa: F821  (copied)
    ('ajuste', 'suporte_lamina_topo', '0.4 mm', 'mm', 'Peça única, suporte: a lâmina fica com isto (2 camadas), em cima da de uma camada, menos perto da peça'),
    ('ajuste', 'suporte_lamina_contato', '1 mm', 'mm', 'Peça única, suporte: até isto da peça a lâmina fica com uma camada só (suporte_lamina), para quebrar rente'),
]
