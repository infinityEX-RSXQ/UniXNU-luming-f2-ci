from pathlib import Path
import json,struct,subprocess
R=Path('D:/civitoip20/lumingios-cdx/crash-symbolication')
maps=json.loads((R/'subcache-mappings.json').read_text())
def read(va,n=8):
    for row in maps:
        for m in row['mappings']:
            if m['address']<=va and va+n<=m['address']+m['size']:
                with (R/row['name']).open('rb') as f:
                    f.seek(m['offset']+va-m['address']);b=f.read(n);assert len(b)==n;return b
    raise ValueError(hex(va))
def q(va):return struct.unpack('<Q',read(va))[0]
def ptr(va):return q(va)&0x7ffffffff
def string(va):return read(va,512).split(b'\0')[0].decode('utf-8')
def sections(base):
    off=base+32;n=struct.unpack_from('<I',read(base,32),16)[0];out=[]
    for _ in range(n):
        cmd,size=struct.unpack('<II',read(off,8));b=read(off,size)
        if cmd==0x19:
            for j in range(struct.unpack_from('<I',b,64)[0]):
                s=struct.unpack_from('<16s16sQQIIIIIIII',b,72+80*j)
                out.append(dict(name=s[0].rstrip(b'\0').decode(),segment=s[1].rstrip(b'\0').decode(),va=s[2],size=s[3]))
        off+=size
    return out
def methods(ro):
    ls=ptr(ro+32)
    if not ls:return []
    if ls&1:
        array=ls&~1;size,count=struct.unpack('<II',read(array,8));assert size==8 and count<100
        out=[]
        for i in range(count):
            at=array+8+i*8;delta=struct.unpack('<q',read(at))[0]>>16
            try:out+=method_list(at+delta)
            except FileNotFoundError:pass
        return out
    return method_list(ls)
def method_list(ls):
    flags,count=struct.unpack('<II',read(ls,8));out=[]
    assert flags&0x80000000 and flags&0xfffc==12,(hex(ls),hex(flags))
    for i in range(count):
        at=ls+8+i*12;na,ty,im=struct.unpack('<iii',read(at,12))
        out.append({'selector':string(0x181d6b32c+na),'imp':hex(at+8+im)})
    return out
def classes(base):
    out=[]
    for s in sections(base):
        if s['name']!='__objc_classlist':continue
        for at in range(s['va'],s['va']+s['size'],8):
            cls=ptr(at);ro=ptr(cls+32)&~7
            name=string(ptr(ro+24))
            if name in ('CADisplayMode','CADisplay'):
                out.append({'name':name,'va':hex(cls),'ro':hex(ro),'methods':methods(ro)})
    return out
def disasm(code,start,name):
    head=struct.pack('<8I',0xfeedfacf,0x100000c,0,2,1,152,0,0)
    seg=struct.pack('<II16sQQQQIIII',0x19,152,b'__TEXT',start,len(code),0x1000,len(code),7,5,1,0)
    sec=struct.pack('<16s16sQQIIIIIIII',b'__text',b'__TEXT',start,len(code),0x1000,2,0,0,0x80000400,0,0,0)
    p=R/(name+'.macho');p.write_bytes((head+seg+sec).ljust(0x1000,b'\0')+code)
    b=subprocess.check_output(['D:/civitoip20/.tools/llvm/clang+llvm-23.1.4-x86_64-pc-windows-msvc/bin/llvm-objdump.exe','--macho','--disassemble',str(p)])
    (R/(name+'.asm')).write_bytes(b);return b.decode()
if __name__=='__main__':
    out=classes(0x189429000)
    (R/'quartzcore-display-methods.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
    for c in out:
        print(c['name'],c['va'])
        for m in c['methods']:
            if any(x in m['selector'].lower() for x in ('init','refresh','scale','width','height','mode')):print(m)
