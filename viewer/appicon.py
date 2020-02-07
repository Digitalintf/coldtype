from coldtype import *
from coldtype.color import Gradient, normalize_color
from functools import partial

def mod_o(idx, dp):
    if dp.glyphName == "O":
        # push the counter over a little for balance
        o_outer, o_counter = dp.explode()
        return o_outer.record(o_counter.translate(20, 0))

def render_icon(size):
    fill = normalize_color((0.3, 0.1, 0.5))
    grade = Gradient.Horizontal(page, (0.75, 0.1, 0.3), fill)
    outline = 15
    oval = DATPen().f(grade).oval(page.inset(15))
    if size <= 128:
        st = Style("ç/variable_ttf/ColdtypeObviously-VF.ttf", 700, slnt=1, wght=1, wdth=1, fill=1, reverse=1, t=-30, bs=[50,-50], ro=1)
        pen = Slug("CT", st).pens().align(page, th=1, tv=1)
        return oval, pen.interleave(lambda p: p.outline(outline).f(grade))
    else:
        s = Style("ç/variable_ttf/ColdtypeObviously-VF.ttf", 500, fill=1, tu=-70, wdth=0.9, overlap_outline=outline, kern_pairs={("C","O"):-90, ("O","L"):-78, ("T","Y"):-90, ("Y","P"):-20, ("P","E"):-247}, r=1, ro=1)
        dps = Graf([StyledString(t, s) for t in ["COLD", "TYPE"]], page.inset(90, 0), leading=10).fit().pens().reversePens().mmap(lambda idx, dps: dps.translate([80, -90][idx], 0)).flatten().map(mod_o).interleave(lambda p: p.outline(outline).f(grade)).scale(0.9, center=False).align(page)
        return oval, dps

page = Rect(1024, 1024)
renders = [
    partial(render_icon, 128),
    partial(render_icon, 1024)
]