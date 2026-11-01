"""Source-only ASLR diagnostics, applied after the existing owner3 patches.
Usage: python instrument_aslr_diagnostics.py /path/to/isolated/xnu
No exception, signing, ASLR-selection or exit policy is changed.
"""
from pathlib import Path
import sys
OLD='"exception_log_max_pid: pid %d (%s): sending exception %d (0x%llx 0x%llx)",'
V1='"exception_log_max_pid: pid %d (%s): sending exception %d (0x%llx 0x%llx) cache-slide=0x%x",'
NEW='"exception_log_max_pid: pid %d (%s): sending exception %d (0x%llx 0x%llx) disable-aslr=%u cache-slide=0x%x",'
TAIL='exception, code[0], codeCnt > 1 ? code[1] : 0);'
V1TAIL='exception, code[0], codeCnt > 1 ? code[1] : 0, (unsigned int)task->task_shared_region_slide);'
NEWTAIL='exception, code[0], codeCnt > 1 ? code[1] : 0, (unsigned int)bootarg_disable_aslr, (unsigned int)task->task_shared_region_slide);'
ANCHOR='\tif (proc_pid(get_bsdtask_info(task)) <= exception_log_max_pid) {'
def exception_instrument_v2(text):
    if NEW in text:
        assert NEWTAIL in text and '/* CDX_ASLR_EXC */' in text
        return text
    if V1 in text:
        assert text.count(V1)==1 and text.count(V1TAIL)==1
        text=text.replace(V1,OLD).replace(V1TAIL,TAIL)
    assert text.count(OLD)==1 and text.count(ANCHOR)==1
    start=text.index(OLD);end=text.index(TAIL,start)+len(TAIL)
    block=text[start:end];assert 'record_system_event' in text[max(0,start-200):start]
    text=text[:start]+block.replace(OLD,NEW).replace(TAIL,NEWTAIL)+text[end:]
    return text.replace(ANCHOR,'\t/* CDX_ASLR_EXC */\n\textern bool bootarg_disable_aslr;\n'+ANCHOR)
REPLACEMENT_SHORT='\t\trecord_system_event(SYSTEM_EVENT_TYPE_INFO, SYSTEM_EVENT_SUBSYSTEM_PROCESS, "CDX_ASLR",\n\t\t    "p=%d n=%.16s off=%u slide=%x", proc_pid(get_bsdtask_info(task)),\n\t\t    proc_name_address(get_bsdtask_info(task)), (unsigned int)bootarg_disable_aslr,\n\t\t    (unsigned int)task->task_shared_region_slide);\n\t\trecord_system_event(SYSTEM_EVENT_TYPE_INFO, SYSTEM_EVENT_SUBSYSTEM_PROCESS, "CDX_EXC",\n\t\t    "p=%d e=%d c0=%llx c1=%llx", proc_pid(get_bsdtask_info(task)),\n\t\t    exception, code[0], codeCnt > 1 ? code[1] : 0);'
def exception_instrument(text):
    if '"CDX_ASLR"' in text and '"CDX_EXC"' in text:
        assert '"p=%d n=%.16s off=%u slide=%x"' in text
        assert '"p=%d e=%d c0=%llx c1=%llx"' in text
        return text
    text=exception_instrument_v2(text)
    start=text.index('\t\t'+'record_system_event',text.index('/* CDX_ASLR_EXC */'))
    end=text.index(NEWTAIL,start)+len(NEWTAIL)
    replacement=REPLACEMENT_SHORT
    return text[:start]+replacement+text[end:]
MAPOLD='''#if DEVELOPMENT || DEBUG
	extern bool bootarg_disable_aslr;
	if (bootarg_disable_aslr) {
		slide_amount = 0;
	}
#endif /* DEVELOPMENT || DEBUG */'''
MAPNEW=MAPOLD.replace('#endif /* DEVELOPMENT || DEBUG */','''	/* CDX_ASLR_MAP: observe existing selection, never alter it. */
	extern unsigned int exception_log_max_pid;
	if ((unsigned int)proc_getpid(p) <= exception_log_max_pid) {
		printf("CDX_ASLR_MAP pid=%d comm=%.16s disable=%u max=0x%x selected=0x%x\\n",
		    proc_getpid(p), p->p_comm, (unsigned int)bootarg_disable_aslr,
		    (unsigned int)max_slide, (unsigned int)slide_amount);
	}
#endif /* DEVELOPMENT || DEBUG */''')
def map_instrument(text):
    if 'CDX_ASLR_MAP' in text:
        assert MAPNEW in text
        return text
    assert text.count(MAPOLD)==1,'Mapping anchor differs; inspect this build source'
    return text.replace(MAPOLD,MAPNEW)
if __name__=='__main__':
    root=Path(sys.argv[1])
    paths=[(root/'osfmk/kern/exception.c',exception_instrument),(root/'bsd/vm/vm_unix.c',map_instrument)]
    changes=[(p,f(p.read_text(encoding='utf-8'))) for p,f in paths]
    for p,t in changes:p.write_text(t,encoding='utf-8')
    print('Added ASLR observations; compile/runtime verification still required.')
