"""Extend the accepted Stage18 r2 CI gates with a checked Stage19 source chain.

No upload, dispatch, device operation or credentials. Default: dry run.
"""
from pathlib import Path
import argparse,hashlib,json
HERE=Path(__file__).resolve().parent
def sha(b):return hashlib.sha256(b).hexdigest()
def once(t,a,b):
    assert t.count(a)==1,(a,t.count(a));return t.replace(a,b)
def integrate(repo,apply=False):
    pins=json.loads((HERE/'ci-input-pins.json').read_text());before={}
    for rel,h in pins.items():
        b=(repo/rel).read_bytes().replace(b'\r\n',b'\n');assert sha(b)==h,'CI input drift: '+rel;before[rel]=b
    rel='.github/workflows/macos.yml';t=before[rel].decode()
    a='''          python3 device/stage18/install_stage18.py --device device --apply \\
            | tee ci-artifacts/stage18-install-report.json'''
    t=once(t,a,a+'''
          python3 device/stage19/verify_source19.py --core unixnu \\
            | tee ci-artifacts/stage19-source-check.json
          python3 device/stage19/install_stage19.py --device device --apply \\
            | tee ci-artifacts/stage19-install-report.json''')
    # Each earlier inline gate follows every actual installation transition;
    # preserve all its original ABI/byte/marker tests.
    a="              materialized = stage18['after']"
    count=t.count(a);assert count==4,('Expected four existing chain gates',count)
    t=t.replace(a,a+'''
          if Path('ci-artifacts/stage19-install-report.json').is_file():
              stage19 = json.loads(Path('ci-artifacts/stage19-install-report.json').read_text())
              for rel in stage19['before']:
                  if stage19['before'][rel] != materialized[rel]:
                      raise SystemExit('stage18 -> stage19 source chain broken: ' + rel)
              materialized = stage19['after']''')
    a='          python3 device/stage18/ci_check18.py'
    t=once(t,a,a+'\n          python3 device/stage19/ci_check19.py')
    a="                       'stage18-install-report.json', 'stage18-kernel-check.json'):"
    t=once(t,a,"                       'stage18-install-report.json', 'stage18-kernel-check.json',\n                       'stage19-install-report.json', 'stage19-source-check.json', 'stage19-kernel-check.json'):")
    changes={rel:t.encode()}
    # The two standalone old regression scripts already validate 16->17->18.
    # Extend their final expected map after validating 18->19; no older tests removed.
    rel='stage17/ci_regression16.py';t=before[rel].decode();a="after18=final18['after']"
    t=once(t,a,a+'''
final19=json.loads(Path('ci-artifacts/stage19-install-report.json').read_text())
for rel in final19['before']:assert final19['before'][rel]==after18[rel]
after18=final19['after']''');changes[rel]=t.encode()
    rel='stage17/ci_check17.py';t=before[rel].decode()
    a="for a,b in [('kits/luming-cpu-display/LegacyDisplayProbe.cpp','LegacyDisplayProbe.cpp'),('drivers/GopFramebuffer/NativeLegacyDisplay.cpp','NativeLegacyDisplay.cpp')]:"
    t=once(t,a,"""final19=json.loads(Path('ci-artifacts/stage19-install-report.json').read_text())
for rel in final19['before']:assert final19['before'][rel]==final18['after'][rel]
"""+a)
    t=once(t,"report['source_sha256'][a]==final18['after']", "report['source_sha256'][a]==final19['after']");changes[rel]=t.encode()
    rel='stage18/ci_check18.py';t=before[rel].decode()
    a="for materialized,template in [('drivers/GopFramebuffer/NativeLegacyDisplay.cpp','stage10/stage10-runtime/NativeLegacyDisplay.cpp'),('kits/luming-cpu-display/LegacyDisplayProbe.cpp','stage10/stage10-runtime/LegacyDisplayProbe.cpp')]:"
    t=once(t,a,"""final19=json.loads(Path('ci-artifacts/stage19-install-report.json').read_text())
for rel in final19['before']:assert final19['before'][rel]==installed['after'][rel]
"""+a)
    t=once(t,"report['source_sha256'][materialized]==installed['after'][template]", "report['source_sha256'][materialized]==final19['after'][template]")
    t=once(t,"for rel in installed['after']:assert hashlib.sha256((Path('device')/rel).read_bytes()).hexdigest()==installed['after'][rel]",
                  "for rel in final19['after']:assert hashlib.sha256((Path('device')/rel).read_bytes()).hexdigest()==final19['after'][rel]")
    changes[rel]=t.encode()
    for rel,b in changes.items():
        if rel.endswith('.py'):compile(b,rel,'exec')
    result=dict(stage=19,before={p:sha(b) for p,b in before.items()},after={p:sha(b) for p,b in changes.items()},
        inline_chain_gates_extended=count,prior_gates_retained=True,applied=apply)
    if apply:
        for rel,b in changes.items():(repo/rel).write_bytes(b)
    return result
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--repo',type=Path,required=True);p.add_argument('--apply',action='store_true');a=p.parse_args()
    print(json.dumps(integrate(a.repo.resolve(),a.apply),indent=2))
