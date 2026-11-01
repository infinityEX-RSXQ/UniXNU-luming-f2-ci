# Codex 显示方案：18:20 照片定位

本组是用户明确标注的 Codex 显示方案测试，与前一组 dsh 诊断分开记录。两张原图仅为分析旋转/裁取阅读，没有改写文字或覆盖原图。照片本身不能证明 kernel 的 SHA；dsh 的 18:17:36 刷机记录指向 p26 候选，作为时间关联记录。

## 已读清并独立核验

```text
CDX_ASLR p=26 n=SpringBoard off=1 slide=0
CDX_EXC  p=26 e=6 c0=1 c1=19f3d0744
```

**正确地址是 `0x19f3d0744`，不是 `0x19f3d3744`，也不是旧的 `0x19f3df2ec`。** 前者的原版指令恰为 `00 00 20 d4`（BRK #0）；已用原始缓存 SHA、类元数据、方法表与失败字符串交叉验证，不是按最近符号猜测。

- 映像：FrontBoardServices，基址 `0x19f3c1000`；新 PC 在映像内偏移 `0xf744`，不是 `0x12744`。
- 类：`FBSDisplayMode`，class_ro `0x1e7a9d8d8`，其方法表为 `0x19f449be0`。
- 方法：`_initWithWidth:height:preferredScale:scaleOverride:refreshRate:gamut:hdr:rotation:virtual:validityCheck:`，IMP `0x19f3d0500`，PC 位于方法内 `+0x244`。
- 失败文本：`FBSDisplayMode cannot be configured as requested : %@`；CFString `0x1e7a9b008`，原字符串 `0x19f4522d4`。
- 源文件文本：`FBSDisplayMode.m`；原指令在默认诊断分支使用源行号 0x70（112）。

这证明**当前可见致命点已变为显示模式校验失败**。不能再按“找不到主 CADisplay”这个旧 PC 修；也不能仅凭新 PC 或 user-client 成功，就声称整个主屏流程和桌面呈现已经通过。

照片中能见到多个 `CDX_DISP client ... status=0`，以及原版 map_display_type / request_power_change 路径，说明客户端确实访问了显示服务。未捕获调用栈或模式的实参，不能确定具体哪个字段不合法；core dump 的 errno2 是退出后的输出失败，仍不是最初故障。

## 校验范围已缩小

原方法先保存模式字段，再检查以下约束；任意一个失败都会汇合到该 fatal 路径：

- width、height 不允许 0 或全 1 的哨兵值。
- preferredScale 不允许全 1 的哨兵值；preferredScale 为 0 时还会走额外的 scaleOverride 检查，不能把“0”一概认定为根因。
- scaleOverride 与 refreshRate 有浮点条件分支；在有限数值范围内，refreshRate 必须大于 0。NaN/Inf 的全部分支语义未在本轮审计中完整归纳。
- gamut、HDR、rotation 分别有范围检查（原码 unsigned 比较，gamut <2、HDR <3、rotation <4）。
- 还存在实际类一致性检查。

另已核对 `_initWithCADisplayMode:scale:rotation:`：它从 CADisplayMode 调用 width / height / preferredScale / refreshRate / colorGamut / hdrMode，并把这些返回值送进上述严格校验。这建立了下一步应追查的模式属性来源，但尚无本机实参证明是哪一项。

## 下一步修复优先级

1. 先核对实际 GOP 尺寸与 CADisplayMode 所读模式信息是否一致，尤其 preferredScale、refreshRate。应取得真实返回值或原版完整失败描述，再改生产这些值的接口。
2. **已发现可疑的源码条件，但还不是确认根因**：NativeLegacyDisplay::registerService 只在 `sheng-vsync > 60` 时调用原版 `setDisplayRefreshProperties`；当前参数是 60，所以这一显式发布分支不执行。源码原注释说 family 本身不负责该属性发布。需要继续核对 CADisplayMode 的 refreshRate 是否因此为 0；不能把软件 vsync=60 当成已经成功发布模式刷新率。
3. 若证实刷新率为 0，应优先对显式 60Hz 配置发布原版 slot301 给出的 1/60s 模式属性，保留真实 GOP 尺寸及所有范围检查。当前未改动、未编译或验证这一候选。
4. 如果是 preferredScale/其他模式字段，则沿原 user-client/模式查询返回路径修复。不要填假物理 DPI、改 FBS 的 fatal 分支或无条件放行校验。
5. Stage11 仍有助于保留异常与显示计数，但它不打印 FBSDisplayMode 的实参，不能指望只靠 Stage11 就判定上述哪个字段错误。当前照片已有足够证据开始追模式属性，不必等待它再次确认同一个 PC。

## 构建协调

已从 dsh 会话确认 Stage11 已交给现有 CI。首个 run 41297695512 在调用 installer 前因 `device/stage11/install_stage11.py` 未进入 checkout 而失败，尚不是 C++ 编译错误；本机已出现新的 run 41297967470 状态记录。避免同时修改 dsh 正在处理的 checkout；本次仅保存独立分析，没有触发 CI 或操作设备。

机器证据：`crash-symbolication/display-mode-20261101-1820.json`。

反汇编：`crash-symbolication/fbs-display-mode-init.asm`、`crash-symbolication/fbs-display-mode-from-ca.asm`。
