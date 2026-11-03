"""The configurator's Python side: motor.js runs it inside Pyodide, in a Web Worker, over the generator files
empacotar.py copies into web/ (gerador/ and the lock's kit files in stl/). Two families of machines:
  - the clip projects (clips_b3d: v0, v0-trava, trident, trident-trava);
  - the one-piece projects, always with the lock (peca_unica_b3d: trident-peca-unica, its sides, rear and top, the
    doors kept with trident-trava's clips; peca_unica_v0_b3d: v0-peca-unica, the top hat's sides only).
It also runs natively, to test it or to build the site's ready-made faces (pre_gerar):
  .venv-b3d/bin/python web/motor.py trident-trava topo
  .venv-b3d/bin/python web/motor.py pre-gerar [machine ...]
  .venv-b3d/bin/python web/motor.py catalogo          (pre/catalogo.json alone)

Every call takes the machine, a face and the changed parameters (a JSON object {name: expression}, as clips_b3d's
--mudar) and returns plain data: JSON text, or bytes for the meshes and the ZIP."""
import io
import json
import os
import sys
import tempfile
import time
import zipfile

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, 'gerador'))
import build123d as bd  # noqa: E402
import clips_b3d as cb  # noqa: E402
import peca_unica_b3d as pu  # noqa: E402
import peca_unica_v0_b3d as pv  # noqa: E402

TITULOS = {'v0': 'Voron V0.2', 'v0-trava': 'Voron V0.2 with lock', 'trident': 'Voron Trident 350',
           'trident-trava': 'Voron Trident 350 with lock'}
# the one-piece machines: generator module, title, faces it builds, the clip machine for its doors and for its frame
PECA_UNICA = {
    'trident-peca-unica': dict(mod=pu, titulo='Voron Trident 350, one-piece', prefixo='trident-peca-unica-',
                               faces=('lateral-direita', 'lateral-esquerda', 'traseira', 'topo'),
                               portas=('trident-trava', ('porta-direita', 'porta-esquerda')), quadro='trident'),
    'v0-peca-unica': dict(mod=pv, titulo='Voron V0.2, one-piece (top hat sides)', prefixo='peca-unica-',
                          faces=('tophat-frente', 'tophat-tras', 'tophat-direita', 'tophat-esquerda'),
                          portas=None, quadro='v0'),
}
_maquinas = {}          # (machine, changes) -> clips_b3d.Maquina, its pieces cached in it; the latest few
_quadros = {}           # a clips_b3d key -> the frame's meshes
_malhas = {}            # (key, piece) -> its mesh
_feitas = {}            # (one-piece key, face) -> the generator's construir_face, its pieces


def _mud(mudancas):
    return json.loads(mudancas) if isinstance(mudancas, str) else dict(mudancas or {})


def _maquina(nome, mudancas):
    mud = _mud(mudancas)
    chave = (nome, json.dumps(mud, sort_keys=True))
    if chave not in _maquinas:
        m = cb.Maquina(nome, mud)                      # a bad expression fails here, before anything is built
        while len(_maquinas) >= 4:
            velha = next(iter(_maquinas))
            del _maquinas[velha]
            _quadros.pop(velha, None)
            for k in [k for k in _malhas if k[0] == velha]:
                del _malhas[k]
        _maquinas[chave] = m
    return _maquinas[chave], chave


def _modulo(nome, mudancas):
    """The one-piece generator with the changes set (its MUDANCAS, over every evaluation), and the cache key."""
    mud = _mud(mudancas)
    mod = PECA_UNICA[nome]['mod']
    mod.MUDANCAS = mud
    pu.MUDANCAS = mud if mod is pu else {}
    return mod, (nome, json.dumps(mud, sort_keys=True))


def _porta(nome, face):
    """A one-piece machine's face that is a clip machine's (the Trident's doors): that machine's name, else None."""
    p = PECA_UNICA.get(nome, {}).get('portas')
    return p[0] if p and face in p[1] else None


def catalogo():
    """The machines, their faces and parameter tables (group, name, expression, unit, comment, value), as JSON."""
    out = []
    for nome in cb.MAQUINAS:
        m, _ = _maquina(nome, {})
        out.append(dict(nome=nome, titulo=TITULOS[nome], familia='clips', prefixo=m.config.STL_PREFIX,
                        faces=[f['nome'] for f in cb.faces(m)],
                        parametros=[dict(grupo=g, nome=n, expr=e, unidade=u, comentario=c, valor=m.v.get(n))
                                    for g, n, e, u, c in m.parametros.PARAMS]))
    for nome, d in PECA_UNICA.items():
        mod, _ = _modulo(nome, {})
        v = mod.valores()
        out.append(dict(nome=nome, titulo=d['titulo'], familia='peca-unica', prefixo=d['prefixo'],
                        faces=list(d['faces']) + list(d['portas'][1] if d['portas'] else ()),
                        portas=list(d['portas'][1]) if d['portas'] else [],
                        parametros=[dict(grupo=g, nome=n, expr=e, unidade=u, comentario=c, valor=v.get(n))
                                    for g, n, e, u, c in mod.parametros.PARAMS]))
    return json.dumps(out, ensure_ascii=False)


def avaliar(nome, mudancas):
    """The values with the changes (JSON {name: value}), or the error of an expression that does not evaluate."""
    try:
        if nome in PECA_UNICA:
            mod, _ = _modulo(nome, mudancas)
            v = mod.valores()
        else:
            v = _maquina(nome, mudancas)[0].v
    except Exception as e:                           # noqa: BLE001  (shown to the user as it is)
        return json.dumps(dict(erro=f'{type(e).__name__}: {e}'), ensure_ascii=False)
    return json.dumps(dict(valores=v), ensure_ascii=False)


# ---------------------------------------------------------------- meshes and placements
def _malha(shape, tol=0.05):
    vs, ts = shape.tessellate(tol, 0.2)
    return (np.array([(p.X, p.Y, p.Z) for p in vs], dtype=np.float32).tobytes(),
            np.array(ts, dtype=np.uint32).tobytes())


def _tipo(nome):
    """construir.cores: covers, corners and the bowden plug outside; clips and the logo inside; the lock's parts."""
    if nome.startswith('trava-'):
        return 'trava'
    return 'interna' if nome.startswith(('clip-', 'logo')) else 'externa'


def _m4(o, x, z):
    """The placement (bordas.colocacoes: x, z, origin; y = z x x, as clips_b3d._local), a 4x4 numpy matrix."""
    x, z = np.array(x, float), np.array(z, float)
    out = np.eye(4)
    out[:3, 0], out[:3, 1], out[:3, 2], out[:3, 3] = x, np.cross(z, x), z, o
    return out


def _de_loc(loc):
    mt = loc.wrapped.Transformation()
    return np.array([[mt.Value(r, c) for c in (1, 2, 3, 4)] for r in (1, 2, 3)] + [[0.0, 0.0, 0.0, 1.0]])


def _lista(m4):
    return [float(x) for x in np.asarray(m4).reshape(16)]


def _matriz(o, x, z):
    return _lista(_m4(o, x, z))


def _frame(chave_frame):
    """The clip machine chave_frame's frame: each length's mesh once, each member as one of them and a matrix."""
    m, chave = _maquina(chave_frame, {})
    if chave not in _quadros:
        malhas, membros = {}, []
        for nm, perfil, loc in cb.membros_frame(m):
            if id(perfil) not in malhas:
                malhas[id(perfil)] = (len(malhas), *_malha(perfil, 0.05))
            membros.append(dict(nome=nm, perfil=malhas[id(perfil)][0], matriz=_lista(_de_loc(loc))))
        _quadros[chave] = dict(perfis=[dict(v=v, t=t) for _, v, t in sorted(malhas.values(), key=lambda x: x[0])], membros=membros)
    return _quadros[chave]


# ---------------------------------------------------------------- the clip projects
def _montar_clips(nome, face, mudancas):
    m, chave = _maquina(nome, mudancas)
    col = cb.colocacoes(m, face)
    qtd = {}
    for p in col:
        qtd[p[0]] = qtd.get(p[0], 0) + 1
    pecas = {}
    for n, k in qtd.items():
        s = cb.construir(m, n)
        if (chave, n) not in _malhas:
            _malhas[(chave, n)] = _malha(s)
        v, tri = _malhas[(chave, n)]
        pecas[n] = dict(tipo=_tipo(n), volume=round(s.volume, 2), quantidade=k, v=v, t=tri)
    normal = next(f['n'] for f in cb.faces(m) if f['nome'] == face)
    frame = 'trident' if nome.startswith('trident') else 'v0'
    return dict(pecas=pecas, colocacoes=[[p[0], _matriz(p[1], p[2], p[4])] for p in col], frame=_frame(frame),
                normal=list(normal))


def _conferir_clips(nome, face, mudancas):
    m, _ = _maquina(nome, mudancas)
    col, con, pre = cb._resumo(cb.interferencia(m, face))
    lista = lambda d: [dict(pecas=k, volume=r[0], profundidade=r[1], tipo=r[2] if len(r) > 2 else None) for k, r in d.items()]   # noqa: E731
    return dict(familia='clips', colisoes=lista(col), pre_cargas=lista(pre), contatos=lista(con))


def _zip_clips(nome, face, mudancas, z):
    m, _ = _maquina(nome, mudancas)
    qtd = {}
    for p in cb.colocacoes(m, face):
        qtd[p[0]] = qtd.get(p[0], 0) + 1
    with tempfile.TemporaryDirectory() as d:
        for n, k in qtd.items():
            bd.export_stl(cb.construir(m, n), os.path.join(d, 'x.stl'), tolerance=0.005, angular_tolerance=0.1)
            z.write(os.path.join(d, 'x.stl'), f'{n}-{k}x.stl')
    z.writestr('quantidades.json', json.dumps(dict(sorted(qtd.items())), indent=1, ensure_ascii=False))


# ---------------------------------------------------------------- the one-piece projects
def _feitas_pu(nome, face, mudancas):
    mod, chave = _modulo(nome, mudancas)
    if (chave, face) not in _feitas:
        while len(_feitas) >= 6:
            del _feitas[next(iter(_feitas))]
        _feitas[(chave, face)] = mod.construir_face(face)
    return mod, chave, _feitas[(chave, face)]


MZ = np.diag([1.0, 1.0, -1.0, 1.0])             # z -> -z: a mirrored part is this of the part, so its placement stays proper


def _travas_pu(nome, mod, lista, feitas):
    """The lock's parts of a one-piece face, locked: {part: (shape in the lock coupon's frame, kind)} and their
    placements [(part, 4x4)]. Mirrored locks take the parts' z-mirror ('-espelho') and a proper placement."""
    partes, col = {}, []
    if mod is pu:
        cursor, capa, queda = pu.trava_v8()
        v, g = pu.valores_trava(), None
    else:
        v = pv.valores()
        g = pv.geo(v)
        vk = dict(v, peca_unica_vao=pv.perfis.evaluate(pv.config.KIT_VAO, v))     # as kit v1 printed them
        a, mk = pv.config.GANCHO_CURSOR[pv.config.CURSOR_FACES]
        cursor, capa, queda = pv.cursor(vk, pv.geo(vk), a, mk, orelha=False)['cursor'], pv.capa(vk, pv.geo(vk))['capa'], g['queda']
    for p in lista:
        r = feitas[p['nome']]
        gg = r.get('g') or g
        if mod is pu:
            if p['tipo'] != 'meio':
                continue
            A = np.eye(4)
            A[2, 3] = r['desloc']                                            # the lock's frame along the middle
            S = None
            if p.get('espelho'):                                             # the middle mirrored across z = Lt / 2
                S = np.diag([1.0, 1.0, -1.0, 1.0])
                S[2, 3] = r['comprimento']
        else:
            if p['tipo'] == 'meio':
                A = _de_loc(r['loc'])
                S = None
            elif r.get('espelho'):
                A = _de_loc(feitas[next(k for k, x in pv.mapa.CANTOS_TRAVA.items() if x == p['nome'])]['loc'])
                S = np.array([[0.0, 1, 0, 0], [1, 0, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]])   # the -hv's mirror across x = y
            else:
                A = _de_loc(r['loc'])
                S = None
        c = gg['c']
        (si, zi), di, dp = gg['ind'], v['trava_indicador_diametro'], v['trava_indicador_profundidade']
        disco = pu._cilindro('y', (si, zi), di, gg['top'] - dp, gg['top'])
        for parte, forma, dy, dz in (('trava-cursor', cursor, -queda, c), ('trava-capa', capa, -v['trava_folga_capa'], c),
                                     ('trava-indicador', disco, 0.0, 0.0)):
            T = np.eye(4)
            T[1, 3], T[2, 3] = dy, dz
            Q = _m4(p['quadro'][0], p['quadro'][1], p['quadro'][3])
            if S is None:
                partes.setdefault(parte, forma)
                col.append((parte, Q @ A @ T))
            else:
                partes.setdefault(parte + '-espelho', bd.mirror(forma, bd.Plane.XY))
                col.append((parte + '-espelho', Q @ S @ A @ T @ MZ))
    return partes, col


def _montar_pu(nome, face, mudancas):
    mod, chave, feitas = _feitas_pu(nome, face, mudancas)
    lista = mod.pecas_da_face(face)
    if mod is pu:
        for p in lista:
            p.setdefault('espelho', p['nome'].endswith('-espelho'))
    pecas, col = {}, []
    for p in lista:
        n = p['nome']
        if n not in pecas:
            s = feitas[n]['peca']
            if (chave, face, n) not in _malhas:
                _malhas[(chave, face, n)] = _malha(s)
            v, tri = _malhas[(chave, face, n)]
            pecas[n] = dict(tipo='externa', volume=round(s.volume, 2), quantidade=0, v=v, t=tri)
        pecas[n]['quantidade'] += 1
        col.append([n, _matriz(p['quadro'][0], p['quadro'][1], p['quadro'][3])])
    partes, travas = _travas_pu(nome, mod, lista, feitas)
    for n, forma in partes.items():
        if (chave, face, n) not in _malhas:
            _malhas[(chave, face, n)] = _malha(forma, 0.02)
        v, tri = _malhas[(chave, face, n)]
        pecas[n] = dict(tipo='trava', volume=round(forma.volume, 2), quantidade=sum(1 for x, _ in travas if x == n), v=v, t=tri)
    col += [[n, _lista(m4)] for n, m4 in travas]
    f = next(x for x in mod.mapa.faces(mod.valores()) if x['nome'] == face)
    return dict(pecas=pecas, colocacoes=col, frame=_frame(PECA_UNICA[nome]['quadro']), normal=list(f['n']))


def _achatar(d, prefixo=''):
    """A check's nested results as (path, number) leaves."""
    for k, x in d.items():
        caminho = f'{prefixo} / {k}' if prefixo else str(k)
        if isinstance(x, dict):
            yield from _achatar(x, caminho)
        elif isinstance(x, (int, float)) and not isinstance(x, bool):
            yield caminho, x
        elif isinstance(x, (list, tuple)) and all(isinstance(y, (int, float)) for y in x):
            yield caminho, max(x, key=abs) if x else 0.0


INFORMATIVOS = ('queda', 'desloc', 'curso_meio', 'face', 'chanfro', 'gancho_topo', 'tempo', 'folga_encaixe_medida')   # measures, not checks


def _conferir_pu(nome, face, mudancas):
    """The generator's own face check (peca_unica_b3d.conferir, peca_unica_v0_b3d.conferir_face; mm³): per group, the
    cases and those not zero (the hook's squeeze is meant)."""
    mod, _, feitas = _feitas_pu(nome, face, mudancas)
    if mod is pu:
        res = pu.conferir(face, feitas)
    else:
        v = pv.valores()
        res = pv.conferir_face(face, feitas, v, pv.geo(v))
    grupos = []
    for k, x in res.items():
        if k in INFORMATIVOS:
            continue
        itens = [(c, y) for c, y in _achatar({k: x}) if not any(f'/ {i}' in c for i in INFORMATIVOS)]
        grupos.append(dict(nome=k, casos=len(itens), nao_zerados=[[c, round(y, 4)] for c, y in itens if abs(y) > 1e-9]))
    return dict(familia='peca-unica', grupos=grupos)


def _zip_pu(nome, face, mudancas, z):
    mod, _, feitas = _feitas_pu(nome, face, mudancas)
    with tempfile.TemporaryDirectory() as d:
        if mod is pu:
            pu.exportar(face, feitas, d)
        else:
            pv.exportar_face(face, feitas, d, pv.geo(pv.valores())['top'])
        for arq in sorted(os.listdir(d)):
            z.write(os.path.join(d, arq), arq)


# ---------------------------------------------------------------- the calls
def montar_face(nome, face, mudancas):
    """The face built: each distinct piece once (its mesh, kind, volume, count), each placement (piece and matrix), the
    frame (each length's mesh once, each member as one of them and a matrix) and the face's outward normal."""
    t = time.time()
    porta = _porta(nome, face)
    if nome in PECA_UNICA and not porta:
        r = _montar_pu(nome, face, mudancas)
    else:
        r = _montar_clips(porta or nome, face, mudancas)
    r['tempo'] = round(time.time() - t, 1)
    return r


def conferir_face(nome, face, mudancas):
    """The face's check, as JSON: the clip projects' construir.interferencia (collisions, meant preloads, contacts),
    the one-piece projects' own check (groups of cases, those not zero)."""
    t = time.time()
    porta = _porta(nome, face)
    r = _conferir_pu(nome, face, mudancas) if nome in PECA_UNICA and not porta else _conferir_clips(porta or nome, face, mudancas)
    r['tempo'] = round(time.time() - t, 1)
    return json.dumps(r, ensure_ascii=False)


def zip_face(nome, face, mudancas):
    """The face's files as their generator exports them, in a ZIP: the clip projects' STLs in their own frames, named
    with their counts; the one-piece projects' lying with their support, the STEPs and the lock's parts; and
    quantidades.json; the changed parameters in parametros.json."""
    buf = io.BytesIO()
    porta = _porta(nome, face)
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as z:
        if nome in PECA_UNICA and not porta:
            _zip_pu(nome, face, mudancas, z)
        else:
            _zip_clips(porta or nome, face, mudancas, z)
        z.writestr('parametros.json', json.dumps(dict(maquina=porta or nome, face=face, mudancas=_mud(mudancas)), indent=1, ensure_ascii=False))
    return buf.getvalue()


def pre_gerar(pasta, nomes=None):
    """Every face of every machine with the default values, built here (natively) for the site to show, check and
    download before its engine has loaded (the engine is only needed once a parameter changes): pre/catalogo.json,
    pre/<machine>.json (each distinct piece's mesh once, base64, the frame, each face's placements, counts and
    check) and pre/<machine>/<face>.zip. nomes: only those machines (the catalogue is always rewritten)."""
    import base64
    b64 = lambda b: base64.b64encode(b).decode()                       # noqa: E731
    os.makedirs(pasta, exist_ok=True)
    cat = json.loads(catalogo())
    with open(os.path.join(pasta, 'catalogo.json'), 'w') as fh:
        json.dump(cat, fh, ensure_ascii=False)
    for c in cat:
        nome = c['nome']
        if nomes and nome not in nomes:
            continue
        t = time.time()
        out = dict(maquina=nome, pecas={}, faces={})
        os.makedirs(os.path.join(pasta, nome), exist_ok=True)
        for face in c['faces']:
            r = montar_face(nome, face, {})
            nomes_face = {}
            for n, p in r['pecas'].items():
                # a one-piece face's pieces are built per face: the same name may differ between faces (lengths)
                chave = n if n not in out['pecas'] or out['pecas'][n]['v'] == b64(p['v']) else f'{n}@{face}'
                out['pecas'].setdefault(chave, dict(tipo=p['tipo'], volume=p['volume'], v=b64(p['v']), t=b64(p['t'])))
                nomes_face[n] = chave
            out['faces'][face] = dict(colocacoes=[[nomes_face[n], [round(x, 6) for x in a]] for n, a in r['colocacoes']],
                                      normal=r['normal'], quantidades={nomes_face[n]: p['quantidade'] for n, p in r['pecas'].items()},
                                      conferencia=json.loads(conferir_face(nome, face, {})))
            with open(os.path.join(pasta, nome, f'{face}.zip'), 'wb') as fh:
                fh.write(zip_face(nome, face, {}))
            print(f'  {nome} {face}: {time.time() - t:.0f} s', flush=True)
        fr = r['frame']
        out['frame'] = dict(perfis=[dict(v=b64(p['v']), t=b64(p['t'])) for p in fr['perfis']],
                            membros=[dict(mb, matriz=[round(x, 6) for x in mb['matriz']]) for mb in fr['membros']])
        with open(os.path.join(pasta, f'{nome}.json'), 'w') as fh:
            json.dump(out, fh, ensure_ascii=False, separators=(',', ':'))
        print(f'{nome}: {len(out["faces"])} faces, {len(out["pecas"])} peças, {time.time() - t:.0f} s', flush=True)


if __name__ == '__main__' and sys.argv[1:2] == ['pre-gerar']:
    pre_gerar(os.path.join(AQUI, 'pre'), sys.argv[2:] or None)
elif __name__ == '__main__' and sys.argv[1:2] == ['catalogo']:
    with open(os.path.join(AQUI, 'pre', 'catalogo.json'), 'w') as fh:       # the catalogue alone (titles, parameters)
        fh.write(catalogo())
elif __name__ == '__main__':
    maq, face = sys.argv[1], sys.argv[2]
    t0 = time.time()
    cat = json.loads(catalogo())
    print('catálogo:', [(c['nome'], len(c['faces']), len(c['parametros'])) for c in cat], f'{time.time() - t0:.1f} s')
    r = montar_face(maq, face, '{}')
    print('face:', {n: (p['quantidade'], p['volume']) for n, p in r['pecas'].items()}, len(r['colocacoes']), 'colocações,',
          len(r['frame']['membros']), 'membros do frame;', r['tempo'], 's')
    print('conferir:', conferir_face(maq, face, '{}')[:600])
    z = zip_face(maq, face, '{}')
    print('zip:', len(z), 'bytes;', zipfile.ZipFile(io.BytesIO(z)).namelist())
    print('erro de expressão:', avaliar(maq, '{"fin_inset": "0.05 mm +"}'))
