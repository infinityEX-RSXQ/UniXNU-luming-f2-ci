"""Check source provenance and actual linked wait/completion call sequences."""
from pathlib import Path
import json,struct,sys
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'stage17'))
# Local source package lives beside stage17-ipc-source instead of CI's stage17.
sys.path.insert(0,str(HERE.parent/'stage17-ipc-source-20261102'))
from qualify_stage17_kernel import inspect,calls
from qualification_base import qualify
REQUIRED=['cdx18_wait_begin','cdx18_wait_end','cdx18_done_begin','cdx18_done_end']
def linked_calls(kernel):
    raw=kernel.read_bytes();at=32;segments=[];sym=None
    for _ in range(struct.unpack_from('<I',raw,16)[0]):
        cmd,n=struct.unpack_from('<II',raw,at)
        if cmd==2:sym=struct.unpack_from('<IIII',raw,at+8)
        if cmd==0x19:segments.append(struct.unpack_from('<QQQQ',raw,at+24))
        at+=n
    assert sym
    tab,count,strings,size=sym;names={}
    for i in range(count):
        ix,t,section,_,va=struct.unpack_from('<IBBHQ',raw,tab+16*i)
        if t&0xe0 or not t&0xe or not section or not va:continue
        end=raw.find(b'\0',strings+ix,strings+size);assert end>=0
        names[raw[strings+ix:end].decode('latin1')]=va
    name='__ZN19NativeLegacyDisplay11waitForSwapEP12IOUserClientjjj'
    start=names[name];end=min(v for v in names.values() if v>start)
    def branches(lo,hi):
        seg=next(s for s in segments if s[0]<=lo and hi<=s[0]+s[3])
        data=raw[seg[2]+lo-seg[0]:seg[2]+hi-seg[0]];out=[]
        for i in range(0,len(data)-3,4):
            word=struct.unpack_from('<I',data,i)[0]
            if word&0xfc000000==0x94000000:
                imm=word&0x3ffffff
                if imm&(1<<25):imm-=1<<26
                out.append((lo+i,lo+i+4*imm))
        return out
    targets=[t for _,t in branches(start,end)]
    begin=targets.index(names['_cdx18_wait_begin'])
    parent=targets.index(0xfffffff00578d998,begin+1)
    finish=targets.index(names['_cdx18_wait_end'],parent+1)
    assert begin<parent<finish
    # retireSwap may be inlined; require a real begin -> original completion ->
    # end sequence within 8KiB of linked code, not just strings/symbol presence.
    allcalls=[]
    for seg in segments:
        if seg[3] and seg[0] and seg[3]<len(raw):
            allcalls.extend(branches(seg[0],seg[0]+seg[3]))
    spans=[]
    for addr,target in allcalls:
        if target!=names['_cdx18_done_begin']:continue
        following=[(a,t) for a,t in allcalls if addr<a<addr+8192]
        original=next(((a,t) for a,t in following if t==0xfffffff005795b88),None)
        if not original:continue
        final=next(((a,t) for a,t in following if a>original[0] and t==names['_cdx18_done_end']),None)
        if final:spans.append([hex(addr),hex(original[0]),hex(final[0])])
    assert spans,'no real original completion bracketed by observers'
    return dict(wait=hex(start),parent='0xfffffff00578d998',completion_spans=spans)
def check(kernel,baseline,sha,report,expected):
    out=qualify(kernel,baseline,sha);info=inspect(kernel);raw=kernel.read_bytes()
    assert all('_'+n in info['defined'] for n in REQUIRED)
    for marker in [b'CDX18WaitState',b'luming-display-wait-probe',b'boundary-samples',b'CDX17 snapshot (intentional)']:assert marker in raw
    report=json.loads(report.read_text());wanted=json.loads(expected.read_text())
    for a,b in [('kits/luming-cpu-display/LegacyDisplayProbe.cpp','LegacyDisplayProbe.cpp'),('drivers/GopFramebuffer/NativeLegacyDisplay.cpp','NativeLegacyDisplay.cpp')]:
        assert report['source_sha256'][a]==wanted['after']['stage10/stage10-runtime/'+b]
    assert report['generated_abi_sha256']==wanted['generated_abi_sha256']
    assert report['virtual_entries']==358 and 176 in report['owned_entries'] and not report['original_instructions_modified']
    assert report['bindings']['_cdx18_original_wait']=='0xfffffff00578d998'
    assert report['bindings']['_cdx18_original_complete']=='0xfffffff005795b88'
    assert report['original_kernelcache_sha256']=='f18b4df865405f2a287b84977d7aca745e056d656d9fc9df1662970ce2969de7'
    out.update(stage=18,source_hashes_verified=True,core_calls=calls(kernel),wait_calls=linked_calls(kernel),runtime_verified=False)
    return out
