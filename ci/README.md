# Public CI build repository — provenance and private inputs

This repository is a **code-only public build mirror** of the luming format-2 device tree.
It contains only our own source (board/configs/DTS/patches/scripts/kits/docs) and the GitHub
Actions workflow needed to build the format-2 kernel, payload and Android v4 boot image.

It deliberately contains **no Apple kernelcache, no IPSW-derived binary, no Xiaomi vendor
`Binaries/luming`, and no 385 MB UEFI bundle**. Those inputs are fetched at run time from the
private repository `infinityEX-RSXQ/UniXNU-luming-f2` release assets with the fine-grained
`PRIVATE_REPO_TOKEN` Actions secret (contents: read-only). Every downloaded asset is checked
against the sha256 passed to the workflow before use:

- kernelcache asset: `kernelcache.macho`, expected sha256
  `f18b4df865405f2a287b84977d7aca745e056d656d9fc9df1662970ce2969de7`
- diagnostic UEFI bundle asset: `uefi-luming-ci-diag.tar.gz`, asset id 686763008
(private release `uefi-luming-ci-diag`), expected sha256
  `109777c2e2f20693a06b7e274cde6147eb38113af1f90b3ec3cd39017fa2ebd4`

Workflow artifacts are intentionally **not uploaded** from this public repository by default:
they can contain Apple-derived kernel material and the Xiaomi firmware volume. The job summary
and logs print only hashes and sizes. Set `upload_artifacts=true` only if an authorised private
destination is configured.

No device operations, no flashing. The boot image is for RAM-only `fastboot boot` testing of
the format-2 luming port.
