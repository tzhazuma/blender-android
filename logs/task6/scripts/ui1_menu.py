"""Run 1: open the Blender top-bar `File` menu and capture the window framebuffer."""
import os
import sys

HOME = os.environ.get("HOME", "/tmp")
sys.path.insert(0, HOME)

import bpy  # noqa: E402

import uihelper  # noqa: E402

uihelper.LOG = os.path.join(HOME, "ui1.log")
log = uihelper.log


def t2():
    uihelper.log("=== blender %s ===" % bpy.app.version_string)
    uihelper.dump_context("t2")
    uihelper.shot("ui1-00-start.png")


def t3():
    try:
        r = bpy.ops.wm.call_menu(name="TOPBAR_MT_file")
        uihelper.log("call_menu TOPBAR_MT_file -> %s" % (r,))
    except Exception as e:
        uihelper.log("call_menu EXC %s: %s" % (type(e).__name__, e))


def t4():
    uihelper.dump_context("t4")


def t5():
    uihelper.shot("ui1-01-filemenu.png")


def t7():
    uihelper.log("quit")
    bpy.ops.wm.quit_blender()


uihelper.Runner([(2, t2), (3, t3), (4, t4), (5, t5), (7, t7)]).start()
