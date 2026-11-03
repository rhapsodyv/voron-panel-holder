"""Parameters of the V0 in one piece with the lock: the V0 with the lock's (gerador/v0-trava/parametros.py), the
one-piece Trident's that it needs, and lock v8's in the 1515 slot."""
import herdar

herdar.copiar(herdar.de('v0-trava', 'parametros'), globals())

# the Trident's final stub and cap (gerador/trident-trava/config.py, TRAVA_VARIANTES['final']), on the V0's
_FINAL = {'trava_toco_aba': 'trava_toco_aba_tras', 'trava_toco_altura': '3.7 mm', 'trava_capa_crista': '5.6 mm',
          'trava_capa_crista_largura': '12 mm', 'trava_capa_concavo': '6.6 mm'}
PARAMS = [(g, n, _FINAL.get(n, e), u, c) for g, n, e, u, c in PARAMS] + [   # noqa: F821  (copied from the V0's)
    ('projeto', 'trava_toco_frente_reta', '1', '', 'Trava: o flanco da frente do rabo-de-andorinha como o de trás, a 45° do pé do toco até alargar trava_toco_aba e depois reto até o topo; a capa leva na frente o mesmo lábio reto (a trava final da Trident)'),
    # the one-piece Trident's
    ('projeto', 'peca_unica_vao', '3.0 mm', 'mm', 'Peça única: vão do acrílico, da face da tampa até a base embaixo dele: a chapa de 2,7 com 0,3 de folga (era 2,8; o usuário, 2026-11-02: "adiciona pelo menos mais 0.1mm de folga"). Deitada, o vão sai em camadas de 0,2: com 3,0 o teto dele fica em 8,3 − 1,3 = 7,0 mm da mesa, numa troca de camada (com 2,9 cairia no meio de uma). Embaixo dele a base fica com 1,3'),
    ('projeto', 'peca_unica_comprimento', 'trava_comprimento', 'mm', 'Peça única com trava: comprimento do corpo de prova'),
    ('projeto', 'suporte_parede', '1.6 mm', 'mm', 'Peça única, suporte de imprimir: espessura da parede de pé na mesa, na frente do vão do acrílico e depois das duas pontas'),
    ('ajuste', 'suporte_folga', '0.6 mm', 'mm', 'Peça única, suporte: distância da parede até a borda da tampa e até as pontas da peça'),
    ('ajuste', 'suporte_lamina_topo', '0.4 mm', 'mm', 'Peça única, suporte: a lâmina fica com isto (2 camadas), em cima da de uma camada, menos perto da peça (o usuário, 2026-11-02: "tem que fazer essa bridge ter 2 camadas, porem 1 camada só onde encosta na nossa peça")'),
    ('ajuste', 'suporte_lamina_contato', '1 mm', 'mm', 'Peça única, suporte: até isto da peça a lâmina fica com uma camada só (suporte_lamina), para quebrar rente'),
    ('ajuste', 'suporte_lamina', '0.2 mm', 'mm', 'Peça única, suporte: lâmina de uma camada do topo da parede até a borda e as pontas da base embaixo do acrílico'),
    # lock v8 in the 1515 slot (ideias-trava/v0-peca-unica-trava-v8.png)
    ('projeto', 'peca_unica_gancho', '1 mm', 'mm', 'Trava v8: o gancho na face de fora da lingueta passa isto da abertura, embaixo da aba de fora (a cavidade do 1515 vai até 2,85 do centro: sobram 0,35)'),
    ('ajuste', 'peca_unica_gancho_folga', '0.1 mm', 'mm', 'Trava v8: folga da perna na abertura e do gancho na aba de fora com o cursor aberto; aberto, o cursor fica solto gancho + 2 folgas (1,2) para dentro'),
    ('projeto', 'peca_unica_perna', '1.2 mm', 'mm', 'Trava v8: a perna lisa do lado do acrílico, da folga na abertura até a lingueta; pelo menos o cursor solto (1,2), que na janela vai para o lugar dela. O resto da abertura é a lingueta (1,7)'),
    ('ajuste', 'trava_ombro_folga', '0.3 mm', 'mm', 'Trava v8: o ombro do cursor por cima da aba de fora fica isto acima da face do frame depois de o cursor descer ao travar (a capa assenta na tampa, e não o ombro no frame)'),
    ('ajuste', 'trava_degrau_folga', '0.3 mm', 'mm', 'Trava v8: o cursor alarga embaixo do acrílico (une a lingueta ao pescoço, que fica fora do acrílico) até isto abaixo da base, onde o acrílico assenta'),
    ('ajuste', 'trava_fundo_folga', '0.3 mm', 'mm', 'Trava v8: a quilha fica isto acima do fundo do rasgo depois de o cursor descer ao travar (o fundo só empurraria para cima; a peça deitada imprime até 0,15 mais fina)'),
    # the faces (gerador/v0-peca-unica/mapa.py)
    ('ajuste', 'peca_unica_aleta_poste', '0.5 mm', 'mm', 'Peça única, cantos: a aleta da perna horizontal começa isto depois da face do poste (os clips das horizontais iam até ele; no canto ela é da peça, e encostada uma ponta impressa mais comprida empurraria o canto contra a perna da trava na vertical)'),
]
