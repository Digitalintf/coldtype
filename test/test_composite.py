from coldtype.test import *

#cheee = Font.Cacheable("~/Type/fonts/fonts/Eckmannpsych-Variable.ttf")
obv = Font.Cacheable("~/Type/ex1/greektown/greektown.ufo")

@animation((1000, 500), timeline=Timeline(120), bg=0)
def simple(f):
    e = f.a.progress(f.i, easefn="qeio", loops=1).e
    le = f.a.progress(f.i, easefn="linear", loops=3, cyclic=0).e
    return DATPenSet([
        #DATPen().rect(f.a.r).f(0, 0.25),
        (StyledString("WHOA",
            Style(mutator, 250, wdth=1-e, wght=e, ro=1))
            .pen()
            .align(f.a.r)
            .rotate(360*le)
            .f(1)
            .f(hsl(le, s=1))
            .s(0).sw(5))])#.blendmode(skia.BlendMode.kLighten)

@animation((1200, 800), timeline=Timeline(90), bg=1, composites=1, rstate=1, solo=1)
def interpolation(f, rs):
    e = f.a.progress(f.i, easefn="qeio", loops=1).e
    le = f.a.progress(f.i, easefn="linear", loops=1, cyclic=False).e
    #rs.callback = -1

    return DATPenSet([
        DATPen().rect(f.a.r).f(1),
        interpolation.last_result.copy().translate(2, -2) if interpolation.last_result else None,
        (StyledString("P",
            Style(co, 500-e*300, wdth=1, slnt=e, ro=1, tu=0))
            .pen()
            .mod_contour(1, lambda p: p.rotate(-360*le))
            .align(f.a.r, x="mnx")
            .translate(30+790*e, 100)
            #.rotate()
            .f(1)
            .s(0).sw(10))
            ]).color_phototype(f.a.r, blur=5, cut=135, cutw=15)