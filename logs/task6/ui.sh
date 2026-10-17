#!/bin/bash
# Device UI helpers for the on-device verification (screenshots / taps / install dialogs).
#   ./ui.sh shot <name>          capture the screen (with retries)
#   ./ui.sh tap <x> <y>          tap in device pixels (3096x2064 landscape)
#   ./ui.sh swipe <x1> <y1> <x2> <y2> [ms]
#   ./ui.sh text <string>        type text into the focused field
#   ./ui.sh key <KEYCODE>
#   ./ui.sh nodes                uiautomator dump -> clickable nodes with bounds
#   ./ui.sh lock                 print keyguard/wakefulness state
set -u
export PATH=$HOME/Library/Android/sdk/platform-tools:$PATH
D=${BLENDER_ADB:-10.20.102.152:5555}
DIR=$(dirname "$0")
cmd=${1:?}; shift

case "$cmd" in
  shot)
    name=$1
    for i in 1 2 3 4; do
      if adb -s "$D" exec-out screencap -p > "$DIR/$name" 2>/dev/null && [ -s "$DIR/$name" ]; then
        echo "shot $name ($(stat -f%z "$DIR/$name") bytes)"
        exit 0
      fi
      echo "shot retry $i" >&2
      adb connect "$D" >/dev/null 2>&1
      sleep 3
    done
    echo "shot FAILED" >&2; exit 1;;
  tap)   adb -s "$D" shell input tap "$1" "$2"; echo "tap $1 $2";;
  swipe) adb -s "$D" shell input swipe "$1" "$2" "$3" "$4" "${5:-300}"; echo "swipe $*";;
  text)  adb -s "$D" shell input text "$1"; echo "text $1";;
  key)   adb -s "$D" shell input keyevent "$1"; echo "key $1";;
  nodes)
    adb -s "$D" shell uiautomator dump /data/local/tmp/ui.xml >/dev/null 2>&1
    adb -s "$D" shell cat /data/local/tmp/ui.xml 2>/dev/null | /usr/bin/python3 -c '
import re,sys
x=sys.stdin.read()
for m in re.finditer(r"<node[^>]*>", x):
    n=m.group(0)
    if "clickable=\"true\"" not in n: continue
    t=re.search(r"text=\"([^\"]*)\"",n); r=re.search(r"resource-id=\"([^\"]*)\"",n)
    b=re.search(r"bounds=\"\[(\d+),(\d+)\]\[(\d+),(\d+)\]\"",n)
    if not b: continue
    x1,y1,x2,y2=map(int,b.groups())
    print("%-40s %-30s center=(%d,%d)"%(t.group(1) if t else "", (r.group(1) if r else ""), (x1+x2)//2,(y1+y2)//2))
';;
  lock)
    echo "keyguard: $(adb -s "$D" shell dumpsys window 2>&1 | grep -oE 'mDreamingLockscreen=(true|false)' | head -1)"
    echo "wake:     $(adb -s "$D" shell dumpsys power 2>&1 | grep -oE 'mWakefulness=[A-Za-z]+' | head -1)"
    echo "top:      $(adb -s "$D" shell dumpsys activity activities 2>&1 | grep -oE 'ResumedActivity: .*' | head -1)";;
  *) echo "unknown: $cmd" >&2; exit 2;;
esac
