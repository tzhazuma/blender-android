# Blender → Android port patches

Four patches carry **every source change** needed to build, run and use
Blender 5.3.0-alpha on Android (arm64-v8a) from the official
[`android` branch](https://projects.blender.org/blender/blender/src/branch/android).

They are against `android` branch HEAD `258eef08`
("Cleanup: Deps: Clarify that the ISPC cross-compilation patch only affects NDK sysroot on macOS")
and are rooted at the Blender source tree, so all four are applied with `-p1` from `blender/`.

All four have been verified to apply **in this order** to a pristine checkout, and the result
was byte-compared against the working tree this repository was built from.

| # | Patch | Contents |
|---|---|---|
| 1 | `blender-android-port.patch` | Build/runtime port: Python install target, libc++ symbol shim, NDK `atomic_ref` fix, single-window fallback, Android file-browser bookmarks and default directory. |
| 2 | `blender-android-saf-native.patch` | Native SAF bridge (`source/creator/creator_android_saf.{cc,hh}` + non-Android stub) and its two lines in `source/creator/CMakeLists.txt`. |
| 3 | `blender-android-saf-hook.patch` | Call sites: `File > Open` and `File > Save As` in `wm_files.cc`, the file-browser hook in `file_ops.cc`, and the include path that lets the editors see the bridge header. |
| 4 | `blender-android-saf-java.patch` | The Java half in `release/android/.../BlenderActivity.java`: six JNI methods, the two pickers and the file copy/publish logic. |

## What each source change is for

### `blender-android-port.patch`

| File | Change | Why |
|---|---|---|
| `CMakeLists.txt` | add `PYTHON_EXECUTABLE_TARGET` | Cross compiling overrides `PYTHON_EXECUTABLE` with the *host* interpreter (build tools must run on the host), but the install rules used the same variable, so `cmake --install` tried to put a **macOS** python binary into the APK. |
| `source/creator/CMakeLists.txt` | add the shim to the `ANDROID` sources; install `${PYTHON_EXECUTABLE_TARGET}` | see above, plus the shim must be part of the shared library itself (archive ordering). |
| `source/creator/symbols_unix.map` | export `_ZNSt6__ndk113__hash_memoryEPKvm` | the pre-compiled deps need this symbol at **runtime**; `libblender.so` is the root of the load group, so it has to be in the version script whitelist. |
| `source/creator/creator_android_libcxx_compat.cc` | **new file** — `std::__ndk1::__hash_memory` shim | `libshaderc_combined.a` was built against a libc++ that still exported it; NDK r28's libc++ does not. |
| `source/blender/editors/sculpt_paint/mesh/paint_image_3d.cc` | `std::atomic_ref` → `__atomic_*` builtins | NDK r28 (LLVM 19) libc++ has no `std::atomic_ref`. Semantics are identical (load-acquire / store-release). |
| `source/blender/editors/screen/screen_edit.cc` | `ED_screen_temp_space_open()`: fall back to a full-screen temp space when a new window cannot be created | the SDL Android backend can only ever own a single window, so secondary spaces silently failed to open. |
| `source/blender/editors/space_file/fsmenu_system_unix.cc` | Android sidebar bookmarks | Android has no XDG user directories, and `/proc/mounts` lists many non-browsable mount points (`/storage/emulated` itself cannot be listed). Insert `Internal Storage` / `Downloads` / `Documents` / … explicitly. |
| `source/blender/blenkernel/intern/appdir.cc` | `BKE_appdir_folder_default()` returns shared storage on Android | `$HOME` is the app private data directory, which no file manager can see; default the file browser to a user visible **and writable** location. |

### `blender-android-saf-native.patch`

Blender opens POSIX paths everywhere; Android hands out `content://` URIs. The bridge
(`creator_android_saf.{cc,hh}`) is the only Android-aware layer:

- `android_saf_pick_open()` — calls `safPickOpen()`, waits for `safIsDone()`, then reads the
  real paths the Java half copied into `filesDir/incoming/` from `filesDir/saf-manifest.txt`.
  Results travel through the filesystem, not JNI arrays, so a multi-file selection of any size
  never has to be marshalled.
- `android_saf_pick_save(name)` — calls `safPickSave(String)`, waits for `safSaveDone()`, and
  reports whether a destination URI was chosen.
- `android_saf_export_path(name)` — the scratch path `<filesDir>/export/<name>` a save writes
  into before publishing.
- `android_saf_finish_save(path)` — polls the scratch file size until it has been stable for
  1.5 s, then `safPublish(String)` streams it to the document URI.
- `android_saf_publish(path)` — the raw publish call.

`creator_android_saf_stub.cc` answers "no picker available" on every non-Android build, so call
sites need no `#ifdef` of their own.

### `blender-android-saf-hook.patch`

| File | Change |
|---|---|
| `source/blender/windowmanager/intern/wm_files.cc` | `File > Open` raises the system open picker instead of Blender's browser (the picked file is copied to private storage first); `File > Save As` raises the create-document picker, rewrites the destination to `filesDir/export/<name>`, saves normally, then publishes the bytes to the chosen URI. |
| `source/blender/editors/space_file/file_ops.cc` | when a file is *opened* from Blender's own browser (import/export dialogs), the picker supplies the file, the browser then navigates to `filesDir/incoming/` and selects it. Save dialogs are skipped — they have their own picker. |
| `source/blender/editors/space_file/CMakeLists.txt`, `source/blender/windowmanager/CMakeLists.txt` | put `source/creator` on those targets' include path so they can include the bridge header. |

### `blender-android-saf-java.patch`

`BlenderActivity` gains the six methods the native side calls
(`safPickOpen`, `safIsDone`, `safPickSave`, `safSaveDone`, `safHasSaveUri`, `safPublish`).
Both `startActivityForResult` calls are posted with `runOnUiThread`: the callers are Blender's
render thread, and without it the picker is silently never shown. Imported documents are copied
into `filesDir/incoming/` (unique names kept apart), the save destination URI is persisted for
the immediate publish, and the manifest is written atomically enough that a cancelled pick
clears it rather than re-importing the previous selection.

## Applying

```bash
git clone --depth 1 --single-branch --branch android \
  https://projects.blender.org/blender/blender.git blender
cd blender
git apply -p1 /path/to/blender-android-port.patch
git apply -p1 /path/to/blender-android-saf-native.patch
git apply -p1 /path/to/blender-android-saf-hook.patch
git apply -p1 /path/to/blender-android-saf-java.patch
```

`--check` passes for each patch in that order against `258eef08`.

> `patch -p1 < ...` also works, but GNU `patch` ignores the `new file mode` header, so the new
> files (`creator_android_libcxx_compat.cc`, `creator_android_saf.cc`, `.hh`, `_stub.cc`) have
> to be created by hand if you use `patch` instead of `git apply` — they must be empty first,
> otherwise `patch` writes the diff into a missing file and fails.

## Not in the patches (non-source steps)

### Host tools and the host dependency chain

Cross-compiling also configures `host_tools` (makesdna / makesrna / datatoc / shader_tool /
msgfmt) against **macOS**, and that configure evaluates the whole feature set. The official
`lib-macos_arm64` repo is a sparse + `blob:none` clone, so several directories it needs are not
checked out by default. Install `git-lfs` and fetch them:

```bash
git lfs install
cd blender/lib/macos_arm64
git sparse-checkout add draco manifold meshoptimizer gmp haru potrace rubberband \
                          zstd openvdb fftw3 sse2neon
```

(Embree is symlinked to Homebrew: `embree/include` → `/opt/homebrew/opt/embree/include`,
`embree/lib` → `/opt/homebrew/opt/embree/lib`, with `brew install embree`.)

### Vulkan header refresh and dependency submodules

```bash
git clone --depth 1 https://projects.blender.org/blender/lib-android_arm64.git blender/lib/android_arm64
# NDK r28 sysroot only has Vulkan 1.3 headers, the android branch needs 1.4:
mkdir -p blender/lib/android_arm64/vulkan/include/vulkan
cp blender/lib/macos_arm64/vulkan/include/vulkan/*.h blender/lib/android_arm64/vulkan/include/vulkan/
cp -R blender/lib/macos_arm64/vulkan/include/vk_video blender/lib/android_arm64/vulkan/include/
```

### Launcher icons

The icons in `release/android/app/src/main/res` are generated from Blender's own
`release/freedesktop/icons/scalable/apps/blender.svg` by `../tools/make_icons.sh`, which renders
all five legacy densities, the round variant and an adaptive foreground (108 dp, logo inside the
66 dp safe zone). The adaptive XML references `@mipmap/ic_launcher_foreground`.

### Build and package

See `../STATUS.md` for the exact `cmake` invocation, the install/`gradle_stage`/`assembleRelease`
steps, and the gotchas (strip `libblender.so` right after linking, Gradle needs
`JAVA_HOME=/opt/homebrew/opt/openjdk@21`, etc.).
