#include <stdint.h>
#include <stdbool.h>
#include <stdio.h>
#include <string.h>
#include <assert.h>
#include <stddef.h>
#define DEVELOPMENT 1
#define MACH_MSGH_BITS_COMPLEX 0x80000000U
#define MACH_MSGH_BITS_LOCAL(x) ((x)&255U)
#define MACH_MSG_TYPE_PORT_RECEIVE 16U
#define MACH_MSG_PORT_DESCRIPTOR 0U
#define MACH_MSG_OOL_DESCRIPTOR 1U
#define MACH_MSG_OOL_PORTS_DESCRIPTOR 2U
#define MACH_MSG_OOL_VOLATILE_DESCRIPTOR 3U
#define MACH_MSG_GUARDED_PORT_DESCRIPTOR 4U
typedef void *ipc_port_t;
typedef uint32_t mach_msg_size_t;
typedef struct { uint32_t bits,id; ipc_port_t local; } mach_msg_header_t;
#define msgh_bits bits
#define msgh_id id
#define msgh_local_port local
typedef struct { uint32_t type, disposition; ipc_port_t name; } fake_desc;
typedef union { fake_desc kdesc_port, kdesc_guarded_port, kdesc_port_array, kdesc_header; } mach_msg_kdescriptor_t;
typedef struct { mach_msg_header_t msgb_header; uint32_t msgb_dsc_count; mach_msg_kdescriptor_t msgb_dsc_array[40]; } mach_msg_kbase_t;
typedef struct { int pid; } audit_token_t;
typedef struct { audit_token_t msgh_audit; } trailer_t;
typedef struct message { mach_msg_kbase_t base; trailer_t trailer; struct message *next; uintptr_t end; } *ipc_kmsg_t;
typedef struct { ipc_kmsg_t imq_messages; } *ipc_mqueue_t;
typedef ipc_kmsg_t *ipc_kmsg_queue_t;
static ipc_kmsg_t ipc_kmsg_queue_first(ipc_kmsg_queue_t q) { return *q; }
static ipc_kmsg_t ipc_kmsg_queue_next(ipc_kmsg_queue_t q, ipc_kmsg_t x) { (void)q;return x->next; }
static mach_msg_size_t ipc_kmsg_validate_signature(ipc_kmsg_t m) { return m->base.msgb_dsc_count; }
static mach_msg_header_t *ikm_header(ipc_kmsg_t m) { return &m->base.msgb_header; }
static uintptr_t ikm_kdata_end(ipc_kmsg_t m) { return m->end; }
static mach_msg_kbase_t *mach_msg_header_to_kbase(mach_msg_header_t *h) { return (mach_msg_kbase_t *)h; }
static uint32_t mach_msg_kdescriptor_type(mach_msg_kdescriptor_t *d) { return d->kdesc_header.type; }
static trailer_t *ipc_kmsg_get_trailer(ipc_kmsg_t m) { return &m->trailer; }
#include "Carrier35.inc"
int get_audit_token_pid(audit_token_t *token) { return token->pid; }
static void init(struct message *m) { memset(m,0,sizeof(*m));m->end=(uintptr_t)(m->base.msgb_dsc_array+40); }
int main(void) {
 struct message a[18]; for(unsigned i=0;i<18;i++) init(&a[i]);
 struct {ipc_kmsg_t imq_messages;} q={&a[0]}; void *target=(void *)(uintptr_t)0x1234;
 struct cdx35_carrier r={0}; a[0].base.msgb_header.bits=MACH_MSGH_BITS_COMPLEX; a[0].base.msgb_header.id=123; a[0].trailer.msgh_audit.pid=88; a[0].base.msgb_dsc_count=1; a[0].base.msgb_dsc_array[0].kdesc_port=(fake_desc){MACH_MSG_PORT_DESCRIPTOR,MACH_MSG_TYPE_PORT_RECEIVE,target};
 cdx35_scan_carriers((ipc_mqueue_t)&q,target,&r); assert(r.valid && r.scanned==1 && r.matches==1 && !r.flags && r.first_id==123 && r.first_sender==88);
 r=(struct cdx35_carrier){0}; a[0].base.msgb_dsc_array[0].kdesc_port.disposition=17; cdx35_scan_carriers((ipc_mqueue_t)&q,target,&r); assert(r.matches==0 && r.flags==0);
 r=(struct cdx35_carrier){0}; a[0].base.msgb_dsc_array[0].kdesc_guarded_port=(fake_desc){MACH_MSG_GUARDED_PORT_DESCRIPTOR,MACH_MSG_TYPE_PORT_RECEIVE,target}; cdx35_scan_carriers((ipc_mqueue_t)&q,target,&r); assert(r.matches==1);
 r=(struct cdx35_carrier){0}; a[0].base.msgb_dsc_array[0].kdesc_port_array=(fake_desc){MACH_MSG_OOL_PORTS_DESCRIPTOR,MACH_MSG_TYPE_PORT_RECEIVE,target}; cdx35_scan_carriers((ipc_mqueue_t)&q,target,&r); assert(r.matches==0 && (r.flags&4));
 r=(struct cdx35_carrier){0}; a[0].end=(uintptr_t)a[0].base.msgb_dsc_array; cdx35_scan_carriers((ipc_mqueue_t)&q,target,&r); assert(r.matches==0 && (r.flags&8));
 init(&a[0]); r=(struct cdx35_carrier){0}; a[0].base.msgb_header.bits=MACH_MSG_TYPE_PORT_RECEIVE; a[0].base.msgb_header.local=target; cdx35_scan_carriers((ipc_mqueue_t)&q,target,&r); assert(r.matches==1);
 for(unsigned i=0;i<17;i++) { init(&a[i]);a[i].next=&a[i+1]; } r=(struct cdx35_carrier){0}; cdx35_scan_carriers((ipc_mqueue_t)&q,target,&r); assert(r.scanned==16 && (r.flags&1));
 init(&a[0]); a[0].base.msgb_header.bits=MACH_MSGH_BITS_COMPLEX; a[0].base.msgb_dsc_count=33; r=(struct cdx35_carrier){0}; cdx35_scan_carriers((ipc_mqueue_t)&q,target,&r); assert((r.flags&2));
 init(&a[0]); init(&a[1]); a[0].next=&a[1];
 for(unsigned i=0;i<2;i++){a[i].base.msgb_header.bits=MACH_MSGH_BITS_COMPLEX; a[i].base.msgb_dsc_count=1; a[i].base.msgb_dsc_array[0].kdesc_port=(fake_desc){MACH_MSG_PORT_DESCRIPTOR,MACH_MSG_TYPE_PORT_RECEIVE,target}; a[i].base.msgb_header.id=200+i; a[i].trailer.msgh_audit.pid=100+i;}
 r=(struct cdx35_carrier){0}; cdx35_scan_carriers((ipc_mqueue_t)&q,target,&r); assert(r.matches==2 && r.scanned==2 && r.first_id==200 && r.first_sender==100);
 init(&a[0]); a[0].base.msgb_header.bits=MACH_MSGH_BITS_COMPLEX; a[0].base.msgb_dsc_count=1; a[0].base.msgb_dsc_array[0].kdesc_header.type=99; r=(struct cdx35_carrier){0}; cdx35_scan_carriers((ipc_mqueue_t)&q,target,&r); assert(r.matches==0 && (r.flags&16));
 q.imq_messages=NULL; r=(struct cdx35_carrier){0}; cdx35_scan_carriers((ipc_mqueue_t)&q,target,&r); assert(r.valid && !r.scanned && !r.matches && !r.flags);
 puts("PASS direct/guarded/header, negative, OOL, bounds, queue and descriptor limits, duplicates, unknown, empty");return 0;
}
