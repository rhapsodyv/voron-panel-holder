"""Geometry of the sliding lock (mm), without Fusion: shared by construir (the coupon and the production
pieces) and the machine maps that place the locks (gerador/v0-trava/mapa.py)."""


def geo(v):
    """Lock coupon geometry in mm, piece frame (s across, d out of the face, z along), shared by
    trava_deslizante and trava_conferir. Everything is placed open; slider and cap slide trava_curso
    toward +z to lock. The slider goes in from below (the frame side, the panel off the printer) at the
    open position, the tongue through the window without legs, the neck up through the slots. It prints
    on its rear end (z = z0), so the neck starts flush with the tongue's rear end, and the stub's rear
    flank comes down at 45 deg from its foot to the bed, and the rest of its rear end lies flat on the bed
    (a dovetail flank leaning less than 45 deg would hang over it). Above the clip's base the neck can
    grow outward over the outer leg's root (wo, the V0's); it goes in through the base where the window
    has no legs (furo)."""
    so = v['slot_opening'] / 2
    inner = so - v['fin_root_clearance'] - v['fin_leg'] - v.get('fin_inset', 0.0)   # legs' inner faces
    T = v['panel_frame_spacing'] + v['panel_thickness']
    w = inner - v['trava_folga_lingueta']                                 # the tongue's half width
    z0, lk, hc, c = v['trava_inicio'], v['trava_lingueta'], v['trava_haste_comprimento'], v['trava_curso']
    # teeth (trava_dentes > 0, the one-piece v4): the tongue is trava_dentes teeth trava_dente long at full width,
    # with 45 deg ramps trava_dente_degrau deep at both ends, narrower between them. Open, each tooth sits in a
    # recess of the legs, trava_dente_folga clear at each end; locked, on the barb after it, the barb that much
    # longer at each end. So the travel is half the teeth's pitch and both follow from the tooth
    n = int(round(v.get('trava_dentes', 0)))
    if n > 0:
        a, r, m = v['trava_dente'], v['trava_dente_degrau'], v['trava_dente_folga']
        c = a + r + 2 * m
        lk = (n - 1) * 2 * c + a + 2 * r
    dentes = [(z0 + 2 * c * i, z0 + 2 * c * i + v['trava_dente'] + 2 * v['trava_dente_degrau']) for i in range(n)]
    fr, m, fl, kr = v['trava_folga_rasgo'], v['trava_capa_sobra'], v['trava_toco_aba'], v['trava_toco_aba_tras']
    hz = (z0, z0 + hc)                                                    # neck, from the tongue's rear end
    zc = (hz[0] + hz[1]) / 2
    tz = (z0 + kr, z0 + v['trava_toco_comprimento'])                      # stub's foot; its rear point is back at z0
    # the neck's slot, open to locked, and long enough for the stub's flared top to come up through
    # it at the open position
    path = (min(hz[0], tz[0] - kr) - fr, max(hz[1] + c, tz[1] + fl) + fr)
    # middle of the cover's flat top; trava_capa_desloc (0 unless a variant sets it) moves the cap and the dot
    # out with a cover placed further out than the slot (the V0 sides' top edge: tampa-simples, top_overhang)
    ctr = -v['cover_overlap'] / 2 + v.get('trava_capa_desloc', 0.0)
    tl = v['trava_toco_largura']                                         # stub's width from the outer side (wo)
    # the slots; the neck is flush with the tongue on +s, unless trava_pescoco_desloc moves it out (the one-piece v5)
    pd = v.get('trava_pescoco_desloc', 0.0)
    hs = (w - v['trava_haste'] + pd, w + pd)
    fz = (path[0], max(hz[1], tz[1] + fl) + fr)                           # the neck and the stub, open, through the base
    cap_z = (path[0] - c - m, path[1] + m)                                # the cap covers the slot past both ends, open and locked
    win = (z0 - v['trava_folga_janela'], z0 + lk + v['trava_folga_janela'])
    sb = v['trava_farpa_sobra']
    return dict(
        so=so, inner=inner, T=T, w=w, z0=z0, lk=lk, c=c, hz=hz, zc=zc, tz=tz, kr=kr, path=path, tl=tl, dentes=dentes,
        # the tongue's sides: centred, or trava_lingueta_desloc out (+s), off the neck (the one-piece v5, one leg);
        # trava_lingueta_alarga widens only the outer side (v6: against the outer lip)
        lingueta=(-w + v.get('trava_lingueta_desloc', 0.0), w + v.get('trava_lingueta_desloc', 0.0) + v.get('trava_lingueta_alarga', 0.0)),
        top=T + v['cover_height'],
        hs=hs,
        # above the step (dg, trava_folga_degrau over the clip's base) the neck's outer face is at wo
        wo=hs[0] + v['trava_pescoco_largura'], dg=v['panel_frame_spacing'] + v['trava_folga_degrau'], furo=fz,
        fh=v['trava_folga_haste'],                                        # the neck and the stub are this narrower a side
        win=win,
        gap=T + v['cover_height'] + v['trava_folga_capa'],                # cap's underside, stub's base
        cap_z=cap_z,
        cap_s=(ctr - v['trava_capa_largura'] / 2, ctr + v['trava_capa_largura'] / 2),
        # the clip's barb only where the tongue sits locked (and never over the window)
        farpa=(max(z0 + c - sb, win[1]), min(z0 + c + lk + sb, v['trava_comprimento'])),
        # the dot on the cover: in front of the open cap, mid-travel, so the locked cap hides it
        ind=(ctr, cap_z[1] + c / 2),
        # the stretch of clip the lock changes (open or locked), from where the legs come back at 45 deg
        # under the window and the neck's slot leans back at 45 deg, to the end of the barb under the locked
        # tongue: the production pieces keep it off the clip joints
        trecho=(min(win[0] - v['slot_depth'] - 1, path[0] - (T + v['dovetail_height'] + 1 - v['panel_frame_spacing'])),
                min(z0 + c + lk + sb, v['trava_comprimento'])),
    )
