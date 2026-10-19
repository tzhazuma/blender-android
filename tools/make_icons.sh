#!/bin/sh
# Render Blender's original upstream logo into every Android launcher density.
#
# Source of truth is the icon shipped in Blender's own source tree:
#   release/freedesktop/icons/scalable/apps/blender.svg
# The output replaces the launcher resources of release/android so the APK carries
# the same mark as the desktop build instead of a generic Android placeholder.
#
# Requires: rsvg-convert (librsvg) and ImageMagick 7 (`magick`).
set -eu

SRC_TREE=$(cd "$(dirname "$0")/../src/blender" && pwd)
SVG="$SRC_TREE/release/freedesktop/icons/scalable/apps/blender.svg"
RES="$SRC_TREE/release/android/app/src/main/res"

[ -f "$SVG" ] || { echo "missing $SVG" >&2; exit 1; }
[ -d "$RES" ] || { echo "missing $RES" >&2; exit 1; }

TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

# Render once at high resolution; every density is a downscale of this master.
rsvg-convert -w 1024 -h 1024 "$SVG" -o "$TMP/logo.png"

# Square/circle masks for the legacy icons. ImageMagick turns a white-on-transparent
# canvas into a grayscale image, which would desaturate the logo when composited, so
# the logo is laid on an opaque white field first and the mask only supplies alpha.
rounded_mask() {
  magick -size "$1x$1" xc:black -fill white \
    -draw "roundrectangle 0,0,$(($1 - 1)),$(($1 - 1)),$(($1 * 20 / 100)),$(($1 * 20 / 100))" "$2"
}
circle_mask() {
  magick -size "$1x$1" xc:black -fill white \
    -draw "circle $(($1 / 2)),$(($1 / 2)) $(($1 / 2)),0" "$2"
}

# Densities follow the standard 48/72/96/144/192 px launcher ladder.
for entry in mdpi:48 hdpi:72 xhdpi:96 xxhdpi:144 xxxhdpi:192; do
  density=${entry%%:*}
  size=${entry##*:}
  logo=$((size * 86 / 100))

  magick "$TMP/logo.png" -resize "${logo}x${logo}" "$TMP/logo-sized.png"
  magick "$TMP/logo-sized.png" -background white -gravity center -extent "${size}x${size}" \
    -flatten "$TMP/field.png"

  rounded_mask "$size" "$TMP/mask-round.png"
  circle_mask "$size" "$TMP/mask-circle.png"

  magick "$TMP/field.png" "$TMP/mask-round.png" -alpha off -compose CopyOpacity -composite \
    -define webp:lossless=true "$RES/mipmap-$density/ic_launcher.webp"
  magick "$TMP/field.png" "$TMP/mask-circle.png" -alpha off -compose CopyOpacity -composite \
    -define webp:lossless=true "$RES/mipmap-$density/ic_launcher_round.webp"

  # Adaptive foreground: 108 dp transparent canvas, logo inside the 66 dp safe zone.
  fg=$((108 * size / 48))
  flogo=$((fg * 66 / 108))
  magick "$TMP/logo.png" -resize "${flogo}x${flogo}" \
    -background none -gravity center -extent "${fg}x${fg}" \
    -define webp:lossless=true "$RES/mipmap-$density/ic_launcher_foreground.webp"

  echo "icons: $density legacy ${size}px, adaptive ${fg}px"
done

# Point the adaptive icon at the rendered foreground. The background stays white,
# matching the desktop logo's own white field.
for name in ic_launcher ic_launcher_round; do
  cat > "$RES/mipmap-anydpi-v26/$name.xml" <<'EOF'
<?xml version="1.0" encoding="utf-8"?>
<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
    <background android:drawable="@color/ic_launcher_background"/>
    <foreground android:drawable="@mipmap/ic_launcher_foreground"/>
    <monochrome android:drawable="@drawable/ic_launcher_monochrome"/>
</adaptive-icon>
EOF
done

echo "icons: regenerated from $SVG"
