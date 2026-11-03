"""Parameters of the V0 with the lock: the V0's (gerador/v0/parametros.py) plus the ones the panel locks add."""
import herdar

herdar.copiar(herdar.de('v0', 'parametros'), globals())

PARAMS = PARAMS + [   # noqa: F821  (copied from the V0's)
    ('projeto', 'trava_margem_emenda', '3 mm', 'mm', 'Trava nas peças: o trecho do clip que a trava muda (do retorno das pernas a 45° ao fim da farpa) fica isto longe de uma emenda entre clips'),
    ('projeto', 'trava_capa_desloc', '0 mm', 'mm', 'Trava: a capa e o círculo ficam isto mais para fora (s) que na tampa de parede; a variante topo usa top_overhang, a da tampa-simples da borda de cima das laterais, que fica 3 mm para fora'),
]
