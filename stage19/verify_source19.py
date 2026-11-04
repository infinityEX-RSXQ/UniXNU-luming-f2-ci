"""Fail closed on source stackshot API/layout drift before the full CI build."""
from pathlib import Path
import argparse,hashlib,json
HERE=Path(__file__).resolve().parent
def verify(tree):
    pins=json.loads((HERE/'xnu-source-pins.json').read_text())
    for rel,h in pins.items():
        b=(tree/rel).read_bytes().replace(b'\r\n',b'\n')
        assert hashlib.sha256(b).hexdigest()==h,'Stage19 XNU layout/API source drift: '+rel
    return dict(stage=19,xnu_source=str(tree),pins_verified=pins)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--xnu',type=Path);p.add_argument('--core',type=Path);a=p.parse_args()
    if a.xnu:tree=a.xnu
    else:
        assert a.core
        candidates=[x for x in (a.core/'out/feeds').glob('xnu-*') if (x/'osfmk/kern/kcdata.h').is_file()]
        assert len(candidates)==1,('Expected one selected XNU feed',candidates)
        tree=candidates[0]
    print(json.dumps(verify(tree.resolve()),indent=2))
