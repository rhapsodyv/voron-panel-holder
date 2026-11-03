# Voron panel holder

Printable holders for the acrylic panels of the **Voron V0.2** and the **Voron Trident 350**. They are made for the stock
panels and the frame's extrusion slots, with no cutting.

**Configurator: <https://rhapsodyv.github.io/voron-panel-holder/>**

Pick the printer and the panel to see the parts on the frame in 3D. You can check them for collisions and download the
STLs. With the default values every panel is ready at once. If you change a parameter (panel thickness, slot opening,
print clearances…), the parts are generated in your browser. The first change loads the CAD engine, which takes about a
minute.

## Designs

| Design | Parts | V0.2 | Trident 350 |
|---|---|---|---|
| Clips | clips in the extrusion slot, covers over them, corners (door hinges and handle included) | all panels | all panels |
| Clips with lock | the same, with a sliding lock on the covers | all panels | all panels |
| One-piece | clip and cover in one part, printed lying, always with the sliding lock | top hat sides (front without the logo yet) | sides, rear and top; the doors use the clips with lock |

## Repository

| Folder | What is in it |
|---|---|
| [`gerador/`](gerador) | The generators, in Python with [build123d](https://github.com/gumyr/build123d). Each machine has a folder with its parameters, part map and design notes. |
| [`web/`](web) | The configurator: a static site that runs the same generators in the browser. It uses [Pyodide](https://pyodide.org) and [OCP.wasm](https://github.com/yeicor/OCP.wasm). |
| [`stl/`](stl) | Only the printed lock kits' files (slider, cap, indicator), which the one-piece generators reuse as they are. The exported parts are not in the repository: download them from the configurator, or generate them. |
| [`ideias-trava/`](ideias-trava) | Drawings from the lock's design. |

The design notes, the READMEs inside the folders and the `LEIA-ME` files are in Portuguese.

## Running it locally

```bash
python3 -m venv .venv-b3d && .venv-b3d/bin/pip install build123d shapely matplotlib
```

```bash
.venv-b3d/bin/python gerador/clips_b3d.py trident face lateral-direita
```

That builds a panel, checks it on the frame and exports its STLs to a new folder in `stl/`. The machines are `v0`, `v0-trava`, `trident` and
`trident-trava`. The one-piece designs are in `gerador/peca_unica_b3d.py` (Trident) and `gerador/peca_unica_v0_b3d.py`
(V0). The configurator runs from `web/`; see [`web/README.md`](web/README.md).

Pushes to `main` publish `web/` on GitHub Pages (`.github/workflows/pages.yml`). Before pushing a generator or parameter
change, run `.venv-b3d/bin/python web/motor.py pre-gerar` to remake the ready-made panels in `web/pre/`.

## License

[MIT](LICENSE): the code, the STLs and the rest of this repository are free to use, change, share and sell. The only
condition is to keep the copyright notice, so please credit this project and link back here when you share a remix.
The Voron name and logo belong to Voron Design.
