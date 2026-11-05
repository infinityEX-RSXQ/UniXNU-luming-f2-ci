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
/* Called only with the carrier port's mqueue lock held and the target port
 * referenced. Never mutates messages, ports, or queue entries. */
struct cdx35_carrier {
	uint32_t valid, scanned, matches, flags;
	uint32_t first_id;
	int first_sender;
};
extern int get_audit_token_pid(audit_token_t *);
static void
cdx35_scan_carriers(ipc_mqueue_t mq, ipc_port_t target, struct cdx35_carrier *out)
{
	out->valid = 1;
	out->first_sender = -1;
#if DEVELOPMENT || DEBUG
	ipc_kmsg_queue_t queue = &mq->imq_messages;
	ipc_kmsg_t item = ipc_kmsg_queue_first(queue);
	while (item && out->scanned < 16) {
		++out->scanned;
		mach_msg_size_t count = ipc_kmsg_validate_signature(item);
		mach_msg_header_t *header = ikm_header(item);
		bool match = MACH_MSGH_BITS_LOCAL(header->msgh_bits) == MACH_MSG_TYPE_PORT_RECEIVE &&
		    header->msgh_local_port == target;
		if (header->msgh_bits & MACH_MSGH_BITS_COMPLEX) {
			mach_msg_kbase_t *base = mach_msg_header_to_kbase(header);
			uintptr_t start = (uintptr_t)base->msgb_dsc_array;
			uintptr_t end = (uintptr_t)ikm_kdata_end(item);
			if (start > end || count > (end - start) / sizeof(mach_msg_kdescriptor_t)) {
				out->flags |= 8; /* signed count does not fit the kdata buffer */
			} else {
				mach_msg_size_t limit = count;
				if (limit > 32) { limit = 32; out->flags |= 2; }
				for (mach_msg_size_t j = 0; j < limit; ++j) {
					mach_msg_kdescriptor_t *d = &base->msgb_dsc_array[j];
					switch (mach_msg_kdescriptor_type(d)) {
					case MACH_MSG_PORT_DESCRIPTOR:
						if (d->kdesc_port.disposition == MACH_MSG_TYPE_PORT_RECEIVE &&
						    d->kdesc_port.name == target) match = true;
						break;
					case MACH_MSG_GUARDED_PORT_DESCRIPTOR:
						if (d->kdesc_guarded_port.disposition == MACH_MSG_TYPE_PORT_RECEIVE &&
						    d->kdesc_guarded_port.name == target) match = true;
						break;
					case MACH_MSG_OOL_PORTS_DESCRIPTOR:
						if (d->kdesc_port_array.disposition == MACH_MSG_TYPE_PORT_RECEIVE)
							out->flags |= 4; /* OOL array intentionally not traversed */
						break;
					case MACH_MSG_OOL_DESCRIPTOR:
					case MACH_MSG_OOL_VOLATILE_DESCRIPTOR:
						break;
					default:
						out->flags |= 16; /* unrecognized type */
						break;
					}
				}
			}
		}
		if (match) {
			++out->matches;
			if (out->matches == 1) {
				out->first_id = (uint32_t)header->msgh_id;
				out->first_sender = get_audit_token_pid(&ipc_kmsg_get_trailer(item)->msgh_audit);
			}
		}
		item = ipc_kmsg_queue_next(queue, item);
	}
	if (item) out->flags |= 1; /* queue scan limited */
#else
	(void)mq; (void)target;
	out->flags |= 32; /* kdata-bound helper unavailable */
#endif
}

struct cdx25_queue {
	struct cdx35_carrier carrier;
	uint32_t valid, token, count, seq, empty;
	uint32_t scanned, match; /* 0=no identity, 1=absent, 2=candidate, 3=mismatch, 4=limited */
};
static uint32_t
cdx25_chain(ipc_port_t first, int *owner, struct cdx25_queue *queues,
    ipc_kmsg_t expected, uint32_t request, ipc_port_t reply)
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
		if (i < 2 && ip_active(port)) {
			struct cdx25_queue *q = &queues[i];
			uint64_t permuted = VM_KERNEL_UNSLIDE_OR_PERM(port);
			q->valid = 1;
			/* 32-bit fingerprint: collisions and object reuse remain possible. */
			q->token = (uint32_t)(permuted ^ (permuted >> 32));
			q->count = port->ip_messages.imq_msgcount;
			q->seq = port->ip_messages.imq_seqno;
			q->empty = ipc_kmsg_queue_empty(&port->ip_messages.imq_messages) ? 1 : 0;
			if (i == 1) cdx35_scan_carriers(&port->ip_messages, first, &q->carrier);
			if (i == 0 && expected && reply) {
				ipc_kmsg_queue_t queue = &port->ip_messages.imq_messages;
				ipc_kmsg_t item = ipc_kmsg_queue_first(queue);
				q->match = 1;
				while (item && q->scanned < 16) {
					++q->scanned;
					if (item == expected) {
						/* Queue lock owns item; never dereference the saved pointer. */
						(void)ipc_kmsg_validate_signature(item);
						const mach_msg_header_t *h = ikm_header(item);
						q->match = ((uint32_t)h->msgh_id == request &&
						    h->msgh_local_port == reply) ? 2 : 3;
						break;
					}
					item = ipc_kmsg_queue_next(queue, item);
				}
				if (item && q->scanned == 16 && q->match == 1) q->match = 4;
			}
		}
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
	if (matches == 1 && found.reply_port) ip_reference(found.reply_port);
	cdx25_unlock();
	unsigned missed = __atomic_load_n(&cdx25_missed, __ATOMIC_RELAXED);
	if (matches != 1) {
		snprintf(out, size, "rpc=%s matches=%u seen=%llu missed=%u\n",
		    matches ? "ambiguous" : "unavailable", matches, (unsigned long long)seen, missed);
		return;
	}
	uint32_t now_state = cdx25_port_state(found.dest_port);
	int owner = -1;
	struct cdx25_queue queues[2] = {};
	uint32_t chain = cdx25_chain(found.dest_port, &owner, queues,
	    found.message, found.request, found.reply_port);
	if (found.dest_port) ip_release(found.dest_port);
	if (found.reply_port) ip_release(found.reply_port);
	char owner_name[17] = {};
	if (owner > 0) proc_name(owner, owner_name, sizeof(owner_name));
	int written = snprintf(out, size,
	    "r=%llu req=%x tx=%x rx=%x d=%u/%u\nchain=%x owner=%d %s miss=%u\nQ=%u:%08x:%u:%u:%u P=%u:%08x:%u:%u:%u M=%u/%u\nC=%u/%u/%u f=%x id=%x pid=%d\n",
	    (unsigned long long)found.seq, found.request, found.send_rc, found.delivery_rc,
	    found.dest_state, now_state, chain, owner, owner_name[0] ? owner_name : "unknown", missed,
	    queues[0].valid, queues[0].token, queues[0].count, queues[0].seq, queues[0].empty,
	    queues[1].valid, queues[1].token, queues[1].count, queues[1].seq, queues[1].empty,
	    queues[0].match, queues[0].scanned,
	    queues[1].carrier.valid, queues[1].carrier.scanned, queues[1].carrier.matches,
	    queues[1].carrier.flags, queues[1].carrier.first_id, queues[1].carrier.first_sender);
	if (written < 0 || (size_t)written >= size) snprintf(out, size, "rpc=truncated\n");
}
