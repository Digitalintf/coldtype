from coldtype.test import *

tl = Timeline(26, fps=23.976, storyboard=[0])

def find_workarea(self):
    return [0, 1, 2]

Timeline.find_workarea = find_workarea

recmono = Font("viewer/assets/RecMono-CasualItalic.ttf")

@animation(rect=(1920, 1080), timeline=tl)
def render(f):
    pe = f.a.t.progress(f.i, loops=1, easefn="qeio").e
    return DATPenSet([
        (StyledString(chr(65+f.i),
            Style(mutator, 1000, wdth=1-pe))
            .pen()
            .f(hsl(pe, s=0.6, l=0.6))
            .align(f.a.r)),
        (StyledString("{:02d}".format(f.i),
            Style(recmono, 50, wdth=1))
            .pens()
            .align(f.a.r.take(100, "mny"), th=0))
    ])