from pathlib import Path
import argparse,json,sys
ROOT=Path('D:/civitoip20/lumingios-cdx');sys.path.insert(0,str(ROOT/'sources'))
from qualify_stage10_kernel import qualify,inspect
def check(kernel,baseline,sha,report,expected):
    r=qualify(kernel,baseline,sha);info=inspect(kernel)
    for name in ['_cdx14p1_scanout_enter','_cdx14p1_scanout_leave','_cdx14p1_console_reclaim',
        '_cdx14p1_schedule_snapshot','_cdx14_frame_begin','_cdx14_frame_end','_cdx14_daemon_summary',
        '_cdx14_exception_summary','_cdx13_publish_ui_scale']:
        assert name in info['defined'],'Missing Stage14.1 definition: '+name
    raw=kernel.read_bytes()
    assert b'CDX14.1 diagnostic snapshot (intentional)' in raw
    assert b'quiet=%u active=%u reclaim=%u before=%u/%u/%u' in raw
    source=json.loads(report.read_text(encoding='utf-8'));after=json.loads(expected.read_text(encoding='utf-8'))['after']
    for target,original in [('drivers/GopFramebuffer/NativeLegacyDisplay.cpp','stage10/stage10-runtime/NativeLegacyDisplay.cpp'),
        ('kits/luming-cpu-display/LegacyDisplayProbe.cpp','stage10/stage10-runtime/LegacyDisplayProbe.cpp')]:
        assert source['source_sha256'][target]==after[original],target+' source drift'
    assert source['generated_abi_sha256']=='8465dbcff188e88e66fdbe9a5e24b102c093b06d17f879f7a55fa3d1c58f8016'
    assert source['virtual_entries']==358
    r.update(stage='14.1',materialized_source_hashes_checked=True,runtime_verified=False)
    return r
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--kernel',type=Path,required=True);p.add_argument('--sha256',required=True)
    p.add_argument('--build-report',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--baseline',type=Path,default=ROOT/'builds/aslr-short-diag-20261101/kernel.macho')
    p.add_argument('--expected',type=Path,default=Path(__file__).with_name('integration-validation.json'))
    a=p.parse_args();assert not a.output.exists()
    r=check(a.kernel,a.baseline,a.sha256,a.build_report,a.expected)
    a.output.write_text(json.dumps(r,indent=2),encoding='utf-8');print(json.dumps(r))
