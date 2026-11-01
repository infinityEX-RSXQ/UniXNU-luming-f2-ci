#include <stdint.h>
#include <stddef.h>
extern void cdx12_capture_mode(int,uint64_t);
extern void cdx12_append_mode_summary(int,char *,size_t);
void cdx12_caller(void) {
    char out[1024]={0};
    cdx12_capture_mode(26,0x1000);
    cdx12_append_mode_summary(26,out,sizeof(out));
}
