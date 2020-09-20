import skia

from fontTools.pens.transformPen import TransformPen
from fontTools.misc.transform import Transform
from fontTools.pens.basePen import BasePen

from coldtype.pens.datpen import DATPen
from coldtype.geometry import Rect, Edge, Point
from coldtype.pens.drawablepen import DrawablePenMixin, Gradient
from coldtype.color import Color


class SkiaPathPen(BasePen):
    def __init__(self, dat, h):
        super().__init__()
        self.dat = dat
        self.path = skia.Path()

        tp = TransformPen(self, (1, 0, 0, -1, 0, h))
        dat.replay(tp)
    
    def _moveTo(self, p):
        self.path.moveTo(p[0], p[1])

    def _lineTo(self, p):
        self.path.lineTo(p[0], p[1])

    def _curveToOne(self, p1, p2, p3):
        self.path.cubicTo(p1[0], p1[1], p2[0], p2[1], p3[0], p3[1])

    def _qCurveToOne(self, p1, p2):
        self.path.quadTo(p1[0], p1[1], p2[0], p2[1])

    def _closePath(self):
        self.path.close()


class SkiaPen(DrawablePenMixin, SkiaPathPen):
    def __init__(self, dat, rect, canvas, style=None):
        super().__init__(dat, rect.h)

        all_attrs = list(self.findStyledAttrs(style))
        skia_paint_kwargs = dict(AntiAlias=True)
        for attrs, attr in all_attrs:
            method, *args = attr
            if method == "skp":
                skia_paint_kwargs = args[0]

        for attrs, attr in all_attrs:
            self.paint = skia.Paint(**skia_paint_kwargs)
            method, *args = attr
            if method == "skp":
                pass
            elif method == "stroke" and args[0].get("weight") == 0:
                pass
            else:
                self.applyDATAttribute(attrs, attr)
                canvas.drawPath(self.path, self.paint)
    
    def fill(self, color):
        self.paint.setStyle(skia.Paint.kFill_Style)
        if color:
            if isinstance(color, Gradient):
                self.gradient(color)
            elif isinstance(color, Color):
                self.paint.setColor(color.skia())
    
    def stroke(self, weight=1, color=None, dash=None):
        self.paint.setStyle(skia.Paint.kStroke_Style)
        if color and weight > 0:
            self.paint.setStrokeWidth(weight)
            if isinstance(color, Gradient):
                self.gradient(color)
            else:
                self.paint.setColor(color.skia())
    
    def gradient(self, gradient):
        self.paint.setShader(skia.GradientShader.MakeLinear([s[1].xy() for s in gradient.stops], [s[0].skia() for s in gradient.stops]))
    
    def Composite(pens, rect, save_to, scale=2):
        #rect = rect.scale(scale)
        surface = skia.Surface(rect.w, rect.h)
        with surface as canvas:
            SkiaPen.CompositeToCanvas(pens, rect, canvas, scale=scale)

        image = surface.makeImageSnapshot()
        image.save(save_to, skia.kPNG)
    
    def CompositeToCanvas(pens, rect, canvas, scale=1):
        def draw(pen, state, data):
            if state == 0:
                SkiaPen(pen, rect, canvas)
        
        if isinstance(pens, DATPen):
            pens = [pens]
        
        for dps in pens:
            dps.walk(draw)