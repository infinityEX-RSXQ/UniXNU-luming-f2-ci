# 给 dsh：Stage14 console 所有权与帧内容取证

## 结论与待证实项

用户转述 `validate accepted=1 reason=0` 和 `copy status=0 bytes=13596000`，与 1236×2750×4 一致。这是 provider 写入路径推进的重要证据，但现有 backend 的无 surface/blank swap 分支也会清黑整屏并产生同样的成功字节日志，不能据此认定是 SpringBoard 图像或确定提交进程。

核对当前 XNU 源码：`pexpert/arm/pe_init.c` 的 kPEReleaseScreen 调 initialize_screen；`video_console.c` 中的 release 分支调用 gc_enable(FALSE)，后者已把 gc_enabled 置 FALSE、调用底层 enable(FALSE)，在图形 console 时设置 disableConsoleOutput=TRUE。因此现有 handoff 并非只有标志位，VT 覆盖目前是待验证假设。`default_fb_surface` 提示也尚无致命调用链证据，不改原版该路径。

`Too many corpses being created` 来自 proc_prepareexit 已进入退出流程后，task_mark_corpse 失败的分支；它不是原始进程退出原因。新增观测不会提高 corpse 上限、禁用 watchdog、跳过签名或假造服务成功。

## 候选源码

1. 保留原 PE_initialize_console release，新增可选 console 核心 latch。设置发生于 VCPUTC 锁内，禁止普通 vcputc 绘制与 gc_enable(TRUE)，拒绝普通 acquire/enable/text/graphics 重接管。panic_active 时放行，以保留 panic 画面。串口输出开关保持原语义；provider 不直接写 disableConsoleOutput。该 latch 不是对任何任意 framebuffer 写入者的全局互斥锁，固件、其他驱动、直接 blit 等仍需以运行时证据判断。
2. CPU 普通 BGRA IOSurface 复制前后，对可见区域的 8×8 网格采样，含首/末像素；计算整数 FNV-1a 摘要，并记录首像素及 grid36 像素。**不是全帧 CRC，也不能只凭摘要判断内容是不是 logo**。源帧再次采样以区分 producer mutation；目标帧与原源帧逐样点比较。前 8 个 CPU 帧连续观测，之后只在 16/32/64/128/256 帧观测，最多 13 次，最后保留的是最后一次采样，不承诺最终物理帧。blank swap 单独计数并断开跨帧比较。
3. 下一次连续采样前，检查目标是否与上次复制后的样点一致，记录 between。它只表示两次 provider 复制之间有内容变化；禁用 handoff 的 console 日志本身也会造成变化，不能单凭 between 非零指认 VT。摘要相同也不证明其余像素正确、面板缓存一致或已扫描显示。
4. 保留 CDX_DISP validate/copy 日志。CDX14FrameSamples 作为 OSData 属性发布到显示服务；字段定义见 ProviderProbe14.h，计数为最佳努力快照，跨线程字段不是原子事务。
5. 按进程名记录 SpringBoard/backboardd/watchdogd/liveactivitiesd 的最近异常 e/c0/c1 和最近退出 namespace/code，每进程各最多输出 4 条异常/4 条退出日志，后续只更新计数和最近值。异常观测位于原 DEVELOPMENT/DEBUG + MACH_BSD 分支内，独立于 pid<=26。不改变原异常或退出处理。
6. 可选首次 handoff 后 15 秒主动 panic，把 VT 状态、最后采样、validate/copy/retire/vsync 和上述服务记录显示出来。明确标记 `CDX14 diagnostic snapshot (intentional)`。没有走到 handoff 则不会安排该快照。它是单次测试诊断，不是正常使用配置。

## CI 接入

沿用 Stage13 成功 run 41320061953、commit 6535914a16f5aa5b8cf88c8e63988403397face0 的原始 checkout 与同一套 pins。将本目录放为 device/stage14，安装顺序：

```
python3 device/stage11/install_stage11.py --device device --apply
python3 device/stage12/install_stage12.py --device device --apply
python3 device/stage13/install_stage13.py --device device --apply
python3 device/stage14/install_stage14.py --device device --apply
# 然后原 f2-luming-ci pre_build -> Stage10 materialize -> defconfig -> build/prelink
```

安装器必须在 Stage13 安装后运行，严格检查 3 个输入 SHA。保持原 materialize_installed_inputs：两个 provider 源文件会由现有流程复制入真实构建目录。runtime/ 是安装结果核对用，不是另一套覆盖入口。不要对已安装的 checkout 再运行安装器。

安装器把 `zzzzzzzzzzzzzzzzzzzzzz-cdx14-observation.patch` 追加到 device series，需保留在最后。原生成器仍产生一份 zzzzz-cdx-generated-aslr.patch；Stage14 的按名异常钩子进入该生成补丁，console/退出辅助函数由末尾补丁添加。不要再叠加另一份 dsh console 补丁；若需合并，先核对双方变化与唯一符号。

需要交回：kernel.macho、kernel SHA256、build-manifest.json、display build-report.json、stage14-install-report.json、最终 device series、生成 ASLR patch 和 Stage14 patch、完整 CI 日志及 CI URL。使用 qualify_stage14_kernel.py 检查真实定义与材料 SHA；Stage13 内核应被拒绝。完整内核编译是必要的下一步，本目录的接口夹具不能替代它。

## 真机对照（构建与产物审核后，由当前设备操作者执行）

保留 Stage13 root/auth/TC/seed、p26、CPU-present、refresh=1、`luming-display-ui-scale=2`，保留 `luming-display-console-handoff=1`。

| 组 | luming-display-vt-latch | luming-display-frame-probe | luming-display-snapshot | 用途 |
|---|---:|---:|---:|---|
| A | 1 | 1 | 1 | 拍 15 秒主动诊断 panic，确认帧与服务状态 |
| B | 0 | 1 | 1 | 仅关闭额外 latch，保留原 release，判断 latch 是否改变结果 |
| 正常观察 | 1 | 1 | 0 | 无主动 panic；保留注册表采样与原日志 |

三个新开关默认都是 0；用 A 时必须让用户知道它会主动 panic。镜像分别命名并记录 SHA；不要同时让两个会话操作手机。本包不含刷写脚本、不执行设备操作。

## 如何解读

- blank>0、f=0/sample=0：可能只处理了 blank swap，不能说桌面已经绘制。
- valid=1、mismatch=0、mutate=0：采样点源/目标一致，继续看多帧 sequence、retire、vsync；不等于完整桌面验收。
- mutate>0：源在复制期间变化，应先查 producer 同步，不能直接归罪 VT。
- 连续采样 between>0：存在中间写入；结合 own/enabled/disabled/blocked/drawn 与 B 组判断。
- own=1、enabled=0、drawn=0，图像仍卡住：不要继续只改 VT，转查帧内容、复制/retire 是否停住、服务退出原因与显示资源回退。
- watchdogd/liveactivitiesd 异常：用该组实际 ASLR/映像基址定位 c1，再修具体断言或依赖；目前没有根因修复的证据。

## 本地验证与边界

通过：实际生成器插桩幂等；Stage13 原异常取证仍在；相关后续设备补丁及 framebuffer 地址补丁可顺序应用；主机测试覆盖 padded stride、采样边界、源变化、目标不匹配、blank gap、采样次数上限、诊断开关/定时安排、console latch/panic 放行/串口语义、按名记录预算与摘要缓冲边界。C console/退出辅助函数与 C++ provider 接口夹具均以 arm64-apple-ios17.0 + mgeneral-regs-only 编译，无 FP/SIMD 指令。

尚未完成：完整 XNU/IOKit 编译、真实运行、VT 覆盖假设验证、daemon 根因修复、桌面验收及触控。上述测试不是面板时序或缓存属性验证。
