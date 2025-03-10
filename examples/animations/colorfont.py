from coldtype import *

ppvf = Font.Cacheable("~/Type/fonts/fonts/PappardelleParty-VF.ttf")

custom_palette = [
    hsl(0.35, 0.7),
    hsl(0.5, 0.7),
    hsl(0.1, 0.7),
    hsl(0.9, 0.7)
]

def spin(fa, g):
    y = 100
    # address color font layers individually
    g[2].translate(0, fa.e(1, rng=(0, y)))
    g[0].translate(0, fa.e(1, rng=(0, -y)))
    g[1].rotate(fa.e(rng=(0, -360*2)))

@animation((1080, 1080), timeline=120)
def pappardelle(f):
    wave = (StSt("SPIN", ppvf, 500,
        palette=custom_palette,
        SPIN=f.e("l"))
        .align(f.a.r))

    r_wave = wave.ambit(th=1, tv=1)

    for idx, g in enumerate(wave):
        spin(f.adj(-idx*4), g)
    
    return [
        DP(r_wave.inset(-20)).f(None).s(custom_palette[2]).sw(3),
        wave.rotate(f.e(to1=1)*360, point=r_wave.pc)
    ]