#include <stdint.h>
#include <stddef.h>
extern "C" int copyin(uint64_t,void *,size_t);
extern "C" void *memcpy(void *,const void *,size_t);
extern "C" size_t strnlen(const char *,size_t);
extern "C" int snprintf(char *,size_t,const char *,...);
extern "C" void IOLog(const char *,...);
extern const void *gIODTPlane;
static unsigned option(const char *) {return 2;}
// Compile-only API fixture. Does not substitute for full IOKit/kernel build.
class OSObject {public:void retain();void release();static OSObject *cast(OSObject *);};
class OSData:public OSObject {public:static OSData *withBytes(const void *,unsigned);unsigned getLength() const;const void *getBytesNoCopy() const;};
class IORegistryEntry:public OSObject {public:static IORegistryEntry *fromPath(const char *,const void *);OSObject *getProperty(const char *) const;bool setProperty(const char *,OSObject *);void removeProperty(const char *);};
#define OSDynamicCast(T,p) static_cast<T *>(OSObject::cast(p))
#include "UiScalePolicy.h"
#include "ModeSnapshot.h"
#include "ModeSummary13.h"
