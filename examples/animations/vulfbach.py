from coldtype import *
from coldtype.time.midi import MidiReader
from coldtype.fx.skia import color_phototype

"""
Run as `coldtype examples/animation/vulfbach.py`
To multiplex, add ` -m` to the end of that call
(then when you hit `a` in the viewer app, the frames
will render in parallel in random-order)

Rendered with organ.wav as the backing track:
    https://vimeo.com/489013931/cd77ab7e4d
"""

midi = MidiReader("examples/animations/media/organ.mid", bpm=183, fps=30)
organ = midi[0]

note_width = 3
r = Rect(1440, 1080)

def pos(x, y):
    return (x*note_width, (y-midi.min)*(r.h-200)/midi.spread+100)

def build_line():
    dp = DATPen().f(None).s(rgb(1, 0, 0.5)).sw(3)
    last_note = None

    for note in organ.notes:
        if last_note and (note.on - last_note.off > 3 or last_note.note == note.note):
            dp.lineTo((pos(last_note.off, last_note.note)))
            dp.endPath()
            last_note = None
        if last_note:
            if last_note.off < note.on:
                dp.lineTo((pos(last_note.off, last_note.note)))
            else:
                dp.lineTo((pos(note.on, last_note.note)))
            dp.lineTo((pos(note.on, note.note)))
        else:
            dp.moveTo((pos(note.on, note.note)))
        last_note = note
    if last_note:
        dp.lineTo((pos(last_note.off, last_note.note)))
    dp.endPath()
    return dp

line = build_line()

@animation(timeline=organ.duration, rect=r, storyboard=[0])
def render(f):
    time_offset = -f.i * note_width + r.w - note_width * 3
    time_offset += 10 # fudge
    looped_line = DATPens([
        (line
            .copy()
            .translate(
                time_offset - organ.duration *note_width,
                0)),
        (line
            .copy()
            .translate(time_offset, 0))
    ])
    return DATPens([
        DATPen().rect(f.a.r).f(0),
        (looped_line.pen()
            .ch(color_phototype(f.a.r, blur=20, cut=215, cutw=40))),
        (looped_line.pen()
            .ch(color_phototype(f.a.r, blur=3, cut=200, cutw=25)))])