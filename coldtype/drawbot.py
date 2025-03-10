import contextlib
import drawBot as db
from coldtype.geometry import Point, Line, Rect
from coldtype.pens.drawbotpen import DrawBotPen
from coldtype.pens.draftingpen import DraftingPen
from coldtype.pens.draftingpens import DraftingPens
from coldtype.pens.datpen import DATPen
from coldtype.text.reader import StyledString, Style, Font
from coldtype.text.composer import StSt
from coldtype.color import hsl, bw
from coldtype.time import Frame
from pathlib import Path

from coldtype.renderer import renderable, Action
from coldtype.renderable.animation import animation, RenderPass

try:
    import drawBot as db
    import AppKit
except ImportError:
    db = None

class drawbot_script(renderable):
    def __init__(self, rect=(1080, 1080), scale=1, **kwargs):
        if not db:
            raise Exception("DrawBot not installed!")
        super().__init__(rect=Rect(rect).scale(scale), rasterizer="drawbot", **kwargs)
        self.self_rasterizing = True
    
    def normalize_result(self, pens):
        return pens
    
    def run(self, render_pass, renderer_state):
        from coldtype.pens.drawbotpen import DrawBotPen
        use_pool = True
        if use_pool:
            pool = AppKit.NSAutoreleasePool.alloc().init()
        try:
            db.newDrawing()
            if renderer_state.previewing:
                ps = renderer_state.preview_scale
                db.size(self.rect.w*ps, self.rect.h*ps)
                db.scale(ps, ps)
                if not renderer_state.renderer.source_reader.config.window_transparent:
                    DATPen().rect(self.rect).f(self.bg).cast(DrawBotPen).draw()
            else:
                db.size(self.rect.w, self.rect.h)
            if self.rstate:
                render_pass.fn(*render_pass.args, renderer_state)
            else:
                render_pass.fn(*render_pass.args)
            result = None
            if renderer_state.previewing:
                previews = (render_pass.output_path.parent / "_previews")
                previews.mkdir(exist_ok=True, parents=True)
                preview_frame = previews / render_pass.output_path.name
                db.saveImage(str(preview_frame))
                result = preview_frame
            else:
                render_pass.output_path.parent.mkdir(exist_ok=True, parents=True)
                db.saveImage(str(render_pass.output_path))
                result = render_pass.output_path
            db.endDrawing()
        finally:
            if use_pool:
                del pool
        return result

class drawbot_animation(drawbot_script, animation):
    def passes(self, action, renderer_state, indices=[]):
        return animation.passes(self, action, renderer_state, indices)
        if action in [
            Action.RenderAll,
            Action.RenderIndices,
            Action.RenderWorkarea]:
            frames = super().active_frames(action, renderer_state, indices)
            passes = []
            for i in frames:
                p = RenderPass(self, action, i, [Frame(i, self)])
                passes.append(p)
            return passes
        else:
            return super().passes(action, renderer_state, indices)

def dbdraw(p:DraftingPen):
    p.cast(DrawBotPen).draw()
    return p

def tobp(p:DraftingPen):
    bp = db.BezierPath()
    p.replay(bp)
    return bp

def dbdraw_with_filters(rect:Rect, filters):
    def _draw_call(p:DraftingPen):
        p.cast(DrawBotPen).draw_with_filters(rect, filters)
        return p
    return _draw_call

def page_rect() -> Rect:
    return Rect(db.width(), db.height())

@contextlib.contextmanager
def new_page(r:Rect=Rect(1000, 1000)):
    _r = Rect(r)
    db.newPage(*_r.wh())
    yield _r

@contextlib.contextmanager
def new_drawing(rect:Rect=Rect(1000, 1000), count=1, save_to=None):
    db.newDrawing()
    for idx in range(0, count):
        with new_page(rect) as r:
            yield idx, r
    if save_to:
        db.saveImage(str(save_to))
    db.endDrawing()

def pdfdoc(fn, path, frame_class=Frame):
    db.newDrawing()
    r = fn.rect
    w, h = r.wh()
    for idx in range(0, fn.duration):
        print(f"Saving page {idx}...")
        db.newPage(w, h)
        if frame_class:
            fn.func(frame_class(idx, fn))
        else:
            fn.func(r)
    pdf_path = Path(path)
    pdf_path.parent.mkdir(exist_ok=True)
    db.saveImage(str(pdf_path))
    print("Saved pdf", str(pdf_path))
    db.endDrawing()