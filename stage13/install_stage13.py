"""Apply AFTER the original stage11 and stage12 installers, before pre_build.
Pinned source-only candidate. Does not edit a kernel image or operate a device.
"""
from pathlib import Path
import argparse,ast,hashlib,json
HERE=Path(__file__).resolve().parent
PINS={
 'scripts/ci/instrument_crash_snapshot.py':'756d8bf8637f3b75abff7ac7422d7ebf78b08c21fac46105fae45f674979b3f6',
 'stage10/stage10-runtime/LegacyDisplayProbe.cpp':'a716b01d3bdbd056edf644edb89f5676f945e2ea596802a17149285c146780c1',
 'stage10/stage10-runtime/NativeLegacyDisplay.cpp':'b46598a56b8fbeaa52269edf5ceb0ad6eb64b2b1389c0f8cb9945c5ff74acafb',
}
def sha(b):return hashlib.sha256(b).hexdigest()
def generator(text):
    tree=ast.parse(text);lines=text.splitlines(keepends=True)
    for node in sorted([n for n in tree.body if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id in ('CAPTURE','SUMMARY')],key=lambda n:n.lineno,reverse=True):
        name=node.targets[0].id;value=ast.literal_eval(node.value)
        if name=='CAPTURE':
            old='\t\t    get_saved_state_reg(thread->machine.upcb, 19));'
            assert value.count(old)==1
            value=value.replace(old,old+'\n\t\textern void cdx13_capture_validity(int, uint64_t);\n'
                '\t\tcdx13_capture_validity(proc_pid(get_bsdtask_info(task)),\n'
                '\t\t    get_saved_state_reg(thread->machine.upcb, 28));')
        else:
            assert 'cdx12_append_mode_summary' in value
            value=value.replace('cdx12_append_mode_summary','cdx13_append_mode_summary')
        lines[node.lineno-1:node.end_lineno]=[name+' = '+repr(value)+'\n']
    changed=''.join(lines);ast.parse(changed);return changed
def install(device,apply=False):
    raw={}
    for rel,pin in PINS.items():
        b=(device/rel).read_bytes().replace(b'\r\n',b'\n')
        assert sha(b)==pin,'Stage12 source drift: '+rel;raw[rel]=b
    probe=raw['stage10/stage10-runtime/LegacyDisplayProbe.cpp'].decode()
    anchor='    IOLog("CDX_DISP mapped w=%u h=%u\\n",width,height);\n    return true;'
    assert probe.count(anchor)==1
    probe=probe.replace(anchor,
        '    IOLog("CDX_DISP mapped w=%u h=%u\\n",width,height);\n'
        '    return cdx13_publish_ui_scale(width,height);')
    decl='static unsigned option(const char *name) {'
    assert probe.count(decl)==1
    probe=probe.replace(decl,'extern "C" bool cdx13_publish_ui_scale(uint32_t,uint32_t);\n'+decl)
    probe+='\n'+(HERE/'UiScalePolicy.h').read_text(encoding='utf-8')+'\n'+(HERE/'ModeSummary13.h').read_text(encoding='utf-8')
    changes={
        'scripts/ci/instrument_crash_snapshot.py':generator(raw['scripts/ci/instrument_crash_snapshot.py'].decode()).encode(),
        'stage10/stage10-runtime/LegacyDisplayProbe.cpp':probe.encode(),
    }
    report=dict(stage=13,before={k:sha(v) for k,v in raw.items()},after={k:sha(changes.get(k,v)) for k,v in raw.items()},applied=apply,
        boot_arg='luming-display-ui-scale=2',refresh_or_backend_changes=False,
        vtable_or_instance_layout_changes=False,original_instructions_modified=False,
        full_kernel_compiled=False,runtime_verified=False,device_operations=False)
    if apply:
        for rel,b in changes.items():(device/rel).write_bytes(b)
    return report
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--device',type=Path,required=True);p.add_argument('--apply',action='store_true');a=p.parse_args()
    print(json.dumps(install(a.device.resolve(),a.apply),indent=2))
