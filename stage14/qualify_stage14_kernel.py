from pathlib import Path
import argparse,json,sys
ROOT=Path('D:/civitoip20/lumingios-cdx')
sys.path.insert(0,str(ROOT/'sources'))
from qualify_stage10_kernel import qualify,inspect
REQUIRED=['_cdx14_console_commit','_cdx14_console_snapshot','_cdx14_frame_begin','_cdx14_frame_end',
    '_cdx14_frame_gap','_cdx14_after_release','_cdx14_daemon_exception','_cdx14_daemon_summary','_cdx14_exception_summary',
    '_cdx13_publish_ui_scale','_cdx13_capture_validity','_cdx13_append_mode_summary']
def check(kernel,baseline,sha,report,expected):
    result=qualify(kernel,baseline,sha);info=inspect(kernel)
    for name in REQUIRED:assert name in info['defined'],'Missing Stage14 definition: '+name
    raw=kernel.read_bytes()
    for token in [b'luming-display-vt-latch',b'luming-display-frame-probe',b'luming-display-snapshot',
        b'CDX14FrameSamples',b'CDX14 diagnostic snapshot (intentional)',b'CDX14 exc %.16s']:
        assert token in raw,'Missing Stage14 marker: '+repr(token)
    r=json.loads(report.read_text(encoding='utf-8'));after=json.loads(expected.read_text(encoding='utf-8'))['after']
    for target,source in [('drivers/GopFramebuffer/NativeLegacyDisplay.cpp','stage10/stage10-runtime/NativeLegacyDisplay.cpp'),
        ('kits/luming-cpu-display/LegacyDisplayProbe.cpp','stage10/stage10-runtime/LegacyDisplayProbe.cpp')]:
        assert r['source_sha256'][target]==after[source],'Stage14 compiled source drift: '+target
    assert r['generated_abi_sha256']=='8465dbcff188e88e66fdbe9a5e24b102c093b06d17f879f7a55fa3d1c58f8016'
    assert r['original_kernelcache_sha256']=='f18b4df865405f2a287b84977d7aca745e056d656d9fc9df1662970ce2969de7'
    assert r['virtual_entries']==358
    result.update(stage=14,stage14_definitions=True,materialized_source_hashes_checked=True,runtime_verified=False)
    return result
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--kernel',type=Path,required=True);p.add_argument('--sha256',required=True)
    p.add_argument('--baseline',type=Path,default=ROOT/'builds/aslr-short-diag-20261101/kernel.macho')
    p.add_argument('--build-report',type=Path,required=True)
    p.add_argument('--expected',type=Path,default=Path(__file__).with_name('integration-validation.json'))
    p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
    r=check(a.kernel,a.baseline,a.sha256,a.build_report,a.expected)
    a.output.write_text(json.dumps(r,indent=2),encoding='utf-8');print(json.dumps(r))
