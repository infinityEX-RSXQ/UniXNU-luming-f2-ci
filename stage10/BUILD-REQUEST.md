# Stage10 显示源码构建请求（2026-11-01）

用户已明确选择“让 dsh 使用现有 CI 构建”。本包请求编译与交付产物；手机由 Codex 协调测试，本请求不包含刷机。

## 已定位的问题与本次实现

stage9已确认SpringBoard在FrontBoardServices的FBSDisplayMonitor初始化触发BRK，失败字符串为failed to find the main CADisplay。当前原版family没有Legacy provider。

本包增加原版21H461 IOMobileGraphicsFamily root，并接入从sheng裁剪的CPU Legacy/GOP后端，只绑定PE_current_console提供的真实framebuffer资源，去除SM8550/A740/HID/触摸/音频等板级外围。

已修复：两个计数器duplicate symbol；NativeLegacy和Probe编译重放污染原IOPlatformExpert编译记录；无定义的可选weak hooks。最小arm64/iOS17链接及编译输出隔离测试通过。原始358-slot ABI、0x18a0尺寸、slot354状态请求、surface/refresh/vsync字节守卫通过。本机只验证了portable C与小型Mach-O fixture，没有编译完整显示C++archive或内核，也没有真机服务发布证据。

## 使用现有stage9 CI配方

保留core 33da81310819b86d3ea62cb704f156c56407764a、XNU d8b80295118ef25ac3a784134bcf95cd8e88109f和原21H461 kernelcache SHA f18b4df865405f2a287b84977d7aca745e056d656d9fc9df1662970ce2969de7。不改变stage9短日志pre_build hook和其他archive/存储策略。

将本目录作为workflow工作目录下stage10/。在现有stage9 pre_build hook完成之后追加（不是替换原hook）：

```sh
python3 stage10/stage10-build/install_stage10_build.py --tree unixnu --device device --kernelcache "$UNIXNU_KERNELCACHE" --runtime-dir stage10/stage10-runtime --audit-dir stage10/stage10-audit --apply
(cd unixnu && ./unixnu defconfig "$DEFCONFIG" -D ../device)
```

随后沿用现有 `unixnu build kernel` 流程。installer固定仅增加IOMobileGraphicsFamily root、追加owned CPU archive配方、打开NATIVE_LEGACY_DISPLAY；MobileDisplay/Adreno保持n，实际archive由core原有force_load契约处理，不要再重复force_load。

完整细节见stage10-build/README.md。prepare_trimmed_builder.py只记录如何从已固定源码准备本包，CI直接使用已生成的build-luming-cpu-legacy-display.py，不需要运行prepare。

若精确ABI守卫、C++编译或链接失败，请保存首个完整诊断及对应build log；修正真实源码或输入，不删除守卫。原构建源可以复制到隔离目录，不覆盖dsh当前正在用的树。

## 交回这些产物

请把新的kernel.macho、build-manifest.json、native-legacy-display/build-report.json、生成的OriginalLegacyFramebufferABI.h、archive日志和CI run URL复制到 D:/civitoip20/lumingios-cdx/builds/stage10-legacy-ci-<runid>/。保存kernel SHA256和构建source commit。

已有display-prelink-20261101/kernel.macho（c8558617…）只有family，没有defined native_legacy_display_probe；已被qualifier正确拒绝，不能冒充本次完整修复。

## 构建后由Codex打包

Codex的sources/qualify_stage10_kernel.py要求新增bundle恰好只有IOMobileGraphicsFamily，保留stage9短日志和其他bundle，定义真实NativeLegacyDisplay vtable及early/late/allocate hooks。

只有通过后，sources/build_stage10_display.py才把新kernel装入已通过stage9的真实FAT，保留ADT的AAPL,phandle、认证blob、原两份TC、同一Data seed与control boot；原CI payload缺少这些修复，不能直接刷。

第一轮用stage10-runtime/args-registration.txt：保留文字console，先验收IOSurface及真实GOP provider、原start及用户客户端、CADisplay枚举是否越过旧BRK。它拒绝swap、不做CPU copy/retire，所以不是可用桌面或帧验收。PM0的用户态行为仍待真机验证。

第二轮才用args-cpu-present.txt启用PM、验证/传输/retire、CPU呈现和首个有效swap后的console handoff。两组不能混用；CPU单BGRA层不等于完整Metal/GPU合成。

当前没有“显示修复编译成功/屏幕可用”的声明。请先交回构建产物与日志。
