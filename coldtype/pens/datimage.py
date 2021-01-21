from pathlib import Path
from coldtype.pens.datpen import DATPen, DATPens
from coldtype.geometry import Rect
import skia, math


class DATImage(DATPen):
    def __init__(self, src, img=None):
        self.src = Path(str(src)).expanduser().absolute()
        if img:
            self._img = img
        else:
            self._img = skia.Image.MakeFromEncoded(skia.Data.MakeFromFileName(str(self.src)))
        self.transforms = []
        self.visible = True
        super().__init__()
        self.addFrame(self.rect())
    
    def rect(self):
        return Rect(self._img.width(), self._img.height())
    
    def bounds(self):
        return self.frame
    
    def img(self):
        return None
    
    def width(self):
        return self._img.width()
    
    def height(self):
        return self._img.height()
    
    def resize(self, factor):
        if factor == 1:
            return self
        self._img = self._img.resize(
            int(self._img.width()*factor),
            int(self._img.height()*factor))
        self.addFrame(self.rect().align(self.frame, "mnx", "mny"))
        return self
    
    def rotate(self, degrees, point=None):
        self.transforms.append(["rotate", degrees, point or self.frame.pc])
        return self
    
    def precompose(self, rect, as_image=True):
        res = DATPens([self]).precompose(rect)
        if as_image:
            return DATImage.FromPen(res, original_src=self.src)
        else:
            return res
        
    def to_pen(self, rect=None):
        return self.precompose(rect or self.frame, as_image=False)
    
    def FromPen(pen:DATPen, original_src=None):
        return DATImage(original_src, img=pen.img().get("src"))
    
    def __str__(self):
        return f"<DATImage({self.src.relative_to(Path.cwd())})/>"