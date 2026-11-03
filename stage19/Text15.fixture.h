// SPDX-License-Identifier: BSD-2-Clause-Patent
// Whole lines only, <=88 columns. Leaves room for an explicit omission footer.
#include <stdarg.h>
struct Cdx15Text {
    char *out;size_t capacity,used;unsigned dropped;
    Cdx15Text(char *p,size_t n):out(p),capacity(n),used(0),dropped(0){if(n)out[0]=0;}
    bool line(const char *format,...) __attribute__((format(printf,2,3))) {
        char row[90]={};va_list args;va_start(args,format);int n=vsnprintf(row,sizeof(row),format,args);va_end(args);
        if(n<0 || n>88 || !n || row[n-1]!='\n' || (size_t)n+used+40>=capacity){++dropped;return false;}
        memcpy(out+used,row,(size_t)n);used+=(size_t)n;out[used]=0;return true;
    }
    bool lines(const char *text){bool ok=true;while(*text){const char *end=text;while(*end && *end!='\n')++end;
        size_t n=(size_t)(end-text);char row[90]={};
        if(n>87){++dropped;ok=false;}else{memcpy(row,text,n);row[n]='\n';ok=line("%s",row)&&ok;}
        text=*end?end+1:end;}return ok;
    }
    void footer(unsigned omit,bool clipped){
        if(used>=capacity)return;
        int n=snprintf(out+used,capacity-used,"omit=%u drop=%u clip=%u\n",omit,dropped,(unsigned)clipped);
        if(n>0)used+=(size_t)n<capacity-used?(size_t)n:capacity-used-1;
    }
};
