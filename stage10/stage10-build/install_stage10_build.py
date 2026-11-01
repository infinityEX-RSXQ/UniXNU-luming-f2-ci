"""Install CPU-only Legacy build integration into isolated CI checkouts.

Run after the existing stage9 pre_build hook, then rerun unixnu defconfig.
No device operations, original image changes, binary patches or credential access.
Without --apply, prints the validated plan and writes nothing.
"""
from pathlib import Path
import argparse,hashlib,json,re,shutil,subprocess,tomllib

HERE=Path(__file__).resolve().parent
PIN_CORE='33da81310819b86d3ea62cb704f156c56407764a'
PIN_CACHE='f18b4df865405f2a287b84977d7aca745e056d656d9fc9df1662970ce2969de7'
FAMILY='com.apple.iokit.IOMobileGraphicsFamily'
ARCHIVE='build-luming-cpu-legacy-display.py'

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def append_array(text,table,key,value):
    start=text.index('['+table+']')
    following=re.search(r'(?m)^\[',text[start+len(table)+2:])
    end=start+len(table)+2+following.start() if following else len(text)
    section=text[start:end]
    match=re.search(r'(?ms)^'+re.escape(key)+r'\s*=\s*\[(.*?)^\]',section)
    assert match,'Missing multiline array '+table+'.'+key
    array=tomllib.loads('x=['+match[1]+']')['x']
    if value in array:return text
    body=match[1].rstrip()
    if body and not body.endswith(','):body+=','
    body+='\n  '+json.dumps(value)+',\n'
    replacement=section[:match.start(1)]+body+section[match.end(1):]
    return text[:start]+replacement+text[end:]

def edit_config(text):
    key='CONFIG_XNU_NATIVE_LEGACY_DISPLAY'
    assert len(re.findall(r'(?m)^'+key+r'=',text))==1
    text=re.sub(r'(?m)^'+key+r'=[yn]$',key+'=y',text)
    for flag in ('CONFIG_XNU_NATIVE_MOBILE_DISPLAY','CONFIG_XNU_NATIVE_ADRENO'):
        assert re.search(r'(?m)^'+flag+r'=n$',text),'CPU-only baseline requires '+flag+'=n'
    assert key+'=y' in text
    return text

def mutation(board_text,config_text):
    before=tomllib.loads(board_text)
    assert before['schema_version']==2 and before['board']['name']=='luming'
    assert before['board']['os_profile']=='ipados-17.7.11-21H461'
    assert 'arch:patches/xnu/series' in before['kernel']['patch_series']
    pre=before['kernel']['prelink']
    assert int(pre['slide'],0)==-0x1000000
    assert pre['early_security_init']=='com.apple.driver.AppleMobileFileIntegrity=0xfffffff005ab4ae0'
    assert 'com.apple.iokit.IOSurface' in pre['roots']
    assert not any(x in pre['roots'] for x in ('com.apple.iokit.IOGPUFamily','com.apple.iokit.IOHIDFamily','com.apple.iokit.IOHIDEventDriver'))
    assert len(pre['roots']) in (27,28)
    updated=append_array(board_text,'kernel','archives',ARCHIVE)
    updated=append_array(updated,'kernel.prelink','roots',FAMILY)
    after=tomllib.loads(updated)
    expected=json.loads(json.dumps(before))
    if ARCHIVE not in expected['kernel']['archives']:expected['kernel']['archives'].append(ARCHIVE)
    if FAMILY not in expected['kernel']['prelink']['roots']:expected['kernel']['prelink']['roots'].append(FAMILY)
    assert after==expected,'Unrelated board setting changed'
    assert len(after['kernel']['prelink']['roots'])==28
    return updated,edit_config(config_text),after

def core_contract(tree):
    git=subprocess.run(['git','-C',str(tree),'rev-parse','HEAD'],capture_output=True,text=True,check=True).stdout.strip()
    assert git==PIN_CORE,'Core commit differs from qualified recipe: '+git
    shell=(tree/'scripts/build-xnu-4k-baseline.sh').read_text()
    assert 'XNU_NATIVE_LEGACY_DISPLAY' in shell and 'libNativeLegacyDisplay.late.a' in shell
    assert 'source_sha256' in shell and 'archive_sha256' in shell
    probes=(tree/'patches/xnu/offline-component-load-probes.patch').read_text()
    late=(tree/'patches/xnu/offline-legacy-start.patch').read_text()
    assert 'offline-mobile-graphics-load' in probes and 'native_legacy_display_probe' in probes
    assert 'native_legacy_display_late_probe' in late and 'IOKitBSDInit' in late
    series=(tree/'profiles/arch/arm64/patches/xnu/series').read_text()
    assert 'offline-component-load-probes.patch' in series and 'offline-legacy-start.patch' in series
    profile=tomllib.loads((tree/'profiles/os/ipados-17.7.11-21H461/profile.toml').read_text())
    assert profile['os']['xnu_revision']=='d8b80295118ef25ac3a784134bcf95cd8e88109f'
    assert profile['kernel']['prelink']['kernelcache_sha256']==PIN_CACHE
    return profile

def install(args):
    tree=args.tree.resolve();device=args.device.resolve();runtime=args.runtime_dir.resolve();audit=args.audit_dir.resolve()
    assert tree!=device
    profile=core_contract(tree)
    board_path=device/'board.toml';board_text=board_path.read_text(encoding='utf-8')
    board=tomllib.loads(board_text)
    config_path=device/'configs'/board['kernel']['defconfig']
    new_board,new_config,after=mutation(board_text,config_path.read_text(encoding='utf-8'))
    cache=Path(args.kernelcache).resolve()
    assert cache.is_file() and sha(cache)==PIN_CACHE
    files={
        HERE/'build-luming-cpu-legacy-display.py':tree/'scripts'/ARCHIVE,
        audit/'audit_raw_legacy.py':tree/'scripts/audit-luming-raw-legacy.py',
        runtime/'LegacyDisplayProbe.cpp':tree/'kits/luming-cpu-display/LegacyDisplayProbe.cpp',
        runtime/'NativeLegacyDisplay.cpp':tree/'drivers/GopFramebuffer/NativeLegacyDisplay.cpp',
        runtime/'NativeLegacyRequest.h':tree/'drivers/GopFramebuffer/NativeLegacyRequest.h',
        runtime/'LICENSE':tree/'kits/luming-cpu-display/LICENSE',
    }
    for p in files:assert p.is_file(),p
    for path in ('scripts/build-arm-driver.py','kits/XnuPrelink/native_prelink.py'):
        assert (tree/path).is_file(),path
    # The existing pre-build generator and its short event diagnostics are untouched.
    plan={'core':str(tree),'device':str(device),'core_commit':PIN_CORE,
          'kernelcache':str(cache),'kernelcache_sha256':PIN_CACHE,'prelink_slide':-0x1000000,
          'roots_before':len(board['kernel']['prelink']['roots']),'roots_after':28,
          'added_root':FAMILY,'added_archive':ARCHIVE,'mobile_display':False,'adreno':False,
          'board_before_sha256':sha(board_path),'defconfig_before_sha256':sha(config_path),
          'copies':[{ 'from':str(a),'to':str(b),'sha256':sha(a)} for a,b in files.items()],
          'preserved_existing_archives':board['kernel']['archives'],
          'preserved_sections':sorted(set(board)-{'kernel'}),
          'refresh_defconfig_required':True,'compiled':False,'device_tested':False}
    if not args.apply:
        print(json.dumps(plan,ensure_ascii=False,indent=2));return
    for src,dst in files.items():
        dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst)
    dst=tree/'kits/luming-cpu-display/build-config.json';dst.parent.mkdir(parents=True,exist_ok=True)
    dst.write_text(json.dumps({'kernelcache':str(cache),'kernelcache_sha256':PIN_CACHE,
        'core_commit':PIN_CORE,'slide':-0x1000000,'raw_audit_required':True},indent=2)+'\n')
    board_path.write_text(new_board,encoding='utf-8');config_path.write_text(new_config,encoding='utf-8')
    plan.update(board_after_sha256=sha(board_path),defconfig_after_sha256=sha(config_path))
    (tree/'kits/luming-cpu-display/install-report.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(plan,ensure_ascii=False,indent=2))

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--tree',type=Path,required=True);p.add_argument('--device',type=Path,required=True)
    p.add_argument('--kernelcache',required=True)
    p.add_argument('--runtime-dir',type=Path,default=HERE.parent/'stage10-runtime')
    p.add_argument('--audit-dir',type=Path,default=HERE.parent/'stage10-audit')
    p.add_argument('--apply',action='store_true')
    install(p.parse_args())

if __name__=='__main__':main()
