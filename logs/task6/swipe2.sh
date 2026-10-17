#!/system/bin/sh
# Synthesize a two-finger swipe on the vivo touchscreen (/dev/input/event6, type-B MT).
# usage: swipe2.sh <dx> <dy> [steps]
#   dx/dy: direction of the swipe in RAW panel units, e.g. "0 20000" = swipe toward +Y.
#   The fingers are laid out perpendicular to the swipe direction.
DEV=${DEV:-/dev/input/event6}
DX=$1
DY=$2
N=${3:-14}

# Raw panel is 20640 x 30960 (portrait native), screen logical is 3096 x 2064 landscape.
CX=10320
CY=15480
# Perpendicular offset between the two fingers (raw units).
if [ "$DX" -ne 0 ]; then
  # Horizontal swipe in raw space -> separate the fingers along Y.
  OX=0; OY=3000
else
  OX=3000; OY=0
fi

SX0=$((CX - OX / 2)); SY0=$((CY - OY / 2))
SX1=$((CX + OX / 2)); SY1=$((CY + OY / 2))
EX0=$((SX0 + DX)); EY0=$((SY0 + DY))
EX1=$((SX1 + DX)); EY1=$((SY1 + DY))

se() { sendevent $DEV "$1" "$2" "$3"; }

# Finger 0 down, finger 1 down.
se 3 47 0; se 3 57 100; se 3 53 $SX0; se 3 54 $SY0; se 3 48 12
se 3 47 1; se 3 57 101; se 3 53 $SX1; se 3 54 $SY1; se 3 48 12
se 1 330 1
se 0 0 0

i=1
while [ $i -le $N ]; do
  X0=$((SX0 + DX * i / N)); Y0=$((SY0 + DY * i / N))
  X1=$((SX1 + DX * i / N)); Y1=$((SY1 + DY * i / N))
  se 3 47 0; se 3 53 $X0; se 3 54 $Y0
  se 3 47 1; se 3 53 $X1; se 3 54 $Y1
  se 0 0 0
  usleep 15000 2>/dev/null || sleep 0.015
  i=$((i + 1))
done

# Both fingers up.
se 3 47 0; se 3 57 -1
se 3 47 1; se 3 57 -1
se 1 330 0
se 0 0 0
echo "swipe2 done dx=$DX dy=$DY"
