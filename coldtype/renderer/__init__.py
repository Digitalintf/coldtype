import sys, os
from pathlib import Path

import asyncio
import signal
import websockets
from watchgod import awatch, Change

import traceback
from subprocess import call
from runpy import run_path
import argparse
import importlib
import inspect
import json

import coldtype
from coldtype.geometry import Rect
from coldtype.pens.svgpen import SVGPen
from coldtype.pens.cairopen import CairoPen
from coldtype.pens.drawbotpen import DrawBotPen
from coldtype.viewer import PersistentPreview, WEBSOCKET_ADDR


class Renderer():
    def Argparser(name="coldtype-render"):
        parser = argparse.ArgumentParser(prog="coldtype-render", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        parser.add_argument("file", type=str)
        parser.add_argument("-w", "--watch", action="store_true", default=False)
        return parser

    def __init__(self, parser):
        self.args = parser.parse_args()
        self.filepath = Path(self.args.file).expanduser().resolve()
        self.watchees = [self.filepath.parent]
        self.preview = PersistentPreview()
        self.preview.clear()
        self.program = None

        signal.signal(signal.SIGINT, self.on_exit)

    def show_error(self):
        print(">>> CAUGHT COLDTYPE RENDER")
        print(traceback.format_exc())
        self.preview.send(f"<pre>{traceback.format_exc()}</pre>", None)

    async def reload(self):
        try:
            self.program = run_path(str(self.filepath))
            for k, v in self.program.items():
               if isinstance(v, coldtype.text.reader.Font):
                   await v.load()
        except Exception as e:
            self.program = None
            self.show_error()

    async def render(self):
        if not self.program:
            self.preview.send("<pre>No program loaded!</pre>")
        else:
            page = self.program["page"]
            renders = self.program["renders"]
            self.preview.clear()
            try:
                for render in renders:
                    if inspect.iscoroutinefunction(render):
                        result = await render()
                    else:
                        result = render()
                    self.preview.send(SVGPen.Composite(result, page, viewBox=True), bg=1, max_width=800)
            except:
                self.show_error()
    
    async def reload_and_render(self):
        await self.reload()
        await self.render()

    def main(self):
        asyncio.run(self.start())

    async def start(self):
        await self.reload_and_render()
        await self.on_start()
        if self.args.watch:
            await asyncio.gather(
                self.listen_to_ws(),
                self.watch_file_changes(),
            )
        else:
            self.on_exit(None, None)
    
    async def on_start(self):
        pass
    
    async def on_message(self, message, action):
        if action:
            await self.on_action(action, message)
    
    async def on_action(self, action, message):
        if action == "render_storyboard":
            await self.reload_and_render()
    
    async def process_ws_message(self, message):
        jdata = json.loads(message)
        await self.on_message(jdata, jdata.get("action"))

    async def listen_to_ws(self):
        async with websockets.connect(WEBSOCKET_ADDR) as websocket:
            async for message in websocket:
                await self.process_ws_message(message)

    async def watch_file_changes(self):
        async for changes in awatch(self.watchees[0]):
            for change, path in changes:
                if change == Change.modified:
                    print(change, path)
                    await self.reload()
                    await self.render()

    def on_exit(self, frame, signal):
        print("<EXIT RENDERER>")
        self.preview.close()
        asyncio.get_event_loop().stop()
        sys.exit(0)