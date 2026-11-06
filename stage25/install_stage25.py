"""Install the default-off Stage25 Mach message trace against a pinned XNU feed."""
from pathlib import Path
import argparse
import difflib
import hashlib
import json

HERE = Path(__file__).resolve().parent
SOURCE = 'osfmk/ipc/mach_msg.c'
SOURCE2 = 'osfmk/ipc/mach_port.c'
PATCH = 'zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz-cdx25-rpc.patch'


def once(text, anchor, replacement):
    if text.count(anchor) != 1:
        raise ValueError(f'Stage25 anchor missing or ambiguous: {anchor!r}')
    return text.replace(anchor, replacement)


def make_patch(tree):
    raw = (tree / SOURCE).read_bytes().replace(b'\r\n', b'\n')
    pin = (HERE / 'mach_msg.sha256').read_text().strip()
    if hashlib.sha256(raw).hexdigest() != pin:
        raise ValueError('Stage25 mach_msg.c source drift')
    old = raw.decode()
    anchor = '#define mach_copyout_field'
    new = once(old, anchor, (HERE / 'Rpc25.inc').read_text().rstrip() + '\n\n' + anchor)
    anchor = '\tmsgr.msgr_context = ikm_header(kmsg)->msgh_remote_port->ip_context;\n'
    new = once(new, anchor, anchor + '''
	bool cdx25_reply = false;
	uint64_t cdx25_seq = cdx25_receive_begin(kmsg, &cdx25_reply);
''')
    anchor = '\t/* kmsg freed */\n\nout:\n'
    new = once(new, anchor, '\tcdx25_receive_end(cdx25_seq, cdx25_reply, mr);\n' + anchor)
    anchor = '\tmr = ipc_kmsg_copyin_from_user(kmsg, send_uctx, space, map, priority, &options);'
    new = once(new, anchor, '\tmach_port_name_t cdx25_name = send_uctx->send_header.msgh_local_port;\n' + anchor)
    anchor = '\tmr = ipc_kmsg_send(kmsg, options, msg_timeout);\n'
    new = once(new, anchor, '''
	bool cdx25_reply = false;
	uint64_t cdx25_seq = cdx25_send_begin(kmsg, cdx25_name, &cdx25_reply);
''' + anchor + '\tcdx25_send_end(cdx25_seq, cdx25_reply, mr);\n')
    anchor = '\tthread_t           self = current_thread();\n\tipc_space_t        space = current_space();\n'
    new = once(new, anchor, anchor + '''	{
		task_t cdx25_task = current_task();
		struct proc *cdx25_proc = get_bsdtask_info(cdx25_task);
		if (cdx25_proc &&
		    cdx25_is_lsd(proc_name_address(cdx25_proc))) {
			cdx25_lsd_recv_name = rcv_name;
			cdx25_lsd_recv_pid = task_pid(cdx25_task);
		}
	}
''')
    diff = difflib.unified_diff(old.splitlines(True), new.splitlines(True),
                                'a/' + SOURCE, 'b/' + SOURCE)
    raw2 = (tree / SOURCE2).read_bytes().replace(b'\r\n', b'\n')
    pin2 = (HERE / 'mach_port.sha256').read_text().strip()
    if hashlib.sha256(raw2).hexdigest() != pin2:
        raise ValueError('Stage25 mach_port.c source drift')
    old2 = raw2.decode()
    anchor2 = '\tkern_return_t ret;\n\n\tif (space == IS_NULL) {\n'
    new2 = once(old2, anchor2, '''	kern_return_t ret;

	if (filter_policy_id) {
		*filter_policy_id = 0;
	}
	return KERN_SUCCESS;

	if (space == IS_NULL) {
''')
    diff_port = difflib.unified_diff(old2.splitlines(True), new2.splitlines(True),
                                     'a/' + SOURCE2, 'b/' + SOURCE2)
    return (f'diff --git a/{SOURCE} b/{SOURCE}\n' + ''.join(diff) +
            f'diff --git a/{SOURCE2} b/{SOURCE2}\n' + ''.join(diff_port)).encode()


def install(tree, device):
    patch = make_patch(tree)
    directory = device / 'patches/xnu/device'
    series = directory / 'series'
    entries = series.read_text().splitlines()
    (directory / PATCH).write_bytes(patch)
    if PATCH not in entries:
        anchor = 'zzzzzzzzzzzzzzzzzzzzzz-cdx14-observation.patch'
        index = entries.index(anchor) if anchor in entries else len(entries)
        entries.insert(index, PATCH)
        series.write_bytes(('\n'.join(entries) + '\n').encode())
    return {'patch': PATCH, 'sha256': hashlib.sha256(patch).hexdigest()}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--core', type=Path, required=True)
    parser.add_argument('--device', type=Path, required=True)
    args = parser.parse_args()
    feeds = [tree for tree in (args.core / 'out/feeds').glob('xnu-*')
             if (tree / SOURCE).is_file()]
    if len(feeds) != 1:
        raise SystemExit(f'Expected one XNU feed, got {feeds}')
    print(json.dumps(install(feeds[0], args.device)))
