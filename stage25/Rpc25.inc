/* Stage25 opt-in diagnostics. Port and kmsg identities stay inside this file. */
#define CDX25_CAPACITY 64
#define CDX25_PENDING UINT32_MAX

struct cdx25_row {
	uint64_t seq, tid, context, peer_tid;
	uint32_t client, name, request, send_rc;
	uint32_t peer, delivery_rc, reply, reply_tx, reply_rc;
	char comm[17];
	ipc_kmsg_t message;
	ipc_port_t reply_port;
	uint64_t dest_addr, dest_space, dest_task;
};
static struct cdx25_row cdx25_rows[CDX25_CAPACITY];
static unsigned cdx25_enabled, cdx25_busy, cdx25_missed;
static uint64_t cdx25_next;

static bool
cdx25_is_springboard(const char *name)
{
	static const char want[] = "SpringBoard";
	if (!name) {
		return false;
	}
	for (unsigned i = 0; i < sizeof(want); i++) {
		if (name[i] != want[i]) {
			return false;
		}
	}
	return true;
}

static void
cdx25_comm_copy(char *dst, size_t n, const char *src)
{
	unsigned i = 0;
	if (src) {
		for (; i + 1 < n && src[i]; i++) {
			dst[i] = src[i];
		}
	}
	for (; i < n; i++) {
		dst[i] = 0;
	}
}

extern char *proc_name_address(void *);
void cdx25_arm(void);
void cdx25_snapshot(uint32_t, uint64_t, uint64_t, uint32_t, char *, size_t);

void
cdx25_arm(void)
{
	__atomic_store_n(&cdx25_enabled, 1, __ATOMIC_RELEASE);
}

static bool
cdx25_lock(void)
{
	if (!__atomic_exchange_n(&cdx25_busy, 1, __ATOMIC_ACQUIRE)) {
		return true;
	}
	__atomic_fetch_add(&cdx25_missed, 1, __ATOMIC_RELAXED);
	return false;
}

static void
cdx25_unlock(void)
{
	__atomic_store_n(&cdx25_busy, 0, __ATOMIC_RELEASE);
}

static struct cdx25_row *
cdx25_slot(uint64_t seq)
{
	return &cdx25_rows[seq % CDX25_CAPACITY];
}

static uint64_t
cdx25_send_begin(ipc_kmsg_t kmsg, mach_port_name_t reply_name, bool *is_reply)
{
	if (!__atomic_load_n(&cdx25_enabled, __ATOMIC_ACQUIRE)) {
		return 0;
	}
	const mach_msg_header_t *header = ikm_header(kmsg);
	if (MACH_MSGH_BITS_REMOTE(header->msgh_bits) == MACH_MSG_TYPE_PORT_SEND_ONCE &&
	    cdx25_lock()) {
		struct cdx25_row *match = NULL;
		unsigned count = 0;
		for (unsigned i = 0; i < CDX25_CAPACITY; i++) {
			struct cdx25_row *row = &cdx25_rows[i];
			if (row->seq && row->reply_tx == CDX25_PENDING &&
			    row->reply_port == header->msgh_remote_port) {
				match = row;
				count++;
			}
		}
		uint64_t seq = 0;
		if (count == 1) {
			seq = match->seq;
			match->reply = header->msgh_id;
			*is_reply = true;
		}
		cdx25_unlock();
		if (seq) {
			return seq;
		}
	}
	ipc_port_t reply = header->msgh_local_port;
	if (!IP_VALID(reply) || !MACH_PORT_VALID(reply_name) ||
	    MACH_MSGH_BITS_LOCAL(header->msgh_bits) != MACH_MSG_TYPE_PORT_SEND_ONCE) {
		return 0;
	}
	task_t task = current_task();
	struct proc *proc = get_bsdtask_info(task);
	if (!proc || !cdx25_is_springboard(proc_name_address(proc))) {
		return 0;
	}

	/*
	 * Resolve the destination port's receiver now, while the send header
	 * still holds a live kernel port pointer.  The receiver identity is
	 * fixed for a port, so this answers "who is SpringBoard sending to"
	 * even when the message stays queued and is never received.
	 */
	uint32_t peer_pid = 0;
	char peer_comm[17] = {};
	uint64_t dest_addr = 0, dest_space = 0, dest_task = 0;
	ipc_port_t dest = header->msgh_remote_port;
	if (IP_VALID(dest)) {
		/*
		 * XNU 10063.141.1 arm64: ip_receiver is at 0x40, is_task at
		 * 0x28.  Disassembly of _ipc_port_get_receiver_task_locked:
		 *   ldr x8, [x19, #0x40]
		 *   ldr x19, [x8, #0x28]
		 */
		dest_addr = (uint64_t)(uintptr_t)dest;
		uintptr_t port_addr = (uintptr_t)dest;
		uint64_t space = *(const volatile uint64_t *)(port_addr + 0x40);
		dest_space = space;
		if (!space) {
			/* no receive right: service port is dead / not owned */
			cdx25_comm_copy(peer_comm, sizeof(peer_comm), "no-recv");
		} else if ((space >> 48) == 0xffff && !(space & 7)) {
			uint64_t taskp = *(const volatile uint64_t *)(uintptr_t)(space + 0x28);
			dest_task = taskp;
			if (!taskp) {
				/* kernel-owned port: ipc_space_kernel has no is_task */
				cdx25_comm_copy(peer_comm, sizeof(peer_comm), "kernel");
			} else if ((taskp >> 48) == 0xffff && !(taskp & 7)) {
				task_t peer_task = (task_t)(uintptr_t)taskp;
				peer_pid = (uint32_t)task_pid(peer_task);
				struct proc *peer_proc = get_bsdtask_info(peer_task);
				cdx25_comm_copy(peer_comm, sizeof(peer_comm),
				    peer_proc ? proc_name_address(peer_proc) : NULL);
			}
		}
	}
	if (!cdx25_lock()) {
		return 0;
	}
	uint64_t seq = ++cdx25_next;
	struct cdx25_row *row = cdx25_slot(seq);
	ipc_port_t old = row->reply_port;
	ip_reference(reply);
	*row = (struct cdx25_row){
		.seq = seq,
		.tid = thread_tid(current_thread()),
		.context = VM_KERNEL_UNSLIDE_OR_PERM(reply),
		.client = task_pid(task),
		.name = reply_name,
		.request = header->msgh_id,
		.send_rc = CDX25_PENDING,
		.delivery_rc = CDX25_PENDING,
		.reply_tx = CDX25_PENDING,
		.reply_rc = CDX25_PENDING,
		.message = kmsg,
		.reply_port = reply,
		.peer = peer_pid,
		.dest_addr = dest_addr,
		.dest_space = dest_space,
		.dest_task = dest_task,
	};
	cdx25_comm_copy(row->comm, sizeof(row->comm), peer_comm);
	cdx25_unlock();
	if (old) {
		ip_release(old);
	}
	return seq;
}

static void
cdx25_send_end(uint64_t seq, bool is_reply, mach_msg_return_t rc)
{
	if (seq && cdx25_lock()) {
		struct cdx25_row *row = cdx25_slot(seq);
		if (row->seq == seq) {
			if (is_reply) {
				row->reply_tx = rc;
			} else {
				row->send_rc = rc;
				if (rc) {
					row->message = NULL;
				}
			}
		}
		cdx25_unlock();
	}
}

/* The header still contains translated kernel port objects at this point. */
static uint64_t
cdx25_receive_begin(ipc_kmsg_t kmsg, bool *is_reply)
{
	if (!__atomic_load_n(&cdx25_enabled, __ATOMIC_ACQUIRE) || !cdx25_lock()) {
		return 0;
	}
	const mach_msg_header_t *header = ikm_header(kmsg);
	const uint64_t tid = thread_tid(current_thread());
	const int pid = task_pid(current_task());
	struct cdx25_row *match = NULL;
	unsigned replies = 0;
	for (unsigned i = 0; i < CDX25_CAPACITY; i++) {
		struct cdx25_row *row = &cdx25_rows[i];
		if (!row->seq || (row->send_rc && row->send_rc != CDX25_PENDING)) {
			continue;
		}
		if (row->message == kmsg && row->request == (uint32_t)header->msgh_id &&
		    row->reply_port == header->msgh_local_port) {
			match = row;
			*is_reply = false;
			break;
		}
		if (row->reply_rc == CDX25_PENDING && row->reply_port == header->msgh_remote_port &&
		    row->client == (uint32_t)pid && row->tid == tid) {
			match = row;
			replies++;
			*is_reply = true;
		}
	}
	uint64_t seq = 0;
	if (match && (!*is_reply || replies == 1)) {
		seq = match->seq;
		if (*is_reply) {
			match->reply = header->msgh_id;
		} else {
			match->message = NULL;
			match->peer = pid;
			match->peer_tid = tid;
			struct proc *proc = get_bsdtask_info(current_task());
			const char *name = proc ? proc_name_address(proc) : NULL;
			if (name) {
				for (unsigned i = 0; i + 1 < sizeof(match->comm) && name[i]; i++) {
					match->comm[i] = name[i];
				}
			}
		}
	}
	cdx25_unlock();
	return seq;
}

static void
cdx25_receive_end(uint64_t seq, bool is_reply, mach_msg_return_t rc)
{
	if (seq && cdx25_lock()) {
		struct cdx25_row *row = cdx25_slot(seq);
		if (row->seq == seq) {
			if (is_reply) {
				row->reply_rc = rc;
			} else {
				row->delivery_rc = rc;
			}
		}
		cdx25_unlock();
	}
}

void
cdx25_snapshot(uint32_t pid, uint64_t tid, uint64_t context, uint32_t name,
    char *out, size_t size)
{
	struct cdx25_row found[3] = {};
	unsigned n = 0;
	uint64_t seen = 0;
	unsigned missed = 0;

	if (!pid || !cdx25_lock()) {
		snprintf(out, size, "rpc=unavailable lock\n");
		return;
	}
	seen = cdx25_next;

	/* Exact thread/port match first, so the selected wait is always row 0. */
	for (unsigned i = 0; i < CDX25_CAPACITY && n < 1; i++) {
		const struct cdx25_row *row = &cdx25_rows[i];
		if (row->seq && row->client == pid && row->tid == tid &&
		    row->context == context && row->name == name &&
		    row->reply_rc == CDX25_PENDING &&
		    (row->send_rc == 0 || row->send_rc == CDX25_PENDING)) {
			found[n++] = *row;
		}
	}

	/* Then one more recent send from the same client, answered or not. */
	for (uint64_t s = seen; s > 0 && s + CDX25_CAPACITY > seen && n < 2; s--) {
		const struct cdx25_row *row = cdx25_slot(s);
		if (row->seq != s || row->client != pid) {
			continue;
		}
		if (row->send_rc != 0 && row->send_rc != CDX25_PENDING) {
			continue;
		}
		bool dup = false;
		for (unsigned j = 0; j < n; j++) {
			if (found[j].seq == s) {
				dup = true;
			}
		}
		if (!dup) {
			found[n++] = *row;
		}
	}
	missed = __atomic_load_n(&cdx25_missed, __ATOMIC_RELAXED);
	cdx25_unlock();

	if (!n) {
		snprintf(out, size, "rpc none seen=%llu m=%u\n",
		    (unsigned long long)seen, missed);
		return;
	}

	int used = snprintf(out, size, "rpc n=%u seen=%llu m=%u\n",
	    n, (unsigned long long)seen, missed);
	if (used < 0 || (size_t)used >= size) {
		return;
	}
	for (unsigned i = 0; i < n; i++) {
		char comm[9] = {};
		for (unsigned j = 0; j < 8 && found[i].comm[j]; j++) {
			comm[j] = found[i].comm[j];
		}
		int w = snprintf(out + used, size - used,
		    "%llx %x t%x x%x p%u %s d%llx\n",
		    (unsigned long long)found[i].seq, found[i].request,
		    found[i].send_rc, found[i].delivery_rc, found[i].peer,
		    comm[0] ? comm : "?", (unsigned long long)found[i].dest_addr);
		if (w < 0 || (size_t)w >= size - used) {
			break;
		}
		used += w;
		if (i == 0) {
			w = snprintf(out + used, size - used,
			    "sp%llx tk%llx\n",
			    (unsigned long long)found[i].dest_space,
			    (unsigned long long)found[i].dest_task);
			if (w < 0 || (size_t)w >= size - used) {
				break;
			}
			used += w;
		}
	}
}
