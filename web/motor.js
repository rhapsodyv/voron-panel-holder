// The configurator's engine, a module Web Worker: Pyodide with the packages pinned in pyodide-lock.json (build123d and
// OCP.wasm, the OpenCascade compiled to WebAssembly), the generator files of gerador/arquivos.json and motor.py.
// Messages in: {id, acao, args}; out: {tipo: 'etapa' | 'log' | 'pronto' | 'falha' | 'resposta' | 'erro', ...}.
import { loadPyodide } from 'https://cdn.jsdelivr.net/pyodide/v314.0.7/full/pyodide.mjs';

const RAIZ = '/home/pyodide/web';
const t0 = performance.now();
const seg = () => ((performance.now() - t0) / 1000).toFixed(1);
const msg = (tipo, dados = {}) => postMessage({ tipo, ...dados });
let motor = null;
self.addEventListener('unhandledrejection', (e) => msg('falha', { texto: String(e.reason && e.reason.message || e.reason) }));
self.addEventListener('error', (e) => msg('falha', { texto: String(e.message || e) }));

async function iniciar() {
  msg('etapa', { texto: 'Loading Python (Pyodide)…' });
  const trava = new URL('pyodide-lock.json', location.href).href;
  const py = await loadPyodide({ lockFileURL: trava, stdout: (s) => msg('log', { texto: s }), stderr: (s) => msg('log', { texto: s }) });
  msg('etapa', { texto: `Python ready in ${seg()} s.` });
  py.setStdout({ batched: (s) => msg('log', { texto: s }) });
  py.setStderr({ batched: (s) => msg('log', { texto: s }) });
  const nomes = Object.keys((await (await fetch(trava)).json()).packages).filter((n) => n !== 'micropip');
  msg('etapa', { texto: `Loading ${nomes.length} packages (about 60 MB on the first visit)…` });
  await py.loadPackage(nomes, { messageCallback: (s) => msg('log', { texto: s }), errorCallback: (s) => msg('log', { texto: s }) });
  msg('etapa', { texto: 'Copying the generator…' });
  const arquivos = await (await fetch('gerador/arquivos.json')).json();
  await Promise.all(['motor.py', ...arquivos].map(async (a) => {
    const dados = new Uint8Array(await (await fetch(a)).arrayBuffer());
    py.FS.mkdirTree(RAIZ + '/' + a.split('/').slice(0, -1).join('/'));
    py.FS.writeFile(RAIZ + '/' + a, dados);
  }));
  py.runPython(`import sys\nsys.path.insert(0, '${RAIZ}')`);
  for (const [mod, texto] of [['OCP.TopoDS', 'Loading OpenCascade…'], ['build123d', 'Loading build123d…'], ['motor', 'Loading the generator…']]) {
    msg('etapa', { texto: `${texto} (${seg()} s)` });
    await py.runPythonAsync(`import ${mod}`);
  }
  motor = py.globals.get('motor');
  msg('log', { texto: `generator loaded (${seg()} s)` });
  msg('pronto', { catalogo: JSON.parse(motor.catalogo()), tempo: seg() });
}

// a Python dict with bytes inside -> a JS object with Uint8Arrays, and the buffers to transfer
function paraJs(proxy) {
  const js = proxy.toJs({ dict_converter: Object.fromEntries, create_proxies: false });
  proxy.destroy();
  const buffers = [];
  (function junta(o) {
    if (o instanceof Uint8Array) buffers.push(o.buffer);
    else if (Array.isArray(o)) o.forEach(junta);
    else if (o && typeof o === 'object') Object.values(o).forEach(junta);
  })(js);
  return [js, buffers];
}

const fila = [];
let ocupado = false;
onmessage = (e) => { fila.push(e.data); proximo(); };

async function proximo() {
  if (ocupado || !motor || !fila.length) return;
  ocupado = true;
  const { id, acao, args } = fila.shift();
  try {
    if (acao === 'montar') {
      const [js, buffers] = paraJs(motor.montar_face(...args));
      postMessage({ tipo: 'resposta', id, resultado: js }, buffers);
    } else if (acao === 'zip') {
      const [js, buffers] = paraJs(motor.zip_face(...args));
      postMessage({ tipo: 'resposta', id, resultado: js }, buffers);
    } else if (acao === 'conferir' || acao === 'avaliar') {
      const f = acao === 'conferir' ? motor.conferir_face : motor.avaliar;
      postMessage({ tipo: 'resposta', id, resultado: JSON.parse(f(...args)) });
    } else {
      throw new Error('unknown action: ' + acao);
    }
  } catch (err) {
    // a Python error: its last line (the exception) is what the user needs
    const linhas = String(err.message || err).trim().split('\n');
    postMessage({ tipo: 'erro', id, texto: linhas[linhas.length - 1], completo: String(err.message || err) });
  }
  ocupado = false;
  proximo();
}

iniciar().then(proximo).catch((err) => msg('falha', { texto: String(err.message || err) }));
