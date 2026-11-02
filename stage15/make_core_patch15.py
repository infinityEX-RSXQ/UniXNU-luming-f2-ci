from pathlib import Path
import difflib,hashlib,json
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
XNU=ROOT/'builds/aslr-short-diag-20261101/xnu'
DAEMON=r'''
/* CDX15 compact read-only view of the existing Stage14 observations. */
size_t cdx15_daemon_summary(char *out, size_t size);
size_t
cdx15_daemon_summary(char *out, size_t size)
{
    static const char *const names[4] = {"SB", "BB", "WD", "LA"};
    if (!out || !size) return 0;
    size_t used = 0; out[0] = 0;
    for (unsigned i = 0; i < 4 && used < size - 1; ++i) {
        unsigned n = __atomic_load_n(&cdx14_daemons[i].count, __ATOMIC_RELAXED);
        unsigned e = __atomic_load_n(&cdx14_exceptions[i].type, __ATOMIC_RELAXED);
        uint64_t pc = __atomic_load_n(&cdx14_exceptions[i].c1, __ATOMIC_RELAXED);
        unsigned ns = __atomic_load_n(&cdx14_daemons[i].ns, __ATOMIC_RELAXED);
        uint64_t code = __atomic_load_n(&cdx14_daemons[i].code, __ATOMIC_RELAXED);
        int got = snprintf(out + used, size - used, "%s n=%u ns=%u c=%llx e=%u pc=%llx\n",
            names[i], n, ns, (unsigned long long)code, e, (unsigned long long)pc);
        if (got < 0) break;
        used += (size_t)got < size - used ? (size_t)got : size - used - 1;
    }
    return used;
}
'''
def once(t,a,b):
    assert t.count(a)==1,repr(a);return t.replace(a,b)
def ipc(text):
    anchor='IOReturn\nIOUserClient::callExternalMethod(uint32_t selector, IOExternalMethodArguments * args)'
    decl='extern "C" uint64_t cdx15_ipc_begin(void *, uint32_t);\nextern "C" void cdx15_ipc_end(uint64_t, uint32_t);\n\n'
    text=once(text,anchor,decl+anchor)
    start=text.index(anchor);end=text.index('\n}\n',start)+3;body=text[start:end]
    body=once(body,'\tIOReturn ret;','\tIOReturn ret;\n\tuint64_t cdx15_token = cdx15_ipc_begin(this, selector);')
    body=once(body,'\treturn ret;','\tcdx15_ipc_end(cdx15_token, (uint32_t)ret);\n\treturn ret;')
    return text[:start]+body+text[end:]
def build():
    rel='iokit/Kernel/IOUserClient.cpp';old=(XNU/rel).read_text(encoding='utf-8');new=ipc(old)
    patch=''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='a/'+rel,tofile='b/'+rel,n=3))
    # Append-only EOF patch for kern_exit, independent of the existing in-body patches.
    rel2='bsd/kern/kern_exit.c';original=(XNU/rel2).read_text(encoding='utf-8')
    patch+=''.join(difflib.unified_diff(original.splitlines(True),(original+'\n'+DAEMON).splitlines(True),fromfile='a/'+rel2,tofile='b/'+rel2,n=3))
    (HERE/'zzzzzzzzzzzzzzzzzzzzzzzz-cdx15-observe.patch').write_text(patch,encoding='utf-8',newline='\n')
    (HERE/'core-source-reference.json').write_text(json.dumps({rel:hashlib.sha256(old.encode()).hexdigest()},indent=2),encoding='utf-8')
if __name__=='__main__':build()
