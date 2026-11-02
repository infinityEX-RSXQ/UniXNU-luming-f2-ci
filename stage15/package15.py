"""Create a source-only handoff after local checks; no CI or device commands."""
from pathlib import Path
import difflib,hashlib,json,zipfile
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
def sha(b):return hashlib.sha256(b).hexdigest()
reports={n:json.loads((HERE/n).read_text(encoding='utf-8')) for n in
    ['integration-validation.json','host-validation.json','qualification-tests.json']}
assert all(r['passed'] for r in reports.values())
assert not reports['host-validation.json']['full_kernel_compiled']
for source,name in [('stage10/stage10-runtime/LegacyDisplayProbe.cpp','LegacyDisplayProbe.cpp'),
    ('stage10/stage10-runtime/NativeLegacyDisplay.cpp','NativeLegacyDisplay.cpp')]:
    assert sha((HERE/'runtime'/name).read_bytes())==reports['integration-validation.json']['after'][source]
baseline=ROOT/'builds/stage14p1-ci-work/p1-fixture/device/stage10/stage10-runtime'
diff=''
for name in ['LegacyDisplayProbe.cpp','NativeLegacyDisplay.cpp']:
    diff+=''.join(difflib.unified_diff((baseline/name).read_text(encoding='utf-8').splitlines(True),
        (HERE/'runtime'/name).read_text(encoding='utf-8').splitlines(True),fromfile='stage14p1/'+name,tofile='stage15/'+name))
(HERE/'stage14p1-to-stage15-source.diff').write_text(diff,encoding='utf-8',newline='\n')
(HERE/'DSH-STAGE15-IMPLEMENTATION-NOTES.md').write_bytes((ROOT/'stage15-analysis-20261102/DSH-STAGE15-IMPLEMENTATION-NOTES.md').read_bytes())
files=sorted(p for p in HERE.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name!='SOURCE-MANIFEST.json')
assert all(p.suffix.lower() not in ['.exe','.o','.macho','.img','.zip'] for p in files)
manifest={'stage':15,'source_only':True,'full_kernel_compiled':False,'runtime_verified':False,'device_operations':False,
    'base_ci_run':41363972872,'base_commit':'e65dff213b2f28d0cc92ca168dcd60b4f3e732ec',
    'files':{p.relative_to(HERE).as_posix():{'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())} for p in files}}
manifest_path=HERE/'SOURCE-MANIFEST.json';manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
files.append(manifest_path)
bundle=ROOT/'DSH-STAGE15-TRACE-SOURCE-20261102.zip';assert not bundle.exists(),'Existing handoff must be versioned explicitly'
with zipfile.ZipFile(bundle,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
    for p in files:z.write(p,HERE.name+'/'+p.relative_to(HERE).as_posix())
with zipfile.ZipFile(bundle) as z:
    assert z.testzip() is None
    for name,metadata in manifest['files'].items():assert sha(z.read(HERE.name+'/'+name))==metadata['sha256']
    assert z.read(HERE.name+'/SOURCE-MANIFEST.json')==manifest_path.read_bytes()
delivery={'stage':15,'bundle':str(bundle),'sha256':sha(bundle.read_bytes()),'bytes':bundle.stat().st_size,
    'file_count':len(files),'zip_crc_and_manifest_verified':True,'local_reports':reports,
    'ci_build_pending':True,'full_kernel_compiled':False,'runtime_verified':False,'device_operations':False}
(ROOT/'evidence/STAGE15-DELIVERY-20261102.json').write_text(json.dumps(delivery,ensure_ascii=False,indent=2),encoding='utf-8')
handover=f'''# 给 dsh：Stage15 源码已准备好

源码包：`{bundle}`

SHA256：`{delivery['sha256']}`（{delivery['bytes']} bytes；{len(files)} 个文件；ZIP CRC 和逐文件 SHA 已核对）

解包后先读 `stage15-trace-source-20261102/BUILD-REQUEST.md`。
沿用已成功的 Stage14.1 CI 41363972872 / e65dff213b2f28d0cc92ca168dcd60b4f3e732ec。
Stage11→12→13→14→14p1 后、pre_build/materialize 前执行本包 install_stage15.py；原五参数 ABI、ASLR/认证与 CPU 呈现保留。

新观察包括：16条 client owner 创建记录；源码 XNU IPC wrapper 的同线程关联（异步 unknown、submit=?）；validate/head/copy/retire 首末时间；独立 vsync；quiet 后 reclaim 前真实 GOP 晚采样；IOWatchdog/AppleKeyStore 匹配服务及真实类；短 daemon 摘要。
不改原版预链接 user-client selector，不用 current_proc 猜提交者，不造硬件服务，不跳 BRK。没有加入 GPU/触控驱动，也没有证明桌面已运行。

本地相关补丁链、功能测试、ARM64 GPR-only 接口夹具均通过；内核核验器的缺调用测试及旧 Stage14.1 拒绝测试通过。完整 XNU/IOKit 编译、链接、真机尚未完成；此包没有 kernel/super，没有执行刷写。

下一步由现有 CI 编译，交回 kernel.macho、SHA、build-report/manifest、stage15-install-report、最终 series/patch 与完整日志；按 BUILD-REQUEST 核验后再沿用现有 cpu-present+p26 参数打包测试。
预期约15秒触发 `CDX15 snapshot (intentional)`，请拍全摘要，尤其 F/L、vs、unknown、late、wd/aks、SB/BB/WD/LA。
若 CI 要修源码，保留实际 diff 并同步 install/expected SHA，不静默跳过核验。
'''
(ROOT/'HANDOVER-DSH-STAGE15-TRACE-20261102.md').write_text(handover,encoding='utf-8')
print(json.dumps({k:v for k,v in delivery.items() if k!='local_reports'},ensure_ascii=False,indent=2))
