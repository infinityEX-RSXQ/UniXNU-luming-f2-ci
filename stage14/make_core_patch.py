"""Build a minimal source patch from the pinned XNU reference; never edits it."""
from pathlib import Path
import difflib,hashlib,json
HERE=Path(__file__).resolve().parent
XNU=Path('D:/civitoip20/lumingios-cdx/builds/aslr-short-diag-20261101/xnu')
CONSOLE_DECL=r'''
/* CDX14: opt-in console ownership; panic remains able to reacquire. */
static unsigned cdx14_vt_owned, cdx14_vt_blocked, cdx14_vt_drawn;
static boolean_t
cdx14_vt_should_block(void)
{
	return __atomic_load_n(&cdx14_vt_owned, __ATOMIC_ACQUIRE) && !panic_active();
}
void cdx14_console_commit(void);
void cdx14_console_snapshot(unsigned *out);
void
cdx14_console_commit(void)
{
	VCPUTC_LOCK_LOCK();
	__atomic_store_n(&cdx14_vt_owned, 1, __ATOMIC_RELEASE);
	gc_enabled = FALSE;
	if (!console_is_serial()) disableConsoleOutput = TRUE;
	VCPUTC_LOCK_UNLOCK();
}
void
cdx14_console_snapshot(unsigned *out)
{
	if (!out) return;
	out[0] = __atomic_load_n(&cdx14_vt_owned, __ATOMIC_ACQUIRE);
	out[1] = gc_enabled;
	out[2] = disableConsoleOutput;
	out[3] = __atomic_load_n(&cdx14_vt_blocked, __ATOMIC_RELAXED);
	out[4] = __atomic_load_n(&cdx14_vt_drawn, __ATOMIC_RELAXED);
}
'''.replace('\\t','\t')
DAEMON_DECL=r'''
/* CDX14: observe failures; do not change exit/corpse/watchdog policy. */
struct cdx14_daemon_record { unsigned count, pid, ns; uint64_t code; };
static struct cdx14_daemon_record cdx14_daemons[4];
static const char *const cdx14_names[4] = {"SpringBoard", "backboardd", "watchdogd", "liveactivitiesd"};
size_t cdx14_daemon_summary(char *out, size_t size);
static void
cdx14_observe_exit(proc_t p, int rv)
{
	for (unsigned i = 0; i < 4; ++i) {
		if (strcmp(p->p_comm, cdx14_names[i])) continue;
		unsigned n = __atomic_add_fetch(&cdx14_daemons[i].count, 1, __ATOMIC_RELAXED);
		unsigned ns = PROC_HAS_EXITREASON(p) ? p->p_exit_reason->osr_namespace : 0;
		uint64_t code = PROC_HAS_EXITREASON(p) ? p->p_exit_reason->osr_code : 0;
		__atomic_store_n(&cdx14_daemons[i].pid, proc_getpid(p), __ATOMIC_RELAXED);
		__atomic_store_n(&cdx14_daemons[i].ns, ns, __ATOMIC_RELAXED);
		__atomic_store_n(&cdx14_daemons[i].code, code, __ATOMIC_RELAXED);
		if (n <= 4) printf("CDX14 exit %.16s p=%d rv=%x ns=%u code=%llx n=%u\n",
		    p->p_comm, proc_getpid(p), rv, ns, (unsigned long long)code, n);
		break;
	}
}
size_t
cdx14_daemon_summary(char *out, size_t size)
{
	if (!out || !size) return 0;
	size_t used = 0; out[0] = 0;
	for (unsigned i = 0; i < 4 && used < size - 1; ++i) {
		int n = snprintf(out + used, size - used, "%.16s n=%u p=%u ns=%u code=%llx\n", cdx14_names[i],
		    __atomic_load_n(&cdx14_daemons[i].count, __ATOMIC_RELAXED),
		    __atomic_load_n(&cdx14_daemons[i].pid, __ATOMIC_RELAXED),
		    __atomic_load_n(&cdx14_daemons[i].ns, __ATOMIC_RELAXED),
		    (unsigned long long)__atomic_load_n(&cdx14_daemons[i].code, __ATOMIC_RELAXED));
		if (n < 0) break;
		used += (size_t)n < size - used ? (size_t)n : size - used - 1;
	}
	return used;
}
'''.replace('\\t','\t')
EXCEPTION_DECL=r'''
struct cdx14_exception_record { unsigned count, type; uint64_t c0, c1; };
static struct cdx14_exception_record cdx14_exceptions[4];
void cdx14_daemon_exception(const char *, unsigned, uint64_t, uint64_t);
size_t cdx14_exception_summary(char *, size_t);
void
cdx14_daemon_exception(const char *name, unsigned e, uint64_t c0, uint64_t c1)
{
	if (!name) return;
	for (unsigned i = 0; i < 4; ++i) {
		if (strcmp(name, cdx14_names[i])) continue;
		unsigned n = __atomic_add_fetch(&cdx14_exceptions[i].count, 1, __ATOMIC_RELAXED);
		__atomic_store_n(&cdx14_exceptions[i].type, e, __ATOMIC_RELAXED);
		__atomic_store_n(&cdx14_exceptions[i].c0, c0, __ATOMIC_RELAXED);
		__atomic_store_n(&cdx14_exceptions[i].c1, c1, __ATOMIC_RELAXED);
		if (n <= 4) printf("CDX14 exc %.16s e=%u c0=%llx c1=%llx\n", name, e,
		    (unsigned long long)c0, (unsigned long long)c1);
		break;
	}
}
size_t
cdx14_exception_summary(char *out, size_t size)
{
	if (!out || !size) return 0;
	size_t used = 0; out[0] = 0;
	for (unsigned i = 0; i < 4 && used < size - 1; ++i) {
		int n = snprintf(out + used, size - used, "%.16s exc=%u e=%u c0=%llx c1=%llx\n", cdx14_names[i],
		    __atomic_load_n(&cdx14_exceptions[i].count, __ATOMIC_RELAXED),
		    __atomic_load_n(&cdx14_exceptions[i].type, __ATOMIC_RELAXED),
		    (unsigned long long)__atomic_load_n(&cdx14_exceptions[i].c0, __ATOMIC_RELAXED),
		    (unsigned long long)__atomic_load_n(&cdx14_exceptions[i].c1, __ATOMIC_RELAXED));
		if (n < 0) break;
		used += (size_t)n < size - used ? (size_t)n : size - used - 1;
	}
	return used;
}
'''
def once(text,old,new):
    assert text.count(old)==1,repr(old);return text.replace(old,new)
def console(text):
    # VCPUTC_LOCK macros must already be defined at insertion location.
    text=once(text,'static void\ngc_enable( boolean_t enable )',CONSOLE_DECL+'\nstatic void\ngc_enable( boolean_t enable )')
    text=once(text,'gc_enable( boolean_t enable )\n{','gc_enable( boolean_t enable )\n{\n\tif (enable && cdx14_vt_should_block()) {\n\t\t__atomic_add_fetch(&cdx14_vt_blocked, 1, __ATOMIC_RELAXED);\n\t\treturn;\n\t}')
    text=once(text,'\tif (gc_initialized && gc_enabled) {','\tif (cdx14_vt_should_block()) return;\n\tif (gc_initialized && gc_enabled) {')
    text=once(text,'\t\tif (gc_enabled) {\n\t\t\tgc_hide_cursor', '\t\tif (gc_enabled && !cdx14_vt_should_block()) {\n\t\t\tif (__atomic_load_n(&cdx14_vt_owned, __ATOMIC_RELAXED))\n\t\t\t\t__atomic_add_fetch(&cdx14_vt_drawn, 1, __ATOMIC_RELAXED);\n\t\t\tgc_hide_cursor')
    text=once(text,'\tuint32_t delay;\n\n\tif (boot_vinfo)', '''\tuint32_t delay;

\tif (cdx14_vt_should_block() && (op == kPEAcquireScreen ||
\t    op == kPEEnableScreen || op == kPETextScreen ||
\t    op == kPETextMode || op == kPEGraphicsMode)) {
\t\t__atomic_add_fetch(&cdx14_vt_blocked, 1, __ATOMIC_RELAXED);
\t\treturn;
\t}
\tif (boot_vinfo)''')
    return text
def exits(text):
    text=once(text,'void\nproc_prepareexit(proc_t p, int rv, boolean_t perf_notify)',DAEMON_DECL+EXCEPTION_DECL+'\nvoid\nproc_prepareexit(proc_t p, int rv, boolean_t perf_notify)')
    return once(text,'\ttask_t task = proc_task(p);\n\n\n\tif (p->p_crash_behavior', '\ttask_t task = proc_task(p);\n\n\tcdx14_observe_exit(p, rv);\n\n\tif (p->p_crash_behavior')
def build(root=XNU):
    patches=[];checks={}
    for rel,transform in [('osfmk/console/video_console.c',console),('bsd/kern/kern_exit.c',exits)]:
        old=(root/rel).read_text(encoding='utf-8');new=transform(old)
        checks[rel]={'reference_sha256':hashlib.sha256(old.encode()).hexdigest()}
        patches.append(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='a/'+rel,tofile='b/'+rel,n=3)))
    (HERE/'zzzzzzzzzzzzzzzzzzzzzz-cdx14-observation.patch').write_text(''.join(patches),encoding='utf-8',newline='\n')
    (HERE/'core-patch-reference.json').write_text(json.dumps(checks,indent=2),encoding='utf-8')
if __name__=='__main__':build()
