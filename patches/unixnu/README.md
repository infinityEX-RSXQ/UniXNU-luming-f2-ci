# patches/unixnu — UniXNU-side patches this board needs

These patches are **not** xnu patch series. They modify the UniXNU tool/scripts and are applied to
a UniXNU checkout (or proposed upstream) before "kernel/firmware/payload/bootimg" steps. They are
copied references from the proven dada route; re-derive them against the pinned UniXNU commit.

| File | Purpose | Status |
| --- | --- | --- |
| `unixnu-bootimg-header-v4.patch` | verify Android boot image header v4 (luming's stock header) in the boot-image step | [adapted] dada reference |
| `unixnu-kern-exit-owner-cache.patch` | owner-cache exit hook used by the owner-root/verified root path | [adapted] reference; only needed when VerifiedRoot is active |
| `unixnu-adt-pram-asmb.patch` | [missing] proposed format-2 ADT converter extension: emit a `/pram` node and a `/chosen/asmb` child (`lp-sip0=0x6f`, `lp-sip1=1`) from typed board tables - required to land the A-line ADT findings (docs/A-FIX-CROSSWALK.md (b8), docs/GAP-LIST.md #6). Do not invent the patch; write it against `scripts/unixnu/devicetree.py` and get it reviewed upstream. | missing |

Apply order matters: run `git -C <UniXNU> apply` with each patch, rebuild/`fetch` as needed, and
record the UniXNU commit. The device CI workflow does not apply these automatically (upstream
clean state is assumed); `docs/FIRST-BUILD-PLAN.md` §0 notes this precondition.
