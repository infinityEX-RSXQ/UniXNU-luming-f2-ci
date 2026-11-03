"""Check integration in an isolated D: fixture; never edit the accepted CI tree."""
from pathlib import Path
import ast,hashlib,json,re,shutil,sys,time
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
sys.path.insert(0,str(HERE));from integrate_ci19 import integrate
repo=ROOT/'builds/stage18-ci-work/repo'
fixture=Path('D:/Codex/tmp')/('stage19-ci-'+str(time.time_ns()));fixture.mkdir(parents=True)
pins=json.loads((HERE/'ci-input-pins.json').read_text())
for rel in pins:
    dst=fixture/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(repo/rel,dst)
assert not integrate(fixture)['applied'];report=integrate(fixture,True)
workflow=(fixture/'.github/workflows/macos.yml').read_text(encoding='utf-8')
embedded=[]
for match in re.finditer(r'^          python3 - <<\'PY\'\n(.*?)^          PY$',workflow,re.M|re.S):
    source='\n'.join(line[10:] if line.startswith('          ') else line for line in match.group(1).splitlines())
    ast.parse(source);embedded.append(source)
assert len(embedded)>=10,('Missing inline Python blocks',len(embedded))
for path in fixture.rglob('*.py'):ast.parse(path.read_text(encoding='utf-8'))
probe=(HERE/'runtime/LegacyDisplayProbe.cpp').read_text()
assert probe.count('thread_call_allocate(cdx14_snapshot_callback')==1
assert probe.count('cdx15_snapshot(reason,sizeof(reason),quiet);')==1
assert probe.count('cdx15_snapshot(stackReason,sizeof(stackReason),quiet19);')==1
positions=[probe.index(x) for x in ['if(cdx19_capture_next())','bool quiet19=cdx14p1_quiesce();',
    'cdx15_snapshot(stackReason,sizeof(stackReason),quiet19);','unsigned reclaimed19=',
    'panic("CDX19 stackshot (intentional)']]
assert positions==sorted(positions)
assert workflow.index('verify_source19.py')<workflow.index('install_stage19.py')<workflow.index('ci_check19.py')
assert workflow.index('ci_check18.py')<workflow.index('ci_check19.py')
report.update(passed=True,fixture=str(fixture),embedded_python_checked=len(embedded),
              callback_capture_before_quiesce=True,full_kernel_compiled=False,runtime_verified=False)
(HERE/'ci-preflight.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
