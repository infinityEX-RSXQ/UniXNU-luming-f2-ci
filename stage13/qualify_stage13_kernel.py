from pathlib import Path
import argparse,json,sys
ROOT=Path('D:/civitoip20/lumingios-cdx')
sys.path.insert(0,str(ROOT/'sources'))
from qualify_stage10_kernel import qualify,inspect
def check(kernel,baseline,sha,build_report,expected):
    result=qualify(kernel,baseline,sha);info=inspect(kernel)
    for name in ['_cdx11_capture_exception','_cdx11_crash_summary','_cdx12_capture_mode',
                 '_cdx13_publish_ui_scale','_cdx13_capture_validity','_cdx13_append_mode_summary']:
        assert name in info['defined'],'Missing stage13 definition: '+name
    raw=kernel.read_bytes()
    for token in [b'luming-display-ui-scale',b'CDX13 w=%llu h=%llu pref=%llu',b'CDX13 ui=%u read=%u rc=%u writes=%u']:
        assert token in raw,'Missing stage13 marker: '+str(token)
    report=json.loads(build_report.read_text(encoding='utf-8'))
    after=json.loads(expected.read_text(encoding='utf-8'))['after']
    for target,source in [('drivers/GopFramebuffer/NativeLegacyDisplay.cpp','stage10/stage10-runtime/NativeLegacyDisplay.cpp'),
                          ('kits/luming-cpu-display/LegacyDisplayProbe.cpp','stage10/stage10-runtime/LegacyDisplayProbe.cpp')]:
        assert report['source_sha256'][target]==after[source],'Materialized input source drift: '+target
    assert report['generated_abi_sha256']=='8465dbcff188e88e66fdbe9a5e24b102c093b06d17f879f7a55fa3d1c58f8016','Legacy ABI drift'
    assert report['original_kernelcache_sha256']=='f18b4df865405f2a287b84977d7aca745e056d656d9fc9df1662970ce2969de7'
    assert report['original_instructions_modified']==False and report['virtual_entries']==358
    result.update(stage=13,materialized_source_hashes_checked=True,unchanged_legacy_abi=True,runtime_verified=False)
    return result
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--kernel',type=Path,required=True)
    p.add_argument('--baseline',type=Path,default=ROOT/'builds/aslr-short-diag-20261101/kernel.macho')
    p.add_argument('--sha256',required=True);p.add_argument('--build-report',type=Path,required=True)
    p.add_argument('--expected',type=Path,default=Path(__file__).with_name('integration-validation.json'))
    p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
    r=check(a.kernel,a.baseline,a.sha256,a.build_report,a.expected)
    a.output.write_text(json.dumps(r,indent=2),encoding='utf-8');print(json.dumps(r))
