# 给 dsh：Stage13 UI 缩放发布候选

## 本轮纠正

用户提供的 Stage12 原照片 `2765ce04e450a6376ceb22255c5dd4c9.jpg` 实际为：

```
CDX12 mode got=1 err=0 busy=0
CDX12 w=1236 h=2750 pref=0 rot=0
CDX12 scaleBits=0 rateBits=404e000000000000
CDX12 gamut=1 hdr=0 pub=1 prop=1
```

`404e000000000000` 是 double 60.0。不要继续采用此前转述的 `4000000000000`，也不需要再次改 getRefreshAttributes。supportedFrameInfo 是可选 trace keys 接口，不是 mode 列表。

FBS 原版 PC `19f3d0744` 不变。其 `x24` 是整数 preferredScale；`d9` 是 double scaleOverride，`d8` 是 double refreshRate。在 pref==0 分支，`19f3d0608` 调到 `18f6e545c`，实际检测 `abs(scaleOverride)<2^-52`，返回 true 后 `19f3d061c` 失败。因此照片的 pref=0 + override=0 确实足以触发此断言。pref=0 本身不总是非法，不能只根据 `b.mi` 判断。

## 最小源码候选

- 在已验证 GOP 映射回调中、显示服务向用户态发布前，以 `luming-display-ui-scale=2` 显式设置 `/chosen` 的 4 字节 OSData `display-scale=2` 和 `display-rotation=0`。
- 原版 21H461 MobileGestalt `1a0215740..5758` 确认读取 `IODeviceTree:/chosen` 的 display-scale，`1a020fc98..fcb0` 确认按长度 4 的 CFData 读取原生 uint32。sheng 的 LegacyDisplayProbe 也采用这个属性契约。此为 UI 点到像素的政策，不是物理 DPI、GPU 能力或面板时序。
- 本候选仅允许实际 1236x2750 scanout，2 倍对应 618x1375 points；未启用开关时保持 control。缺失或零 scale 可设置，既有相同值保持，其他正值/未知类型/非零 rotation 会拒绝。双属性发布失败会回滚本次写入，记录 rc。
- 这条属性最终是否传到当前失败对象仍须真机验证。它是有原版消费者和参考实现支持的候选，不宣称已经证明修好 CADisplayMode 的所有来源。
- 替换最终 CDX12 长摘要为 CDX13 短行，保留原对象字段读取和异常策略。原 fatal 条件下额外保存 x28 的 validityCheck；只读，不改 FBS 指令/参数/校验返回。
- NativeLegacyDisplay.cpp、getRefreshAttributes、supportedFrameInfo、vtable 358 entries、0x18a0 ABI、CPU swap/copy、已有 root/auth/TC/seed 都不变。

## CI 接入顺序

沿用成功的 Stage12 CI `41309364157` 对应源码、pins 和现有构建流程。此包是 **增量源码安装器**，包内 runtime/ 用来核对结果，不能再整份覆盖运行一次 Stage11/12 安装。

```
python3 device/stage11/install_stage11.py --device device --apply
python3 device/stage12/install_stage12.py --device device --apply
python3 device/stage13/install_stage13.py --device device --apply
# 然后原 f2-luming-ci.sh pre_build -> stage10 installer -> defconfig -> build/prelink
```

stage13 目录必须进入 device checkout。安装器只接受 Stage12 安装后的 LF SHA；第二次运行会拒绝重复应用。沿用原 materialize_installed_inputs，不直接编辑 out/tree；不添加重复 archive。

交回 kernel.macho、build-manifest.json、display build-report.json、stage13-install-report.json、生成的 aslr patch、CI URL 与首处编译错误（若有）。存入 `D:/civitoip20/lumingios-cdx/builds/stage13-ui-scale-<runid>/`。

用 qualify_stage13_kernel.py 核验新定义符号、实际编译来源 SHA、原 bundle 集及 ABI。原 Stage12 内核应被拒绝。

## 真机候选（完成构建与产物审核后）

同一 Stage12 p26 + cpu-present + refresh=1 配置，**只新增 `luming-display-ui-scale=2`**。保留现有 control boot、ADT/root auth/TC/seed。不要加旧 sheng 的其他板级开关。此包不执行刷机。

预期先看到 `CDX13 ui=2 read=2 rc=0 writes=...`，表示属性发布回读成功，不等于 FBS 接受。若仍相同 PC，最终短行会给 got/err、pref、sb/rb、vcGot/vc、issues、gamut/HDR/rotation 和 ui 回读。

`issues=4` 表示捕获的 pref 和 override 同时接近零；got=0 时 issues=ffffffff，禁止解读占位字段。issues 只覆盖可观察标量条件，不覆盖类身份。若旧 PC 消失，应继续检查 SpringBoard 存活与真实 validate/copy/retire 计数及屏幕帧。

若 read=2 但 pref/override 仍双零，下一轮应追 FBS 使用的具体 immutable/XPC mode 与缩放服务缓存；不应再次盲改刷新率或跳过断言。

## 已完成验证范围

主机测试：零值修复、相同值幂等、冲突/类型拒绝、缺失 chosen、第二次写失败回滚（含恢复原零值）、分配失败、尺寸/开关、实际照片字段检查、copyin 错误、PID/锁忙、输出边界。

真实生成器：Stage11 -> Stage12 -> Stage13 -> 原 source patch，应用/再次插桩幂等检查，移除插桩后原策略一致；7 个后续设备补丁仍可应用。

ARM64 iOS17：接口夹具以 mgeneral-regs-only 编译通过；这不是完整 IOKit/XNU 编译。完整内核与真机结果尚待 dsh CI/测试。
