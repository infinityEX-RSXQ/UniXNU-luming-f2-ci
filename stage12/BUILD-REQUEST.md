# 给 dsh：Stage12 模式参数取证 + 60Hz 属性发布候选

Stage11 照片已精确确认 `match=1 busy=0 n=1 drop=0`、`first/last c1=19f3d0744`、`st=10 fail=0 reg=1 cl=4 rc=0 val=0 cp=0 ret=0 vs=0`。不要继续按 19f3d37xx、12328/12e24 或 st=0 分支分析。

实际故障是 FBSDisplayMode 的 `_initWithWidth:height:preferredScale:scaleOverride:refreshRate:gamut:hdr:rotation:virtual:validityCheck:`，IMP 19f3d0500，PC+244，FBS image offset f744。失败文本 `FBSDisplayMode cannot be configured as requested : %@`，原方法表、CFString、BRK 均已核验。

Stage12 在不跳过断言/校验的前提下实现两项独立变更：

1. 在该精确原 PC 捕获对象的实际模式字段，追加 CDX12 原始整数/浮点位模式到已有 panic 摘要。只读当前 SpringBoard 地址空间的 64 字节；使用原 XNU copyin，失败打印 err，不直接解引用用户地址。copyin 可能经过 VM fault 处理，本实现不宣称其执行时间有硬实时界限。
2. 为当前 60Hz 软件调度设置补齐原版 IOMFBDisplayRefresh 的显式发布；默认关闭，只在 `luming-display-refresh-publish=1` 且 sheng-vsync=60 时开启。原大于 60 的行为保留。**这仍是待测候选，不能宣称它必然解决 FBS 模式断言**：原 CADisplayMode 的 refreshRate 是由 packed mode 解码，尚未证明等同该属性。

## 接入

从成功的 stage11 分支 commit `8f795c7df15b19397cc717b923d2cf4b83a853e2` 干净隔离 checkout 开始。保留 core/XNU/kernelcache/Stage10 builder 和 stage11 的所有成功适配，不新开 framework/GPU 路线。

把包解为 device/stage12/，在 workflow 中：

```sh
# 原 Stage11 安装步骤（仍保留）
python3 device/stage11/install_stage11.py --device device --apply
# 新增，紧跟其后，必须在 pre_build 和 stage10 runtime installer 之前
python3 device/stage12/install_stage12.py --device device --apply
# 后面保持原顺序：f2-luming-ci.sh pre_build -> install_stage10_build.py
# -> defconfig -> build/prelink。
```

确保 stage12 目录实际进入 device checkout；Stage11 首轮曾因目录未入 checkout 而失败。installer 校验的是 Stage11 installer **执行后的**三个 source LF SHA，不要在原始 checkout 提前运行，也不要放宽 hash guard。源改动最终必须由原 materialize_installed_inputs 复制到实际 build tree；不直接改 out/tree，不额外打一个重复定义 archive。

生成器仍使用单一 zzzzz-cdx-generated-aslr.patch；只添加精确 mode capture 与摘要，不改例外返回、签名、ASLR、panic 选择、sync/coredump 行为。摘要缓冲区由 640 改为 1024 字节。驱动 vtable、实例布局和原字节 guard 保持。

## 参数与测试分支

构建阶段不刷机，先交回产物审核。通过后建议：

- A：原 Stage11 CPU-present/p26 参数，新增开关缺省或 =0。只增加模式实参取证；用于确认非法字段。
- B：同一内核、同一参数，仅增加 `luming-display-refresh-publish=1`。开启 60Hz 属性发布候选，观察旧 PC 是否消失，以及 CDX12 refresh property 日志。若需要节省一轮，可以先 B；若无效，模式字段应直接指出下一项。

不要把 boot arg 填进未审核的 CI payload，不重刷 userdata。候选 super 保留受检 ADT/auth blob/TC/seed/control boot；诊断与属性开关都通过源编译引入，不改 Mach-O 指令。

CDX12 的 `got=1 err=0` 才可解释 w/h/pref/rot/gamut/hdr。scaleBits 与 rateBits 是 IEEE754 double 的原始位模式，内核不做浮点运算。例：`404e000000000000` = 60.0，`0` = 0.0。scaleOverride=0 不一定非法，需结合 preferredScale 分支；不能仅见零就盲改。`got=0` 时字段为占位零，绝不可作为原模式的测量值。

## 验证与交回

本地已执行主机 copyin 夹具（成功/失败/PID/锁忙/输出边界）、ARM64 C/C++ 接口编译链接、实际源补丁生成与后续设备补丁应用检查。完整 Probe/XNU 尚未编译、未真机测试。

交回 kernel.macho、build-manifest.json、display build-report.json、生成的 aslr patch、install_stage12 的 JSON、首处编译错误（若有）与 CI URL，存入：

`D:/civitoip20/lumingios-cdx/builds/stage12-mode-ci-<runid>/`

用包内 qualify_stage12_kernel.py 校验 source hash、CDX11/12 定义符号、原 bundle 集和格式；kernel.macho 不能复用 Stage11 旧产物。构建成功与真正出帧分开报告。
