"""Create a distinctive test .blend in shared storage for on-device verification."""
import os

import bpy

L = []


def p(s):
    L.append(str(s))
    print(s, flush=True)


bpy.ops.wm.read_homefile(use_empty=False)
scn = bpy.context.scene
scn.name = "AndroidTestScene"
scn.render.filepath = "/storage/emulated/0/Download/"

# A UV sphere is easy to recognise in a screenshot, the default cube is not.
bpy.ops.mesh.primitive_uv_sphere_add(radius=2.0, location=(0.0, 0.0, 2.0))
bpy.ops.object.shade_smooth()
bpy.ops.object.light_add(type="AREA", location=(4.0, -4.0, 8.0))
bpy.ops.object.camera_add(location=(7.0, -7.0, 5.0))

for path in (
    "/storage/emulated/0/Download/my_scene.blend",
    "/storage/emulated/0/Documents/my_scene.blend",
):
    try:
        bpy.ops.wm.save_as_mainfile(filepath=path)
        p("SAVED %s exists=%s size=%s" % (path, os.path.exists(path), os.path.getsize(path)))
    except Exception as e:
        p("SAVE %s FAILED %s: %s" % (path, type(e).__name__, e))

with open(os.path.join(os.environ.get("HOME", "/tmp"), "mkblend.txt"), "w") as f:
    f.write("\n".join(L) + "\n")
