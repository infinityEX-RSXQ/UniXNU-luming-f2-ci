# Stage23 waiter and owner snapshot

Stage22 found an lsd unfair lock in only the second snapshot. Its owner was
waiting in Mach receive. The captured frames reached only the Mach wrappers.

Stage23 page 7 prints both stacks from each snapshot, up to four frames each,
starting at index 2 by default. The waiter's stack is A0/A1 and the direct
owner's stack is B0/B1. R/O give the associated pid, thread, and wait kind.
L is the copied receive label if uniquely resolved from that sample. A local
Mach name cannot identify a peer. Unresolved labels print unavailable. A tilde
marks a truncated label.

The two observations are 15 seconds apart. Compare typed edges and frames
before deciding whether a wait persists. The optional frame index, root
ordinal, and lsd instance remain configurable. Page 6 remains available.

CI uses the accepted Stage18 inputs and the existing Intel macOS/Xcode 16.4
workflow. Repack with page=7, frame=2, step=0 and thread=0. This is an opt-in
diagnostic candidate that ends with an intentional snapshot panic.
