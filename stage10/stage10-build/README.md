# Stage10 CPU Legacy display build integration

This is an uncompiled integration bundle for the existing Format2 stage9 owner
recipe. It does not operate a device, publish CI, change Apple instructions or
claim that SpringBoard renders. The first target is a genuine
IOMobileFramebufferLegacy service backed by the already initialized firmware GOP.

## Files and sibling directories

Ship these files in `stage10-build/`:

- `install_stage10_build.py`
- `build-luming-cpu-legacy-display.py`
- this README and `ci-chain-snippet.yml`
- qualification JSON files, for review

Ship `stage10-runtime/` beside it, containing `LegacyDisplayProbe.cpp`,
`NativeLegacyDisplay.cpp`, `NativeLegacyRequest.h` and LICENSE. Ship
`stage10-audit/audit_raw_legacy.py` beside it. The generated builder is standalone;
the preparation script, its source-cache tree, host fixture and local verification
helper are not CI inputs.

## Exact baseline contracts

- UniXNU core commit: `33da81310819b86d3ea62cb704f156c56407764a`.
- XNU source: `d8b80295118ef25ac3a784134bcf95cd8e88109f` / 10063.141.1.
- OS profile: `ipados-17.7.11-21H461`, ordinary ARM64/native4K.
- Raw original kernelcache SHA256:
  `f18b4df865405f2a287b84977d7aca745e056d656d9fc9df1662970ce2969de7`.
- Prelink slide: `-0x1000000`; original AMFI early initializer unchanged.
- Original IOMobileGraphicsFamily text SHA256:
  `2e044ee68c1650397e1435234ca6459206262e4c7ed709cb7131c6f664f9bd9b`.
- Existing 27 Apple roots gain exactly IOMobileGraphicsFamily, for 28 roots.
  Existing IOSurface, IOAVFamily, AppleM2ScalerCSCDriver, AppleARMPlatform,
  AMFI and KPI dependencies already cover that family's original dependency set.
- Keep `CONFIG_XNU_NATIVE_MOBILE_DISPLAY=n` and `CONFIG_XNU_NATIVE_ADRENO=n`.
  Set only `CONFIG_XNU_NATIVE_LEGACY_DISPLAY=y`.
- Existing archive order is preserved; the CPU archive recipe is appended last.
  It produces exactly `build/native-legacy-display/libNativeLegacyDisplay.late.a`.
  The core's existing linker switch force-loads this file and checks
  `build-report.json` archive/source hashes. Do not additionally force-load it in
  EXTRA_LD_ARCHIVES.

## Chain after the existing stage9 pre_build hook

The installer must run **after** the current short ASLR/event pre_build generator
has completed, without replacing it. The workflow configures defconfig before
that hook, so it must run defconfig again after this installer updates the board
defconfig. `ci-chain-snippet.yml` shows the three commands to append to that same
existing step.

The kernelcache path must be the same verified raw input prepared for the normal
kernel build. In the current CI workflow that is `$UNIXNU_KERNELCACHE` from the
proprietary-input preparation step. No URL, token or proprietary file is put in
this bundle.

Example from the workflow workspace, with a `stage10/` bundle directory:

```sh
python3 stage10/stage10-build/install_stage10_build.py \
  --tree unixnu --device device --kernelcache "$UNIXNU_KERNELCACHE" \
  --runtime-dir stage10/stage10-runtime --audit-dir stage10/stage10-audit --apply
(cd unixnu && ./unixnu defconfig "$DEFCONFIG" -D ../device)
```

Without `--apply`, the installer checks its inputs and prints a plan, changing
nothing. It leaves the existing hook, XNU patches, short diagnostics, payload
arguments, ADT, trust cache and Data seed untouched. It changes only two board
arrays and one defconfig flag, then copies the owned build/runtime/audit files to
the isolated core checkout. The existing `./unixnu build kernel` command runs the
new recipe after its normal compile-record bootstrap.

## Archive build and qualification

The builder first runs the portable raw-original audit. That audit proves the
class identity, 0x18a0 extent, 358 slots, nine pure leaves, protected constructor
chain and getter bodies. Its JSON explicitly distinguishes raw addresses from
postslide kext addresses. Only family-internal slots receive the prelink slide;
native IOService imports resolve normally at the native XNU link. A uniform
slide applied to every slot would be wrong.

The native class compiles from the actual XNU C++ compile record, then its object
vtable and unresolved original-class imports are checked. The builder retains
all of sheng's exact original-code byte guards for its bound getters, refresh,
vsync and swap lifecycle, while using a raw-cache read wrapper that reverses the
intended prelink slide. The 358-slot qualifier already includes slot337 through
the pure-slot list; no exception was added for the CPU fork.

Both owned compilations use the builder's `compile_owned` replay. It preserves
the XNU target, SDK, language/ABI options and working directory, replaces only
the input/output, and removes separate or joined `-MF`, `-MT`, `-MJ` destinations.
It does not invoke the shared `build-arm-driver.py` replay, which would overwrite
the source kernel's `IOPlatformExpert` dependency/compile-record outputs. A tiny
ARM64/iOS17 two-object fixture verified that the original record/dependency
sentinels remain byte-identical and only owned dependency files are emitted;
this fixture is not a compile of the full display class.

Only the owned class's `__mod_init_func` is removed from its late object; text
bytes must remain identical. The late static constructor is explicitly invoked
by the runtime after the original family is loaded. The archive contains only:

1. `NativeLegacyDisplay.late.o`
2. `original-bindings.o`
3. `LegacyDisplayProbe.o`

No Presenter, Adreno, SM8550, SMMU, GPU power, HID, KeyStore, touch, WiFi, audio,
battery or panel timing object is included. Existing boot log/PMGR/etc remain in
their original owner archives, unchanged.

## Payload gates and observability

The root packer owns the actual test args and must preserve the validated
stage9 ADT, two original TrustCache modules, seed and existing args. Runtime
publication gates are:

```text
offline-mobile-graphics-load=1 offline-legacy-register=1 offline-legacy-phase=4
```

The backend has separate mapping, power, validation, transfer and completion
gates. Consult the runtime README for the complete test list; do not claim that
the three publication gates alone present frames. `sheng-vsync=60` is a software
timer cadence, not a claim about panel clock programming.

Keep `luming-display-console-handoff=0` for the first registration-only test. When
enabled as `=1`, the runtime may release the text console only after a successfully
validated/copied real frame. This is an observable transition, not evidence that
UI rendering has become available.

Expected evidence progression: `CDX_DISP` constructor → original family loaded →
IOSurface available after IOBSD → real GOP memory provider → DT/probe/start →
user client → validated BGRA IOSurface → bounded CPU copy → swap completion.
Validate actual pixels and multiple completed frames, then investigate the
backboardd/SpringBoard producer. CPU scanout cannot supply missing Metal/GPU
rendering by itself.

## What was verified locally

- Python syntax checks passed.
- The two board arrays/one flag mutation on the actual saved owner board passed;
  an idempotence check passed, with all other parsed board fields equal.
- Every retained original-code byte guard ran against the exact raw original
  cache and passed. See `original-binding-guard-validation.json`.
- No C++ compile, native link, prelink, runtime service or device display was
  tested here. Xcode iphoneos SDK, the XNU-generated headers/compile records,
  xcrun tools and Homebrew LLVM/objcopy remain required on the macOS runner.

The portable raw audit is independent of pruned sheng QEMU observations and does
not require a pre-existing display candidate, avoiding a fresh-build dependency
cycle. Any guard failure requires inspecting the actual new inputs, not deleting
or weakening the check.
