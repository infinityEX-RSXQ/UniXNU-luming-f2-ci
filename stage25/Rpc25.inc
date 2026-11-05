/* Stage25 opt-in diagnostics. Port and kmsg identities stay inside this file. */
#define CDX25_CAPACITY 64
#define CDX25_PENDING UINT32_MAX

struct cdx25_row {
	uint64_t seq, tid, context, peer_tid;
	uint32_t client, name, request, send_rc, dest_state;
	uint32_t peer, delivery_rc, reply, reply_tx, reply_rc;
	char comm[17];
	ipc_kmsg_t message;
	ipc_port_t reply_port, dest_port;
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

extern char *proc_name_address(void *);
extern void proc_name(int pid, char *buf, int size);
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

/* Values 0 invalid, 1 dead, 2 in transit, 3 limbo, 4 kernel, 5 userspace.
 * Each is only a momentary observation protected by the port lock. */
static uint32_t
cdx25_port_state(ipc_port_t port)
{
	uint32_t state = 0;
	if (IP_VALID(port)) {
		ip_mq_lock(port);
		if (!ip_active(port)) state = 1;
		else if (ip_in_transit(port)) state = 2;
		else if (ip_in_limbo(port)) state = 3;
		else if (ip_in_space(port, ipc_space_kernel)) state = 4;
		else state = 5;
		ip_mq_unlock(port);
	}
	return state;
}

/* Follow at most four successive destinations. Each nibble is one
 * independent, locked observation; this is not an atomic chain snapshot. */
static uint32_t
cdx25_chain(ipc_port_t first, int *owner)
{
	*owner = -1;
	if (!IP_VALID(first)) return 0;
	ip_reference(first);
	ipc_port_t port = first;
	uint32_t result = 0;
	for (unsigned i = 0; i < 4 && IP_VALID(port); ++i) {
		ipc_port_t next = IP_NULL;
		uint32_t state;
		ip_mq_lock(port);
		if (!ip_active(port)) state = 1;
		else if (ip_in_transit(port)) {
			state = 2;
			next = ip_get_destination(port);
			if (IP_VALID(next)) ip_reference(next);
		} else if (ip_in_limbo(port)) state = 3;
		else if (ip_in_space(port, ipc_space_kernel)) state = 4;
		else {
			state = 5;
			/* XNU resolves the receiver PID while the port is locked. */
			*owner = ipc_port_get_receiver_task_locked(port, NULL);
		}
		ip_mq_unlock(port);
		result |= state << (i * 4);
		ip_release(port);
		port = next;
	}
	if (IP_VALID(port)) ip_release(port);
	return result;
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
	/* Snapshot only; the receiver may change after releasing this lock. */
	ipc_port_t dest = header->msgh_remote_port;
	uint32_t dest_state = cdx25_port_state(dest);
	if (!cdx25_lock()) return 0;
	uint64_t seq = ++cdx25_next;
	struct cdx25_row *row = cdx25_slot(seq);
	ipc_port_t old = row->reply_port;
	ipc_port_t old_dest = row->dest_port;
	ip_reference(reply);
	if (IP_VALID(dest)) ip_reference(dest);
	*row = (struct cdx25_row){
		.seq = seq,
		.tid = thread_tid(current_thread()),
		.context = VM_KERNEL_UNSLIDE_OR_PERM(reply),
		.client = task_pid(task),
		.name = reply_name,
		.request = header->msgh_id,
		.dest_state = dest_state,
		.send_rc = CDX25_PENDING,
		.delivery_rc = CDX25_PENDING,
		.reply_tx = CDX25_PENDING,
		.reply_rc = CDX25_PENDING,
		.message = kmsg,
		.reply_port = reply,
		.dest_port = IP_VALID(dest) ? dest : IP_NULL,
	};
	cdx25_unlock();
	if (old) {
		ip_release(old);
	}
	if (old_dest) ip_release(old_dest);
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
	struct cdx25_row found = {};
	unsigned matches = 0;
	uint64_t seen = 0;
	if (!context || !name || !cdx25_lock()) {
		snprintf(out, size, "rpc=unavailable\n");
		return;
	}
	seen = cdx25_next;
	for (unsigned i = 0; i < CDX25_CAPACITY; i++) {
		const struct cdx25_row *row = &cdx25_rows[i];
		if (row->seq && row->client == pid && row->tid == tid &&
		    row->context == context && row->name == name &&
		    row->reply_rc == CDX25_PENDING &&
		    (row->send_rc == 0 || row->send_rc == CDX25_PENDING)) {
			found = *row;
			matches++;
		}
	}
	if (matches == 1 && found.dest_port) ip_reference(found.dest_port);
	cdx25_unlock();
	unsigned missed = __atomic_load_n(&cdx25_missed, __ATOMIC_RELAXED);
	if (matches != 1) {
		snprintf(out, size, "rpc=%s matches=%u seen=%llu missed=%u\n",
		    matches ? "ambiguous" : "unavailable", matches, (unsigned long long)seen, missed);
		return;
	}
	uint32_t now_state = cdx25_port_state(found.dest_port);
	int owner = -1;
	uint32_t chain = cdx25_chain(found.dest_port, &owner);
	if (found.dest_port) ip_release(found.dest_port);
	char owner_name[17] = {};
	if (owner > 0) proc_name(owner, owner_name, sizeof(owner_name));
	snprintf(out, size, "rpc seq=%llu req=%x tx=%x rx=%x d=%u/%u\npeer=%u tid=%llx %s\nchain=%x owner=%d %s missed=%u\n",
	    (unsigned long long)found.seq, found.request, found.send_rc, found.delivery_rc, found.dest_state, now_state,
	    found.peer, (unsigned long long)found.peer_tid,
	    found.comm[0] ? found.comm : "unknown", chain, owner, owner_name[0] ? owner_name : "unknown", missed);
}
