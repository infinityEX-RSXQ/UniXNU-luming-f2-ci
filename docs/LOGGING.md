# LOGGING — real, upstream log paths for the luming format-2 build

Goal (user requirement): no hand-made probes. Every path below is an **upstream UniXNU/XNU
facility** that the sheng/dada reference boards ship, switched on and documented here. Device
operations to read logs after a boot are approval-gated; this document only defines paths and
procedures.

## 1. Log paths: ON / OFF / missing

| Path | Mechanism | State | Config / boot arg |
| --- | --- | --- | --- |
| **Video console** | DarwinBoot fills `boot_args.Video[6]` from the UEFI GOP; XNU `pexpert` draws kprintf/panics there | **ON** (upstream default) | `-v`, `debug=0x14e`. No display component needed (dada's first boot does this). |
| **UFS periodic log writer** (`BootLog.c` + `BootProcessProbe.c`) | every 2 s writes the kernel message buffer + board process rows into the **last 32 MiB of the userdata/root partition** | **ON** | `CONFIG_XNU_LUMING_BOOT_LOG=y`, `luming-log=1` (opens the driver log window; without it the writer refuses) |
| **Panic/exec ring flush** (upstream device patch `zzzz…-luming-ufs-log.patch`) | an in-kernel 256 KiB ring fed by `cons_putc`; flushed to the same UFS window on `PE_panic_hook` and around `load_init_program`/`execve` | **ON** | same `luming-log=1`; format `LUMINGL1` |
| **Panic screen** | payload patches the kernel copy: panic message + registers drawn to the framebuffer and kept visible (no auto-reset) | **ON** | board `[payload] panic_screen = true` (sheng reference; dada ships false, so this is [adapted sheng]). Build evidence: `logs/payload-patch.log`. |
| **Panic backtrace** | XNU panic prints formatted backtrace to console/panic screen/UFS ring | **ON** | `keepsyms=1`, `debug=0x14e`, `-v` |
| **Serial console** | XNU `serial=3` console selection | **Requested, [missing] backend** | `serial=3` in `kernel_args`. Upstream format-2 has no GENI UART console driver; the luming UART is GENI at `0xA9C000` (DTS node exists, no format-2 driver). Only the QEMU `VirtIO` console (`CONFIG_XNU_NATIVE_VIRTIO_CONSOLE=n`) exists upstream. |
| **Boot-progress screen** | upstream `boot-progress` rows/panels (sheng uses it) | **[missing] intentionally off** | `CONFIG_XNU_BOOT_PROGRESS=n`: `scripts/build-xnu-4k-baseline.sh` gates it on the audited owner-root/Virtio-block/source-corecrypto set; this board does not carry that yet (dada also keeps it off). Boot log/console still work without it. |
| **Firmware/UEFI log (AI9 fallback)** | AdvancedLogger + QR screen in the UEFI FD | **available fallback** | `agents/uefi-log/artifacts-ai9/Mu-luming-0.img`, `agents/uefi-log/REPORT-AI9.md`; scan the QR with a second phone (OneSend). Captures the **firmware** log before ExitBootServices, not XNU logs. Use it if the video console never appears. |

No `printf`-patching, marker injection or binary probe is used by this build for logging.

## 2. UFS log window: location and format

The driver opens the log window only when `luming-log=1` is in the boot arguments
(`LumingUfs.cpp`, `native_ufs_log_open`):

- root partition = GPT partition **`userdata`** (LUN 0), 4096-byte blocks, measured LBAs
  `3,124,736 .. 128,619,514` (478.7 GiB).
- window = the **last 8192 blocks (32 MiB)** of that partition:
  `first_lba = userdata.last_lba + 1 - 8192`.
- immediately below it, 256 MiB are reserved as the export region; the Data store stays below both
  (`luming-log-reserve=<MiB>`, default 1024).
- absolute LBAs are stored in the window header, so a reader does not need the partition geometry
  if it reads the right window.

Two writers share block 0 (last writer wins the header); `read-luming-log.py` recognises both:

| Magic (8 bytes, block 0) | Writer | Layout |
| --- | --- | --- |
| `LUMINGL2` | periodic `BootLog.c` (2 s) | header block 0; kernel message buffer blocks 1..128 (`LogMsgBlocks=128`); board text slots from block 129, 16 blocks each in a ring |
| `LUMINGL1` | panic/exec ring (`printf.c` patch) | header block 0: `len` at 8, `status` at 24, `first_lba` at 32, `value` at 40, reason at 64; text blocks 1..N (up to 256 KiB / 64 blocks) |

## 3. Read-back procedure (after a boot; approval required)

The window is the tail of `userdata`; extract only the last 32 MiB (never the whole 478 GiB).

### Recovery / adb-root route (recommended)

```sh
# 1. Boot the recovery (OrangeFox) or an adb-root context; identify the userdata block device.
adb shell 'ls -l /dev/block/by-name/userdata'
# 2. Size in 4096-byte blocks (blockdev --getsize64 gives bytes).
adb shell 'blockdev --getsize64 /dev/block/by-name/userdata'      # e.g. 513762568192
# 3. Dump only the last 8192 blocks (32 MiB) into /tmp and pull it.
adb shell 'SIZE=$(blockdev --getsize64 /dev/block/by-name/userdata); \
           SKIP=$(( SIZE/4096 - 8192 )); \
           dd if=/dev/block/by-name/userdata of=/tmp/luming-log.bin bs=4096 skip=$SKIP count=8192'
adb pull /tmp/luming-log.bin
# 4. Decode.
python agents/f2-luming/scripts/read-luming-log.py luming-log.bin --output logs/luming-log
```

If `blockdev` is unavailable, use `/sys/class/block/<dev>/size` (512-byte sectors):
`SKIP=$(( $(cat /sys/class/block/sda36/size)/8 - 8192 ))`.

### Host-image route

If the userdata image is available on the host (e.g. the built `ios16-root.simg`/`userdata` image),
the reader accepts the whole image or any file whose tail is the window:

```sh
python agents/f2-luming/scripts/read-luming-log.py path/to/userdata.img --output logs/luming-log
```

Outputs: `window.bin` (raw 32 MiB), `header.json`, `message.txt` (kernel message buffer),
`board.txt` (newest board text rows). `read-luming-log.py` errors with
`no LUMINGL2/LUMINGL1 header` when the window was never opened (check `luming-log=1` and the driver
log window/root layout).

## 4. luming-specific risks and fallbacks

1. **Early boot before the UFS driver**: the video console/panic screen are the only log paths
   until `LumingUfs` publishes the root layout. If the video console does not appear (GOP hand-off
   or FB mapping failure), no XNU log can be persisted; fallback = AI9 firmware QR logger
   (`agents/uefi-log/artifacts-ai9/Mu-luming-0.img`) or the upstream panic screen once a kernel
   reaches panic.
2. **FB/console mapping (fixed in source)**: DarwinBoot passes the GOP framebuffer as a physical
   address without the iBoot `b0` marker (`0xFC800000`, an even value). Upstream XNU's
   `osfmk/console/video_console.c initialize_screen()` treated even values as virtual after VM init
   and died silently; the device patch `patches/xnu/device/zzzzz-fix-darwinboot-physical-framebuffer.patch`
   now treats non-kernel-VA values as physical. Expected geometry remains FB `0xFC800000`, stride
   4944, 1236×2750 (docs/KNOWN-VALUES.md #5). If the console is still blank, verify
   `boot_args.Video[6]` in the payload log and fall back to the AI9 QR path.
3. **UFS log window depends on the UFS/root path**: `luming-log=1` opens only after the driver has
   read the GPT/root layout (`native_ufs_log_open` → "no root layout" otherwise). First milestone
   therefore relies on the video console/panic screen for bring-up; the UFS log becomes active at
   the storage milestone.
4. **Serial**: `serial=3` is recorded in the kernel args but there is no GENI console backend in
   format 2; the DTS node `serial@a9c000` and the A-line GENI patch are the inputs for a future
   upstream GENI console component. Until then do not rely on serial output.

## 5. CI enforcement

`scripts/check-luming.py` has a **log observability gate**: it fails if any of
`CONFIG_XNU_LUMING_BOOT_LOG`, `CONFIG_XNU_DT_PANIC_REGION`, `CONFIG_XNU_NATIVE_CS_HASH_CACHE`,
`CONFIG_XNU_NATIVE_UFS`, `CONFIG_XNU_NATIVE_RAM_BLOCK` are off, if `panic_screen` is false, if
`luming-log=1`/`serial=3`/`keepsyms=1`/`debug=0x14e` disappear from `kernel_args`, if the BootLog
sources or the reader/format pair (`LUMINGL2`/`LUMINGL1`) stop matching, or if this file disappears.
