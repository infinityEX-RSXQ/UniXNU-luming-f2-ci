#include <stdint.h>
#include <stddef.h>
extern void cdx11_capture_exception(int, const char *, int, uint64_t, uint64_t, unsigned, unsigned);
extern int cdx11_crash_summary(int, const char *, const char *, char *, size_t);
void cdx11_caller(void) {
    char output[640];
    cdx11_capture_exception(812,"SpringBoard",6,1,0x19f3df2ecULL,0,1);
    (void)cdx11_crash_summary(812,"SpringBoard","SpringBoard exited",output,sizeof(output));
}
