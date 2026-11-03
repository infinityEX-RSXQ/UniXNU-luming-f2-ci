# Stage19 — actual waiting-stack evidence, 2026-11-03

This is a diagnostic source change. It does not establish that the desktop works.
Host checks passed; a complete macOS build and hardware capture remain pending.

## Baseline and interpretation

- Device repository: infinityEX-RSXQ/UniXNU-luming-f2-ci, accepted Stage18 r2 commit
  `1ff0191689395552bb047ec5dde2a34be73fc203`.
- UniXNU: `33da81310819b86d3ea62cb704f156c56407764a`; profile 21H461; Intel macOS/Xcode 16.4.
- Accepted device kernel SHA256:
  `8ba11aab6079d5adf32bad5f0d10cf97ec63b1c3b884ff1fdd4ca675cdec8586`.
- Stage18 observed two advancing completion IDs and three returned waits. Its W4
  mode0/nonblocking Busy is consistent with the audited original branch when the
  ID MATCHES +0x16bc and neither current nor queued request satisfies the wait.
  These observations do not exclude every possible display protocol failure.
- No daemon-exit record does not prove a process is running normally. Selector72
  registration and GPU/fence waits remain hypotheses until actual evidence arrives.

## Implementation

The accepted source-built kernel really defines `stack_snapshot_from_kernel`.
Its declaration, implementation, kcdata layouts and ARM stack address treatment
are pinned in `xnu-source-pins.json`. Absence of a guessed symbol such as
`stackshot_snapshot` does not make this existing kernel-consumer API unavailable.
`thread_getstatus` is not a scheduler-state query and is not used here.

`install_stage19.py` changes only the owned LegacyDisplayProbe source, after
verifying all three Stage18 source inputs. The display backend and generator are
byte-identical. Original IOMFB selector dispatch, wait/completion methods and
subscription semantics are retained. The new capture is default off.

When enabled, the existing independent thread_call captures two coherent kernel
stackshots, with the second scheduled 15 seconds after the first call completes.
Both captures occur BEFORE display quiesce and console reclaim, without holding
provider/diagnostic locks. Their printed `ms` values are relative to the existing
diagnostic epoch, not claims about exact seconds after boot. Stackshot performs
its normal debugger rendezvous; no task/thread suspension API is called by this
consumer. TRYLOCK, no compression and no fault-in flags are used. There is no
unbounded retry. Each capture has a 4 MiB buffer; raw successful snapshots are
copied into IORegistry OSData, and the temporary buffer is freed.

The bounded decoder selects processes by exact comm name, not a fixed PID:
backboardd, SpringBoard, launchd. It counts all observed threads and retains up to
eight per process, ranking main thread first, then waiting/non-idle threads. For
each retained thread it records thread ID, scheduler state, flags, continuation,
up to four kernel and four user return addresses, wait event, wait owner/context
and wait kind where present. Raw kcdata preserves additional threads/frames.

Screen output shows one selected thread from each sample. `n` in K/U rows is the
original observed frame count, not the number of printed addresses. Kernel LRs
and continuations are unslid. Wait events may be unslid OR permuted; do not compare
them blindly to raw IORegistry object pointers. User addresses require the actual
shared-cache UUID/slide and matching binaries. `sc=unavailable` explicitly means
the last syscall number is not in the decoded data. The parser rejects partial or
malformed buffers. API failure, process absence, missing frames or property-save
failure remain visible; none is converted to successful evidence.

Raw/state properties on the owned active display service:
`CDX19Raw0`, `CDX19Raw1`, `CDX19State0`, `CDX19State1`.
These are RAM properties, not persistent crash files. A phone reboot loses them;
no runtime extraction transport is supplied by this patch. The photo page remains
useful independently. No claim is made that the raw snapshot has been retrieved.

## CI integration

Copy this directory to `device/stage19` in a checkout of the accepted commit.
Do not copy `runtime/` over the Stage10 input: the ordered installers must produce
that result themselves. `runtime/` is the reference materialization for inspection.

From the checkout's parent (where `device` is the device repository):

```sh
python3 device/stage19/integrate_ci19.py --repo device
python3 device/stage19/integrate_ci19.py --repo device --apply
```

This verifies four exact Stage18 CI inputs, extends their checked source chain to
Stage19, keeps old ABI/byte/call checks, and adds source pin verification before
installation plus `ci_check19.py` after final link. The final linked capture must
contain exactly one direct BL to the defined source kernel API, not a hardcoded
address or unresolved import. The altered workflow remains Intel macOS. Dispatch
once using the accepted Stage18 inputs, with both workflow ref and device_ref set
to the new branch. No automatic retry or device action belongs to this job.

Return the full kernel, complete build/prelink report, Stage19 source/install/kernel
reports, and prior Stage15–18 gate reports. Keep kernel assets in the existing
private artifact channel; this source package contains no kernel or credentials.
Independently qualify the downloaded kernel against the original 21H461
kernelcache with `qualify_stage19_kernel.check` before packaging for a phone.

Host validation: `validation.json`, `ci-preflight.json`, `test-output.txt`.
The prior repository skeleton check still reports 142 pass, 7 missing, 4 warn,
1 pre-existing error (`.github/workflows/porting-record.yml` absent). It is not a
green full-build result. Stage19 local adapter compilation is ARM64 kernel/GPR-only,
not a substitute for the complete macOS kernel link.

## Runtime configuration after the complete build qualifies

Retain accepted Stage18 options for CPU present, refresh, p26, console handoff and
the diagnostic snapshot. In addition set:

```text
luming-display-snapshot=1
luming-display-stackshot=1
luming-display-stack-page=0
luming-display-stack-thread=0
```

Page 0 = backboardd; 1 = SpringBoard; 2 = launchd. Thread 0 = highest priority
retained thread (main thread when flagged); 1..7 select other retained ranks.
Ranks can change between samples, so compare actual T row IDs, not just rank.
Page selection needs no new kernel, only the existing boot-option carrier.
If stackshot is disabled, the accepted Stage18 diagnostic path remains active.
The final CDX19 intentional panic is the observation endpoint, not an unexplained
kernel crash. Photograph its complete S/P/T/K/U/W/cache/footer rows.

Acceptance is evidence, not a desktop promise: both API results and parser states
must be reported. Compare the same thread across the two timestamps, symbolize
available addresses with the exact new kernel/cache identity, and use wait kind
and owner/context to distinguish Mach IPC, semaphore, fence or service waits.
Two matching waits alone still do not prove the wait is abnormal. If capture or
decoding fails, report unavailable and retain its rc/error rather than guessing.
