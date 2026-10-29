# FAULT-LOCALIZATION-2 — OSMetaClass::instanceConstructed inside IOWorkLoop::workLoop

Offline analysis of `build/payload51/EFI/UniXNU/Payloads/kernel.macho` (xnu-10063.141.1 build,
format-2 kernel extracted from `build/super-format2-t27.img`, J2 member `payload` →
`EFI/UniXNU/Payloads/kernel.macho`). **No device operations were performed for this report.**
Symbols: `tmp/k51.nm` (3.5 MB, unslid VAs). Reproduce with
`python agents/f2-luming/tools/analyze-fault-2.py`; raw JSON in `tmp/task341-analysis.json`.

## 1. Current evidence (from the device and task-341)

PSCI-reset markers written at function entries (`movz w0,#0x8400,lsl#16; movk w0,#9; smc #0` =
`00 80 b0 52 20 01 80 72 03 00 00 d4`); **reboot = reached, freeze = not reached**:

| Marker VA | Function | Result |
| --- | --- | --- |
| `0xfffffff007839810` | `OSObject_typed_operator_new` | reached |
| `0xfffffff007839a58` | `OSObject::OSObject(OSMetaClass const*)` | reached |
| `0xfffffff007838450` | `OSMetaClass::instanceConstructed() const` | reached |
| `0xfffffff0078c77d0` | `IOWorkLoop::init()` | **not reached** (kernel freezes) |

Call chain: `PE_init_iokit` → `InitIOKit` → `startIOServiceMatching` →
`IOWorkLoop::workLoop()` (`0xfffffff0078c78f0`). The fault is after the call to
`OSMetaClass::instanceConstructed` is entered and before `IOWorkLoop::init` is called, i.e. inside
`instanceConstructed`/its return path in `workLoop`, or inside the constructor bookkeeping that
`workLoop` performs between the two markers.

**Important caveat about entry markers:** a PSCI marker at a function entry replaces the first
12 bytes (3 instructions) and resets *before the body executes*. "instanceConstructed reached"
therefore proves the call target was reached, not that its body completed. The next markers below
are placed at body instructions exactly to localize the body.

## 2. Caller: `IOWorkLoop::workLoop()` (annotated)

`0xfffffff0078c78f0` (from `llvm-objdump -d --start-address=0xfffffff0078c78f0 --stop-address=0xfffffff0078c7970`):

```
fffffff0078c78f0  a9be4ff4   stp x20, x19, [sp, #-0x20]!
fffffff0078c78f4  a9017bfd   stp x29, x30, [sp, #0x10]
fffffff0078c78f8  910043fd   add x29, sp, #0x10
fffffff0078c78fc  f0ffcaa0   adrp x0, 0xfffffff00721e000      ; IOKit kalloc type descriptor
fffffff0078c7900  9123a000   add  x0, x0, #0x8e8
fffffff0078c7904  52800901   mov  w1, #0x48                   ; sizeof(IOWorkLoop)
fffffff0078c7908  97fdc7c2   bl   0xfffffff007839810           ; OSObject_typed_operator_new
fffffff0078c790c  aa0003f3   mov  x19, x0                    ; x19 = new object (or NULL)
fffffff0078c7910  d0001514   adrp x20, 0xfffffff007b69000
fffffff0078c7914  91296294   add  x20, x20, #0xa58            ; x20 = &IOWorkLoop::gMetaClass
fffffff0078c7918  aa1403e1   mov  x1, x20
fffffff0078c791c  97fdc84f   bl   0xfffffff007839a58           ; OSObject::OSObject(ctor)
fffffff0078c7920  f0ffc7e8   adrp x8, 0xfffffff0071c6000
fffffff0078c7924  9120c108   add  x8, x8, #0x830             ; IOWorkLoop vtable
fffffff0078c7928  f9000008   str  x8, [x0]                   ; object vptr = IOWorkLoop vtable
fffffff0078c792c  aa1403e0   mov  x0, x20
fffffff0078c7930  97fdc2c8   bl   0xfffffff007838450           ; instanceConstructed(gMetaClass)
fffffff0078c7934  f9400268   ldr  x8, [x19]                  ; object vptr
fffffff0078c7938  f9403508   ldr  x8, [x8, #0x68]            ; vtable slot +0x68
fffffff0078c793c  aa1303e0   mov  x0, x19
fffffff0078c7940  d63f0100   blr  x8                          ; IOWorkLoop::init
fffffff0078c7944  370000c0   tbnz w0, #0x0, +0x6c            ; if init() == true
```

Facts verified from the Mach-O file:
- `IOWorkLoop::gMetaClass` = `0xfffffff007b69a58`, symbol `__ZN10IOWorkLoop10gMetaClassE`,
  inside `__DATA,__common` (section flags `0x1` = S_ZEROFILL, i.e. BSS; segment `__DATA`
  vmaddr `0xfffffff007a4c000`, maxprot/initprot `rw`).
- The object vptr is `__ZTV10IOWorkLoop + 0x10` = `0xfffffff0071c6830`; slot `+0x68`
  (`0xfffffff0071c6898`) contains `0xfffffff0078c77d0` = `IOWorkLoop::init`. **The init call target
  and vtable slot are correct in this image**; a fault before the init marker is therefore not caused
  by a broken vtable slot.
- `workLoopWithOptions` has the identical sequence at `0xfffffff0078c796c` (`bl` at `0x…79b4`,
  init `blr` at `0x…79dc`).
- DarwinBoot zeroes the whole allocated kernel window (`ZeroMem ((VOID *)(UINTN)Address, (UINTN)Used)`,
  DarwinBoot.c:708) before copying segments, so `__DATA,__common` starts as zero for a fresh boot.
  `IOWorkLoop::gMetaClass` is therefore **zero unless its C++ constructor ran**; the constructor is
  listed through the kernel image's `__mod_init_func` (`__DATA_CONST` list containing the
  `IOWorkLoop` initializer at `0xfffffff0078c7574`), i.e. it depends on the format-2 boot/prelink
  running the kernel's `__mod_init_func` constructors.

## 3. Callee: `OSMetaClass::instanceConstructed()` (annotated)

`0xfffffff007838450` … `0xfffffff00783847c` (12 instructions; full symbol, next symbol
`instanceDestructed` at `0x…8480`):

```
fffffff007838450  a9be4ff4   stp  x20, x19, [sp, #-0x20]!    ; save callee-saved
fffffff007838454  a9017bfd   stp  x29, x30, [sp, #0x10]
fffffff007838458  910043fd   add  x29, sp, #0x10
fffffff00783845c  aa0003f3   mov  x19, x0                    ; x19 = this (OSMetaClass, e.g. gMetaClass)
fffffff007838460  91009260   add  x0, x19, #0x24             ; &this->instanceCount (+0x24)
fffffff007838464  97fffa4f   bl   0xfffffff007836da0           ; OSIncrementAtomic(&instanceCount)
fffffff007838468  35000060   cbnz w0, 0xfffffff007838474     ; if old count != 0 -> return
fffffff00783846c  f9400a73   ldr  x19, [x19, #0x10]          ; x19 = this->superClassLink (+0x10)
fffffff007838470  b5ffff93   cbnz x19, 0xfffffff007838460    ; if superClassLink != 0 -> recurse/loop
fffffff007838474  a9417bfd   ldp  x29, x30, [sp, #0x10]
fffffff007838478  a8c24ff4   ldp  x20, x19, [sp], #0x20
fffffff00783847c  d65f03c0   ret
```

`OSIncrementAtomic` (`0xfffffff007836da0`):

```
fffffff007836da0  885f7c08   ldxr  w8, [x0]
fffffff007836da4  11000509   add   w9, w8, #1
fffffff007836da8  880a7c09   stxr  w10, w9, [x0]
fffffff007836dac  35ffffaa   cbnz  w10, 0xfffffff007836da0   ; retry loop
fffffff007836db0  aa0803e0   mov   x0, x8                     ; return old value
fffffff007836db4  d65f03c0   ret
```

### What the source says

Pinned xnu `d8b80295118ef25ac3a784134bcf95cd8e88109f`,
`libkern/c++/OSMetaClass.cpp` (`instanceConstructed`, lines ~984-990):

```cpp
void
OSMetaClass::instanceConstructed() const
{
    // if ((0 == OSIncrementAtomic(&(((OSMetaClass *) this)->instanceCount))) && superClassLink)
    if ((0 == OSIncrementAtomic(&instanceCount)) && superClassLink) {
        superClassLink->instanceConstructed();
    }
}
```

The compiler turned the recursive call into the loop above. Field offsets are confirmed by the
`OSMetaClass` constructor at `0xfffffff007837990`:

```
fffffff0078379c4  29047c03   stp  w3, wzr, [x0, #0x20]   ; +0x20 classSize, +0x24 instanceCount = 0
fffffff0078379c8  f9000802   str  x2, [x0, #0x10]       ; +0x10 superClassLink (x2 = parent metaclass)
```

So: `+0x24` = `instanceCount`, `+0x10` = `superClassLink`. This is pure metaclass bookkeeping
(instance counts along the superclass chain, used for leak/instance accounting and kext-unload
safety). It is **not required for constructing the `IOWorkLoop` object**; the object vtable store
and the `init` call do not depend on it.

## 4. Why it can fault on a non-Apple boot (hypotheses, ordered)

1. **Metaclass constructors/`__mod_init_func` not (fully) run or not correctly ordered on the
   format-2 prelink path.** `IOWorkLoop::gMetaClass` lives in `__DATA,__common` BSS; if its
   `OSMetaClass` constructor did not run, `superClassLink` is 0 and the loop is safe. If some
   constructor ran while its parent metaclass was not yet constructed, the chain can contain a
   zero object (still safe) — but if the chain contains a **stale/garbage pointer**, the second loop
   iteration executes `ldxr/stxr` on `garbage+0x24` and faults. A stale pointer is plausible if the
   format-2 kernel image's prelink pointers are not slid/relocated or if a constructor was skipped.
2. **A metaclass in the chain is in read-only memory.** Metaclass globals from Apple/prelinked kexts
   (`__PLK_DATA_CONST`, `__DATA_CONST`) are `r--` in this image (`__DATA_CONST` initprot `1`,
   `__PLK_DATA_CONST` initprot `1`). `instanceConstructed` writes `instanceCount` in every chain
   element; if a chain element is one of those read-only metaclasses, the `stxr` faults even though
   the pointer is perfectly valid. This would be invisible on Apple's direct-boot path (its
   metaclass chain ends before reaching a read-only element) but can happen with the format-2
   prelink metadata.
3. **The `instanceCount`/BSS page itself is not writable/mapped as expected in the early IOKit
   window.** DarwinBoot zeroes the window, but the kernel's own pmap mapping of `__DATA`/BSS must be
   writable by the time `workLoop` constructs objects; a permission/mapping mismatch makes the
   first `ldxr/stxr` fault (marker M1 below freezes while entry marker resets).
4. **Chain cycle / non-terminating chain.** If a `superClassLink` cycle exists, the loop never
   reaches the epilogue and the device hangs (no fault; marker M3 never fires). Candidate fix F1
   (stop after the local class) avoids it.

Hypothesis 2 is the most XNU-specific: the code is correct only if every metaclass in the chain is
in writable `__DATA`; Apple's prelink guarantees that, a hand-assembled format-2 kernel may not.
Hypotheses 1/3 are boot-path issues; hypothesis 4 is a data-initialization order issue.

## 5. Next PSCI-marker targets (bisect inside the body)

Marker encoding (verified with `llvm-mc -triple=arm64`):

```
movz w0, #0x8400, lsl #16   -> 00 80 b0 52
movk w0, #9                 -> 20 01 80 72
smc  #0                     -> 03 00 00 d4
12-byte PSCI marker         -> 00 80 b0 52 20 01 80 72 03 00 00 d4
```

Patch the kernel **file offset** shown; all addresses are unslid VAs in the loaded kernel (the
kernel is loaded at `VirtualBase = 0xfffffff00427c000`, so the code executes at these VAs; the PSCI
reset happens before any address translation issue from the marker itself). Use **one marker per
build** — the first reset ends the run.

| Pri | Marker target (VA) | File offset | Replaces (current 12 bytes) | What reset means | What freeze means |
| --- | --- | --- | --- | --- | --- |
| 1 | `0xfffffff007838468` (M1: after `OSIncrementAtomic` returns) | `0x834468` | `60 00 00 35 73 0a 40 f9 93 ff ff b5` | prologue + first `OSIncrementAtomic` succeeded; fault is after this (chain load/loop or caller) | fault **inside `OSIncrementAtomic`** (M1 not reached): `this+0x24` is not a writable mapped address (hypothesis 3) |
| 2 | `0xfffffff007838470` (M2: after `ldr x19,[x19,#0x10]`) | `0x834470` | `93 ff ff b5 fd 7b 41 a9 f4 4f c2 a8` | the first `superClassLink` load succeeded (`ldr` did not fault); fault is in the recursive walk/loop or after return | fault at the `ldr [x19,#0x10]` — `gMetaClass` or its `superClassLink` field is at an invalid address |
| 3 | `0xfffffff007838474` (M3: epilogue — chain reached null) | `0x834474` | `fd 7b 41 a9 f4 4f c2 a8 c0 03 5f d6` | `instanceConstructed` completed the whole chain and is returning; if `init` still freezes, fault is after the return in `workLoop` (object/vtable path/in `init` prologue) | the chain-walk did not terminate: cycle or a later chain element's `OSIncrementAtomic` faulted (hypothesis 2/4). Compare with M2: M2 reset + M3 freeze = a later iteration dies |
| optional 0 | `0xfffffff007838460` (M0: before the atomic call) | `0x834460` | `60 92 00 91 4f fa ff 97 60 00 00 35` | prologue + `mov x19,x0` executed; first atomic yet to run | fault in prologue/stack (should be impossible; rules out stack corruption) |

Marker patch snippets (Python, offline; backup first):

```python
from pathlib import Path
p = Path('EFI/UniXNU/Payloads/kernel.macho')
MARKER = bytes.fromhex('00 80 b0 52 20 01 80 72 03 00 00 d4')
patches = {
    0x834468: bytes.fromhex('60 00 00 35 73 0a 40 f9 93 ff ff b5'),  # M1
    0x834470: bytes.fromhex('93 ff ff b5 fd 7b 41 a9 f4 4f c2 a8'),  # M2
    0x834474: bytes.fromhex('fd 7b 41 a9 f4 4f c2 a8 c0 03 5f d6'),  # M3
    0x834460: bytes.fromhex('60 92 00 91 4f fa ff 97 60 00 00 35'),  # M0
}
off = 0x834468  # choose one
data = bytearray(p.read_bytes())
assert bytes(data[off:off + 12]) == patches[off], 'unexpected bytes, wrong image/revision'
data[off:off + 12] = MARKER
p.write_bytes(data)
```

Then rebuild/refresh the payload FAT member (`EFI/UniXNU/Payloads/kernel.macho`) inside the
format-2 super image (`build/super-format2-t27.img`, J2 `payload` member) and boot that image.
Keep a backup copy; verify bytes with `llvm-objdump` or a hexdump before flashing.

## 6. Candidate binary fixes (test in this order)

These are diagnostic workarounds for the device boot, not the production fix. All offsets are in
`kernel.macho`; current bytes were verified against `tmp/k51.nm` + `__TEXT_EXEC`
(`vmaddr 0xfffffff007244000`, fileoff `0x240000`). The `__TEXT_EXEC` mapping is
`file_offset = VA - 0xfffffff007244000 + 0x240000`.

### F1 — stop the superclass-chain walk (narrowest test)

At `0xfffffff00783846c` (file offset `0x83446c`) replace the `ldr x19,[x19,#0x10]` with
`mov x19, xzr`:

```
current: 73 0a 40 f9   ldr x19, [x19, #0x10]
new:     f3 03 1f aa   mov x19, xzr
```

Wait — `mov x19, xzr` encoding: `0xaa1f03f3` → little-endian bytes **f3 03 1f aa**. Yes.

Effect: after incrementing the local `gMetaClass` instance count, `x19 = 0`, so `cbnz x19` falls
through to the epilogue and `instanceConstructed` returns without touching any parent metaclass.
The counter bookkeeping for superclasses is skipped (diagnostic only). If the fault is a bad/
read-only superclass pointer (hypothesis 1/2), this should let `workLoop` reach the `init` call.

```python
off = 0x83446c
old = bytes.fromhex('73 0a 40 f9')
new = bytes.fromhex('f3 03 1f aa')
```

### F2 — skip the `instanceConstructed` call in `workLoop` (fast isolation)

At `0xfffffff0078c7930` (file offset `0x8c3930`) NOP the `bl instanceConstructed`:

```
current: c8 c2 fd 97   bl 0xfffffff007838450
new:     1f 20 03 d5   nop
```

Optional companion for `workLoopWithOptions` at `0xfffffff0078c79b4` (offset `0x8c39b4`):
`a7 c2 fd 97` → `1f 20 03 d5`.

Effect: `workLoop` skips the metaclass bookkeeping entirely and goes straight to the `init` call
through the (verified) vtable slot. If the device then reaches the `init` marker/boots further,
the fault is exactly the metaclass bookkeeping; F1 is the narrower alternative. If it still dies,
the fault is in the object/vtable/init path (M3 result confirms).

```python
# workLoop
off = 0x8c3930; old = bytes.fromhex('c8 c2 fd 97'); new = bytes.fromhex('1f 20 03 d5')
# workLoopWithOptions (optional)
# off = 0x8c39b4; old = bytes.fromhex('a7 c2 fd 97'); new = bytes.fromhex('1f 20 03 d5')
```

### F3 — skip `instanceConstructed` body globally (diagnostic last resort)

At function entry `0xfffffff007838450` (offset `0x834450`) replace the first 12 bytes with
`ret; nop; nop`:

```
current: f4 4f be a9 fd 7b 01 a9 fd 43 00 91   (stp/stp/add prologue)
new:     c0 03 5f d6 1f 20 03 d5 1f 20 03 d5   (ret; nop; nop)
```

This affects every caller (the binary has hundreds of direct `BL` sites to
`instanceConstructed`, including `workLoop` at `0x78c7930` and `workLoopWithOptions` at
`0x78c79b4`), so use it only to prove that this function is the blocker; it leaves all instance
counts untouched and is **not** a production fix.

## 7. Recommended device-test matrix (one image per row, no device ops here)

| Image | Patch | Question answered |
| --- | --- | --- |
| A | M1 marker `0x834468` | Is the first `OSIncrementAtomic` the fault? (freeze) vs bookkeeping chain/caller (reset) |
| B | M2 marker `0x834470` | Does the first `superClassLink` load fault? |
| C | M3 marker `0x834474` | Does the chain terminate (reset) or loop forever/die later (freeze)? |
| D | F1 chain-stop `0x83446c` | Does skipping the superclass walk let `init` run? |
| E | F2 NOP call `0x8c3930` | Does skipping the bookkeeping entirely let `init` run? (then F1 is the narrow fix) |
| F | F3 entry ret `0x834450` | Global proof/diagnostic only |

Interpretation shortcut:
- M1 freeze → atomic/BSS mapping issue (hypothesis 3); F1/F2 won't help; inspect kernel mapping of
  `__DATA`/BSS or run `__mod_init_func` initialization.
- M1 reset, M2 freeze → `ldr [x19,#0x10]` on `gMetaClass`; inspect `IOWorkLoop::gMetaClass` address
  mapping/relocation (BSS section `__DATA,__common`, zeroed window).
- M2 reset, M3 freeze → the walk reaches a later chain element and dies there; the chain contains a
  bad/read-only/cyclic parent pointer. F1/F2 should avoid it; then fix metaclass initialization.
- M3 reset, but `init` marker still not reached → fault after the function return, between
  `0x78c7934` and `0x78c7940`: object vtable load or `blr` to `init`; inspect object pointer x19 /
  vtable mapping (although vtable slot `+0x68` is verified as `0x78c77d0` in this image).

## 8. Practical notes

- The init vtable slot is confirmed correct (`0xfffffff0071c6898` contains
  `0xfffffff0078c77d0`); a “not reached” init marker therefore cannot be explained by a wrong slot
  address, only by a fault before the `blr` or a bad object/vtable mapping.
- The `IOWorkLoop::gMetaClass` object is in `__DATA,__common` BSS (`0xfffffff007b69a58`), which
  DarwinBoot zeroes as part of the kernel window. If the kernel's `__mod_init_func` C++ constructors
  are not executed on the format-2 path, this object remains zero and `instanceConstructed` is
  harmless; therefore the most interesting hypotheses are a **partially-initialized/relocated
  metaclass chain** (hypothesis 1/2) or a **BSS write/mapping fault** (hypothesis 3), both of which
  the marker matrix above distinguishes cheaply.
- Source reference used: pinned xnu `d8b8029…` `libkern/c++/OSMetaClass.cpp`
  `instanceConstructed()` (the local `.tools/xnu-8796` copy is byte-identical for this function;
  header at `.tools/xnu-8796/libkern/c++/OSMetaClass.h`).
- No device operations: the doc describes offline byte patches only. Apply to a copy of
  `kernel.macho`, refresh the J2 `payload` FAT member in `build/super-format2-t27.img`, and keep the
  original image for comparison.
