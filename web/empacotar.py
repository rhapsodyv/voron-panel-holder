"""Copy into web/ the generator files the configurator runs in the browser (gerador/, and in stl/ the printed lock kits'
files the one-piece generators read), and list them in web/gerador/arquivos.json (paths from web/), so web/ is the whole
static site (serve it, or publish it as it is). Run it again after changing the generator: python3 web/empacotar.py"""
import json
import os
import shutil
import sys

WEB = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(WEB)
sys.path.insert(0, os.path.join(REPO, 'gerador'))
import herdar  # noqa: E402

COMUNS = ['perfis.py', 'geometria_trava.py', 'herdar.py', 'bordas.py', 'travas.py', 'peca_unica_b3d.py',
          'peca_unica_v0_b3d.py', 'clips_b3d.py']
# the machines, each with the reference files it reads (a machine built on another keeps its own referencia/ copy)
V0 = ['v0_frame.json', 'misumi_1515.json', 'logo_voron.json']
TRIDENT = ['frame_350.json', 'perfil_2020_usuario.json', 'misumi_2020.json']
MAQUINAS = {'v0': V0, 'v0-trava': V0, 'v0-peca-unica': V0, 'trident': TRIDENT, 'trident-trava': TRIDENT,
            'trident-peca-unica': TRIDENT}


def kits():
    """The printed lock kits' files the one-piece generators read (peca_unica_b3d: V7, V8, DISCO; peca_unica_v0_b3d:
    KIT, DISCO), from the configs' choices."""
    cursor_tri = herdar.de('trident-peca-unica', 'config').CURSOR_V8
    cursor_v0 = herdar.de('v0-peca-unica', 'config').CURSOR_FACES
    return [f'stl/trident-provas-peca-unica-trava-v7/{a}' for a in ('trava-cursor-final.step', 'trava-capa-final.step', 'trava-capa-final-2x.stl')] + [
        f'stl/trident-provas-peca-unica-trava-v8/trava-cursor-{cursor_tri}.step',
        f'stl/trident-provas-peca-unica-trava-v8/trava-cursor-{cursor_tri}-1x.stl',
        'stl/trident-provas-peca-unica-trava-v5/trava-indicador-1x.stl',
        f'stl/provas-peca-unica-trava-v1/trava-cursor-{cursor_v0}-1x.stl', 'stl/provas-peca-unica-trava-v1/trava-capa-1x.stl',
        'stl/provas-trava-v3/trava-indicador-1x.stl']


def main():
    for d in ('gerador', 'stl'):
        if os.path.isdir(os.path.join(WEB, d)):
            shutil.rmtree(os.path.join(WEB, d))
    arquivos = []

    def copia(rel):
        os.makedirs(os.path.dirname(os.path.join(WEB, rel)), exist_ok=True)
        shutil.copyfile(os.path.join(REPO, rel), os.path.join(WEB, rel))
        arquivos.append(rel)
    for f in COMUNS:
        copia(f'gerador/{f}')
    for m, refs in MAQUINAS.items():
        for f in ('config.py', 'parametros.py', 'mapa.py'):
            copia(f'gerador/{m}/{f}')
        for f in refs:
            copia(f'gerador/{m}/referencia/{f}')
    for f in kits():
        copia(f)
    with open(os.path.join(WEB, 'gerador', 'arquivos.json'), 'w') as fh:
        json.dump(arquivos, fh, indent=1)
    print(f'{len(arquivos)} arquivos em {WEB} (gerador/, stl/)')


if __name__ == '__main__':
    main()
