/* Stage25 opt-in diagnostics. Port and kmsg identities stay inside this file. */
#include <machine/machine_routines.h>
#include <IOKit/IOLib.h>
#include <pexpert/pexpert.h>
#define CDX25_CAPACITY 64
#define CDX25_PENDING UINT32_MAX

extern struct proc *proc_find(int pid);
extern void proc_rele(struct proc *p);

/*
 * Tail of struct ipc_service_port_label with CONFIG_SERVICE_PORT_INFO.
 * Kept local to avoid pulling another kernel header into mach_msg.c late.
 */
struct cdx25_svc_label {
	void *sblabel;
	uint64_t launchd_context;
	uint32_t launchd_name;
	uint16_t flags;
	uint8_t domain;
	char *service_name;
};

struct cdx25_row {
	uint64_t seq, tid, context, peer_tid;
	uint32_t client, name, request, send_rc;
	uint32_t peer, delivery_rc, reply, reply_tx, reply_rc;
	uint32_t is_lsd;
	char comm[17];
	char svc[17];
	char wait_svc[17];
	ipc_kmsg_t message;
	ipc_port_t reply_port;
	uint64_t dest_addr, dest_space, dest_task;
	uint64_t wait_owner;
	uint64_t wait_ctx;
	uint32_t wait_type;
	uint32_t wait_flags;
	uint32_t wait_pid;
	uint32_t dest_hops;
};
static struct cdx25_row cdx25_rows[CDX25_CAPACITY];
static unsigned cdx25_enabled, cdx25_busy, cdx25_missed;
static uint64_t cdx25_next;
static uint32_t cdx25_lsd_recv_name;
static uint32_t cdx25_lsd_recv_pid;
static uint32_t cdx25_lsd_recv_msg_id;
static uint32_t cdx25_lsd_recv_msg_size;

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

static bool
cdx25_is_lsd(const char *name)
{
	return name && name[0] == 'l' && name[1] == 's' && name[2] == 'd' &&
	    name[3] == '\0';
}

extern char *proc_name_address(void *);

static bool
cdx25_lsd_selfreply(ipc_kmsg_t kmsg, ipc_port_t reply)
{
	if (!IP_VALID(reply)) {
		return false;
	}
	task_t task = current_task();
	struct proc *proc = get_bsdtask_info(task);
	if (!proc || !cdx25_is_lsd(proc_name_address(proc))) {
		return false;
	}
	mach_msg_header_t *hdr = ikm_header(kmsg);
	if (hdr->msgh_id != 0xca8) {
		return false;
	}
	hdr->msgh_id = 0xd0c;
	hdr->msgh_bits = MACH_MSGH_BITS(MACH_MSG_TYPE_PORT_SEND_ONCE, 0);
	hdr->msgh_remote_port = reply;
	hdr->msgh_local_port = MACH_PORT_NULL;
	hdr->msgh_size = (mach_msg_size_t)(sizeof(mach_msg_header_t) + 8);
	*(uint64_t *)((char *)hdr + sizeof(mach_msg_header_t)) = 0;
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

/*
 * Follow the ip_destination chain of a send target.  A send-once right or a
 * port in transit has no ip_receiver (ip_receiver_name == 0), but its
 * ip_destination points at the real port; the chain ends either at a port
 * with a receive right (a space/task) or at IP_NULL (limbo/dead).
 */
static task_t
cdx25_chain_task(ipc_port_t port, uint64_t *space_out, uint32_t *hops,
    char *svc, size_t svc_size)
{
	ipc_port_t p = port;
	*space_out = 0;
	*hops = 0;
	for (unsigned i = 0; i < 8; i++) {
		if (!IP_VALID(p)) {
			break;
		}
		if (!svc[0] && ip_active(p) && p->ip_service_port && p->ip_splabel) {
			struct cdx25_svc_label *label =
			    (struct cdx25_svc_label *)p->ip_splabel;
			char *name = label->service_name;
			if (name && ((uintptr_t)name >> 48) == 0xffff) {
				cdx25_comm_copy(svc, svc_size, name);
			}
		}
		if (ip_in_a_space(p)) {
			ipc_space_t space = p->ip_receiver;
			*space_out = (uint64_t)(uintptr_t)space;
			*hops = i;
			return space ? space->is_task : TASK_NULL;
		}
		if (!ip_active(p)) {
			break;
		}
		if (!ip_mq_lock_try(p)) {
			break;
		}
		ipc_port_t next = ip_get_destination(p);
		ip_mq_unlock(p);
		if (!IP_VALID(next) || next == p) {
			break;
		}
		p = next;
	}
	*hops = 8;
	return TASK_NULL;
}

/*
 * If the resolved peer is blocked receiving on a port, record that port's
 * owner and (when it is a service port) its service label.  This answers
 * "what is lsd itself waiting for" at the moment SpringBoard sends to it.
 */
static void
cdx25_capture_wait(task_t task, uint64_t *owner, uint64_t *ctx,
    uint32_t *type, uint32_t *flags, uint32_t *pid,
    char *svc, size_t svc_size)
{
	thread_t th, fallback = NULL;
	if (!task) {
		return;
	}
	queue_iterate(&task->threads, th, thread_t, task_threads) {
		if (th->block_hint == kThreadWaitNone ||
		    th->block_hint == kThreadWaitParkedWorkQueue) {
			continue;
		}
		if (!fallback) {
			fallback = th;
		}
		if (th->block_hint == kThreadWaitPortReceive &&
		    th->waitq.wq_q && th->wait_event == IPC_MQUEUE_RECEIVE) {
			*type = (uint32_t)kThreadWaitPortReceive;
			thread_waitinfo_v2_t wi = {};
			struct ipc_service_port_label *ispl = NULL;
			wi.wait_type = kThreadWaitPortReceive;
			kdp_mqueue_recv_find_owner(th->waitq.wq_q,
			    th->wait_event, &wi, &ispl);
			*owner = wi.owner;
			*ctx = wi.context;
			*flags = wi.wait_flags;
			if (waitq_type(th->waitq.wq_q) == WQT_PORT) {
				ipc_port_t wp = ip_from_waitq(th->waitq.wq_q);
				if (IP_VALID(wp) && ip_active(wp) &&
				    wp->ip_specialreply) {
					*pid = (uint32_t)wp->ip_pid;
					struct proc *p = proc_find((int)*pid);
					if (p) {
						cdx25_comm_copy(svc, svc_size,
						    proc_name_address(p));
						proc_rele(p);
					}
				}
			}
			if (ispl) {
				struct cdx25_svc_label *label =
				    (struct cdx25_svc_label *)ispl;
				char *name = label->service_name;
				if (name && ((uintptr_t)name >> 48) == 0xffff) {
					cdx25_comm_copy(svc, svc_size, name);
				}
			}
			return;
		}
	}
	if (fallback) {
		*type = (uint32_t)fallback->block_hint;
	}
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
	if (!proc) {
		return 0;
	}
	const char *client_name = proc_name_address(proc);
	bool is_lsd = cdx25_is_lsd(client_name);
	if (!cdx25_is_springboard(client_name) && !is_lsd) {
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
	char svc[17] = {};
	char wait_svc[17] = {};
	uint64_t wait_owner = 0;
	uint64_t wait_ctx = 0;
	uint32_t wait_type = 0;
	uint32_t wait_flags = 0;
	uint32_t wait_pid = 0;
	uint64_t dest_addr = 0, dest_space = 0, dest_task = 0;
	uint32_t dest_hops = 0;
	ipc_port_t dest = header->msgh_remote_port;
	if (IP_VALID(dest)) {
		dest_addr = (uint64_t)(uintptr_t)dest;
		uint64_t space = 0;
		task_t peer_task = cdx25_chain_task(dest, &space, &dest_hops,
		    svc, sizeof(svc));
		dest_space = space;
		dest_task = (uint64_t)(uintptr_t)peer_task;
		if (peer_task) {
			peer_pid = (uint32_t)task_pid(peer_task);
			struct proc *peer_proc = get_bsdtask_info(peer_task);
			cdx25_comm_copy(peer_comm, sizeof(peer_comm),
			    peer_proc ? proc_name_address(peer_proc) : NULL);
			cdx25_capture_wait(peer_task, &wait_owner, &wait_ctx,
			    &wait_type, &wait_flags, &wait_pid,
			    wait_svc, sizeof(wait_svc));
		} else if (space) {
			/* kernel-owned port: ipc_space_kernel has no is_task */
			cdx25_comm_copy(peer_comm, sizeof(peer_comm), "kernel");
		} else {
			cdx25_comm_copy(peer_comm, sizeof(peer_comm), "no-recv");
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
		.is_lsd = is_lsd,
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
		.dest_hops = dest_hops,
		.wait_owner = wait_owner,
		.wait_ctx = wait_ctx,
		.wait_type = wait_type,
		.wait_flags = wait_flags,
		.wait_pid = wait_pid,
	};
	cdx25_comm_copy(row->comm, sizeof(row->comm), peer_comm);
	cdx25_comm_copy(row->svc, sizeof(row->svc), svc);
	cdx25_comm_copy(row->wait_svc, sizeof(row->wait_svc), wait_svc);
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
	task_t recv_task = current_task();
	struct proc *recv_proc = get_bsdtask_info(recv_task);
	if (recv_proc && cdx25_is_lsd(proc_name_address(recv_proc))) {
		cdx25_lsd_recv_msg_id = (uint32_t)header->msgh_id;
		cdx25_lsd_recv_msg_size = header->msgh_size;
	}
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
	for (uint64_t s = seen; s > 0 && s + CDX25_CAPACITY > seen && n < 1; s--) {
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

	int used = snprintf(out, size, "    rpc n=%u seen=%llu m=%u\n",
	    n, (unsigned long long)seen, missed);
	if (used < 0 || (size_t)used >= size) {
		return;
	}
	if (n) {
		int rw = snprintf(out + used, size - used,
		    "    R0 tx%x rc%x r%x\n", found[0].reply_tx,
		    found[0].reply_rc, found[0].reply);
		if (rw > 0 && (size_t)rw < size - used) {
			used += rw;
		}
	} else {
		snprintf(out + used, size - used, "    R0 none\n");
	}
	{
		uint32_t spid = n ? found[0].client : 0;
		struct cdx25_row *latest = NULL;
		if (spid) {
			for (unsigned i = 0; i < CDX25_CAPACITY; i++) {
				struct cdx25_row *row = &cdx25_rows[i];
				if (row->seq && row->client == spid &&
				    (!latest || row->seq > latest->seq)) {
					latest = row;
				}
			}
		}
		if (latest) {
			char lc[9] = {};
			for (unsigned j = 0; j < 8 && latest->comm[j]; j++) {
				lc[j] = latest->comm[j];
			}
			int lw = snprintf(out + used, size - used,
			    "    L%llx req%x tx%x rc%x p%u %s\n",
			    (unsigned long long)latest->seq, latest->request,
			    latest->reply_tx, latest->reply_rc, latest->peer,
			    lc[0] ? lc : "?");
			if (lw > 0 && (size_t)lw < size - used) {
				used += lw;
			}
		} else {
			snprintf(out + used, size - used, "    L none\n");
		}
	}
	{
		uint32_t gcx = ml_phys_read_word_64(0x3d99094ULL);
		uint32_t gid = 0;
		if (gcx & 0x80000000u) {
			gid = ml_phys_read_word_64(0x3d00000ULL);
		}
		int gw = snprintf(out + used, size - used,
		    "    G%x/%x\n", gcx, gid);
		if (gw > 0 && (size_t)gw < size - used) {
			used += gw;
		}
	}
	{
		int s1 = 0;
		if (PE_parse_boot_argn("luming-gpu-s1", &s1, sizeof(s1)) && s1 > 0) {
			const uint64_t gcc = 0x100000ULL;
			uint32_t v = ml_phys_read_word_64(gcc + 0x71004);
			if (!(v & 1u)) {
				ml_phys_write_word_64(gcc + 0x71004, v | 1u);
			}
			v = ml_phys_read_word_64(gcc + 0x52010);
			ml_phys_write_word_64(gcc + 0x52010, v | 0x00300000u);
			const uint64_t en[] = {
				0x3d990bcULL, 0x3d990e4ULL, 0x3d993e8ULL,
				0x3d990e8ULL, 0x3d997000ULL, 0x3d990d4ULL,
				0x3d99060ULL, 0x3d990f4ULL,
			};
			for (unsigned i = 0; i < sizeof(en) / sizeof(en[0]); i++) {
				v = ml_phys_read_word_64(en[i]);
				if (!(v & 1u)) {
					ml_phys_write_word_64(en[i], v | 1u);
				}
			}
			IODelay(10);
			uint32_t gcx2 = ml_phys_read_word_64(0x3d99094ULL);
			uint32_t gid2 = 0;
			uint32_t st = 1;
			if (s1 >= 2) {
				uint32_t pm = ml_phys_read_word_64(0x3d90000ULL);
				uint32_t po = ml_phys_read_word_64(0x3d90004ULL);
				if (!(pm & 1u) && !(po & 1u)) {
					ml_phys_write_word_64(0x3d90000ULL, pm & ~1u);
					ml_phys_write_word_64(0x3d90004ULL, 0);
					ml_phys_write_word_64(0x3d90010ULL, 0x00440034u);
					ml_phys_write_word_64(0x3d90014ULL, 0x00001555u);
					ml_phys_write_word_64(0x3d90020ULL, 0x20485699u);
					ml_phys_write_word_64(0x3d90024ULL, 0x00182261u);
					ml_phys_write_word_64(0x3d90028ULL, 0x82aa299cu);
					ml_phys_write_word_64(0x3d90018ULL, 0x00000400u);
					ml_phys_write_word_64(0x3d9001cULL, 0x00000005u);
					ml_phys_write_word_64(0x3d90000ULL,
					    ml_phys_read_word_64(0x3d90000ULL) | 4u);
					ml_phys_write_word_64(0x3d90004ULL, 1u);
					for (unsigned j = 0; j < 1000; j++) {
						if (ml_phys_read_word_64(0x3d90000ULL) &
						    0x80000000u) {
							break;
						}
						IODelay(1);
					}
					ml_phys_write_word_64(0x3d90018ULL,
					    ml_phys_read_word_64(0x3d90018ULL) | 7u);
					ml_phys_write_word_64(0x3d90000ULL,
					    ml_phys_read_word_64(0x3d90000ULL) | 1u);
				}
				v = ml_phys_read_word_64(0x3d99080ULL);
				ml_phys_write_word_64(0x3d99080ULL,
				    (v & ~0x00fff007u) | 0x00228000u);
				IODelay(1);
				for (unsigned j = 0; j < 2000; j++) {
					if (ml_phys_read_word_64(0x3d99094ULL) &
					    0x80000000u) {
						break;
					}
					IODelay(1);
				}
				v = ml_phys_read_word_64(0x3d99080ULL);
				ml_phys_write_word_64(0x3d99080ULL, v | 0x800u);
				gcx2 = ml_phys_read_word_64(0x3d99094ULL);
				if (gcx2 & 0x80000000u) {
					gid2 = ml_phys_read_word_64(0x3d00000ULL);
				}
				st = 2;
			}
			int sw = snprintf(out + used, size - used,
			    "    S1 %d st%x cx%x id%x\n", s1, st, gcx2, gid2);
			if (sw > 0 && (size_t)sw < size - used) {
				used += sw;
			}
			return;
		}
	}
	struct cdx25_row *x = NULL;
	uint32_t wn = cdx25_lsd_recv_name;
	uint32_t wpid = cdx25_lsd_recv_pid;
	if (!wn && found[0].dest_task) {
		task_t lt = (task_t)(uintptr_t)found[0].dest_task;
		thread_t th;
		queue_iterate(&lt->threads, th, thread_t, task_threads) {
			if (th->block_hint != kThreadWaitPortReceive ||
			    !th->waitq.wq_q ||
			    th->wait_event != IPC_MQUEUE_RECEIVE) {
				continue;
			}
			thread_waitinfo_v2_t wi = {};
			struct ipc_service_port_label *ispl = NULL;
			wi.wait_type = kThreadWaitPortReceive;
			kdp_mqueue_recv_find_owner(th->waitq.wq_q,
			    th->wait_event, &wi, &ispl);
			wn = (uint32_t)wi.owner;
			break;
		}
	}
	if (!wn) {
		wn = (uint32_t)found[0].wait_owner;
	}
	if (!wpid) {
		wpid = found[0].peer;
	}
	if (wn) {
		for (uint64_t s = seen; s > 0 && s + CDX25_CAPACITY > seen; s--) {
			struct cdx25_row *row = cdx25_slot(s);
			if (row->seq == s && row->name == wn &&
			    row->client == wpid) {
				x = row;
				break;
			}
		}
	}
	if (x) {
		char xc[9] = {};
		for (unsigned j = 0; j < 8 && x->comm[j]; j++) {
			xc[j] = x->comm[j];
		}
		snprintf(out + used, size - used,
		    "    W%x M%llx req%x r%x p%u %s d%llx s%.8s\n",
		    wn, (unsigned long long)x->seq, x->request,
		    cdx25_lsd_recv_msg_id, x->peer,
		    xc[0] ? xc : "?", (unsigned long long)x->dest_addr, x->svc);
	} else if (wn) {
		snprintf(out + used, size - used, "    W%x no-row\n", wn);
	} else {
		snprintf(out + used, size - used, "    W none\n");
	}
	return;
	if (found[0].dest_task) {
		task_t lt = (task_t)(uintptr_t)found[0].dest_task;
		thread_t th;
		unsigned printed = 0;
		queue_iterate(&lt->threads, th, thread_t, task_threads) {
			if (printed >= 5) {
				break;
			}
			struct arm_saved_state *ss = get_user_regs(th);
			if (!ss || !is_saved_state64(ss)) {
				continue;
			}
			int w = snprintf(out + used, size - used,
			    "    T%llx b%u pc%llx\n",
			    (unsigned long long)thread_tid(th),
			    (unsigned)th->block_hint,
			    (unsigned long long)saved_state64(ss)->pc);
			if (w > 0 && (size_t)w < size - used) {
				used += w;
				printed++;
			} else {
				break;
			}
		}
		return;
	}
	for (unsigned i = 0; i < n; i++) {
		char comm[9] = {};
		for (unsigned j = 0; j < 8 && found[i].comm[j]; j++) {
			comm[j] = found[i].comm[j];
		}
		int w = snprintf(out + used, size - used,
		    "    %llx %x t%x x%x p%u %s d%llx\n",
		    (unsigned long long)found[i].seq, found[i].request,
		    found[i].send_rc, found[i].delivery_rc, found[i].peer,
		    comm[0] ? comm : "?", (unsigned long long)found[i].dest_addr);
		if (w < 0 || (size_t)w >= size - used) {
			break;
		}
		used += w;
		if (i == 0 && found[i].dest_task) {
			task_t lt = (task_t)(uintptr_t)found[i].dest_task;
			thread_t th, pick = NULL, first = NULL;
			queue_iterate(&lt->threads, th, thread_t, task_threads) {
				if (!first) {
					first = th;
				}
				if (th->block_hint == kThreadWaitNone ||
				    th->block_hint == kThreadWaitParkedWorkQueue) {
					continue;
				}
				pick = th;
				if (th->block_hint == kThreadWaitPortReceive) {
					break;
				}
			}
			if (!pick) {
				pick = first;
			}
			if (pick) {
				struct arm_saved_state *ss = get_user_regs(pick);
				if (ss && is_saved_state64(ss)) {
					w = snprintf(out + used, size - used,
					    "    T%llx b%u pc%llx lr%llx\n",
					    (unsigned long long)thread_tid(pick),
					    (unsigned)pick->block_hint,
					    (unsigned long long)saved_state64(ss)->pc,
					    (unsigned long long)saved_state64(ss)->lr);
					if (w > 0 && (size_t)w < size - used) {
						used += w;
					}
				}
			}
			continue;
		}
		if (i == 0) {
			w = snprintf(out + used, size - used,
			    "    sp%llx tk%llx h%u R%x rt%x rr%x\n",
			    (unsigned long long)found[i].dest_space,
			    (unsigned long long)found[i].dest_task,
			    found[i].dest_hops, found[i].reply,
			    found[i].reply_tx, found[i].reply_rc);
			if (w < 0 || (size_t)w >= size - used) {
				break;
			}
			used += w;
		}
		if (i == 0 && (found[i].wait_owner || found[i].wait_ctx ||
		    found[i].wait_svc[0] || found[i].wait_type)) {
			w = snprintf(out + used, size - used,
			    "    L%u ty%u w%llx c%llx f%x rp%u svc=%.8s\n",
			    found[i].peer, found[i].wait_type,
			    (unsigned long long)found[i].wait_owner,
			    (unsigned long long)found[i].wait_ctx,
			    found[i].wait_flags, found[i].wait_pid,
			    found[i].wait_svc);
			if (w > 0 && (size_t)w < size - used) {
				used += w;
			}
		}
		if (i == 0 && found[i].dest_task) {
			task_t lt = (task_t)(uintptr_t)found[i].dest_task;
			thread_t th, pick = NULL, first = NULL;
			queue_iterate(&lt->threads, th, thread_t, task_threads) {
				if (!first) {
					first = th;
				}
				if (th->block_hint == kThreadWaitNone ||
				    th->block_hint == kThreadWaitParkedWorkQueue) {
					continue;
				}
				pick = th;
				if (th->block_hint == kThreadWaitPortReceive) {
					break;
				}
			}
			if (!pick) {
				pick = first;
			}
			if (pick) {
				struct arm_saved_state *ss = get_user_regs(pick);
				if (ss && is_saved_state64(ss)) {
					w = snprintf(out + used, size - used,
					    "    T%llx b%u pc%llx lr%llx\n",
					    (unsigned long long)thread_tid(pick),
					    (unsigned)pick->block_hint,
					    (unsigned long long)saved_state64(ss)->pc,
					    (unsigned long long)saved_state64(ss)->lr);
					if (w > 0 && (size_t)w < size - used) {
						used += w;
					}
				}
			}
		}
		if (found[i].svc[0] && (size_t)used + 24 < size) {
			w = snprintf(out + used, size - used,
			    "    svc=%.12s\n", found[i].svc);
			if (w > 0 && (size_t)w < size - used) {
				used += w;
			}
		}
	}
}




