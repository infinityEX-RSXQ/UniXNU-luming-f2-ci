// SPDX-License-Identifier: BSD-2-Clause-Patent
#define CDX19_LIBRARY_ONLY
#include "test_model19.cpp"
#include "Relations21.h"
static cdx19::Sample sample;
static cdx21::Relations relations;
static void task(Bytes &b,unsigned pid,uint64_t tid,uint64_t owner,bool target=true,unsigned kind=10){
 begin(b,0x903,pid);Bytes p(120);w64(p,0,pid+10000);w32(p,84,pid);memcpy(p.data()+88,target?"lsd":"outside",target?4:8);item(b,0x905,p);
 begin(b,0x904,tid);Bytes t(104);w64(t,0,tid);w32(t,88,1);item(b,0x906,t);Bytes u(24);w64(u,0,0x190001000+tid);array(b,0x916,u,3);end(b,tid);
 Bytes w(31);w64(w,0,owner);w64(w,8,tid);w64(w,16,0x12340000);w[24]=kind;array(b,0x91d,w,1);end(b,pid);
}
static void collect(Bytes &b){sample={};assert(cdx19::parse(b.data(),b.size(),sample));assert(cdx21::collect(b.data(),b.size(),sample,relations));assert(relations.valid);}
int main(){
 Bytes b;item(b,0x59a25807);task(b,99,0x2b0,0x255);task(b,200,0x255,0x111,false);task(b,201,0x111,0,false);item(b,0xf19158ed);
 collect(b);assert(relations.n==2 && relations.count==3 && relations.passes==2);
 auto &o=relations.owners[0];assert(o.tid==0x255 && o.found && o.id.pid==200 && o.id.unique==10200 && !strcmp(o.id.comm,"outside"));
 assert(o.thread.nu==3 && o.thread.u[0]==0x190001255 && o.thread.kind==10 && o.thread.owner==0x111);
 assert(o.source==1 && o.firstWaiter==0x2b0);
 assert(relations.owners[1].found && relations.owners[1].id.pid==201);
 // Typed SleepWithInheritor -> mutex owner chain, including reverse task order.
 Bytes typed;item(typed,0x59a25807);task(typed,201,0x888,0,false,2);task(typed,200,0x2fc,0x888,false,1);task(typed,96,0x600,0x2fc,true,18);item(typed,0xf19158ed);collect(typed);
 assert(relations.n==2 && cdx21::find(relations,0x2fc)->id.pid==200 && cdx21::find(relations,0x888)->id.pid==201);
 collect(b);
 // Same owner value in a receive record must never be used as a TID.
 auto &root=sample.processes[3].threads[0];root.kind=2;assert(!strcmp(cdx21::kind(root),"portname"));
 assert(cdx21::collect(b.data(),b.size(),sample,relations) && !relations.n);
 root.kind=4;assert(!strcmp(cdx21::kind(root),"pid"));assert(cdx21::collect(b.data(),b.size(),sample,relations) && !relations.n);
 root.kind=10;root.owner=~uint64_t(0)-2;assert(!strcmp(cdx21::kind(root),"sentinel"));assert(cdx21::collect(b.data(),b.size(),sample,relations) && !relations.n);
 // Missing owner, duplicate TID and task-order-independent owner lookup.
 Bytes missing;item(missing,0x59a25807);task(missing,99,88,999);item(missing,0xf19158ed);collect(missing);assert(relations.n==1 && !relations.owners[0].found);
 Bytes duplicate;item(duplicate,0x59a25807);task(duplicate,200,597,0,false);task(duplicate,99,688,597);task(duplicate,201,597,0,false);item(duplicate,0xf19158ed);collect(duplicate);
 assert(relations.owners[0].matches==2 && !relations.owners[0].found);
 // Global index overflow is explicit; it does not fabricate a missing owner.
 Bytes many;item(many,0x59a25807);task(many,99,688,597);for(unsigned j=0;j<1026;++j)task(many,200+j,10000+j,0,false);task(many,3000,597,0,false);item(many,0xf19158ed);collect(many);
 assert(relations.overflow==4 && relations.count==1024 && relations.owners[0].found && relations.owners[0].id.pid==3000);
 // A cycle is collected with deduplicated owners, never released or declared deadlock.
 Bytes cycle;item(cycle,0x59a25807);task(cycle,99,688,597);task(cycle,200,597,688,false);item(cycle,0xf19158ed);collect(cycle);assert(relations.n==2 && !relations.depthLimited);
 Bytes chain;item(chain,0x59a25807);task(chain,99,688,100);for(unsigned j=100;j<106;++j)task(chain,200+j,j,j+1,false);item(chain,0xf19158ed);collect(chain);assert(relations.depthLimited && relations.passes==3 && !relations.owners[relations.n-1].found);
 // Port labels and turnstile versions retain source type and never infer domain.
 Bytes labels;item(labels,0x59a25807);task(labels,99,688,0);task(labels,200,597,0,false);
 begin(labels,0x934,1000);Bytes li(5);li[0]=7;li[4]=3;item(labels,0x935,li);Bytes name={'s','e','r','v','i','c','e',0};item(labels,0x936,name);end(labels,1000);
 Bytes turn(28);w64(turn,0,688);w64(turn,8,597);w64(turn,18,8);turn[26]=7;array(labels,0x929,turn,1);item(labels,0xf19158ed);collect(labels);
 assert(relations.nt==1 && relations.turns[0].version==28 && relations.turns[0].label==7 && relations.n==1 && relations.owners[0].found);
 assert(relations.owners[0].source==2 && relations.owners[0].firstWaiter==688);
 assert(relations.nl==1 && relations.labels[0].id==7 && relations.labels[0].domain==3 && !strcmp(relations.labels[0].name,"service"));
 for(size_t at=0;at<labels.size();at+=16+cdx19::u32(labels.data()+at+4))if(cdx19::u64(labels.data()+at+8)>>32==0x929){w64(labels,at+16+18,4);break;}
 collect(labels);assert(relations.n==0); // workqueue context is not a TID
 cdx21::Relations empty={};sample.parsed=0;assert(!cdx21::collect(b.data(),b.size(),sample,empty) && empty.error==1);
 puts("PASS Stage21 owner joins, sentinels, task order, ambiguity, missing, overflow, chain limits, turnstile, labels");
}
