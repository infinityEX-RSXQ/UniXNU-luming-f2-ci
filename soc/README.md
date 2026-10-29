# UniXNU SM8550 support

Shared Qualcomm SM8550 support for UniXNU: CPU topology, GICv3, UFS and
Adreno 740 resources, GMU operations, GPU SMMU integration, and XNU patches.

`soc.toml` selects `Adreno740` and `AdrenoMetal`. Device repositories supply
memory layout, peripherals, firmware, power policy, and packaging.
`kits/Sm8550Platform` preserves its `ShengGmu*` and `ShengGpuSmmu*` source
filenames and exported symbols. Generated headers supply the selected
device's firmware and power inputs.

Hardware descriptions use the SM8550 DTS at revision
`42f3b40c702abbc37c3a04c95af008cd283aeaf3` of
[sm8550-mainline](https://github.com/ianchb/sm8550-mainline).

Build through the [UniXNU CLI](https://unixnu.com/building).
Read the [device repository specification](https://unixnu.com/porting/device-repository),
[device-tree specification](https://unixnu.com/porting/device-tree),
and [component catalog](https://unixnu.com/reference/components).

## Contents

| Path | Contents |
| --- | --- |
| `soc.toml` | SoC profile and component selection |
| `configs/` | Kernel configuration fragments |
| `dts/sm8550.dtsi` | Shared hardware resources |
| `patches/xnu/series` | Ordered SoC patches |
| `kits/Sm8550Platform/` | GMU, command database, GPU SMMU operations |

Build verification and hardware observations are recorded separately.
sheng is the initial device integration.
