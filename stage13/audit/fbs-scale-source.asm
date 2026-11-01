D:\Codex\workspaces\2026-10-29\zai\work\stage13-mode\audit\fbs-scale-source.macho:
(__TEXT,__text) section
18f660858:	ff 43 01 d1	sub	sp, sp, #0x50
18f66085c:	e9 23 01 6d	stp	d9, d8, [sp, #0x10]
18f660860:	f6 57 02 a9	stp	x22, x21, [sp, #0x20]
18f660864:	f4 4f 03 a9	stp	x20, x19, [sp, #0x30]
18f660868:	fd 7b 04 a9	stp	x29, x30, [sp, #0x40]
18f66086c:	fd 03 01 91	add	x29, sp, #0x40
18f660870:	3e 93 48 95	bl	0x194885568
18f660874:	f3 03 00 aa	mov	x19, x0
18f660878:	00 02 00 b4	cbz	x0, 0x18f6608b8
18f66087c:	23 00 00 94	bl	0x18f660908
18f660880:	b0 eb 01 94	bl	0x18f6db740
18f660884:	e2 92 48 95	bl	0x19488540c
18f660888:	f4 03 00 aa	mov	x20, x0
18f66088c:	9d ec 01 94	bl	0x18f6dbb00
18f660890:	df 92 48 95	bl	0x19488540c
18f660894:	f5 03 00 aa	mov	x21, x0
18f660898:	16 93 48 95	bl	0x1948854f0
18f66089c:	12 93 48 95	bl	0x1948854e4
18f6608a0:	bf 02 13 eb	cmp	x21, x19
18f6608a4:	e0 00 00 54	b.eq	0x18f6608c0
18f6608a8:	e0 03 13 aa	mov	x0, x19
18f6608ac:	45 00 00 94	bl	0x18f6609c0
18f6608b0:	08 40 62 1e	fcvt	s8, d0
18f6608b4:	0d 00 00 14	b	0x18f6608e8
18f6608b8:	e8 03 27 1e	fmov	s8, wzr
18f6608bc:	0b 00 00 14	b	0x18f6608e8
18f6608c0:	08 f0 a7 52	mov	w8, #0x3f800000
18f6608c4:	e8 0f 00 b9	str	w8, [sp, #0xc]
18f6608c8:	e2 33 00 91	add	x2, sp, #0xc
18f6608cc:	00 00 80 d2	mov	x0, #0x0
18f6608d0:	01 00 80 d2	mov	x1, #0x0
18f6608d4:	03 00 80 d2	mov	x3, #0x0
18f6608d8:	04 00 80 d2	mov	x4, #0x0
18f6608dc:	05 00 80 d2	mov	x5, #0x0
18f6608e0:	90 f0 ff 97	bl	0x18f65cb20
18f6608e4:	e8 0f 40 bd	ldr	s8, [sp, #0xc]
18f6608e8:	f9 92 48 95	bl	0x1948854cc
18f6608ec:	00 41 20 1e	fmov	s0, s8
18f6608f0:	fd 7b 44 a9	ldp	x29, x30, [sp, #0x40]
18f6608f4:	f4 4f 43 a9	ldp	x20, x19, [sp, #0x30]
18f6608f8:	f6 57 42 a9	ldp	x22, x21, [sp, #0x20]
18f6608fc:	e9 23 41 6d	ldp	d9, d8, [sp, #0x10]
18f660900:	ff 43 01 91	add	sp, sp, #0x50
18f660904:	c0 03 5f d6	ret
18f660908:	ff c3 01 d1	sub	sp, sp, #0x70
18f66090c:	f4 4f 05 a9	stp	x20, x19, [sp, #0x50]
18f660910:	fd 7b 06 a9	stp	x29, x30, [sp, #0x60]
18f660914:	fd 83 01 91	add	x29, sp, #0x60
18f660918:	e8 c3 00 91	add	x8, sp, #0x30
18f66091c:	ff 23 03 a9	stp	xzr, x8, [sp, #0x30]
18f660920:	e9 02 00 b0	adrp	x9, 93 ; 0x18f6bd000
18f660924:	20 51 43 fd	ldr	d0, [x9, #0x6a0]
18f660928:	e0 23 00 fd	str	d0, [sp, #0x40]
18f66092c:	ff 27 00 f9	str	xzr, [sp, #0x48]
18f660930:	69 1c 2f b0	adrp	x9, 385933 ; 0x1ed9ed000
18f660934:	29 3d 41 f9	ldr	x9, [x9, #0x278]
18f660938:	e9 27 00 f9	str	x9, [sp, #0x48]
18f66093c:	29 02 00 b5	cbnz	x9, 0x18f660980
18f660940:	49 fe 2d f0	adrp	x9, 376779 ; 0x1eb62b000
18f660944:	29 bd 46 f9	ldr	x9, [x9, #0xd78]
18f660948:	e9 07 00 f9	str	x9, [sp, #0x8]
18f66094c:	e9 02 00 b0	adrp	x9, 93 ; 0x18f6bd000
18f660950:	20 41 43 fd	ldr	d0, [x9, #0x680]
18f660954:	09 01 00 b0	adrp	x9, 33 ; 0x18f681000
