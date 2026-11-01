D:\Codex\workspaces\2026-10-29\zai\work\stage13-mode\audit\mg-scale-cf-0.macho:
(__TEXT,__text) section
1a0215720:	a8 a0 25 d0	adrp	x8, 308246 ; 0x1eb62b000
1a0215724:	08 cd 47 f9	ldr	x8, [x8, #0xf98]
1a0215728:	08 01 40 f9	ldr	x8, [x8]
1a021572c:	a8 83 1b f8	stur	x8, [x29, #-0x48]
1a0215730:	08 00 80 12	mov	w8, #-0x1
1a0215734:	e8 4f 00 b9	str	w8, [sp, #0x4c]
1a0215738:	d4 02 00 b0	adrp	x20, 89 ; 0x1a026e000
1a021573c:	94 f2 04 91	add	x20, x20, #0x13c
1a0215740:	21 d4 23 b0	adrp	x1, 293509 ; 0x1e7c9a000
1a0215744:	21 40 07 91	add	x1, x1, #0x1d0
1a0215748:	e0 03 14 aa	mov	x0, x20
1a021574c:	02 00 80 52	mov	w2, #0x0
1a0215750:	03 00 80 52	mov	w3, #0x0
1a0215754:	24 00 80 52	mov	w4, #0x1
1a0215758:	05 e9 ff 97	bl	0x1a020fb6c
1a021575c:	f3 03 00 aa	mov	x19, x0
1a0215760:	21 d4 23 b0	adrp	x1, 293509 ; 0x1e7c9a000
1a0215764:	21 c0 07 91	add	x1, x1, #0x1f0
1a0215768:	e0 03 14 aa	mov	x0, x20
1a021576c:	02 00 80 52	mov	w2, #0x0
1a0215770:	03 00 80 12	mov	w3, #-0x1
1a0215774:	24 00 80 52	mov	w4, #0x1
1a0215778:	fd e8 ff 97	bl	0x1a020fb6c
1a021577c:	1f 04 00 31	cmn	w0, #0x1
1a0215780:	20 02 00 54	b.eq	0x1a02157c4
1a0215784:	08 2d 80 52	mov	w8, #0x168
1a0215788:	09 01 00 4b	sub	w9, w8, w0
1a021578c:	ea 16 8c 52	mov	w10, #0x60b7
1a0215790:	6a c1 b6 72	movk	w10, #0xb60b, lsl #16
1a0215794:	2a 7d 2a 9b	smull	x10, w9, w10
1a0215798:	4a fd 60 d3	lsr	x10, x10, #32
1a021579c:	4a 01 09 0b	add	w10, w10, w9
1a02157a0:	4b 7d 08 13	asr	w11, w10, #8
1a02157a4:	6a 7d 4a 0b	add	w10, w11, w10, lsr #31
1a02157a8:	48 a5 08 1b	msub	w8, w10, w8, w9
1a02157ac:	00 01 62 1e	scvtf	d0, w8
1a02157b0:	88 02 00 b0	adrp	x8, 81 ; 0x1a0266000
1a02157b4:	01 b9 46 fd	ldr	d1, [x8, #0xd70]
1a02157b8:	00 08 61 1e	fmul	d0, d0, d1
1a02157bc:	08 40 62 1e	fcvt	s8, d0
