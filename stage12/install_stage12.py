"""Run AFTER stage11 installer, BEFORE pre_build and stage10 runtime install.
Pinned isolated checkout only. Default dry run. No kernel binary/device edits.
"""
from pathlib import Path
import argparse,hashlib,importlib.util,json
HERE=Path(__file__).resolve().parent
PINS={
 'scripts/ci/instrument_crash_snapshot.py':'f3f75d2e7841580c5fd1d6ca6037efa06efa2867651a505021f06afe65c4d481',
 'stage10/stage10-runtime/LegacyDisplayProbe.cpp':'5c1ff177f2ddd833bf2df385d35700a19bd2a92faf987dfbdb7e89acd4f38d04',
 'stage10/stage10-runtime/NativeLegacyDisplay.cpp':'0ab790c93a086aad4639529126ec65b7228a7bb2fb4b921ebf4b9e590fe990a1',
}
def sha(data):return hashlib.sha256(data).hexdigest()
MODE_CAPTURE='''
#if defined(__arm64__)
\t/* CDX12_MODE: exact original fatal, not a general user-memory reader. */
\textern void cdx12_capture_mode(int, uint64_t);
\tif (exception == EXC_BREAKPOINT && codeCnt > 1 &&
\t    bootarg_disable_aslr && task->task_shared_region_slide == 0 &&
\t    code[1] == 0x19f3d0744ULL && thread->machine.upcb &&
\t    get_saved_state_pc(thread->machine.upcb) == 0x19f3d0744ULL &&
\t    strcmp(proc_name_address(get_bsdtask_info(task)), "SpringBoard") == 0) {
\t\tcdx12_capture_mode(proc_pid(get_bsdtask_info(task)),
\t\t    get_saved_state_reg(thread->machine.upcb, 19));
\t}
#endif
'''
def instrument12(text):
    marker='CAPTURE = '
    # Load string constants through AST, never execute the old CLI main.
    import ast
    tree=ast.parse(text)
    constants={n.targets[0].id:ast.literal_eval(n.value) for n in tree.body
        if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id in ('CAPTURE','SUMMARY')}
    assert set(constants)=={'CAPTURE','SUMMARY'}
    capture=constants['CAPTURE']+MODE_CAPTURE
    summary=constants['SUMMARY'].replace('char cdx11_reason[640];','char cdx11_reason[1024];')
    summary=summary.replace('\t\tprefix_str = cdx11_reason;',
        '\t\textern void cdx12_append_mode_summary(int, char *, size_t);\n'
        '\t\tcdx12_append_mode_summary(proc_getpid(p), cdx11_reason, sizeof(cdx11_reason));\n'
        '\t\tprefix_str = cdx11_reason;')
    assert summary!=constants['SUMMARY']
    # Replace only the two literal assignments; keep original transforms.
    lines=text.splitlines(keepends=True)
    for node in sorted([n for n in tree.body if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id in constants],key=lambda n:n.lineno,reverse=True):
        value=capture if node.targets[0].id=='CAPTURE' else summary
        lines[node.lineno-1:node.end_lineno]=[node.targets[0].id+' = '+repr(value)+'\n']
    changed=''.join(lines)
    anchor="return text.replace(anchor, anchor + CAPTURE)"
    assert changed.count(anchor)==1
    # ARM saved-state layout is declared explicitly only for the ARM candidate.
    changed=changed.replace(anchor,
        "changed = text.replace(anchor, anchor + CAPTURE)\n"
        "    include = '#if defined(__arm64__)\\n#include <arm/thread.h>\\n#endif\\n'\n"
        "    assert '#include <mach/thread_status.h>' in changed\n"
        "    return changed.replace('#include <mach/thread_status.h>', '#include <mach/thread_status.h>\\n'+include, 1)")
    ast.parse(changed)
    return changed

def backend12(text):
    anchor='extern "C" bool native_legacy_set_refresh_properties(void *display);'
    assert text.count(anchor)==1
    text=text.replace(anchor,anchor+'\nextern "C" void cdx12_refresh_observed(void *display);')
    old='if(primary && hz>60 && hz<=240)native_legacy_set_refresh_properties(this);'
    new='''unsigned publish60=0;PE_parse_boot_argn("luming-display-refresh-publish",&publish60,sizeof(publish60));
        if(primary && hz<=240 && (hz>60 || (publish60==1 && hz==60))) {
            native_legacy_set_refresh_properties(this);cdx12_refresh_observed(this);
        }'''
    assert text.count(old)==1
    return text.replace(old,new)

def install(device,apply=False):
    raw={}
    for rel,pin in PINS.items():
        data=(device/rel).read_bytes().replace(b'\r\n',b'\n');assert sha(data)==pin,'Stage11 source drift: '+rel;raw[rel]=data
    helper=(HERE/'ModeSnapshot.h').read_text(encoding='utf-8')
    observer='''
extern "C" void cdx12_refresh_observed(void *object) {
    IOService *display=static_cast<IOService *>(object);
    cdx12_refresh_calls=cdx12_refresh_calls+1;
    cdx12_refresh_present=display && display->getProperty("IOMFBDisplayRefresh")!=nullptr;
    IOLog("CDX12 refresh publish=%u property=%u\\n",cdx12_refresh_calls,cdx12_refresh_present);
}
'''
    changes={
     'scripts/ci/instrument_crash_snapshot.py':instrument12(raw['scripts/ci/instrument_crash_snapshot.py'].decode()).encode(),
     'stage10/stage10-runtime/NativeLegacyDisplay.cpp':backend12(raw['stage10/stage10-runtime/NativeLegacyDisplay.cpp'].decode()).encode(),
     'stage10/stage10-runtime/LegacyDisplayProbe.cpp':(raw['stage10/stage10-runtime/LegacyDisplayProbe.cpp'].decode()+'\n#include <libkern/copyio.h>\n'+helper+observer).encode(),
    }
    report={'stage':12,'before':{k:sha(v) for k,v in raw.items()},'after':{k:sha(v) for k,v in changes.items()},
        'applied':apply,'refresh_fix_requires_boot_arg':'luming-display-refresh-publish=1 and sheng-vsync=60',
        'mode_capture':'64 bytes copyin at qualified FBSDisplayMode fatal only',
        'full_kernel_compiled':False,'device_operations':False}
    if apply:
        for rel,data in changes.items():(device/rel).write_bytes(data)
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--device',type=Path,required=True);p.add_argument('--apply',action='store_true');a=p.parse_args()
    print(json.dumps(install(a.device.resolve(),a.apply),indent=2))
