D:\Codex\workspaces\2026-10-29\zai\work\stage13-mode\audit\ca-preferred-scale-full.macho:
(__TEXT,__text) section
189570760:	fd 7b bf a9	stp	x29, x30, [sp, #-0x10]!
189570764:	fd 03 00 91	mov	x29, sp
189570768:	08 04 40 f9	ldr	x8, [x0, #0x8]
18957076c:	00 21 40 b9	ldr	w0, [x8, #0x20]
189570770:	a0 01 00 35	cbnz	w0, 0x1895707a4
189570774:	09 0d 40 39	ldrb	w9, [x8, #0x3]
189570778:	c9 00 20 37	tbnz	w9, #0x4, 0x189570790
18957077c:	08 0d 40 f9	ldr	x8, [x8, #0x18]
189570780:	1f e1 10 f1	cmp	x8, #0x438
189570784:	28 00 80 52	mov	w8, #0x1
189570788:	00 95 88 9a	cinc	x0, x8, hi
18957078c:	06 00 00 14	b	0x1895707a4
189570790:	40 9e 2e f0	adrp	x0, 381899 ; 0x1e693b000
189570794:	00 00 19 91	add	x0, x0, #0x640
189570798:	00 10 20 1e	fmov	s0, #2.00000000
18957079c:	ee 40 14 95	bl	0x18da80b54
1895707a0:	00 00 39 9e	fcvtzu	x0, s0
1895707a4:	fd 7b c1 a8	ldp	x29, x30, [sp], #0x10
1895707a8:	c0 03 5f d6	ret
1895707ac:	ff 03 03 d1	sub	sp, sp, #0xc0
1895707b0:	e9 23 05 6d	stp	d9, d8, [sp, #0x50]
1895707b4:	fc 6f 06 a9	stp	x28, x27, [sp, #0x60]
1895707b8:	fa 67 07 a9	stp	x26, x25, [sp, #0x70]
1895707bc:	f8 5f 08 a9	stp	x24, x23, [sp, #0x80]
1895707c0:	f6 57 09 a9	stp	x22, x21, [sp, #0x90]
1895707c4:	f4 4f 0a a9	stp	x20, x19, [sp, #0xa0]
1895707c8:	fd 7b 0b a9	stp	x29, x30, [sp, #0xb0]
1895707cc:	fd c3 02 91	add	x29, sp, #0xb0
