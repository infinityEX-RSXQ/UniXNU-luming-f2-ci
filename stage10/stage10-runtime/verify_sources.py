"""Bounded source contract check. Not a C++ compile, ABI proof or device test."""
from pathlib import Path
import hashlib,json,re
R=Path(__file__).resolve().parent
b=(R/'NativeLegacyDisplay.cpp').read_text(encoding='utf-8')
p=(R/'LegacyDisplayProbe.cpp').read_text(encoding='utf-8')
imports=set()
for group in re.findall(r'extern "C"\s+(?:__attribute__\(\(.*?\)\)\s*)?([^;]+);',b,re.S):
    imports.update(re.findall(r'\b(native_legacy_\w+)\s*\(',group))
definition=r'(?m)^\s*(?:__attribute__\(\(.*?\)\)\s*)?(?:(?:extern "C"|static|inline)\s+)*(?:void|bool|unsigned|uint64_t|IOService\s*\*)\s*(native_legacy_\w+)\s*\([^;{}]*\)\s*\{'
defined=set(re.findall(definition,p))
defined.update(re.findall(definition,b))
aliases={
    'native_legacy_surface_descriptor','native_legacy_surface_width','native_legacy_surface_height',
    'native_legacy_surface_stride','native_legacy_surface_allocation','native_legacy_surface_format',
    'native_legacy_surface_planes','native_legacy_vsync_notify','native_legacy_set_refresh_properties'}
unresolved=imports-defined-aliases
assert not unresolved,unresolved
for forbidden in ['sheng_cpufreq_probe','sheng_gpu_power_probe','native_touch_probe','sheng_wifi_probe',
    'sheng_adsp_probe','sheng_battery_probe','sheng_audio_probe','sheng_buttons_probe',
    'sheng_backlight_probe','sheng_dpu_probe','native_keystore_probe','native_hid_input_probe',
    'native_gop_presenter','native_gop_gpu_offer','interpose(']:
    assert forbidden not in p,forbidden
assert 'v.v_display<=1' in p and 'primary=video.v_display==1' not in b
assert 'primary=valid;' in b
assert 'return format==0x42475241 && !planes;' in b
assert 'PE_initialize_console(nullptr,kPEReleaseScreen)' in p
assert 'weak_import' not in p
assert 'boot_progress_prepare_scanout' not in p
assert 'boot_progress_cancel_scanout' not in p
assert 'extern "C" {extern volatile uint64_t native_legacy_early_retires,native_legacy_early_failures;}' in b
assert p.count('volatile uint64_t native_legacy_early_retires,native_legacy_early_failures;')==1
assert p.count('native_legacy_display_static_init();')==1
assert 'native_gop_presenter_static_init' not in p
for hook in ['native_legacy_display_probe','native_legacy_display_late_probe']:
    assert hook in defined
arg_sets={}
for filename,presentation in [('args-registration.txt',False),('args-cpu-present.txt',True)]:
    tokens=(R/filename).read_text(encoding='utf-8').split()
    values=dict(t.split('=',1) for t in tokens)
    assert len(values)==len(tokens),filename
    assert values=={
        'offline-mobile-graphics-load':'1','offline-legacy-register':'1','offline-legacy-phase':'4',
        'offline-legacy-gop':'1','offline-legacy-pm':str(int(presentation)),
        'offline-legacy-validate':str(int(presentation)),'offline-legacy-transfer':str(int(presentation)),
        'offline-legacy-retire':str(int(presentation)),'offline-legacy-cpu-present':str(int(presentation)),
        'sheng-vsync':'60' if presentation else '0','luming-display-console-handoff':str(int(presentation))},filename
    arg_sets[filename]=values
report={
    'backend_hooks':sorted(imports),'source_defined_hooks':sorted(defined),
    'required_original_aliases':sorted(aliases),'unresolved_custom_backend_hooks':sorted(unresolved),
    'guarded_leaves':[int(n) for n in re.findall(r'^\s*LEAF\((\d+)\)',b,re.M)],
    'cpu_only_plain_bgra':True,'preserves_text_boot_console_mode':True,
    'no_undefined_optional_scanout_hooks':True,
    'retirement_counters_have_one_definition':True,
    'argument_sets':arg_sets,
    'sources':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in R.iterdir() if p.is_file() and p.suffix in ('.cpp','.h')},
    'macos_compile_verified':False,'prelink_verified':False,'hardware_tested':False,
    'scope':'Source-level custom-hook completeness and scope checks only. Generated ABI and aliases require exact original-code audits and macOS compilation.'}
(R/'source-contract.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report))
