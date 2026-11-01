# Stage10 runtime audit and two test boundaries

This is a source/static-ABI review for luming and the exact 21H461 original
family. No new kernel, macOS compile, prelink or device result was produced by
this runtime subtask. Current device evidence is the stage9 FBSDisplayMonitor
trap: `[[CADisplay displays] firstObject]` is nil, with the original failure
string `failed to find the main CADisplay`. See the existing
`D:/civitoip20/lumingios-cdx/evidence/STAGE9-RESULT-20261101.md`.

## Service and lifecycle requirements

The existing text console, IOSurface service and a framebuffer address do not
instantiate an IOMobileFramebuffer. The minimal source path supplied here is:

1. Add original `com.apple.iokit.IOMobileGraphicsFamily` as the 28th root. Keep
   its existing original IOSurface/IOAV/AppleM2ScalerCSC/AppleARMPlatform/AMFI/KPI
   dependencies. Enable only the native Legacy implementation, keeping the
   Mobile/Adreno alternatives disabled.
2. The existing DEVELOPMENT/DEBUG BSD hook loads that family and checks status
   zero before invoking our early probe. Only then register the owned subclass
   metaclass, allocate it and verify its actual original ancestry. The generated
   C++ storage declaration is an ABI shim, not permission to replace the real
   original metaclass chain with a direct IOService subclass.
3. Retain the initialized object until the existing post-`IOKitBSDInit` hook.
   Original IOSurface requires the genuine IOBSD resource. Load it there and
   wait at most five seconds for the real `IOCoreSurfaceRoot`.
4. Validate the current `PE_current_console` result again and create one
   IOPlatformDevice memory resource with exactly its physical address and
   `rowBytes * height` extent. The IOService-plane nub attaches to IOResources;
   its DeviceTree-plane node attaches to `/arm-io` as `gop-display`, with the
   implemented `device_type=display-subsystem` property.
5. Probe, attach and start the original Legacy lifecycle on that nub. Keep only
   the real NativeLegacyDisplay under that display subsystem. The reference
   sheng integration records failed enumeration with an extra Presenter child;
   no Presenter is created in this CPU port.
6. Keep the original user client and service properties. Select the unique,
   validated GOP mapping as main; `PE_Video.v_display` is a text/graphics mode,
   not a main-display identity. The control FD deliberately uses mode zero.
   No vendor compatible, fake display ID, physical density or panel timing is
   injected to try to satisfy an unknown client check.

These are concrete dependencies of the port and its original family. They do
not prove that every private CADisplay requirement is already satisfied. If
stage10 registers successfully but CADisplay remains empty, inspect the actual
IORegistry ancestry/provider, original mode/main queries and user-client return
codes next. Do not delete the FBS assertion or fabricate a CADisplay object.

The existing exact-original user-client auditor also establishes an earlier
gate: for every in-range selector (`selector < 90`), `externalMethod` first
dispatches provider virtual slot182 through the provider pointer at client
offset `0xd8`. Therefore a registered service alone does not establish usable
user-client calls. The generated Legacy table binds its original concrete
slot182; this port does not substitute the base framebuffer's pure-virtual
target or return fabricated success. If the first client fails, preserve its
status and any `CDX_DISP` guarded slot/caller before considering rendering work.
The source assertion is in
`work/unixnu-reuse-20261029/sources/core/scripts/audit-mobile-graphics-userclient.py`
under the original provider pre-dispatch gate check.

## First round: registration and enumeration

Use `args-registration.txt` as the only added-args file. It explicitly selects
phase 4 and the real GOP, with all presentation-related gates zero. Existing
stage9 arguments must remain intact; the packer rejects duplicate keys rather
than replacing an existing value silently.

| Gate | First round | Source-level effect |
| --- | --- | --- |
| mobile-graphics-load / legacy-register / phase | 1 / 1 / 4 | Required to load and instantiate this implementation |
| legacy-gop | 1 | Required for owned slot288 `startHardware` to map the real GOP |
| legacy-pm | 0 | Original start is still run; the additional logical PM registration is skipped |
| legacy-validate | 0 | Owned slot296 returns false before request-field or surface access |
| legacy-transfer | 0 | `kickOnce` returns before reading a pending request or writing scanout |
| legacy-retire / legacy-cpu-present | 0 / 0 | This backend does not complete a frame |
| sheng-vsync | 0 | No software vsync timer is created |
| console-handoff | 0 | Normal text console stays available |

The original `start` must succeed before the PM option is read. Therefore PM=1
is not a prerequisite for service publication in this source. PM=1 is required
by this backend's later validation/transfer path and is reserved for round two.
The exact original slot354 powered-state call still runs after successful
original start, because the already lit GOP is a real firmware resource. Its
consumed request shape `{skipRequested=1, requested=0, skipPowered=0, powered=1,
noChange=1}` and false third argument were independently checked against the
original setter and callers; the raw audit must enforce those bytes/layouts.
It does not control panel rails or claim physical PM support.

With validation disabled, callers cannot obtain successful frame presentation
from this backend. The source adds no panic on these zero-valued gates.
Unknown original backend leaves remain fail-stop guards; a new private client
call may still reach one and must be captured by its named `CDX_DISP` slot and
caller. This is a diagnostic build, and producer errors or lack of rendered
frames after enumeration are expected limitations, not successful UI evidence.

Do not use `validate=1` with `transfer=0` as an indefinite runtime mode: an
accepted request can remain pending. Do not use `transfer=1` with both retirement
gates zero: the first copied frame latches `transferred` and will not retire.
Round one disables validation and transfer together to avoid these owned paths.

Two private-path details remain unverified by this runtime subtask: whether the
original selector6 wait requires any requested-state transition beyond the
independently audited powered-only slot354 update when logical PM is disabled,
and the complete original submit caller's rejection/queue cleanup on a false
slot296 validator result. The owned code's immediate false/return behavior is
established above; it does not by itself prove the behavior of every original
caller. PM=0 remains an explicitly limited enumeration diagnostic choice and
must not be reported as proof that all client power/wait paths work. Both items
are follow-up original-code/runtime audit checkpoints, and neither has a new
device observation from this source package.

Round-one evidence should distinguish:

- Family load status zero and successful class registration/init.
- `CDX_DISP` actual mode/geometry, IOSurface load zero, DT attach, mapping,
  successful original probe/start and service registration observations.
- Actual IOService registration with IOMobileFramebuffer/Legacy ancestry and a
  real original user client. A `registered` callback log alone is not an
  independent registry query.
- Direct user-space CADisplay enumeration, if a runnable probe becomes available,
  or the next concrete SpringBoard trace. Passing the old trap address alone
  does not prove full display mode/client/frame contracts.

## Second round: bounded CPU presentation

Only after recording the first round, use `args-cpu-present.txt`. This enables
the logical PM, restricted BGRA validator, real bounded copy, normal original
completion and 60Hz software cadence. On the first fully validated transfer,
the optional public console-release path allows scanout ownership to change.
It declares no missing weak boot-progress imports and does not patch console
internals. Panic can use the normal platform screen reacquisition path.

Observe accepted swaps, copied byte counts, completion increments and multiple
visibly changing real frames. A validated blank swap may legitimately produce
black; it proves neither SpringBoard rendering nor a dead panel. The CPU backend
accepts only a single full-frame, untransformed plain nonplanar BGRA layer, or a
validated all-disabled black frame. It has no compressed-surface decoder,
multi-layer compositor, Metal renderer, GPU fences, physical vblank or touch.

The two argument files are test alternatives, not cumulative additions.
All original-family ABI guards, source/archive hashes, compile and prelink gates
must pass before either is packaged for a device test.
