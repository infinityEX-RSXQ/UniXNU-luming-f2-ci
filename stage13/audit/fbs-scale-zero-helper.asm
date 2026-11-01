D:\Codex\workspaces\2026-10-29\zai\work\stage13-mode\audit\fbs-scale-zero-helper.macho:
(__TEXT,__text) section
18f6e545c:	00 c0 60 1e	fabs	d0, d0
18f6e5460:	08 96 e7 d2	mov	x8, #0x3cb0000000000000
18f6e5464:	01 01 67 9e	fmov	d1, x8
18f6e5468:	00 20 61 1e	fcmp	d0, d1
18f6e546c:	e0 57 9f 1a	cset	w0, mi
18f6e5470:	c0 03 5f d6	ret
18f6e5474:	f4 4f be a9	stp	x20, x19, [sp, #-0x20]!
18f6e5478:	fd 7b 01 a9	stp	x29, x30, [sp, #0x10]
18f6e547c:	fd 43 00 91	add	x29, sp, #0x10
18f6e5480:	f3 03 00 aa	mov	x19, x0
18f6e5484:	00 60 00 91	add	x0, x0, #0x18
18f6e5488:	37 84 46 95	bl	0x194886564
18f6e548c:	60 42 00 91	add	x0, x19, #0x10
18f6e5490:	01 00 80 d2	mov	x1, #0x0
18f6e5494:	1e 17 02 94	bl	0x18f76b10c
18f6e5498:	60 22 00 91	add	x0, x19, #0x8
18f6e549c:	01 00 80 d2	mov	x1, #0x0
18f6e54a0:	fd 7b 41 a9	ldp	x29, x30, [sp, #0x10]
18f6e54a4:	f4 4f c2 a8	ldp	x20, x19, [sp], #0x20
18f6e54a8:	19 17 02 14	b	0x18f76b10c
18f6e54ac:	00 d4 e2 7e	fabd	d0, d0, d2
18f6e54b0:	08 96 e7 d2	mov	x8, #0x3cb0000000000000
18f6e54b4:	02 01 67 9e	fmov	d2, x8
18f6e54b8:	00 20 62 1e	fcmp	d0, d2
18f6e54bc:	e8 57 9f 1a	cset	w8, mi
