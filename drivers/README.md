# drivers/ — format-2 component wrappers and luming board drivers

Format 2 resolves components from the official catalog (`UniXNU/components.toml`), the device
module directories (`drivers/<ID>`), or `feeds.toml`/`local.toml` overrides. This skeleton selects
only catalog IDs today; the luming-specific drivers are not ported yet.

## Planned / missing

| Directory | Component | Source that exists in this workspace | What is missing |
| --- | --- | --- | --- |
| `drivers/LumingUfs` [missing] | board fork of the sheng UFS transport (dada calls its equivalent `DadaUfs`) | `agents/nativeufs-fix/patches/0001-0002`, `agents/ufs-ci` NativeUfs SM8735 probe/stage-0 integration, `UniXNU-luming/scripts/build-native-ufs-bindings.py` | a format-2 component entry in `UniXNU/components.toml`, a build recipe (`build-arm-driver.py` analogue), the storage-class/kext-binding archive step copied from dada, and publishing the source |
| `drivers/LumingPlatformPower` [missing] | sheng PMGR/ApplePMGRNub equivalent so AMFI can be enabled later | format-1 `UniXNU-luming` TODO only; sheng `scripts/build-sheng-platform-power.py` | the same candidate-based builder port + prelink candidates; not needed for the no-AMFI first boot |
| `drivers/LumingDisplayTouch` [missing] | luming panel/backlight + touch/keys input | A-line display markers, `agents/c-ios16-star` display notes; the stock luming DT touch node | a format-2 display component (GopFramebuffer is SM8550/Adreno-adjacent) and an input component; docs/GAP-LIST.md #4/#5 |

## Catalog components already selected (no local wrapper needed)

`ArmDTPlatform`, `ArmCpu`, `SoftwareAES`, `ShengUfs` (placeholder for LumingUfs),
`RamBlock`, `VerifiedRoot`, `XnuPrelink`, `DarwinBoot` are resolved from the official catalog and
component submodules, as in sheng/dada. Add a `drivers/<ID>` submodule only when the board owns a
fork; keep `.gitmodules` pins by canonical catalog ID (dada reference).

## How to add a board driver without publishing (local testing)

1. Create `drivers/<ID>/` with the component sources and a `README.md` describing its runtime
   identifiers (keep original filenames/classes/bundle IDs).
2. Add to `feeds.toml`:
   ```toml
   [[source]]
   name = "<ID>"
   kind = "driver"
   local = "drivers/<ID>"
   ```
3. Add the component ID to `board.toml` `[components].include` and its build command to
   `[kernel].archives` (dada uses `component:<ID>` markers).
4. A catalog entry is required before publishing (official device repositories select canonical
   IDs only); see UniXNU docs/reference/components.md.
