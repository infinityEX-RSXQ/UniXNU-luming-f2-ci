# 给 dsh：Stage16 vsync 分支诊断与相对时间修正

先看 `evidence/STAGE15-RESULT-20261102-0943.md`。Stage15图中3次成功的validate/head/copy/retire都关联backboardd client，late==last；vs=0但没有初始化/订阅分支证据。尚未定位到唯一修复点，不能宣布必须上GPU或强制vsync。

本包是小范围诊断增量，尚未完整编译或真机验证。以成功 Stage15 run **41372922740** / commit **ec66ac81fa5896213cb5da02168acd6649e47cc3** 为基线。
安装顺序：原11→12→13→14→14p1→15之后、pre_build/materialize之前，追加：

```sh
python3 device/stage16/install_stage16.py --device device --apply > stage16-install-report.json
```

安装器固定成功Stage15的两份provider SHA和Stage15 core patch SHA；不改core patch/series、原私有ABI、定时器策略、注册策略、格式/拷贝/认证/GPU/daemon策略。仍沿用358项原ABI。`runtime/`为结果核对副本。

**实际代码增量：**

- 原有 startVsync 每条返回路径记录真实分支；成功只在原addEventSource已成功、原timer字段赋值后记录。
- 原有 armVsync 仅在原本需要检查订阅的位置调用一次既有vsyncWanted()，记录检查得到的布尔结果；没有新增私有对象读取，不计造subscriber数量，不绕过无订阅条件。
- 所有诊断状态沿用Stage15独立spin lock；查IOKit/设置timer都在锁外。未添加vtable方法或实例字段。
- 时间改为mapping核验后trace启用时的相对毫秒，解决照片F/L全999999的截断。新增age是trace相对时间，不是完整开机耗时。尚未发生的事件仍显示0。
- 摘要增加一条 `vst= sa= ar= aa= sf= af= hz=`；仍≤88字符/行且panic reason<700B，必要时减少client摘要行，omit/drop如实报。
- `CDX16VsyncState`保留本轮pacing原始状态；旧`CDX15TraceState`、late和daemon观察保留。

## 字段解释

vst为最近startVsync分支：0=未观察到，1=hz为0，2=hz>240，3=非primary，4=无bootMapping，5=已有timer，6=无work loop，7=timer分配失败，8=addEventSource失败，9=创建完成。sa为start尝试次数。

ar为最近armVsync分支：0=未观察到，1=无timer，2=已armed，3=订阅检查为空，4=请求下一次timer唤醒。aa为arm尝试次数。ar是最近调用结果，不是全部历史；实际通知仍看原vs/last/arm行。

sf/af是对应start/arm观察的标志位，十六进制：1=timer对象存在、2=primary、4=bootMapping、8=start中getWorkLoop成功、16=订阅非空、32=本次确实读取过订阅状态。没有32时，不能用16为0推断无订阅。sf成功时记录新timer存在；af来自该次arm的原有检查。

hz是最近pacing观察的频率；start失败前后arm可能更新它，结合vst/sf解读。vs=0、arm=0单独不能区分原因。

保持Stage15测试参数，`sheng-vsync=60`在本地super中已核对存在；不需要改super内容或platform服务来迎合日志。预期约handoff15秒主动触发 `CDX16 snapshot (intentional)`。这仍是短时诊断，不是正常长期运行镜像。

## CI与回传

沿用既有Stage15成功配方。旧的Stage15/14/14p1 panic标记检查需按stage16_installed选择CDX16新标识；这类变化只调整诊断标记组合，不删除源码/ABI/对象/链接核验。提供实际workflow diff。
原Stage15核验器会因新标识与source SHA变化拒绝本版，这是预期；改用本包qualify_stage16_kernel.py，默认baseline现有D:路径，CI可显式给--baseline。

```sh
python3 device/stage16/qualify_stage16_kernel.py --kernel kernel.macho --sha256 ACTUAL_SHA --build-report build-report.json --output stage16-kernel-check.json
```

交回kernel/SHA、build-report/manifest、stage16-install-report、CI日志/URL、实际workflow diff。只在完整构建与资格核验通过后按既有参数打super测试。
本地通过了固定输入/防重装、原Stage15 model/adapter回归、相对时间、start9类结果与arm各分支测试、订阅只读一次、ARM64 GPR-only接口夹具编译。接口夹具不等于完整XNU/IOKit构建；未操作设备。

若vst=9且ar=3，不强迫发送给不存在的订阅者，应继续检查client注册和backboardd/SpringBoard渲染等待。若vst失败，则只修对应真实失败分支。LA旧SessionSyncEngine断言和KeyStore/Watchdog服务缺口继续独立记录，不跳BRK或伪装服务成功。
