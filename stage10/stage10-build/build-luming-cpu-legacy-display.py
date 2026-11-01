#!/usr/bin/env python3
"""Bind an owned concrete backend to the unchanged original Legacy lifecycle."""
import hashlib
import os
import json
from pathlib import Path
import struct
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/native-legacy-display';OUT.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(ROOT/'kits/XnuPrelink'))
from native_prelink import macho,backed_offset,exports
def run(cmd,**kw):return subprocess.check_output([str(x) for x in cmd],timeout=90,**kw)
def require(v,why):
    if not v:raise SystemExit(why)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def replay_command(record,source,destination,includes=()):
    # Preserve the actual XNU target/sysroot/language/ABI flags and working
    # directory, but never send a driver's dependency/JSON outputs back to
    # the source kernel's IOPlatformExpert compile record or dependency file.
    args=record['arguments'];command=[];i=0;inputs=outputs=0
    while i<len(args):
        value=args[i]
        if value==record['file']:
            command.append(str(source));inputs+=1
        elif value=='-o':
            if i+1>=len(args):raise ValueError('Missing compile output operand')
            command+=['-o',str(destination)];outputs+=1;i+=1
        elif value in ('-MF','-MT','-MJ'):
            if i+1>=len(args):raise ValueError('Missing dependency output operand')
            i+=1
        elif any(value.startswith(flag) and value!=flag for flag in ('-MF','-MT','-MJ')):
            pass
        elif value=='-Xclang' and i+1<len(args) and args[i+1].startswith('-W'):
            i+=1
        elif not value.startswith('-W'):
            command.append(value)
        i+=1
    if inputs!=1 or outputs!=1:
        raise ValueError('Expected exactly one source and one separate -o in the XNU record')
    command+=['-Wall','-Wextra','-Werror','-Wno-unused-parameter',
      '-Wno-unknown-warning-option','-Wno-c99-designator','-Wno-reorder-init-list',
      '-Wno-deprecated-enum-enum-conversion','-I',str(ROOT/'.cache/xnu-work/osfmk')]
    for include in includes:command+=['-I',str(include)]
    return command

def compile_owned(source,destination,includes=()):
    recipe=ROOT/'build/xnu/ios-obj/DEVELOPMENT_ARM64_BCM2837/iokit/DEVELOPMENT/IOPlatformExpert.cpo.json'
    original=recipe.read_bytes()
    record=json.loads(original.decode().strip().rstrip(','))
    command=replay_command(record,source,destination,includes)
    destination.with_suffix('.compile-command.json').write_text(json.dumps(command,indent=2)+'\n')
    result=subprocess.run(command,cwd=record['directory'],stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,text=True,timeout=90)
    destination.with_suffix('.compile.log').write_text(result.stdout)
    require(recipe.read_bytes()==original,'Owned compile altered the source-kernel record')
    require(result.returncode==0,result.stdout[-3500:])
    data=destination.read_bytes()
    require(struct.unpack_from('<4I',data)==(0xfeedfacf,0x100000c,0,1),
        'Expected ordinary ARM64 relocatable owned object')
    at=32;deployment=None
    for _ in range(struct.unpack_from('<I',data,16)[0]):
        cmd,length=struct.unpack_from('<II',data,at)
        if cmd==0x32:deployment=struct.unpack_from('<II',data,at+8)
        at+=length
    require(deployment==(2,0x110000),'Expected iOS 17 owned object deployment')


def materialize_installed_inputs():
    # "unixnu build" runs this recipe from out/<device>/<os-profile>/<name>/tree, which links
    # only the declared modules; the installer stages its non-module inputs in the core
    # checkout. Compile inputs and the reported source hashes must name files inside this
    # tree, so copy exactly the installer-owned inputs here before any guard reads them.
    names=('drivers/GopFramebuffer/NativeLegacyDisplay.cpp',
           'drivers/GopFramebuffer/NativeLegacyRequest.h',
           'kits/luming-cpu-display/LegacyDisplayProbe.cpp',
           'kits/luming-cpu-display/build-config.json')
    installed=None
    for candidate in [os.environ.get('UNIXNU_CORE','')]+[str(parent) for parent in ROOT.parents]:
        if candidate and (Path(candidate)/'kits/luming-cpu-display/build-config.json').is_file():
            installed=Path(candidate);break
    for name in names:
        destination=ROOT/name
        if installed is None:
            require(destination.is_file(),'Stage10 input missing from both the build tree and its core checkout: '+name)
            continue
        source=installed/name
        require(source.is_file(),'Missing installed Stage10 input '+str(source))
        destination.parent.mkdir(parents=True,exist_ok=True)
        if not destination.is_file() or destination.read_bytes()!=source.read_bytes():
            destination.write_bytes(source.read_bytes())
materialize_installed_inputs()
SPEC=json.loads((ROOT/'kits/luming-cpu-display/build-config.json').read_text())
RAW_CACHE=Path(os.environ.get('LUMING_DISPLAY_KERNELCACHE') or os.environ.get('UNIXNU_KERNELCACHE') or SPEC['kernelcache'])
require(os.environ.get('XNU_NATIVE_LEGACY_DISPLAY')=='1','Run through the refreshed display-enabled defconfig')
patched_bsd=(ROOT/'.cache/xnu-work/bsd/kern/bsd_init.c').read_text()
require('native_legacy_display_late_probe();' in patched_bsd and
        'native_legacy_display_probe();' in patched_bsd and
        'offline-mobile-graphics-load' in patched_bsd,
        'The actual patched XNU source must contain both display lifecycle hooks')
require(sha(RAW_CACHE)==SPEC['kernelcache_sha256'],'Require unchanged exact 21H461 raw kernelcache')
print(run(['python3',ROOT/'scripts/audit-luming-raw-legacy.py','--tree',ROOT,'--kernelcache',RAW_CACHE,
           '--output',ROOT/'build/display-analysis/mobile-graphics-legacy-abi.json'],text=True),end='')
audit=json.loads((ROOT/'build/display-analysis/mobile-graphics-legacy-abi.json').read_text())
pure=audit['abstract_slots'];methods=audit['methods']
header='''// SPDX-License-Identifier: BSD-2-Clause-Patent
// Opaque ABI storage for the exact original class, not source-level access
// to its private fields. The actual original metadata supplies its full
// Framebuffer/Service/IOService ancestry. Only qualified base prototypes may
// be called from source; opaque entries are original dispatch targets only.
#pragma once
#include <IOKit/IOService.h>
#include <libkern/libkern.h>
struct OriginalLegacySwapRequest;
class IOMobileFramebufferLegacy : public IOService {
 OSDeclareAbstractStructors(IOMobileFramebufferLegacy)
 unsigned char originalPrivate[0x18a0-sizeof(IOService)];
public:
 // Both fields are qualified by the complete original slot-249 getter.
 // This modifies this object's own mode state, never a vtable or executable.
 void installBootDimensions(uint32_t width,uint32_t height) {
  *reinterpret_cast<uint32_t *>(reinterpret_cast<unsigned char *>(this)+5808)=width;
  *reinterpret_cast<uint32_t *>(reinterpret_cast<unsigned char *>(this)+5812)=height;
 }
 const OriginalLegacySwapRequest *pendingSwapRequest() const {
  const OriginalLegacySwapRequest *request=nullptr;
  memcpy(&request,reinterpret_cast<const unsigned char *>(this)+5480,sizeof(request));return request;
 }
 // The real normal scanout backend removes its pending head before calling
 // slot 295. Slot 312 is a discard path (terminal state 8), not presentation.
 // The queue is a tail queue (head at +5480, tail pointer at +5488, each request's next at +2960 and previous-link at +2968): taking the head
 // moves the next request, if a client already queued one behind it (int-132: swap 3 arrived during swap 2's GPU copy and the old
 // single-entry form refused to retire swap 2, so every wait on it stayed busy), up to the head. The original queue's reference
 // moves to the current-swap slot for the original completion body.
 bool activateOnlyPendingSwap(const OriginalLegacySwapRequest *request) {
  auto self=reinterpret_cast<unsigned char *>(this);
  auto bytes=reinterpret_cast<const unsigned char *>(request);
  const void *current=nullptr,*head=nullptr,*tail=nullptr,*next=nullptr,*previous=nullptr;
  memcpy(&current,self+5472,8);memcpy(&head,self+5480,8);memcpy(&tail,self+5488,8);
  if(!request || current || head!=request)return false;
  memcpy(&next,bytes+2960,8);memcpy(&previous,bytes+2968,8);
  if(previous!=self+5480)return false;
  if(next) {
   const void *link=self+5480;
   memcpy(const_cast<unsigned char *>(reinterpret_cast<const unsigned char *>(next))+2968,&link,8);
  } else if(tail!=bytes+2960)return false;
  memcpy(self+5472,&request,8);
  if(next) {memcpy(self+5480,&next,8);}
  else {const void *empty=nullptr,*emptyTail=self+5480;memcpy(self+5480,&empty,8);memcpy(self+5488,&emptyTail,8);}
  return true;
 }
 void free() override;
 bool init(OSDictionary *properties=nullptr) override;
 IOReturn setProperties(OSObject *) override;
 void systemWillShutdown(IOOptionBits) override;
 IOService *probe(IOService *,SInt32 *) override;
 bool start(IOService *) override;
 void stop(IOService *) override;
 IOWorkLoop *getWorkLoop() const override;
 IOReturn newUserClient(task_t,void *,UInt32,IOUserClient **) override;
 IOReturn setPowerState(unsigned long,IOService *) override;
'''
for i in range(168,358):
    if i==184:header+=' virtual bool isMainDisplay();\n'
    elif i==188:header+=' virtual IOReturn getDotPitch(uint32_t *);\n'
    elif i==213:header+=' virtual IOReturn supportedFrameInfo(uint32_t,uint32_t *,char *,uint32_t *)=0;\n'
    elif i==249:header+=' virtual void getDisplayDimensions(uint32_t *,uint32_t *);\n'
    elif i==290:header+=' virtual void kickSwapQueue();\n'
    elif i==296:header+=' virtual bool validateSwap(const OriginalLegacySwapRequest *);\n'
    elif i==295:header+=' virtual void completeCurrentSwap();\n'
    elif i==337:header+=' virtual IOReturn collectCompletionReports(uint32_t,void *,uint32_t *,uint32_t)=0;\n'
    elif i==288:header+=' virtual bool startHardware();\n'
    elif i==301:header+=' virtual bool getRefreshAttributes(uint64_t *,bool);\n'
    elif i in pure:header+=f' virtual __attribute__((noreturn)) void opaque{i}()=0;\n'
    else:header+=f' virtual __attribute__((deprecated("Unclassified ABI: never call from source"))) void opaque{i}();\n'
header+='};\nstatic_assert(sizeof(IOMobileFramebufferLegacy)==0x18a0,"Actual original instance extent");\n'
(OUT/'OriginalLegacyFramebufferABI.h').write_text(header)
compile_owned(ROOT/'drivers/GopFramebuffer/NativeLegacyDisplay.cpp',OUT/'NativeLegacyDisplay.o',(OUT,))
obj=OUT/'NativeLegacyDisplay.o';raw=obj.read_bytes();image=macho(raw)
st=next(p for c,p,_ in image['commands'] if c==2);sy,count,strings,_=struct.unpack_from('<4I',raw,st+8);symbols=[]
for i in range(count):
    ix,kind,section,_,va=struct.unpack_from('<IBBHQ',raw,sy+i*16)
    symbols.append((raw[strings+ix:raw.index(b'\0',strings+ix)].decode(),va,kind))
vtable=next(va for name,va,_ in symbols if name=='__ZTV19NativeLegacyDisplay');relocations={}
for segment in image['segments']:
    for sec in segment['sections']:
        if sec['va']<=vtable<sec['va']+sec['size']:
            ro,rc=struct.unpack_from('<2I',raw,sec['command_offset']+56)
            for i in range(rc):
                offset,bits=struct.unpack_from('<2I',raw,ro+i*8)
                if bits>>27&1 and bits>>28==0 and bits>>25&3==3:relocations[sec['va']+offset]=symbols[bits&0xffffff][0]
compiled=[relocations.get(vtable+16+i*8) for i in range(358)]
require(all(compiled) and vtable+16+358*8 not in relocations,'Exact owned 358-entry vtable')
candidate=RAW_CACHE
SLIDE=-0x1000000
require(audit['intended_prelink_slide']==SLIDE and audit['raw_sha256']==SPEC['kernelcache_sha256'],
        'Raw audit provenance and intended prelink slide')
require(int(audit['legacy_vptr'],16)==int(audit['raw_legacy_vptr'],16)+SLIDE,
        'Legacy vptr must explicitly be postslide, not the raw original address')
require(audit['legacy_instance_bytes']==0x18a0 and audit['instance_extent']['value']==0x18a0 and
        int(audit['instance_extent']['raw_metaclass'],16)+SLIDE==0xfffffff006b35940,
        'Independent exact original class extent and rebased metaclass identity')
old=candidate.read_bytes();old_image=macho(old)
names={n:v for v,group in exports(old,old_image).items() for n in group}
def read(va,n):
    at=backed_offset(old_image['segments'],va-SLIDE,n,len(old));return old[at:at+n]
bindings={'__ZN25IOMobileFramebufferLegacyC2EPK11OSMetaClass':0xfffffff0057865cc,
          '__ZN25IOMobileFramebufferLegacyD2Ev':0xfffffff005786618,
          '__ZN25IOMobileFramebufferLegacy10gMetaClassE':0xfffffff006b35940,
          '__ZTV25IOMobileFramebufferLegacy':int(audit['legacy_vptr'],16)-16}
owned=[];native=[]
for i,name in enumerate(compiled):
    expected=int(methods[i]['address'],16)
    if name.startswith(('__ZN19NativeLegacyDisplay','__ZNK19NativeLegacyDisplay')):
        owned.append(i);require(i in (0,1,7,14,84,86,87,141,155,184,188,288,290,296,301) or i in pure,'Only qualified own methods and guarded leaves override')
    elif '25IOMobileFramebufferLegacy' in name:
        require(i not in pure,'No unresolved original abstract backend target');bindings[name]=expected
    else:
        require(i<168 and names.get(name)==expected,'Actual inherited native base symbol '+str(i));native.append(i)
require(owned==sorted([0,1,7,14,84,86,87,141,155,184,188,288,290,296,301]+pure),'Exact owned method set')
undefined={n for n,_,k in symbols if k==1 and 'IOMobileFramebufferLegacy' in n}
require(undefined==set(bindings),'All and only actual original-class imports qualified')
# Exact original IOSurface getters, independently observed through the real
# original swap request. These aliases call original code; no object layout
# is substituted and no original method/vtable is patched.
for name,address,field,wide in [
    ('descriptor',0xfffffff004b9ead0,48,True),('width',0xfffffff004b9ebbc,88,True),
    ('height',0xfffffff004b9ebc4,96,True),('stride',0xfffffff004b9ebd4,104,True),
    ('allocation',0xfffffff004b9ebfc,144,True),('format',0xfffffff004b9ebac,128,False),
    ('planes',0xfffffff004b9ebf4,152,False)]:
    expected=(0xf9400000 if wide else 0xb9400000)|((field//(8 if wide else 4))<<10)
    require(read(address,8)==struct.pack('<2I',expected,0xd65f03c0),'Exact original surface getter '+name)
    bindings['_native_legacy_surface_'+name]=address
# The original display-refresh notification sender (self, timestamp, continuous host time, frame interval): it sends the six-word
# vsync message (type 5) to every client entry queued at +5592, the tail queue that selector 72's registration (slot 208) fills at
# +5512 + type*16. The platform subclass that normally calls it on each panel vblank is not part of this port.
require(read(0xfffffff005796720,16)==bytes.fromhex('ff0302d1fd7b07a9fdc30191a0831ff8') and
        read(0xfffffff005796830,4)==bytes.fromhex('08ed4af9') and
        read(0xfffffff00579685c,16)==bytes.fromhex('e2230091c3008052240080521684ff97') and
        read(0xfffffff005795fbc,4)==bytes.fromhex('0ab182d2'),
        'Original vsync sender, its +5592 queue and six-word drop-allowed async send')
bindings['_native_legacy_vsync_notify']=0xfffffff005796720
# Slot 301 fills the six refresh words that setDisplayRefreshProperties publishes as IOMFBDisplayRefresh (minimum interval, its mach
# time, maximum interval, its mach time, step, its mach time; intervals in 32.32 seconds): the generic body fixes the minimum at
# 0x04444444 (1/60 s), and the render server paces its display timer by it.
require(int(methods[301]['address'],16)==0xfffffff00579ea5c and read(0xfffffff00579ea68,8)==bytes.fromhex('888888d28888a0f2') and
        read(0xfffffff00579ec54,4)==bytes.fromhex('08b544f9'),
        'Original slot-301 refresh words with the 1/60 s minimum, called by setDisplayRefreshProperties')
# setDisplayRefreshProperties itself (self): fills the six words through slot 301 and publishes them as IOMFBDisplayRefresh. Nothing in
# the family calls it (the platform subclass does), so without it the render server falls back to its own 1/60 s heartbeat.
require(read(0xfffffff00579ebb8,16)==bytes.fromhex('ff0302d1fd7b07a9fdc30191a0031ff8') and
        read(0xfffffff00579ed54,16)==bytes.fromhex('086540f90173ff90218c0c9100013fd6'),
        'Original setDisplayRefreshProperties publishing IOMFBDisplayRefresh through setProperty')
bindings['_native_legacy_set_refresh_properties']=0xfffffff00579ebb8
# Both protected destructors/constructors must follow the exact original chain.
def branch(pc):
    word=struct.unpack('<I',read(pc,4))[0];require(word&0xfc000000==0x94000000,'Actual protected base call')
    value=word&0x3ffffff;return pc+4*(value-(1<<26) if value&(1<<25) else value)
require(branch(0xfffffff0057865fc)==0xfffffff00577b510 and branch(0xfffffff005786630)==0xfffffff00577b55c,
        'Original protected Legacy C2/D2 really call their original Service bases')
# Actual caller passes only self at slot 288 and tests bit zero of w0.
require(read(0xfffffff005787ef8,16)==bytes.fromhex('080040f9088144f900013fd6e0000037'),
        'Original bool start_hardware() call and result check')
getter=int(methods[249]['address'],16)
for offset,field in [(0x30,5808),(0x58,5812)]:
    require(struct.unpack('<I',read(getter+offset,4))[0]==0xb9400000|((field//4)<<10)|(8<<5)|8,
            'Actual original width/height getter fields')
require(int(methods[295]['address'],16)==0xfffffff005795b88 and
        read(0xfffffff005795b98,16)==bytes.fromhex('e00740f9280080520101001272d3ff97'),
        'Actual original slot-295 passes true to the normal current completion body')
require(read(0xfffffff00578aa7c,24)==bytes.fromhex('080040f9084545f9030080d2e20303aa0400805200013fd6'),
        'Original completion calls optional report slot 337 with null outputs and zero limit')
require(read(0xfffffff005777e9c,16)==bytes.fromhex('080040f908e142f900013fd6c0000036'),
        'Original isMainDisplay dispatch uses only self and tests boolean bit zero')
asm=OUT/'original-bindings.S';asm.write_text(''.join(f'.globl {name}\n.set {name}, {va:#x}\n' for name,va in sorted(bindings.items())))
sdk=run(['xcrun','--sdk','iphoneos','--show-sdk-path'],text=True).strip()
run(['xcrun','clang','-target','arm64-apple-ios17.0','-isysroot',sdk,'-c',asm,'-o',OUT/'original-bindings.o'])
llvm=Path(run(['brew','--prefix','llvm'],text=True).strip())/'bin';late=OUT/'NativeLegacyDisplay.late.o'
run([llvm/'llvm-objcopy','--remove-section=__DATA,__mod_init_func','--globalize-symbol=__GLOBAL__sub_I_NativeLegacyDisplay.cpp',obj,late])
def code(data,info):
    sec=next(s for g in info['segments'] for s in g['sections'] if s['name']=='__text');return data[sec['fileoff']:sec['fileoff']+sec['size']]
require(code(raw,image)==code(late.read_bytes(),macho(late.read_bytes())),'Only owned initializer section registration changes')
source=ROOT/'kits/luming-cpu-display/LegacyDisplayProbe.cpp'
compile_owned(source,OUT/'LegacyDisplayProbe.o')

# CPU-only archive: no HID, KeyStore, GPU, SMMU, WiFi, touch, battery or SoC power objects.
archive=OUT/'libNativeLegacyDisplay.late.a'
archive.unlink(missing_ok=True)
run(['xcrun','ar','rcs',archive,late,OUT/'original-bindings.o',OUT/'LegacyDisplayProbe.o'])
sources=[ROOT/'drivers/GopFramebuffer/NativeLegacyDisplay.cpp',
         ROOT/'drivers/GopFramebuffer/NativeLegacyRequest.h',source,
         ROOT/'kits/luming-cpu-display/build-config.json']
(OUT/'build-report.json').write_text(json.dumps(dict(
    source_sha256={str(p.relative_to(ROOT)):sha(p) for p in sources},
    generated_abi_sha256=sha(OUT/'OriginalLegacyFramebufferABI.h'),
    original_kernelcache_sha256=sha(candidate),
    original_audit_sha256=sha(ROOT/'build/display-analysis/mobile-graphics-legacy-abi.json'),
    compiled_object_sha256=sha(obj),late_object_sha256=sha(late),archive_sha256=sha(archive),
    bindings={n:hex(v) for n,v in bindings.items()},virtual_entries=358,
    owned_entries=owned,inherited_native_entries=native,
    guarded_backend_leaves=[i for i in pure if i not in (213,337)],
    original_instructions_modified=False,driver_initialized=False,
    display_presented=False,desktop=False,cpu_only=True,
    archive_members=[late.name,'original-bindings.o','LegacyDisplayProbe.o'],
    upstream_generator_sha256='93e4bd23912dcbd26f090f7cf1f5b62fcb92a185c8e35dd5e0968deb31ebe777'),indent=2)+'\n')
print('Built CPU-only Legacy archive; compile/ABI audit does not prove runtime presentation')
