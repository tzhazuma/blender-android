# Blender → Android port patches

`blender-android-port.patch` contains **every source change** needed to build and run
Blender 5.3.0-alpha on Android (arm64-v8a) from the official
[`android` branch](https://projects.blender.org/blender/blender/src/branch/android).

The patch is against `android` branch HEAD `258eef08`
("Cleanup: Deps: Clarify that the ISPC cross-compilation patch only affects NDK sysroot on macOS").

## Contents

| File | Change | Why |
|---|---|---|
| `CMakeLists.txt` | add `PYTHON_EXECUTABLE_TARGET` | Cross compiling overrides `PYTHON_EXECUTABLE` with the *host* interpreter (build tools must run on the host), but the install rules used the same variable, so `cmake --install` tried to put a **macOS** python binary into the APK. |
| `source/creator/CMakeLists.txt` | add the shim to the `blender` target; install `${PYTHON_EXECUTABLE_TARGET}` | see above, plus the shim must be part of the shared library itself (archive ordering). |
| `source/creator/symbols_unix.map` | export `_ZNSt6__ndk113__hash_memoryEPKvm` | the pre-compiled deps need this symbol at **runtime**; `libblender.so` is the root of the load group, so it has to be in the version script whitelist. |
| `source/creator/creator_android_libcxx_compat.cc` | **new file** — `std::__ndk1::__hash_memory` shim | `libshaderc_combined.a` was built against a libc++ that still exported it; NDK r28's libc++ does not. |
| `source/blender/editors/sculpt_paint/mesh/paint_image_3d.cc` | `std::atomic_ref` → `__atomic_*` builtins | NDK r28 (LLVM 19) libc++ has no `std::atomic_ref`. Semantics are identical (load-acquire / store-release). |
| `source/blender/editors/screen/screen_edit.cc` | `ED_screen_temp_space_open()`: fall back to a full-screen temp space when a new window cannot be created | **Fixes `File > Open` / `File > Save As` doing nothing at all on Android** — the SDL Android backend can only ever own a single window, so the file browser, Preferences and Project Setup silently failed to open. See `../STATUS.md` §4. |
| `source/blender/editors/space_file/fsmenu_system_unix.cc` | Android sidebar bookmarks | Android has no XDG user directories, and `/proc/mounts` lists many non-browsable mount points (`/storage/emulated` itself cannot be listed). Insert `Internal Storage` / `Downloads` / `Documents` / … explicitly. |
| `source/blender/blenkernel/intern/appdir.cc` | `BKE_appdir_folder_default()` returns shared storage on Android | `$HOME` is the app private data directory, which no file manager can see; default the file browser to a user visible **and writable** location. |

## Applying

```bash
git clone --depth 1 --single-branch --branch android \
  https://projects.blender.org/blender/blender.git blender
cd blender
git apply -p1 /path/to/blender-android-port.patch     # preferred
```

`git apply --check -p1` passes against `258eef08`.

> `patch -p1 < ...` also works for the 7 modified files, but GNU `patch` ignores the
> `new file mode` header and does **not** create `source/creator/creator_android_libcxx_compat.cc`
> (create it by hand from the patch if you use `patch` instead of `git apply`).

## Not in the patch (non-source steps)

The build also needs a **Vulkan header refresh** and the **official pre-compiled dependency
submodules**; both are described in `../STATUS.md` §2.2, §3.2 and §3.16. In short:

```bash
git clone --depth 1 https://projects.blender.org/blender/lib-android_arm64.git blender/lib/android_arm64
git clone --depth 1 --filter=blob:none --sparse \
  https://projects.blender.org/blender/lib-macos_arm64.git blender/lib/macos_arm64   # host tools
# NDK r28 sysroot only has Vulkan 1.3 headers, the android branch needs 1.4:
mkdir -p blender/lib/android_arm64/vulkan/include/vulkan
cp blender/lib/macos_arm64/vulkan/include/vulkan/*.h blender/lib/android_arm64/vulkan/include/vulkan/
cp -R blender/lib/macos_arm64/vulkan/include/vk_video blender/lib/android_arm64/vulkan/include/
```
