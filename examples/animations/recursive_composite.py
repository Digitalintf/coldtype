from coldtype import *
from coldtype.fx.skia import fill, phototype

@animation((1080, 1080), timeline=90, composites=1)
def recursive_composite(f):
    return (DPS([
        f.last_render(lambda p: p
            .translate(1, -2)
            .scale(0.997)
            .ch(fill(1))),
        (DP(Rect(200, 200))
            .align(f.a.r.inset(100, 100), "mnx", "mxy")
            .rotate(f.e("eeio")*-360)
            .translate(f.a.r.w*0.6*f.e("ceio", 1), 0)
            .f(0).s(1).sw(10) # invert for phototype
            )])
        .ch(phototype(f.a.r,
            fill=hsl(0.90, 0.8), blur=3, cut=133, cutw=30)))