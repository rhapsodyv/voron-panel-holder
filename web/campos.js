// What the page shows in English: the parameters a user is meant to change (the rest of each machine's table are design
// decisions, listed under Advanced by their generator names), the machines' and faces' names, and the checks' phrases.

const CLIPS = ['v0', 'v0-trava', 'trident', 'trident-trava'];
const TRAVA = ['v0-trava', 'trident-trava'];
const PU = ['trident-peca-unica', 'v0-peca-unica'];

// The one-piece machines take few: their lock's slider and cap are the printed kits' (the generator copies their files),
// so a change to the slot, the panel's height or the clips' fit would no longer match them.
export const CAMPOS = [
  { grupo: 'Panel and frame', nome: 'panel_thickness', rotulo: 'Panel thickness', em: CLIPS,
    ajuda: 'Measured thickness of the panel sheets (acrylic).' },
  { grupo: 'Panel and frame', nome: 'panel_frame_spacing', rotulo: 'Panel distance from the frame', em: CLIPS,
    ajuda: 'How far the panel sits off the extrusion face, on the clip\'s base.' },
  { grupo: 'Panel and frame', nome: 'slot_opening', rotulo: 'Slot opening', em: CLIPS,
    ajuda: 'Measured opening of the extrusion\'s slot (Trident 2020: 6.35 measured, 6.0 in the CAD; V0 1515: 3.0).' },
  { grupo: 'Panel and frame', nome: 'panel_edge_clearance', rotulo: 'Panel edge clearance', em: CLIPS,
    ajuda: 'Gap between the panel\'s edge and the clip\'s stop.' },
  { grupo: 'Panel and frame', nome: 'peca_unica_vao', rotulo: 'Panel pocket height', em: PU,
    ajuda: 'The slot the panel slides into, from the cover down to the base under the panel: the panel\'s thickness and its ' +
      'clearance. Printed lying, keep it on a 0.2 mm layer boundary (3.0 for 2.7 mm panels).' },
  { grupo: 'Print fit', nome: 'fin_inset', rotulo: 'Clip leg inset', em: CLIPS,
    ajuda: 'Moves each leg of the clip\'s fin toward the slot\'s centre, per side: more is easier to push in and pull out, and holds less.' },
  { grupo: 'Print fit', nome: 'dovetail_clearance', rotulo: 'Cover dovetail clearance', em: CLIPS,
    ajuda: 'Per flank, between the cover and the clip\'s dovetail it slides onto.' },
  { grupo: 'Print fit', nome: 'cover_clip_clearance', rotulo: 'Cover to clip clearance', em: CLIPS,
    ajuda: 'On the clip\'s flat faces under the cover: its wall and its shoulder.' },
  { grupo: 'Print fit', nome: 'door_fin_clearance', rotulo: 'Solid fin clearance', em: [...CLIPS, ...PU],
    ajuda: 'Per side, the solid fin in the slot: the doors\' clips, and the one-piece corners.' },
  { grupo: 'Print fit', nome: 'hinge_hole_side', rotulo: 'Hinge hole, side panel', em: [...CLIPS, 'trident-peca-unica'],
    ajuda: 'The M3 hinge screw threads into the plastic here.' },
  { grupo: 'Print fit', nome: 'hinge_hole_door', rotulo: 'Hinge hole, door', em: [...CLIPS, 'trident-peca-unica'],
    ajuda: 'The door turns freely on the M3 screw.' },
  { grupo: 'Print fit', nome: 'bed_chamfer', rotulo: 'Bed chamfer', em: [...CLIPS, 'trident-peca-unica'],
    ajuda: 'Chamfer on the edges that touch the print bed, against elephant\'s foot (0: none).' },
  { grupo: 'Lock', nome: 'trava_folga_toco', rotulo: 'Cap fit', em: TRAVA,
    ajuda: 'Clearance of the cap\'s socket on the slider\'s dovetail.' },
  { grupo: 'Lock', nome: 'trava_orelha_comprimento', rotulo: 'Slider brim tab', em: TRAVA,
    ajuda: 'Length of the one-layer tab that holds the slider on the bed; snap it off before assembly (0: none).' },
  { grupo: 'Print support', nome: 'suporte_lamina_contato', rotulo: 'Single-layer edge', em: PU,
    ajuda: 'Within this distance of the part the support\'s bridge stays one layer thick, so it snaps off cleanly.' },
  { grupo: 'Print support', nome: 'suporte_folga', rotulo: 'Support gap', em: PU,
    ajuda: 'Gap between the support\'s wall and the part.' },
];

export const MAQUINAS = {
  'v0': 'Voron V0.2',
  'v0-trava': 'Voron V0.2 with lock',
  'trident': 'Voron Trident 350',
  'trident-trava': 'Voron Trident 350 with lock',
  'trident-peca-unica': 'Voron Trident 350, one-piece',
  'v0-peca-unica': 'Voron V0.2, one-piece (top hat sides)',
};

export const FACES = {
  'lateral-direita': 'Right side', 'lateral-esquerda': 'Left side', 'traseira': 'Rear', 'topo': 'Top', 'porta': 'Door',
  'porta-direita': 'Right door', 'porta-esquerda': 'Left door', 'tophat-frente': 'Top hat, front', 'tophat-tras': 'Top hat, rear',
  'tophat-direita': 'Top hat, right', 'tophat-esquerda': 'Top hat, left', 'tophat-tampo': 'Top hat, lid',
};

// the checks' phrases, as the generators write them
export const TERMOS = [
  ['orelha do cursor (sai antes de montar)', 'slider\'s brim tab in the cap (snapped off before assembly)'],
  ['aleta apertando a aba do rasgo', 'fin pressing the slot\'s lip'],
  ['nervura na peça que faz as vezes da chapa', 'rib on the part that stands in for the sheet'],
  ['travado × frame (o aperto do gancho)', 'locked × frame (the hook\'s squeeze)'],
  ['travado × capa (a orelha do cursor passa por ela)', 'locked × cap (the slider\'s brim tab passes through it)'],
  ['acrílico (borda no batente) × peça', 'acrylic (edge at the stop) × part'],
  ['acrílico × capa aberta e travada', 'acrylic × cap, open and locked'],
  ['acrílico × cursor no curso', 'acrylic × slider along its travel'],
  ['entrando por baixo × peça', 'going in from below × part'],
  ['peca entrando × frame', 'part going in × frame'],
  ['capa aberta × peça', 'cap open × part'],
  ['capa travada × peça', 'cap locked × part'],
  ['travado × peça', 'locked × part'],
  ['aberto × frame', 'open × frame'],
  ['aberto × peça', 'open × part'],
  ['entrando × frame', 'going in × frame'],
  ['curso × peça', 'travel × part'],
  ['peca × frame', 'part × frame'],
];
export const GRUPOS_CONFERENCIA = {
  frame: 'frame, in place', frame_entrando: 'frame, going in straight', cunhas: 'neighbour faces\' wedges',
  cunhas_entrando: 'wedges, going in', entre_pecas: 'between the parts', 'acrílico': 'acrylic', faces_vizinhas: 'neighbour faces',
  faces_vizinhas_entrando: 'neighbour faces, going in', trava: 'lock (slider, cap, travel)',
};
export function traduzir(texto) {
  let s = String(texto);
  for (const [pt, en] of TERMOS) s = s.split(pt).join(en);
  return s;
}
