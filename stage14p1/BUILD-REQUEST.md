# 给 dsh：Stage14.1 恢复诊断画面

## 当前事实和诊断遗漏

用户反馈 Stage14 测试后只有略花的苹果标志，对是否曾出现 `CDX14 diagnostic snapshot` 文字不确定。**目前不能确认主动 panic 已执行，更不能把静止 logo 认定为桌面已运行。**

已独立核验返回内核：run 41359974470，commit `d47f17cf5e640fce1c382bc4a840c641f407a715`，kernel SHA256 `561aff1aad00c5b0679ed99879e16f89554c744609ad06875aaac2ca9460e377`。本地 snapshotA 镜像确有 vt-latch=1/frame-probe=1/snapshot=1/console-handoff=1/ui-scale=2；没有设备镜像读回证据。

Stage14 的 `panic_active()` 放行仅能阻止 latch 拦截新的开启调用，不能主动开启已经由 release 关闭的 console。printf 下层仍检查 disableConsoleOutput，vcputc 仍要求 gc_enabled，当前诊断回调直接 panic 未重新 acquire。因此遗漏足以解释“发生 panic 却没有文字”的可能性；尚未取得本轮实际计数证明。

## 最小修正

- 每次 backend kickOnce 在栈上持有一个无 ABI 布局变化的 RAII 写入 lease；所有返回路径归还，包含 blank fill、普通 CPU copy 和退休路径。正常未触发诊断时不冻结。
- 15 秒诊断回调先置 frozen，拒绝新写屏进入，最多等待现存 lease 退出约 1 秒（100×IOSleep(10)）。竞态通过顺序一致原子操作和进入后的复查处理。
- quiet=1 后才调用 console 核心辅助函数：VCPUTC 锁内清除 Stage14 latch，然后在正常 thread-call 上下文依次 release/text/acquire；此时允许常规 console 分配与锁操作。它发生在 panic() 前，不在已停 CPU 的 panic 路径中分配。
- 保留恢复前 VT 状态，再输出新标识 `CDX14.1 diagnostic snapshot (intentional)` 和 `quiet/active/reclaim/before`，其余 Stage14 帧/服务诊断保留。若 quiet=0，不强行重新获取正在被写入的 framebuffer。
- 没有 handoff 的对照组现在也可在首次 prepare_scanout 后安排同一个 15 秒诊断，以免 handoff=0 时旧计时器根本不启动。
- 保留 dsh 已修的 FrameSamples14.h 头文件 guard 和 eq 的 unsigned 格式修正。没有改面板 stride/cache、FBS 校验、root/auth/TC、daemon 退出策略或 corpse 上限。

该修正只解决可观测性。没有诊断数据之前，花纹仍可能涉及真实帧内容、扫描输出、同步或其他写入者，不能在本轮认定具体根因。

## 构建入口

沿用成功的 Stage14 CI 配方和该提交里的 Stage14 安装器（包含 dsh 的实际编译修正）。本目录放到 device/stage14p1；在原 Stage11→12→13→14 安装后，再执行：

```
python3 device/stage14p1/install_stage14p1.py --device device --apply
# 然后原 pre_build / materialize / defconfig / build / prelink
```

安装器检查成功 Stage14 的两个 provider 源文件 SHA 和原 CDX14 patch SHA；不接受早先未修编译错误的旧包输入。追加的 `zzzzzzzzzzzzzzzzzzzzzzz-cdx14p1-console-reclaim.patch` 保留在原 Stage14 patch 之后。runtime/ 只用于核对安装结果。

交回 kernel.macho、SHA、display build-report.json、build manifest、stage14p1-install-report.json、最终 device series 和两份 console patch、CI URL/日志。用 qualify_stage14p1_kernel.py 检查真实定义与实际源码 SHA。原 Stage14 内核必须被拒绝，不能只核对日志字符串。

## 建议测试

先保留原 snapshotA 的全部参数，只替换核验后的新内核。这是诊断版，预期约首次 handoff 15 秒后加最多约 1 秒 drain 等待，主动触发一次 panic。

应拍到：

```
CDX14.1 diagnostic snapshot (intentional)
quiet=1 active=0 reclaim=1 before=1/0/1
```

before 是恢复前 owned/enabled/disabled；恢复后的 VT 一般为 own=0/enabled=1/disabled=0。**这个恢复后的状态不表示停绘失败，是诊断主动恢复文字输出。** 随后拍完整的 f/sampled/blank、src/dst、mismatch/mutate/between、copy/retire/vsync 和服务异常记录。

若仍只有 logo，第二组仅改 `luming-display-console-handoff=0`、`luming-display-vt-latch=0`，frame-probe/snapshot 仍为 1。14.1 的计时器在此组也会安排。它是日志对照，console 日志会污染目标帧，不能用 between 非零单独证明外部覆盖。

quiet=0/active>0 表示在途写入未排空；不能把此时的无文字当作 reclaim 已成功。没有新标识时，也不能确认回调确实运行。不要重复同一镜像把 logo 当成新证据。

## 验证范围

通过：Stage14 console patch 和物理 framebuffer 地址 patch 后可继续应用本 patch；安装器 dry-run、源 SHA、防重复应用；恢复前后调用顺序检查；实际原子 quiesce 的在途退出、冻结拒绝、RAII 返回及超时测试；C reclaim 与更新后的真实 provider helper/callback 部分以 arm64-apple-ios17.0、mgeneral-regs-only 编译通过。

尚未完成完整 XNU/IOKit 编译与真机验证。没有执行任何设备命令。关闭 snapshot 开关时，该版本不会为诊断冻结或重取 console。触控继续排在显示稳定之后。
