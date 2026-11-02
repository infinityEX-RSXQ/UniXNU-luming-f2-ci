from pathlib import Path
import hashlib,json,struct
from qualify_stage15_kernel import check,ipc_calls,ROOT
HERE=Path(__file__).resolve().parent;TMP=Path('D:/Codex/tmp/stage15-host')
TMP.mkdir(parents=True,exist_ok=True)
names=['_cdx15_ipc_begin','_cdx15_ipc_end','__ZN12IOUserClient18callExternalMethodEjP25IOExternalMethodArguments','_next']
values=[0x1000,0x1004,0x1010,0x1020]
raw=bytearray(1024);struct.pack_into('<8I',raw,0,0xfeedfacf,0x100000c,0,2,2,96,0,0)
struct.pack_into('<II16sQQQQIIII',raw,32,0x19,72,b'__TEXT',0x1000,0x100,0x100,0x100,7,5,0,0)
struct.pack_into('<6I',raw,104,2,24,0x200,4,0x240,0x100)
strings=b'\0'
for i,(name,value) in enumerate(zip(names,values)):
    struct.pack_into('<IBBHQ',raw,0x200+16*i,len(strings),0xf,1,0,value);strings+=name.encode()+b'\0'
raw[0x240:0x240+len(strings)]=strings
for offset,target in [(0x110,0x1000),(0x114,0x1004)]:
    pc=0x1000+offset-0x100;struct.pack_into('<I',raw,offset,0x94000000|(((target-pc)//4)&0x3ffffff))
path=TMP/'linked-wrapper-fixture.macho';path.write_bytes(raw);assert ipc_calls(path)['direct_calls_verified']
struct.pack_into('<I',raw,0x114,0xd503201f);path.write_bytes(raw)
try:ipc_calls(path)
except AssertionError as e:missing_call=str(e)
else:raise AssertionError('A marker/definition-only wrapper was accepted')
old=ROOT/'builds/stage14p1-diagnostic-41363972872/kernel.macho'
try:
    check(old,ROOT/'builds/aslr-short-diag-20261101/kernel.macho',hashlib.sha256(old.read_bytes()).hexdigest(),
        old.with_name('build-report.json'),HERE/'integration-validation.json')
except AssertionError as e:
    rejected=str(e);assert 'missing Stage15 definition' in rejected,rejected
else:raise AssertionError('Old Stage14.1 kernel accepted')
result=dict(passed=True,linked_wrapper_positive_fixture=True,missing_call_negative_fixture=missing_call,
    stage14p1_negative_test=rejected,stage15_real_kernel_available=False)
(HERE/'qualification-tests.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result,indent=2))
