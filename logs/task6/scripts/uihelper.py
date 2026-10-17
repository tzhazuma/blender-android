"""Shared helpers for driving the Blender UI from a --python startup script.

Blender renders its own window; `bpy.ops.screen.screenshot()` grabs that framebuffer
directly, which lets us inspect the UI even while the Android lock screen covers the
display.
"""
import os
import time
import traceback

import bpy

HOME = os.environ.get("HOME", "/tmp")
# Driver scripts override this after import (one log file per run).
LOG = os.path.join(HOME, "ui.log")


def log(msg):
    try:
        with open(LOG, "a") as f:
            f.write("[%s] %s\n" % (time.strftime("%H:%M:%S"), msg))
    except Exception:
        pass


def shot(name):
    p = os.path.join(HOME, name)
    try:
        r = bpy.ops.screen.screenshot(filepath=p)
        sz = os.path.getsize(p) if os.path.exists(p) else -1
        log("SHOT %s ret=%s exists=%s size=%s" % (name, r, os.path.exists(p), sz))
        return sz
    except Exception as e:
        log("SHOT %s EXC %s: %s\n%s" % (name, type(e).__name__, e, traceback.format_exc()))
        return -1


def dump_context(tag):
    try:
        wm = bpy.context.window_manager
        log("%s: windows=%d" % (tag, len(wm.windows)))
        for w in wm.windows:
            log("%s:   window %r screen=%r" % (tag, w, w.screen.name if w.screen else None))
            if w.screen:
                for a in w.screen.areas:
                    sp = a.spaces.active
                    log("%s:     area %-14s space=%s" % (tag, a.type, sp.type if sp else None))
    except Exception as e:
        log("%s: dump_context EXC %s: %s" % (tag, type(e).__name__, e))


def dump_file_browser(tag):
    """Report the state of every active file-browser space."""
    found = False
    try:
        wm = bpy.context.window_manager
        for w in wm.windows:
            if not w.screen:
                continue
            for a in w.screen.areas:
                if a.type != "FILE_BROWSER":
                    continue
                found = True
                sp = a.spaces.active
                p = sp.params
                log("%s: FILE_BROWSER area %r" % (tag, a))
                log("%s:   params.dir=%r" % (tag, p.dir))
                log("%s:   params.file=%r" % (tag, p.file))
                log("%s:   params.activedir=%r" % (tag, getattr(p, "activedir", None)))
                log("%s:   params.display=%r" % (tag, p.display))
                log("%s:   params.sort=%r" % (tag, p.sort))
                log("%s:   params.filter_glob=%r" % (tag, p.filter_glob))
                log("%s:   params.use_filter=%r" % (tag, p.use_filter))
                log("%s:   params.show_hidden=%r" % (tag, getattr(p, "show_hidden", None)))
                log("%s:   params.rename_buffer=%r" % (tag, getattr(p, "rename_buffer", None)))
                try:
                    log("%s:   listdir(dir)=%r" % (tag, sorted(os.listdir(p.dir))[:40]))
                except Exception as e:
                    log("%s:   listdir(dir) ERR %s: %s" % (tag, type(e).__name__, e))
                try:
                    for region in a.regions:
                        log("%s:   region %s" % (tag, region.type))
                except Exception as e:
                    log("%s:   regions ERR %s" % e)
    except Exception as e:
        log("%s: dump_file_browser EXC %s: %s\n%s" % (tag, type(e).__name__, e, traceback.format_exc()))
    if not found:
        log("%s: no FILE_BROWSER area" % tag)


class Runner:
    """Tiny step scheduler driven by bpy.app.timers."""

    def __init__(self, steps, tick=1.0):
        self.steps = steps  # list of (t, callable)
        self.tick = tick
        self.t = 0

    def start(self):
        bpy.app.timers.register(self._run, first_interval=self.tick)

    def _run(self):
        self.t += 1
        for t, fn in self.steps:
            if t == self.t:
                try:
                    fn()
                except Exception as e:
                    log("step t=%d EXC %s: %s\n%s" % (t, type(e).__name__, e, traceback.format_exc()))
        maxt = max(t for t, _ in self.steps)
        if self.t >= maxt:
            return None
        return self.tick
