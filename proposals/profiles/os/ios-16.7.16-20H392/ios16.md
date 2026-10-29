# iPhone X iOS 16 目标与当前边界

默认目标为 iOS **16.7.16 / 20H392**，对应[苹果发布记录](https://developer.apple.com/news/releases/?id=05112026j)。IPSW 使用苹果 CDN；BuildManifest 中已实际读取并确认：

| 字段 | 值 |
| --- | --- |
| ProductVersion / ProductBuildVersion | 16.7.16 / 20H392 |
| SupportedProductTypes | iPhone10,3、iPhone10,6 |
| 本仓库选择的 Erase 身份 | d22ap，ApBoardID 0x06，ApChipID 0x8015 |
| KernelCache 成员 | kernelcache.release.iphone10b |
| DeviceTree 成员 | Firmware/all_flash/DeviceTree.d22ap.im4p |
| OS 成员 | 087-86698-044.dmg |
| Kernel IM4P SHA256 | 2d6a13d040aaf87cec09bb6906d43e9bd8cea951e43d1aa1cd62707dfdc5aaec |

IM4P 的 SHA384 与苹果 manifest 的 Digest 和本仓库 pin 三者匹配。以上仅确认原始 Apple 输入。它不等于该系统能运行在 SM7250。

[目标 Actions run 40262916511](https://github.com/SuzukiR1n/UniXNU-Picasso/actions/runs/40262916511) 的三个任务均成功：格式/DTS/C++ 校验、EFI 应用构建、Apple 输入审计。macOS 实际解压得到 `Darwin Kernel Version 22.6.0; xnu-8796.142.1.703.8~1/RELEASE_ARM64_T8015`，arm64 Mach-O SHA256 为 `2ec297bac95bcba01046fd0148e97e7e5885c05a6c18827f39f534ba375c1221`。完整元数据见 [审计报告](evidence/ios16-input-report.json)。公开源码候选 `8796.141.3` 与该二进制版本不同，ABI 比对仍是必需步骤。

本仓库 OS profile 位于 `profiles/os/ios-16.7.16-20H392/`。启动工具将其复制到锁定官方 checkout 的 profile 目录，保留官方 resolver 不变。公开 Darwin 22 源码 `xnu-8796.141.3`（`1b191cb58250d0705d8a51287127505aa4bc0789`）目前只是**待进行 ABI 比对的源码候选**，不声称它与目标内核的所有私有接口一致。

## 还需要完成的内核工作

1. 用 `scripts/audit-ios16.py --decode` 核对实际内核版本、arm64 类型和 Mach-O 哈希，保存报告。
2. 对 Darwin 22 重建 4 KiB 页、非 Apple CPU、机器层、平台专家、GIC/定时器和安全初始化补丁；当前官方 Darwin 23 补丁不能直接导入。
3. 按 Darwin 22 的真实编译记录构建 ArmDTPlatform、ArmCpu 和所需内核库，修改当前写死 iOS 17 的部署目标与对象审计，不拼接两代内核库。
4. 审计目标 kext 的类布局、导出符号、预链接闭包与 AMFI early initializer。iPad 的内存地址、产品标识、信任缓存和 root UUID 不能沿用。
5. 编译、预链接和 ABI 检查全部通过后，才允许内核入口；UEFI、内存与分区资格项仍需独立完成。

`abi_qualified = false` 和入口门槛明确记录当前状态。只有完成上述移植和证据后才能改为 true。Actions 中的输入审计成功不能替代完整 iOS 16 内核构建。

## 历史宿主机结果

在用户指定 iPhone X iOS 16 之前，[run 40261601315](https://github.com/SuzukiR1n/UniXNU-Picasso/actions/runs/40261601315) 曾对官方 iPadOS 17 / Darwin 23 基线完成配置校验、EFI 应用和 XNU 预链接。其 `kernel.macho` SHA256 为 `5a2fc13eafe3f8efb78863b2b898248e8a4fcc174da63b6125d9d69e68835867`。这是旧目标的宿主机构建结果，不是本目标的 iOS 16 镜像，也没有手机启动测试。
