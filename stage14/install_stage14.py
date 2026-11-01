"""Install AFTER original Stage11,12,13 installers, BEFORE pre_build. Dry-run default."""
from pathlib import Path
import argparse,hashlib,json,ast
HERE=Path(__file__).resolve().parent
PINS={
 'stage10/stage10-runtime/LegacyDisplayProbe.cpp':'ecde85db5133b93ff4b2bcde2400a41df34c92bbc34dcd51fefe455c162cf7ae',
 'stage10/stage10-runtime/NativeLegacyDisplay.cpp':'b46598a56b8fbeaa52269edf5ceb0ad6eb64b2b1389c0f8cb9945c5ff74acafb',
 'scripts/ci/instrument_aslr_short_diagnostics.py':'0539691c11bf879c803c4e79ae851de800b4c727bca694f2f7b97eaa0cfe390d',
}
EXTRA='''
# CDX14: name-filtered observation outside the pid<=26 log filter.
_cdx14_original_exception_instrument = exception_instrument
def exception_instrument(text):
    text = _cdx14_original_exception_instrument(text)
    if '/* CDX14_DAEMON_EXC */' in text: return text
    anchor = '\\t/* CDX_ASLR_EXC */'
    assert text.count(anchor) == 1
    extra = ('\\t/* CDX14_DAEMON_EXC */\\n'
        '\\textern void cdx14_daemon_exception(const char *, unsigned, uint64_t, uint64_t);\\n'
        '\\tcdx14_daemon_exception(proc_name_address(get_bsdtask_info(task)), exception,\\n'
        '\\t    codeCnt > 0 ? code[0] : 0, codeCnt > 1 ? code[1] : 0);\\n')
    return text.replace(anchor, extra + anchor)
'''
def sha(b):return hashlib.sha256(b).hexdigest()
def once(t,a,b):
    assert t.count(a)==1,repr(a);return t.replace(a,b)
def install(device,apply=False):
    raw={p:(device/p).read_bytes().replace(b'\r\n',b'\n') for p in PINS}
    for p,pin in PINS.items():assert sha(raw[p])==pin,'Stage13 source drift: '+p
    probe=raw['stage10/stage10-runtime/LegacyDisplayProbe.cpp'].decode()
    probe=once(probe,'#include <kern/task.h>','#include <kern/task.h>\n#include <kern/thread_call.h>\n#include <kern/clock.h>')
    probe=once(probe,'static unsigned consoleOwnership;','static unsigned consoleOwnership;\nextern "C" void cdx14_after_release(void);')
    probe=once(probe,'    PE_initialize_console(nullptr,kPEReleaseScreen);','    PE_initialize_console(nullptr,kPEReleaseScreen);\n    cdx14_after_release();')
    probe+='\n'+(HERE/'FrameSamples14.h').read_text(encoding='utf-8')+'\n'+(HERE/'ProviderProbe14.h').read_text(encoding='utf-8')
    backend=raw['stage10/stage10-runtime/NativeLegacyDisplay.cpp'].decode()
    backend=once(backend,'extern "C" bool native_legacy_prepare_scanout(void);',
        'extern "C" bool native_legacy_prepare_scanout(void);\n'
        'extern "C" void cdx14_frame_begin(void *,uint64_t,uint64_t,const void *,uint64_t,uint64_t,uint32_t,uint32_t);\n'
        'extern "C" void cdx14_frame_end(bool);\nextern "C" void cdx14_frame_gap(void);')
    backend=once(backend,'        if(!surface) {','        if(!surface) {\n            cdx14_frame_gap();')
    backend=once(backend,'        uint64_t copyStart;__asm__ volatile(',
        '        cdx14_frame_begin(reinterpret_cast<void *>(bootMapping->getVirtualAddress()),\n'
        '            bootMapping->getLength(),video.v_rowBytes,reinterpret_cast<const void *>(source->getVirtualAddress()),\n'
        '            source->getLength(),sourceStride,width,height);\n'
        '        uint64_t copyStart;__asm__ volatile(')
    backend=once(backend,'                OSSafeReleaseNULL(source);native_legacy_transfer_observed(kIOReturnBadArgument,request,0);return;',
        '                cdx14_frame_end(false);\n                OSSafeReleaseNULL(source);native_legacy_transfer_observed(kIOReturnBadArgument,request,0);return;')
    backend=once(backend,'        OSSafeReleaseNULL(source);transferred=true;',
        '        cdx14_frame_end(true);\n        OSSafeReleaseNULL(source);transferred=true;')
    gen=raw['scripts/ci/instrument_aslr_short_diagnostics.py'].decode()
    gen=once(gen,"if __name__=='__main__':",EXTRA+"\nif __name__=='__main__':");ast.parse(gen)
    patch='zzzzzzzzzzzzzzzzzzzzzz-cdx14-observation.patch'
    series=(device/'patches/xnu/device/series').read_text(encoding='utf-8')
    assert patch not in series
    changes={'stage10/stage10-runtime/LegacyDisplayProbe.cpp':probe.encode(),
        'stage10/stage10-runtime/NativeLegacyDisplay.cpp':backend.encode(),
        'scripts/ci/instrument_aslr_short_diagnostics.py':gen.encode(),
        'patches/xnu/device/'+patch:(HERE/patch).read_bytes(),
        'patches/xnu/device/series':(series.rstrip()+'\n'+patch+'\n').encode()}
    result=dict(stage=14,applied=apply,before={p:sha(b) for p,b in raw.items()},
        after={p:sha(b) for p,b in changes.items()},device_operations=False,full_kernel_compiled=False,runtime_verified=False)
    if apply:
        for p,b in changes.items():(device/p).write_bytes(b)
    return result
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--device',type=Path,required=True);p.add_argument('--apply',action='store_true');a=p.parse_args()
    print(json.dumps(install(a.device.resolve(),a.apply),indent=2))
