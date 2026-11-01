from pathlib import Path
import argparse,json,sys
ROOT=Path('D:/civitoip20/lumingios-cdx')
sys.path.insert(0,str(ROOT/'sources'))
from qualify_stage10_kernel import qualify,inspect
def check(kernel,baseline,sha,build_report,expected):
    result=qualify(kernel,baseline,sha);info=inspect(kernel)
    for symbol in ['_cdx11_capture_exception','_cdx11_crash_summary','_cdx12_capture_mode','_cdx12_append_mode_summary','_cdx12_refresh_observed']:
        assert symbol in info['defined'],'Missing defined symbol '+symbol
    data=kernel.read_bytes()
    for token in [b'CDX12 mode got=%u',b'CDX12 scaleBits=%llx rateBits=%llx',b'luming-display-refresh-publish']:
        assert token in data,'Missing stage12 format/boot argument'
    sources=json.loads(build_report.read_text(encoding='utf-8'))['source_sha256']
    after=json.loads(expected.read_text(encoding='utf-8'))['after']
    for target,src in [('drivers/GopFramebuffer/NativeLegacyDisplay.cpp','stage10/stage10-runtime/NativeLegacyDisplay.cpp'),
                       ('kits/luming-cpu-display/LegacyDisplayProbe.cpp','stage10/stage10-runtime/LegacyDisplayProbe.cpp')]:
        assert sources[target]==after[src],'Compiled source hash drift: '+target
    result.update(stage=12,source_hashes_checked=True,runtime_verified=False)
    return result
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--kernel',type=Path,required=True)
    p.add_argument('--baseline',type=Path,default=ROOT/'builds/aslr-short-diag-20261101/kernel.macho')
    p.add_argument('--sha256',required=True);p.add_argument('--build-report',type=Path,required=True)
    p.add_argument('--expected',type=Path,default=Path(__file__).with_name('integration-validation.json'))
    p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
    r=check(a.kernel,a.baseline,a.sha256,a.build_report,a.expected)
    a.output.write_text(json.dumps(r,indent=2),encoding='utf-8');print(json.dumps(r))
