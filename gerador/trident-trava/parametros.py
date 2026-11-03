"""Parameters of the Trident with the lock: the Trident's (gerador/trident/parametros.py) plus the ones the
panel locks add."""
import herdar

herdar.copiar(herdar.de('trident', 'parametros'), globals())

PARAMS = PARAMS + [   # noqa: F821  (copied from the Trident's)
    ('projeto', 'trava_margem_emenda', '3 mm', 'mm', 'Trava nas peças: o trecho do clip que a trava muda (do retorno das pernas a 45° ao fim da farpa) fica isto longe de uma emenda entre clips'),
    ('projeto', 'canto_miolo', '1', '', 'Cantos: em cima do montante, onde os clips não chegam, o oco entre a tampa e o frame vira sólido, do batente do acrílico até a parede de fora e do frame até dentro da tampa (v2, 2026-10-31: o oco ligava a câmara à tampa pelos canais do montante e por baixo do acrílico). 0 = oco, como na Trident'),
    ('ajuste', 'canto_miolo_folga', '0.2 mm', 'mm', 'Cantos: folga entre o miolo e a ponta dos clips'),
    # peça única (clip e tampa numa peça, deitada com a face de fora na mesa; ideia do usuário, 2026-10-31):
    # corpo de prova com a trava, construir.peca_unica_trava()
    ('projeto', 'peca_unica_vao', '2.8 mm', 'mm', 'Peça única: vão do acrílico, da face da tampa até a base embaixo dele. Deitada, o teto do vão fica em 10,7 − 2,9 = 7,8 mm da mesa, numa troca de camada de 0,2 (com 2,7 cairia no meio de uma camada). A prova v1 imprimiu bem'),
    ('projeto', 'peca_unica_pilar', '1 mm', 'mm', 'Peça única com trava: as pernas da trava ficam presas na peça só nas pontas; do lado da janela por um pilar deste comprimento, do outro na aleta maciça'),
    ('projeto', 'peca_unica_dobra', '3 mm', 'mm', 'Peça única com trava: trecho liso da perna entre o pilar e a farpa e entre a farpa e a aleta maciça, onde ela dobra ao entrar (viga presa nas duas pontas, a dobra dentro da camada: ~1,8% com a farpa da v2)'),
    ('projeto', 'peca_unica_fenda', '1 mm', 'mm', 'Peça única com trava: fenda entre as pernas da trava e a peça (5 camadas). A face de baixo da perna imprime como ponte sobre ela, de pilar a aleta, e pode ceder um pouco'),
    ('ajuste', 'peca_unica_fenda_topo', '0.1 mm', 'mm', 'Peça única com trava: a fenda entra isto na peça, acima da face do frame, para começar numa troca de camada (a face do frame fica a 10,7 da mesa, no meio de uma camada)'),
    # these default to the v1 coupon; config.PECA_UNICA_VARIANTES has the v2 ones
    ('projeto', 'peca_unica_farpa', '( fin_barb - fin_inset )', 'mm', 'Peça única com trava: quanto a farpa das pernas da trava passa da abertura do rasgo, por lado (v1: a do clip, 0,09; saía mesmo travada). A face de cima continua a 23° do mesmo ponto: o aperto encaixado não muda, a farpa só fica mais funda'),
    ('projeto', 'peca_unica_perna', 'fin_leg', 'mm', 'Peça única com trava: espessura das pernas da trava onde elas dobram (fora da farpa), da face de dentro (a da lingueta) para fora'),
    ('projeto', 'peca_unica_farpa_comprimento', '0 mm', 'mm', 'Peça única com trava: comprimento da farpa, terminando onde termina a parte larga da lingueta travada; quanto mais curta, mais longo o trecho que dobra do lado do pilar. 0 = de peca_unica_dobra depois do pilar até lá (v1)'),
    ('projeto', 'peca_unica_dobra_fim', 'peca_unica_dobra', 'mm', 'Peça única com trava: trecho liso da perna entre a farpa e a aleta maciça'),
    ('projeto', 'peca_unica_comprimento', 'trava_comprimento', 'mm', 'Peça única com trava: comprimento do corpo de prova'),
    # lingueta com dentes (peça única v4, ideia do usuário): config.PECA_UNICA_VARIANTES['dentes']
    ('projeto', 'trava_dentes', '0', '', 'Trava com dentes (peça única v4, ideia do usuário): a lingueta vira tantos dentes, com partes estreitas entre eles. Aberta, cada dente fica num rebaixo das pernas; travada, anda meio passo e fica atrás de um trecho de farpa. O curso e a lingueta saem do dente (geometria_trava). 0 = uma lingueta só'),
    ('projeto', 'trava_dente', '4 mm', 'mm', 'Trava com dentes: comprimento de cada dente na largura cheia (a farpa que ele segura)'),
    ('projeto', 'trava_dente_degrau', '0.55 mm', 'mm', 'Trava com dentes: entre os dentes a lingueta é isto mais estreita por lado (rampas a 45°), e os rebaixos das pernas são isto fundos. Mais que a farpa: aberta, a perna dobra para entrar sem bater nos dentes nem na parte estreita'),
    ('projeto', 'peca_unica_gancho', '0 mm', 'mm', 'Peça única v5 (ideia do usuário): uma perna só, grossa, do lado do acrílico, presa na base pelo comprimento todo, com um gancho que passa isto da abertura do rasgo, na peça inteira (faces a 45°). Ela não dobra: aberta, o cursor fica solto de lado e a peça entra deslocada para fora e volta para enganchar; travada, a lingueta (trava_lingueta_desloc) enche o vão entre a perna e a aba de fora. 0 = pernas que dobram'),
    ('ajuste', 'peca_unica_gancho_folga', '0.1 mm', 'mm', 'Peça única v5: folga da perna na abertura, da lingueta na aba de fora e do gancho embaixo da aba; ao entrar a peça anda o gancho mais isto'),
    ('projeto', 'peca_unica_rasgo_folga', '1', '', 'Peça única v5: folga do rasgo do pescoço (gancho + 2 folgas, para o lado do acrílico), para o cursor ficar solto de lado enquanto a peça entra deslocada: 1 = no rasgo todo (v5); 2 = só onde o pescoço fica com a trava aberta, até o bico da lingueta centrar o cursor na perna, e depois uma rampa de 45° até a largura do pescoço; 0 = nenhuma (o rasgo só do pescoço)'),
    ('projeto', 'peca_unica_gancho_aperto', '-peca_unica_gancho_folga', 'mm', 'Peça única v6 (cunha, contra o balanço da v5): a rampa a 45° de cima do gancho sobe até passar isto acima da quina da aba, com a peça assentada e a perna rente à lingueta. Ao travar, a lingueta (justa até a aba de fora) empurra a peça para o lado do acrílico e a rampa aperta a peça contra o frame, como a cunha dos clips da Trident. Negativo = folga embaixo da aba (v5: −0,1)'),
    ('projeto', 'trava_lingueta_alarga', '0 mm', 'mm', 'Trava: a lingueta fica isto mais larga só do lado de fora (+s). Peça única v6: até encostar na aba de fora (peca_unica_gancho_folga); mais não entra, porque ao pôr a peça o cursor solto fica só 0,1 para dentro do lugar'),
    ('projeto', 'trava_toco_frente_reta', '0', '', 'Trava: 1 = o flanco da frente do rabo-de-andorinha como o de trás: a 45° do pé do toco até alargar trava_toco_aba, e depois reto até o topo; a capa leva na frente o mesmo lábio reto de trava_capa_labio (2026-11-01, usuário: o lado de trás, reto + inclinado, segurou mais firme que o da frente, só inclinado). 0 = um flanco só, da base ao topo'),
    ('projeto', 'trava_lingueta_desloc', '0 mm', 'mm', 'Trava: a lingueta (e a quilha) fica isto para fora (+s) do pescoço (peça única v5: até peca_unica_gancho_folga da aba de fora). 0 = centrada'),
    ('projeto', 'trava_pescoco_desloc', '0 mm', 'mm', 'Trava: o pescoço, o toco e os rasgos ficam isto para fora (+s) da lingueta. 0 = rente à lingueta do lado de fora'),
    ('projeto', 'peca_unica_um_lado', '0', '', 'Peça única com trava: 1 = perna só do lado de fora (+s), com farpa e solta pela fenda; a do lado do acrílico vira parede presa na peça, sem farpa (com os mesmos rebaixos dos dentes). Travada, a farpa de fora fica presa pelos dentes, e eles se apoiam na parede (ideia do usuário). 0 = pernas dos dois lados'),
    ('ajuste', 'trava_dente_folga', '0.4 mm', 'mm', 'Trava com dentes: o rebaixo passa isto do dente (com as rampas) em cada ponta, e a farpa passa isto do dente travado'),
    ('projeto', 'suporte_parede', '1.6 mm', 'mm', 'Peça única, suporte de imprimir (ideia do usuário): espessura da parede de pé na mesa, na frente do vão do acrílico e depois das duas pontas'),
    ('ajuste', 'suporte_folga', '0.6 mm', 'mm', 'Peça única, suporte: distância da parede até a borda da tampa e até as pontas da peça'),
    ('ajuste', 'suporte_lamina', '0.2 mm', 'mm', 'Peça única, suporte: lâmina de uma camada do topo da parede até a borda e as pontas da base embaixo do acrílico; quebra rente depois de imprimir'),
]

# v2 (2026-10-31): o topo impresso entrava firme demais; as pernas recolhem 0,03 por lado (dobra para entrar
# 0,12 -> 0,09, aperto encaixado 0,06 -> 0,03). A lingueta da trava acompanha (geometria_trava: vão das pernas).
# v3 (2026-10-31, pedido do usuário): 0,05 (dobra 0,07, aperto 0,01).
# v4 (2026-11-01, pedido do usuário, para a lateral esquerda): 0,07 (dobra 0,05, encaixada 0,01 de folga, sem aperto).
PARAMS = [(g, n, '0.07 mm', u, c + '. Trident com trava: v2 0,03 (o topo entrava firme demais), v3 0,05, v4 0,07 (pedidos do usuário)') if n == 'fin_inset'
          else (g, n, e, u, c) for g, n, e, u, c in PARAMS]
