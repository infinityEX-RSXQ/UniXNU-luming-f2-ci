"""Generate the self-contained CI builder from the pinned owned-source recipe.
Only used to prepare this handover; the generated builder is the CI artifact.
"""
from pathlib import Path
import hashlib

HERE=Path(__file__).resolve().parent
SOURCE=HERE.parent/'unixnu-reuse-20261029/sources/sheng/scripts/build-gop-legacy-display.py'
PIN='93e4bd23912dcbd26f090f7cf1f5b62fcb92a185c8e35dd5e0968deb31ebe777'
raw=SOURCE.read_bytes();assert hashlib.sha256(raw).hexdigest()==PIN
s=raw.decode().split("hid_source=ROOT/'kits/sheng/HidInputProbe.cpp'",1)[0]
s=s.replace('import hashlib\n','import hashlib\nimport os\n')
REPLAY_HELPER='''
def replay_command(record,source,destination,includes=()):
    # Preserve the actual XNU target/sysroot/language/ABI flags and working
    # directory, but never send a driver's dependency/JSON outputs back to
    # the source kernel's IOPlatformExpert compile record or dependency file.
    args=record['arguments'];command=[];i=0;inputs=outputs=0
    while i<len(args):
        value=args[i]
        if value==record['file']:
            command.append(str(source));inputs+=1
        elif value=='-o':
            if i+1>=len(args):raise ValueError('Missing compile output operand')
            command+=['-o',str(destination)];outputs+=1;i+=1
        elif value in ('-MF','-MT','-MJ'):
            if i+1>=len(args):raise ValueError('Missing dependency output operand')
            i+=1
        elif any(value.startswith(flag) and value!=flag for flag in ('-MF','-MT','-MJ')):
            pass
        elif value=='-Xclang' and i+1<len(args) and args[i+1].startswith('-W'):
            i+=1
        elif not value.startswith('-W'):
            command.append(value)
        i+=1
    if inputs!=1 or outputs!=1:
        raise ValueError('Expected exactly one source and one separate -o in the XNU record')
    command+=['-Wall','-Wextra','-Werror','-Wno-unused-parameter',
      '-Wno-unnecessary-virtual-specifier','-Wno-c99-designator','-Wno-reorder-init-list',
      '-Wno-deprecated-enum-enum-conversion','-I',str(ROOT/'.cache/xnu-work/osfmk')]
    for include in includes:command+=['-I',str(include)]
    return command

def compile_owned(source,destination,includes=()):
    recipe=ROOT/'build/xnu/ios-obj/DEVELOPMENT_ARM64_BCM2837/iokit/DEVELOPMENT/IOPlatformExpert.cpo.json'
    original=recipe.read_bytes()
    record=json.loads(original.decode().strip().rstrip(','))
    command=replay_command(record,source,destination,includes)
    destination.with_suffix('.compile-command.json').write_text(json.dumps(command,indent=2)+'\\n')
    result=subprocess.run(command,cwd=record['directory'],stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,text=True,timeout=90)
    destination.with_suffix('.compile.log').write_text(result.stdout)
    require(recipe.read_bytes()==original,'Owned compile altered the source-kernel record')
    require(result.returncode==0,result.stdout[-3500:])
    data=destination.read_bytes()
    require(struct.unpack_from('<4I',data)==(0xfeedfacf,0x100000c,0,1),
        'Expected ordinary ARM64 relocatable owned object')
    at=32;deployment=None
    for _ in range(struct.unpack_from('<I',data,16)[0]):
        cmd,length=struct.unpack_from('<II',data,at)
        if cmd==0x32:deployment=struct.unpack_from('<II',data,at+8)
        at+=length
    require(deployment==(2,0x110000),'Expected iOS 17 owned object deployment')
'''
anchor="def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()\n"
assert s.count(anchor)==1
s=s.replace(anchor,anchor+REPLAY_HELPER+'\n')
s=s.replace("print(run(['python3',ROOT/'scripts/audit-mobile-graphics-legacy.py'],text=True),end='')",'''SPEC=json.loads((ROOT/'kits/luming-cpu-display/build-config.json').read_text())
RAW_CACHE=Path(os.environ.get('LUMING_DISPLAY_KERNELCACHE') or os.environ.get('UNIXNU_KERNELCACHE') or SPEC['kernelcache'])
require(os.environ.get('XNU_NATIVE_LEGACY_DISPLAY')=='1','Run through the refreshed display-enabled defconfig')
patched_bsd=(ROOT/'.cache/xnu-work/bsd/kern/bsd_init.c').read_text()
require('native_legacy_display_late_probe();' in patched_bsd and
        'native_legacy_display_probe();' in patched_bsd and
        'offline-mobile-graphics-load' in patched_bsd,
        'The actual patched XNU source must contain both display lifecycle hooks')
require(sha(RAW_CACHE)==SPEC['kernelcache_sha256'],'Require unchanged exact 21H461 raw kernelcache')
print(run(['python3',ROOT/'scripts/audit-luming-raw-legacy.py','--tree',ROOT,'--kernelcache',RAW_CACHE,
           '--output',ROOT/'build/display-analysis/mobile-graphics-legacy-abi.json'],text=True),end='')''')
start=s.index("candidate=ROOT/'build/xnu-prelink/native-owner-mobile-graphics-candidate.macho'")
end=s.index('old=candidate.read_bytes();old_image=macho(old)',start)
s=s[:start]+'''candidate=RAW_CACHE
SLIDE=-0x1000000
require(audit['intended_prelink_slide']==SLIDE and audit['raw_sha256']==SPEC['kernelcache_sha256'],
        'Raw audit provenance and intended prelink slide')
require(int(audit['legacy_vptr'],16)==int(audit['raw_legacy_vptr'],16)+SLIDE,
        'Legacy vptr must explicitly be postslide, not the raw original address')
require(audit['legacy_instance_bytes']==0x18a0 and audit['instance_extent']['value']==0x18a0 and
        int(audit['instance_extent']['raw_metaclass'],16)+SLIDE==0xfffffff006b35940,
        'Independent exact original class extent and rebased metaclass identity')
'''+s[end:]
s=s.replace("at=backed_offset(old_image['segments'],va,n,len(old));return old[at:at+n]", "at=backed_offset(old_image['segments'],va-SLIDE,n,len(old));return old[at:at+n]")
s=s.replace("source=ROOT/'kits/sheng/LegacyDisplayProbe.cpp'", "source=ROOT/'kits/luming-cpu-display/LegacyDisplayProbe.cpp'")
# Both owned compilations use the same output-isolated replay, including the
# backend compilation that the shared build-arm-driver helper would pollute.
backend="print(run(['python3',ROOT/'scripts/build-arm-driver.py','NativeLegacyDisplay'],text=True),end='')"
assert s.count(backend)==1
s=s.replace(backend,"compile_owned(ROOT/'drivers/GopFramebuffer/NativeLegacyDisplay.cpp',OUT/'NativeLegacyDisplay.o',(OUT,))")
start=s.index("r=json.loads((ROOT/'build/xnu/ios-obj/DEVELOPMENT_ARM64_BCM2837/iokit/DEVELOPMENT/IOPlatformExpert.cpo.json')")
end=s.index("run(cmd,cwd=r['directory'])",start)+len("run(cmd,cwd=r['directory'])")
s=s[:start]+"source=ROOT/'kits/luming-cpu-display/LegacyDisplayProbe.cpp'\ncompile_owned(source,OUT/'LegacyDisplayProbe.o')"+s[end:]
s+='''
# CPU-only archive: no HID, KeyStore, GPU, SMMU, WiFi, touch, battery or SoC power objects.
archive=OUT/'libNativeLegacyDisplay.late.a'
archive.unlink(missing_ok=True)
run(['xcrun','ar','rcs',archive,late,OUT/'original-bindings.o',OUT/'LegacyDisplayProbe.o'])
sources=[ROOT/'drivers/GopFramebuffer/NativeLegacyDisplay.cpp',
         ROOT/'drivers/GopFramebuffer/NativeLegacyRequest.h',source,
         ROOT/'kits/luming-cpu-display/build-config.json']
(OUT/'build-report.json').write_text(json.dumps(dict(
    source_sha256={str(p.relative_to(ROOT)):sha(p) for p in sources},
    generated_abi_sha256=sha(OUT/'OriginalLegacyFramebufferABI.h'),
    original_kernelcache_sha256=sha(candidate),
    original_audit_sha256=sha(ROOT/'build/display-analysis/mobile-graphics-legacy-abi.json'),
    compiled_object_sha256=sha(obj),late_object_sha256=sha(late),archive_sha256=sha(archive),
    bindings={n:hex(v) for n,v in bindings.items()},virtual_entries=358,
    owned_entries=owned,inherited_native_entries=native,
    guarded_backend_leaves=[i for i in pure if i not in (213,337)],
    original_instructions_modified=False,driver_initialized=False,
    display_presented=False,desktop=False,cpu_only=True,
    archive_members=[late.name,'original-bindings.o','LegacyDisplayProbe.o'],
    upstream_generator_sha256='93e4bd23912dcbd26f090f7cf1f5b62fcb92a185c8e35dd5e0968deb31ebe777'),indent=2)+'\\n')
print('Built CPU-only Legacy archive; compile/ABI audit does not prove runtime presentation')
'''
compile(s,'build-luming-cpu-legacy-display.py','exec')
(HERE/'build-luming-cpu-legacy-display.py').write_text(s,encoding='utf-8')
(HERE/'upstream-generator.sha256').write_text(PIN+'  sheng/scripts/build-gop-legacy-display.py\n',encoding='utf-8')
print('Generated CPU-only archive builder',len(s),'bytes')
