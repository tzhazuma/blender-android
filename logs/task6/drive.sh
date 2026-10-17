#!/bin/bash
# Helper: push files into the Blender app's private home dir and drive runs.
# Usage:
#   ./drive.sh push <local...>          push files to app home
#   ./drive.sh run <script> [waits]     force-stop, launch with --python <script>, wait
#   ./drive.sh get <name...>            cat files from app home
#   ./drive.sh ls                       list app home
set -u
export PATH=$HOME/Library/Android/sdk/platform-tools:$PATH
D=${BLENDER_ADB:-10.20.102.152:5555}
PKG=org.blender.blender
APP_HOME=/data/user/0/$PKG/files/home

adb_retry() {
  for i in 1 2 3 4; do
    if adb -s "$D" "$@" 2>&1; then return 0; fi
    echo "[drive] adb retry $i: $*" >&2
    adb connect "$D" >/dev/null 2>&1
    sleep 3
  done
  return 1
}

cmd=${1:?}; shift

case "$cmd" in
  push)
    for f in "$@"; do
      adb -s "$D" shell "run-as $PKG sh -c 'cat > $APP_HOME/$(basename "$f")'" < "$f" || exit 1
      echo "[drive] pushed $(basename "$f")"
    done
    ;;
  run)
    script=$1; waits=${2:-20}
    adb -s "$D" shell am force-stop $PKG
    sleep 1
    adb -s "$D" shell "am start -n $PKG/.BlenderActivity --es args '--python $APP_HOME/$script'"
    sleep "$waits"
    ;;
  bg)
    # background mode: -b --python
    script=$1; waits=${2:-25}
    adb -s "$D" shell am force-stop $PKG
    sleep 1
    adb -s "$D" shell "am start -n $PKG/.BlenderActivity --es args '-b --python $APP_HOME/$script'"
    sleep "$waits"
    ;;
  get)
    for f in "$@"; do
      echo "===== $f ====="
      adb -s "$D" shell "run-as $PKG cat $APP_HOME/$f" 2>&1
    done
    ;;
  ls)
    adb -s "$D" shell "run-as $PKG ls -la $APP_HOME" 2>&1
    ;;
  rm)
    for f in "$@"; do
      adb -s "$D" shell "run-as $PKG rm -f $APP_HOME/$f"
    done
    ;;
  *)
    echo "unknown: $cmd" >&2; exit 2;;
esac
