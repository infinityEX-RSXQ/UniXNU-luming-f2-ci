// Interface fixture only; not a replacement for the full macOS IOKit build.
#include <stdint.h>
#include <stddef.h>
extern unsigned option(const char *);
class OSData {public:static OSData *withBytes(const void *,unsigned);void release();};
class Service {public:bool setProperty(const char *,OSData *);};
extern Service *activeLegacyDisplay;
extern void IOLog(const char *,...) __attribute__((format(printf,1,2)));
extern void panic(const char *,...) __attribute__((noreturn,format(printf,1,2)));
typedef void *thread_call_param_t;
typedef void (*thread_call_func_t)(thread_call_param_t,thread_call_param_t);
typedef struct thread_call *thread_call_t;
extern thread_call_t thread_call_allocate(thread_call_func_t,thread_call_param_t);
extern bool thread_call_enter_delayed(thread_call_t,uint64_t);
extern void clock_interval_to_deadline(unsigned,unsigned,uint64_t *);
#define NSEC_PER_SEC 1000000000U
extern volatile uint32_t native_legacy_swap_validation_calls,native_legacy_swap_validation_result,
    native_legacy_transfer_calls,native_legacy_retirement_calls,native_legacy_vsync_count;
extern volatile int native_legacy_transfer_status;
extern volatile uint64_t native_legacy_transfer_bytes;
#include "FrameSamples14.h"
#include "ProviderProbe14.h"
