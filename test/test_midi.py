from coldtype.test import *
from coldtype.animation.midi import *


reader = MidiReader(Path("assets/loop.mid").resolve(), bpm=120)


@animation(duration=60, storyboard=[0, 17], bg=0.1)
def test_midi_read(f):
    drums = reader[0]
    kick = drums.fv(f.i, [36], all=1)
    snare = drums.fv(f.i, [38], [5, 20])
    hat = drums.fv(f.i, [42], [3, 10])
    cowbell = drums.fv(f.i, [49], [3, 10])

    style = Style(co, 500, tu=-150, r=1, ro=1)
    print(">>>", snare.ease())
    cold_pens = StyledString("COLD", style.mod(wdth=1-snare.ease())).pens()
    type_pens = StyledString("TYPE", style.mod(rotate=15*hat.ease(eo="eei"))).pens()

    one_kick = kick.count < 2
    cold_pens.f(0.6j if one_kick else 0.75j, 0.75, 0.5)
    type_pens.f(0.05j if one_kick else 0.9j, 0.75, 0.5)

    def mod_p(idx, dp):
        if dp.glyphName == "P":
            o = dp.explode()
            o[1].translate(50*cowbell.ease(), 0)
            return o.implode()
    
    type_pens.map(mod_p) # move the p counter over

    r = f.a.r.inset(0, 150)
    return [
        cold_pens.align(r, y="maxy").understroke(sw=10),
        type_pens.align(r, y="miny").understroke(sw=10)
    ]
