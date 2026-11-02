"""Verify linked source hashes, preserved ABI and direct calls in all three XNU wrappers."""
from pathlib import Path
import argparse,json,struct
from qualification_base import qualify,inspect
REQUIRED=['cdx15_ipc_begin','cdx15_ipc_end','cdx17_ipc_arguments','cdx17_port_begin','cdx17_port_end','cdx16_vsync_observed']
def calls(kernel):
    raw=kernel.read_bytes();off=32;segments=[];sym=None
    for _ in range(struct.unpack_from('<I',raw,16)[0]):
        cmd,n=struct.unpack_from('<II',raw,off)
        if cmd==2:sym=struct.unpack_from('<IIII',raw,off+8)
        if cmd==0x19:segments.append(struct.unpack_from('<QQQQ',raw,off+24))
        off+=n
    assert sym
    tab,count,strings,size=sym;addresses={}
    for i in range(count):
        ix,t,section,desc,va=struct.unpack_from('<IBBHQ',raw,tab+16*i)
        if t&0xe0 or not t&0xe or not section or not va:continue
        end=raw.find(b'\0',strings+ix,strings+size);assert end>=0
        addresses[raw[strings+ix:end].decode('latin1')]=va
    result={}
    for name,expected in [
        ('__ZN12IOUserClient18callExternalMethodEjP25IOExternalMethodArguments',['_cdx15_ipc_begin','_cdx17_ipc_arguments','_cdx15_ipc_end']),
        ('_is_io_connect_set_notification_port',['_cdx17_port_begin','_cdx17_port_end']),
        ('_is_io_connect_set_notification_port_64',['_cdx17_port_begin','_cdx17_port_end'])]:
        start=addresses[name];end=min(v for v in addresses.values() if v>start);assert 0<end-start<4096
        seg=next(s for s in segments if s[0]<=start and end<=s[0]+s[3])
        data=raw[seg[2]+start-seg[0]:seg[2]+end-seg[0]];targets=[]
        for i in range(0,len(data)-3,4):
            word=struct.unpack_from('<I',data,i)[0]
            if word>>26==0x25:
                imm=word&0x3ffffff
                if imm&(1<<25):imm-=1<<26
                targets.append(start+i+4*imm)
        seq=[targets.index(addresses[n]) for n in expected]
        assert seq==sorted(seq),(name,'observer order changed')
        result[name]=dict(address=hex(start),ordered_direct_calls=expected)
    return result
def check(kernel,baseline,sha,report,expected):
    out=qualify(kernel,baseline,sha);info=inspect(kernel);raw=kernel.read_bytes()
    assert all('_'+n in info['defined'] for n in REQUIRED)
    for s in [b'CDX17 snapshot (intentional)',b'CDX17IPCState',b'luming-display-ipc-page']:
        assert s in raw,repr(s)
    report=json.loads(report.read_text());after=json.loads(expected.read_text())['after']
    for a,b in [('kits/luming-cpu-display/LegacyDisplayProbe.cpp','LegacyDisplayProbe.cpp'),('drivers/GopFramebuffer/NativeLegacyDisplay.cpp','NativeLegacyDisplay.cpp')]:
        assert report['source_sha256'][a]==after['stage10/stage10-runtime/'+b]
    assert report['generated_abi_sha256']=='8465dbcff188e88e66fdbe9a5e24b102c093b06d17f879f7a55fa3d1c58f8016'
    assert report['virtual_entries']==358 and not report['original_instructions_modified']
    assert report['original_kernelcache_sha256']=='f18b4df865405f2a287b84977d7aca745e056d656d9fc9df1662970ce2969de7'
    out.update(stage=17,source_hashes_verified=True,core_calls=calls(kernel),runtime_verified=False)
    return out
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--kernel',type=Path,required=True);p.add_argument('--baseline',type=Path,required=True)
    p.add_argument('--sha256',required=True);p.add_argument('--report',type=Path,required=True);p.add_argument('--expected',type=Path,default=Path(__file__).with_name('validation.json'))
    p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
    r=check(a.kernel,a.baseline,a.sha256,a.report,a.expected);a.output.write_text(json.dumps(r,indent=2));print(json.dumps(r))
