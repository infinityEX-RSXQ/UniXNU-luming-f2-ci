    // Diagnostic boundary samples are not the original gate action's decision
    // point. Read private words only while the family's recursive gate is held.
    static bool enabled18(){
        unsigned v=0;PE_parse_boot_argn("luming-display-wait-probe",&v,sizeof(v));return v==1;
    }
    Cdx18View gatedView18(){
        Cdx18View view={};IOWorkLoop *loop=getWorkLoop();
        if(!loop || !loop->inGate())return view;
        const auto *self=reinterpret_cast<const unsigned char *>(this);
        const void *current=nullptr,*queued=nullptr;
        memcpy(&view.completed,self+0x16bc,4);
        memcpy(&current,self+0x1560,8);memcpy(&queued,self+0x1568,8);
        view.current=current?1U:0U;view.queued=queued?1U:0U;view.valid=1;return view;
    }
    Cdx18View boundaryView18(){
        Cdx18View view={};IOWorkLoop *loop=getWorkLoop();if(!loop)return view;
        auto action=[](OSObject *owner,void *a,void *,void *,void *)->IOReturn {
            *static_cast<Cdx18View *>(a)=static_cast<NativeLegacyDisplay *>(owner)->gatedView18();return kIOReturnSuccess;
        };
        if(loop->runAction(action,this,&view)!=kIOReturnSuccess)view={};return view;
    }
    IOReturn waitForSwap(IOUserClient *client,uint32_t id,uint32_t flags,uint32_t timeout) override {
        if(!enabled18())return IOMobileFramebufferLegacy::waitForSwap(client,id,flags,timeout);
        Cdx18View pre=boundaryView18();uint64_t token=cdx18_wait_begin(client,id,flags,timeout,&pre);
        IOReturn status=IOMobileFramebufferLegacy::waitForSwap(client,id,flags,timeout);
        Cdx18View post=boundaryView18();cdx18_wait_end(token,(uint32_t)status,&post);return status;
    }
