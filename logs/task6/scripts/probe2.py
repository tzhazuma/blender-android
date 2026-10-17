"""Background-mode probe #2: real .blend open/save round-trips on Android paths."""
import os
import traceback

import bpy

L = []


def p(s):
    L.append(str(s))


def safe(fn, *a, **kw):
    try:
        return fn(*a, **kw)
    except Exception as e:
        return "ERR:%s:%s" % (type(e).__name__, e)


HOME = os.environ.get("HOME", "/tmp")
DL = "/storage/emulated/0/Download"
DOCS = "/storage/emulated/0/Documents"
ROOT = "/storage/emulated/0"

p("=== prefs filepaths (all attrs) ===")
fp = bpy.context.preferences.filepaths
for a in dir(fp):
    if a.startswith("_"):
        continue
    try:
        v = getattr(fp, a)
    except Exception as e:
        v = "ERR %s" % e
    if callable(v):
        continue
    p("  fp.%s = %r" % (a, v))

p("=== dirs exist? ===")
for d in (HOME, DL, DOCS, ROOT, "/", "/storage/emulated", "/storage", "/mnt/user/0/emulated"):
    p("  isdir(%s)=%s isfile=%s exists=%s" % (d, safe(os.path.isdir, d), safe(os.path.isfile, d),
                                              safe(os.path.exists, d)))

p("=== make test dirs ===")
for d in (os.path.join(DL, "BlenderProbe"), os.path.join(DOCS, "BlenderProbe")):
    p("  makedirs %s -> %s" % (d, safe(lambda dd=d: (os.makedirs(dd, exist_ok=True), True)[1])))

p("=== save/open round trips ===")
cases = [
    ("apphome", os.path.join(HOME, "roundtrip_home.blend")),
    ("download", os.path.join(DL, "BlenderProbe", "roundtrip_download.blend")),
    ("documents", os.path.join(DOCS, "BlenderProbe", "roundtrip_documents.blend")),
    ("sdcard_root", os.path.join(ROOT, "roundtrip_root.blend")),
]
for name, path in cases:
    try:
        r = bpy.ops.wm.save_as_mainfile(filepath=path)
        p("SAVE %-10s %-60s ret=%s exists=%s size=%s" %
          (name, path, r, os.path.exists(path),
           safe(os.path.getsize, path)))
    except Exception as e:
        p("SAVE %-10s %-60s EXC %s: %s" % (name, path, type(e).__name__, e))
        continue
    try:
        # Wipe current file state first so we really re-read from disk.
        bpy.ops.wm.read_homefile(use_empty=True)
        r = bpy.ops.wm.open_mainfile(filepath=path)
        p("OPEN %-10s %-60s ret=%s bpy.data.filepath=%r" % (name, path, r, bpy.data.filepath))
    except Exception as e:
        p("OPEN %-10s %-60s EXC %s: %s" % (name, path, type(e).__name__, e))

p("=== startup dir resolution (what the file browser would default to) ===")
try:
    import ctypes
    lib = ctypes.CDLL(None)
except Exception as e:
    p("ctypes ERR %s" % e)

p("=== operator filepath defaults ===")
for opname in ("wm.open_mainfile", "wm.save_as_mainfile", "wm.save_as_mainfile_copy"):
    try:
        import bpy.ops
        mod, fn = opname.split(".")
        op = getattr(getattr(bpy.ops, mod), fn)
        p("  %s: %r" % (opname, safe(lambda o=op: o.get_rna_type().properties["filepath"].default)))
    except Exception as e:
        p("  %s ERR %s: %s" % (opname, type(e).__name__, e))

p("=== resource / script paths ===")
p("  resource_path LOCAL=%s" % safe(lambda: bpy.utils.resource_path("LOCAL")))
p("  user_resource=%s" % safe(lambda: bpy.utils.user_resource("CONFIG")))
p("  script_paths=%r" % safe(lambda: bpy.utils.script_paths()))
p("  addon count=%d" % len(safe(lambda: list(bpy.context.preferences.addons)) or []))

out = os.path.join(HOME, "probe2.txt")
with open(out, "w") as f:
    f.write("\n".join(L) + "\n")
