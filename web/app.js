// The configurator's page: the machine, face and parameter choices, the 3D view (three.js), the check and the ZIP of
// the face's STLs. With the default values all of it comes ready-made from pre/ (motor.py pre-gerar, built on a
// computer), so the page works at once; a changed parameter goes to the engine (motor.js, a Web Worker running the
// generator in Pyodide), which loads meanwhile. The choice lives in the link (#m=…&f=…&p=…) and in this browser
// (localStorage), so it can be shared and comes back. The page is in English (campos.js: the user's parameters, the
// names, the checks' phrases); the generator's own names stay as they are.
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { CAMPOS, FACES, GRUPOS_CONFERENCIA, MAQUINAS, traduzir } from './campos.js';

const $ = (id) => document.getElementById(id);
const CORES = { externa: 0x966ecd, interna: 0x7dc3eb, trava: 0xe07b39, frame: 0x8c8e94 };
const estado = { catalogo: null, maquina: 'trident-trava', face: 'topo', mudancas: {}, valores: {}, erros: {}, gerado: null,
  ocupado: false, motorPronto: false };
const numero = (v, casas = 0) => v.toLocaleString('en-US', { maximumFractionDigits: casas });

// ---------------------------------------------------------------- the engine
const motor = new Worker(new URL('motor.js', import.meta.url), { type: 'module' });
const pendentes = new Map();
let proximoId = 1;
function chamar(acao, args) {
  const id = proximoId++;
  if (!estado.motorPronto) progresso('Waiting for the engine to finish loading…');
  return new Promise((ok, falha) => { pendentes.set(id, { ok, falha }); motor.postMessage({ id, acao, args }); });
}
motor.onerror = (e) => { estado.motorFalhou = true; seloMotor(); progresso('The engine failed: ' + (e.message || e), true); console.error(e); };
motor.onmessage = (e) => {
  const m = e.data;
  if (m.tipo === 'etapa') { estado.etapa = m.texto; seloMotor(); if (!estado.ocupado && !estado.catalogo) progresso(m.texto); }
  else if (m.tipo === 'log') { if (estado.ocupado && estado.motorPronto) progresso(m.texto.trim()); }
  else if (m.tipo === 'pronto') motorPronto(m.catalogo, m.tempo);
  else if (m.tipo === 'falha') { estado.motorFalhou = true; seloMotor(); progresso('The engine did not load: ' + m.texto, true); }
  else if (m.tipo === 'resposta' || m.tipo === 'erro') {
    const p = pendentes.get(m.id);
    pendentes.delete(m.id);
    if (m.tipo === 'resposta') p.ok(m.resultado); else p.falha(Object.assign(new Error(m.texto), { completo: m.completo }));
  }
};

function seloMotor() {
  const s = $('estado');
  if (estado.motorFalhou) { s.className = 'estado erro'; s.textContent = 'engine failed'; return; }
  s.className = 'estado ' + (estado.motorPronto ? 'pronto' : 'carregando');
  s.textContent = estado.motorPronto ? 'engine ready' : 'engine loading…';
  s.title = estado.motorPronto ? 'You can change parameters and generate.' : (estado.etapa || '') + ' The default configuration already works.';
}
function progresso(texto, erro = false) { const p = $('progresso'); p.textContent = texto; p.classList.toggle('erro-txt', erro); }

// ---------------------------------------------------------------- choices: link and this browser
function lerEscolha() {
  const h = new URLSearchParams(location.hash.slice(1));
  let salvo = {};
  try { salvo = JSON.parse(localStorage.getItem('panel-holder') || '{}'); } catch { salvo = {}; }
  estado.maquina = h.get('m') || salvo.maquina || estado.maquina;
  estado.face = h.get('f') || salvo.face || estado.face;
  try { estado.mudancas = h.get('p') ? { [estado.maquina]: JSON.parse(h.get('p')) } : (salvo.mudancas || {}); } catch { estado.mudancas = {}; }
}
function guardarEscolha() {
  const mud = estado.mudancas[estado.maquina] || {};
  const h = new URLSearchParams({ m: estado.maquina, f: estado.face });
  if (Object.keys(mud).length) h.set('p', JSON.stringify(mud));
  history.replaceState(null, '', '#' + h.toString());
  try { localStorage.setItem('panel-holder', JSON.stringify({ maquina: estado.maquina, face: estado.face, mudancas: estado.mudancas })); } catch { /* private window */ }
}
const maq = () => estado.catalogo.find((c) => c.nome === estado.maquina);
const mudancas = () => estado.mudancas[estado.maquina] || (estado.mudancas[estado.maquina] = {});
const padrao = () => !Object.keys(mudancas()).length;
const chaveAtual = () => JSON.stringify([estado.maquina, estado.face, mudancas()]);
const nomeFace = (f) => FACES[f] || f;

// ---------------------------------------------------------------- ready-made faces (pre/)
const pre = {};
async function carregarPre(m) {
  if (!pre[m]) pre[m] = fetch(`pre/${m}.json`).then((r) => { if (!r.ok) throw new Error(`pre/${m}.json: ${r.status}`); return r.json(); });
  return pre[m];
}
const deBase64 = (s) => Uint8Array.from(atob(s), (c) => c.charCodeAt(0));
async function faceProntaPre() {
  const d = await carregarPre(estado.maquina);
  const f = d.faces[estado.face];
  const pecas = {};
  for (const [n, k] of Object.entries(f.quantidades)) pecas[n] = { ...d.pecas[n], quantidade: k, v: deBase64(d.pecas[n].v), t: deBase64(d.pecas[n].t) };
  return { pecas, colocacoes: f.colocacoes, normal: f.normal, conferencia: f.conferencia,
    frame: { perfis: d.frame.perfis.map((p) => ({ v: deBase64(p.v), t: deBase64(p.t) })), membros: d.frame.membros } };
}

// ---------------------------------------------------------------- start
async function iniciar() {
  seloMotor();
  try {
    estado.catalogo = await (await fetch('pre/catalogo.json')).json();
  } catch {
    progresso('No ready-made faces (pre/): waiting for the engine to load…');
    return;                    // motorPronto() starts the page with the engine's catalogue
  }
  comecar();
}
function comecar() {
  if (!estado.catalogo.some((c) => c.nome === estado.maquina)) estado.maquina = estado.catalogo[0].nome;
  const sm = $('maquina');
  sm.innerHTML = estado.catalogo.map((c) => `<option value="${c.nome}">${MAQUINAS[c.nome] || c.titulo}</option>`).join('');
  sm.value = estado.maquina;
  for (const id of ['maquina', 'face', 'gerar', 'conferir', 'baixar']) $(id).disabled = false;
  trocarMaquina(false);
  gerar();
}
function motorPronto(catalogo, tempo) {
  estado.motorPronto = true;
  document.body.dataset.motor = tempo;
  seloMotor();
  if (!estado.catalogo) { estado.catalogo = catalogo; comecar(); return; }
  if (!estado.ocupado) progresso(`Engine loaded in ${tempo} s: you can change parameters now.`);
  if (!padrao()) avaliar();
}

function trocarMaquina(limparFace = true) {
  const m = maq();
  if (limparFace || !m.faces.includes(estado.face)) estado.face = m.faces.includes(estado.face) ? estado.face : m.faces[0];
  $('face').innerHTML = m.faces.map((f) => `<option value="${f}">${nomeFace(f)}${(m.portas || []).includes(f) ? ' (clips with lock)' : ''}</option>`).join('');
  $('face').value = estado.face;
  estado.valores = Object.fromEntries(m.parametros.map((p) => [p.nome, p.valor]));
  estado.erros = {};
  desenharParametros();
  if (!padrao() && estado.motorPronto) avaliar();
  marcarDesatualizado();
  guardarEscolha();
  if (limparFace) gerar();
}
$('maquina').onchange = () => { estado.maquina = $('maquina').value; trocarMaquina(); };
$('face').onchange = () => { estado.face = $('face').value; guardarEscolha(); marcarDesatualizado(); gerar(); };

function marcarDesatualizado() {
  const a = $('aviso');
  const desat = estado.gerado && estado.gerado !== chaveAtual();
  a.hidden = !desat;
  a.textContent = desat ? 'Changes not generated yet: press Generate.' : '';
}

// ---------------------------------------------------------------- parameters: the user's, and the rest under Advanced
const UNIDADES = { mm: 'mm', deg: '°' };
function fmt(v) { return typeof v === 'number' ? (Math.abs(v) >= 100 ? v.toFixed(1) : String(+v.toFixed(4))) : String(v); }
function escapar(s) { return String(s).replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;'); }
const camposDaMaquina = (m) => CAMPOS.filter((c) => c.em.includes(m.nome) && m.parametros.some((p) => p.nome === c.nome));

function desenharParametros() {
  const m = maq();
  const filtro = $('filtro').value.trim().toLowerCase();
  const so = $('so-alterados').checked;
  const mud = mudancas();
  const passa = (nome, texto) => (!filtro || nome.toLowerCase().includes(filtro) || texto.toLowerCase().includes(filtro)) && (!so || nome in mud);
  const tabela = Object.fromEntries(m.parametros.map((p) => [p.nome, p]));
  const campos = camposDaMaquina(m);
  // the user's parameters, by group: a number in the parameter's unit
  const grupos = {};
  for (const c of campos) if (passa(c.nome, c.rotulo + ' ' + c.ajuda)) (grupos[c.grupo] = grupos[c.grupo] || []).push(c);
  let html = Object.entries(grupos).map(([g, cs]) => `<h3 class="grupo">${g}</h3>` + cs.map((c) => {
    const p = tabela[c.nome];
    const valor = c.nome in mud && !Number.isNaN(parseFloat(mud[c.nome])) ? parseFloat(mud[c.nome]) : fmt(p.valor);
    return `<div class="param ${c.nome in mud ? 'alterado' : ''} ${estado.erros[c.nome] ? 'invalido' : ''}" data-nome="${c.nome}" data-tipo="numero">
      <label class="rotulo" for="p-${c.nome}">${c.rotulo}</label>
      <div class="entrada"><input id="p-${c.nome}" type="text" inputmode="decimal" spellcheck="false" value="${escapar(valor)}"><span class="unidade">${UNIDADES[p.unidade] || ''}</span>
        <span class="padrao">default ${fmt(p.valor)}</span></div>
      <div class="desc">${escapar(c.ajuda)}</div></div>`;
  }).join('')).join('');
  // the design values, by the generator's names
  const nossos = new Set(campos.map((c) => c.nome));
  const resto = m.parametros.filter((p) => !nossos.has(p.nome) && passa(p.nome, ''));
  html += `<details id="avancado" ${filtro || so ? 'open' : ''}><summary>Advanced: design values (${resto.length})</summary>
    <p class="nota">The design's own parameters, by their names in the generator (each machine's <code>parametros.py</code>).
    They take expressions in the other parameters' names. Change them only if you know the design.</p>` +
    resto.map((p) => `<div class="param ${p.nome in mud ? 'alterado' : ''} ${estado.erros[p.nome] ? 'invalido' : ''}" data-nome="${p.nome}">
      <div class="topo"><span class="nome">${p.nome}</span><span class="valor">= ${fmt(estado.valores[p.nome])}${UNIDADES[p.unidade] ? ' ' + UNIDADES[p.unidade] : ''}</span></div>
      <input type="text" value="${escapar(mud[p.nome] ?? p.expr)}" spellcheck="false" aria-label="${p.nome}"></div>`).join('') + '</details>';
  const aberto = $('avancado') && $('avancado').open;
  $('parametros').innerHTML = html;
  if (aberto) $('avancado').open = true;
  const n = Object.keys(mud).length;
  $('n-alterados').textContent = n ? `${n} changed` : '';
}
$('parametros').addEventListener('change', (e) => {
  const row = e.target.closest('.param');
  if (!row) return;
  const nome = row.dataset.nome;
  const p = maq().parametros.find((x) => x.nome === nome);
  const v = e.target.value.trim();
  if (row.dataset.tipo === 'numero') {
    // a number in the parameter's unit (a decimal comma too): the same as the default is no change
    const x = Number(v.replace(',', '.'));
    if (v !== '' && Number.isNaN(x)) {
      estado.erros[nome] = 'not a number';
      progresso(`Invalid parameter: ${nome} (not a number)`, true);
      row.classList.add('invalido');
      return;
    }
    delete estado.erros[nome];
    if (v === '' || Math.abs(x - p.valor) < 1e-9) delete mudancas()[nome];
    else mudancas()[nome] = `${x}${p.unidade === 'mm' ? ' mm' : p.unidade === 'deg' ? ' deg' : ''}`;
  } else if (!v || v === p.expr) {
    delete mudancas()[nome];
  } else {
    mudancas()[nome] = v;
  }
  guardarEscolha();
  desenharParametros();
  marcarDesatualizado();
  if (estado.motorPronto) avaliar();
});
$('filtro').oninput = desenharParametros;
$('so-alterados').onchange = desenharParametros;
$('restaurar').onclick = () => { estado.mudancas[estado.maquina] = {}; guardarEscolha(); trocarMaquina(false); };

async function avaliar() {
  const r = await chamar('avaliar', [estado.maquina, JSON.stringify(mudancas())]);
  estado.erros = {};
  if (r.erro) {
    // the expression that failed: try each change alone
    for (const [k, v] of Object.entries(mudancas())) {
      const s = await chamar('avaliar', [estado.maquina, JSON.stringify({ [k]: v })]);
      if (s.erro) estado.erros[k] = s.erro;
    }
    progresso('Invalid parameter: ' + Object.entries(estado.erros).map(([k, e]) => `${k} (${e})`).join('; '), true);
  } else {
    estado.valores = r.valores;
    if ($('progresso').classList.contains('erro-txt')) progresso('');
  }
  desenharParametros();
  marcarDesatualizado();
}

// ---------------------------------------------------------------- generate, check, download
async function tarefa(rotulo, f) {
  if (estado.ocupado) return;
  estado.ocupado = true;
  for (const id of ['gerar', 'conferir', 'baixar', 'maquina', 'face']) $(id).disabled = true;
  const t = performance.now();
  try {
    const feito = await f();
    progresso(feito || `${rotulo}: ${((performance.now() - t) / 1000).toFixed(1)} s.`);
  } catch (err) {
    progresso(`${rotulo} failed: ${err.message}`, true);
    console.error(err.completo || err);
  } finally {
    estado.ocupado = false;
    for (const id of ['gerar', 'conferir', 'baixar', 'maquina', 'face']) $(id).disabled = false;
  }
}
const args = () => [estado.maquina, estado.face, JSON.stringify(mudancas())];

function gerar() {
  if (Object.keys(estado.erros).length) { progresso('Fix the invalid parameters before generating.', true); return; }
  return tarefa('Generating', async () => {
    const pronto = padrao();
    const r = pronto ? await faceProntaPre() : await chamar('montar', args());
    mostrarFace(r);
    estado.gerado = chaveAtual();
    marcarDesatualizado();
    $('bloco-conferencia').hidden = true;
    return pronto ? 'Default configuration (ready-made).' : null;
  });
}
$('gerar').onclick = gerar;

function mostrarConferencia(r) {
  if (r.familia === 'peca-unica') { mostrarConferenciaPU(r); return; }
  const prof = (l) => l.length ? ` (up to ${Math.max(...l.map((x) => x.profundidade)).toFixed(3)} mm)` : '';
  const tipos = [...new Set(r.pre_cargas.map((x) => traduzir(x.tipo)))];
  $('conferencia').innerHTML =
    `<p class="conf-linha ${r.colisoes.length ? 'erro-txt' : 'ok-txt'}">Collisions: ${r.colisoes.length || 'none'}</p>` +
    r.colisoes.map((c) => `<div class="conf-item" data-pecas="${escapar(c.pecas)}">${escapar(c.pecas)}: ${c.profundidade} mm, ${c.volume} mm³</div>`).join('') +
    `<p class="conf-linha">Design preloads: ${r.pre_cargas.length}${prof(r.pre_cargas)}${tipos.length ? ': ' + tipos.join('; ') : ''}</p>` +
    `<p class="conf-linha">Contacts (under 0.05 mm): ${r.contatos.length}${prof(r.contatos)}</p>` +
    `<p class="progresso">The face's parts against each other and the frame (the generator's interference check).</p>`;
  $('bloco-conferencia').hidden = false;
}
function mostrarConferenciaPU(r) {
  $('conferencia').innerHTML = r.grupos.map((g) => g.nao_zerados.length
    ? `<p class="conf-linha">${GRUPOS_CONFERENCIA[g.nome] || g.nome}: ${g.casos} cases, ${g.nao_zerados.length} not zero</p>` +
      g.nao_zerados.map(([c, v]) => `<div class="conf-item">${escapar(traduzir(c.split(' / ').slice(1).join(' / ')))}: ${v} mm³</div>`).join('')
    : `<p class="conf-linha ok-txt">${GRUPOS_CONFERENCIA[g.nome] || g.nome}: ${g.casos} cases, all zero</p>`).join('') +
    `<p class="progresso">Overlap volumes (mm³), the one-piece generator's own check. By design: the hook's squeeze (locked × frame), ` +
    `the slider's brim tab in the cap (snapped off before assembly) and, on the Trident's hinge corners, the barb passing the slot's lip going in.</p>`;
  $('bloco-conferencia').hidden = false;
}
$('conferir').onclick = () => tarefa('Checking', async () => {
  if (padrao()) { mostrarConferencia((await faceProntaPre()).conferencia); return 'Check of the default configuration (ready-made).'; }
  mostrarConferencia(await chamar('conferir', args()));
});
$('conferencia').addEventListener('click', (e) => {
  const it = e.target.closest('.conf-item[data-pecas]');
  if (it) selecionarChaves(it.dataset.pecas.split(' × '));
});

$('baixar').onclick = () => tarefa('Exporting', async () => {
  const dados = padrao() ? await (await fetch(`pre/${estado.maquina}/${estado.face}.zip`)).blob() : await chamar('zip', args());
  const a = document.createElement('a');
  a.href = URL.createObjectURL(new Blob([dados], { type: 'application/zip' }));
  a.download = `${maq().prefixo}${estado.face}${padrao() ? '' : '-custom'}.zip`;
  a.click();
  setTimeout(() => URL.revokeObjectURL(a.href), 10000);
});

// ---------------------------------------------------------------- 3D view
const tela = $('tela');
const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
tela.appendChild(renderer.domElement);
const cena = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(30, 1, 1, 50000);
camera.up.set(0, 0, 1);
const controles = new OrbitControls(camera, renderer.domElement);
controles.addEventListener('change', desenhar);
cena.add(new THREE.HemisphereLight(0xffffff, 0x5a5a5a, 1.6));
const luz = new THREE.DirectionalLight(0xffffff, 1.8);
luz.position.set(0.4, 0.6, 1);
camera.add(luz);
cena.add(camera);
const grupoPecas = new THREE.Group();
const grupoFrame = new THREE.Group();
cena.add(grupoPecas, grupoFrame);
const material = (cor, extra = {}) => new THREE.MeshStandardMaterial({ color: cor, roughness: 0.7, metalness: 0.05, ...extra });
const materiais = { externa: material(CORES.externa), interna: material(CORES.interna), trava: material(CORES.trava),
  frame: material(CORES.frame, { roughness: 0.5, metalness: 0.3 }), selecionada: material(0xffd23f, { emissive: 0x6b4f00 }) };

function corDeFundo() { return getComputedStyle(document.documentElement).getPropertyValue('--vista').trim() || '#eceae6'; }
function desenhar() { cena.background = new THREE.Color(corDeFundo()); renderer.render(cena, camera); }
new ResizeObserver(() => {
  const w = tela.clientWidth, h = tela.clientHeight;
  renderer.setSize(w, h, false);
  camera.aspect = w / Math.max(h, 1);
  camera.updateProjectionMatrix();
  desenhar();
}).observe(tela);
matchMedia('(prefers-color-scheme: dark)').addEventListener('change', desenhar);

function geometria(v, t) {
  const g = new THREE.BufferGeometry();
  const f = v.byteOffset % 4 ? new Float32Array(v.slice().buffer) : new Float32Array(v.buffer, v.byteOffset, v.byteLength / 4);
  const i = t.byteOffset % 4 ? new Uint32Array(t.slice().buffer) : new Uint32Array(t.buffer, t.byteOffset, t.byteLength / 4);
  g.setAttribute('position', new THREE.BufferAttribute(f, 3));
  g.setIndex(new THREE.BufferAttribute(i, 1));
  g.computeVertexNormals();
  return g;
}
function matriz(a) { return new THREE.Matrix4().set(...a); }
function limpar(grupo) {
  for (const o of grupo.children) o.geometry.dispose();
  grupo.clear();
}

let ultimo = null;
function mostrarFace(r) {
  limpar(grupoPecas);
  limpar(grupoFrame);
  const geos = Object.fromEntries(Object.entries(r.pecas).map(([n, p]) => [n, geometria(p.v, p.t)]));
  const conta = {};
  for (const [n, a] of r.colocacoes) {
    conta[n] = (conta[n] || 0) + 1;
    const malha = new THREE.Mesh(geos[n].clone(), materiais[r.pecas[n].tipo]);
    malha.matrixAutoUpdate = false;
    malha.matrix.copy(matriz(a));
    malha.userData = { nome: n, chave: `${n}:${conta[n]}`, tipo: r.pecas[n].tipo };
    grupoPecas.add(malha);
  }
  Object.values(geos).forEach((g) => g.dispose());
  const perfis = r.frame.perfis.map((p) => geometria(p.v, p.t));
  for (const mb of r.frame.membros) {
    const malha = new THREE.Mesh(perfis[mb.perfil].clone(), materiais.frame);
    malha.matrixAutoUpdate = false;
    malha.matrix.copy(matriz(mb.matriz));
    malha.userData = { nome: mb.nome, chave: `frame:${mb.nome}`, tipo: 'frame' };
    grupoFrame.add(malha);
  }
  perfis.forEach((g) => g.dispose());
  grupoFrame.visible = $('ver-frame').checked;
  $('vazio').hidden = true;
  const novaFace = !ultimo || ultimo.face !== estado.face || ultimo.maquina !== estado.maquina;
  ultimo = { face: estado.face, maquina: estado.maquina };
  if (novaFace) enquadrar(r.normal);
  tabelaPecas(r.pecas);
  selecionar(null);
}

function enquadrar(normal) {
  grupoPecas.updateMatrixWorld(true);
  const caixa = new THREE.Box3().setFromObject(grupoPecas);
  const centro = caixa.getCenter(new THREE.Vector3());
  const tam = caixa.getSize(new THREE.Vector3()).length();
  const n = new THREE.Vector3(...normal);
  const inclina = Math.abs(n.z) > 0.9 ? new THREE.Vector3(0, -0.45, 0) : new THREE.Vector3(0, 0, 0.35);
  const dir = n.clone().add(inclina).normalize();
  camera.position.copy(centro).addScaledVector(dir, tam * 2.2);
  camera.near = tam / 100; camera.far = tam * 20; camera.updateProjectionMatrix();
  controles.target.copy(centro);
  controles.update();
  desenhar();
}

function tabelaPecas(pecas) {
  const corCss = { externa: 'var(--c-externa)', interna: 'var(--c-interna)', trava: 'var(--c-trava)' };
  const linhas = Object.entries(pecas).sort((a, b) => a[0].localeCompare(b[0]));
  $('pecas').querySelector('tbody').innerHTML = linhas.map(([n, p]) =>
    `<tr class="clicavel" data-nome="${n}"><td><span class="cor" style="background:${corCss[p.tipo]}"></span>${n.split('@')[0]}</td>` +
    `<td class="num">${p.quantidade}</td><td class="num">${numero(p.volume)}</td></tr>`).join('');
  const total = linhas.reduce((a, [, p]) => a + p.quantidade, 0);
  $('pecas').querySelector('tbody').insertAdjacentHTML('beforeend', `<tr><td><b>total</b></td><td class="num"><b>${total}</b></td><td></td></tr>`);
  $('bloco-pecas').hidden = false;
  estado.pecas = pecas;
}
$('pecas').addEventListener('click', (e) => { const tr = e.target.closest('tr[data-nome]'); if (tr) selecionar(tr.dataset.nome); });

function pintar(teste) {
  for (const m of [...grupoPecas.children, ...grupoFrame.children]) {
    m.material = teste(m) ? materiais.selecionada : (m.userData.tipo === 'frame' ? materiais.frame : materiais[m.userData.tipo]);
  }
  desenhar();
}
function selecionar(nome) {
  pintar((m) => nome && m.userData.nome === nome);
  document.querySelectorAll('#pecas tr').forEach((tr) => tr.classList.toggle('sel', tr.dataset.nome === nome));
  const s = $('selecao');
  if (!nome || !estado.pecas || !estado.pecas[nome]) { s.hidden = true; return; }
  const p = estado.pecas[nome];
  s.hidden = false;
  s.innerHTML = `<b>${nome.split('@')[0]}</b><br>${p.quantidade}× on this face · ${numero(p.volume, 2)} mm³`;
}
function selecionarChaves(chaves) {
  pintar((m) => chaves.includes(m.userData.chave));
  const s = $('selecao');
  s.hidden = false;
  s.innerHTML = chaves.map((c) => `<b>${escapar(c)}</b>`).join('<br>');
}
$('ver-frame').onchange = () => { grupoFrame.visible = $('ver-frame').checked; desenhar(); };

// click (not drag) on a piece selects it
const raio = new THREE.Raycaster();
let inicio = null;
renderer.domElement.addEventListener('pointerdown', (e) => { inicio = [e.clientX, e.clientY]; });
renderer.domElement.addEventListener('pointerup', (e) => {
  if (!inicio || Math.hypot(e.clientX - inicio[0], e.clientY - inicio[1]) > 4) return;
  const r = renderer.domElement.getBoundingClientRect();
  raio.setFromCamera(new THREE.Vector2(((e.clientX - r.left) / r.width) * 2 - 1, -((e.clientY - r.top) / r.height) * 2 + 1), camera);
  const hit = raio.intersectObjects(grupoPecas.children, false)[0];
  selecionar(hit ? hit.object.userData.nome : null);
});

lerEscolha();
iniciar();
