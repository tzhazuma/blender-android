# Headless probe for Blender-on-Android file access.
# Writes results to $HOME/probe1.txt inside the app private dir.
import os
import sys
import traceback

L = []


def p(s):
    L.append(str(s))


def safe(fn, *a):
    try:
        return fn(*a)
    except Exception as e:
        return "ERR:%s:%s" % (type(e).__name__, e)


p("=== env ===")
for k in ("HOME", "TMPDIR", "PATH", "BLENDER_ANDROID_EXTRACT_DIR", "TMP", "USER", "EXTERNAL_STORAGE"):
    p("%s=%s" % (k, os.environ.get(k)))

p("=== cwd/uid ===")
p("cwd=%s" % safe(os.getcwd))
p("uid=%s euid=%s gid=%s" % (safe(os.getuid), safe(os.geteuid), safe(os.getgid)))
p("umask=%s" % safe(lambda: os.umask(0o022)))

p("=== listdir ===")
for d in (
    "/",
    "/sdcard",
    "/storage",
    "/storage/emulated",
    "/storage/emulated/0",
    "/storage/emulated/0/Download",
    "/storage/emulated/0/Documents",
    "/storage/emulated/0/Android/data/org.blender.blender/files",
    "/storage/self/primary",
    "/mnt",
    "/data",
    "/data/local/tmp",
    "/data/user/0/org.blender.blender/files",
    os.environ.get("HOME", "/nonexistent"),
    "/system",
    "/proc/self/fd",
):
    r = safe(os.listdir, d)
    if isinstance(r, list):
        p("listdir %-55s OK n=%d first=%s" % (d, len(r), r[:12]))
    else:
        p("listdir %-55s %s" % (d, r))

p("=== stat / access ===")
for d in ("/storage/emulated/0", "/storage/emulated/0/Download", os.environ.get("HOME", "/")):
    p("access W %-45s %s" % (d, safe(os.access, d, os.W_OK)))
    p("stat   %-45s %s" % (d, safe(os.stat, d)))

p("=== write tests ===")
targets = [
    os.path.join(os.environ.get("HOME", "/tmp"), "write_test.bin"),
    "/storage/emulated/0/Download/blender_write_test.bin",
    "/storage/emulated/0/blender_write_test.bin",
    "/sdcard/blender_write_test.bin",
    "/data/local/tmp/blender_write_test.bin",
]
for t in targets:
    try:
        with open(t, "wb") as f:
            f.write(b"hello-blender-android")
        p("write %-55s OK" % t)
        safe(os.remove, t)
    except Exception as e:
        p("write %-55s ERR %s: %s" % (t, type(e).__name__, e))

p("=== blender ===")
try:
    import bpy

    p("bpy version=%s" % bpy.app.version_string)
    p("bpy.app.binary_path=%s" % bpy.app.binary_path)
    p("bpy.app.tempdir=%s" % bpy.app.tempdir)
    p("bpy.utils.resource_path('LOCAL')=%s" % bpy.utils.resource_path("LOCAL"))
    p("bpy.utils.resource_path('USER')=%s" % bpy.utils.resource_path("USER"))
    p("bpy.utils.resource_path('SYSTEM')=%s" % bpy.utils.resource_path("SYSTEM"))
    p("bpy.data.filepath=%r" % bpy.data.filepath)
    p("bpy.path.abspath('//')=%s" % bpy.path.abspath("//"))
    fp = bpy.context.preferences.filepaths
    p("prefs.filepaths.file_preview_type=%s" % fp.file_preview_type)
    p("prefs.filepaths.use_filter_file_extensions=%s" % fp.use_filter_file_extensions)
    p("prefs.filepaths.temporary_directory=%r" % fp.temporary_directory)
    p("prefs.filepaths.render_output_directory=%r" % fp.render_output_directory)
    p("prefs.filepaths.script_directory=%r" % fp.script_directory)
    p("prefs.filepaths.font_directory=%r" % fp.font_directory)
    p("prefs.filepaths.texture_directory=%r" % fp.texture_directory)
    p("prefs.filepaths.sound_directory=%r" % fp.sound_directory)
    p("prefs.filepaths.temporary_directory=%r" % fp.temporary_directory)
    p("prefs.filepaths.recent_files=%s" % list(fp.recent_files))
    p("prefs.filepaths.use_relative_paths=%s" % fp.use_relative_paths)

    p("=== save test (app private home) ===")
    hp = os.path.join(os.environ.get("HOME", "/tmp"), "probe_save.blend")
    try:
        r = bpy.ops.wm.save_as_mainfile(filepath=hp)
        p("save_as_mainfile(%s) -> %s exists=%s size=%s" % (hp, r, os.path.exists(hp),
                                                            safe(lambda: os.path.getsize(hp))))
    except Exception as e:
        p("save_as_mainfile(%s) EXC %s: %s" % (hp, type(e).__name__, e))

    p("=== save test (/storage/emulated/0/Download) ===")
    sp = "/storage/emulated/0/Download/probe_save.blend"
    try:
        r = bpy.ops.wm.save_as_mainfile(filepath=sp)
        p("save_as_mainfile(%s) -> %s exists=%s" % (sp, r, os.path.exists(sp)))
    except Exception as e:
        p("save_as_mainfile(%s) EXC %s: %s" % (sp, type(e).__name__, e))

    p("=== open test ===")
    try:
        r = bpy.ops.wm.open_mainfile(filepath=hp)
        p("open_mainfile(%s) -> %s ; data.filepath=%r" % (hp, r, bpy.data.filepath))
    except Exception as e:
        p("open_mainfile EXC %s: %s" % (type(e).__name__, e))

    p("=== preferences / appdir ===")
    try:
        import _bpy
        p("_bpy has appdir? %s" % hasattr(_bpy, "appdir"))
    except Exception as e:
        p("import _bpy ERR %s" % e)
except Exception:
    p("bpy section failed:\n%s" % traceback.format_exc())

out = os.path.join(os.environ.get("HOME", "/tmp"), "probe1.txt")
try:
    with open(out, "w") as f:
        f.write("\n".join(L) + "\n")
except Exception as e:
    sys.stderr.write("cannot write %s: %s\n" % (out, e))
