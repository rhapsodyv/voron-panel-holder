"""Cross-section profiles of panel-holder-v12, as closed polygons of (s, d) expressions.

Coordinates of every profile:
  s  across the edge, 0 = slot centre, + toward the frame's outer edge (mm)
  d  height above the frame face, 0 = face, + outward, - into the slot (mm)

Each vertex is a pair of Fusion expressions written with the user parameters in parametros.py,
so the same source drives the Fusion sketch dimensions and the local checks.
"""
import math
import re

T = '( panel_frame_spacing + panel_thickness )'        # top of the acrylic
SO = '( slot_opening / 2 )'
TIP = '( slot_depth - fin_tip_clearance )'
WALL_IN = '( frame_size / 2 - wall_width )'             # inner face of the cover's outer wall
DT_IN = f'( -{SO} + panel_edge_clearance - dovetail_inset )'           # dovetail inner root
DT_IN_TOP = f'( {DT_IN} - dovetail_height * tan(dovetail_angle_in) )'
DT_OUT_TOP = f'( {DT_IN_TOP} + dovetail_top_width )'
DT_OUT = f'( {DT_OUT_TOP} - ( dovetail_height - cover_recess ) * tan(dovetail_angle_out) )'
# covers stand cover_clip_clearance off the clip's flat faces: the wall's inner face and the shoulder
WALL_FIT = f'( {WALL_IN} + cover_clip_clearance )'
REC_FIT = f'( {T} + cover_recess + cover_clip_clearance )'


# ---------------------------------------------------------------- building blocks
def _leg_right():
    """Right leg of the split fin (v11 B18), outer chain from the root down to the tip, then the inner
    chain back up to the root.

    Each leg leans out from its root by fin_lip_preload at the bottom of the slot lip (a shear, s grows
    with the depth): once in, the lip pushes it back upright, so it presses on the slot's side walls and
    the barb still sits where it would without the lean. 0 on the V0. fin_inset moves the whole leg
    toward the slot centre (legs closer together: less bend to go in and out, and as much less squeeze).
    """
    right = [
        (f'{SO} - fin_root_clearance', '0 mm'),
        (f'{SO} - fin_root_clearance', '-( slot_lip + fin_barb_gap )'),
        (f'{SO} + fin_barb', '-( slot_lip + fin_barb_gap + fin_barb_ramp )'),
        (f'{SO} + fin_barb', '-( slot_cavity_depth - fin_barb_end )'),
        ('fin_tip_half', f'-{TIP}'),
        ('fin_tip_half - fin_tip_leg', f'-{TIP}'),
        (f'{SO} - fin_root_clearance - fin_leg', '-fin_inner_straight'),
        # neck: from the root down fin_neck_length the leg is only fin_neck thick (thinned on the inside),
        # then widens at 45 deg to fin_leg; fin_neck = fin_leg: no neck (the points fall on the straight face)
        (f'{SO} - fin_root_clearance - fin_leg', '-( fin_neck_length + fin_leg - fin_neck )'),
        (f'{SO} - fin_root_clearance - fin_neck', '-fin_neck_length'),
        (f'{SO} - fin_root_clearance - fin_neck', '0 mm'),
    ]
    return [(f'( {s} ) - fin_inset - ( {d} ) * fin_lip_preload / slot_lip', d) for s, d in right]


def _split_fin():
    """Barbed split fin, right leg then the mirrored left leg, from s=+SO to s=-SO.

    fin_relief: each leg's root goes up into the base by this much, between a groove of fin_relief_gap
    outside it and the gap between the legs carried up inside it. The leg then bends over its whole
    length from up there, not only over the slot lip's thickness below the frame face (on the 2020 the
    lip is 2 mm: a 1 mm leg bent 0.3 there yields, so the barb got shaved instead of the leg flexing).
    0: the legs start at the frame face (the points collapse; the sketch skips repeated ones).
    """
    right = _leg_right()
    (s_out, _), (s_in, _) = right[0], right[-1]
    groove = f'( {s_out} ) + fin_relief_gap'
    right = [(groove, '0 mm'), (groove, 'fin_relief'), (s_out, 'fin_relief')] + right + [(s_in, 'fin_relief')]
    return right + [(f'-( {s} )', d) for s, d in reversed(right)]


def barb_cut():
    """Right-hand region a split-fin clip loses where it has no barb (between the barb stretches): all
    of the leg outside its root line, from where the barb face starts down past the tip. What is left
    is a straight leg that passes the opening freely and only locates the clip sideways. Mirror for
    the left. Same lean as _split_fin."""
    pts = [
        (f'{SO} - fin_root_clearance', '-( slot_lip + fin_barb_gap )'),
        (f'{SO} + fin_barb + 1 mm', '-( slot_lip + fin_barb_gap )'),
        (f'{SO} + fin_barb + 1 mm', f'-( {TIP} + 1 mm )'),
        (f'{SO} - fin_root_clearance', f'-( {TIP} + 1 mm )'),
    ]
    return [(f'( {s} ) - fin_inset - ( {d} ) * fin_lip_preload / slot_lip', d) for s, d in pts]


def _seg_dist(p, a, b):
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    t = 0.0 if dx == dy == 0 else max(0.0, min(1.0, ((p[0] - ax) * dx + (p[1] - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(p[0] - ax - t * dx, p[1] - ay - t * dy)


def leg_min_wall(name, vals, samples=200):
    """Thinnest wall of a split fin's leg (perpendicular, not across s): the smallest distance between
    the leg's outer chain (root, barb, tip) and its inner chain, below the frame face. Near the tip the
    leg leans in, so its wall is thinner than fin_tip_leg; a slicer drops what is thinner than its
    perimeter (fin_min_wall)."""
    right = [(evaluate(s, vals), evaluate(d, vals)) for s, d in _leg_right()]
    outer, inner = right[0:5], right[5:]

    def walk(chain):
        for a, b in zip(chain, chain[1:]):
            for i in range(samples + 1):
                yield (a[0] + (b[0] - a[0]) * i / samples, a[1] + (b[1] - a[1]) * i / samples)

    best = math.inf
    for chain, other in ((inner, outer), (outer, inner)):
        for p in walk(chain):
            if p[1] < -0.05:
                best = min(best, min(_seg_dist(p, a, b) for a, b in zip(other, other[1:])))
    return best


def _solid_fin():
    """Door fin: solid, centred, no barb, with a lead-in chamfer (door base and latch side)."""
    w = '( slot_opening / 2 - door_fin_clearance )'
    return [
        (w, '0 mm'),
        (w, f'-( {TIP} - door_fin_chamfer )'),
        (f'{w} - door_fin_chamfer', f'-{TIP}'),
        (f'-( {w} - door_fin_chamfer )', f'-{TIP}'),
        (f'-{w}', f'-( {TIP} - door_fin_chamfer )'),
        (f'-{w}', '0 mm'),
    ]


def _arc_fin():
    """Hinge-side door fin: an arc band centred on the hinge pin, so it swings into the slot.

    Polyline approximation: root on the frame face, three intermediate angles between the tip
    and -157 deg, the tip as a radial segment.
    """
    r_in = '( door_arc_outer - door_arc_thickness )'
    r_out = 'door_arc_outer'
    angles = [f'( door_arc_tip_angle + {k} * ( -157 deg - door_arc_tip_angle ) / 4 )' for k in (3, 2, 1)]

    def at(r, a):
        return (f'door_pin_s + {r} * cos( {a} )', f'door_pin_d + {r} * sin( {a} )')

    root_in = (f'door_pin_s - sqrt( {r_in} * {r_in} - door_pin_d * door_pin_d )', '0 mm')
    root_out = (f'door_pin_s - sqrt( {r_out} * {r_out} - door_pin_d * door_pin_d )', '0 mm')
    inner = [at(r_in, a) for a in angles] + [at(r_in, 'door_arc_tip_angle')]
    outer = [at(r_out, 'door_arc_tip_angle')] + [at(r_out, a) for a in reversed(angles)]
    return [root_in] + inner + outer + [root_out]


def _rib(start):
    """Base start at the frame face, then the preload rib under the acrylic."""
    return [
        (start, '0 mm'),
        (start, 'panel_frame_spacing + panel_preload - rib_inset'),
        (f'{start} + rib_inset', 'panel_frame_spacing + panel_preload'),
        (f'{start} + rib_inset + rib_width', 'panel_frame_spacing + panel_preload'),
        (f'{start} + rib_inset + rib_width + panel_preload', 'panel_frame_spacing'),
    ]


def _stop(s):
    """Edge stop of the acrylic at s."""
    return [(s, 'panel_frame_spacing'), (s, T)]


def _dovetail(shift='0 mm'):
    return [
        (f'{DT_IN} + {shift}', T),
        (f'{DT_IN_TOP} + {shift}', f'{T} + dovetail_height'),
        (f'{DT_OUT_TOP} + {shift}', f'{T} + dovetail_height'),
        (f'{DT_OUT} + {shift}', f'{T} + cover_recess'),
    ]


STOP_STD = f'-{SO} + panel_edge_clearance'
# where the base under the acrylic starts, base_inset in from the frame's inner edge (Trident: the Z carriages
# and XY joints pass right by the posts' inner edge, 0.3 past the face; 0 on the V0)
BASE_START = '-( frame_size / 2 - base_inset )'
BASE_STD = _rib(BASE_START) + _stop(STOP_STD) + _dovetail() + [(WALL_IN, f'{T} + cover_recess'), (WALL_IN, '0 mm')]

# ---------------------------------------------------------------- clips
# Standard clip (v11 B18 family): split barbed fin, base under the acrylic, edge stop, male dovetail.
CLIP_PADRAO = _split_fin() + BASE_STD

# Top of the side panels (v11 B19): the outer wall belongs to the clip, the dovetail moves out by
# top_overhang so the 4.0 cover passes beyond the frame and leaves the gap where the top hat sits.
CLIP_PAREDE = _split_fin() + _rib(BASE_START) + _stop(STOP_STD) + _dovetail('top_overhang') + [
    ('frame_size / 2', f'{T} + cover_recess'),
    ('frame_size / 2', '0 mm'),
]

# U channel without fin (v11 B20): edges with nothing behind (top of the door and of the rear).
U_START = f'( {WALL_IN} - u_base_width )'
U_STOP = f'( {WALL_IN} - u_end_wall )'
CLIP_U = _rib(U_START) + _stop(U_STOP) + _dovetail() + [(WALL_IN, f'{T} + cover_recess'), (WALL_IN, '0 mm')]

# U whose end wall, u_outer_wall thick, is the outer face (no cover wall over it), so the sheet reaches
# closer to the outer line: the Trident's door centre (no post, the two doors meet) and the V0 rear's
# bottom (both stock sheets uncut). Same base under the sheet as CLIP_U; dovetail moved by u_outer_shift.
C_STOP = '( frame_size / 2 - u_outer_wall )'
C_START = f'( {C_STOP} - ( u_base_width - u_end_wall ) )'
CLIP_U_FORA = _rib(C_START) + _stop(C_STOP) + _dovetail('u_outer_shift') + [
    ('frame_size / 2', f'{T} + cover_recess'), ('frame_size / 2', '0 mm')]

# U with a thinner end wall (u_end_wall_thin): the V0 rear's top, a little more room for the stock sheet
# while the gap above, where the top hat's sheet sits, stays as it is.
CLIP_U_FINO = _rib(U_START) + _stop(f'( {WALL_IN} - u_end_wall_thin )') + _dovetail() + [
    (WALL_IN, f'{T} + cover_recess'), (WALL_IN, '0 mm')]

# Door base (replaces v11 B21): solid centred fin, no barb; the acrylic stop sits door_stop_extra
# further out than the standard one, so the taller door panel fits (as in v11 B21).
CLIP_PORTA = _solid_fin() + _rib(BASE_START) + _stop(f'{STOP_STD} + door_stop_extra') + _dovetail() + [
    (WALL_IN, f'{T} + cover_recess'), (WALL_IN, '0 mm')]

# Door, latch side: same solid fin, standard stop.
CLIP_PORTA_LATERAL = _solid_fin() + BASE_STD

# Door, hinge side: arc fin centred on the hinge pin. The acrylic stop and the dovetail sit
# door_hinge_shift further out than the standard ones (Trident: the stock door sheet runs from the
# centre to past the slot centre); 0 on the V0.
CLIP_PORTA_DOBRADICA = _arc_fin() + _rib(BASE_START) + _stop(f'{STOP_STD} + door_hinge_shift') + \
    _dovetail('door_hinge_shift') + [(WALL_IN, f'{T} + cover_recess'), (WALL_IN, '0 mm')]

# Rear middle bar (H): holds the top edge of the lower rear sheet and the bottom edge of the upper
# one. Nothing behind it (the frame's rear bar sits 37 mm inside), so no fin. Symmetric about s = 0:
# a web of h_web between the sheets, the standard base and rib under each sheet, a centred
# dovetail for its cover. s runs across the bar, d out of the face as in every profile.
H_STOP = '( h_web / 2 )'
H_START = f'-( {H_STOP} + frame_size / 2 + {STOP_STD} )'          # base under each sheet as long as the standard one
H_ROOT = f'( {H_STOP} + dovetail_inset )'
H_TOP = f'( {H_ROOT} + dovetail_height * tan(dovetail_angle_in) )'
_H_LEFT = _rib(H_START) + [(f'-{H_STOP}', 'panel_frame_spacing'), (f'-{H_STOP}', T), (f'-{H_ROOT}', T),
                          (f'-{H_TOP}', f'{T} + dovetail_height')]
CLIP_H = _H_LEFT + [(f'-( {s} )', d) for s, d in reversed(_H_LEFT)]

# ---------------------------------------------------------------- covers
def _cover_top(shift='0 mm'):
    """Cover above the acrylic, from the outer line round to the dovetail slot (moved out by shift)."""
    return [
        ('frame_size / 2', f'{T} + cover_height - cover_cut'),
        ('frame_size / 2 - cover_cut', f'{T} + cover_height'),
        ('-( frame_size / 2 + cover_overlap ) + cover_cut', f'{T} + cover_height'),
        ('-( frame_size / 2 + cover_overlap )', f'{T} + cover_height - cover_cut'),
        ('-( frame_size / 2 + cover_overlap )', T),
        (f'{DT_IN} - dovetail_clearance + {shift}', T),
        (f'{DT_IN_TOP} - dovetail_clearance + {shift}', f'{T} + dovetail_height + dovetail_clearance'),
        (f'{DT_OUT_TOP} + dovetail_clearance + {shift}', f'{T} + dovetail_height + dovetail_clearance'),
        (f'{DT_OUT} + dovetail_clearance + {shift} + ( {DT_OUT_TOP} - {DT_OUT} ) * cover_clip_clearance / '
         f'( dovetail_height + dovetail_clearance - cover_recess )', REC_FIT),
    ]


_COVER_TOP = _cover_top() + [(WALL_FIT, REC_FIT)]

# Cover with the outer wall and the 45° corner wedge (v11 "8.3" covers)
_WEDGE = [
    (WALL_FIT, '0 mm'),
    ('frame_size / 2', '0 mm'),
    ('frame_size / 2 + wall_width / 2', 'wall_width / 2'),
    ('frame_size / 2', 'wall_width'),
]
TAMPA_PAREDE = _WEDGE + _COVER_TOP

# Door, hinge side: the same cover with the dovetail slot door_hinge_shift further out (see CLIP_PORTA_DOBRADICA)
TAMPA_PAREDE_DOBRADICA = _WEDGE + _cover_top('door_hinge_shift') + [(WALL_FIT, REC_FIT)]

# Cover with the wall but no corner wedge: bottom edges where nothing meets it (Trident: the skirt
# sits right below the frame)
TAMPA_BASE = [
    (WALL_FIT, '0 mm'),
    ('frame_size / 2', '0 mm'),
] + _COVER_TOP

# Cover without the wall (v11 "4.0" covers): top of the panels, where the top hat sits
TAMPA_SIMPLES = [('frame_size / 2', T)] + _COVER_TOP + [(WALL_FIT, T)]

# Over CLIP_U_FORA: its end wall is the outer face, so the cover has no wall and rests on it. Straight
# pieces without the wall; the corner leg carries it down to the frame face (the corner's clip cut leaves
# it only where no clip runs).
TAMPA_U_FORA = [('frame_size / 2', REC_FIT)] + _cover_top('u_outer_shift')
TAMPA_U_FORA_CANTO = [(C_STOP, '0 mm'), ('frame_size / 2', '0 mm')] + _cover_top('u_outer_shift') + [(C_STOP, REC_FIT)]

# ---------------------------------------------------------------- hinge knuckles
# The pin is the door's (door_pin_s, door_pin_d). Seen from the side panel, whose s axis is the door's
# d axis and vice versa, the same pin sits at (frame_size / 2 + door_pin_d, door_pin_s - frame_size / 2).
# Each knuckle is a block from the cover's wall out to the pin, closed on the outside by a half disc
# centred on the pin. Its radius keeps hinge_clearance from the other panel's face, so the door
# swings without the knuckles rubbing (polyline inscribed in the circle: never outside it).
PINO_PORTA = ('door_pin_s', 'door_pin_d')
PINO_LATERAL = ('( frame_size / 2 + door_pin_d )', '( door_pin_s - frame_size / 2 )')


def _knuckle(pin, radius):
    ps, pd = pin
    arc = [(f'{ps} + {radius} * cos( {a} deg )', f'{pd} + {radius} * sin( {a} deg )') for a in range(-60, 61, 30)]
    return [(WALL_FIT, '0 mm'), (ps, '0 mm'), (ps, f'{pd} - {radius}')] + arc + [(ps, f'{pd} + {radius}'), (WALL_FIT, f'{T} + cover_height')]


NO_LATERAL = _knuckle(PINO_LATERAL, '( door_pin_s - frame_size / 2 - hinge_clearance )')   # holds the screw
NO_PORTA = _knuckle(PINO_PORTA, '( door_pin_d - hinge_clearance )')                       # turns on it

# Cover of the rear middle bar: symmetric, over both sheets as far as a standard cover reaches over
# its sheet, centred dovetail slot. Made in two halves whose outer ends meet the vertical covers.
H_REACH = f'( {H_STOP} + panel_edge_clearance + frame_size / 2 + cover_overlap - {SO} )'
_TAMPA_H_LEFT = [
    (f'-{H_REACH}', T),
    (f'-{H_REACH}', f'{T} + cover_height - cover_cut'),
    (f'-{H_REACH} + cover_cut', f'{T} + cover_height'),
]
TAMPA_H = _TAMPA_H_LEFT + [(f'-( {s} )', d) for s, d in reversed(_TAMPA_H_LEFT)] + [
    (f'{H_ROOT} + dovetail_clearance', T),
    (f'{H_TOP} + dovetail_clearance', f'{T} + dovetail_height + dovetail_clearance'),
    (f'-( {H_TOP} + dovetail_clearance )', f'{T} + dovetail_height + dovetail_clearance'),
    (f'-( {H_ROOT} + dovetail_clearance )', T),
]

# One piece, clip and cover together (the user's idea, 2026-10-31; machine trident-trava, peca_unica_* params),
# printed lying with the outer face on the bed: the wall cover's outline and wedge, solid from the frame face
# up between the acrylic stop and the wall, the clip's base under the acrylic without the rib, its top
# peca_unica_vao under the cover, and the doors' solid fin (the lock holds it: construir.peca_unica_trava).
# Not in PROFILES: the other machines lack its parameters.
PECA_UNICA = _solid_fin() + [
    (BASE_START, '0 mm'),
    (BASE_START, f'{T} - peca_unica_vao'),
    (STOP_STD, f'{T} - peca_unica_vao'),
    (STOP_STD, T),
    ('-( frame_size / 2 + cover_overlap )', T),
    ('-( frame_size / 2 + cover_overlap )', f'{T} + cover_height - cover_cut'),
    ('-( frame_size / 2 + cover_overlap ) + cover_cut', f'{T} + cover_height'),
    ('frame_size / 2 - cover_cut', f'{T} + cover_height'),
    ('frame_size / 2', f'{T} + cover_height - cover_cut'),
    ('frame_size / 2', 'wall_width'),
    ('frame_size / 2 + wall_width / 2', 'wall_width / 2'),
    ('frame_size / 2', '0 mm'),
]

# Reference acrylic strip (only for checking)
ACRILICO_REF = [
    ('-( frame_size / 2 + 12 mm )', 'panel_frame_spacing'),
    (f'-{SO}', 'panel_frame_spacing'),
    (f'-{SO}', T),
    ('-( frame_size / 2 + 12 mm )', T),
]

SPLIT_FIN = ('clip-padrao', 'clip-parede')    # clips with the barbed split fin (barb stretches apply to them)

PROFILES = {
    'clip-padrao': CLIP_PADRAO,
    'clip-parede': CLIP_PAREDE,
    'clip-u': CLIP_U,
    'clip-porta': CLIP_PORTA,
    'clip-porta-lateral': CLIP_PORTA_LATERAL,
    'clip-porta-dobradica': CLIP_PORTA_DOBRADICA,
    'clip-u-fora': CLIP_U_FORA,
    'clip-u-fino': CLIP_U_FINO,
    'tampa-parede-dobradica': TAMPA_PAREDE_DOBRADICA,
    'tampa-u-fora': TAMPA_U_FORA,
    'tampa-u-fora-canto': TAMPA_U_FORA_CANTO,
    'tampa-parede': TAMPA_PAREDE,
    'tampa-simples': TAMPA_SIMPLES,
    'tampa-base': TAMPA_BASE,
    'acrilico-ref': ACRILICO_REF,
    'no-lateral': NO_LATERAL,
    'no-porta': NO_PORTA,
    'clip-h': CLIP_H,
    'tampa-h': TAMPA_H,
}


# ---------- local evaluation (same expressions, plain Python) ----------
def param_values(params):
    """Evaluate the parameter table to floats (mm, degrees)."""
    vals = {}
    for _, name, expr, unit, _ in params:
        vals[name] = evaluate(expr, vals)
    return vals


_FUNCS = {
    '_tand': lambda a: math.tan(math.radians(a)),
    '_sind': lambda a: math.sin(math.radians(a)),
    '_cosd': lambda a: math.cos(math.radians(a)),
    'sqrt': math.sqrt,
    '__builtins__': {},
}


def evaluate(expr, vals):
    py = re.sub(r'(\d)\s*(mm|deg)\b', r'\1', expr)
    py = re.sub(r'\btan\(', '_tand(', py)
    py = re.sub(r'\bsin\(', '_sind(', py)
    py = re.sub(r'\bcos\(', '_cosd(', py)
    return float(eval(py, dict(_FUNCS), dict(vals)))


def polygon(name, vals):
    return [(evaluate(s, vals), evaluate(d, vals)) for s, d in PROFILES[name]]
