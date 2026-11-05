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
