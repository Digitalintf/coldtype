import inspect, platform, re, tempfile, skia, math, os

from enum import Enum
from subprocess import run
from pathlib import Path
from datetime import datetime

from coldtype.geometry import Rect, Point
from coldtype.color import normalize_color
from coldtype.animation import Timeable, Frame
from coldtype.animation.timeline import Timeline
from coldtype.text.reader import normalize_font_prefix, Font
from coldtype.pens.datpen import DATPen, DATPenSet
from coldtype.pens.dattext import DATText

from coldtype.renderable.renderable import renderable, drawbot_script, Action, RenderPass

try:
    import drawBot as db
    import AppKit
except ImportError:
    db = None

class animation(renderable, Timeable):
    def __init__(self, rect=(1080, 1080), duration=10, storyboard=[0], timeline:Timeline=None, **kwargs):
        super().__init__(**kwargs)
        self.rect = Rect(rect)
        self.r = self.rect
        self.start = 0
        self.end = duration
        #self.duration = duration
        self.storyboard = storyboard
        if timeline:
            self.timeline = timeline
            self.t = timeline
            self.start = timeline.start
            self.end = timeline.end
            #self.duration = timeline.duration
            if self.storyboard != [0] and timeline.storyboard == [0]:
                pass
            else:
                self.storyboard = timeline.storyboard.copy()
        else:
            self.timeline = Timeline(30)
    
    def __call__(self, func):
        res = super().__call__(func)
        self.prefix = self.name + "_"
        return res
    
    def folder(self, filepath):
        return filepath.stem + "/" + self.name # TODO necessary?
    
    def all_frames(self):
        return list(range(0, self.duration))
    
    def active_frames(self, action, renderer_state, indices):
        frames = self.storyboard.copy()
        for fidx, frame in enumerate(frames):
            frames[fidx] = (frame + renderer_state.frame_index_offset) % self.duration
        if action == Action.RenderAll:
            frames = self.all_frames()
        elif action in [Action.PreviewIndices, Action.RenderIndices]:
            frames = indices
        elif action in [Action.RenderWorkarea]:
            if self.timeline:
                try:
                    frames = self.workarea()
                except:
                    frames = self.all_frames()
                #if hasattr(self.timeline, "find_workarea"):
                #    frames = self.timeline.find_workarea()
        return frames
    
    def workarea(self):
        return list(self.timeline.workareas[0])
    
    def pass_suffix(self, index):
        return "{:04d}".format(index)
    
    def passes(self, action, renderer_state, indices=[]):
        frames = self.active_frames(action, renderer_state, indices)
        return [RenderPass(self, self.pass_suffix(i), [Frame(i, self)]) for i in frames]
    
    def package(self, filepath, output_folder):
        pass

    def contactsheet(self, gx, sl=slice(0, None, None)):
        try:
            sliced = True
            start, stop, step = sl.indices(self.duration)
            duration = (stop - start) // step
        except AttributeError: # indices storyboard
            duration = len(sl)
            sliced = False
        
        ar = self.rect
        gy = math.ceil(duration / gx)
        
        @renderable(rect=(ar.w*gx, ar.h*gy), bg=self.bg, name=self.name + "_contactsheet")
        def contactsheet(r:Rect):
            _pngs = list(sorted(self.output_folder.glob("*.png")))
            if sliced:
                pngs = _pngs[sl]
            else:
                pngs = [p for i, p in enumerate(_pngs) if i in sl]
            
            dps = DATPenSet()
            dps += DATPen().rect(r).f(self.bg)
            for idx, g in enumerate(r.grid(columns=gx, rows=gy)):
                if idx < len(pngs):
                    dps += DATPen().rect(g).f(None).img(pngs[idx], g, pattern=False)
            return dps
        
        return contactsheet


class drawbot_animation(drawbot_script, animation):
    def passes(self, action, renderer_state, indices=[]):
        if action in [
            Action.RenderAll,
            Action.RenderIndices,
            Action.RenderWorkarea]:
            frames = super().active_frames(action, renderer_state, indices)
            passes = []
            for i in frames:
                p = RenderPass(self, "{:04d}".format(i), [Frame(i, self)])
                passes.append(p)
            return passes
        else:
            return super().passes(action, renderer_state, indices)


class FFMPEGExport():
    def __init__(self, a:animation,
        passes:list,
        date=False,
        loops=1):
        self.a = a
        self.passes = passes
        self.date = date
        self.loops = loops
        self.fmt = None

        passes = [p for p in self.passes if p.render == self.a]
        template = str(passes[0].output_path).replace("0000.png", "%4d.png")

        self.folder = passes[0].output_path.parent.parent

        # https://github.com/typemytype/drawbot/blob/master/drawBot/context/tools/mp4Tools.py
        self.args = [
            "ffmpeg",
            "-y", # overwrite existing files
            "-loglevel", "16", # 'error, 16' Show all errors
            "-r", str(self.a.timeline.fps),
            "-i", template, # input sequence
            "-filter_complex", f"loop=loop={self.loops-1}:size={self.a.timeline.duration}:start=0"
        ]
    
    def h264(self):
        self.fmt = "mp4"
        self.args.extend([
            "-c:v", "libx264",
            "-crf", "20", # Constant Rate Factor
            "-pix_fmt", "yuv420p", # pixel format
        ])
        return self
    
    def prores(self):
        # https://video.stackexchange.com/questions/14712/how-to-encode-apple-prores-on-windows-or-linux
        self.fmt = "mov"
        self.args.extend([
            "-c:v", "prores_ks",
            "-c:a", "pcm_s16le",
            "-profile:v", "2"
        ])
        return self
    
    def gif(self):
        self.fmt = "gif"
        #self.args.extend([])
        return self
    
    def write(self):
        if not self.fmt:
            raise Exception("No fmt specified")
        
        now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        d = ("_" + now) if self.date else ""
        self.output_path = self.folder / f"{self.a.name}{d}.{self.fmt}"

        self.args.append(self.output_path)
        run(self.args)

        print(">", self.output_path)
        return self
    
    def open(self):
        """i.e. Reveal-in-Finder"""
        os.system(f"open {self.output_path.parent}")
        return self