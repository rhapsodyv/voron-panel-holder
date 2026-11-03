"""A machine folder built on another one (gerador/v0-trava on gerador/v0): load the other folder's
config, parametros or mapa module, so the new folder only states what it changes."""
import importlib.util
import os

HERE = os.path.dirname(os.path.abspath(__file__))


def de(maquina, arquivo):
    """The module gerador/<maquina>/<arquivo>.py, loaded fresh (its own copy, never shared)."""
    path = os.path.join(HERE, maquina, f'{arquivo}.py')
    spec = importlib.util.spec_from_file_location(f'{maquina}_{arquivo}_base', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def copiar(mod, destino):
    """Every public name of mod into the namespace destino (a module's globals())."""
    destino.update({k: v for k, v in vars(mod).items() if not k.startswith('__')})
