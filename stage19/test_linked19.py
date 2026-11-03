"""Synthetic Mach-O checks for the real linked kernel-consumer call gate."""
from pathlib import Path
import struct
from qualify_stage19_kernel import capture_call
BASE=0xfffffff007980000
def fixture(path,wrong=False,duplicate=False):
    names={'_cdx19_capture_next':BASE,'_next_fixture':BASE+0x40,
           '_stack_snapshot_from_kernel':BASE+0x80,'_end_fixture':BASE+0xc0}
    code=bytearray(struct.pack('<I',0xd65f03c0)*64)
    def bl(off,target):
        delta=target-(BASE+off);assert not delta%4
        struct.pack_into('<I',code,off,0x94000000|((delta//4)&0x3ffffff))
    bl(0,names['_stack_snapshot_from_kernel']+(4 if wrong else 0))
    if duplicate:bl(4,names['_stack_snapshot_from_kernel'])
    strings=bytearray(b'\0');symbols=bytearray()
    for name,addr in names.items():
        ix=len(strings);strings+=name.encode()+b'\0';symbols+=struct.pack('<IBBHQ',ix,0xf,1,0,addr)
    fileoff=0x100;table=fileoff+len(code);strtab=table+len(symbols)
    header=struct.pack('<8I',0xfeedfacf,0x100000c,0,2,2,96,0,0)
    segment=struct.pack('<II16sQQQQIIII',0x19,72,b'__TEXT',BASE,len(code),fileoff,len(code),7,5,0,0)
    sym=struct.pack('<6I',2,24,table,len(names),strtab,len(strings))
    path.write_bytes((header+segment+sym).ljust(fileoff,b'\0')+code+symbols+strings)
if __name__=='__main__':
    root=Path('D:/Codex/tmp/stage19-linked-fixtures');root.mkdir(exist_ok=True)
    good=root/'good.macho';fixture(good);assert len(capture_call(good)['direct_bl'])==1
    for label,kwargs in [('wrong-target',dict(wrong=True)),('duplicate',dict(duplicate=True))]:
        path=root/(label+'.macho');fixture(path,**kwargs)
        try:capture_call(path)
        except (AssertionError,ValueError):pass
        else:raise AssertionError('Invalid source API call accepted: '+label)
    print('Stage19 linked gate: exact source API accepted; wrong/duplicate calls rejected')
