"""Fusion script: builds the whole panel holder of one machine from the generator (gerador/construir.py).

Add this folder in Utilities > Scripts and Add-Ins (the + next to My Scripts) and run it.
The output goes to Text Commands (File > View > Show Text Commands).
"""
import importlib
import os
import sys
import traceback

import adsk.core

GEN = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MAQUINA = 'trident'


def run(_context):
    ui = adsk.core.Application.get().userInterface
    try:
        if GEN not in sys.path:
            sys.path.insert(0, GEN)
        for mod in ('perfis', 'construir'):
            if mod in sys.modules:
                importlib.reload(sys.modules[mod])
        import construir
        construir.usar(MAQUINA)
        construir.construir_tudo()
        ui.messageBox(f'{construir.DOC_NAME} gerado. O resumo das verificações está em Text Commands.')
    except Exception:
        ui.messageBox('Falhou:\n' + traceback.format_exc())
