"""Reject stale kernels and source/ABI drift before dsh packages a test image."""
from pathlib import Path
import argparse,json,struct,sys
ROOT=Path('D:/civitoip20/lumingios-cdx')
from qualification_base import qualify,inspect
REQUIRED=['cdx15_mapping_observed','cdx15_client_open','cdx15_ipc_begin','cdx15_ipc_end',
    'cdx15_validation','cdx15_head','cdx15_copy','cdx15_retire_begin','cdx15_retire_end',
    'cdx15_gate','cdx15_vsync','cdx15_target_observed','cdx15_snapshot','cdx15_daemon_summary',
    'cdx14p1_scanout_enter','cdx14p1_scanout_leave','cdx14p1_console_reclaim',
    'cdx14p1_schedule_snapshot','cdx13_publish_ui_scale']
def ipc_calls(kernel):
    raw=kernel.read_bytes();offset=32;segments=[];sym=None
    for _ in range(struct.unpack_from('<I',raw,16)[0]):
        command,length=struct.unpack_from('<II',raw,offset)
        if command==2:sym=struct.unpack_from('<IIII',raw,offset+8)
        if command==0x19:
            va,size,file,filesize=struct.unpack_from('<QQQQ',raw,offset+24)
            segments.append((va,size,file,filesize))
        offset+=length
    assert sym
    table,count,strings,string_bytes=sym;addresses={}
    for i in range(count):
        ix,typ,section,desc,va=struct.unpack_from('<IBBHQ',raw,table+16*i)
        if typ&0xe0 or not typ&0xe or not section or not va:continue
        end=raw.find(b'\0',strings+ix,strings+string_bytes);assert end>=0
        addresses[raw[strings+ix:end].decode('latin1')]=va
    name='__ZN12IOUserClient18callExternalMethodEjP25IOExternalMethodArguments'
    start=addresses[name];end=min(v for v in addresses.values() if v>start)
    assert 0<end-start<4096,'unexpected wrapper extent; inspect linked disassembly'
    segment=next(s for s in segments if s[0]<=start and end<=s[0]+s[3])
    data=raw[segment[2]+start-segment[0]:segment[2]+end-segment[0]];targets=[]
    for i in range(0,len(data)-3,4):
        word=struct.unpack_from('<I',data,i)[0]
        if word>>26==0x25:
            imm=word&0x3ffffff
            if imm&(1<<25):imm-=1<<26
            targets.append(start+i+4*imm)
    expected=[addresses['_cdx15_ipc_begin'],addresses['_cdx15_ipc_end']]
    assert all(t in targets for t in expected),'wrapper lacks direct calls to both Stage15 hooks; inspect veneers/inlining before accepting'
    assert targets.index(expected[0])<targets.index(expected[1]),'IPC observation order changed'
    return dict(wrapper=hex(start),begin=hex(expected[0]),end=hex(expected[1]),direct_calls_verified=True)
def check(kernel,baseline,sha,build_report,expected):
    result=qualify(kernel,baseline,sha);info=inspect(kernel)
    for name in REQUIRED:assert '_'+name in info['defined'],'missing Stage15 definition: '+name
    raw=kernel.read_bytes()
    for marker in [b'CDX15 snapshot (intentional)',b'CDX15TraceState',b'luming-display-trace',b'late=skip quiet=']:
        assert marker in raw,'missing Stage15 marker: '+repr(marker)
    report=json.loads(build_report.read_text(encoding='utf-8'))
    after=json.loads(expected.read_text(encoding='utf-8'))['after']
    for materialized,template in [('drivers/GopFramebuffer/NativeLegacyDisplay.cpp','stage10/stage10-runtime/NativeLegacyDisplay.cpp'),
        ('kits/luming-cpu-display/LegacyDisplayProbe.cpp','stage10/stage10-runtime/LegacyDisplayProbe.cpp')]:
        assert report['source_sha256'][materialized]==after[template],materialized+' source drift'
    assert report['generated_abi_sha256']=='8465dbcff188e88e66fdbe9a5e24b102c093b06d17f879f7a55fa3d1c58f8016'
    assert report['virtual_entries']==358
    assert report['original_kernelcache_sha256']=='f18b4df865405f2a287b84977d7aca745e056d656d9fc9df1662970ce2969de7'
    result.update(stage=15,stage15_definitions=REQUIRED,core_ipc_calls=ipc_calls(kernel),materialized_source_hashes_checked=True,
        original_private_abi_preserved=True,runtime_verified=False)
    return result
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--kernel',type=Path,required=True);p.add_argument('--sha256',required=True)
    p.add_argument('--build-report',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--baseline',type=Path,default=ROOT/'builds/aslr-short-diag-20261101/kernel.macho')
    p.add_argument('--expected',type=Path,default=Path(__file__).with_name('integration-validation.json'))
    a=p.parse_args();assert not a.output.exists(),'do not overwrite an existing qualification'
    result=check(a.kernel,a.baseline,a.sha256,a.build_report,a.expected)
    a.output.write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result))
