# DSH → Codex：Stage15 实现建议（提交者/分阶段/late-destination/vsync/平台服务）

日期：2026-11-02。基于 Stage14.1 真机结果（kernel `1bb6d602…`）与 `STAGE14P1-RESULT`。

## 0. 适用范围与不可改边界

- 原版 `IOMobileGraphicsFamily` / `IOMobileFramebufferUserClient` 是**预链接二进制**，不能直接给 `externalMethod` 加代码。
- 因此 Stage15 的提交者取证应做在**我们自己的 provider（NativeLegacyDisplay）**和**内核侧（XNU 源码补丁）**，不要假设能 patch 原版 user client 的 selector 分发。
- 不伪造 `IOWatchdog`/`AppleKeyStore` 成功，不跳过原版 BRK。

## 1. 提交者关联（provider 侧，最小可行）

### 1.1 client 创建时记录 task
在 `NativeLegacyDisplay::newUserClient(task_t owningTask, void *, UInt32 type, OSDictionary *, IOUserClient **handler)` 覆盖里：
- 调 `super::newUserClient(...)` 之前/之后，取 `proc_t p = (proc_t)get_bsdtask_info(owningTask)`，记录：
  - `pid`, `comm[16]`, `client` 指针, `type`, 时间戳（ms）
- 存入固定数组 `cdx15_clients[16]`，线性覆盖最旧。
- 只记录一次创建，不做 per-call printf。

### 1.2 swap 归属（尽力而为）
- 在 `validateSwap` / 提交入口，检查 `OriginalLegacySwapRequest` 中是否有 owner/client 字段（按 21H461 ABI 审计结果）；若有：
  - `client -> client table -> pid/comm`
- 若 request 没有 owner 信息：
  - 不猜、不读 current_proc；把提交者标为 `unknown`，只累计 `unknown_count`。
- 摘要输出：`CDX15 cli pid=<n> n=<n> name=<16>` 最多 4 行 + `CDX15 unk=<n>`。

## 2. 分阶段计数与时间戳（provider 侧）

短行格式（每行 ≤ 88 字符）：
```
CDX15 sub=<n> val=<n> q=<n> cp=<n> ret=<n> rej=<n>
CDX15 t0=<ms> t1=<ms> t2=<ms> t3=<ms> t4=<ms>
CDX15 vs=<n> last=<ms> sub=<n> arm=<0/1> late=<n>
```
- 阶段定义：submit（从 user client 进入 provider）→ validate → queue → copy → retire。
- `rej` 为 reject reason 位图或计数。
- 时间戳用 `mach_absolute_time`→ms，记录**首次和最后一次**各阶段；不要每帧 printf。
- 所有计数用 `volatile`，快照时读一次；跨线程一致性只作 best-effort，标注。

## 3. vsync 单独短行

- 在 provider 的 vsync 定时器回调里累计：发送次数、订阅者数、定时器状态（armed/idle/late）、最后发送时间。
- 不要和 copy/retire 混在一行；上次 `vsync` 被反光挡住，拆行更可靠。
- `sub` 用客户端订阅数（如果 ABI 能取到），取不到就输出 `sub=?`。

## 4. late-destination 采样（核心新增）

- 在 Stage14.1 已有的 `scanout_enter/leave` 框架里：
  1. `quiesce` 成功、console reclaim 之前
  2. 用**持有生命周期且已核验**的 GOP 映射（不是已释放的 IOSurface 源指针）再读取目标帧的 8×8 网格
  3. 与最后一次 copy 的 dst 采样比较
- 输出：
```
CDX15 late=<摘要hex> last=<摘要hex> eq=<0/1>
CDX15 latepx=<first8hex> lastpx=<first8hex>
```
- 这样能回答“最后一次 copy 之后 framebuffer 是否被改写”，而不是只看复制瞬间。

## 5. 平台服务取证（不做假成功）

### 5.1 IOWatchdog
- 内核/ provider 侧无法替代用户态 `IOServiceGetMatchingService`，但可在快照时枚举 IORegistry：
  - 查找 class 名包含 `Watchdog` 的节点（`IOService::getMatchingServices` 或遍历 `gIOServicePlane`）
  - 输出 `CDX15 wd node=<n> cls=<16>`（是否存在、类名）
- 若存在节点但 watchdogd 仍失败，说明匹配/权限/生命周期问题，不是“完全没有服务”。

### 5.2 AppleKeyStore / MobileKeyBag
- 同样枚举 `AppleKeyStore` 相关节点是否存在：`CDX15 aks node=<n> cls=<16>`
- 记录 `liveactivitiesd` 的 `MKBEventsRegister` 返回值（用户态不可直接取）；内核可记录其 exception 的 c1 已在 CDX14 摘要里。
- 不要用假服务或跳过 BRK。

## 6. 快照输出顺序（照片友好）

1. `CDX15 snapshot (intentional)`
2. `CDX15 sub/val/q/cp/ret/rej`
3. `CDX15 t0..t4`
4. `CDX15 vs ...`
5. `CDX15 cli ...`（最多 4 行）+ `unk`
6. `CDX15 late/last/eq` + `latepx/lastpx`
7. `CDX15 wd node/aks node`
8. 既有 CDX11/12/13 daemon 行保留

每行独立，不要依赖上一行换行；总长度控制在 panic reason 1024B 内（预计 < 700B）。

## 7. 验证与负向对照

- build-report 只允许 source/object/archive 变化；ABI/358/vtable/original_instructions 不变。
- qualifier 拒绝 Stage14.1 内核（缺 CDX15 符号）。
- 主机测试：padded stride、late 采样边界、client 表覆盖、vsync 计数不溢出。
- 真机 A 组：保持 Stage14.1 参数 + `luming-display-snapshot=1`，15 秒快照。
- 真机 B 组（可选）：`vt-latch=0` 复测，判断 latch 是否改变结果。

## 8. 已知风险

- client→swap 归属可能不可得：如 request 无 owner，只能报 unknown，不要伪造。
- late 采样必须用仍然有效的 GOP 映射；若映射已释放，跳过并输出 `late=skip`。
- 快照期间其他 CPU 可能仍写 FB；`eq` 只是采样时刻证据。
- 不要把 watchdogd/KeyStore 失败直接归因为“桌面不出的原因”，先拿 backboardd/SpringBoard 的等待/渲染证据。
