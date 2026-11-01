// SPDX-License-Identifier: BSD-2-Clause-Patent
// Explicit UI pixels-per-point policy. No physical DPI or panel timing claim.
// Same 4-byte native-endian /chosen contract consumed by stock MobileGestalt.
extern "C" {
volatile unsigned cdx13_ui_requested,cdx13_ui_readback,cdx13_ui_status=99;
volatile unsigned cdx13_ui_writes;

bool cdx13_publish_ui_scale(uint32_t width,uint32_t height)
{
    const unsigned scale=option("luming-display-ui-scale");
    cdx13_ui_requested=scale;
    if(!scale){cdx13_ui_status=0;return true;}
    // The enabled experiment is qualified only for this measured scanout.
    // 2 -> 618 x 1375 points. Scale 3 is not an integral division here.
    if(scale>3 || width!=1236 || height!=2750 || width%scale || height%scale) {
        cdx13_ui_status=1;return false;
    }
    IORegistryEntry *chosen=IORegistryEntry::fromPath("/chosen",gIODTPlane);
    if(!chosen){cdx13_ui_status=2;return false;}
    const char *keys[2]={"display-scale","display-rotation"};
    const uint32_t desired[2]={scale,0};
    OSObject *prior[2]={nullptr,nullptr};
    bool replace[2]={false,false},written[2]={false,false};
    unsigned failure=0;
    for(unsigned i=0;i<2;++i) {
        prior[i]=chosen->getProperty(keys[i]);
        if(prior[i]) {
            prior[i]->retain();
            OSData *data=OSDynamicCast(OSData,prior[i]);uint32_t value=0;
            if(!data || data->getLength()!=4){failure=3;break;}
            memcpy(&value,data->getBytesNoCopy(),4);
            if(value==desired[i])continue;
            // Permit repairing a zero scale; do not overwrite a conflicting
            // positive policy, a nonzero rotation, or an unknown property type.
            if(i!=0 || value!=0){failure=4;break;}
        }
        replace[i]=true;
    }
    if(!failure)for(unsigned i=0;i<2;++i)if(replace[i]) {
        OSData *data=OSData::withBytes(&desired[i],4);
        bool ok=data && chosen->setProperty(keys[i],data);
        if(data)data->release();
        if(!ok){failure=5;break;}
        written[i]=true;
    }
    if(!failure)for(unsigned i=0;i<2;++i) {
        OSData *data=OSDynamicCast(OSData,chosen->getProperty(keys[i]));
        uint32_t actual=0;
        if(!data || data->getLength()!=4){failure=6;break;}
        memcpy(&actual,data->getBytesNoCopy(),4);
        if(actual!=desired[i]){failure=7;break;}
        if(i==0)cdx13_ui_readback=actual;
    }
    if(failure) {
        // Roll back only properties written by this attempt.
        for(unsigned i=0;i<2;++i)if(written[i]) {
            if(prior[i]) {if(!chosen->setProperty(keys[i],prior[i]))failure=8;}
            else chosen->removeProperty(keys[i]);
        }
        cdx13_ui_readback=0;
    } else for(unsigned i=0;i<2;++i)if(written[i])cdx13_ui_writes=cdx13_ui_writes+1;
    for(unsigned i=0;i<2;++i)if(prior[i])prior[i]->release();
    chosen->release();cdx13_ui_status=failure;
    IOLog("CDX13 ui=%u read=%u rc=%u writes=%u\n",scale,
        cdx13_ui_readback,failure,cdx13_ui_writes);
    return failure==0;
}
}
