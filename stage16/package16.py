from pathlib import Path
import difflib,hashlib,json,sys,zipfile
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;OLD=ROOT/'stage15-trace-source-20261102'
def sha(b):return hashlib.sha256(b).hexdigest()
validation=json.loads((HERE/'validation.json').read_text(encoding='utf-8'));assert validation['passed']
for file in ['LICENSE','qualification_base.py']:(HERE/file).write_bytes((OLD/file).read_bytes())
q=(OLD/'qualify_stage15_kernel.py').read_text(encoding='utf-8')
q=q.replace("'cdx15_daemon_summary',","'cdx15_daemon_summary','cdx16_vsync_observed',")
q=q.replace("b'CDX15 snapshot (intentional)'","b'CDX16 snapshot (intentional)',b'CDX16VsyncState'")
q=q.replace('stage=15,','stage=16,').replace("'integration-validation.json'","'validation.json'")
q=q.replace('missing Stage15 definition:','missing Stage16 definition:')
(HERE/'qualify_stage16_kernel.py').write_text(q,encoding='utf-8')
sys.path.insert(0,str(HERE));from qualify_stage16_kernel import check
build=ROOT/'builds/stage15-trace-41372922740'
try:check(build/'kernel.macho',ROOT/'builds/aslr-short-diag-20261101/kernel.macho',
    '3a125982ec62facaab9ae7a4b24a1a3e67756b6ab31374693742d1dd0e429d60',build/'build-report.json',HERE/'validation.json')
except AssertionError as e:rejected=str(e);assert rejected=='missing Stage16 definition: cdx16_vsync_observed',rejected
else:raise AssertionError('old kernel accepted')
(HERE/'qualification-negative.json').write_text(json.dumps({'passed':True,'stage15_rejected':rejected,'stage16_kernel_available':False},indent=2),encoding='utf-8')
diff=''
for name in ['LegacyDisplayProbe.cpp','NativeLegacyDisplay.cpp']:
    assert sha((HERE/'runtime'/name).read_bytes())==validation['after']['stage10/stage10-runtime/'+name]
    diff+=''.join(difflib.unified_diff((OLD/'runtime'/name).read_text(encoding='utf-8').splitlines(True),
        (HERE/'runtime'/name).read_text(encoding='utf-8').splitlines(True),fromfile='stage15/'+name,tofile='stage16/'+name))
(HERE/'stage15-to-stage16.diff').write_text(diff,encoding='utf-8',newline='\n')
(HERE/'STAGE15-RESULT-20261102-0943.md').write_bytes((ROOT/'evidence/STAGE15-RESULT-20261102-0943.md').read_bytes())
files=sorted(p for p in HERE.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name!='SOURCE-MANIFEST.json')
assert all(p.suffix.lower() not in ['.exe','.o','.macho','.img','.zip'] for p in files)
manifest={'stage':16,'source_only':True,'base_run':41372922740,'full_kernel_compiled':False,'runtime_verified':False,
    'files':{p.relative_to(HERE).as_posix():{'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())} for p in files}}
mp=HERE/'SOURCE-MANIFEST.json';mp.write_text(json.dumps(manifest,indent=2),encoding='utf-8');files.append(mp)
bundle=ROOT/'DSH-STAGE16-VSYNC-SOURCE-20261102.zip';assert not bundle.exists()
with zipfile.ZipFile(bundle,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
    for p in files:z.write(p,HERE.name+'/'+p.relative_to(HERE).as_posix())
with zipfile.ZipFile(bundle) as z:
    assert z.testzip() is None
    for name,m in manifest['files'].items():assert sha(z.read(HERE.name+'/'+name))==m['sha256']
delivery=dict(stage=16,bundle=str(bundle),sha256=sha(bundle.read_bytes()),bytes=bundle.stat().st_size,
    files=len(files),zip_and_manifest_verified=True,validation=validation,full_kernel_compiled=False,runtime_verified=False,device_operations=False)
(ROOT/'evidence/STAGE16-DELIVERY-20261102.json').write_text(json.dumps(delivery,indent=2),encoding='utf-8')
handover=f'''# 给 dsh：Stage15照片复核与Stage16源码

先读 `D:/civitoip20/lumingios-cdx/evidence/STAGE15-RESULT-20261102-0943.md`。
Stage15内核和本地super已独立核验；3次backboardd client关联帧完成，late样本一致。vs=0仍需区分初始化、无订阅或timer问题；没有证据直接跳到GPU。F/L全999999是诊断显示被截断，下一版已改相对时间。

源码包 `{bundle}`，SHA256 `{delivery['sha256']}`，{delivery['bytes']} bytes。
读包内BUILD-REQUEST.md，沿用Stage15成功run41372922740/commit ec66ac81fa5896213cb5da02168acd6649e47cc3，在stage15安装后追加install_stage16.py。
只补start/arm分支与时间诊断，保持原timer策略；未强制vsync、未改私有ABI、未伪造硬件服务。

本地功能/分支/ARM64 GPR-only夹具通过，旧Stage15内核拒绝测试通过，ZIP逐文件校验通过。尚未完整构建或真机测试，本轮没有刷机。
请现有CI构建并交回kernel/SHA、build-report/manifest、stage16-install-report、workflow实际diff、日志；核验通过再按原参数测试。
预期 `CDX16 snapshot (intentional)`；拍清vst/sa/ar/aa/sf/af/hz、vs、age/F/L、late和daemon摘要。分支码解释见BUILD-REQUEST.md。
'''
(ROOT/'HANDOVER-DSH-STAGE16-VSYNC-20261102.md').write_text(handover,encoding='utf-8')
print(json.dumps({k:v for k,v in delivery.items() if k!='validation'},indent=2))
