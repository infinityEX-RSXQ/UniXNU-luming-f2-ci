#include <stdint.h>
#include <stddef.h>
extern "C" int copyin(uint64_t,void *,size_t);
extern "C" void *memcpy(void *,const void *,size_t);
extern "C" size_t strnlen(const char *,size_t);
extern "C" int snprintf(char *,size_t,const char *,...);
#include "ModeSnapshot.h"
