# Stage15：在已通过的 Stage14.1 上观察帧停在哪一步

本包响应 `stage15-analysis-20261102/DSH-STAGE15-IMPLEMENTATION-NOTES.md`。
这是诊断源码交付，尚未完整编译 XNU、尚未验证真机、没有操作设备。不要把它当作桌面/GPU/触控已修复。

## 构建基线与入口

沿用成功的 Stage14.1 CI **41363972872**，提交 **e65dff213b2f28d0cc92ca168dcd60b4f3e732ec**。
该次内核 SHA256：`1bb6d6022aa28ecbfe35fe052dc18549ba2b3cff042b22837beb3660653c469c`。
core 固定 `33da81310819b86d3ea62cb704f156c56407764a`；XNU 固定 `d8b80295118ef25ac3a784134bcf95cd8e88109f`。

把本目录放进现有 CI device/stage15，在原 Stage11→12→13→14→14p1 安装完成后、原 pre_build/materialize 之前执行：

```sh
python3 device/stage15/install_stage15.py --device device
python3 device/stage15/install_stage15.py --device device --apply > stage15-install-report.json
# 接原 pre_build / materialize / defconfig / build / prelink
```

安装器检查 Stage14.1 两份 provider 与 console patch 的原始 SHA，拒绝源漂移与重复安装；不改旧安装器。
新增 `zzzzzzzzzzzzzzzzzzzzzzzz-cdx15-observe.patch` 必须在 device series 最后，不能被生成 ASLR patch 的步骤移除。
generated ASLR 仍应是 `16541d2ae10b2c26fc9f5db477c577d5fd32591825b5db1230a407f73730e90b`。
`runtime/` 是安装后的核对副本，正常构建仍从原模板 materialize，不能只换 runtime 文件漏掉 core patch。

保留原版私有 ABI：358 virtual entries，original instance size 0x18a0，ABI header SHA
`8465dbcff188e88e66fdbe9a5e24b102c093b06d17f879f7a55fa3d1c58f8016`。
仍用经过原版 ABI 核对的五参数 newUserClient 方法（含 this）；不加六参数 overload，不改实例布局/vtable。

## 观察点与归属边界

- provider 的 newUserClient 记录 task 所属 pid/comm、type、结果、client registry ID、时间；固定 16 条，摘要最多 4 条。它是创建历史，不是实时连接清单；没有新增 clientClose hook。
- 原版 IOMobileFramebufferUserClient 预链接二进制不变。额外在**源码构建的 XNU** `IOUserClient::callExternalMethod` 外围加 begin/end 观察，保留原 ipcEnter/Exit、virtual dispatch、返回值。无需改变原 selector 分发。
- 只观察 client registry ID 在本 provider 表里的调用。验证恰好在同线程有效 IPC 上下文中发生时，才关联已记录 client owner。这个 owner 不是端口转交后的实际发送者；不是 current_proc 猜测。异步/缺失关联仍 unknown。
- `sub=?`：没有审计原 selector 的提交语义，不伪造提交次数。`ipc` 是进入该 XNU wrapper 且成功记录的调用数；早期 MIG 拒绝、其他 trap/override 路径可能不经过它。它不等于所有 swap。
- `val` 是 provider 验证次数；`q` 是已记录 request generation 第一次到达 eligible pending head 的次数，**不是原版私有 enqueue 次数**；`cp` 成功 CPU copy；`ret` completeCurrentSwap 返回；`rej` provider 拒绝。
- request 仅作为不解引用的身份键；完成期间地址复用会产生新 generation，旧退休事件不会抹掉新请求。重复观察不会重复统计 q。
- 所有计数/表通过独立短临界区 IOSimpleLock 保护；查询进程、注册表、采像素、生成文本、分配 OSData 均在该锁外。大快照状态放静态区，并以独立原子 guard 串行化，避免把事件环放到 kernel stack。

## 晚采样、vsync、服务

- 仅保留已经通过 phys/长度/stride/深度核验的 GOP IOMemoryMap 引用；本诊断引用故意保留至 reboot。初始化沿用单一 provider startHardware 顺序，映射若发生替换则标记 invalid 并跳过晚采样。
- 每次成功写像素（包括 blank fill）后，从有效 GOP 目标取 8×8 网格。这个最近目标样本独立于 Stage14 早期采样预算，不会拿第 8 帧冒充最后帧。
- 原 15 秒诊断先 quiesce/drain（最多约 1 秒），**然后取 late 样本，再 reclaim/清屏，最后 panic**。不读取已退休的源 IOSurface 指针。
- `late / last / eq` 比较最后拷贝时与晚采样时的 64 个目标像素；`latepx / lastpx / f` 是首像素及样本序号。`late=skip` 如实表示 quiet、目标样本或映射不可用。相等不证明整个帧、cache 一致性或面板扫描输出正确。
- `vs` 是 notifyVSync 调用观察数，`last` 为其最后 uptime 毫秒；`arm` 表示已请求下一次 timer；`late` 是超期观察数。subscriber 数始终 `sub=?`。这些不证明用户态收到 vsync/事件，也不直接给出线程等待栈。
- `wd` 对精确 IOServiceMatching("IOWatchdog")、`aks` 对 "AppleKeyStore"，输出找到的实际类名；`wdAlt` 独立查询 "AppleARMWatchdogTimer"。值 1=匹配服务存在，0=未匹配，-1=构造 matching 字典失败。未匹配不等于已证明所有 IORegistry 节点都不存在；只有 kext bundle 在 prelink 中也不等于服务已注册。
- 没有假 Watchdog/KeyStore、没有跳 BRK、没有放宽 AMFI 或修改 daemon 退出/corpse 策略。daemon 的退出和异常记录沿用 Stage14，只增加短摘要。

## 屏幕格式与判读

每个 Stage15 摘要行≤88字符，panic reason（含新标识）<700字节。字段过大时显示上限并设 clip=1；省略的 client 数见 omit，放不下的行见 drop，不应把省略当作零。完整计数/时间/client 表和最近 64 条事件，在快照时发布为 provider 的 OSData `CDX15TraceState`（按 TraceModel15.h 布局解释；不是持续更新）。

顺序：snapshot → quiet/gate → 计数 → F/L → vsync → client → unknown → late → 服务 → daemon → omit/drop/clip。
F/L 五阶段分别 submit/validate/head/copy/retire 的首末 uptime 毫秒；submit 显示 ?。0 可表示未观察到，不是耗时。可见上限 counts=65535、time=999999ms；完整数仍在 OSData，32位累计饱和会标 clip。
gate 位：1=CPU copy enabled，2=transfer busy，4=logical PM，8=boot mapping，16=primary，32=pending，64=validated。它是最近一次 kick 的观察，不是同步读取的全局状态。

保留 Stage14.1 的 cpu-present、p26、refresh、ui-scale、console-handoff、vt-latch、frame-probe=1、snapshot=1 参数。trace 在 frame-probe 或 snapshot 开启时默认开启；可显式 `luming-display-trace=1`。`luming-display-trace=0` 关闭新观察。snapshot 仍开启时，会按原诊断时序主动停机，不能用来测试长时间运行。

预期标识：`CDX15 snapshot (intentional) r=1`。先拍完整摘要，不以是否还停在苹果 logo 作为唯一判据。

1. 若 val/q/cp/ret 都少且相等：说明 provider 已观察到的帧完成了；还不能断言 SB/BB 在等 GPU，应继续抓用户态等待/渲染证据。
2. 若 val 多而 q 少：结合 gate、rej 和时间检查 pending/validation/PM；若 q 多而 cp 少或 ret 少，则跟进 CPU copy/完成路径。
3. 若 quiet=1 且 late != last：确有采样点在最后写入后变化；仍需识别写入者。相等则只排除这些采样点的变化。
4. 若 wd=0 / aks=0，结合真实失败调用再做平台服务修复；不要把它们直接当作桌面不出的原因。
5. SpringBoard/backboardd 无退出记录只表示观察器没记到退出，不等于线程健康。当前包没有伪造“等待 GPU”的结论。

watchdogd 早前 PC 是 `0x10000ab0c`，不能与 liveactivitiesd 的 `0x1c18f64f8` 混写。先保留真实 daemon 证据，不做二进制跳过断言。

## 交回产物、核验与验证范围

交回 kernel.macho、SHA256、CI URL/完整日志、build-report.json、build-manifest.json、stage15-install-report.json、最终 device series、生成 ASLR patch、新 core patch。build report 应包含两个 materialized source SHA、ABI、原 kernelcache、object/archive SHA。沿用现有 CI 编译后核验：

```sh
python3 device/stage15/qualify_stage15_kernel.py --kernel kernel.macho --sha256 ACTUAL_SHA --build-report build-report.json --output stage15-kernel-check.json
```

核验器检查真实 defined symbol（含 core/IPC hooks）、IOUserClient wrapper 对 begin/end 的实际 BL 调用、源码 SHA、原依赖 bundle、358项 ABI 和原 kernelcache。只有定义却未接入调用的内核不能通过。若链接器生成 branch veneer，先交回反汇编核对，不能为通过检查而跳过它。
旧 Stage14.1 必须被拒绝。脚本默认 baseline 是现有 D: 项目路径；若在 CI 执行，应显式给 --baseline。qualification_base.py 是随包携带、未改动的 Stage10 依赖核验器。

本地已通过：固定基线安装器 dry-run/防重装；相关 device/core patch 顺序应用；ASLR生成结果不变；model/adapter 功能测试（含完成时地址复用、异步 unknown、晚采样检测目标变化、行/缓冲区边界、锁外 API）；真实 IOUserClient wrapper 的8种锁/分发组合；arm64 iOS17 GPR-only 接口夹具编译。
接口夹具不是完整 XNU/IOKit 编译；完整 CI、链接、机上日志均待 dsh 执行。若 CI 需要新增编译修正，交回 diff 后同步 hash/核验器，不能静默绕过 pin。

显示稳定后再推进触控；本包不改触控、分区或其他硬件配置。
