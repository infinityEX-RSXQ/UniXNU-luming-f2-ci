"""Append source-only observations to the existing stage9 exception diagnostics.

Run on an isolated prepared XNU source or during the existing patch generator.
Preserves all exception/exit/signature/ASLR and panic-selection policy.
"""
from pathlib import Path
import argparse

CAPTURE = '''\t/* CDX11_CAPTURE: independent of exception_log_max_pid. */
\textern void cdx11_capture_exception(int, const char *, int,
\t    uint64_t, uint64_t, unsigned int, unsigned int);
\tcdx11_capture_exception(proc_pid(get_bsdtask_info(task)),
\t    proc_name_address(get_bsdtask_info(task)), exception,
\t    code[0], codeCnt > 1 ? code[1] : 0,
\t    (unsigned int)task->task_shared_region_slide,
\t    (unsigned int)bootarg_disable_aslr);
'''
SUMMARY = '''
#if DEVELOPMENT || DEBUG
\t/* CDX11_FINAL: after the existing coredump/sync, before the existing panic. */
\textern int cdx11_crash_summary(int, const char *, const char *, char *, size_t);
\tchar cdx11_reason[640];
\tif (cdx11_crash_summary(proc_getpid(p), p->p_name, prefix_str,
\t    cdx11_reason, sizeof(cdx11_reason))) {
\t\tprefix_str = cdx11_reason;
\t}
#endif
'''

def exception_instrument(text):
    if '/* CDX11_CAPTURE:' in text:
        assert text.count(CAPTURE) == 1, 'stage11 capture drift'
        return text
    # Both stage9 records must already be present. Insert outside the pid gate,
    # in the same DEVELOPMENT/MACH_BSD scope as bootarg_disable_aslr.
    anchor = '\t/* CDX_ASLR_EXC */\n\textern bool bootarg_disable_aslr;\n'
    assert text.count(anchor) == 1, 'Require the existing stage9 short diagnostics'
    assert '"CDX_ASLR"' in text and '"CDX_EXC"' in text
    return text.replace(anchor, anchor + CAPTURE)

def exit_instrument(text):
    if '/* CDX11_FINAL:' in text:
        assert text.count(SUMMARY) == 1, 'stage11 summary drift'
        return text
    start = text.index('proc_handle_critical_exit(proc_t p, int rv)\n{')
    end = text.index('\nvoid\nproc_prepareexit(', start)
    block = text[start:end]
    anchor = '\tsync(p, (void *)NULL, (int *)NULL);\n'
    assert block.count(anchor) == 1 and block.count('panic_with_options(') == 2
    assert 'proc_crash_coredump(p);' in block and 'if (!proc_should_trigger_panic(p, rv))' in block
    return text[:start] + block.replace(anchor, anchor + SUMMARY) + text[end:]

def apply(root):
    targets = [(root/'osfmk/kern/exception.c', exception_instrument),
               (root/'bsd/kern/kern_exit.c', exit_instrument)]
    changes = [(p, f(p.read_text(encoding='utf-8'))) for p,f in targets]
    for p, contents in changes:
        p.write_text(contents, encoding='utf-8', newline='\n')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('tree', type=Path)
    args = parser.parse_args()
    apply(args.tree)
    print('CDX11 source instrumentation applied; full macOS build/runtime not yet verified.')
