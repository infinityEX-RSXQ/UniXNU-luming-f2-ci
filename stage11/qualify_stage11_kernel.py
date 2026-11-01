"""Require the source-built snapshot, in addition to stage10's existing guards."""
from pathlib import Path
import argparse, json, sys
ROOT=Path('D:/civitoip20/lumingios-cdx')
sys.path.insert(0,str(ROOT/'sources'))
from qualify_stage10_kernel import qualify, inspect

def check(kernel,baseline,sha,build_report):
    result=qualify(kernel,baseline,sha)
    info=inspect(kernel)
    for name in ('_cdx11_capture_exception','_cdx11_crash_summary'):
        assert name in info['defined'], 'Missing defined stage11 function '+name
    data=kernel.read_bytes()
    for token in (b'CDX11 pid=%d match=%u',b'CDX11 first e=%d',b'CDX11 last e=%d',b'CDX11 val=%u'):
        assert token in data, 'Missing compact diagnostic format'
    sources=json.loads(build_report.read_text(encoding='utf-8'))['source_sha256']
    assert sources['drivers/GopFramebuffer/NativeLegacyDisplay.cpp']=='0ab790c93a086aad4639529126ec65b7228a7bb2fb4b921ebf4b9e590fe990a1'
    assert sources['kits/luming-cpu-display/LegacyDisplayProbe.cpp']=='5c1ff177f2ddd833bf2df385d35700a19bd2a92faf987dfbdb7e89acd4f38d04'
    result.update(stage=11,diagnostic_symbols_defined=True,diagnostic_source_hash_qualified=True,
        runtime_verified=False)
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--kernel',type=Path,required=True)
    p.add_argument('--baseline',type=Path,default=ROOT/'builds/aslr-short-diag-20261101/kernel.macho')
    p.add_argument('--sha256',required=True)
    p.add_argument('--build-report',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    assert not a.output.exists(), 'Refuse overwrite'
    r=check(a.kernel,a.baseline,a.sha256,a.build_report)
    a.output.write_text(json.dumps(r,indent=2),encoding='utf-8')
    print(json.dumps(r,indent=2))
