#!/usr/bin/env python3
"""Apply the doc/porting updates of the dada clone recipe with UTF-8 I/O."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def edit(rel, pairs):
    path = ROOT / rel
    text = path.read_text(encoding='utf-8')
    for old, new in pairs:
        if old not in text:
            print(f'WARN {rel}: pattern not found: {old[:60]!r}')
        text = text.replace(old, new)
    path.write_text(text, encoding='utf-8')
    print(f'updated {rel}')


def dedupe_board():
    path = ROOT / 'board.toml'
    lines = path.read_text(encoding='utf-8').splitlines()
    out, seen = [], set()
    for line in lines:
        if line.startswith('trust_cache_sha256 = ') and line in seen:
            continue
        if line.startswith('trust_cache_sha256 = '):
            seen.add(line)
        out.append(line)
    path.write_text('\n'.join(out) + '\n', encoding='utf-8')
    print('deduplicated board.toml trust_cache pin')


def main():
    dedupe_board()
    edit('README.md', [
        ('''5. **AMFI-less entitlement guards** (dada patches) and luming display/input components are needed
   before userland exec and GUI.''',
         '''5. **AMFI/PMGR/owner-cache path** follows dada's proven restored-AMFI shape (27 prelink roots,
   `early_security_init`, trust-cache pin, copied `build-luming-platform-power.py`/storage builders).
   The no-AMFI entitlement-guard patches are fallback only; UI still needs display/input components.'''),
    ])
    edit('docs/KNOWN-VALUES.md', [
        ('''| AMFI | intentionally NOT prelinked (dada no-AMFI configuration); trust-cache runtime off; AMFI-less entitlement guards required before userland exec | DADA; GAP-LIST #9 |''',
         '''| AMFI/PMGR | **restored to the proven dada shape**: 27 prelink roots include AppleMobileFileIntegrity + ApplePMGR + sandbox + AppleImage4; `early_security_init` = profile value; trust-cache runtime on; copied `build-luming-platform-power.py` publishes the ApplePMGRNub | DADA `docs/known-values.md` "Trust cache lock"/"PMGR instrument"; clone recipe §2 |
| Trust-cache pin | `7416ca4f...a7323a7` (21H461 bundle of two v2 modules); payload `--trust-cache` input, never stored in the repo | profile `[payload] trust_cache_sha256`; clone recipe §2.2 |'''),
    ])
    edit('docs/GAP-LIST.md', [
        ('''| 9 | P1 | **AMFI/PMGR absent by design.** First boot is dada's no-AMFI route; userland `exec` will hit the NULL-AMFI entitlement path (`IOTaskHasEntitlement`, `IOUserClient::copyClientEntitlement`) without dada's AMFI-less guard patches. | userland exec (launchd) in the S6/S7 phase | dada's `patches/xnu/zzzzz-dada-entitlements-without-amfi.patch` + `zzzzzz-dada-more-amfi-null-guards.patch` (not cached) or the sheng AMFI+PMGR instrument (`build-sheng-platform-power.py` analogue) | dada repo `patches/xnu/`; sheng `scripts/build-sheng-platform-power.py` |''',
         '''| 9 | P1 | **AMFI/PMGR/owner-cache path must be validated on SM8735.** The skeleton now copies dada's proven shape: 27 prelink roots incl AMFI+PMGR, `early_security_init`, trust-cache runtime on, owner-cache/union switches and UUIDs, `build-luming-platform-power.py` (same kernelcache/slide addresses as DadaPlatformPower), trust-cache pin. It has never run on luming. | userland exec/root chain | run the copied builders/patches; verify PMGR bindings against luming's prelink; fallback: the copied AMFI-less guard patches (inactive in the device series) | `patches/xnu/device/series`, `scripts/build-luming-platform-power.py`, `firmware/patches/`; clone recipe §2.2 |'''),
        ('''| 15 | P2 | **Trailing `[kernel.prelink] early_security_init = ""` semantics unverified.** Clearing an inherited profile scalar in format 2 has not been tested against the resolver. | prelink may still carry the AMFI initializer (or reject an empty value) | the dada→luming clone recipe's exact key/clearing idiom, then validate with `unixnu status --json` | `agents/official-crawl/recipe/REPORT-DADA-CLONE-RECIPE.md` (pending); dada `docs/known-values.md` "Why AMFI is not prelinked" |''',
         '''| 15 | P2 | **Prelink values are copied, not re-measured.** `[kernel.prelink]` copies dada's current 27-root AMFI+PMGR shape and `early_security_init` (same 21H461 kernelcache/slide), but the resolver has not run against this board yet. | G2 prelink gate | `unixnu status --json` + prelink report must show 27 roots incl AMFI+PMGR and the early-security initializer; compare with the dada reference `docs/evidence/kernel-build.json` | `agents/official-crawl/recipe/cache/dada-full/docs/evidence/kernel-build.json`; clone recipe §2.1 |'''),
    ])
    edit('docs/A-FIX-CROSSWALK.md', [
        ('''| a12 | **`com.apple.driver.AppleMobileFileIntegrity`/`ApplePMGR` removal from prelink roots** | dada reference (`docs/reference/dada-known-values.md`); no AMFI panic `AMFI: No PMGR?y` | This one **is** carried forward: board.toml `[kernel.prelink] roots` is dada's 24-root no-AMFI set; `early_security_init` is cleared. |''',
         '''| a12 | **`com.apple.driver.AppleMobileFileIntegrity`/`ApplePMGR` restore in the prelink roots** | dada current HEAD / clone recipe §2.1: 27 roots incl AMFI+PMGR+sandbox+AppleImage4, `early_security_init` restored, trust-cache runtime on; the earlier 24-root no-AMFI variant is documented history and dead-ends after launchd | Carried forward as the proven shape: board.toml `[kernel.prelink]` 27 roots + early init; defconfig trust-cache/owner switches; copied `build-luming-platform-power.py`; trust-cache pin |'''),
        ('''| b11 | **iOS16 20H392 SHNGROOT userdata image** (`build/ios16-root/luming/userdata/userdata-root.img`) | `agents/roots-userspace/route-b/verified-inventory.json` | Not used on the chosen route (Lead decision: official iOS17-era profile, sheng SHNGROOT recipe); recorded in `docs/KNOWN-VALUES.md` #4 as retired alternative | Reusable only if the project ever returns to an iOS16/Darwin22 profile. |''',
         '''| b11 | **iOS16 20H392 SHNGROOT userdata image** (`build/ios16-root/luming/userdata/userdata-root.img`) | `agents/roots-userspace/route-b/verified-inventory.json` | Not used on the chosen route (official iPadOS 17.7.11 profile; sheng SHNGROOT recipe); recorded in `docs/KNOWN-VALUES.md` #4 as retired alternative | Reusable only if the project ever returns to an iOS16/Darwin22 profile. |'''),
    ])
    edit('docs/UFS.md', [
        ('## Component shape (from dada\'s proven DadaUfs)', '## Component shape (from dada\'s proven DadaUfs, copied into drivers/LumingUfs)'),
    ])
    edit('porting.toml', [
        ('dada-shaped no-AMFI kernel configuration', 'dada-shaped AMFI+PMGR kernel configuration'),
        ('the closest no-AMFI source-XNU format-2 device', 'the closest proven source-XNU format-2 device (AMFI+PMGR restored)'),
        ("the no-AMFI first boot may need dada's AMFI-less entitlement guards before userland exec", 'the owner-cache/union and trust-cache path must be validated on SM8735; the copied AMFI-less guards are fallback only'),
        ('SHENG_PMGR is off; there is no luming PMGR instrument for the AMFI/PMGR path yet.', 'SHENG_PMGR is on; the copied build-luming-platform-power.py (DadaPlatformPower, same kernelcache/slide addresses) publishes the ApplePMGRNub; untested on SM8735.'),
        ('Without PMGR, AMFI panics with \'AMFI: No PMGR?y\'; the no-AMFI configuration avoids it but requires entitlement guards for userland exec.', 'The copied PMGR instrument must satisfy AMFI on SM8735; the copied AMFI-less entitlement guards are the fallback only.'),
    ])
    print('docs recipe applied')


if __name__ == '__main__':
    main()
