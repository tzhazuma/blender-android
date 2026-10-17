"""Windowed-mode end-to-end verification of the File > Open / Save As fix.

Runs inside Blender (started with `--python`), drives the *same* code path the UI uses
(`wm.open_mainfile` / `wm.save_as_mainfile` invoked with `INVOKE_DEFAULT` -> the fileselect
handler -> `ED_screen_temp_space_open()`), and captures Blender's own window framebuffer
with `bpy.ops.screen.screenshot()` so the evidence does not depend on the Android lock
screen or on screen captures of the device.

Must be started WITHOUT `-b` (background mode has no window / no file browser).
"""
import os
import sys

HOME = os.environ.get("HOME", "/tmp")
sys.path.insert(0, HOME)

import bpy  # noqa: E402

import uihelper  # noqa: E402

uihelper.LOG = os.path.join(HOME, "verify.log")
log = uihelper.log

OPEN_DIR = "/storage/emulated/0/Download"
OPEN_FILE = "my_scene.blend"
SAVE_DIR = "/storage/emulated/0/Documents"
SAVE_FILE = "android_saved.blend"
SAVE_PATH = os.path.join(SAVE_DIR, SAVE_FILE)


def fb_space():
    """Return the active FILE_BROWSER space, or None."""
    for w in bpy.context.window_manager.windows:
        if not w.screen:
            continue
        for a in w.screen.areas:
            if a.type == "FILE_BROWSER":
                return a.spaces.active
    return None


def step(tag, fn):
    try:
        r = fn()
        log("%s -> %r" % (tag, r))
    except Exception as e:
        log("%s EXC %s: %s" % (tag, type(e).__name__, e))


def main():
    log("=== verify: blender %s ===" % bpy.app.version_string)
    log("cwd=%s HOME=%s" % (os.getcwd(), HOME))
    uihelper.dump_context("t2")
    uihelper.shot("v-00-start.png")


def open_invoke():
    step("wm.open_mainfile(INVOKE)", lambda: bpy.ops.wm.open_mainfile("INVOKE_DEFAULT"))


def open_shot():
    uihelper.dump_context("t5")
    uihelper.dump_file_browser("t5")
    uihelper.shot("v-01-open-browser.png")


def go_download():
    step("file.select_bookmark(%s)" % OPEN_DIR,
         lambda: bpy.ops.file.select_bookmark(dir=OPEN_DIR))


def download_shot():
    uihelper.dump_file_browser("t8")
    uihelper.shot("v-02-browse-download.png")


def pick_file():
    sp = fb_space()
    log("params.dir=%r params.file=%r" % (sp.params.dir, sp.params.file))
    sp.params.file = OPEN_FILE
    uihelper.shot("v-03-file-selected.png")


def execute_open():
    step("file.execute() [open]", lambda: bpy.ops.file.execute())


def opened_shot():
    log("after open: bpy.data.filepath=%r" % bpy.data.filepath)
    uihelper.dump_context("t12")
    uihelper.shot("v-04-opened.png")


def save_invoke():
    step("wm.save_as_mainfile(INVOKE)", lambda: bpy.ops.wm.save_as_mainfile("INVOKE_DEFAULT"))


def save_shot():
    uihelper.dump_file_browser("t15")
    uihelper.shot("v-05-save-browser.png")


def go_documents():
    step("file.select_bookmark(%s)" % SAVE_DIR,
         lambda: bpy.ops.file.select_bookmark(dir=SAVE_DIR))


def pick_save_name():
    sp = fb_space()
    sp.params.file = SAVE_FILE
    uihelper.shot("v-06-save-ready.png")


def execute_save():
    step("file.execute() [save]", lambda: bpy.ops.file.execute())


def saved_shot():
    log("after save: bpy.data.filepath=%r exists(%s)=%s size=%s" %
        (bpy.data.filepath, SAVE_PATH, os.path.exists(SAVE_PATH),
         os.path.getsize(SAVE_PATH) if os.path.exists(SAVE_PATH) else -1))
    uihelper.dump_context("t21")
    uihelper.shot("v-07-saved.png")


def finish():
    log("=== verify done ===")
    bpy.ops.wm.quit_blender()


uihelper.Runner([
    (2, main),
    (4, open_invoke),
    (6, open_shot),
    (8, go_download),
    (10, download_shot),
    (11, pick_file),
    (12, execute_open),
    (14, opened_shot),
    (16, save_invoke),
    (18, save_shot),
    (20, go_documents),
    (21, pick_save_name),
    (22, execute_save),
    (24, saved_shot),
    (26, finish),
]).start()
