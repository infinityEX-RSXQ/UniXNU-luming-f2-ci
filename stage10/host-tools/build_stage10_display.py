"""Pack a qualified source-built display kernel over stage9, with variable sizes.
Only creates new artifacts. No fastboot/device operations. CI payload is not used.
"""
from pathlib import Path
import argparse,ast,hashlib,json,mmap,shutil,struct,sys,tomllib,zlib
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'sources'))
from fat32_inject import Fat32Volume
from qualify_stage10_kernel import qualify
helper=ROOT/'sources/build_stage3_streamed.py'
assert hashlib.sha256(helper.read_bytes()).hexdigest()=='c1e0ada2a36cf929ba06e5611deba6e36b84e66db38ac3f5332080a64ba873aa'
tree=ast.parse(helper.read_text(encoding='utf-8'))
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))],type_ignores=[]),str(helper),'exec'))

def stream_span(source,dest,off,size):
    with Path(source).open('rb') as f:
        f.seek(off)
        while size:
            b=f.read(min(size,1024*1024));assert b;dest.write(b);size-=len(b)

def replace_stream(fat,path,source):
    directory,name=path.rsplit('/',1);dc=fat.find_dir(directory)
    entries,buffer,_=fat.parse_dir(dc);entry=next(e for e in entries if e.name.upper()==name.upper())
    old=fat.chain(entry.cluster) if entry.cluster else []
    size=source.stat().st_size;needed=max(1,(size+fat.cluster_bytes-1)//fat.cluster_bytes)
    free=sum(1 for v in fat.fat[2:fat.cluster_count+2] if v==0)
    assert needed<=len(old)+free,'New kernel exceeds verified 80MiB FAT capacity; stop before release'
    chain=old[:needed]
    if needed>len(old):chain+=fat.alloc_chain(needed-len(old))
    for c in old[needed:]:fat.set_fat(c,0)
    for i,c in enumerate(chain):fat.set_fat(c,chain[i+1] if i+1<len(chain) else 0xfffffff)
    with source.open('rb') as f:
        left=size
        for c in chain:
            count=min(left,fat.cluster_bytes);chunk=f.read(count);assert len(chunk)==count
            off=fat.cluster_offset(c);fat.data[off:off+fat.cluster_bytes]=chunk.ljust(fat.cluster_bytes,b'\0');left-=count
        assert left==0 and not f.read(1)
    slot=(entry.slot+entry.lfn_count)*32
    struct.pack_into('<H',buffer,slot+20,chain[0]>>16);struct.pack_into('<H',buffer,slot+26,chain[0]&65535);struct.pack_into('<I',buffer,slot+28,size)
    fat._write_dir(dc,buffer);fat.update_fsinfo()

def add_args(config,extra):
    parsed=tomllib.loads(config.decode());args=next(e['args'] for e in parsed['entry'] if e['id']=='xnu')
    existing={x.split('=',1)[0] for x in args.split()}
    tokens=extra.split();assert tokens and len({x.split('=',1)[0] for x in tokens})==len(tokens)
    assert not existing.intersection(x.split('=',1)[0] for x in tokens),'No existing stage9 argument may be replaced'
    new=args+' '+' '.join(tokens)
    assert new.isascii() and len(new.encode('ascii'))<1024,'Arguments exceed the control firmware command-line buffer'
    oldline='args = '+json.dumps(args);newline='args = '+json.dumps(new)
    assert config.decode().count(oldline)==1
    changed=config.decode().replace(oldline,newline).encode()
    assert next(e['args'] for e in tomllib.loads(changed.decode())['entry'] if e['id']=='xnu')==new
    return changed,new

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--kernel',type=Path,required=True);ap.add_argument('--sha256',required=True);ap.add_argument('--ci-manifest',type=Path,required=True);ap.add_argument('--extra-args-file',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--report',type=Path,required=True);a=ap.parse_args()
    assert not a.out.exists() and not a.report.exists(),'Refuse to overwrite prior candidate or report'
    qualification=qualify(a.kernel,ROOT/'builds/aslr-short-diag-20261101/kernel.macho',a.sha256)
    ci=json.loads(a.ci_manifest.read_text(encoding='utf-8'));assert any(x['path'].endswith('/kernel.macho') and x['sha256']==a.sha256 and x['bytes']==a.kernel.stat().st_size for x in ci['files'])
    base=ROOT/'images/super-stage9-aslr-short.img';assert hash_file(base)=='e09e044cac914db5c711261c7f63f8a78368fe1df183dd56bc3c45dd4765e5de'
    header,table,members=read_j2(base)
    baseline=MappedFat(base,members['payload']['offset'],members['payload']['size'])
    paths=[p for p in baseline.list_paths() if not p.endswith('/')];before={p:baseline.file_hash(p) for p in paths}
    oldcfg=baseline.read_file('EFI/UniXNU/unixnu.toml');newcfg,args=add_args(oldcfg,a.extra_args_file.read_text(encoding='utf-8').strip())
    entry=baseline.find_entry(baseline.find_dir('EFI/UniXNU/Payloads'),'kernel.macho')
    capacity=(sum(1 for v in baseline.fat[2:baseline.cluster_count+2] if v==0)+len(baseline.chain(entry.cluster)))*baseline.cluster_bytes
    assert a.kernel.stat().st_size<=capacity,'Display kernel does not fit existing payload; image resize requires separate validation'
    baseline.close()
    work=a.out.parent/(a.out.name+'.work');assert not work.exists();work.mkdir(parents=True)
    payload=work/'payload.img'
    with payload.open('xb') as f:stream_span(base,f,members['payload']['offset'],members['payload']['size'])
    fat=MappedFat(payload,write=True)
    try:
        replace_stream(fat,'EFI/UniXNU/Payloads/kernel.macho',a.kernel)
        fat.replace_file('EFI/UniXNU/unixnu.toml',newcfg);fat.mapping.flush()
    finally:fat.close()
    fat=MappedFat(payload)
    try:
        assert paths==[p for p in fat.list_paths() if not p.endswith('/')]
        checks=[]
        for p,h in before.items():
            after=fat.file_hash(p)
            expected=a.sha256 if p=='EFI/UniXNU/Payloads/kernel.macho' else hashlib.sha256(newcfg).hexdigest() if p=='EFI/UniXNU/unixnu.toml' else h
            assert after==expected,p;checks.append({'path':p,'before':h,'after':after})
        assert fat.read_file('EFI/UniXNU/unixnu.toml')==newcfg
    finally:fat.close()
    config=work/'outer.toml'
    with base.open('rb') as f:f.seek(members['config']['offset']);old_outer=f.read(members['config']['size'])
    new_outer,outerargs=add_args(old_outer,a.extra_args_file.read_text(encoding='utf-8').strip());assert args==outerargs;config.write_bytes(new_outer)
    members['kernel'].update(path=a.kernel,offset=0,size=a.kernel.stat().st_size)
    members['payload'].update(path=payload,offset=0,size=payload.stat().st_size)
    members['config'].update(path=config,offset=0,size=config.stat().st_size)
    nh=bytearray(header);nt=bytearray(table);cursor=8192
    for i,(name,item) in enumerate(members.items()):
        item['target_offset']=cursor;crc=span_hash(item['path'],item['offset'],item['size'],True)
        struct.pack_into('<24sIIQQII',nt,i*64,name.encode(),item['mid'],item['flags'],cursor,item['size'],crc,item['reserved']);cursor=(cursor+item['size']+4095)&~4095
    struct.pack_into('<Q',nh,32,cursor);struct.pack_into('<I',nh,52,zlib.crc32(nt)&0xffffffff);struct.pack_into('<I',nh,44,0);struct.pack_into('<I',nh,44,zlib.crc32(nh)&0xffffffff)
    part=work/'super.part'
    with part.open('xb') as f:
        f.write(nh);f.write(nt)
        for item in members.values():f.seek(item['target_offset']);stream_span(item['path'],f,item['offset'],item['size'])
        f.seek(cursor-1);f.write(b'\0')
    _,_,checked=read_j2(part)
    for name,item in checked.items():assert span_hash(part,item['offset'],item['size'])==span_hash(members[name]['path'],members[name]['offset'],members[name]['size']),name
    control=ROOT/'images/boot-owner-C-control.img';assert hash_file(control)=='bbd3718b380f6541c514992b55de418ed33302d05646db3803fef8533ffc6579'
    result={'stage':10,'purpose':'Legacy CPU display candidate','kernel_qualification':qualification,'super_file':str(a.out.resolve()),'super_sha256':hash_file(part),'super_bytes':cursor,'effective_args':args,'file_checks':checks,'j2_crcs_and_spans_checked':True,'kernel_size_change_supported':True,'ci_payload_used':False,'adt_trustcache_seed_preserved':True,'control_boot_sha256':hash_file(control),'hardware_tested':False}
    part.replace(a.out);a.report.write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result))

if __name__=='__main__':main()
