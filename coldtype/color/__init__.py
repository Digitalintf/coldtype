from random import random
from fontTools.ttLib.tables.C_P_A_L_ import Color as FTCPALColor
from coldtype.color.color import Color


def lighten_max(color, maxLightness=0.55):
    return Color.from_hsl(color.h, color.s, max(maxLightness, color.l))


def color_var(*rgba):
    c = [random() if x == -1 or x == "random" or x == "rand" or x == "R" else x for x in rgba]
    if len(c) == 1:
        return Color.from_rgb(c[0], c[0], c[0])
    elif len(c) == 2:
        return Color.from_rgb(c[0], c[0], c[0], c[1])
    elif len(c) == 3:
        return Color.from_rgb(c[0], c[1], c[2])
    elif len(c) == 4:
        return Color.from_rgb(c[0], c[1], c[2], c[3])


def hex_to_tuple(h):
    return tuple([c/255 for c in (palette.r, palette.g, palette.b, palette.a)])


def normalize_color(v):
    if v is None:
        return Color.from_rgb(0,0,0,0)
    elif isinstance(v, Color):
        return v
    elif isinstance(v, Gradient):
        return v
    elif isinstance(v, float) or isinstance(v, int):
        return Color.from_rgb(v, v, v)
    elif isinstance(v, FTCPALColor):
        return Color.from_rgb(v.red/255, v.green/255, v.blue/255, v.alpha/255)
    elif isinstance(v, str):
        if v == "random" or v == -1:
            return Color.from_rgb(random(), random(), random())
        elif v == "none":
            return Color.from_rgb(0,0,0,0)
        else:
            return Color.from_html(v)
    else:
        if len(v) == 1:
            if v[0] == "random":
                return Color.from_rgb(random(), random(), random(), 1)
            if v[0] == None:
                return Color.from_rgb(0,0,0,0)
            elif isinstance(v[0], str):
                return Color.from_html(v[0])
            elif isinstance(v[0], Gradient):
                return v[0]
            else:
                try:
                    iter(v[0])
                    return normalize_color(v[0])
                except TypeError:
                    return Color.from_rgb(v[0], v[0], v[0])
        elif len(v) == 2:
            if v[0] == "random" or v[0] == -1:
                return Color.from_rgb(random(), random(), random(), float(v[1]))
            elif isinstance(v[0], str):
                return Color.from_html(v[0]).with_alpha(v[1])
            else:
                c = Color.from_rgb(v[0], v[0], v[0], v[1])
                return c
        else:
            if hasattr(v[0], "imag"):
                return Color.from_hsl(v[0].imag, *v[1:])
            else:
                vs = [random() if _v == "random" else _v for _v in v]
                return Color.from_rgb(*vs)


class Gradient():
    def __init__(self, *stops):
        self.stops = []
        for c, p in stops:
            self.addStop(c, p)
    
    def addStop(self, color, point):
        self.stops.append([normalize_color(color), point])
    
    def Vertical(rect, a, b):
        return Gradient([a, rect.point("N")], [b, rect.point("S")])
    
    def Horizontal(rect, a, b):
        return Gradient([a, rect.point("E")], [b, rect.point("W")])
    
    def Random(rect, opacity=0.5):
        return Gradient([("random", opacity), rect.point("SE")], [("random", opacity), rect.point("NW")])