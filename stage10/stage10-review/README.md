# Stage10 independent build review

2026-11-01. No device operations and no changes to the main device repository,
the pinned shared core, or original Apple binaries.

The current stage10 Legacy/GOP design remains the better starting point than
`D:/civitoip20/tmp/display-port`. The latter's own integration record says its
three original-class addresses did not verify against the exact 21H461 cache;
its statement that a Legacy header is missing predates the stage10 generator,
which now derives and qualifies that header from the pinned raw cache.

## Defects found and corrected

1. **Duplicate symbols in the force-loaded archive.** The backend's
   `extern "C" { volatile uint64_t ...; }` defined the two early-retirement
   counters, while the probe defined them again. The runtime owner changed the
   backend to `extern` storage declarations, retaining one probe definition.
   `check_duplicate_link.py` compiled two minimal ARM64/iOS17 Mach-O objects;
   ld64.lld reproduced both duplicate-symbol errors, then linked successfully
   after the declaration fix. `duplicate-link-proof.json` contains the commands
   and outputs. This is a link-language proof, not the full kernel link.

2. **Native class compile replay could overwrite kernel build records.**
   The trimmed builder called the pinned shared `build-arm-driver.py`, whose
   replay retained `-MF`, `-MT`, and `-MJ` operands pointing at IOPlatformExpert
   outputs. The earlier stage10 trimming only removed them from the later probe
   replay. The owned builder and its preparation generator now use one
   `compile_owned`/`replay_command` implementation for both owned compilations.
   It keeps actual target/sysroot/language/ABI flags and CWD, isolates source and
   object outputs, strips separate and joined dependency/JSON destinations,
   preserves include paths, and verifies ordinary ARM64/iOS17 object headers.
   The shared core is unchanged.

`check_compile_replay.py` executes those exact helpers extracted from the builder
AST against a fixture. Two tiny owned ARM64/iOS17 objects compile; original JSON
and dependency sentinels remain byte-identical; generated `.d` files stay under
the owned output directory; bad output operands are rejected. Re-running the
preparation generator produces byte-identical builder source. Results are in
`compile-replay-validation.json`.

## Other checks completed

- Python syntax checks passed for builder, preparation generator, and installer.
- All retained surface/refresh/vsync/original constructor/code guards reran
  against the exact raw original cache and passed. The corresponding updated
  result remains in `../stage10-build/original-binding-guard-validation.json`.
- `check_family_only_rejection.py` tested the existing `c8558617…` kernel. The
  stage10 qualifier correctly refuses it because it lacks defined
  `_native_legacy_display_probe`; adding IOMobileGraphicsFamily alone is not a
  display implementation. See `family-only-rejection.json`.
- Core hooks/load order, 28-root selection, late archive force-load path, source
  hashing, 358-slot ABI generation, and preserved stage9 payload gates were
  inspected. No additional proven build blocker was found in this review.

## Remaining limits

The complete NativeLegacyDisplay/Probe C++ objects have not been compiled against
the generated native XNU headers on macOS by this review. Full archive/link,
prelink, service publication, CADisplay enumeration, swap completion, and pixels
remain unverified. Registration-only tests need the real boot arguments from the
runtime contract and should keep console handoff disabled until publication is
observed. The CPU provider does not itself supply general GPU/Metal rendering.

Modified files owned by this subtask:

- `../stage10-build/build-luming-cpu-legacy-display.py`
- `../stage10-build/prepare_trimmed_builder.py`
- `../stage10-build/README.md`

The runtime counter correction was performed by the runtime owner, not this
review. No packer, image, CI workflow, or target device was changed here.
