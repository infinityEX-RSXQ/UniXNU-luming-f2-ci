"""Qualify a source-built stage10 candidate before packaging; no device access."""
from pathlib import Path
import argparse,hashlib,json,struct,xml.etree.ElementTree as ET

def inspect(path):
    b=Path(path).read_bytes(); assert b[:4]==b'\xcf\xfa\xed\xfe','expected arm64 Mach-O'
    assert struct.unpack_from('<I',b,4)[0]==0x100000c,'expected arm64 CPU'
    off=32;raw=None;sym=None
    for _ in range(struct.unpack_from('<I',b,16)[0]):
        cmd,n=struct.unpack_from('<II',b,off);assert n>=8 and off+n<=len(b)
        if cmd==2:sym=struct.unpack_from('<IIII',b,off+8)
        if cmd==0x19 and b[off+8:off+24].rstrip(b'\0')==b'__PRELINK_INFO':
            fo,fs=struct.unpack_from('<QQ',b,off+40);assert fo+fs<=len(b);raw=b[fo:fo+fs].rstrip(b'\0')
        off+=n
    assert sym and raw,'need symbol table and prelink metadata, not only strings'
    root=ET.fromstring(raw);ids={e.attrib['ID']:e for e in root.iter() if 'ID' in e.attrib}
    def value(e):
        if 'IDREF' in e.attrib:return value(ids[e.attrib['IDREF']])
        if e.tag in ('string','key'):return e.text or ''
        if e.tag=='integer':return int(e.text or '0',0)
        if e.tag=='dict':
            c=list(e);return {value(c[i]):value(c[i+1]) for i in range(0,len(c),2)}
        if e.tag=='array':return [value(c) for c in e]
        if e.tag in ('true','false'):return e.tag=='true'
        if e.tag=='plist':return value(list(e)[0])
        return None
    meta=value(root);kexts=meta['_PrelinkInfoDictionary']
    defined=set();so,ns,st,ss=sym;assert so+ns*16<=len(b) and st+ss<=len(b)
    for i in range(ns):
        ix,t,sect,desc,va=struct.unpack_from('<IBBHQ',b,so+16*i)
        assert ix<ss
        if not t&0xe0 and t&0xe and sect and va:
            end=b.find(b'\0',st+ix,st+ss);assert end>=0
            defined.add(b[st+ix:end].decode('latin1'))
    return {'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b),'bundles':sorted({x['CFBundleIdentifier'] for x in kexts}),'defined':defined,'short_logs':all(x in b for x in [b'CDX_ASLR\0',b'CDX_EXC\0',b'p=%d n=%.16s off=%u slide=%x',b'p=%d e=%d c0=%llx c1=%llx'])}

def qualify(kernel,baseline,sha):
    now=inspect(kernel);base=inspect(baseline)
    assert now['sha256']==sha,'candidate hash differs from approved CI artifact hash'
    assert base['sha256']=='8a347cbdeac4a2e750c06235f1d4948a0acb47a5127480e872c2311069c9a933','stage9 baseline drift'
    assert set(base['bundles'])<=set(now['bundles']),'lost a previously working prelink dependency'
    assert set(now['bundles'])-set(base['bundles'])=={'com.apple.iokit.IOMobileGraphicsFamily'},'Expected only the original IOMobileGraphicsFamily addition'
    assert now['short_logs'],'short ASLR/exception diagnostics lost'
    for name in ['_native_legacy_display_probe','_native_legacy_display_late_probe','_native_legacy_display_allocate']:
        assert name in now['defined'],'missing defined runtime symbol '+name
    assert any('NativeLegacyDisplay' in n and ('__ZTV' in n or '__ZTC' in n) for n in now['defined']),'no concrete Legacy runtime vtable'
    return {'sha256':sha,'bytes':now['bytes'],'preserved_baseline_bundles':base['bundles'],'added_bundles':sorted(set(now['bundles'])-set(base['bundles'])),'display_symbols':[n for n in sorted(now['defined']) if 'native_legacy_display_' in n or 'NativeLegacyDisplay' in n],'short_logs':True,'qualified':True,'runtime_verified':False}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('kernel',type=Path);p.add_argument('--baseline',type=Path,required=True);p.add_argument('--sha256',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    result=qualify(a.kernel,a.baseline,a.sha256);a.output.write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result))
