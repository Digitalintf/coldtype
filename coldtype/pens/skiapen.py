import skia, struct

from coldtype.pens.skiapathpen import SkiaPathPen
from coldtype.pens.datpen import DATPen, DATPens
from coldtype.pens.dattext import DATText
from coldtype.img.datimage import DATImage
from coldtype.geometry import Rect, Point
from coldtype.pens.drawablepen import DrawablePenMixin, Gradient
from coldtype.color import Color
from coldtype.text.reader import Style


class SkiaPen(DrawablePenMixin, SkiaPathPen):
    def __init__(self, dat, rect, canvas, scale, style=None, alpha=1):
        super().__init__(dat, rect.h)
        self.scale = scale
        self.canvas = canvas
        self.rect = rect
        self.blendmode = None
        self.style = style
        self.alpha = alpha

        all_attrs = list(self.findStyledAttrs(style))
        skia_paint_kwargs = dict(AntiAlias=True)
        for attrs, attr in all_attrs:
            method, *args = attr
            if method == "skp":
                skia_paint_kwargs = args[0]
                if "AntiAlias" not in skia_paint_kwargs:
                    skia_paint_kwargs["AntiAlias"] = True
            elif method == "blendmode":
                self.blendmode = args[0].to_skia()

        for attrs, attr in all_attrs:
            filtered_paint_kwargs = {}
            for k, v in skia_paint_kwargs.items():
                if not k.startswith("_"):
                    filtered_paint_kwargs[k] = v
            self.paint = skia.Paint(**filtered_paint_kwargs)
            if self.blendmode:
                self.paint.setBlendMode(self.blendmode)
            method, *args = attr
            if method == "skp":
                pass
            elif method == "skb":
                pass
            elif method == "blendmode":
                pass
            elif method == "stroke" and args[0].get("weight") == 0:
                pass
            elif method == "dash":
                pass
            else:
                canvas.save()
                did_draw = self.applyDATAttribute(attrs, attr)
                self.paint.setAlphaf(self.paint.getAlphaf()*self.alpha)
                if not did_draw:
                    canvas.drawPath(self.path, self.paint)
                canvas.restore()
    
    def fill(self, color):
        self.paint.setStyle(skia.Paint.kFill_Style)
        if color:
            if isinstance(color, Gradient):
                self.gradient(color)
            elif isinstance(color, Color):
                self.paint.setColor(color.skia())
    
    def stroke(self, weight=1, color=None, dash=None):
        self.paint.setStyle(skia.Paint.kStroke_Style)
        if dash:
            self.paint.setPathEffect(skia.DashPathEffect.Make(*dash))
        if color and weight > 0:
            self.paint.setStrokeWidth(weight*self.scale)
            if isinstance(color, Gradient):
                self.gradient(color)
            else:
                self.paint.setColor(color.skia())
    
    def gradient(self, gradient):
        self.paint.setShader(skia.GradientShader.MakeLinear([s[1].flip(self.rect).xy() for s in gradient.stops], [s[0].skia() for s in gradient.stops]))
    
    def image(self, src=None, opacity=1, rect=None, pattern=True):
        if isinstance(src, skia.Image):
            image = src
        else:
            image = skia.Image.MakeFromEncoded(skia.Data.MakeFromFileName(str(src)))

        if not image:
            print("image <", src, "> not found, cannot be used")
            return
        
        _, _, iw, ih = image.bounds()
        
        if pattern:
            matrix = skia.Matrix()
            matrix.setScale(rect.w / iw, rect.h / ih)
            self.paint.setShader(image.makeShader(
                skia.TileMode.kRepeat,
                skia.TileMode.kRepeat,
                matrix
            ))
        
        if opacity != 1:
            tf = skia.ColorFilters.Matrix([
                1, 0, 0, 0, 0,
                0, 1, 0, 0, 0,
                0, 0, 1, 0, 0,
                0, 0, 0, opacity, 0
            ])
            cf = self.paint.getColorFilter()
            if cf:
                self.paint.setColorFilter(skia.ColorFilters.Compose(
                    tf, cf))
            else:
                self.paint.setColorFilter(tf)
        
        if not pattern:
            bx, by, bw, bh = self.path.getBounds()
            if rect:
                bx, by = rect.flip(self.rect.h).xy()
                #bx += rx
                #by += ry
            sx = rect.w / iw
            sy = rect.h / ih
            self.canvas.save()
            #self.canvas.setMatrix(matrix)
            self.canvas.clipPath(self.path, doAntiAlias=True)
            if False:
                self.canvas.scale(sx, sy)
            else:
                # TODO scale the image, or maybe that shouldn't be here? this scaling method is horrible for image quality
                self.canvas.scale(sx, sy)
            was_alpha = self.paint.getAlphaf()
            self.paint.setAlphaf(was_alpha*self.alpha)
            self.canvas.drawImage(image, bx/sx, by/sy, self.paint)
            self.paint.setAlphaf(was_alpha)
            self.canvas.restore()
            return True
    
    def shadow(self, clip=None, radius=10, color=Color.from_rgb(0,0,0,1)):
        #print("SHADOW>", self.style, clip, radius, color)
        if clip:
            if isinstance(clip, Rect):
                skia.Rect()
                sr = skia.Rect(*clip.scale(self.scale, "mnx", "mny").flip(self.rect.h).mnmnmxmx())
                self.canvas.clipRect(sr)
            elif isinstance(clip, DATPen):
                sp = SkiaPathPen(clip, self.rect.h)
                self.canvas.clipPath(sp.path, doAntiAlias=True)
        self.paint.setColor(skia.ColorBLACK)
        self.paint.setImageFilter(skia.ImageFilters.DropShadow(0, 0, radius, radius, color.skia()))
        return
    
    def Composite(pens, rect, save_to, scale=1, context=None, style=None):
        rect = rect.scale(scale).round()

        if context:
            info = skia.ImageInfo.MakeN32Premul(rect.w, rect.h)
            surface = skia.Surface.MakeRenderTarget(context, skia.Budgeted.kNo, info)
        else:
            #print("CPU RENDER")
            surface = skia.Surface(rect.w, rect.h)
        
        with surface as canvas:
            if callable(pens):
                pens(canvas) # direct-draw
            else:
                SkiaPen.CompositeToCanvas(pens, rect, canvas, scale=scale, style=style)

        image = surface.makeImageSnapshot()
        image.save(save_to, skia.kPNG)
    
    def PDFOnePage(pens, rect, save_to, scale=1):
        stream = skia.FILEWStream(str(save_to))
        with skia.PDF.MakeDocument(stream) as document:
            with document.page(rect.w, rect.h) as canvas:
                SkiaPen.CompositeToCanvas(pens, rect, canvas, scale=scale)
    
    def PDFMultiPage(pages, rect, save_to, scale=1):
        stream = skia.FILEWStream(str(save_to))
        with skia.PDF.MakeDocument(stream) as document:
            for page in pages:
                with document.page(rect.w, rect.h) as canvas:
                    SkiaPen.CompositeToCanvas(page, rect, canvas, scale=scale)
    
    def SVG(pens, rect, save_to, scale=1):
        stream = skia.FILEWStream(str(save_to))
        canvas = skia.SVGCanvas.Make((rect.w, rect.h), stream)
        SkiaPen.CompositeToCanvas(pens, rect, canvas, scale=scale)
        del canvas
        stream.flush()
    
    def CompositeToCanvas(pens, rect, canvas, scale=1, style=None):
        if scale != 1:
            pens.scale(scale, scale, Point((0, 0)))
        
        if not pens.visible:
            return
        
        def draw(pen, state, data):
            if state != 0:
                return

            if not pen.visible:
                return
            
            if isinstance(pen, DATText):
                if not isinstance(pen.style, Style):
                    pen.style = Style(*pen.style[:-1], **pen.style[-1], load_font=0)
                
                if isinstance(pen.style.font, str):
                    font = skia.Typeface(pen.style.font)
                else:
                    font = skia.Typeface.MakeFromFile(str(pen.style.font.path))
                    if len(pen.style.variations) > 0:
                        fa = skia.FontArguments()
                        # h/t https://github.com/justvanrossum/drawbot-skia/blob/master/src/drawbot_skia/gstate.py
                        to_int = lambda s: struct.unpack(">i", bytes(s, "ascii"))[0]
                        makeCoord = skia.FontArguments.VariationPosition.Coordinate
                        rawCoords = [makeCoord(to_int(tag), value) for tag, value in pen.style.variations.items()]
                        coords = skia.FontArguments.VariationPosition.Coordinates(rawCoords)
                        fa.setVariationDesignPosition(skia.FontArguments.VariationPosition(coords))
                        font = font.makeClone(fa)
                pt = pen._frame.point("SW")
                canvas.drawString(
                    pen.text,
                    pt.x,
                    rect.h - pt.y,
                    skia.Font(font, pen.style.fontSize),
                    skia.Paint(AntiAlias=True, Color=pen.style.fill.skia()))
                return
            elif isinstance(pen, DATImage):
                paint = skia.Paint(AntiAlias=True)
                f = pen._frame
                canvas.save()
                for action, *args in pen.transforms:
                    if action == "rotate":
                        deg, pt = args
                        canvas.rotate(-deg, pt.x, pt.y)
                    #print(action, args)
                paint.setAlphaf(paint.getAlphaf()*data["alpha"]*pen.alpha)
                bm = pen.blendmode()
                if bm:
                    paint.setBlendMode(bm.to_skia())
                
                canvas.drawImage(pen._img, f.x, f.y, paint)
                canvas.restore()
                #pen = DATPen().rect(pen.bounds()).img(pen._img, rect=pen.bounds(), pattern=False)
                return
            
            if state == 0:
                SkiaPen(pen, rect, canvas, scale, style=style, alpha=data["alpha"])
        
        pens.walk(draw, visible_only=True)
    
    def Precompose(pens, rect, fmt=None, context=None, scale=1, disk=False):
        rect = rect.round()

        if scale < 0:
            rescale = abs(scale)
            scale = 1
        else:
            rescale = None

        sr = rect
        if scale != 1:
            sr = rect.scale(scale).round()
        rect = rect.round()
        if context:
            info = skia.ImageInfo.MakeN32Premul(sr.w, sr.h)
            surface = skia.Surface.MakeRenderTarget(context, skia.Budgeted.kNo, info)
            assert surface is not None
        else:
            surface = skia.Surface(sr.w, sr.h)
        
        with surface as canvas:
            canvas.save()
            canvas.scale(scale, scale)
            SkiaPen.CompositeToCanvas(pens.translate(-rect.x, -rect.y), rect, canvas)
            canvas.restore()
        img = surface.makeImageSnapshot()
        if rescale is not None:
            x, y, w, h = rect.scale(rescale)
            img = img.resize(int(w), int(h))
        
        if disk:
            img.save(disk, skia.kPNG)
            #return disk
        return img
    
    def ReadImage(src):
        return skia.Image.MakeFromEncoded(skia.Data.MakeFromFileName(str(src)))