"""Prior graphics/ABI gates plus the real source-kernel stackshot call."""
from pathlib import Path
import json,struct,sys
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'stage18'))
sys.path.insert(0,str(HERE.parent/'stage18-wait-source-20261102'))
from qualify_stage18_kernel import check as check18,inspect
def capture_call(kernel):
    raw=kernel.read_bytes();at=32;segments=[];sym=None
    for _ in range(struct.unpack_from('<I',raw,16)[0]):
        cmd,n=struct.unpack_from('<II',raw,at)
        if cmd==2:sym=struct.unpack_from('<IIII',raw,at+8)
        if cmd==0x19:segments.append(struct.unpack_from('<QQQQ',raw,at+24))
        at+=n
    assert sym;table,count,strings,size=sym;names={}
    for i in range(count):
        ix,t,section,_,va=struct.unpack_from('<IBBHQ',raw,table+16*i)
        if t&0xe0 or not t&0xe or not section or not va:continue
        end=raw.find(b'\0',strings+ix,strings+size);assert end>=0
        names[raw[strings+ix:end].decode('latin1')]=va
    start=names['_cdx19_capture_next'];stop=min(v for v in names.values() if v>start)
    target=names['_stack_snapshot_from_kernel'];assert start!=target
    seg=next(s for s in segments if s[0]<=start and stop<=s[0]+s[3])
    code=raw[seg[2]+start-seg[0]:seg[2]+stop-seg[0]];hits=[]
    for i in range(0,len(code)-3,4):
        op=struct.unpack_from('<I',code,i)[0]
        if op&0xfc000000==0x94000000:
            imm=op&0x3ffffff
            if imm&(1<<25):imm-=1<<26
            if start+i+4*imm==target:hits.append(hex(start+i))
    assert len(hits)==1,('Expected real source-kernel stackshot call',hits)
    return dict(capture=hex(start),source_api=hex(target),direct_bl=hits)
def check(kernel,baseline,baseline_sha,report,expected):
    out=check18(kernel,baseline,baseline_sha,report,expected)
    raw=kernel.read_bytes()
    for marker in (b'CDX23 q=',b'CDX22 q=',b'luming-display-stack-thread',b'CDX21 q=',b'CDX21State0',b'CDX21State1',b'luming-display-stack-owner',b'luming-display-stackshot',b'CDX19Raw0',b'CDX19Raw1',b'CDX19State0',b'CDX19State1',b'stack=unavailable',b'CDX19 stackshot (intentional)'):
        assert marker in raw,marker
    wanted=json.loads(expected.read_text());assert wanted['backend_unchanged'] and wanted['generator_unchanged']
    out.update(stage=19,stackshot_call=capture_call(kernel),hardware_verified=False)
    return out
