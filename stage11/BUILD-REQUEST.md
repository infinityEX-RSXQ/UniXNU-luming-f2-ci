# 给 dsh：Stage11 紧凑崩溃摘要

目标是可靠取得 SpringBoard 的原始异常地址和显示路径计数，不是宣称已经修复主显示枚举。保留当前 CPU Legacy/GOP、存储、签名、ASLR 与退出策略。此包尚未完整编译内核或真机验证。

请从成功的 stage10 Legacy CI 41274600288 / commit `6ba406461065345e8cac15a25e70facaa0af68c4` 的干净隔离 checkout 接入；沿用 core `33da81310819b86d3ea62cb704f156c56407764a`、XNU `d8b80295118ef25ac3a784134bcf95cd8e88109f` 和原版 kernelcache SHA `f18b4df865405f2a287b84977d7aca745e056d656d9fc9df1662970ce2969de7`。不要改用 NativeMobileDisplay 分支。

## 接入位置

把包内文件存为 `device/stage11/`。在原 workflow 的 pre_build 步骤中，**在运行 `bash device/scripts/ci/f2-luming-ci.sh pre_build` 之前**增加：

```sh
python3 device/stage11/install_stage11.py --device device --apply
```

然后按原顺序运行：

1. 原 stage9 pre_build：其生成器现在同时生成 kern_exit.c 的摘要钩子，仍只生成原来的一个 `zzzzz-cdx-generated-aslr.patch`。
2. 原 stage10 `install_stage10_build.py`：复制扩展后的 Probe 到 core；保持现有 builder 的 materialize_installed_inputs 修复。
3. 原 defconfig 及 kernel 编译/prelink。不添加 archive、framework root 或 GPU 驱动。

必须在**安装 stage10 runtime 之前**修改 device 的 Probe 源码。不要只改 CI 的临时 out/tree，否则 materialize 会用已安装的原件覆盖。不要把该 helper 再复制成独立 archive 对象，否则会重复定义。installer 默认只演示计划，`--apply` 才写入；对源内容按 LF SHA 校验，遇到差异停下交回信息，不放宽 guard。

## 行为

- 在 exception_triage 的既有 DEVELOPMENT/MACH_BSD 范围，按进程名捕获 SpringBoard 的 EXC_BREAKPOINT/EXC_BAD_ACCESS；不受 pid<=26 限制。
- 保存同一 PID 的首次与最近一次异常、slide、disable_aslr 标志与计数，忽略二次 EXC_CRASH/EXC_CORPSE_NOTIFY。它是观察记录，不等于完整故障线程回溯。
- 仅在**原有 proc_handle_critical_exit 已决定 panic、原有 coredump/sync 完成后**，给 SpringBoard 原 panic 前缀追加 6 行摘要。不新增 panic，也不改变异常返回或进程退出条件。
- try-lock 不等待；冲突时明确 `match=0 busy=1`，不伪造有效 PC。匹配不到 PID 则 `match=0`；只有 match=1 才解释 first/last。显示计数是近似观测，不是原子事务。

示例仅为主机夹具输出，不是真机结果：

```text
SpringBoard[812] exited
CDX11 pid=812 match=1 busy=0 n=1 drop=0
CDX11 first e=6 c0=1 c1=19f3df2ec
CDX11 last e=6 off=1 sl=0 c0=1 c1=19f3df2ec
CDX11 st=10 fail=0 reg=1 cl=1 rc=0
CDX11 val=0 ok=0 why=0 cp=0 rc=ffffffff
CDX11 ret=0 vs=0
```

val=0 是“没有观察到 validator 调用”，不严格证明用户态没有请求；reg/cl 成功不是 CADisplay 枚举证明。cp 的 rc=ffffffff 在 cp=0 时是初始值，不是一次真实复制失败。ret/vs 为累计次数，软件 vsync 不是硬件 vblank。

## 已有验证

- 真正执行了主机 C++ 编译与断言测试：进程名隔离、超过 PID 阈值、原始异常不被二次通知覆盖、first/last、PID 变化、锁冲突、输出边界。
- ARM64 iOS17 Mach-O 的 C 调用者与 C++ helper 完成编译和链接，两个 C ABI 符号正确；未引入 libatomic 依赖。夹具的动态未定义符号允许项不代表完整内核链接通过。
- 在固定 XNU 原始源码执行修改后的实际生成器，补丁可应用；与后续 7 个影响目标文件的设备补丁顺序兼容。删除两段新增源代码后与旧源文本逐字一致；重复插入幂等、锚点漂移拒绝。
- 尚未用 macOS XNU SDK 编译完整 Probe/XNU；尚无新内核、新 super 或真机结果。

## 交回与验收

先只构建，暂不刷机。交回 `kernel.macho`、build-manifest.json、display build-report.json、生成的 `zzzzz-cdx-generated-aslr.patch`、CI 日志及链接，放入：

`D:/civitoip20/lumingios-cdx/builds/stage11-crash-summary-ci-<runid>/`

预期 Probe LF SHA：`5c1ff177f2ddd833bf2df385d35700a19bd2a92faf987dfbdb7e89acd4f38d04`；NativeLegacyDisplay.cpp 必须仍为 `0ab790c93a086aad4639529126ec65b7228a7bb2fb4b921ebf4b9e590fe990a1`。完整编译如果报错，保留第一处错误及命令，不关闭诊断或 ABI guard。

Codex 侧用 `qualify_stage11_kernel.py` 验证原 bundle 集、两个真实定义的 C 符号、格式字符串及源文件 hash，避免拿 stage10 内核冒充 stage11。通过后再用既有受检 packer 以 stage9 为存储/ADT/TC 基线制作新候选；参数与 CPU-present 相同。p26 版仍可先测试，它与本源码补丁独立，不能称其已经包含 CDX11。

只要下一轮 `match=1` 且 slide/off 有效，即可判断原 `0x19f3df2ec` 是否仍发生。地址改变必须重新符号化；没有新 PC 前不盲目修改显示枚举和像素格式检查。
