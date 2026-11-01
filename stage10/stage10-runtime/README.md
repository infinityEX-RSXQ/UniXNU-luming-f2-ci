# Luming CPU Legacy display runtime, stage 10

Source-only adaptation for the original ordinary-ARM64 iPadOS 17.7.11 / 21H461
IOMobileGraphicsFamily ABI used by the current luming owner3-based build. The
immediate checkpoint is a real IOMobileFramebuffer service that the original
CADisplay client can discover. A successful registration is not proof of a
visible UI, a working GPU, or an accepted/completed compositor frame.

This directory is isolated from the dsh working tree. No device commands or
partition writes were performed by this subtask.

## Sources and adaptation

- `NativeLegacyDisplay.cpp` derives from `UniXNU/GopFramebuffer` at
  `cf3b42979a9c44219e7bb149543e6fc3388b58ed`.
- `NativeLegacyRequest.h` and `Test/request-state.c` are unchanged copies from
  that same component revision; their portable bounds/copy assertions passed.
- `LegacyDisplayProbe.cpp` adapts the phase-4 lifecycle from
  `UniXNU/UniXNU-sheng` at `08cde20edc3254ed6f7df8d0f5384fb887786e8f`,
  `package/LegacyDisplayProbe.cpp`.
- BSD-2-Clause-Patent terms are retained in `LICENSE`.

The shared concrete backend has two functional changes: accept only plain,
nonplanar BGRA surfaces, and select the sole validated current-console GOP
mapping as the main display. The reference's `v_display == 1` test could not be
used here: XNU defines that field as Text/Graphics mode, and the current luming
control firmware's `BootVideo.h:31` deliberately sets it to **0** to keep the
working text-console path. This adaptation accepts modes 0 and 1 and does not
modify `PE_state.video` or forge a firmware mode/identity. `primary=valid` means
this single owned framebuffer resource has been selected as main by the port.
Its shared retirement counters are external declarations; the probe provides
their single definitions to avoid duplicate symbols when both objects link.

The runtime removes all sheng CPU frequency, GPU/power, touch, keystore, HID,
Wi-Fi, audio/DSP, battery, buttons, backlight and DPU probe calls. It also removes
NativeGOPPresenter construction, GPU handoff, and diagnostic user-client vptr
interposition. The backend's GPU-offer callback returns false, so validated
frames use the shared bounded CPU copy. Original user-client behavior is not
patched. Unknown backend leaves 211/245/246/306/307/338/345 retain fail-stop guards.

## Required build contract

Use the paired `work/stage10-build` integration. It must add the original
IOMobileGraphicsFamily root and use the supplied, pinned raw 21H461 kernelcache
for exact ABI qualification. Do not substitute headers or addresses from a
different IPSW, sheng hardware driver, or previously prelinked image.

The build generates `OriginalLegacyFramebufferABI.h`, validates the actual
358-entry owned vtable, and emits original aliases for seven IOSurface getters,
the vsync sender, and refresh-property publisher. The generated header and
original binding addresses are build products, not invented here. Manual
constructor staging must remove `__DATA,__mod_init_func` from the owned object,
globalize `__GLOBAL__sub_I_NativeLegacyDisplay.cpp`, and call it exactly once
inside OSMetaClass preModLoad/postModLoad. Never run the original family class
constructors a second time.

The archive contains only the late NativeLegacyDisplay object, qualified
original-bindings object, and this LegacyDisplayProbe object. No Presenter or
SM8550 peripheral archive is needed. `source-contract.json` lists required
custom C symbols; the builder remains responsible for compiled symbol checking.

## Runtime ordering and inputs

1. Existing core hooks load the original IOMobileGraphicsFamily, then call
   `native_legacy_display_probe` under the explicit registration gate.
2. The probe manually registers the owned class once, validates real
   `PE_current_console` geometry, allocates/initializes the owned subclass, and
   retains it pending until the core's post-IOKitBSDInit hook.
3. `native_legacy_display_late_probe` loads IOSurface and waits up to five
   seconds for the real IOCoreSurfaceRoot. It creates one IOPlatformDevice with
   the exact GOP physical range, puts it under `/arm-io` in the device-tree plane
   as `gop-display` / `device_type=display-subsystem`, then performs the original
   probe, attach and start lifecycle.
4. The backend verifies its mapped memory descriptor against the same console
   base, dimensions and length before selecting it as main. Width and height
   are the actual scanout pixels. No panel timing, vendor compatible, physical
   density, display scale, GPU completion or hardware vblank is fabricated.
5. Only after a validated real copy or blank swap is about to write scanout may
   the optional console-handoff policy call public
   `PE_initialize_console(nullptr, kPEReleaseScreen)`. Until then, diagnostics
   stay visible. This uses the public text-console release path only. The
   stage-9 control symbol table has no boot-progress prepare/cancel entry
   points, so this probe declares no optional unresolved weak hooks.

The current control firmware already rejects non-BGRA UEFI pixel formats and
zeros boot-video tail fields. The probe additionally rejects rotation, nonzero
offset, unsupported mode, missing/non-32bpp geometry, short stride/length,
arithmetic overflow and unaligned base/stride. Mapping failure prevents service
publication. There is no alternate framebuffer address or guessed geometry.

The first test targets registration and CADisplay enumeration while keeping the
text console. Use `args-registration.txt` with the existing baseline:

```text
offline-mobile-graphics-load=1 offline-legacy-register=1 offline-legacy-phase=4
offline-legacy-gop=1 offline-legacy-pm=0 offline-legacy-validate=0
offline-legacy-transfer=0 offline-legacy-retire=0 offline-legacy-cpu-present=0
sheng-vsync=0 luming-display-console-handoff=0
```

The second test uses `args-cpu-present.txt` instead, enabling logical PM,
validation, transfer, retirement, CPU presentation, `sheng-vsync=60` and console
handoff. The detailed gate behavior, first-round limitations and acceptance
criteria are in `RUNTIME-ACCEPTANCE.md`. These are alternative added-args files.

`sheng-vsync=60` requests a **software timer cadence** for the original vsync
message sender. It is not a measurement or claim of the panel's physical refresh
rate. Leave GPU, early-retirement, differential-copy and unit-scale experiment
flags absent for the CPU test. The phase-4 backend accepts one complete,
untransformed plain BGRA layer over black, or a validated blank swap; it is not
a general multi-layer compositor or compressed-surface decoder.

## Diagnostics and failure handling

Short `CDX_DISP` lines distinguish ctor, console mode/geometry, IOSurface load,
DT attach, probe, start, service registration, first user clients, validation,
and actual copies. PM/client/validation/copy observations are bounded. The
unknown-leaf guard names its slot and lifecycle stage before panicking.

Lifecycle stage 1 is constructor registration, 2 is console validation, 3 is a
retained pending object, 4 is late IOSurface/resource setup, 5 is original start,
10 is a successfully started owned service; 8 is failure. Failure reasons:

| Reason | Meaning |
| --- | --- |
| 1 / 2 | OSMetaClass pre/post registration failed |
| 3 | Unsupported or invalid current-console handoff |
| 4 / 5 / 6 | Allocation, real ancestry check, or original initialization failed |
| 7 | IOSurface load/matching or revalidated console failed |
| 8 / 9 | Resource allocation/init or nub/DT setup failed |
| 10 / 11 | Original probe/attach or original start failed |

On setup failure, new attachments and retained objects are unwound. On success,
the display and nub intentionally keep owned references until reboot because
this built-in experiment does not implement an unload transition. Existing
memory descriptor/array references are released after the nub retains them.

First acceptance is actual service enumeration: a registered NativeLegacyDisplay
with IOMobileFramebuffer/Legacy ancestry and original matching properties, and
CADisplay returning a real main display. Then require accepted frame, bounded
copy and normal retirement evidence before claiming a visible frame. An active
SpringBoard process or the absence of its previous assertion alone is not a UI
success criterion. GPU/Metal, HID/touch, physical PM and full rendering remain
separate work.

## Verification performed here

```text
python verify_sources.py
python verify_portable.py --cc <Windows LLVM clang.exe>
```

Source custom-hook completeness/scope checks passed. The unchanged portable C
tests compiled with `-Wall -Wextra -Werror` and all layer-mask, overflow, padding,
alignment, fill and CPU-copy assertions returned 0; see `portable-tests.json`.
No macOS XNU C++ compile, archive prelink, display service enumeration, frame
presentation or physical hardware success is asserted by those host tests.
The generated original-ABI audit and slot-354 state-setter contract must pass
before the package can be considered a test candidate.

Primary references: [GOP integration](https://unixnu.com/drivers/gop-framebuffer),
[component selection](https://unixnu.com/reference/components),
[device tree](https://unixnu.com/porting/device-tree), and
[device repositories](https://unixnu.com/porting/device-repository).
