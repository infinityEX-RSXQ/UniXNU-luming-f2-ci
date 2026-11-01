// SPDX-License-Identifier: BSD-2-Clause-Patent
// Integer-only, bounded samples of visible pixels; NOT a full-frame CRC.
// Appended verbatim to LegacyDisplayProbe.cpp, so it must not carry "#pragma
// once": the pragma in the translation unit itself is -Werror on the XNU build.
struct Cdx14Samples {
    uint64_t hash;
    uint32_t pixels[64];
};
static bool cdx14_samples(const volatile void *base,uint64_t bytes,uint64_t stride,
    uint32_t width,uint32_t height,Cdx14Samples *out) {
    if(!base || !out || !width || !height || width>16384 || height>16384 ||
       ((uintptr_t)base&3) || (stride&3) || stride<(uint64_t)width*4 ||
       stride>65536 || stride>bytes/height)return false;
    out->hash=14695981039346656037ULL;
    for(unsigned i=0;i<64;++i) {
        uint64_t x=(uint64_t)(i%8)*(width-1)/7;
        uint64_t y=(uint64_t)(i/8)*(height-1)/7;
        const volatile uint32_t *pixel=reinterpret_cast<const volatile uint32_t *>(
            reinterpret_cast<const volatile unsigned char *>(base)+y*stride+x*4);
        uint32_t value=*pixel;out->pixels[i]=value;
        for(unsigned b=0;b<4;++b){out->hash^=(value>>(b*8))&255;out->hash*=1099511628211ULL;}
    }
    return true;
}
static unsigned cdx14_sample_diff(const Cdx14Samples &a,const Cdx14Samples &b) {
    unsigned n=0;for(unsigned i=0;i<64;++i)n+=(a.pixels[i]!=b.pixels[i]);return n;
}
static bool cdx14_sample_due(uint64_t sequence) {
    return sequence<=8 || (sequence<=256 && !(sequence&(sequence-1)));
}
