"""Read-only selector/notification tracing on the successful Stage16 source."""
from pathlib import Path
import argparse,difflib,hashlib,json
HERE=Path(__file__).resolve().parent
PINS={
'stage10/stage10-runtime/LegacyDisplayProbe.cpp':'7ad53f1536861fe5ae529c89bf739d5ab11c72a93619668079e9ac30c535ea93',
'stage10/stage10-runtime/NativeLegacyDisplay.cpp':'6032eadd760591c93ea505fd94dbbd16ff081771a09b83a3fed5746a23dea374',
'patches/xnu/device/zzzzzzzzzzzzzzzzzzzzzzzz-cdx15-observe.patch':'5bd651af5b44260d769109b7cf8f14d06739b181b7b7e86cbc7203281f6bcda5'}
PATCH='patches/xnu/device/zzzzzzzzzzzzzzzzzzzzzzzz-cdx17-observe.patch'
def sha(b):return hashlib.sha256(b).hexdigest()
def once(t,a,b):assert t.count(a)==1,repr(a);return t.replace(a,b)
def install(device,apply=False):
    before={p:(device/p).read_bytes().replace(b'\r\n',b'\n') for p in PINS}
    for p,h in PINS.items():assert sha(before[p])==h,'Stage16 input drift: '+p
    assert not (device/PATCH).exists(),'Stage17 patch already exists'
    rel='stage10/stage10-runtime/LegacyDisplayProbe.cpp';probe=before[rel].decode()
    probe=once(probe,'CDX16 snapshot (intentional)','CDX17 snapshot (intentional)')
    anchor='extern "C" uint64_t cdx15_ipc_begin(void *object,uint32_t selector) {'
    extra=(HERE/'Trace17.h').read_text()+'\n'+(HERE/'Adapter17.h').read_text()+'\n'
    probe=once(probe,anchor,extra+anchor)
    probe=once(probe,'if(cdx15::client(cdx15_state,id))token=cdx15::begin(cdx15_state,id,thread,selector,now);',
        'if(auto *c=cdx15::client(cdx15_state,id)){\n        token=cdx15::begin(cdx15_state,id,thread,selector,now);\n        if(token)cdx17::begin(cdx17_state,token,id,c->pid,selector,0,false,now);\n    }')
    probe=once(probe,'    cdx15::end(cdx15_state,token,status,now);',
        '    cdx17::end(cdx17_state,token,0,status,now);\n    cdx15::end(cdx15_state,token,status,now);')
    anchor='    text.line("CDX16 quiet=%u gate=%x age=%u\\n",(unsigned)quiet,state.gate,cdx15_ms(mach_absolute_time(),clipped));'
    probe=once(probe,anchor,'    if(option("luming-display-ipc-page")!=2){\n'+(HERE/'Snapshot17.h').read_text()+'\n    }\n'+anchor)
    changes={rel:probe.encode(),PATCH:(HERE/Path(PATCH).name).read_bytes()}
    report=dict(stage=17,before={p:sha(b) for p,b in before.items()},after={
        'stage10/stage10-runtime/NativeLegacyDisplay.cpp':PINS['stage10/stage10-runtime/NativeLegacyDisplay.cpp'],
        **{p:sha(b) for p,b in changes.items()}},applied=apply,scheduling_policy_changed=False,
        prelinked_dispatch_changed=False,full_kernel_compiled=False,runtime_verified=False)
    if apply:
        for p,b in changes.items():target=device/p;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(b)
    return report
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--device',type=Path,required=True);p.add_argument('--apply',action='store_true');a=p.parse_args()
    print(json.dumps(install(a.device.resolve(),a.apply),indent=2))
