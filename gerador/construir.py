"""Build (or rebuild) panel-holder in Fusion from parametros.py, perfis.py and mapa.py.

Two modes, chosen by the document: in a direct-modeling design (no timeline, the default for a new
document) every expression is evaluated here from parametros.py and the geometry is plain; in a
parametric design the expressions go to Fusion as user parameters and every sketch is dimensioned.

Runs inside Fusion; each step is a separate call so no single call runs long:

    construir.estado()             what exists (document, parameters, generated components)
    construir.preparar()           open or create the document, add missing user parameters
    construir.referencia()         Misumi 1515 piece for the test coupons
    construir.perfil('nome')       one test coupon (perfis.PROFILES, length test_length)
    construir.arranjar()           lay the coupons out side by side
    construir.exportar_stl()       export the coupons (or given components) as STL, the quantity in each file name
    construir.exportar_faces([...], pasta) export the pieces of assembled faces, named with their counts
    construir.frame_ref()          the V0.2 frame (1515 members) as reference, component frame-v0
    construir.pecas(['nome', ...]) straight pieces from mapa.PECAS, inside component pecas
    construir.cantos(['nome', ...]) L corners from mapa.CANTOS, inside component pecas
    construir.puxador()            the door handle (config.PUXADOR: V0 latch side outward, Trident door centre inward)
    construir.logo()               the Voron logo and its pocket in tampa-parede-h-logo
    construir.passa_bowden()       Trident: plug for the rear sheet's exhaust notch, with the bowden fitting hole
    construir.montar(['face', ...]) one component per face with the pieces in place (mapa.faces)
    construir.lista()              parts list counted from the assembled faces
    construir.interferencia('face') interference of one face with the frame
    construir.entre_faces([...])   interference between pieces of different faces (frame corners)
    construir.giro_porta(graus)    door opened about the hinge pin, checked against the side and the frame
    construir.cores()              colours: covers and corners (outside) one, clips (inside) another
    construir.salvar()             save (first save goes to project Voron / folder Panel-Holder)
    construir.construir_tudo()     everything above in order, with the checks (run it from Fusion's Scripts and Add-Ins)

Direct mode: the values live in parametros.py; change them there and run the steps again.
Parametric mode: user parameters already in the document are never overwritten (Fusion owns them).
Generated components are deleted and rebuilt by their step; do not edit them by hand.
"""
import importlib
import json
import math
import os
import sys
import time

import adsk.core
import adsk.fusion

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import perfis  # noqa: E402
import geometria_trava  # noqa: E402

# the machine: its folder (gerador/<name>) holds config.py, parametros.py, mapa.py and referencia/
MAQUINAS = ('v0', 'trident', 'v0-trava', 'trident-trava', 'trident-peca-unica')
MAQ = {'nome': None, 'dir': None}
config = parametros = mapa = None


def _load(name, path):
    import importlib.util
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def usar(maquina='v0'):
    """Pick the machine every step works on (reloads its config, parameters and map)."""
    global config, parametros, mapa, DOC_NAME, FRAME_COMPONENT, REF_COMPONENT, PROVAS, CONJUNTOS
    if maquina not in MAQUINAS:
        raise ValueError(f'máquina {maquina!r}: use uma de {MAQUINAS}')
    d = os.path.join(HERE, maquina)
    for shared in ('bordas', 'geometria_trava'):     # shared code used by the maps: pick up its edits too
        if shared in sys.modules:
            importlib.reload(sys.modules[shared])
    config = _load(f'{maquina}_config', os.path.join(d, 'config.py'))
    parametros = _load(f'{maquina}_parametros', os.path.join(d, 'parametros.py'))
    mapa = _load(f'{maquina}_mapa', os.path.join(d, 'mapa.py'))
    MAQ.update(nome=maquina, dir=d)
    DOC_NAME, FRAME_COMPONENT, REF_COMPONENT = config.DOC_NAME, config.FRAME_COMPONENT, config.REF_COMPONENT
    PROVAS, CONJUNTOS = config.PROVAS, config.CONJUNTOS
    return config.NOME


def _ref(name):
    """A file of the machine's referencia/ folder."""
    return os.path.join(MAQ['dir'], 'referencia', name)

NEW_DOC_DIRECT = True      # a document created by preparar() is direct modeling (no timeline)
PROJECT = 'Voron'
FOLDER = 'Panel-Holder'
REF_OFFSET = '50 mm'   # vertices are dimensioned from a point at (-50, -50) so every distance stays positive
P3 = adsk.core.Point3D.create
V3 = adsk.core.Vector3D.create
_CTX = {'direto': False, 'vals': {}, 'um': None}   # set by _contexto() for the document in use


# ---------------------------------------------------------------- document and parameters
def estado():
    app = adsk.core.Application.get()
    print('documentos abertos:', [d.name for d in app.documents])
    doc = _find_open(app)
    if doc is None:
        print(f'{DOC_NAME} não está aberto; na pasta {PROJECT}/{FOLDER}:', _find_saved(app) is not None)
        return
    design = _design(doc)
    names = [o.component.name for o in design.rootComponent.occurrences]
    direct = design.designType == adsk.fusion.DesignTypes.DirectDesignType
    print(f'{doc.name}: salvo={doc.isSaved} modificado={doc.isModified} '
          f'modo={"direto" if direct else "paramétrico"} componentes na raiz={names}')


def preparar():
    t = time.time()
    usar(MAQ['nome'] or 'v0')
    app = adsk.core.Application.get()
    doc = _find_open(app)
    new = False
    if doc is None:
        saved = _find_saved(app)
        new = saved is None
        doc = app.documents.open(saved, True) if saved else app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    doc.activate()
    design = _design(doc)
    if new:
        design.designType = (adsk.fusion.DesignTypes.DirectDesignType if NEW_DOC_DIRECT
                             else adsk.fusion.DesignTypes.ParametricDesignType)
        design.attributes.add('gerador', 'documento', DOC_NAME)
    design.fusionUnitsManager.distanceDisplayUnits = adsk.fusion.DistanceUnits.MillimeterDistanceUnits
    _contexto(design)
    added = []
    if not _CTX['direto']:
        ups = design.userParameters
        for group, name, expr, unit, comment in parametros.PARAMS:
            if ups.itemByName(name) is None:
                ups.add(name, adsk.core.ValueInput.createByString(expr), unit, f'[{group}] {comment}')
                added.append(name)
    modo = 'direto (valores do parametros.py)' if _CTX['direto'] else f'paramétrico, {len(added)} parâmetros novos {added}'
    print(f'preparar: {doc.name}, {"novo, " if new else ""}{modo}, {time.time() - t:.1f} s')


def salvar():
    t = time.time()
    app = adsk.core.Application.get()
    doc = _require_open()
    if doc.isSaved:
        ok = doc.save('Gerado por gerador/construir.py')
    else:
        proj = next(p for p in app.data.dataProjects if p.name == PROJECT)
        folder = proj.rootFolder.dataFolders.itemByName(FOLDER)
        ok = doc.saveAs(DOC_NAME, folder, 'Gerado por gerador/construir.py', '')
    print(f'salvar: {ok}, {time.time() - t:.1f} s')


def construir_tudo(salvar_no_fim=True):
    """The whole design in one run: coupons, frame, pieces, corners, faces, checks, save.

    Meant for a direct-modeling document run from Fusion's Scripts and Add-Ins (no time limit
    there); over the MCP, keep to one step per call. Prints a summary of the checks.
    """
    t = time.time()
    preparar()
    referencia()
    for name in PROVAS + ['acrilico-ref']:
        perfil(name)
    arranjar()
    frame_ref()
    pecas()
    if getattr(config, 'PUXADOR', ('tampa-parede-v-puxador',))[0] in mapa.PECAS:
        puxador()
    if getattr(config, 'LOGO_JSON', None):
        logo()
    if 'passa-bowden' in getattr(mapa, 'EXTRAS', ()):
        passa_bowden()
    cantos()
    chanfro_mesa()
    montar()
    faces = [f['nome'] for f in mapa.faces(_param_values(_design(_require_open())))]
    worst = {f: max(interferencia(f).values() or [0.0]) for f in faces}
    cross = entre_faces(faces)
    for face in [f for f in faces if f.startswith('porta')]:
        for a in (15, 45, 90, 110):
            giro_porta(a, com_frame=False, face=face)
    cores()
    bad = {f: round(w, 3) for f, w in worst.items() if w >= 0.05}
    print(f'construir_tudo: {time.time() - t:.0f} s; interferência por face acima de 0,05 mm: {bad or "nenhuma"}; '
          f'entre faces: {len(cross) or "nenhuma"}')
    if salvar_no_fim:
        salvar()


# outside pieces (covers, corners) and inside pieces (clips), to tell them apart in the model
CORES = {
    'externa': ('panel-holder externa', (150, 110, 205)),     # lilac
    'interna': ('panel-holder interna', (125, 195, 235)),     # light blue
    'acrilico': ('panel-holder acrilico', (225, 232, 240)),
    'frame': ('panel-holder frame', (140, 142, 148)),          # grey
}


def cores():
    """Colour every generated piece: covers and corners lilac, clips light blue, frame grey."""
    t = time.time()
    design = _design(_require_open())
    aps = {k: _appearance(design, name, rgb) for k, (name, rgb) in CORES.items()}
    count = 0
    for comp in design.allComponents:
        n = comp.name
        kind = ('interna' if n.startswith(('clip-', 'logo')) else 'externa' if n.startswith(('tampa-', 'canto-', 'passa-'))
                else 'acrilico' if n == 'acrilico-ref'
                else 'frame' if n in (FRAME_COMPONENT, REF_COMPONENT) or n.startswith('ref-') else None)
        if kind is None:
            continue
        for b in comp.bRepBodies:
            b.appearance = aps[kind]
            count += 1
    print(f'cores: {count} corpos, {time.time() - t:.1f} s')


def _appearance(design, name, rgb):
    """A plain plastic appearance of the given colour, copied once into the design."""
    ap = design.appearances.itemByName(name)
    if ap is None:
        app = adsk.core.Application.get()
        lib = next(lb for lb in app.materialLibraries if 'Appearance' in lb.name)
        base = next(a for a in lib.appearances if a.name.startswith('Plastic - Matte'))
        ap = design.appearances.addByCopy(base, name)
    for prop in ap.appearanceProperties:
        if prop.objectType == adsk.core.ColorProperty.classType():
            adsk.core.ColorProperty.cast(prop).value = adsk.core.Color.create(*rgb, 255)
            break
    return ap


# ---------------------------------------------------------------- test coupons
def referencia():
    t = time.time()
    root = _design(_require_open()).rootComponent
    _delete_component(root, REF_COMPONENT)
    comp = _new_component(root, REF_COMPONENT)
    prof = _misumi_sketch(comp)
    _extrude(comp, prof, REF_COMPONENT, 'test_length')
    print(f'referencia: {time.time() - t:.1f} s')


def perfil(name):
    """One test coupon. A name in config.VARIANTES is the standard clip (or the profile given by its
    '_perfil' key) with those parameters changed (config.FARPAS, older: the standard clip with that
    barb). Direct mode."""
    t = time.time()
    importlib.reload(perfis)
    design = _design(_require_open())
    root = design.rootComponent
    _delete_component(root, name)
    comp = _new_component(root, name)
    variants = dict(getattr(config, 'VARIANTES', {}))
    variants.update({k: ({'fin_barb': b} if b else {}) for k, b in getattr(config, 'FARPAS', {}).items()})
    changes = {k: e for k, e in variants.get(name, {}).items() if not k.startswith('_')}
    base = variants[name].get('_perfil', 'clip-padrao') if name in variants else name   # '_perfil': a cover variant
    keep = _CTX['vals']
    try:
        _CTX['vals'] = _vals_with(changes)
        _check_wall(name, base)
        prof, sk = _profile_sketch(design, comp, base)
        body = _extrude(comp, prof, name, 'test_length').bodies.item(0)
        _barb_stretches(comp, body, base, _CTX['vals']['test_length'])
        _marca(comp, body, getattr(config, 'MARCAS', {}).get(name, 0))
    finally:
        _CTX['vals'] = keep
    print(f'perfil {name}' + (f' ({changes})' if changes else '') + f': {time.time() - t:.1f} s')


def _check_wall(name, profile):
    """Refuse a split-fin clip whose leg wall is thinner than fin_min_wall (0.4 by default): the slicer
    would drop it (v8's clip 3 lost its leg tips at 0.38). Direct mode (the values are in Python)."""
    if profile not in perfis.SPLIT_FIN or not _CTX['direto']:
        return
    wall, least = perfis.leg_min_wall(profile, _CTX['vals']), _CTX['vals'].get('fin_min_wall', 0.4)
    if wall < least - 0.005:
        raise RuntimeError(f'{name}: parede da perna de {wall:.3f} mm, abaixo de fin_min_wall {least:.2f} '
                           f'(engrosse fin_tip_leg ou encurte fin_inner_straight)')


def _marca(comp, body, n):
    """n grooves across the piece's top (its highest face along d: a clip's dovetail), near the start
    of its length, to tell test variants apart (config.MARCAS). 1 mm wide, 0.6 deep, 2.5 apart."""
    if n <= 0:
        return
    bb = body.boundingBox
    x0, x1, top = bb.minPoint.x * 10 - 1, bb.maxPoint.x * 10 + 1, bb.maxPoint.y * 10
    xy = comp.xYConstructionPlane
    for i in range(n):
        z = 3 + 2.5 * i
        pl = _offset_plane(comp, xy, f'{z} mm', (0, 0, 1))
        pts = [(f'{x0:.3f} mm', f'{top - 0.6:.3f} mm', f'{z} mm'), (f'{x1:.3f} mm', f'{top - 0.6:.3f} mm', f'{z} mm'),
               (f'{x1:.3f} mm', f'{top + 1:.3f} mm', f'{z} mm'), (f'{x0:.3f} mm', f'{top + 1:.3f} mm', f'{z} mm')]
        sk, pr = _poly_sketch(comp.parentDesign, comp, pl, pts, f'marca {i + 1}')
        _extrude_dir(comp, pr, sk, '1 mm', (0, 0, 1), CUT, body)


def _vals_with(changes):
    """The parameter table evaluated again with some expressions changed, so derived values follow
    them (fin_barb_ramp from fin_barb). A change that names a parameter defined further down the
    table (test_length = 'clip_run_h / 6') is applied once the table is done."""
    vals, late = {}, {}
    for _, n, e, _, _ in parametros.PARAMS:
        if n in changes:
            try:
                vals[n] = perfis.evaluate(changes[n], vals)
                continue
            except NameError:
                late[n] = changes[n]
        vals[n] = perfis.evaluate(e, vals)
    for n, e in list(late.items()) + [(n, e) for n, e in changes.items() if n not in vals]:
        vals[n] = perfis.evaluate(e, vals)
    return vals


def _barb_stretches(comp, body, profile, length):
    """Split-fin clip with the barb only in stretches of fin_anchor_length (one at each end, then evenly
    spaced, at most fin_anchor_gap apart); between them the legs have no barb (perfis.barb_cut), so a
    long clip takes the force of its stretches, not of its whole length. fin_anchor_length 0: barb
    all along (the default). length in mm. Returns the stretches as (start, end) in mm."""
    v = _CTX['vals']
    a, g = v.get('fin_anchor_length', 0.0), v.get('fin_anchor_gap', 0.0)
    if profile not in perfis.SPLIT_FIN or a <= 0 or length <= 2 * a:
        return [(0.0, length)]
    n = max(2, math.ceil((length + g) / (a + g) - 1e-9))
    step = (length - a) / (n - 1)
    stretches = [(i * step, i * step + a) for i in range(n)]
    xy = comp.xYConstructionPlane
    for (_, z0), (z1, _) in zip(stretches, stretches[1:]):
        pl = _offset_plane(comp, xy, f'{z0:.4f} mm', (0, 0, 1))
        for side in (1, -1):
            pts = [(s if side > 0 else f'-( {s} )', d, f'{z0:.4f} mm') for s, d in perfis.barb_cut()]
            sk, pr = _poly_sketch(comp.parentDesign, comp, pl, pts, 'sem farpa')
            _extrude_dir(comp, pr, sk, f'{z1 - z0:.4f} mm', (0, 0, 1), CUT, body)
    return stretches


PASSO = 4.0   # cm between coupon sets


def arranjar():
    """Lay the coupons out side by side: each clip with its cover, the acrylic and the 1515 reference."""
    t = time.time()
    design = _design(_require_open())
    root = design.rootComponent
    um = design.unitsManager
    coupons = {c for c, *_ in CONJUNTOS} | {c for _, c, *_ in CONJUNTOS} | {'acrilico-ref', REF_COMPONENT}
    first = {}
    for occ in list(root.occurrences):
        name = occ.component.name
        if name not in coupons:
            continue
        if name in first:
            occ.deleteMe()
        else:
            first[name] = occ
    used = set()

    def place(name, x):
        m = adsk.core.Matrix3D.create()
        m.translation = V3(x, 0, 0)
        if name not in used:
            first[name].transform = m
            used.add(name)
        else:
            occ = root.occurrences.addExistingComponent(first[name].component, m)
            if _CTX['direto']:
                occ.transform2 = m        # direct modeling composes m with the first occurrence's place

    for i, (clip, cover, cover_shift, acr_shift, ref) in enumerate(CONJUNTOS):
        x = i * PASSO
        place(clip, x)
        place(cover, x + _cm(cover_shift))
        place('acrilico-ref', x + _cm(acr_shift))
        if ref:
            place(REF_COMPONENT, x)
    _capture_positions(design)
    print(f'arranjar: {len(CONJUNTOS)} conjuntos, {time.time() - t:.1f} s')




def exportar_stl(nomes=None, pasta=None):
    """Export components (default: the test coupons) as binary STL in mm, one file per component.

    nomes: a list (one of each) or {name: quantity}; the quantity goes in the file name (<name>-2x.stl),
    and quantidades.json lists them.
    """
    t = time.time()
    nomes = nomes or PROVAS
    qtd = dict(nomes) if isinstance(nomes, dict) else {name: 1 for name in nomes}
    ver = DOC_NAME.split('-')[-1]
    pre = config.STL_PREFIX
    pasta = pasta or os.path.join(os.path.dirname(HERE), 'stl', f'{pre}provas-{ver}' if nomes == PROVAS else f'{pre}pecas-{ver}')
    os.makedirs(pasta, exist_ok=True)
    design = _design(_require_open())
    em = design.exportManager
    for name, q in qtd.items():
        body = design.allComponents.itemByName(name).bRepBodies.item(0)
        opts = em.createSTLExportOptions(body, os.path.join(pasta, f'{name}-{q}x.stl'))
        opts.meshRefinement = adsk.fusion.MeshRefinementSettings.MeshRefinementHigh
        opts.isBinaryFormat = True
        opts.unitType = adsk.fusion.DistanceUnits.MillimeterDistanceUnits
        em.execute(opts)
    with open(os.path.join(pasta, 'quantidades.json'), 'w') as f:
        json.dump(dict(sorted(qtd.items())), f, indent=1, ensure_ascii=False)
    print(f'exportar_stl: {len(qtd)} arquivos ({sum(qtd.values())} peças) em {pasta}, {time.time() - t:.1f} s')


def exportar_faces(faces, pasta):
    """Export the pieces of assembled faces (montar), each file named with its count across those faces."""
    design = _design(_require_open())
    qtd = {}
    for face in faces:
        comp = design.allComponents.itemByName(f'face-{face}')
        if comp is None:
            raise RuntimeError(f'face-{face} não existe; rode montar() antes')
        for occ in comp.allOccurrences:
            if occ.component.bRepBodies.count:
                qtd[occ.component.name] = qtd.get(occ.component.name, 0) + 1
    exportar_stl(dict(sorted(qtd.items())), pasta)
    return qtd


# ---------------------------------------------------------------- frame reference
def frame_ref():
    """The V0.2 frame: Misumi 1515 members placed as in the official CAD (component frame-v0)."""
    t = time.time()
    design = _design(_require_open())
    root = design.rootComponent
    for name in (FRAME_COMPONENT, 'ref-1515-200', 'ref-1515-80'):
        _delete_component(root, name)
    data = json.load(open(_ref(config.FRAME_JSON)))['membros']
    frame = _new_component(root, FRAME_COMPONENT)
    frame_occ = next(o for o in root.occurrences if o.component == frame)
    members = {}
    for m in data:
        length = round(m['comprimento'])
        k = 'XYZ'.index(m['eixo'])
        i, j = (k + 1) % 3, (k + 2) % 3        # right-handed: e_i x e_j = e_k
        # some CAD boxes are 0.1 mm loose on their max side (top hat rails measure 15.1) and others carry
        # 0.01 mm noise (99.99): position the 15 mm square from the min side, rounded to 0.1 mm
        bb = [round(c, 1) / 10 for c in m['bb']]
        half = _param_values(design)['frame_size'] / 20      # cm
        o = [0.0, 0.0, 0.0]
        o[i] = bb[i] + half
        o[j] = bb[j] + half + half            # the profile square is centred at local (0, -frame_size / 2)
        o[k] = bb[k]
        unit = lambda q: V3(*[1.0 if r == q else 0.0 for r in range(3)])  # noqa: E731
        mat = adsk.core.Matrix3D.create()
        mat.setWithCoordinateSystem(P3(*o), unit(i), unit(j), unit(k))
        if _CTX['direto']:
            # direct modeling: one body per member, copied and moved into place (occurrences of a
            # shared component drift there when other parts of the design change)
            if length not in members:
                tmp = _new_component(root, f'tmp-1515-{length}')
                _extrude(tmp, _misumi_sketch(tmp), 'tmp', f'{length} mm')
                members[length] = adsk.fusion.TemporaryBRepManager.get().copy(tmp.bRepBodies.item(0))
                _delete_component(root, tmp.name)
            tbm = adsk.fusion.TemporaryBRepManager.get()
            body = tbm.copy(members[length])
            tbm.transform(body, mat)
            frame.bRepBodies.add(body).name = m.get('nome', f'1515 {length}')
            continue
        if length not in members:
            occ = frame.occurrences.addNewComponent(mat)
            comp = occ.component
            comp.name = f'ref-1515-{length}'
            prof = _misumi_sketch(comp)
            _extrude(comp, prof, comp.name, f'{length} mm')
            members[length] = comp
        else:
            _place(frame_occ, members[length], mat)
    _capture_positions(design)
    print(f'frame_ref: {len(data)} membros, {time.time() - t:.1f} s')


# ---------------------------------------------------------------- straight pieces and faces
T_EXPR = '( panel_frame_spacing + panel_thickness )'
CUT = adsk.fusion.FeatureOperations.CutFeatureOperation
JOIN = adsk.fusion.FeatureOperations.JoinFeatureOperation
NEW = adsk.fusion.FeatureOperations.NewBodyFeatureOperation


def pecas(nomes=None):
    """Build straight-piece components (mapa.PECAS) inside component 'pecas', laid out in a row.

    Cover middles are extruded joint_scarf longer at each end and the extra is cut at 45°, so only
    their top overlaps the corner legs (the scarf joint).
    """
    t = time.time()
    importlib.reload(perfis)
    design = _design(_require_open())
    root = design.rootComponent
    parent = _parent(design, 'pecas')
    order = list(mapa.PECAS)
    feitos = []
    for name in nomes or order:
        profile, length = mapa.PECAS[name]
        _check_wall(name, profile)
        _delete_component(root, name)
        mat = adsk.core.Matrix3D.create()
        if not _CTX['direto']:     # direct modeling: pieces at the origin (see _place)
            mat.translation = V3(order.index(name) * 3.0, -40.0, 0)
        comp = parent.occurrences.addNewComponent(mat).component
        comp.name = name
        prof, sk = _profile_sketch(design, comp, profile)
        if profile == 'tampa-h':
            # half of the rear middle cover: the outer end follows the vertical cover's inner chamfer
            # (straight to its foot, then 45° up), so the T joint closes without a gap
            body = _extrude(comp, prof, name, f'{length} + cover_cut + 1 mm').bodies.item(0)
            ch0, top = f'{T_EXPR} + cover_height - cover_cut', f'{T_EXPR} + cover_height + 1 mm'
            pts = [('0 mm', f'{T_EXPR} - 1 mm', length), ('0 mm', ch0, length),
                   ('0 mm', top, f'{length} + {top} - ( {ch0} )'), ('0 mm', top, f'{length} + 10 mm'),
                   ('0 mm', f'{T_EXPR} - 1 mm', f'{length} + 10 mm')]
            skw, pw = _poly_sketch(design, comp, comp.yZConstructionPlane, pts, 'ponta da tampa em H')
            _extrude_sym(comp, pw, '60 mm', CUT, body)
        elif not profile.startswith('tampa'):
            body = _extrude(comp, prof, name, length).bodies.item(0)
            _barb_stretches(comp, body, profile, _cm(length) * 10)
        else:
            total = f'( {length} + 2 * joint_scarf )'
            body = _extrude(comp, prof, name, total).bodies.item(0)
            rec, top = f'{T_EXPR} + cover_recess', f'{T_EXPR} + cover_height + 2 mm'
            for pts in ([('0 mm', '-12 mm', 'joint_scarf'), ('0 mm', rec, 'joint_scarf'),
                         ('0 mm', top, '-2 mm'), ('0 mm', '-12 mm', '-2 mm')],
                        [('0 mm', '-12 mm', f'{total} - joint_scarf'), ('0 mm', rec, f'{total} - joint_scarf'),
                         ('0 mm', top, f'{total} + 2 mm'), ('0 mm', '-12 mm', f'{total} + 2 mm')]):
                skw, pw = _poly_sketch(design, comp, comp.yZConstructionPlane, pts, 'chanfro da junta')
                _extrude_sym(comp, pw, '60 mm', CUT, body)
        feitos.append(f'{name} ({sk.isFullyConstrained})')
    _capture_positions(design)
    print(f'pecas: {feitos}, {time.time() - t:.1f} s')


def cantos(nomes=None, etapa=None):
    """Build L corner components (mapa.CANTOS) inside component 'pecas'.

    Local frame: x along leg A, y along leg B, z = d, origin at the outer corner of the cover frame.
    corner = leg A + leg B, minus the space each edge's clips occupy from where they start, minus
    the 45° scarf at each leg end that meets a cover middle, plus the finger grip on one leg.

    etapa: 'pernas' (rebuilds the component), 'clips', 'miolo' (canto_miolo machines only), 'juntas',
    'pega' (finger grip) or 'dobradica' (hinge knuckle, mapa.DOBRADICA corners only), to keep each Fusion
    call short; None runs them all.
    The heavier steps also run in parts, one per call: 'pernaA' then 'pernaB', 'clipsA', 'clipsB',
    'pega-labio' then 'pega-rebaixo', 'dobradica-no' then 'dobradica-furo' and 'dobradica-cunha'.
    """
    importlib.reload(perfis)
    design = _design(_require_open())
    _parent(design, 'pecas')              # visible, or direct modeling skips its bodies in cuts
    for name in nomes or list(mapa.CANTOS):
        for step in ([etapa] if etapa else ['pernas', 'clips', 'miolo', 'juntas', 'pega', 'dobradica']):
            t = time.time()
            _canto_etapa(design, name, step)
            print(f'canto {name}, {step}: {time.time() - t:.1f} s')
    _capture_positions(design)


def puxador(nome=None, parte=None):
    """Door handle (v11) on a cover middle: a ledge at the cover's top, flush with it (the cover still
    prints face down), carried past one of the cover's edges, for the fingertips, with a V groove on top.
    Centred on the piece; run after pecas([nome]). config.PUXADOR = (piece, side): 'fora' past the frame
    edge (V0, latch side), 'dentro' past the cover's inner edge, over the door's own sheet (Trident, door
    centre, where the two doors meet).

    Piece frame: x = s, y = d, z along the edge (0 to length + 2 * joint_scarf).
    parte: 'aba' or 'sulco' to run one half per call; None runs both.
    """
    t = time.time()
    nome_cfg, lado = getattr(config, 'PUXADOR', ('tampa-parede-v-puxador', 'fora'))
    nome = nome or nome_cfg
    design = _design(_require_open())
    _parent(design, 'pecas')              # visible, or direct modeling skips its bodies in cuts
    comp = design.allComponents.itemByName(nome)
    xy, xz = comp.xYConstructionPlane, comp.xZConstructionPlane
    length = mapa.PECAS[nome][1]
    zc = f'( {length} + 2 * joint_scarf ) / 2'
    top, ch0 = f'{T_EXPR} + cover_height', f'{T_EXPR} + cover_height - cover_cut'
    e = 'handle_edge_chamfer'
    half = 'handle_length / 2 + handle_taper'
    # S(u): s of a point u outward from the cover's edge line the ledge passes (- = into the cover)
    if lado == 'fora':
        S = lambda u: f'frame_size / 2 + ( {u} )'                     # noqa: E731
    else:
        S = lambda u: f'-( frame_size / 2 + cover_overlap ) - ( {u} )'  # noqa: E731
    if parte in (None, 'aba'):
        _handle_ledge(design, comp, nome, xy, xz, length, zc, top, ch0, S, e, half)
    if parte in (None, 'sulco'):
        _handle_groove(design, comp, nome, xy, zc, top)
    print(f'puxador {nome} ({lado}, {parte or "tudo"}): corpos {comp.bRepBodies.count}, {time.time() - t:.1f} s')


def _handle_ledge(design, comp, nome, xy, xz, length, zc, top, ch0, S, e, half):
    # ledge: the chamfer on that edge filled up and carried past it, bottom at the chamfer's foot
    sec = [(S('-( cover_cut + 0.5 mm )'), top), (S(f'handle_reach - {e}'), top), (S('handle_reach'), f'{top} - {e}'),
           (S('handle_reach'), f'{ch0} + {e}'), (S(f'handle_reach - {e}'), ch0), (S('0 mm'), ch0),
           (S('0 mm'), f'{ch0} - 0.5 mm'), (S('-0.5 mm'), f'{ch0} - 0.5 mm')]
    sk, pr = _poly_sketch(design, comp, xy, [(s, d, '0 mm') for s, d in sec], 'puxador seção')
    a = _extrude_dir(comp, pr, sk, f'( {length} + 2 * joint_scarf )', (0, 0, 1), NEW).bodies.item(0)
    plan = [(S('-( cover_cut + 1 mm )'), f'{zc} - ( {half} )'), (S('0 mm'), f'{zc} - ( {half} )'),
            (S('handle_reach'), f'{zc} - handle_length / 2'), (S('handle_reach'), f'{zc} + handle_length / 2'),
            (S('0 mm'), f'{zc} + {half}'), (S('-( cover_cut + 1 mm )'), f'{zc} + {half}')]
    sk, pr = _poly_sketch(design, comp, xz, [(s, '0 mm', z) for s, z in plan], 'puxador planta')
    b = _extrude_sym(comp, pr, '40 mm', NEW).bodies.item(0)
    tools = adsk.core.ObjectCollection.create()
    tools.add(b)
    inp = comp.features.combineFeatures.createInput(a, tools)
    inp.operation = adsk.fusion.FeatureOperations.IntersectFeatureOperation
    comp.features.combineFeatures.add(inp)
    ledge = _loose_body(comp, nome)
    tools = adsk.core.ObjectCollection.create()
    tools.add(ledge)
    comp.features.combineFeatures.add(comp.features.combineFeatures.createInput(comp.bRepBodies.itemByName(nome), tools))


def _handle_groove(design, comp, nome, xy, zc, top):
    # V groove on top, centred on the handle
    g, gw = 'handle_groove_s', 'handle_groove_width / 2'
    groove = [(f'{g} - {gw}', f'{top} + 1 mm'), (f'{g} - {gw}', top), (g, f'{top} - handle_groove_depth'),
              (f'{g} + {gw}', top), (f'{g} + {gw}', f'{top} + 1 mm')]
    pl = _offset_plane(comp, xy, zc, (0, 0, 1))
    sk, pr = _poly_sketch(design, comp, pl, [(s, d, zc) for s, d in groove], 'puxador sulco')
    _extrude_sym(comp, pr, 'handle_groove_length', CUT, comp.bRepBodies.itemByName(nome))


def logo(nome='tampa-parede-h-logo'):
    """The Voron logo of v11 (referencia/logo_voron.json): a component of its own, logo_thickness on the
    cover's outer face, and the matching pocket cut in the cover. Both share the cover's frame, so the two
    STLs load aligned in the slicer (print the cover face down, the logo as a part in another filament)."""
    t = time.time()
    design = _design(_require_open())
    root = design.rootComponent
    parent = _parent(design, 'pecas')
    data = json.load(open(_ref(config.LOGO_JSON)))
    cover = design.allComponents.itemByName(nome)
    centre = _cm(f'( {mapa.PECAS[nome][1]} + 2 * joint_scarf ) / 2') * 10
    top = _cm(f'{T_EXPR} + cover_height') * 10
    base = top - data['espessura']
    _delete_component(root, 'logo-voron')
    mat = adsk.core.Matrix3D.create()
    if not _CTX['direto']:     # direct modeling: pieces at the origin (see _place)
        mat.translation = V3(len(mapa.PECAS) * 3.0, -40.0, 0)
    comp = parent.occurrences.addNewComponent(mat).component
    comp.name = 'logo-voron'
    loops = [data['externo']] + data['furos']
    for target, op in ((comp, NEW), (cover, CUT)):
        plane = _offset_plane(target, target.xZConstructionPlane, f'{base} mm', (0, 1, 0))
        sk = target.sketches.add(plane)
        sk.name = 'logo Voron'
        sk.isComputeDeferred = True
        lines = sk.sketchCurves.sketchLines
        for lp in loops:
            pts = [sk.modelToSketchSpace(P3(s_ / 10, base / 10, (centre + a) / 10)) for s_, a in lp]
            first = lines.addByTwoPoints(P3(pts[0].x, pts[0].y, 0), P3(pts[1].x, pts[1].y, 0))
            prev = first.endSketchPoint
            for p in pts[2:]:
                prev = lines.addByTwoPoints(prev, P3(p.x, p.y, 0)).endSketchPoint
            lines.addByTwoPoints(prev, first.startSketchPoint)
        sk.isComputeDeferred = False
        prof = max(sk.profiles, key=lambda p: p.areaProperties().area)   # the hexagon less its three cuts
        body = None if op == NEW else target.bRepBodies.item(0)
        ext = _extrude_dir(target, prof, sk, f'{data["espessura"]} mm + 0.01 mm' if op == CUT else f'{data["espessura"]} mm',
                           (0, 1, 0), op, body)
        if op == NEW:
            ext.bodies.item(0).name = 'logo-voron'
    print(f'logo: área {comp.bRepBodies.item(0).physicalProperties.area * 100:.1f} mm², '
          f'volume {comp.bRepBodies.item(0).physicalProperties.volume * 1000:.1f} mm³, {time.time() - t:.1f} s')


def passa_bowden(nome='passa-bowden'):
    """Trident without the exhaust filter: plug for the stock rear sheet's exhaust notch, with the hole
    for the bowden fitting (the user's inner plate and bowden arm stay, clamped by the fitting's nut).

    Piece frame = the rear top edge's (x = s, y = d, z along the edge, 0 at the edge's centre): the plug
    fills the notch in the sheet's plane, its top under the edge's clips and cover like the sheet; the
    outer plate laps over the sheet on the sides and bottom, stopping short of the cover.
    """
    t = time.time()
    design = _design(_require_open())
    root = design.rootComponent
    parent = _parent(design, 'pecas')
    _delete_component(root, nome)
    comp = parent.occurrences.addNewComponent(adsk.core.Matrix3D.create()).component
    comp.name = nome
    xz = comp.xZConstructionPlane
    so, c, ch = '( slot_opening / 2 )', 'bowden_plug_clearance', 'bowden_plate_chamfer'
    bottom = f'-( {so} + exhaust_notch_depth )'                     # notch bottom; the sheet's top edge at -so
    # plug: the notch less the clearance, bottom corners chamfered past the notch's r 3.5
    s0, s1, hw = f'{bottom} + {c}', f'-( {so} + {c} )', f'( exhaust_notch_width / 2 - {c} )'
    plug = [(s1, f'-{hw}'), (s1, hw), (f'{s0} + {ch}', hw), (s0, f'{hw} - {ch}'), (s0, f'-( {hw} - {ch} )'),
            (f'{s0} + {ch}', f'-{hw}')]
    pl = _offset_plane(comp, xz, 'panel_frame_spacing', (0, 1, 0))
    sk, pr = _poly_sketch(design, comp, pl, [(s, 'panel_frame_spacing', z) for s, z in plug], 'tampão')
    body = _extrude_dir(comp, pr, sk, 'panel_thickness', (0, 1, 0), NEW).bodies.item(0)
    body.name = nome
    # outer plate over the sheet: sides and bottom, up to just below the top edge's cover
    p0, p1 = f'{bottom} - bowden_plate_overlap', '-( frame_size / 2 + cover_overlap + bowden_cover_gap )'
    pw = '( exhaust_notch_width / 2 + bowden_plate_overlap )'
    plate = [(f'{p1} - {ch}', f'-{pw}'), (p1, f'-( {pw} - {ch} )'), (p1, f'{pw} - {ch}'), (f'{p1} - {ch}', pw),
             (f'{p0} + {ch}', pw), (p0, f'{pw} - {ch}'), (p0, f'-( {pw} - {ch} )'), (f'{p0} + {ch}', f'-{pw}')]
    pl = _offset_plane(comp, xz, T_EXPR, (0, 1, 0))
    sk, pr = _poly_sketch(design, comp, pl, [(s, T_EXPR, z) for s, z in plate], 'aba de fora')
    _extrude_dir(comp, pr, sk, 'bowden_plate_thickness', (0, 1, 0), JOIN, body)
    # the fitting's hole
    sk, pr = _circle_sketch(design, comp, xz, (f'{bottom} + bowden_hole_up', '0 mm', 'bowden_hole_x'), 'bowden_hole', 'furo do passa-tubo')
    _extrude_sym(comp, pr, '40 mm', CUT, body)
    b = comp.bRepBodies.item(0)
    print(f'passa_bowden: volume {b.physicalProperties.volume * 1000:.0f} mm³, {time.time() - t:.1f} s')


def _box(design, comp, body, s, d, z, op, name):
    """Box (s0, s1) x (d0, d1) x (z0, z1) in mm in a piece's frame (x = s, y = d, z along), cut from,
    joined to or (NEW) made as a body."""
    pl = _offset_plane(comp, comp.xYConstructionPlane, f'{z[0]:.4f} mm', (0, 0, 1))
    pts = [(f'{a:.4f} mm', f'{b:.4f} mm', f'{z[0]:.4f} mm') for a, b in ((s[0], d[0]), (s[1], d[0]), (s[1], d[1]), (s[0], d[1]))]
    sk, pr = _poly_sketch(design, comp, pl, pts, name)
    return _extrude_dir(comp, pr, sk, f'{z[1] - z[0]:.4f} mm', (0, 0, 1), op, body)


def _trava_geo(v):
    """Lock coupon geometry (geometria_trava.geo, kept there so the maps can use it without Fusion)."""
    return geometria_trava.geo(v)


def _box_rampa(design, comp, body, s, d, z, d_sup, name):
    """Box cut as _box, its near end (z[0]) leaning back toward z = 0 at 45 deg above d = d_sup."""
    near = lambda dd: z[0] - max(0.0, dd - d_sup)   # noqa: E731
    pts = [(d[0], z[1]), (d[1], z[1]), (d[1], near(d[1]))] + ([(d_sup, z[0])] if d[0] < d_sup < d[1] else []) + [(d[0], near(d[0]))]
    pl = _offset_plane(comp, comp.yZConstructionPlane, f'{s[0]:.4f} mm', (1, 0, 0))
    sk, pr = _poly_sketch(design, comp, pl, [(f'{s[0]:.4f} mm', f'{a:.4f} mm', f'{b:.4f} mm') for a, b in pts], name)
    return _extrude_dir(comp, pr, sk, f'{s[1] - s[0]:.4f} mm', (1, 0, 0), CUT, body)


def _chanfro_mesa(comp, body, planes, dist, skip=None, outer=False):
    """Chamfer of dist mm on the edges of body's flat faces lying on one of planes, (axis, value in mm)
    pairs: the faces that touch the bed, against elephant's foot. An edge whose other face already
    leans 45 deg or flatter from the bed (a cover's chamfer, a scarf, the cursor's nose) is left as it
    is, and so is one whose midpoint (piece frame, mm) skip() accepts; outer: only each face's outer
    loop (not a pocket inside it, as the logo's). All at once if Fusion takes it, else edge by edge;
    returns (done, failed)."""
    def mids():
        out = []
        for f in body.faces:
            if f.geometry.surfaceType != adsk.core.SurfaceTypes.PlaneSurfaceType:
                continue
            xyz = [[vx.geometry.x * 10, vx.geometry.y * 10, vx.geometry.z * 10] for vx in f.vertices]
            if not any(all(abs(c[axis] - value) < 1e-3 for c in xyz) for axis, value in planes):
                continue
            for lp in f.loops:
                if outer and not lp.isOuter:
                    continue
                for e in lp.edges:
                    ok, a, b = e.evaluator.getParameterExtents()
                    ok, p = e.evaluator.getPointAtParameter((a + b) / 2)
                    m = (p.x * 10, p.y * 10, p.z * 10)
                    other = [g for g in e.faces if g != f]
                    if other:
                        ok, n0 = f.evaluator.getNormalAtPoint(p)
                        ok, n1 = other[0].evaluator.getNormalAtPoint(p)
                        if n0.dotProduct(n1) > 0.6:     # other face within ~53 deg of the bed: already sloped
                            continue
                        # other face lower than the chamfer (the 0.15 notch between a hinge knuckle and
                        # the cover's chamfer): no room for it, and the elephant's foot only fills the notch
                        axis, value = next((ax, va) for ax, va in planes if all(abs(c[ax] - va) < 1e-3 for c in xyz))
                        if max(abs([vx.geometry.x, vx.geometry.y, vx.geometry.z][axis] * 10 - value) for vx in other[0].vertices) < dist - 1e-3:
                            continue
                    if not (skip and skip(m)) and all(math.dist(m, mm) > 1e-3 for mm, _ in out):
                        out.append((m, e))
        return out

    def chamfer(edges):
        inp = comp.features.chamferFeatures.createInput2()
        inp.chamferEdgeSets.addEqualDistanceChamferEdgeSet(edges, adsk.core.ValueInput.createByReal(dist / 10), False)
        comp.features.chamferFeatures.add(inp)
    found = mids()
    if not found:
        return 0, 0
    coll = adsk.core.ObjectCollection.create()
    for _, e in found:
        coll.add(e)
    try:
        chamfer(coll)
        return len(found), 0
    except RuntimeError:
        pass
    done = failed = 0
    for m, _ in found:
        match = [e for mm, e in mids() if math.dist(mm, m) < 1e-3]
        if not match:
            continue                              # taken by a neighbour's chamfer
        one = adsk.core.ObjectCollection.create()
        one.add(match[0])
        try:
            chamfer(one)
            done += 1
        except RuntimeError:
            failed += 1
    return done, failed


def _chanfro_encaixe(comp, body, planes, dist, fino, dist_fino):
    """_chanfro_mesa with dist, except dist_fino on the edges whose midpoint fino() accepts: a fit with no
    clearance, where a big chamfer eats the lips and none lets the elephant's foot bind it."""
    a = _chanfro_mesa(comp, body, planes, dist, skip=fino)
    b = _chanfro_mesa(comp, body, planes, dist_fino, skip=lambda m: not fino(m)) if dist_fino > 0 else (0, 0)
    return a[0] + b[0], a[1] + b[1]


def chanfro_mesa(nomes=None):
    """bed_chamfer on the edges that touch the bed, on the straight pieces and corners (default all of
    mapa.PECAS and mapa.CANTOS; run after pecas, puxador, logo and cantos, as the last step on them):

    clips              printed standing on an end: both ends' edges (either end can go down), not the
                       fin's (it flexes in the slot, too thin at the tips)
    covers, corners    printed outer face down: the outer face's outline, not a pocket inside it (the
                       logo's, which takes an inlay flush with the face)
    """
    t = time.time()
    design = _design(_require_open())
    _parent(design, 'pecas')              # visible, or direct modeling skips its bodies
    v = _param_values(design)
    dist = v.get('bed_chamfer', 0.0)
    if dist <= 0:
        print('chanfro_mesa: bed_chamfer 0, nada a fazer')
        return
    top = v['panel_frame_spacing'] + v['panel_thickness'] + v['cover_height']
    out = {}
    ja = []
    for name in nomes or list(mapa.PECAS) + list(mapa.CANTOS):
        comp = design.allComponents.itemByName(name)
        if comp.attributes.itemByName('gerador', 'chanfro_mesa'):
            ja.append(name)                     # done since the piece was last built (pecas/cantos rebuild it)
            continue
        body = comp.bRepBodies.itemByName(name) or comp.bRepBodies.item(0)
        if name in mapa.CANTOS:
            planes, skip = [(2, top)], None                              # corner frame: z = d
        elif mapa.PECAS[name][0].startswith('tampa'):
            planes, skip = [(1, top)], None                              # piece frame: y = d
        else:
            planes, skip = [(2, 0.0), (2, _cm(mapa.PECAS[name][1]) * 10)], (lambda m: m[1] < -1e-3)
        out[name] = _chanfro_mesa(comp, body, planes, dist, skip, outer=True)
        comp.attributes.add('gerador', 'chanfro_mesa', f'{dist}')
    bad = {k: f for k, (d_, f) in out.items() if f}
    print(f'chanfro_mesa {dist:.2f} mm: {len(out)} peças, arestas {sum(d_ for d_, _ in out.values())}'
          f'{f", falharam {bad}" if bad else ""}{f", já tinham {ja}" if ja else ""}; {time.time() - t:.1f} s')
    return out


def trava_deslizante(parte=None, variante=None):
    """Sliding lock test coupon (Trident v8 on; the V0 since 2026-10-28), four components in place, open (parte: 'clip', 'tampa',
    'cursor' or 'capa' builds just that one; one call each keeps a call short):

    trava-clip    the standard clip, trava_comprimento long. A window without legs where the tongue sits
                  when open (the legs come back at 45 deg on the window's near side, so the clip prints
                  standing on its far end), the neck's slot (closed; its near end leans back at 45 deg
                  for the same print), and the barb only where the tongue sits locked: elsewhere the legs
                  are straight at the slot's width
    trava-tampa   the wall cover, as long, with the neck's slot through its top, under the cap, and a dot
                  ahead of the open cap that the locked cap hides; trava-indicador is the disc that fills
                  the dot, to print in another filament like the logo
    trava-cursor  tongue (with a 45 deg keel down to the slot's floor), neck and a dovetail on the neck's
                  tip above the cover (its rear flank at 45 deg); on the V0 the neck widens outward above the
                  clip's base, over the outer leg's root (the clip's base is cut that wide only where the
                  slider goes in, over the window). Printed on its rear end: the
                  layers run along the neck, and its widths come out in XY like the slots and the gap
                  between the legs. It goes in from
                  below, the panel off the printer: the tongue through the window, the neck and its
                  tip up through the slots, so the clip and the cover need no opening for the tongue. With
                  trava_dentes (the one-piece v4) the tongue is that many teeth, narrower between them, with
                  45 deg ramps, and the keel only under them; no pointed nose
    trava-capa    the knob (crest over the neck, concave flanks, flat ends) over the cover's flat top, long
                  enough to hide the slot open and locked. Slides onto the neck's tip from the inner side
                  (-s), its socket open on the outer edge; printed on its inner end, the socket's open
                  end up: the socket's profile comes out in XY, like the stub's height on the slider,
                  and every layer draws the lips whole (underside down, the 1 mm rear lip was five
                  layers tapering to nothing and the bridged roof squeezed the stub)
    Every part gets trava_chanfro_mesa on the edges that touch the bed in those orientations. Fits: the
    tongue is the gap between the legs, the slots the neck's width; trava_folga_haste comes off the neck.

    variante: a name in config.TRAVA_VARIANTES builds that variant's slider and cap (parte 'cursor' or
    'capa', default both) as 'trava-cursor-<name>' and 'trava-capa-<name>', beside the standard ones and
    for the same clip and cover, with config.TRAVA_MARCAS grooves (a variant of only the cap, as the socket's
    clearance, is built with parte='capa' and fits the standard slider).
    """
    t = time.time()
    design = _design(_require_open())
    root = design.rootComponent
    v = _vals_with(config.TRAVA_VARIANTES[variante]) if variante else _CTX['vals']
    g = _trava_geo(v)
    so, inner, T, top, w, hs, hz = g['so'], g['inner'], g['T'], g['top'], g['w'], g['hs'], g['hz']
    z0, lk, gap = g['z0'], g['lk'], g['gap']
    L, dt = v['trava_comprimento'], T + v['dovetail_height'] + 1
    th, fl = v['trava_toco_altura'], v['trava_toco_aba']
    zc, tz, tl = g['zc'], g['tz'], g['tl']
    partes = [parte] if parte else (['cursor', 'capa'] if variante else ['clip', 'tampa', 'cursor', 'capa'])
    if variante and set(partes) - {'cursor', 'capa'}:
        raise ValueError('uma variante da trava só tem cursor e capa (o clip e a tampa são os de sempre)')
    nome = lambda p: f'trava-{p}-{variante}' if variante else f'trava-{p}'   # noqa: E731
    marca = config.TRAVA_MARCAS.get(variante, 0) if variante else 0
    chanfros = {}
    for p in partes:
        _delete_component(root, nome(p))
    if 'tampa' in partes:
        _delete_component(root, 'trava-indicador')
    if 'clip' in partes:
        comp = _new_component(root, 'trava-clip')
        prof, sk = _profile_sketch(design, comp, 'clip-padrao')
        body = _extrude(comp, prof, 'trava-clip', f'{L} mm').bodies.item(0)
        # no legs over the window; on its near side (z = 0) the legs start at the root and grow down at
        # 45 deg, so printed standing on z = L each layer of the leg rests on the one below, no support
        win, deep, s0 = g['win'], v['slot_depth'] + 1, so + v['fin_barb'] + 1
        pl = _offset_plane(comp, comp.yZConstructionPlane, f'{-s0:.4f} mm', (1, 0, 0))
        pts = [(f'{-s0:.4f} mm', f'{d:.4f} mm', f'{z:.4f} mm') for d, z in
               ((0.0, win[0]), (0.0, win[1]), (-deep, win[1]), (-deep, win[0] - deep))]
        sk, pr = _poly_sketch(design, comp, pl, pts, 'sem pernas')
        _extrude_dir(comp, pr, sk, f'{2 * s0:.4f} mm', (1, 0, 0), CUT, body)
        # the neck's slot, flush with the legs' inner face on +s; along it the dovetail's outer flank would
        # be a loose sliver (its root is in the slot): off up to the wall's inner face (nothing else of the
        # clip is out there above the shoulder), there the cover holds by the inner flank.
        # Printed standing on z = L, the clip comes back over the slot's near end: that end leans back at
        # 45 deg from the top of the base under the acrylic, so every layer rests on the one below
        dsup = v['panel_frame_spacing']
        _box_rampa(design, comp, body, (hs[0], inner), (0.0, dt), g['path'], dsup, 'rasgo da haste')
        _box_rampa(design, comp, body, (inner, v['frame_size'] / 2), (T + v['cover_recess'], dt), g['path'], dsup, 'lasca do rabo')
        # a neck wider above the step (the V0's): its slot out to wo from the top of the base, which stays
        # whole over the outer leg's root, and through the base where the slider goes in, open, over the
        # window without legs
        if g['wo'] > inner:
            if not g['win'][0] <= g['furo'][0] < g['furo'][1] <= g['win'][1]:
                raise ValueError(f'a entrada do pescoço largo (z {g["furo"]}) sai da janela sem pernas (z {g["win"]})')
            _box_rampa(design, comp, body, (inner, g['wo']), (dsup, T + v['cover_recess']), g['path'], dsup, 'rasgo largo')
            _box(design, comp, body, (inner, g['wo']), (-1.0, dsup + 0.5), g['furo'], CUT, 'entrada do pescoço largo')
        # the barb only where the tongue sits locked (perfis.barb_cut elsewhere): the rest of the legs is
        # straight at the slot's width, so the clip goes in and out with the force of that stretch only,
        # and locked the tongue keeps those legs from bending in
        xy = comp.xYConstructionPlane
        for za, zb in ((0.0, g['farpa'][0]), (g['farpa'][1], L)):
            if zb - za < 0.01:
                continue
            pl = _offset_plane(comp, xy, f'{za:.4f} mm', (0, 0, 1))
            for side in (1, -1):
                pts = [(s_ if side > 0 else f'-( {s_} )', d_, f'{za:.4f} mm') for s_, d_ in perfis.barb_cut()]
                sk, pr = _poly_sketch(design, comp, pl, pts, 'sem farpa')
                _extrude_dir(comp, pr, sk, f'{zb - za:.4f} mm', (0, 0, 1), CUT, body)
        # printed standing on z = L: that end's edges, not the legs' (they flex in the slot, thin at the tips)
        chanfros['clip'] = _chanfro_mesa(comp, body, [(2, L)], v['trava_chanfro_mesa'], skip=lambda m: m[1] < -1e-3)
    if 'tampa' in partes:
        comp = _new_component(root, 'trava-tampa')
        prof, sk = _profile_sketch(design, comp, 'tampa-parede')
        body = _extrude(comp, prof, 'trava-tampa', f'{L} mm').bodies.item(0)
        _box(design, comp, body, (hs[0], max(hs[1], g['wo'])), (T - 0.1, top + 1), g['path'], CUT, 'rasgo da haste')
        # the open/locked dot: a pocket in the top, and a disc that fills it (another filament, as the logo)
        (si, zi), di, dp = g['ind'], v['trava_indicador_diametro'], v['trava_indicador_profundidade']
        if di > 0:
            for target, op in ((comp, CUT), (_new_component(root, 'trava-indicador'), NEW)):
                pl = _offset_plane(target, target.xZConstructionPlane, f'{top - dp:.4f} mm', (0, 1, 0))
                sk, pr = _circle_sketch(design, target, pl, (f'{si:.4f} mm', f'{top - dp:.4f} mm', f'{zi:.4f} mm'), f'{di} mm', 'indicador')
                ext = _extrude_dir(target, pr, sk, f'{dp + 1:.4f} mm' if op == CUT else f'{dp:.4f} mm', (0, 1, 0), op, body if op == CUT else None)
                if op == NEW:
                    ext.bodies.item(0).name = 'trava-indicador'
        # outer face down; not the dot's rim (the disc fills it flush)
        chanfros['tampa'] = _chanfro_mesa(comp, body, [(1, top)], v['trava_chanfro_mesa'],
                                          skip=lambda m: math.hypot(m[0] - si, m[2] - zi) < di / 2 + 0.2)
    if 'cursor' in partes:
        # one side profile (tongue, stem, dovetail stub) extruded the tongue's width (out to wo if wider),
        # then the stem and the stub thinned to trava_haste (trava_pescoco_largura above the step) less
        # trava_folga_haste a side. Printed on its rear end (z = z0): the
        # stem and the tongue start on the bed, the layers run along the stem, the stub's front flank is a
        # roof, and its rear flank comes down at 45 deg to the bed, where the rest of its rear end lies flat
        comp = _new_component(root, nome('cursor'))
        e, fh = v['trava_entrada'], g['fh']
        d0, d1, df = -v['trava_quilha_fundo'], -v['trava_lingueta_topo'], -v['trava_lingueta_fundo']
        kr = g['kr']
        rear = [(tz[0] - kr, gap + th), (tz[0] - kr, gap + kr), (tz[0], gap)]    # flat on the bed, then the 45 deg flank
        # the neck's rear top corner, under the cap's rear lip, comes down at 45 deg too, from the stub's foot to
        # the bed (a /\ over the bed): the lip touches only the flank and the cap rests on the stub's top alone,
        # so a print variation no longer pinches the lip between the neck and the flank
        pc = min(v['trava_pescoco_chanfro'], tz[0] - hz[0])
        # with teeth the keel is only under them (the narrow parts end at df, clear of the legs' tips as they bend
        # in by them), each one's rear end at 45 deg, as it prints on the slider's rear end
        bottom = [(z0, d0), (z0 + lk, d0)]
        if g['dentes']:
            bottom = []
            for i, (ta, tb) in enumerate(g['dentes']):
                bottom += ([(ta, d0)] if i == 0 else [(ta, df), (ta + df - d0, d0)]) + [(tb, d0), (tb, df)]
            bottom[-1] = (z0 + lk, d0)
        # the front flank: one slope from the base to the top, or (trava_toco_frente_reta) 45 deg from the foot until it
        # flares fl and then straight up to the top, as the rear one
        front = [(tz[1], gap)] + ([(tz[1] + fl, gap + fl)] if v.get('trava_toco_frente_reta', 0) else []) + [(tz[1] + fl, gap + th)]
        side = bottom + [(z0 + lk, d1), (hz[1], d1), (hz[1], gap)] + front + rear + [
                (hz[0] + pc, gap), (hz[0], gap - pc)]
        side = [p for i, p in enumerate(side) if math.dist(p, side[i - 1]) > 1e-6]      # stub as long as the stem
        wo, dg = g['wo'], g['dg']
        wl, wr = g['lingueta']                  # the tongue's sides (-w, w unless trava_lingueta_desloc)
        wx = max(wr, wo)
        pl = _offset_plane(comp, comp.yZConstructionPlane, f'{wl:.4f} mm', (1, 0, 0))
        sk, pr = _poly_sketch(design, comp, pl, [(f'{wl:.4f} mm', f'{d:.4f} mm', f'{z:.4f} mm') for z, d in side], 'perfil da trava')
        body = _extrude_dir(comp, pr, sk, f'{wx - wl:.4f} mm', (1, 0, 0), NEW).bodies.item(0)
        body.name = nome('cursor')
        zt = max(hz[1], tz[1] + fl) + 1
        _box(design, comp, body, (wl - 1, hs[0] + fh), (d1, gap), (hz[0] - 1, hz[1] + 1), CUT, 'haste')
        if wo > wr:
            # below the step only the tongue's width: the clip's base is whole there over the outer leg's root
            _box(design, comp, body, (wr, wx + 1), (d0 - 1, dg), (z0 - 1, zt), CUT, 'degrau do pescoço')
        if fh > 0:
            for sa, da, db in (((hs[1], d1, dg), (wo, dg, gap + th + 1)) if wo > hs[1] else ((hs[1], d1, gap + th + 1),)):
                _box(design, comp, body, (sa - fh, wx + 1), (da, db), (z0 - 1, zt), CUT, 'folga da haste')
        elif wr > max(hs[1], wo) + 1e-6:
            # the tongue out past the neck (trava_lingueta_desloc): the neck and the stub keep their own +s face
            _box(design, comp, body, (max(hs[1], wo), wx + 1), (d1, gap + th + 1), (z0 - 1, zt), CUT, 'lingueta para fora')
        # the stub: trava_toco_largura from the outer side (v6: the neck's, it comes up through the slots)
        if tl < wo - wl:
            _box(design, comp, body, (wl - 1, wo - tl + fh), (gap - 0.01, gap + th + 1), (z0 - 1, zt), CUT, 'toco')
        elif tl > wo - wl:
            stub = [(tz[1], gap), (tz[1] + fl, gap + th)] + rear
            pl = _offset_plane(comp, comp.yZConstructionPlane, f'{wo - tl:.4f} mm', (1, 0, 0))
            sk, pr = _poly_sketch(design, comp, pl, [(f'{wo - tl:.4f} mm', f'{d:.4f} mm', f'{z:.4f} mm') for z, d in stub], 'toco')
            _extrude_dir(comp, pr, sk, f'{tl - wo:.4f} mm', (1, 0, 0), JOIN, body)
        # keel: below the tongue's straight part the sides close in at trava_quilha_angulo from the vertical
        # (clear of the legs' tips) down to the slot's floor, so the slider rests on the frame (45 deg on the
        # Trident; steeper on the V0, whose legs' tips are closer together)
        if d0 < df:
            pl = _offset_plane(comp, comp.xYConstructionPlane, f'{z0 - 1:.4f} mm', (0, 0, 1))
            kt = math.tan(math.radians(v['trava_quilha_angulo']))
            for sg, se in ((1, wr), (-1, wl)):
                q = [(se, df), (se + sg, df), (se + sg, d0 - 1), (se - sg * (df - d0 + 1) * kt, d0 - 1)]
                sk, pr = _poly_sketch(design, comp, pl, [(f'{a:.4f} mm', f'{b:.4f} mm', f'{z0 - 1:.4f} mm') for a, b in q], 'quilha')
                _extrude_dir(comp, pr, sk, f'{lk + 2:.4f} mm', (0, 0, 1), CUT, body)
        pl = _offset_plane(comp, comp.xZConstructionPlane, f'{d0 - 0.5:.4f} mm', (0, 1, 0))
        if g['dentes']:
            # teeth: between them the tongue is trava_dente_degrau narrower a side, up to its top (the neck stays),
            # with 45 deg ramps at each tooth's ends: they lead it behind the barb, and the rear ones print
            r = v['trava_dente_degrau']
            edge = [(w - r, z0 - 1)]
            for ta, tb in g['dentes']:
                edge += [(w - r, ta), (w, ta + r), (w, tb - r), (w - r, tb)]
            edge += [(w - r, z0 + lk + 1), (w + 1, z0 + lk + 1), (w + 1, z0 - 1)]
            for sg in (1, -1):
                sk, pr = _poly_sketch(design, comp, pl, [(f'{sg * a:.4f} mm', f'{d0 - 0.5:.4f} mm', f'{b:.4f} mm') for a, b in edge], 'dentes')
                _extrude_dir(comp, pr, sk, f'{d1 - d0 + 0.5:.4f} mm', (0, 1, 0), CUT, body)
        else:
            # pointed nose: from trava_entrada_comprimento before the leading end the tongue narrows by
            # trava_entrada a side, so it finds the gap between the legs by itself
            lt, ze = v['trava_entrada_comprimento'], z0 + lk
            for sg, se in ((1, wr), (-1, wl)):
                tri = [(se - sg * e, ze), (se + sg, ze), (se + sg, ze - lt * (e + 1) / e)]
                sk, pr = _poly_sketch(design, comp, pl, [(f'{a:.4f} mm', f'{d0 - 0.5:.4f} mm', f'{b:.4f} mm') for a, b in tri], 'bico')
                _extrude_dir(comp, pr, sk, f'{d1 - d0 + 1:.4f} mm', (0, 1, 0), CUT, body)
        if marca:
            # grooves in the stub's -s face (inside the cap's socket in use), 1 wide, 0.6 deep along d (a third
            # of a narrower stub: the V0's is 1.5)
            sf, gd = wo - tl + fh, min(0.6, (tl - 2 * fh) / 3)
            for i in range(marca):
                zm_ = zc + (i - (marca - 1) / 2) * 2.0
                _box(design, comp, body, (sf - 1, sf + gd), (gap, gap + th + 1), (zm_ - 0.5, zm_ + 0.5), CUT, 'marca')
        # on its rear end; the stub's flat base (and the neck's top under the cap's lip, without
        # trava_pescoco_chanfro) only trava_chanfro_encaixe
        chanfros['cursor'] = _chanfro_encaixe(comp, body, [(2, z0)], v['trava_chanfro_mesa'], lambda m: m[1] > gap - 0.5,
                                              v['trava_chanfro_encaixe'])
        # a one-layer tab on the bed off the stub's flat base, out past its top (the user's "auto brim"), so
        # that small base holds on the bed; snapped off before assembly. The stub's outer bed edge first gets
        # a deeper 45 deg recess, so the break, at the tab's top, stays trava_orelha_recuo inside the face the
        # cap's socket sits on; the tab keeps clear of the side chamfers (the stub comes up through the slots)
        ol, oh = v['trava_orelha_comprimento'], v['trava_orelha_altura']
        if ol > 0:
            r, dt = oh + v['trava_orelha_recuo'], gap + th
            tri = [(z0 - 1, dt - r - 1), (z0 - 1, dt + 1), (z0 + r + 1, dt + 1)]
            pl = _offset_plane(comp, comp.yZConstructionPlane, f'{wl - 1:.4f} mm', (1, 0, 0))
            sk, pr = _poly_sketch(design, comp, pl, [(f'{wl - 1:.4f} mm', f'{d:.4f} mm', f'{z:.4f} mm') for z, d in tri], 'recuo da orelha')
            _extrude_dir(comp, pr, sk, f'{wx - wl + 2:.4f} mm', (1, 0, 0), CUT, body)
            ins = v['trava_chanfro_encaixe'] + 0.1
            _box(design, comp, body, (wo - tl + fh + ins, wo - fh - ins), (gap + kr + 0.05, dt + ol), (z0, z0 + oh), JOIN, 'orelha')
    if 'capa' in partes:
        comp = _new_component(root, nome('capa'))
        (c0, c1), (s0, s1) = g['cap_z'], g['cap_s']
        rim, crest = gap + v['trava_capa_aba'], top + v['trava_capa_crista']
        ch, cw, cc = v['trava_capa_chanfro'], v['trava_capa_crista_largura'] / 2, v['trava_capa_concavo']
        # the crest sits over the stem (zc)
        n = max(4, round(cc / 0.25))
        rise = [(zc - cw - cc * (1 - i / n), rim + (crest - rim) * (i / n) ** 2) for i in range(n + 1)]
        side = ([(c0, gap), (c0, rim - ch), (c0 + ch, rim)] + rise + [(2 * zc - z, d) for z, d in reversed(rise)] +
                [(c1 - ch, rim), (c1, rim - ch), (c1, gap)])
        pl = _offset_plane(comp, comp.yZConstructionPlane, f'{s0:.4f} mm', (1, 0, 0))
        sk, pr = _poly_sketch(design, comp, pl, [(f'{s0:.4f} mm', f'{d:.4f} mm', f'{z:.4f} mm') for z, d in side], 'perfil da capa')
        body = _extrude_dir(comp, pr, sk, f'{s1 - s0:.4f} mm', (1, 0, 0), NEW).bodies.item(0)
        body.name = nome('capa')
        # socket: the stub's dovetail (45 deg at the rear, flared at the front), its flanks trava_folga_toco
        # further out along the edge (the roof stays on the stub's top, the cap's one downward stop),
        # open on the outer edge (+s, nearer the stub), blind at the stub's -s face as drawn (a slider
        # with trava_folga_haste leaves that much there); the rear lip under the 45 deg flank ends square,
        # trava_capa_labio tall, short of the stub's foot, and so does the front one with trava_toco_frente_reta
        ft, kr, le = v['trava_folga_toco'], g['kr'], v['trava_capa_labio']
        front = ([(tz[1] + le + ft, gap - 1), (tz[1] + le + ft, gap + le), (tz[1] + fl + ft, gap + fl)] if v.get('trava_toco_frente_reta', 0)
                 else [(tz[1] + ft, gap - 1), (tz[1] + ft, gap)])
        sock = [(tz[0] - le - ft, gap - 1)] + front + [(tz[1] + fl + ft, gap + th),
                (tz[0] - kr - ft, gap + th), (tz[0] - kr - ft, gap + kr), (tz[0] - le - ft, gap + le)]
        sb = g['wo'] - tl
        pl = _offset_plane(comp, comp.yZConstructionPlane, f'{sb:.4f} mm', (1, 0, 0))
        sk, pr = _poly_sketch(design, comp, pl, [(f'{sb:.4f} mm', f'{d:.4f} mm', f'{z:.4f} mm') for z, d in sock], 'encaixe')
        _extrude_dir(comp, pr, sk, f'{s1 + 1 - sb:.4f} mm', (1, 0, 0), CUT, body)
        # corners chamfered at 45 deg, seen from above
        k = v['trava_capa_canto']
        pl = _offset_plane(comp, comp.xZConstructionPlane, f'{gap - 1:.4f} mm', (0, 1, 0))
        for se, ss in ((s0, -1), (s1, 1)):
            for ze, sz in ((c0, -1), (c1, 1)):
                tri = [(se - ss * (k + 1), ze + sz), (se + ss, ze - sz * (k + 1)), (se + ss, ze + sz)]
                sk, pr = _poly_sketch(design, comp, pl, [(f'{a:.4f} mm', f'{gap - 1:.4f} mm', f'{b:.4f} mm') for a, b in tri], 'canto')
                _extrude_dir(comp, pr, sk, f'{crest - gap + 2:.4f} mm', (0, 1, 0), CUT, body)
        # grooves across the underside near the rear end, 1 wide, 0.6 deep: trava_capa_sulcos on the standard
        # cap, a variant's TRAVA_MARCAS in their place (TRAVA_MARCAS_CAPA, where it has the variant, for the cap alone)
        for i in range((getattr(config, 'TRAVA_MARCAS_CAPA', {}).get(variante, marca) if variante else 0) or round(v['trava_capa_sulcos'])):
            zm_ = c0 + 3 + 2.0 * i
            _box(design, comp, body, (s0 - 1, s1 + 1), (gap - 1, gap + 0.6), (zm_ - 0.5, zm_ + 0.5), CUT, 'sulco')
        # on its inner end (-s), away from the socket's open end
        chanfros['capa'] = _chanfro_mesa(comp, body, [(0, s0)], v['trava_chanfro_mesa'])
    alto = f' ({g["wo"] - hs[0] - 2 * g["fh"]:.2f} acima de {g["dg"]:.1f})' if g['wo'] > w else ''
    print(f'trava_deslizante {"+".join(partes)}{f" ({variante}, marca {marca})" if variante else ""}: lingueta {2 * w:.2f} no vão de {2 * inner:.2f}, '
          f'pescoço {hs[1] - hs[0] - 2 * g["fh"]:.2f} nos rasgos de {hs[1] - hs[0]:.2f}{alto}; janela z {g["win"][0]:.1f}–'
          f'{g["win"][1]:.1f}, farpa z {g["farpa"][0]:.1f}–{g["farpa"][1]:.1f}, rasgo z {g["path"][0]:.1f}–{g["path"][1]:.1f}, '
          f'círculo z {g["ind"][1]:.1f}, '
          f'curso {g["c"]:.1f}; capa z {g["cap_z"][0]:.1f}–{g["cap_z"][1]:.1f} ({g["cap_z"][1] - g["cap_z"][0]:.1f}) × s '
          f'{g["cap_s"][0]:.1f}–{g["cap_s"][1]:.1f}; chanfro da mesa (arestas feitas, falhas) {chanfros}; {time.time() - t:.1f} s')


def trava_sem_orelha(body, v=None):
    """Temporary copy of a lock slider without its bed tab (snapped off before assembly), for the checks:
    everything of it past the stub's top."""
    v = v or _CTX['vals']
    tbm = adsk.fusion.TemporaryBRepManager.get()
    c = tbm.copy(body)
    ol = v['trava_orelha_comprimento']
    if ol > 0:
        g = _trava_geo(v)
        dt, z0, oh = g['gap'] + v['trava_toco_altura'], g['z0'], v['trava_orelha_altura']
        zb = (z0 - 1, z0 + oh + v['trava_orelha_recuo'] / 2)      # up to where the recess keeps the stub inside dt
        box = tbm.createBox(adsk.core.OrientedBoundingBox3D.create(
            P3(0, (dt + (ol + 1) / 2) / 10, (zb[0] + zb[1]) / 20), V3(1, 0, 0), V3(0, 1, 0), 4.0, (ol + 1) / 10, (zb[1] - zb[0]) / 10))
        tbm.booleanOperation(c, box, adsk.fusion.BooleanTypes.DifferenceBooleanType)
    return c


def trava_conferir(qual='curso', passo=1.0, variante=None, fixas=('trava-clip', 'trava-tampa')):
    """Checks the lock coupon with temporary copies; prints the largest overlap (mm³, 0 = clear) and where.

    curso    slider and cap along the travel, against clip and cover, and cap against slider
    entrada  the slider going in from below at the open position, against clip and cover
    capa     the cap sliding onto the stub from the inner side, against slider and cover
    variante: that variant's slider and cap (config.TRAVA_VARIANTES; the standard one of a part it lacks) with
    the standard clip and cover.
    fixas: the pieces the slider and cap run in, in place of clip and cover (('peca-unica-trava',) for the
    one-piece coupon: its body of that name, not the support).
    """
    t = time.time()
    design = _design(_require_open())
    v = _vals_with(config.TRAVA_VARIANTES[variante]) if variante else _CTX['vals']
    g = _trava_geo(v)
    tbm = adsk.fusion.TemporaryBRepManager.get()
    suf = f'-{variante}' if variante else ''
    # a variant of only the slider uses the standard cap, and one of only the cap the standard slider
    nome = lambda p: f'trava-{p}{suf}' if design.allComponents.itemByName(f'trava-{p}{suf}') else f'trava-{p}'   # noqa: E731
    corpo = lambda n: design.allComponents.itemByName(n).bRepBodies.itemByName(n) or design.allComponents.itemByName(n).bRepBodies.item(0)   # noqa: E731
    pecas = [(n.replace('trava-', ''), corpo(n)) for n in fixas]
    cursor, capa = corpo(nome('cursor')), corpo(nome('capa'))
    cursor = trava_sem_orelha(cursor, v)

    def moved(b, ds=0.0, dd=0.0, dz=0.0):
        c = tbm.copy(b)
        mat = adsk.core.Matrix3D.create()
        mat.translation = V3(ds / 10, dd / 10, dz / 10)
        tbm.transform(c, mat)
        return c

    def overlap(a, b):
        a = tbm.copy(a)
        if not tbm.booleanOperation(a, b, adsk.fusion.BooleanTypes.IntersectionBooleanType):
            return 0.0
        return a.volume * 1000 if a.faces.count else 0.0

    steps = lambda end: [round(i * passo, 3) for i in range(int(end / passo + 1e-6) + 1)] + ([end] if end % passo else [])  # noqa: E731
    worst = {}

    def note(key, pos, vol):
        if vol > worst.get(key, (None, -1))[1]:
            worst[key] = (pos, vol)
    # the cap only ever touches the outermost piece (the cover, or the one piece)
    externa = pecas[-1]
    if qual == 'curso':
        for dz in steps(g['c']):
            cur, cap = moved(cursor, dz=dz), moved(capa, dz=dz)
            for n, b in pecas:
                note(f'cursor × {n}', dz, overlap(cur, b))
            note(f'capa × {externa[0]}', dz, overlap(cap, externa[1]))
            note('capa × cursor', dz, overlap(cap, cur))
    elif qual == 'entrada':
        for dd in steps(g['gap'] + v['trava_toco_altura'] + 1):
            cur = moved(cursor, dd=-dd)
            for n, b in pecas:
                note(f'cursor × {n}', dd, overlap(cur, b))
    elif qual == 'capa':
        for ds in steps(g['cap_s'][1] - (g['wo'] - g['tl']) + 0.5):
            cap = moved(capa, ds=-ds)
            note('capa × cursor', ds, overlap(cap, cursor))
            note(f'capa × {externa[0]}', ds, overlap(cap, externa[1]))
    print(f'trava_conferir {qual}{f" ({variante})" if variante else ""} (passo {passo}): {time.time() - t:.1f} s')
    for key, (pos, vol) in worst.items():
        print(f'    {key}: {vol:.4f} mm³ (pior em {pos})')
    return worst


def _peca_unica_trechos(v):
    """Along the one-piece lock coupon (mm from its near end): the window without fin, the slit under the
    legs (from the post to the solid fin), the barbs, the stretches thinned from the outside (peca_unica_perna),
    the recesses for the teeth (trava_dentes; none for one tongue), and where the solid fin starts again."""
    g = _trava_geo(v)
    if g['dentes']:
        # teeth: the post right before the first recess (no window: the slider goes in from below through the
        # recesses, its teeth in them and its narrow parts by the barbs); each recess the open tooth, ramps
        # included, trava_dente_folga longer at each end, and the first one is where the legs bend by the post;
        # each barb the locked tooth's full width as much longer, so recesses and barbs alternate
        m, r, a = v['trava_dente_folga'], v['trava_dente_degrau'], v['trava_dente']
        rebaixos = [(t0 - m, t1 + m) for t0, t1 in g['dentes']]
        farpas = [(t0 + g['c'] + r - m, t0 + g['c'] + r + a + m) for t0, _ in g['dentes']]
        fenda0 = rebaixos[0][0]
        win = (fenda0 - v['peca_unica_pilar'],) * 2
        if r < v['peca_unica_farpa'] + 0.1:
            raise ValueError(f'rebaixo de {r} raso demais para a farpa de {v["peca_unica_farpa"]}: a perna bate nos dentes ao entrar')
        if v['fin_leg'] - r < 0.4 - 1e-6:
            raise ValueError(f'perna de {v["fin_leg"] - r:.2f} nos rebaixos: menos que 0,4')
        finas = []
    else:
        win = g['win']
        fenda0 = win[1] + v['peca_unica_pilar']
        # the barb only under the locked tongue's full width (its nose narrows trava_entrada_comprimento), at its
        # far end, peca_unica_farpa_comprimento long but at least peca_unica_dobra from the post (0: from there),
        # then peca_unica_dobra_fim to the solid fin
        end = g['z0'] + g['c'] + g['lk'] - v['trava_entrada_comprimento']
        start = fenda0 + v['peca_unica_dobra']
        if v['peca_unica_farpa_comprimento'] > 0:
            start = max(start, end - v['peca_unica_farpa_comprimento'])
        farpas, rebaixos = [(start, end)], []
        finas = [(fenda0, start)]
    if min(b - a_ for a_, b in farpas) < 1.0:
        raise ValueError(f'farpa da peça única curta demais: z {farpas}')
    fenda = (fenda0, farpas[-1][1] + v['peca_unica_dobra_fim'])
    finas.append((farpas[-1][1], fenda[1]))
    if v['peca_unica_comprimento'] - fenda[1] < 3.0:
        raise ValueError(f'aleta maciça curta demais depois das pernas: z {fenda[1]:.1f} a {v["peca_unica_comprimento"]:.1f}')
    return dict(win=win, fenda=fenda, farpas=farpas, finas=finas, rebaixos=rebaixos)


def peca_unica_trava(parte=None, variante=None):
    """Test coupon of the one piece (clip and cover together, perfis.PECA_UNICA; the user's idea, 2026-10-31)
    with the lock, trava_comprimento long, in the lock coupon's frame: the slider, cap and disc are the
    coupon's (trava_deslizante). Printed lying, the outer face on the bed. Component peca-unica-trava, two
    bodies (parte 'peca' or 'suporte' builds just one; one call each keeps a call short):

    peca-unica-trava  the doors' solid fin, no barb, except over the lock: the window without fin where the
                      tongue sits open, then the clip's two legs (gap = the tongue), the barb only under the
                      locked tongue's full width. Lying, a leg fixed along its root would bend across the
                      layers going in, and crack there: each leg is a beam along the edge instead, cut off the
                      piece by a slit (peca_unica_fenda, from a layer change) and held only at its ends, a post
                      by the window (peca_unica_pilar) and the solid fin; it bends inside the layers. Its
                      underside prints as a bridge over the slit. Locked, the tongue keeps the legs from bending
                      in. The neck's slot through the whole piece and the dot on the outer face, as the cover's
    suporte           the user's support for the base under the acrylic, snapped off after printing: a wall
                      standing on the bed suporte_folga in front of the cover's inner edge and past both ends,
                      up to the slot's ceiling, and a one-layer lamina from its top to the base's edge and ends,
                      so the ceiling's first layer bridges from the acrylic stop to the walls

    variante: a name in config.PECA_UNICA_VARIANTES (v2: the barb deeper, the legs longer and thinner where they
    bend; v3: the barb under the whole tongue, a longer travel; v4: a tongue of teeth, trava_dentes, that sit in
    recesses of the legs open and on as many barbs locked) builds component peca-unica-trava-<variante>, with
    config.PECA_UNICA_MARCAS grooves across the outer face near the far end; none, the v1 coupon (the
    parameters' defaults)
    """
    t = time.time()
    design = _design(_require_open())
    root = design.rootComponent
    changes = config.PECA_UNICA_VARIANTES[variante] if variante else {}
    v = _vals_with(changes) if variante else _CTX['vals']
    nome = f'peca-unica-trava-{variante}' if variante else 'peca-unica-trava'
    g = _trava_geo(v)
    tr = _peca_unica_trechos(v)
    L, so, top, T = v['peca_unica_comprimento'], g['so'], g['top'], g['T']
    partes = [parte] if parte else ['peca', 'suporte']
    out = {}
    if 'peca' in partes:
        _delete_component(root, nome)
        comp = _new_component(root, nome)
        sk, pr = _poly_sketch(design, comp, comp.xYConstructionPlane, [(s, d, '0 mm') for s, d in perfis.PECA_UNICA], 'perfil peca-unica')
        body = _extrude_dir(comp, pr, sk, f'{L} mm', (0, 0, 1), NEW).bodies.item(0)
        body.name = nome
        # the legs' barb peca_unica_farpa past the opening: the clip's leg with that fin_barb (its face's height
        # follows, from the same start)
        lv = _vals_with({**changes, 'fin_barb': f'{v["peca_unica_farpa"] + v["fin_inset"]:.4f} mm'})
        gancho = v.get('peca_unica_gancho', 0.0)
        if gancho > 0:
            # one thick leg on the acrylic's side (-s) and no other (the user's v5): fixed to the base its whole
            # length, from the tongue's inner face (the tongue moved out, trava_lingueta_desloc, against the outer
            # lip) to peca_unica_gancho_folga short of the opening, with a hook peca_unica_gancho past it all along
            # the piece, its faces at 45 deg (they print). It does not bend: open, the slider floats aside in its
            # slot, so the piece goes in moved out (+s) and slides back to hook; locked, the tongue fills the gap
            # between the leg and the outer lip, so it cannot move out again. Nothing prints in the air.
            # peca_unica_gancho_aperto (v6, the wedge): the hook's faces go up so the top one passes that far above
            # the lip's corner; the tongue, out to the outer lip, pushes the piece in and the slope pulls it down
            gf, wl = v['peca_unica_gancho_folga'], g['lingueta'][0]
            sr, lip, tip = -(so - gf), v['slot_lip'], v['slot_depth'] - v['fin_tip_clearance']
            sb = gf + v.get('peca_unica_gancho_aperto', -gf)
            hk = [(wl, 0.0), (wl, -tip), (sr, -tip), (sr, -lip - 2 * (gancho + gf) - 0.5 + sb), (-(so + gancho), -lip - (gancho + gf) - 0.5 + sb),
                  (-(so + gancho), -lip - (gancho + gf) + sb), (sr, -lip + sb), (sr, 0.0)]
            _box(design, comp, body, (-so - 1, so + 1), (-v['slot_depth'] - 1, 0.0), (-1.0, L + 1), CUT, 'sem aleta')
            sk, pr = _poly_sketch(design, comp, comp.xYConstructionPlane, [(f'{a_:.4f} mm', f'{d:.4f} mm', '0 mm') for a_, d in hk], 'perna com gancho')
            _extrude_dir(comp, pr, sk, f'{L} mm', (0, 0, 1), JOIN, body)
            # the window: no leg where the open tongue sits, so the piece moves out past the floating slider
            _box(design, comp, body, (-so - gancho - 2, so + 1), (-v['slot_depth'] - 1, 0.0), g['win'], CUT, 'janela')
        else:
            # no solid fin from the window to the far end of the legs
            _box(design, comp, body, (-so - 1, so + 1), (-v['slot_depth'] - 1, 0.0), (tr['win'][0], tr['fenda'][1]), CUT, 'sem aleta')
            # the clip's legs after the window (a neck at 0 leaves repeated points: dropped)
            leg = [(perfis.evaluate(s, lv), perfis.evaluate(d, lv)) for s, d in perfis._leg_right()]
            if tr['rebaixos']:
                # teeth: the slider goes in from below by the barbs (its narrow parts) and its neck's end too, so the
                # leg's inner face goes straight down to the tip, which ends flat where the outer slope (the lead-in
                # into the slot) leaves 0.5 of wall: the clip's tip curls in under the tongue, in their way
                (sa, da), (sb, db), si_ = leg[3], leg[4], leg[6][0]
                dc = da + (sa - si_ - 0.5) / (sa - sb) * (db - da)
                leg = leg[:4] + [(si_ + 0.5, dc), (si_, dc)] + leg[6:]
            leg = [p for i, p in enumerate(leg) if math.dist(p, leg[i - 1]) > 1e-6]
            z0, z1 = tr['win'][1], tr['fenda'][1]
            for sg in (1, -1):
                pl = _offset_plane(comp, comp.xYConstructionPlane, f'{z0:.4f} mm', (0, 0, 1))
                sk, pr = _poly_sketch(design, comp, pl, [(f'{sg * s:.4f} mm', f'{d:.4f} mm', f'{z0:.4f} mm') for s, d in leg], 'perna da trava')
                _extrude_dir(comp, pr, sk, f'{z1 - z0:.4f} mm', (0, 0, 1), JOIN, body)
            # the barb only in its stretches (perfis.barb_cut elsewhere: straight legs at the slot's width)
            cut = [(perfis.evaluate(s, lv), perfis.evaluate(d, lv)) for s, d in perfis.barb_cut()]
            ends = [z0] + [z for f in tr['farpas'] for z in f] + [z1]
            um = v.get('peca_unica_um_lado', 0) > 0.5
            for za, zb, lados in [(a, b, (1, -1)) for a, b in zip(ends[::2], ends[1::2])] + ([(z0, z1, (-1,))] if um else []):
                pl = _offset_plane(comp, comp.xYConstructionPlane, f'{za:.4f} mm', (0, 0, 1))
                for sg in lados:
                    sk, pr = _poly_sketch(design, comp, pl, [(f'{sg * s:.4f} mm', f'{d:.4f} mm', f'{za:.4f} mm') for s, d in cut], 'sem farpa')
                    _extrude_dir(comp, pr, sk, f'{zb - za:.4f} mm', (0, 0, 1), CUT, body)
            # thinner where they bend, from the outside (the tongue's face stays); the post keeps the clip's leg
            if v['peca_unica_perna'] < v['fin_leg'] - 1e-6:
                s0 = g['inner'] + v['peca_unica_perna']
                for za, zb in tr['finas']:
                    for sg in (1, -1):
                        _box(design, comp, body, tuple(sorted((sg * s0, sg * (so + v['peca_unica_farpa'] + 1)))),
                             (-v['slot_depth'] - 1, -0.5), (za, zb), CUT, 'perna fina')
            # the teeth's recesses, from the inside through the legs' whole height (the open teeth go in through them)
            si = g['inner'] + v.get('trava_dente_degrau', 0.0)
            for za, zb in tr['rebaixos']:
                _box(design, comp, body, (-si, si), (-v['slot_depth'] - 1, -0.5), (za, zb), CUT, 'rebaixo')
            # the slit: the legs held only by the post and the solid fin. peca_unica_um_lado: only the +s leg; the -s one
            # stays a wall fixed to the piece along its length, with no barb (above: cut its whole length)
            ft = v['peca_unica_fenda_topo']
            _box(design, comp, body, (-g['inner'] if um else -so - 1, so + 1), (ft - v['peca_unica_fenda'], ft), tr['fenda'], CUT, 'fenda')
        # the neck's slot, through the whole piece
        # (with the hook it is peca_unica_gancho + 2 peca_unica_gancho_folga wider toward -s, where the slider floats
        # as the piece moves out, and only through the base: below it the leg is right by it. peca_unica_rasgo_folga:
        # 1 that width all along, 0 none, 2 only where the neck is with the lock open, up to where the tongue's nose
        # has centred the slider on the leg, then a 45 deg ramp to the neck's width)
        modo = round(v.get('peca_unica_rasgo_folga', 1)) if gancho > 0 else 0
        fl_ = gancho + 2 * v['peca_unica_gancho_folga'] if modo else 0.0
        (h0, h1), (p0, p1) = (g['hs'][0], max(g['hs'][1], g['wo'])), g['path']
        if modo == 2:
            zw = g['hz'][1] + g['win'][1] - (g['z0'] + g['lk']) + v['trava_entrada_comprimento'] + 0.3
            edge = [(h0 - fl_, p0), (h1, p0), (h1, p1), (h0, p1), (h0, zw + fl_), (h0 - fl_, zw)]
            pl = _offset_plane(comp, comp.xZConstructionPlane, '0 mm', (0, 1, 0))
            sk, pr = _poly_sketch(design, comp, pl, [(f'{a_:.4f} mm', '0 mm', f'{b_:.4f} mm') for a_, b_ in edge], 'rasgo da haste')
            _extrude_dir(comp, pr, sk, f'{top + 1:.4f} mm', (0, 1, 0), CUT, body)
        else:
            _box(design, comp, body, (h0 - fl_, h1), (0.0 if gancho > 0 else -1.0, top + 1), (p0, p1), CUT, 'rasgo da haste')
        # the open/locked dot (the coupon's disc trava-indicador fills it)
        (si, zi), di, dp = g['ind'], v['trava_indicador_diametro'], v['trava_indicador_profundidade']
        if di > 0:
            pl = _offset_plane(comp, comp.xZConstructionPlane, f'{top - dp:.4f} mm', (0, 1, 0))
            sk, pr = _circle_sketch(design, comp, pl, (f'{si:.4f} mm', f'{top - dp:.4f} mm', f'{zi:.4f} mm'), f'{di} mm', 'indicador')
            _extrude_dir(comp, pr, sk, f'{dp + 1:.4f} mm', (0, 1, 0), CUT, body)
        # outer face down: its edges (the slot's too), not the dot's rim
        out['chanfro'] = _chanfro_mesa(comp, body, [(1, top)], v['trava_chanfro_mesa'],
                                       skip=lambda m: math.hypot(m[0] - si, m[2] - zi) < di / 2 + 0.2)
        # the variant's grooves, across the outer face's flat near the far end (past the locked cap)
        for i in range(config.PECA_UNICA_MARCAS.get(variante, 0) if variante else 0):
            za = L - 4 - 2.5 * i
            _box(design, comp, body, (-8.0, 5.0), (top - 0.6, top + 1), (za, za + 1), CUT, f'marca {i + 1}')
        out['peca'] = round(body.volume * 1000, 2)
    if 'suporte' in partes:
        comp = design.allComponents.itemByName(nome)
        for b in [b for b in comp.bRepBodies if b.name == 'suporte']:
            b.deleteMe()
        ceil, lam = T - v['peca_unica_vao'], v['suporte_lamina']           # the slot's ceiling (the base's top)
        gf, pw = v['suporte_folga'], v['suporte_parede']
        s_in = -(v['frame_size'] / 2 + v['cover_overlap'])                 # the cover's inner edge
        sw = (s_in - gf - pw, s_in - gf)
        zw = (-gf - pw, L + gf + pw)
        stop = -so + v['panel_edge_clearance']
        base0 = -(v['frame_size'] / 2 - v['base_inset'])
        boxes = [(sw, (ceil, top), zw, 'parede da frente'),
                 ((sw[0], stop), (ceil, top), (zw[0], -gf), 'parede da ponta'),
                 ((sw[0], stop), (ceil, top), (L + gf, zw[1]), 'parede da ponta'),
                 ((sw[0], base0), (ceil - lam, ceil), zw, 'lâmina da frente'),
                 ((sw[0], stop), (ceil - lam, ceil), (zw[0], 0.0), 'lâmina da ponta'),
                 ((sw[0], stop), (ceil - lam, ceil), (L, zw[1]), 'lâmina da ponta')]
        # made apart and added as a body: a join feature touching the piece (the laminas do) merges it into the
        # piece, participant bodies or not
        tbm = adsk.fusion.TemporaryBRepManager.get()
        sup = None
        for s, d, z, _ in boxes:
            box = tbm.createBox(adsk.core.OrientedBoundingBox3D.create(
                P3((s[0] + s[1]) / 20, (d[0] + d[1]) / 20, (z[0] + z[1]) / 20), V3(1, 0, 0), V3(0, 1, 0),
                (s[1] - s[0]) / 10, (d[1] - d[0]) / 10, (z[1] - z[0]) / 10))
            if sup is None:
                sup = box
            else:
                tbm.booleanOperation(sup, box, adsk.fusion.BooleanTypes.UnionBooleanType)
        b = comp.bRepBodies.add(sup)
        b.name = 'suporte'
        out['suporte'] = round(b.volume * 1000, 2)
    if v.get('peca_unica_gancho', 0.0) > 0:
        print(f'peca_unica_trava {"+".join(partes)} ({variante}): perna única com gancho de {v["peca_unica_gancho"]:.2f} na peça toda '
              f'(aperto na quina da aba {v.get("peca_unica_gancho_aperto", -v["peca_unica_gancho_folga"]):.2f}), '
              f'face de dentro em s {g["lingueta"][0]:.3f}, lingueta s {g["lingueta"][0]:.3f}–{g["lingueta"][1]:.3f}, pescoço s {g["hs"][0]:.3f}–{g["hs"][1]:.3f}; '
              f'janela z {g["win"][0]:.1f}–{g["win"][1]:.1f}, rasgo z {g["path"][0]:.1f}–{g["path"][1]:.1f}; {out}; {time.time() - t:.1f} s')
        return out
    print(f'peca_unica_trava {"+".join(partes)}{f" ({variante})" if variante else ""}: janela z {tr["win"][0]:.1f}–{tr["win"][1]:.1f}, fenda z {tr["fenda"][0]:.1f}–'
          f'{tr["fenda"][1]:.1f}, farpa z {", ".join(f"{a:.1f}–{b:.1f}" for a, b in tr["farpas"])}'
          f'{", rebaixos z " + ", ".join(f"{a:.1f}–{b:.1f}" for a, b in tr["rebaixos"]) if tr["rebaixos"] else ""}, rasgo z {g["path"][0]:.1f}–{g["path"][1]:.1f}; '
          f'{out}; {time.time() - t:.1f} s')
    return out


def peca_unica_exportar(pasta, variante=None):
    """The one-piece coupon as it prints, for the slicer: piece and support joined in one body, lying with the
    outer face at Z = 0 (X along the edge, Y = -s); plus a STEP of the component with the two bodies apart.
    variante: that variant's coupon (peca_unica_trava), files named after it."""
    t = time.time()
    design = _design(_require_open())
    v = _CTX['vals']
    top = _trava_geo(v)['top']
    os.makedirs(pasta, exist_ok=True)
    nome = f'peca-unica-trava-{variante}' if variante else 'peca-unica-trava'
    comp = design.allComponents.itemByName(nome)
    tbm = adsk.fusion.TemporaryBRepManager.get()
    one = tbm.copy(comp.bRepBodies.itemByName(nome))
    tbm.booleanOperation(one, tbm.copy(comp.bRepBodies.itemByName('suporte')), adsk.fusion.BooleanTypes.UnionBooleanType)
    mat = adsk.core.Matrix3D.create()
    mat.setWithCoordinateSystem(P3(0, 0, top / 10), V3(0, -1, 0), V3(0, 0, -1), V3(1, 0, 0))
    tbm.transform(one, mat)
    tmp = _new_component(design.rootComponent, 'peca-unica-exportar')
    try:
        b = tmp.bRepBodies.add(one)
        em = design.exportManager
        opts = em.createSTLExportOptions(b, os.path.join(pasta, f'{nome}-1x.stl'))
        opts.meshRefinement = adsk.fusion.MeshRefinementSettings.MeshRefinementHigh
        opts.isBinaryFormat = True
        opts.unitType = adsk.fusion.DistanceUnits.MillimeterDistanceUnits
        em.execute(opts)
        vol = b.volume * 1000
    finally:
        _delete_component(design.rootComponent, 'peca-unica-exportar')
    occ = next(o for o in design.rootComponent.occurrences if o.component == comp)
    em = design.exportManager
    em.execute(em.createSTEPExportOptions(os.path.join(pasta, f'{nome}.step'), occ.component))
    print(f'peca_unica_exportar: {pasta}, volume {vol:.2f} mm³, {time.time() - t:.1f} s')


def trava_pecas(nomes=None):
    """Cut the lock into production pieces (a machine whose map has trava_pecas, gerador/v0-trava), in each
    piece's lock frame from the map: on a clip, the coupon clip's window without legs, the neck's slots and
    the way in for the wide neck (the barb stays as on every clip); on a cover or a corner, the neck's slot
    and the dot. Each piece must come fresh from pecas() or cantos(): one already cut is refused."""
    t = time.time()
    design = _design(_require_open())
    v = _CTX['vals']
    specs = mapa.trava_pecas(v)
    planes = lambda comp: (comp.yZConstructionPlane, comp.xZConstructionPlane, comp.xYConstructionPlane)   # noqa: E731
    feitos = []
    for name in nomes or list(specs):
        sp = specs[name]
        comp = design.allComponents.itemByName(name)
        if comp is None:
            raise RuntimeError(f'{name}: falta a peça; rode pecas() ou cantos() antes')
        if comp.attributes.itemByName('panel-holder', 'trava'):
            raise RuntimeError(f'{name}: a trava já foi cortada; reconstrua a peça antes')
        body = comp.bRepBodies.item(0)
        vv = _vals_with(config.TRAVA_VARIANTES['topo']) if sp['topo'] else v     # cap and dot further out
        g = _trava_geo(vv)
        ol, ex, ey, ez = sp['quadro']
        P = lambda s, d, z: tuple(ol[i] + s * ex[i] + d * ey[i] + z * ez[i] for i in range(3))   # noqa: E731
        axis = lambda u: next(k for k in range(3) if abs(u[k]) > 0.5)                            # noqa: E731

        def box(s, d, z, nm):
            pts = [P(a, b, c) for a in s for b in d for c in z]
            x, y, zz = [(min(p[i] for p in pts), max(p[i] for p in pts)) for i in range(3)]
            _box(design, comp, body, x, y, zz, CUT, nm)

        def prism(s, dz, nm):
            """Polygon in (d, z) at s[0], cut through to s[1]."""
            i = axis(ex)
            pl = _offset_plane(comp, planes(comp)[i], f'{P(s[0], 0, 0)[i]:.4f} mm', tuple(float(k == i) for k in range(3)))
            sk, pr = _poly_sketch(design, comp, pl, [tuple(f'{c:.4f} mm' for c in P(s[0], d, z)) for d, z in dz], nm)
            _extrude_dir(comp, pr, sk, f'{s[1] - s[0]:.4f} mm', ex, CUT, body)

        def rampa(s, d, z, d_sup, nm):
            """As _box_rampa: the near end (z[0]) leans back toward z = 0 at 45 deg above d_sup."""
            near = lambda dd: z[0] - max(0.0, dd - d_sup)   # noqa: E731
            prism(s, [(d[0], z[1]), (d[1], z[1]), (d[1], near(d[1]))] + ([(d_sup, z[0])] if d[0] < d_sup < d[1] else []) +
                  [(d[0], near(d[0]))], nm)

        T, top, hs, inner, wo = g['T'], g['top'], g['hs'], g['inner'], g['wo']
        dsup, rec, fs = v['panel_frame_spacing'], v['cover_recess'], v['frame_size']
        dt = T + v['dovetail_height'] + 1
        if sp['parte'] == 'clip':
            win, deep, s0 = g['win'], v['slot_depth'] + 1, g['so'] + v['fin_barb'] + 1
            prism((-s0, s0), [(0.0, win[0]), (0.0, win[1]), (-deep, win[1]), (-deep, win[0] - deep)], 'sem pernas')
            rampa((hs[0], inner), (0.0, dt), g['path'], dsup, 'rasgo da haste')
            # the dovetail's outer flank over the slot, off to the wall (as on the coupon); on clip-parede, whose
            # dovetail is top_overhang further out, its inner flank too, or a sliver of it would float over the slot
            rampa((inner if sp['perfil'] != 'clip-parede' else -fs / 2, fs / 2), (T + rec, dt), g['path'], dsup, 'lasca do rabo')
            if wo > inner:
                if not g['win'][0] <= g['furo'][0] < g['furo'][1] <= g['win'][1]:
                    raise ValueError(f'a entrada do pescoço largo (z {g["furo"]}) sai da janela sem pernas (z {g["win"]})')
                rampa((inner, wo), (dsup, T + rec), g['path'], dsup, 'rasgo largo')
                box((inner, wo), (-1.0, dsup + 0.5), g['furo'], 'entrada do pescoço largo')
        else:
            box((hs[0], max(hs[1], wo)), (T - 0.1, top + 1), g['path'], 'rasgo da haste')
            (si, zi), di, dp = g['ind'], v['trava_indicador_diametro'], v['trava_indicador_profundidade']
            c3, j = P(si, top - dp, zi), axis(ey)
            pl = _offset_plane(comp, planes(comp)[j], f'{c3[j]:.4f} mm', tuple(float(k == j) for k in range(3)))
            sk, pr = _circle_sketch(design, comp, pl, tuple(f'{c:.4f} mm' for c in c3), f'{di} mm', 'indicador')
            _extrude_dir(comp, pr, sk, f'{dp + 1:.4f} mm', ey, CUT, body)
        comp.attributes.add('panel-holder', 'trava', '1')
        feitos.append(f'{name} ({body.volume * 1000:.0f} mm³)')
    print(f'trava_pecas: {feitos}, {time.time() - t:.1f} s')


def trava_espelho(nomes=('trava-cursor', 'trava-capa')):
    """Mirror images (z -> -z in the coupon's frame) of the slider and the cap, as '<name>-espelho', for the
    locks whose frame is left-handed (gerador/v0-trava: verticals sliding down where the piece's z runs up)."""
    t = time.time()
    design = _design(_require_open())
    root = design.rootComponent
    tbm = adsk.fusion.TemporaryBRepManager.get()
    feitos = []
    for name in nomes:
        src = design.allComponents.itemByName(name).bRepBodies.item(0)
        new = f'{name}-espelho'
        _delete_component(root, new)
        comp = _new_component(root, new)
        copy = comp.bRepBodies.add(tbm.copy(src))
        ents = adsk.core.ObjectCollection.create()
        ents.add(copy)
        comp.features.mirrorFeatures.add(comp.features.mirrorFeatures.createInput(ents, comp.xYConstructionPlane))
        copy.deleteMe()
        body = comp.bRepBodies.item(0)
        body.name = new
        bb = body.boundingBox
        feitos.append(f'{new}: {body.volume * 1000:.2f} mm³ (original {src.volume * 1000:.2f}), z {bb.minPoint.z * 10:.1f}–{bb.maxPoint.z * 10:.1f}')
    print(f'trava_espelho: {feitos}, {time.time() - t:.1f} s')


def _canto_etapa(design, name, step):
    root = design.rootComponent
    leg_a, leg_b = mapa.CANTOS[name]
    (cov_a, clip_a, off_a, start_a, scarf_a), (cov_b, clip_b, off_b, start_b, scarf_b) = leg_a[:5], leg_b[:5]
    # leg length: an optional 6th element of the leg, cover_corner by default
    Ja, Jb = (leg_a[5] if len(leg_a) > 5 else 'cover_corner'), (leg_b[5] if len(leg_b) > 5 else 'cover_corner')
    if step == 'pernas':
        _canto_etapa(design, name, 'pernaA')
        _canto_etapa(design, name, 'pernaB')
        return
    if step == 'clips':
        _canto_etapa(design, name, 'clipsA')
        _canto_etapa(design, name, 'clipsB')
        return
    ext = '2 mm'
    if step == 'pernaA':
        _delete_component(root, name)
        parent = _parent(design, 'pecas')
        mat = adsk.core.Matrix3D.create()
        if not _CTX['direto']:     # direct modeling: pieces at the origin (see _place)
            mat.translation = V3(list(mapa.CANTOS).index(name) * 12.0, -70.0, 0)
        comp = parent.occurrences.addNewComponent(mat).component
        comp.name = name
        yz, xz, xy = comp.yZConstructionPlane, comp.xZConstructionPlane, comp.xYConstructionPlane
        # legs: cover profiles (s measured from the outer line of each edge), each extended past the
        # corner and cut on the diagonal like a picture frame, so chamfers and wedges meet cleanly
        pl = _offset_plane(comp, yz, f'-{ext}', (1, 0, 0))
        sk, pr = _profile_on_plane(design, comp, pl, cov_a, lambda s, d: (f'-{ext}', f'frame_size / 2 - ( {s} )', d), 'perna A')
        body = _extrude_dir(comp, pr, sk, f'{Ja} + {ext}', (1, 0, 0), NEW).bodies.item(0)
        sk, pr = _poly_sketch(design, comp, xy, [('-4 mm', '-4 mm', '0 mm'), ('40 mm', '40 mm', '0 mm'),
                                                  ('-4 mm', '40 mm', '0 mm')], 'meia-esquadria A')
        _extrude_sym(comp, pr, '40 mm', CUT, body)
        return
    comp = design.allComponents.itemByName(name)
    yz, xz, xy = comp.yZConstructionPlane, comp.xZConstructionPlane, comp.xYConstructionPlane
    if step == 'pernaB':
        if comp.bRepBodies.count != 1:
            raise RuntimeError(f'{name}: pernaB espera só a perna A ({comp.bRepBodies.count} corpos); rode pernaA antes')
        body = comp.bRepBodies.item(0)
        pl = _offset_plane(comp, xz, f'-{ext}', (0, 1, 0))
        sk, pr = _profile_on_plane(design, comp, pl, cov_b, lambda s, d: (f'frame_size / 2 - ( {s} )', f'-{ext}', d), 'perna B')
        body_b = _extrude_dir(comp, pr, sk, f'{Jb} + {ext}', (0, 1, 0), NEW).bodies.item(0)
        sk, pr = _poly_sketch(design, comp, xy, [('-4 mm', '-4 mm', '0 mm'), ('40 mm', '-4 mm', '0 mm'),
                                                  ('40 mm', '40 mm', '0 mm')], 'meia-esquadria B')
        _extrude_sym(comp, pr, '40 mm', CUT, body_b)
        tools = adsk.core.ObjectCollection.create()
        tools.add(body_b)
        comp.features.combineFeatures.add(comp.features.combineFeatures.createInput(body, tools))
        body = comp.bRepBodies.item(0)
        body.name = name
        # a leg whose cover has no corner wedge (tampa-simples) ends flush with its outer line: trim
        # the other leg's wedge, which the miter would carry past it (into the top hat's wedge)
        # (only the corner quadrant beyond both outer lines holds that nose; a larger box would lie on the
        # wedge-less leg's outer face, and direct modeling fails on that coplanar contact)
        v = _param_values(design)
        if any(max(s for s, _ in perfis.polygon(cover, v)) <= v['frame_size'] / 2 + 1e-6 for cover in (cov_a, cov_b)):
            pts = [('-4 mm', '-4 mm'), ('0 mm', '-4 mm'), ('0 mm', '0 mm'), ('-4 mm', '0 mm')]
            sk, pr = _poly_sketch(design, comp, xy, [(x, y, '0 mm') for x, y in pts], 'apara cunha')
            _extrude_sym(comp, pr, '40 mm', CUT, body)
        return
    body = comp.bRepBodies.item(0)
    if step == 'clipsA':
        # space of each edge's clips, from where they start to past the joint
        pl = _offset_plane(comp, yz, start_a, (1, 0, 0))
        sk, pr = _profile_on_plane(design, comp, pl, clip_a,
                                   lambda s, d: (start_a, f'frame_size / 2 + {off_a} - ( {s} )', d), 'clips A')
        _extrude_dir(comp, pr, sk, f'{Ja} - {start_a} + 1 mm', (1, 0, 0), CUT, body)
    elif step == 'clipsB':
        pl = _offset_plane(comp, xz, start_b, (0, 1, 0))
        sk, pr = _profile_on_plane(design, comp, pl, clip_b,
                                   lambda s, d: (f'frame_size / 2 + {off_b} - ( {s} )', start_b, d), 'clips B')
        _extrude_dir(comp, pr, sk, f'{Jb} - {start_b} + 1 mm', (0, 1, 0), CUT, body)
    elif step == 'miolo':
        # canto_miolo > 0: before each edge's clips start (over the post) the corner was hollow between the
        # cover and the frame, open to the chamber through the post's channels and under the acrylic. Fill
        # it where the clip's body would be, without the fin and the base under the acrylic: from the
        # acrylic stop out to the cover's wall, from the frame face up into the cover, canto_miolo_folga
        # short of the clips. Only standard clips, and only where both legs' clips start past the stop
        # (the top's corners): a vertical leg's clips start clip_end_gap from the corner and fill the space.
        v = _param_values(design)
        if v.get('canto_miolo', 0.0) <= 0:
            return
        top = f'{T_EXPR} + cover_height - 1 mm'
        legs = (('A', clip_a, off_a, start_a, start_b), ('B', clip_b, off_b, start_b, start_a))
        for leg, clip, off, start, other in legs:
            if clip != 'clip-padrao':
                continue
            w0 = f'frame_size / 2 + {off} - {perfis.WALL_FIT}'
            w1 = f'frame_size / 2 + {off} - ( {perfis.STOP_STD} )'
            if min(_cm(start), _cm(other)) - _cm('canto_miolo_folga') <= _cm(w1):
                continue
            end = f'{start} - canto_miolo_folga'
            pts = [('0 mm', w0), (end, w0), (end, w1), ('0 mm', w1)]
            pts = [(u, w, '0 mm') if leg == 'A' else (w, u, '0 mm') for u, w in pts]
            sk, pr = _poly_sketch(design, comp, xy, pts, f'miolo {leg}')
            _extrude_dir(comp, pr, sk, top, (0, 0, 1), JOIN, body)
    elif step == 'juntas':
        # 45° scarf where a cover middle overlaps the leg end
        rec, top = f'{T_EXPR} + cover_recess', f'{T_EXPR} + cover_height + 2 mm'
        if scarf_a:
            pts = [(Ja, '0 mm', rec), (f'{Ja} + 1 mm', '0 mm', rec), (f'{Ja} + 1 mm', '0 mm', top),
                   (f'{Ja} - joint_scarf - 2 mm', '0 mm', top)]
            sk, pr = _poly_sketch(design, comp, xz, pts, 'junta A')
            _extrude_sym(comp, pr, '60 mm', CUT, body)
        if scarf_b:
            pts = [('0 mm', Jb, rec), ('0 mm', f'{Jb} + 1 mm', rec), ('0 mm', f'{Jb} + 1 mm', top),
                   ('0 mm', f'{Jb} - joint_scarf - 2 mm', top)]
            sk, pr = _poly_sketch(design, comp, yz, pts, 'junta B')
            _extrude_sym(comp, pr, '60 mm', CUT, body)
    elif step.startswith('pega'):
        leg = mapa.PEGA.get(name)
        _grip(design, comp, name, leg, step[5:] or None)
        if leg and step in ('pega', 'pega-labio'):
            # the lip must stay out of the clips' space: where the clip owns the outer wall (clip-u-fora)
            # the lip would reach into it; elsewhere this cut finds nothing
            _canto_etapa(design, name, f'clips{leg}')
    elif step.startswith('dobradica'):
        _hinge(design, comp, name, step[10:] or None)


def _hinge(design, comp, name, part=None):
    """Hinge knuckle on the hinge edge's leg of a mapa.DOBRADICA corner (perfis.NO_LATERAL / NO_PORTA).

    Side corner: knuckle from the corner over hinge_side_len, screw hole, head counterbore at the
    corner end; the side's wedge is cut away where the door's knuckle sits. Door corner: knuckle from
    hinge_side_len + hinge_gap over hinge_door_len (at the pin), its far end on a 45° gusset toward
    the cover, free hole for the screw; the door's wedge is cut away along the side's knuckle.
    u runs along the leg from the corner, w = frame_size / 2 - s goes inward from the outer line.
    """
    if name not in mapa.DOBRADICA:
        return
    parts = [part] if part else ['no', 'furo', 'cunha']
    _, leg, knuckle = mapa.DOBRADICA[name]
    xy, yz, xz = comp.xYConstructionPlane, comp.yZConstructionPlane, comp.xZConstructionPlane
    if leg == 'A':
        P = lambda u, w, d: (u, w, d)   # noqa: E731
        section, axis = yz, (1, 0, 0)
    else:
        P = lambda u, w, d: (w, u, d)   # noqa: E731
        section, axis = xz, (0, 1, 0)
    W = lambda s: f'frame_size / 2 - ( {s} )'   # noqa: E731
    body = lambda: comp.bRepBodies.itemByName(name)   # noqa: E731
    side = knuckle == 'no-lateral'
    pin_s, pin_d = perfis.PINO_LATERAL if side else perfis.PINO_PORTA
    start = '0 mm' if side else 'hinge_side_len + hinge_gap'
    door_end = 'hinge_side_len + hinge_gap + hinge_door_len'          # door knuckle's end, at the pin
    pts = [P('0 mm', W(s), d) for s, d in perfis.PROFILES[knuckle]]
    length = 'hinge_side_len' if side else 'hinge_door_len + wall_width + door_pin_s - frame_size / 2 + 1 mm'
    plane = section if side else None
    if not side and ('no' in parts or 'furo' in parts):
        plane = _offset_plane(comp, section, start, axis)
    if 'no' in parts and side:
        sk, pr = _poly_sketch(design, comp, plane, pts, 'nó da lateral')
        _extrude_dir(comp, pr, sk, length, axis, JOIN, body())
    if 'no' in parts and not side:
        sk, pr = _poly_sketch(design, comp, plane, pts, 'nó da porta')
        tool = _extrude_dir(comp, pr, sk, length, axis, NEW).bodies.item(0)
        # 45° gusset end: u_end = door_end + ( w - w_pin ), longer toward the cover
        w_pin = W('door_pin_s')
        wa, wb = f'{w_pin} - 5 mm', 'wall_width + 1 mm'
        ua, ub = f'{door_end} - 5 mm', f'{door_end} + wall_width + 1 mm - ( {w_pin} )'
        far = f'{door_end} + wall_width + door_pin_s + 10 mm'
        sk, pr = _poly_sketch(design, comp, xy, [P(ua, wa, '0 mm'), P(ub, wb, '0 mm'), P(far, wb, '0 mm'), P(far, wa, '0 mm')], 'reforço do nó')
        _extrude_sym(comp, pr, '40 mm', CUT, tool)
        tools = adsk.core.ObjectCollection.create()
        tools.add(_loose_body(comp, name))
        comp.features.combineFeatures.add(comp.features.combineFeatures.createInput(body(), tools))
    if 'furo' in parts:
        dia = 'hinge_hole_side' if side else 'hinge_hole_door'
        sk, pr = _circle_sketch(design, comp, plane, P(start, W(pin_s), pin_d), dia, 'furo do pino')
        _extrude_dir(comp, pr, sk, f'{length} + 1 mm', axis, CUT, body())
        if side:
            sk, pr = _circle_sketch(design, comp, plane, P(start, W(pin_s), pin_d), 'hinge_head_d', 'rebaixo da cabeça')
            _extrude_dir(comp, pr, sk, 'hinge_head_depth', axis, CUT, body())
    if 'cunha' in parts:
        # this panel's wedge goes where the other panel's knuckle is (beyond the outer line: only the
        # wedge): the door's knuckle, gusset included, from hinge_side_len on; the side's knuckle from
        # the corner to hinge_side_len
        if side:
            cut_from, cut_to = 'hinge_side_len', f'{door_end} + door_pin_s - frame_size / 2 + 1 mm'
        else:
            cut_from, cut_to = '0 mm', 'hinge_side_len + hinge_gap'
        sk, pr = _poly_sketch(design, comp, xy, [P(cut_from, '-3 mm', '0 mm'), P(cut_to, '-3 mm', '0 mm'),
                                                 P(cut_to, '0 mm', '0 mm'), P(cut_from, '0 mm', '0 mm')], 'recorte da cunha')
        _extrude_sym(comp, pr, '40 mm', CUT, body())


def _grip(design, comp, name, leg, part=None):
    """Finger grip on one leg (v11): near the corner the outer chamfer is filled up into a lip, and
    under the lip a pocket with a 45° roof is cut into the outer face, for a fingertip to pull with.

    Leg A: along x, outer line y = 0; leg B: along y, outer line x = 0. Below, u runs along the leg
    from the corner and w goes inward from the outer line (w = frame_size / 2 - s).
    """
    if leg is None:
        return
    xy, yz, xz = comp.xYConstructionPlane, comp.yZConstructionPlane, comp.xZConstructionPlane
    if leg == 'A':
        P = lambda u, w, d: (u, w, d)   # noqa: E731
        section, along, axis = yz, xz, (1, 0, 0)
    else:
        P = lambda u, w, d: (w, u, d)   # noqa: E731
        section, along, axis = xz, yz, (0, 1, 0)
    top = f'{T_EXPR} + cover_height'
    ch0 = f'{T_EXPR} + cover_height - cover_cut'       # outer chamfer starts here, on the outer line
    end = 'grip_from + grip_length'
    lip_end = f'{end} + grip_lip_margin'
    roof = f'{top} - grip_lip_chamfer'

    def tool(sec_pts, sec_len, side_pts, side_plane, label):
        # a prism of the cross-section along the leg, intersected with a prism of the side view
        sk, pr = _poly_sketch(design, comp, section, [P('0 mm', w, d) for w, d in sec_pts], f'{label} seção')
        a = _extrude_dir(comp, pr, sk, sec_len, axis, NEW).bodies.item(0)
        sk, pr = _poly_sketch(design, comp, side_plane, side_pts, f'{label} vista')
        b = _extrude_sym(comp, pr, '40 mm', NEW).bodies.item(0)
        tools = adsk.core.ObjectCollection.create()
        tools.add(b)
        inp = comp.features.combineFeatures.createInput(a, tools)
        inp.operation = adsk.fusion.FeatureOperations.IntersectFeatureOperation
        comp.features.combineFeatures.add(inp)
        return _loose_body(comp, name)

    def combine(tool_body, op):
        tools = adsk.core.ObjectCollection.create()
        tools.add(tool_body)
        inp = comp.features.combineFeatures.createInput(comp.bRepBodies.itemByName(name), tools)
        inp.operation = op
        comp.features.combineFeatures.add(inp)

    if part in (None, 'labio'):
        _grip_lip(tool, combine, P, along, ch0, roof, top, lip_end)
    if part in (None, 'rebaixo'):
        _grip_pocket(tool, combine, P, xy, roof, end)


def _grip_lip(tool, combine, P, along, ch0, roof, top, lip_end):
    # lip: the outer chamfer filled up to the top (small chamfer on the edge), from the corner, where
    # the other leg's chamfer bounds it, to just past the pocket, ending on a 45° slope
    lip = tool([('0 mm', f'{ch0} - 0.5 mm'), ('0 mm', roof), ('grip_lip_chamfer', top), ('cover_cut + 0.5 mm', top)],
               f'{lip_end} + cover_cut + 1 mm',
               [P('0 mm', '0 mm', f'{ch0} - 0.5 mm'), P('0 mm', '0 mm', ch0), P('cover_cut', '0 mm', top),
                P(lip_end, '0 mm', top), P(f'{lip_end} + cover_cut + 0.5 mm', '0 mm', f'{ch0} - 0.5 mm')],
               along, 'lábio')
    combine(lip, adsk.fusion.FeatureOperations.JoinFeatureOperation)


def _grip_pocket(tool, combine, P, xy, roof, end):
    # pocket: from the top of the wedge up to the 45° roof under the lip, ends at 45° along the leg
    pocket = tool([('-1 mm', 'wall_width'), ('grip_depth / 2', 'wall_width'), ('grip_depth', 'wall_width + grip_depth / 2'),
                   ('grip_depth', f'{roof} - grip_depth'), ('0 mm', roof), ('-1 mm', roof)],
                  f'{end} + 2 mm',
                  [P('grip_from - 1 mm', '-1 mm', '0 mm'), P(f'{end} + 1 mm', '-1 mm', '0 mm'),
                   P(f'{end} - grip_depth - 0.5 mm', 'grip_depth + 0.5 mm', '0 mm'),
                   P('grip_from + grip_depth + 0.5 mm', 'grip_depth + 0.5 mm', '0 mm')],
               xy, 'rebaixo')
    combine(pocket, CUT)


def montar(faces=None):
    """One component per face with occurrences of the straight pieces in place."""
    t = time.time()
    design = _design(_require_open())
    root = design.rootComponent
    um = design.unitsManager
    v = _param_values(design)
    L = {k: _cm(expr) * 10 for k, (_, expr) in mapa.PECAS.items()}
    missing = [k for k in list(mapa.PECAS) + list(mapa.CANTOS) + list(getattr(mapa, 'EXTRAS', ()))
               if design.allComponents.itemByName(k) is None]
    if missing:
        raise RuntimeError(f'faltam peças: {missing}; rode construir.pecas(), construir.cantos() (e as peças avulsas) antes')
    done = []
    for face in mapa.faces(v):
        if faces and face['nome'] not in faces:
            continue
        cname = f"face-{face['nome']}"
        _delete_component(root, cname)
        fcomp = _new_component(root, cname)
        focc = next(o for o in root.occurrences if o.component == fcomp)
        count = 0
        for name, o, a, n, tt, _edge in mapa.colocacoes(v, L, face):
            mat = adsk.core.Matrix3D.create()
            mat.setWithCoordinateSystem(P3(*[c / 10 for c in o]), V3(*a), V3(*n), V3(*tt))
            _place(focc, design.allComponents.itemByName(name), mat)
            count += 1
        # direct modeling sometimes leaves an occurrence composed with another place: check each one
        # against the map and set it again if it drifted
        drift = 0
        for occ, (name, o, a, n, tt, _edge) in zip(fcomp.occurrences, mapa.colocacoes(v, L, face)):
            got = occ.transform2.translation.asArray()
            if max(abs(got[k] * 10 - o[k]) for k in range(3)) > 0.01:
                mat = adsk.core.Matrix3D.create()
                mat.setWithCoordinateSystem(P3(*[c / 10 for c in o]), V3(*a), V3(*n), V3(*tt))
                occ.createForAssemblyContext(focc).transform2 = mat
                drift += 1
        done.append(f"{face['nome']}: {count}" + (f' ({drift} reposicionadas)' if drift else ''))
    _capture_positions(design)
    print(f'montar: {done}, {time.time() - t:.1f} s')


def lista():
    design = _design(_require_open())
    from collections import Counter
    count = Counter()
    for occ in design.rootComponent.occurrences:
        if occ.component.name.startswith('face-'):
            for child in occ.childOccurrences:
                count[child.component.name] += 1
    um = design.unitsManager
    for name, n in sorted(count.items()):
        size = (f'{_cm(mapa.PECAS[name][1]) * 10:7.2f} mm' if name in mapa.PECAS
                else '  canto em L' if name in mapa.CANTOS else '  logo' if name.startswith('logo') else '  peça avulsa')
        print(f'{name:26s} {size}  × {n}')
    print('total:', sum(count.values()))


def _depth(body):
    """Penetration depth of an interference body, mm: the thinnest side of each lump's box (pieces are
    axis-aligned), the largest over the lumps (one clip's two fin legs come as one body, two lumps)."""
    def thin(bb):
        return min(bb.maxPoint.x - bb.minPoint.x, bb.maxPoint.y - bb.minPoint.y, bb.maxPoint.z - bb.minPoint.z) * 10
    lumps = [lp for lp in body.lumps] if body.lumps.count else []
    return max(thin(lp.boundingBox) for lp in lumps) if lumps else thin(body.boundingBox)


def _preload(one, two, depth, v):
    """Intended overlaps: a clip's rib pressing a piece that stands in for the acrylic (the bowden
    plug), and the split fin's legs pressing on the slot's side walls (fin_lip_preload). Returns a label."""
    names = {one, two}
    clip = any(n.startswith('clip-') for n in names)
    if clip and names & set(getattr(mapa, 'EXTRAS', ())) and abs(depth - v['panel_preload']) < 0.01:
        return 'nervura na peça que faz as vezes da chapa'
    # the lock slider's one-layer bed tab, snapped off before assembly, crosses its cap in the assembled model
    if any(n.startswith('trava-cursor') for n in names) and any(n.startswith('trava-capa') for n in names) \
            and depth <= v.get('trava_orelha_altura', 0.0) + 0.01:
        return 'orelha do cursor (sai antes de montar)'
    lip = max(v.get('fin_lip_preload', 0.0), -v.get('fin_barb_gap', 0.0))
    if lip > 0 and FRAME_COMPONENT in names and any(n.startswith(('clip-padrao', 'clip-parede')) for n in names) \
            and depth <= lip + 0.01:
        return 'aleta apertando a aba do rasgo'
    return None


def interferencia(face):
    """Interference between one assembled face and the frame (coincident faces are ignored)."""
    t = time.time()
    design = _design(_require_open())
    root = design.rootComponent
    ents = adsk.core.ObjectCollection.create()
    for occ in root.occurrences:
        if occ.component.name in (f'face-{face}', FRAME_COMPONENT):
            ents.add(occ)
    inp = design.createInterferenceInput(ents)
    inp.areCoincidentFacesIncluded = False
    res = design.analyzeInterference(inp)
    um = design.unitsManager
    from collections import defaultdict
    worst = defaultdict(float)
    pre = {}
    v = _param_values(design)
    for r in res:
        names = [e.assemblyContext.component.name if e.assemblyContext else e.parentComponent.name
                 for e in (r.entityOne, r.entityTwo)]
        pieces = [n for n in names if n in mapa.PECAS or n in mapa.CANTOS or n in getattr(mapa, 'EXTRAS', ()) or n.startswith('trava-')]
        if not pieces:
            continue                          # frame against frame: joints of the reference itself
        piece = pieces[0]
        other = [n for n in names if n != piece][0] if len(set(names)) > 1 else piece
        depth = _depth(r.interferenceBody)
        tag = _preload(piece, other, depth, v)
        if tag:
            pre[(piece, other)] = (max(depth, pre.get((piece, other), (0, ''))[0]), tag)
            continue
        worst[(piece, other)] = max(worst[(piece, other)], depth)
    print(f'interferencia {face}: {time.time() - t:.1f} s (profundidade da sobreposição; < 0,05 mm = contato)')
    for (piece, other), (depth, tag) in sorted(pre.items()):
        print(f'    pré-carga {piece} × {other}: {depth:.3f} mm ({tag})')
    for (piece, other), depth in sorted(worst.items(), key=lambda kv: -kv[1]):
        tag = 'COLISÃO' if depth >= 0.05 else 'contato'
        print(f'    {tag:8s} {piece} × {other}: {depth:.3f} mm')
    return worst


def entre_faces(faces):
    """Interference between pieces of different faces, where the faces meet at the frame's corners."""
    t = time.time()
    design = _design(_require_open())
    root = design.rootComponent
    wanted = {f'face-{f}' for f in faces}
    ents = adsk.core.ObjectCollection.create()
    for occ in root.occurrences:
        if occ.component.name in wanted:
            ents.add(occ)
    inp = design.createInterferenceInput(ents)
    inp.areCoincidentFacesIncluded = False
    res = design.analyzeInterference(inp)
    from collections import defaultdict
    worst = defaultdict(float)
    v = _param_values(design)
    for r in res:
        where = []
        for e in (r.entityOne, r.entityTwo):
            occ = e if isinstance(e, adsk.fusion.Occurrence) else e.assemblyContext
            if occ is None:
                where.append(('?' + str(len(where)), e.parentComponent.name))
                continue
            path = occ.fullPathName.split('+')                      # face-x:1+piece:2
            where.append((path[0].rsplit(':', 1)[0][5:], path[-1].rsplit(':', 1)[0]))
        if where[0][0] == where[1][0]:
            continue                          # same face: interferencia(face) covers it
        depth = _depth(r.interferenceBody)
        if _preload(where[0][1], where[1][1], depth, v):
            continue                          # the rib on the bowden plug (reported as unplaced bodies)
        key = tuple(sorted('/'.join(w) for w in where))
        worst[key] = max(worst[key], depth)
    print(f'entre_faces {sorted(faces)}: {time.time() - t:.1f} s (< 0,05 mm = contato)')
    for (one, two), depth in sorted(worst.items(), key=lambda kv: -kv[1]):
        tag = 'COLISÃO' if depth >= 0.05 else 'contato'
        print(f'    {tag:8s} {one} × {two}: {depth:.3f} mm')
    if not worst:
        print('    nenhuma')
    return worst


def giro_porta(graus, com_frame=True, face='porta'):
    """Open a door by `graus` about its hinge pin and check it against the hinge-side panel, the other
    door if there is one (and the frame); the door goes back to its place afterwards.
    face: 'porta' (V0, hinge on the right), 'porta-direita' or 'porta-esquerda' (Trident). The right
    hinge opens about +Z, the left one about -Z."""
    t = time.time()
    design = _design(_require_open())
    root = design.rootComponent
    v = _param_values(design)
    sx = -1 if face.endswith('esquerda') else 1
    px = sx * (v['frame_width'] / 2 - v['frame_size'] / 2 + v['door_pin_s'])
    py = -v['frame_depth'] / 2 - v['door_pin_d']
    occ = next(o for o in root.occurrences if o.component.name == f'face-{face}')
    keep = occ.transform2
    rot = adsk.core.Matrix3D.create()
    rot.setToRotation(math.radians(sx * graus), V3(0, 0, 1), P3(px / 10, py / 10, 0))
    moved = keep.copy()
    moved.transformBy(rot)
    others = ['lateral-direita' if sx == 1 else 'lateral-esquerda']
    names = {o.component.name for o in root.occurrences}
    other_door = 'face-porta-esquerda' if face == 'porta-direita' else 'face-porta-direita' if face == 'porta-esquerda' else None
    if other_door in names:
        others.append(other_door[5:])
    try:
        occ.transform2 = moved
        print(f'giro_porta {face} {graus}°: pino em x {px:.2f}, y {py:.2f}')
        entre_faces([face] + others)
        if com_frame:
            ents = adsk.core.ObjectCollection.create()
            for o in root.occurrences:
                if o.component.name in (f'face-{face}', FRAME_COMPONENT):
                    ents.add(o)
            inp = design.createInterferenceInput(ents)
            inp.areCoincidentFacesIncluded = False
            worst = 0.0
            for r in design.analyzeInterference(inp):
                names = [e.assemblyContext.component.name if e.assemblyContext else e.parentComponent.name
                         for e in (r.entityOne, r.entityTwo)]
                if not any(n in mapa.PECAS or n in mapa.CANTOS for n in names) or all(n in mapa.PECAS or n in mapa.CANTOS for n in names):
                    continue                  # frame x frame, or door piece x door piece (moves together)
                worst = max(worst, _depth(r.interferenceBody))
            print(f'    porta × frame: maior profundidade {worst:.3f} mm')
    finally:
        occ.transform2 = keep
    print(f'    {time.time() - t:.1f} s')


# ---------------------------------------------------------------- sketch helpers
def _profile_sketch(design, comp, profile_name):
    """Sketch of a profile from perfis.PROFILES with every vertex dimensioned from the parameters."""
    um = design.unitsManager
    verts = perfis.PROFILES[profile_name]
    sk = comp.sketches.add(comp.xYConstructionPlane)
    sk.name = f'perfil {profile_name}'
    sk.isComputeDeferred = True
    dims = sk.sketchDimensions
    H = adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation
    V = adsk.fusion.DimensionOrientations.VerticalDimensionOrientation
    xy = [(_cm(s), _cm(d)) for s, d in verts]   # cm
    # a feature at 0 (fin_relief) leaves repeated vertices: drop them, a sketch line can't be zero long
    keep = [i for i in range(len(xy)) if abs(xy[i][0] - xy[i - 1][0]) + abs(xy[i][1] - xy[i - 1][1]) > 1e-7]
    xy, verts = [xy[i] for i in keep], [verts[i] for i in keep]
    lines = sk.sketchCurves.sketchLines
    first = lines.addByTwoPoints(P3(*xy[0], 0), P3(*xy[1], 0))
    pts = [first.startSketchPoint, first.endSketchPoint]
    prev = first.endSketchPoint
    for x, y in xy[2:]:
        prev = lines.addByTwoPoints(prev, P3(x, y, 0)).endSketchPoint
        pts.append(prev)
    lines.addByTwoPoints(prev, first.startSketchPoint)
    if not _CTX['direto']:
        ref = sk.sketchPoints.add(P3(-5, -5, 0))
        dims.addDistanceDimension(sk.originPoint, ref, H, P3(-2.5, 0.6, 0)).parameter.expression = REF_OFFSET
        dims.addDistanceDimension(sk.originPoint, ref, V, P3(0.6, -2.5, 0)).parameter.expression = REF_OFFSET
    for i, (sp, (sx, dy)) in enumerate(zip(pts, verts) if not _CTX['direto'] else []):
        x, y = sp.geometry.x, sp.geometry.y
        dims.addDistanceDimension(ref, sp, H, P3(x, -5.4 - 0.08 * (i % 6), 0)).parameter.expression = f'{REF_OFFSET} + ( {sx} )'
        dims.addDistanceDimension(ref, sp, V, P3(-5.4 - 0.08 * (i % 6), y, 0)).parameter.expression = f'{REF_OFFSET} + ( {dy} )'
    sk.isComputeDeferred = False
    return max(sk.profiles, key=lambda p: p.areaProperties().area), sk


def _poly_sketch(design, comp, plane, pts3, name):
    """Closed polygon on any plane parallel to a principal plane, every vertex dimensioned.

    pts3: vertices as (x, y, z) expressions in the component's model coordinates; the coordinate
    normal to the plane is only used to place the point.
    """
    um = design.unitsManager
    sk = comp.sketches.add(plane)
    sk.name = name
    sk.isComputeDeferred = True
    o = sk.modelToSketchSpace(P3(0, 0, 0))
    axes = []
    for k in range(3):
        u = [0.0, 0.0, 0.0]
        u[k] = 1.0
        p = sk.modelToSketchSpace(P3(*u))
        axes.append((p.x - o.x, p.y - o.y))

    def expr(row, e3):
        terms = [('' if axes[k][row] > 0 else '-') + f'( {e3[k]} )' for k in range(3) if abs(axes[k][row]) > 0.5]
        base = (o.x, o.y)[row] * 10
        if abs(base) > 1e-6:
            terms.append(f'( {base:.6f} mm )')
        return ' + '.join(terms) if terms else '0 mm'

    pts = [sk.modelToSketchSpace(P3(*[_cm(e) for e in e3])) for e3 in pts3]
    lines = sk.sketchCurves.sketchLines
    first = lines.addByTwoPoints(P3(pts[0].x, pts[0].y, 0), P3(pts[1].x, pts[1].y, 0))
    sps = [first.startSketchPoint, first.endSketchPoint]
    prev = first.endSketchPoint
    for p in pts[2:]:
        prev = lines.addByTwoPoints(prev, P3(p.x, p.y, 0)).endSketchPoint
        sps.append(prev)
    lines.addByTwoPoints(prev, first.startSketchPoint)
    if not _CTX['direto']:
        dims = sk.sketchDimensions
        H = adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation
        V = adsk.fusion.DimensionOrientations.VerticalDimensionOrientation
        # the reference sits far away: a sketch axis can run against a model axis, and every distance
        # from the reference must stay positive (a negative one would flip the point to the other side)
        ref_offset = '500 mm'
        ref = sk.sketchPoints.add(P3(-50, -50, 0))
        dims.addDistanceDimension(sk.originPoint, ref, H, P3(-25, 0.6, 0)).parameter.expression = ref_offset
        dims.addDistanceDimension(sk.originPoint, ref, V, P3(0.6, -25, 0)).parameter.expression = ref_offset
        for i, (sp, e3) in enumerate(zip(sps, pts3)):
            x, y = sp.geometry.x, sp.geometry.y
            dims.addDistanceDimension(ref, sp, H, P3(x, -50.4 - 0.08 * (i % 6), 0)).parameter.expression = f'{ref_offset} + ( {expr(0, e3)} )'
            dims.addDistanceDimension(ref, sp, V, P3(-50.4 - 0.08 * (i % 6), y, 0)).parameter.expression = f'{ref_offset} + ( {expr(1, e3)} )'
    sk.isComputeDeferred = False
    return sk, max(sk.profiles, key=lambda p: p.areaProperties().area)


def _circle_sketch(design, comp, plane, c3, dia_expr, name):
    """Circle on a principal plane, centre and diameter dimensioned from expressions (see _poly_sketch)."""
    um = design.unitsManager
    sk = comp.sketches.add(plane)
    sk.name = name
    sk.isComputeDeferred = True
    o = sk.modelToSketchSpace(P3(0, 0, 0))
    axes = []
    for k in range(3):
        u = [0.0, 0.0, 0.0]
        u[k] = 1.0
        p = sk.modelToSketchSpace(P3(*u))
        axes.append((p.x - o.x, p.y - o.y))

    def expr(row):
        terms = [('' if axes[k][row] > 0 else '-') + f'( {c3[k]} )' for k in range(3) if abs(axes[k][row]) > 0.5]
        base = (o.x, o.y)[row] * 10
        if abs(base) > 1e-6:
            terms.append(f'( {base:.6f} mm )')
        return ' + '.join(terms) if terms else '0 mm'

    c = sk.modelToSketchSpace(P3(*[_cm(e) for e in c3]))
    circ = sk.sketchCurves.sketchCircles.addByCenterRadius(P3(c.x, c.y, 0), _cm(dia_expr) / 2)
    if _CTX['direto']:
        sk.isComputeDeferred = False
        return sk, min(sk.profiles, key=lambda p: p.areaProperties().area)
    dims = sk.sketchDimensions
    H = adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation
    V = adsk.fusion.DimensionOrientations.VerticalDimensionOrientation
    ref_offset = '500 mm'
    ref = sk.sketchPoints.add(P3(-50, -50, 0))
    dims.addDistanceDimension(sk.originPoint, ref, H, P3(-25, 0.6, 0)).parameter.expression = ref_offset
    dims.addDistanceDimension(sk.originPoint, ref, V, P3(0.6, -25, 0)).parameter.expression = ref_offset
    dims.addDiameterDimension(circ, P3(c.x + 0.5, c.y + 0.5, 0)).parameter.expression = dia_expr
    dims.addDistanceDimension(ref, circ.centerSketchPoint, H, P3(c.x, -50.4, 0)).parameter.expression = f'{ref_offset} + ( {expr(0)} )'
    dims.addDistanceDimension(ref, circ.centerSketchPoint, V, P3(-50.4, c.y, 0)).parameter.expression = f'{ref_offset} + ( {expr(1)} )'
    sk.isComputeDeferred = False
    return sk, min(sk.profiles, key=lambda p: p.areaProperties().area)


def _profile_on_plane(design, comp, plane, profile_name, mapper, name):
    """A profile of perfis.PROFILES drawn on a plane; mapper turns (s, d) expressions into (x, y, z)."""
    pts3 = [mapper(s, d) for s, d in perfis.PROFILES[profile_name]]
    return _poly_sketch(design, comp, plane, pts3, f'{name}: {profile_name}')


def _extrude_dir(comp, prof, sk, dist_expr, model_dir, op, target=None):
    """One-sided extrude toward a model direction, whatever the sketch normal is."""
    nrm = sk.xDirection.crossProduct(sk.yDirection)
    pos = nrm.dotProduct(V3(*model_dir)) > 0
    inp = comp.features.extrudeFeatures.createInput(prof, op)
    inp.setOneSideExtent(adsk.fusion.DistanceExtentDefinition.create(_vi(dist_expr)),
                         adsk.fusion.ExtentDirections.PositiveExtentDirection if pos else adsk.fusion.ExtentDirections.NegativeExtentDirection)
    if target is not None:
        inp.participantBodies = [target]
    return _add_extrude(comp, inp, op)


def _extrude_sym(comp, prof, dist_expr, op, target=None):
    inp = comp.features.extrudeFeatures.createInput(prof, op)
    inp.setSymmetricExtent(_vi(dist_expr), True)
    if target is not None:
        inp.participantBodies = [target]
    return _add_extrude(comp, inp, op)


def _add_extrude(comp, inp, op):
    """Add an extrude; a cut that finds no material is a no-op (direct modeling refuses it, the
    timeline used to accept it silently), e.g. a clip run where the miter left only its own leg."""
    try:
        return comp.features.extrudeFeatures.add(inp)
    except RuntimeError as e:
        if op == CUT and ('No target body found' in str(e) or '!extrudes.empty()' in str(e)):
            print(f'    (corte vazio em {comp.name}: nada a remover)')
            return None
        raise


def _offset_plane(comp, base, expr, toward):
    """Construction plane parallel to base, offset by expr toward a model direction."""
    nrm = base.geometry.normal
    sign = '' if nrm.dotProduct(V3(*toward)) > 0 else '-'
    inp = comp.constructionPlanes.createInput()
    inp.setByOffset(base, _vi(f'{sign}( {expr} )'))
    return comp.constructionPlanes.add(inp)


def _parent(design, name):
    comp = design.allComponents.itemByName(name)
    comp = comp if comp is not None else _new_component(design.rootComponent, name)
    # direct modeling leaves hidden bodies out of cuts and combines: keep the pieces visible
    for occ in design.rootComponent.occurrences:
        if occ.component == comp:
            occ.isLightBulbOn = True
    return comp


def _misumi_sketch(comp):
    """Misumi 1515 section from the official V0.2 CAD, as fixed geometry (loops pre-chained in the JSON)."""
    data = json.load(open(_ref(config.PERFIL_JSON)))
    sk = comp.sketches.add(comp.xYConstructionPlane)
    sk.name = 'perfil Misumi 1515 (CAD V0.2)'
    sk.isComputeDeferred = True
    lines = sk.sketchCurves.sketchLines
    for loop in data['loops']:
        pts = loop[:-1] if loop[0] == loop[-1] else loop
        first = lines.addByTwoPoints(P3(pts[0][0] / 10, pts[0][1] / 10, 0), P3(pts[1][0] / 10, pts[1][1] / 10, 0))
        prev = first.endSketchPoint
        for x, y in pts[2:]:
            prev = lines.addByTwoPoints(prev, P3(x / 10, y / 10, 0)).endSketchPoint
        lines.addByTwoPoints(prev, first.startSketchPoint)
    sk.isComputeDeferred = False
    return max(sk.profiles, key=lambda p: p.areaProperties().area)


def _extrude(comp, prof, body_name, length_expr):
    ext = comp.features.extrudeFeatures.addSimple(
        prof, _vi(length_expr),
        adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    ext.bodies.item(0).name = body_name
    return ext


# ---------------------------------------------------------------- document helpers
def _design(doc):
    return adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))


def _find_open(app):
    for d in app.documents:
        if d.name.startswith(DOC_NAME):
            return d
    return None


def _require_open():
    app = adsk.core.Application.get()
    doc = _find_open(app)
    if doc is None:
        # not saved yet: the unsaved document created by preparar(), recognised by its mark
        for d in app.documents:
            design = _design(d)
            mark = design.attributes.itemByName('gerador', 'documento') if design else None
            if not d.isSaved and mark is not None and mark.value == DOC_NAME:
                doc = d
                break
    if doc is None:
        raise RuntimeError(f'{DOC_NAME} não está aberto; rode construir.preparar() antes')
    doc.activate()
    _contexto(_design(doc))
    return doc


def _contexto(design):
    """Mode of the document in use: direct (values from parametros.py) or parametric (Fusion's)."""
    _CTX['direto'] = design.designType == adsk.fusion.DesignTypes.DirectDesignType
    _CTX['um'] = design.unitsManager
    if _CTX['direto']:
        usar(MAQ['nome'] or 'v0')
        _CTX['vals'] = perfis.param_values(parametros.PARAMS)


def _cm(expr):
    """An expression's value in cm (Fusion's internal unit)."""
    if _CTX['direto']:
        return perfis.evaluate(expr, _CTX['vals']) / 10
    return _CTX['um'].evaluateExpression(expr, 'mm')


def _vi(expr):
    """ValueInput for a length: the expression itself (parametric) or its value (direct)."""
    if _CTX['direto']:
        return adsk.core.ValueInput.createByReal(_cm(expr))
    return adsk.core.ValueInput.createByString(expr)


def _find_saved(app):
    proj = next(p for p in app.data.dataProjects if p.name == PROJECT)
    folder = proj.rootFolder.dataFolders.itemByName(FOLDER)
    for f in folder.dataFiles:
        if f.name == DOC_NAME:
            return f
    return None


def _param_values(design):
    """Parameter values in mm (lengths), degrees (angles) and plain numbers (counts)."""
    if design.designType == adsk.fusion.DesignTypes.DirectDesignType:
        return perfis.param_values(parametros.PARAMS)
    out = {}
    for p in design.userParameters:
        out[p.name] = math.degrees(p.value) if p.unit == 'deg' else p.value if p.unit == '' else p.value * 10
    return out


def _place(parent_occ, comp, mat):
    """New occurrence of an existing component inside the component of parent_occ (a root
    occurrence), at mat relative to it. Direct modeling composes mat with the position of the
    component's first occurrence, so there the matrix is set again through the root-context proxy."""
    occ = parent_occ.component.occurrences.addExistingComponent(comp, mat)
    if _CTX['direto']:
        world = mat.copy()
        world.transformBy(parent_occ.transform2)
        occ.createForAssemblyContext(parent_occ).transform2 = world
    return occ


def _loose_body(comp, main):
    """The one body of comp besides the named main body (a tool built for a combine). Direct
    modeling returns no feature from a combine, so the result is found here instead."""
    others = [b for b in comp.bRepBodies if b.name != main]
    if len(others) != 1:
        raise RuntimeError(f'{comp.name}: esperava um corpo além de {main}, há {[b.name for b in others]}')
    return others[0]


def _new_component(root, name):
    occ = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    occ.component.name = name
    return occ.component


def _delete_component(root, name):
    """Delete every occurrence of the component (anywhere in the assembly), which removes it."""
    for occ in reversed([o for o in root.allOccurrences if o.component.name == name]):
        if occ.isValid:
            occ.deleteMe()


def _capture_positions(design):
    if design.designType == adsk.fusion.DesignTypes.DirectDesignType:
        return
    if design.snapshots.hasPendingSnapshot:
        design.snapshots.add()


usar('v0')     # default machine; call construir.usar('trident') to switch
