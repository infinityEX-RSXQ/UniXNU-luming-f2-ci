from pathlib import Path
import subprocess,json
R=Path(__file__).resolve().parent
T=Path('D:/civitoip20/.tools/llvm/clang+llvm-23.1.4-x86_64-pc-windows-msvc/bin')
def run(cmd):
    p=subprocess.run([str(x) for x in cmd],capture_output=True,text=True)
    return {'argv':[str(x) for x in cmd],'exit_code':p.returncode,'output':p.stdout+p.stderr}
records=[]
for stem in ['duplicate_a','duplicate_b','declaration_a']:
    p=run([T/'clang++.exe','-target','arm64-apple-ios17.0','-c',R/(stem+'.cpp'),'-o',R/(stem+'.o')]);records.append(p);assert p['exit_code']==0,p
base=[T/'ld64.lld.exe','-dylib','-arch','arm64','-platform_version','ios','17.0','17.0']
bad=run([*base,R/'duplicate_a.o',R/'duplicate_b.o','-o',R/'duplicate.dylib']);records.append(bad)
assert bad['exit_code']!=0 and 'duplicate symbol' in bad['output']
good=run([*base,R/'declaration_a.o',R/'duplicate_b.o','-o',R/'declaration.dylib']);records.append(good)
assert good['exit_code']==0,good
result={'duplicate_c_linkage_definitions_reproduce_link_failure':True,'extern_storage_declaration_fix_links':True,'scope':'Minimal two-object proof only, not full native kernel compile','records':records}
(R/'duplicate-link-proof.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result,indent=2))
