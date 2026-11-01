"""Read-only qualification of the pinned 21H461 original Legacy class.
Nothing is written outside this task's work directory.
"""
from pathlib import Path
import argparse,hashlib,json,struct,sys
parser=argparse.ArgumentParser()
parser.add_argument('--tree',type=Path)
parser.add_argument('--kernelcache',type=Path,default=Path('D:/civitoip20/lumingios-cdx/stock-ipsw-analysis/kernelcache.ipad7.macho'))
parser.add_argument('--output',type=Path)
args=parser.parse_args()
sys.path.insert(0,str(args.tree/'kits/XnuPrelink') if args.tree else 'D:/civitoip20/unixnu-format2/components/XnuPrelink-luming')
import native_prelink as np
OUT=Path(__file__).resolve().parent
P=args.kernelcache
B=P.read_bytes();assert hashlib.sha256(B).hexdigest()=='f18b4df865405f2a287b84977d7aca745e056d656d9fc9df1662970ce2969de7'
I=np.macho(B);exports=np.exports(B,I);names={n:v for v,ns in exports.items() for n in ns}
def read(va,n):
    at=np.backed_offset(I['segments'],va,n,len(B));return B[at:at+n]
info=next(s for s in I['segments'] if s['name']=='__PRELINK_INFO')
meta=np.unserialize_xml(read(info['va'],info['filesize']))
entries={e['CFBundleIdentifier']:e for e in meta['_PrelinkInfoDictionary']}
family=entries['com.apple.iokit.IOMobileGraphicsFamily']
header=np.backed_offset(I['segments'],family['_PrelinkExecutableLoadAddr'],32,len(B))
bundle=np.macho(B,header)
text=next(s for s in bundle['segments'] if s['name']=='__TEXT_EXEC' and s['size'])
assert hashlib.sha256(read(text['va'],text['size'])).hexdigest()=='2e044ee68c1650397e1435234ca6459206262e4c7ed709cb7131c6f664f9bd9b'
SLIDE=-0x1000000
def raw(post):return post-SLIDE
def vptr(pc):
    a,b,c=struct.unpack('<3I',read(pc,12))
    assert a&0x9f00001f==0x90000008 and b&0xffc003ff==0x91000108 and c==0x91004108
    imm=((a>>5)&0x7ffff)*4+((a>>29)&3)
    if imm&(1<<20):imm-=1<<21
    return (pc&~4095)+(imm<<12)+((b>>10)&4095)+16
def branch(pc):
    w=struct.unpack('<I',read(pc,4))[0];assert w&0xfc000000==0x94000000
    q=w&0x3ffffff
    if q&(1<<25):q-=1<<26
    return pc+q*4
base_va=vptr(raw(0xfffffff00577b324));service_va=vptr(raw(0xfffffff00577b51c));legacy_va=vptr(raw(0xfffffff0057865d8))
assert branch(raw(0xfffffff0057865fc))==raw(0xfffffff00577b510)
assert branch(raw(0xfffffff00577b540))==raw(0xfffffff00577b318)
base=struct.unpack('<262Q',read(base_va,262*8));service=struct.unpack('<262Q',read(service_va,262*8));legacy=struct.unpack('<358Q',read(legacy_va,358*8))
assert [i for i,(a,b) in enumerate(zip(base,service)) if a!=b]==[0,1,7]
assert all(legacy) and read(legacy_va+358*8,24)==bytes(24)
pure=[i for i,a in enumerate(legacy) if a==names['___cxa_pure_virtual']]
assert pure==[211,213,245,246,306,307,337,338,345]
changed=[i for i,(a,b) in enumerate(zip(base,legacy)) if a!=b]
assert len(changed)==103 and [i for i in changed if i<168]==[0,1,7,14,21,44,79,85,86,87,111,141,155]
assert names['__ZN9IOService13newUserClientEP4taskPvjPP12IOUserClient']==base[141]
methods=[]
for i,a in enumerate(legacy):
    internal=text['va']<=a<text['va']+text['size']
    if i>=168 and i not in pure:assert internal
    methods.append({'slot':i,'raw_address':hex(a),'address':hex(a+SLIDE if internal else a),'family_internal':internal,'kernel_export_names':exports.get(a,[]),'abstract':i in pure})
getters=[]
for name,post,field,wide in [('descriptor',0xfffffff004b9ead0,48,True),('width',0xfffffff004b9ebbc,88,True),('height',0xfffffff004b9ebc4,96,True),('stride',0xfffffff004b9ebd4,104,True),('allocation',0xfffffff004b9ebfc,144,True),('format',0xfffffff004b9ebac,128,False),('planes',0xfffffff004b9ebf4,152,False)]:
    w=(0xf9400000 if wide else 0xb9400000)|((field//(8 if wide else 4))<<10)
    assert read(raw(post),8)==struct.pack('<2I',w,0xd65f03c0)
    getters.append({'name':name,'raw':hex(raw(post)),'rebased':hex(post),'field':field,'wide':wide})
# The original class's unique metaclass constructor loads the exact class
# string into x1, Service metaclass into x2, and object extent into w3.
def adrp_add(pc,register):
    a,b=struct.unpack('<2I',read(pc,8))
    assert a&0x9f00001f==0x90000000|register
    assert b&0xffc003ff==0x91000000|(register<<5)|register
    imm=(((a>>5)&0x7ffff)<<2)|((a>>29)&3)
    if imm&(1<<20):imm-=1<<21
    return (pc&~4095)+(imm<<12)+((b>>10)&4095)
class_string=adrp_add(raw(0xfffffff0057866a4),1)
assert read(class_string,len(b'IOMobileFramebufferLegacy\0'))==b'IOMobileFramebufferLegacy\0'
parent_meta=adrp_add(raw(0xfffffff0057866ac),2)
assert parent_meta==raw(0xfffffff006b31400)
assert read(raw(0xfffffff0057866b4),4)==struct.pack('<I',0x52831403)
meta_getter=legacy[7]
assert read(meta_getter,8)==bytes.fromhex('ff4300d1e00700f9')
actual_meta=adrp_add(meta_getter+8,0)
assert actual_meta==raw(0xfffffff006b35940)
# Owned announcePoweredByFirmware calls this exact original int-returning
# state setter with x0=self,x1=request,w2=false. The original family itself
# calls it with the same stack request shape, including powered-only updates.
# +0/+8 are skip words, +4/+12 are requested/powered, byte+16 is no-change.
setter=legacy[354]
assert setter==raw(0xfffffff0057970cc)
for offset,words in [
    (0x00,[0xd10103ff,0xa9037bfd,0x9100c3fd,0xf81f83a0,0xf81f03a1]),
    (0x14,[0x52800029,0x0a090048,0x381ef3a8]),
    (0x30,[0xf85f03a8,0x39404108,0x52000108,0x0a090108,0x381ee3a8]),
    (0x44,[0xf85f03a8,0xb9400108]),
    (0x5c,[0xf9400be9,0xf85f03a8,0xb9400508,0xb956cd29]),
    (0x7c,[0xf9400be9,0xf85f03a8,0xb9400508,0xb916cd28]),
    (0x98,[0xf85f03a8,0xb9400908]),
    (0xb0,[0xf9400be9,0xf85f03a8,0xb9400d08,0xb956d129]),
    (0xd0,[0xf9400be9,0xf85f03a8,0xb9400d08,0xb916d128]),
    (0xf8,[0xf9400be0,0xf9400008,0xf944a908,0xd63f0100]),
    (0x11c,[0xb9400fe0,0xa9437bfd,0x910103ff,0xd65f03c0])]:
    assert read(setter+offset,len(words)*4)==struct.pack('<'+'I'*len(words),*words)
assert legacy[298]==raw(0xfffffff0057a00bc)
assert read(legacy[298],20)==struct.pack('<5I',0xd10043ff,0xf90007e0,0x52800000,0x910043ff,0xd65f03c0)
# The original powered-only caller uses {skipRequested=1,skipPowered=0},
# writes its supplied power value to +12, and dispatches slot354(self,&req,false).
assert read(raw(0xfffffff00578b8a0),20)==bytes.fromhex('e81300b9e81b00b928008052e8830039e8870039')
assert read(raw(0xfffffff00578b920),44)==bytes.fromhex('e00740f9e1430091ff1b00b9a8035ff8e81f00b9080040f9088945f9090080522201001200013fd6a0431eb8')
result={'raw_kernel':str(P),'raw_original_path':str(P),'raw_sha256':hashlib.sha256(B).hexdigest(),'original_sha256':hashlib.sha256(B).hexdigest(),'intended_prelink_slide':SLIDE,'family':family,'family_text':{'address':hex(text['va']),'size':text['size'],'sha256':hashlib.sha256(read(text['va'],text['size'])).hexdigest()},'original_family_text_sha256':hashlib.sha256(read(text['va'],text['size'])).hexdigest(),'raw_base_vptr':hex(base_va),'raw_service_vptr':hex(service_va),'raw_legacy_vptr':hex(legacy_va),'base_vptr':hex(base_va+SLIDE),'service_vptr':hex(service_va+SLIDE),'legacy_vptr':hex(legacy_va+SLIDE),'legacy_slots':358,'legacy_virtual_entries':358,'legacy_instance_bytes':0x18a0,'abstract_slots':pure,'changed_slots':changed,'inherited_generic_changes':changed,'methods':methods,'iosurface_getters':getters,'instance_extent':{'value':0x18a0,'status':'statically proven in exact class-name/parent metaclass constructor','raw_size_instruction':hex(raw(0xfffffff0057866b4)),'raw_metaclass':hex(actual_meta),'raw_parent_metaclass':hex(parent_meta)},'new_user_client_abi':'IOService::newUserClient(task_t,void*,UInt32,IOUserClient**)','static_dispatch_audit':True,'legacy_runtime_instance_created':False,'original_instructions_modified':False,'warning':'Only family-internal method addresses receive kext slide. Kernel-export slots are rebound by native prelink and retain RAW addresses here solely for original symbol-name qualification.'}
result['firmware_power_setter']={'slot':354,'raw_address':hex(setter),'address':hex(setter+SLIDE),'abi':'int(self, StateRequest*, bool)','request_offsets':{'skip_requested':0,'requested':4,'skip_powered':8,'powered':12,'no_change':16},'original_powered_only_caller':hex(raw(0xfffffff00578b920)),'changed_callback_slot':298,'changed_callback_is_original_return_zero':True}
destination=args.output or OUT/'raw-legacy-abi.json'
destination.parent.mkdir(parents=True,exist_ok=True)
destination.write_text(json.dumps(result,indent=2),encoding='utf-8')
print('PASS pinned original family bytes, constructors, 358 vtable slots and IOSurface getters')
print('raw legacy vptr',hex(legacy_va),'postslide',hex(legacy_va+SLIDE),'family SHA',result['family_text']['sha256'])
