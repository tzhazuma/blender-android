"""Run 2: invoke `File > Open` (wm.open_mainfile INVOKE) and inspect the file browser."""
import os
import sys

HOME = os.environ.get("HOME", "/tmp")
sys.path.insert(0, HOME)

import bpy  # noqa: E402

import uihelper  # noqa: E402

uihelper.LOG = os.path.join(HOME, "ui2.log")


def t2():
    uihelper.log("=== ui2: open file browser ===")
    uihelper.shot("ui2-00-start.png")


def t3():
    try:
        r = bpy.ops.wm.open_mainfile("INVOKE_DEFAULT")
        uihelper.log("open_mainfile INVOKE -> %s" % (r,))
    except Exception as e:
        uihelper.log("open_mainfile INVOKE EXC %s: %s" % (type(e).__name__, e))


def t5():
    uihelper.dump_context("t5")
    uihelper.dump_file_browser("t5")
    uihelper.shot("ui2-01-open-browser.png")


def t7():
    uihelper.dump_file_browser("t7")
    uihelper.shot("ui2-02-open-browser-later.png")


def t8():
    uihelper.log("quit")
    bpy.ops.wm.quit_blender()


uihelper.Runner([(2, t2), (3, t3), (5, t5), (7, t7), (8, t8)]).start()
