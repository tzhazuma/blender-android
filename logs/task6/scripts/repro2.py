import os, sys
HOME = os.environ.get("HOME", "/tmp")
sys.path.insert(0, HOME)
import bpy
import uihelper
uihelper.LOG = os.path.join(HOME, "repro2.log")


def t2():
    uihelper.log("=== repro2 start ===")
    uihelper.shot("r-00-start.png")


def t3():
    r = bpy.ops.wm.open_mainfile("INVOKE_DEFAULT")
    uihelper.log("open_mainfile INVOKE -> %s" % (r,))


def t6():
    uihelper.dump_context("t6")
    for w in bpy.context.window_manager.windows:
        uihelper.log("WIN %r screen=%r ghostwin?" % (w, w.screen.name))
    uihelper.shot("r-01-after-open.png")


def t12():
    uihelper.dump_context("t12")
    uihelper.shot("r-02-later.png")
    uihelper.log("still running, browser should be up")


uihelper.Runner([(2, t2), (3, t3), (6, t6), (12, t12), (60, t12)]).start()
