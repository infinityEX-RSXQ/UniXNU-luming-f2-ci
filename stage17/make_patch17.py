from pathlib import Path
import difflib,sys
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
sys.path.insert(0,str(ROOT/'stage15-trace-source-20261102'))
from make_core_patch15 import ipc
from install_stage17 import once,PATCH
XNU=ROOT/'builds/aslr-short-diag-20261101/xnu'
def make():
    rel='iokit/Kernel/IOUserClient.cpp';old=ipc((XNU/rel).read_text(encoding='utf-8'));new=old
    anchor='/* Routine io_connect_set_notification_port */'
    declarations='''extern "C" uint64_t cdx17_port_begin(void *, uint32_t, unsigned, unsigned);
extern "C" void cdx17_port_end(uint64_t, unsigned, uint32_t);
extern "C" void cdx17_ipc_arguments(uint64_t, const IOExternalMethodArguments *);

'''
    assert new.count(anchor)==2
    at=new.index(anchor);new=new[:at]+declarations+new[at:]
    for name,wide in [('is_io_connect_set_notification_port(',0),('is_io_connect_set_notification_port_64(',1)]:
        start=new.index(name);end=new.index('\n}\n',start)+3;body=new[start:end]
        body=once(body,'\tclient->ipcEnter(kIPCLockWrite);',
            '\tuint64_t cdx17_token = cdx17_port_begin(client, notification_type, '+str(wide)+', port != MACH_PORT_NULL);\n\tclient->ipcEnter(kIPCLockWrite);')
        body=once(body,'\treturn ret;','\tcdx17_port_end(cdx17_token, '+str(wide)+', (uint32_t)ret);\n\treturn ret;')
        new=new[:start]+body+new[end:]
    new=once(new,'\tuint64_t cdx15_token = cdx15_ipc_begin(this, selector);',
        '\tuint64_t cdx15_token = cdx15_ipc_begin(this, selector);\n\tcdx17_ipc_arguments(cdx15_token, args);')
    patch=''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='a/'+rel,tofile='b/'+rel,n=3))
    (HERE/Path(PATCH).name).write_text(patch,encoding='utf-8',newline='\n')
    return old,new
if __name__=='__main__':make()
