import os, time
HOME = os.environ.get("HOME", "/tmp")
with open(os.path.join(HOME, "imm.log"), "a") as f:
    f.write("[%s] module import OK\n" % time.strftime("%H:%M:%S"))
import bpy
with open(os.path.join(HOME, "imm.log"), "a") as f:
    f.write("[%s] bpy %s\n" % (time.strftime("%H:%M:%S"), bpy.app.version_string))

def tick():
    with open(os.path.join(HOME, "imm.log"), "a") as f:
        f.write("[%s] tick\n" % time.strftime("%H:%M:%S"))
    return None

bpy.app.timers.register(tick, first_interval=1.0)
