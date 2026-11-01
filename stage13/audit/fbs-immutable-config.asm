D:\Codex\workspaces\2026-10-29\zai\work\stage13-mode\audit\fbs-immutable-config.macho:
(__TEXT,__text) section
19f3cf710:	ef 3b b6 6d	stp	d15, d14, [sp, #-0xa0]!
19f3cf714:	ed 33 01 6d	stp	d13, d12, [sp, #0x10]
19f3cf718:	eb 2b 02 6d	stp	d11, d10, [sp, #0x20]
19f3cf71c:	e9 23 03 6d	stp	d9, d8, [sp, #0x30]
19f3cf720:	fc 6f 04 a9	stp	x28, x27, [sp, #0x40]
19f3cf724:	fa 67 05 a9	stp	x26, x25, [sp, #0x50]
19f3cf728:	f8 5f 06 a9	stp	x24, x23, [sp, #0x60]
19f3cf72c:	f6 57 07 a9	stp	x22, x21, [sp, #0x70]
19f3cf730:	f4 4f 08 a9	stp	x20, x19, [sp, #0x80]
19f3cf734:	fd 7b 09 a9	stp	x29, x30, [sp, #0x90]
19f3cf738:	fd 43 02 91	add	x29, sp, #0x90
19f3cf73c:	ff 03 07 d1	sub	sp, sp, #0x1c0
19f3cf740:	f7 03 04 aa	mov	x23, x4
19f3cf744:	f5 03 03 aa	mov	x21, x3
19f3cf748:	f6 03 02 aa	mov	x22, x2
19f3cf74c:	e1 4f 00 f9	str	x1, [sp, #0x98]
19f3cf750:	fb 03 00 aa	mov	x27, x0
19f3cf754:	e8 12 26 90	adrp	x8, 311900 ; 0x1eb62b000
19f3cf758:	08 cd 47 f9	ldr	x8, [x8, #0xf98]
19f3cf75c:	08 01 40 f9	ldr	x8, [x8]
19f3cf760:	a8 03 16 f8	stur	x8, [x29, #-0xa0]
19f3cf764:	ff 22 24 94	bl	0x19fcd8360
19f3cf768:	fc 03 00 aa	mov	x28, x0
19f3cf76c:	fa 22 24 94	bl	0x19fcd8354
19f3cf770:	f4 03 00 aa	mov	x20, x0
19f3cf774:	e0 03 1c aa	mov	x0, x28
19f3cf778:	0a a0 02 94	bl	0x19f4777a0
19f3cf77c:	f8 03 00 aa	mov	x24, x0
19f3cf780:	e0 03 1c aa	mov	x0, x28
19f3cf784:	3f 8a 02 94	bl	0x19f472080
19f3cf788:	f3 03 00 aa	mov	x19, x0
19f3cf78c:	1f 04 00 71	cmp	w0, #0x1
19f3cf790:	f4 5b 00 f9	str	x20, [sp, #0xb0]
19f3cf794:	f6 d7 06 a9	stp	x22, x21, [sp, #0x68]
19f3cf798:	f7 af 00 b9	str	w23, [sp, #0xac]
19f3cf79c:	f8 53 00 f9	str	x24, [sp, #0xa0]
19f3cf7a0:	61 00 00 54	b.ne	0x19f3cf7ac
19f3cf7a4:	14 00 80 d2	mov	x20, #0x0
19f3cf7a8:	13 00 00 14	b	0x19f3cf7f4
19f3cf7ac:	28 00 80 52	mov	w8, #0x1
19f3cf7b0:	69 00 80 52	mov	w9, #0x3
19f3cf7b4:	ca 00 80 52	mov	w10, #0x6
19f3cf7b8:	8b 00 80 52	mov	w11, #0x4
19f3cf7bc:	ac 00 80 52	mov	w12, #0x5
19f3cf7c0:	1f 03 70 f2	tst	x24, #0x10000
19f3cf7c4:	ed 00 80 52	mov	w13, #0x7
19f3cf7c8:	ad 11 9f da	csinv	x13, x13, xzr, ne
19f3cf7cc:	1f 03 1c 72	tst	w24, #0x10
19f3cf7d0:	8c 11 8d 9a	csel	x12, x12, x13, ne
19f3cf7d4:	1f 03 1d 72	tst	w24, #0x8
19f3cf7d8:	6b 11 8c 9a	csel	x11, x11, x12, ne
19f3cf7dc:	1f 03 1a 72	tst	w24, #0x40
19f3cf7e0:	4a 11 8b 9a	csel	x10, x10, x11, ne
19f3cf7e4:	1f 03 1b 72	tst	w24, #0x20
19f3cf7e8:	29 11 8a 9a	csel	x9, x9, x10, ne
19f3cf7ec:	1f 03 1e 72	tst	w24, #0x4
19f3cf7f0:	14 11 89 9a	csel	x20, x8, x9, ne
19f3cf7f4:	7f 06 00 71	cmp	w19, #0x1
19f3cf7f8:	f5 17 9f 1a	cset	w21, eq
19f3cf7fc:	e0 03 1c aa	mov	x0, x28
19f3cf800:	48 8a 02 94	bl	0x19f472120
19f3cf804:	1f 0c 00 f1	cmp	x0, #0x3
19f3cf808:	68 00 80 52	mov	w8, #0x3
19f3cf80c:	16 30 88 9a	csel	x22, x0, x8, lo
19f3cf810:	68 37 24 f0	adrp	x8, 296687 ; 0x1e7abe000
19f3cf814:	00 3d 44 f9	ldr	x0, [x8, #0x878]
19f3cf818:	39 22 24 94	bl	0x19fcd80fc
19f3cf81c:	f7 03 00 aa	mov	x23, x0
19f3cf820:	e0 03 1c aa	mov	x0, x28
19f3cf824:	b7 87 02 94	bl	0x19f471700
19f3cf828:	f8 03 00 aa	mov	x24, x0
19f3cf82c:	e0 03 1c aa	mov	x0, x28
19f3cf830:	64 96 02 94	bl	0x19f4751c0
19f3cf834:	f9 03 00 aa	mov	x25, x0
19f3cf838:	e0 03 1c aa	mov	x0, x28
19f3cf83c:	a9 90 02 94	bl	0x19f473ae0
19f3cf840:	ff 0f 00 f9	str	xzr, [sp, #0x18]
19f3cf844:	ff 43 00 39	strb	wzr, [sp, #0x10]
19f3cf848:	ff 07 00 f9	str	xzr, [sp, #0x8]
19f3cf84c:	e0 03 00 39	strb	w0, [sp]
19f3cf850:	e0 03 17 aa	mov	x0, x23
19f3cf854:	e2 03 14 aa	mov	x2, x20
19f3cf858:	e3 03 15 aa	mov	x3, x21
19f3cf85c:	e4 03 13 aa	mov	x4, x19
19f3cf860:	e5 03 16 aa	mov	x5, x22
19f3cf864:	e6 03 18 aa	mov	x6, x24
19f3cf868:	e7 03 19 aa	mov	x7, x25
19f3cf86c:	25 7e 02 94	bl	0x19f46f100
19f3cf870:	f5 03 00 aa	mov	x21, x0
19f3cf874:	e0 03 1c aa	mov	x0, x28
19f3cf878:	9a 93 02 94	bl	0x19f4746e0
19f3cf87c:	38 22 24 94	bl	0x19fcd815c
19f3cf880:	f4 03 00 aa	mov	x20, x0
19f3cf884:	3f 0c 00 94	bl	0x19f3d2980
19f3cf888:	f7 03 00 aa	mov	x23, x0
19f3cf88c:	73 22 24 94	bl	0x19fcd8258
19f3cf890:	7f 06 00 71	cmp	w19, #0x1
19f3cf894:	a0 01 00 54	b.eq	0x19f3cf8c8
19f3cf898:	e0 03 1c aa	mov	x0, x28
19f3cf89c:	81 88 02 94	bl	0x19f471aa0
19f3cf8a0:	2f 22 24 94	bl	0x19fcd815c
19f3cf8a4:	f3 03 00 aa	mov	x19, x0
19f3cf8a8:	36 0c 00 94	bl	0x19f3d2980
19f3cf8ac:	e8 02 00 cb	sub	x8, x23, x0
19f3cf8b0:	08 11 00 91	add	x8, x8, #0x4
19f3cf8b4:	09 05 40 92	and	x9, x8, #0x3
19f3cf8b8:	e8 03 08 eb	negs	x8, x8
19f3cf8bc:	08 05 40 92	and	x8, x8, #0x3
19f3cf8c0:	37 45 88 da	csneg	x23, x9, x8, mi
19f3cf8c4:	62 22 24 94	bl	0x19fcd824c
19f3cf8c8:	e0 03 15 aa	mov	x0, x21
19f3cf8cc:	cd 90 02 94	bl	0x19f473c00
19f3cf8d0:	e8 03 67 9e	fmov	d8, xzr
19f3cf8d4:	80 00 00 37	tbnz	w0, #0x0, 0x19f3cf8e4
19f3cf8d8:	e0 03 1c aa	mov	x0, x28
19f3cf8dc:	28 20 24 94	bl	0x19fcd797c
19f3cf8e0:	08 c0 22 1e	fcvt	d8, s0
19f3cf8e4:	e0 03 1c aa	mov	x0, x28
19f3cf8e8:	66 88 02 94	bl	0x19f471a80
19f3cf8ec:	1c 22 24 94	bl	0x19fcd815c
19f3cf8f0:	e0 77 00 f9	str	x0, [sp, #0xe8]
19f3cf8f4:	e0 03 1c aa	mov	x0, x28
19f3cf8f8:	da 95 02 94	bl	0x19f475060
19f3cf8fc:	18 22 24 94	bl	0x19fcd815c
19f3cf900:	e0 73 00 f9	str	x0, [sp, #0xe0]
19f3cf904:	e0 03 1c aa	mov	x0, x28
19f3cf908:	be 84 02 94	bl	0x19f470c00
19f3cf90c:	14 22 24 94	bl	0x19fcd815c
19f3cf910:	00 e4 00 4f	movi.16b	v0, #0x0
19f3cf914:	e0 83 07 ad	stp	q0, q0, [sp, #0xf0]
19f3cf918:	e0 83 08 ad	stp	q0, q0, [sp, #0x110]
19f3cf91c:	70 22 24 94	bl	0x19fcd82dc
19f3cf920:	f8 03 00 aa	mov	x24, x0
19f3cf924:	e2 c3 03 91	add	x2, sp, #0xf0
19f3cf928:	e3 c3 04 91	add	x3, sp, #0x130
19f3cf92c:	04 02 80 52	mov	w4, #0x10
19f3cf930:	ec 87 02 94	bl	0x19f4718e0
19f3cf934:	f5 ef 0b a9	stp	x21, x27, [sp, #0xb8]
19f3cf938:	f8 6b 00 f9	str	x24, [sp, #0xd0]
19f3cf93c:	20 09 00 b4	cbz	x0, 0x19f3cfa60
19f3cf940:	fa 03 00 aa	mov	x26, x0
19f3cf944:	fc 4b 00 f9	str	x28, [sp, #0x90]
19f3cf948:	ff 6f 00 f9	str	xzr, [sp, #0xd8]
19f3cf94c:	ff 67 00 f9	str	xzr, [sp, #0xc8]
19f3cf950:	13 00 80 d2	mov	x19, #0x0
19f3cf954:	e8 83 40 f9	ldr	x8, [sp, #0x100]
19f3cf958:	16 01 40 f9	ldr	x22, [x8]
19f3cf95c:	7b 37 24 f0	adrp	x27, 296687 ; 0x1e7abe000
19f3cf960:	1c 00 80 d2	mov	x28, #0x0
19f3cf964:	e8 83 40 f9	ldr	x8, [sp, #0x100]
19f3cf968:	08 01 40 f9	ldr	x8, [x8]
19f3cf96c:	1f 01 16 eb	cmp	x8, x22
19f3cf970:	60 00 00 54	b.eq	0x19f3cf97c
19f3cf974:	e0 6b 40 f9	ldr	x0, [sp, #0xd0]
19f3cf978:	05 22 24 94	bl	0x19fcd818c
19f3cf97c:	e8 7f 40 f9	ldr	x8, [sp, #0xf8]
19f3cf980:	14 79 7c f8	ldr	x20, [x8, x28, lsl #3]
19f3cf984:	60 3b 44 f9	ldr	x0, [x27, #0x870]
19f3cf988:	dd 21 24 94	bl	0x19fcd80fc
19f3cf98c:	e2 03 14 aa	mov	x2, x20
19f3cf990:	00 41 60 1e	fmov	d0, d8
19f3cf994:	e3 03 17 aa	mov	x3, x23
19f3cf998:	4a 7d 02 94	bl	0x19f46eec0
19f3cf99c:	f9 03 00 aa	mov	x25, x0
19f3cf9a0:	e0 03 14 aa	mov	x0, x20
19f3cf9a4:	e2 77 40 f9	ldr	x2, [sp, #0xe8]
19f3cf9a8:	36 90 02 94	bl	0x19f473a80
19f3cf9ac:	f8 03 00 aa	mov	x24, x0
19f3cf9b0:	e0 03 14 aa	mov	x0, x20
19f3cf9b4:	e2 73 40 f9	ldr	x2, [sp, #0xe0]
19f3cf9b8:	32 90 02 94	bl	0x19f473a80
19f3cf9bc:	f5 03 00 aa	mov	x21, x0
19f3cf9c0:	f8 00 00 37	tbnz	w24, #0x0, 0x19f3cf9dc
19f3cf9c4:	d5 00 00 35	cbnz	w21, 0x19f3cf9dc
19f3cf9c8:	e0 6f 40 f9	ldr	x0, [sp, #0xd8]
19f3cf9cc:	c0 01 00 b4	cbz	x0, 0x19f3cfa04
19f3cf9d0:	e2 03 19 aa	mov	x2, x25
19f3cf9d4:	93 81 02 94	bl	0x19f470020
19f3cf9d8:	11 00 00 14	b	0x19f3cfa1c
19f3cf9dc:	98 00 00 34	cbz	w24, 0x19f3cf9ec
19f3cf9e0:	b3 19 00 b5	cbnz	x19, 0x19f3cfd14
19f3cf9e4:	68 22 24 94	bl	0x19fcd8384
19f3cf9e8:	f3 03 00 aa	mov	x19, x0
19f3cf9ec:	95 01 00 34	cbz	w21, 0x19f3cfa1c
19f3cf9f0:	e8 67 40 f9	ldr	x8, [sp, #0xc8]
19f3cf9f4:	48 1c 00 b5	cbnz	x8, 0x19f3cfd7c
19f3cf9f8:	63 22 24 94	bl	0x19fcd8384
19f3cf9fc:	e0 67 00 f9	str	x0, [sp, #0xc8]
19f3cfa00:	07 00 00 14	b	0x19f3cfa1c
19f3cfa04:	68 37 24 f0	adrp	x8, 296687 ; 0x1e7abe000
19f3cfa08:	00 05 43 f9	ldr	x0, [x8, #0x608]
19f3cfa0c:	e2 03 19 aa	mov	x2, x25
19f3cfa10:	94 9d 02 94	bl	0x19f477060
19f3cfa14:	d2 21 24 94	bl	0x19fcd815c
19f3cfa18:	e0 6f 00 f9	str	x0, [sp, #0xd8]
19f3cfa1c:	1e 22 24 94	bl	0x19fcd8294
19f3cfa20:	9c 07 00 91	add	x28, x28, #0x1
19f3cfa24:	5f 03 1c eb	cmp	x26, x28
19f3cfa28:	e1 f9 ff 54	b.ne	0x19f3cf964
19f3cfa2c:	e2 c3 03 91	add	x2, sp, #0xf0
19f3cfa30:	e3 c3 04 91	add	x3, sp, #0x130
19f3cfa34:	e0 6b 40 f9	ldr	x0, [sp, #0xd0]
19f3cfa38:	04 02 80 52	mov	w4, #0x10
19f3cfa3c:	a9 87 02 94	bl	0x19f4718e0
19f3cfa40:	fa 03 00 aa	mov	x26, x0
19f3cfa44:	e0 f8 ff b5	cbnz	x0, 0x19f3cf960
19f3cfa48:	f8 6b 40 f9	ldr	x24, [sp, #0xd0]
19f3cfa4c:	0f 22 24 94	bl	0x19fcd8288
19f3cfa50:	f3 00 00 b4	cbz	x19, 0x19f3cfa6c
19f3cfa54:	fc 4b 40 f9	ldr	x28, [sp, #0x90]
19f3cfa58:	f6 67 40 f9	ldr	x22, [sp, #0xc8]
19f3cfa5c:	19 00 00 14	b	0x19f3cfac0
19f3cfa60:	0a 22 24 94	bl	0x19fcd8288
19f3cfa64:	09 00 80 d2	mov	x9, #0x0
19f3cfa68:	06 00 00 14	b	0x19f3cfa80
19f3cfa6c:	f5 ef 4b a9	ldp	x21, x27, [sp, #0xb8]
19f3cfa70:	fc 4b 40 f9	ldr	x28, [sp, #0x90]
19f3cfa74:	e9 6f 40 f9	ldr	x9, [sp, #0xd8]
19f3cfa78:	ea 67 40 f9	ldr	x10, [sp, #0xc8]
19f3cfa7c:	8a 1b 00 b5	cbnz	x10, 0x19f3cfdec
19f3cfa80:	e9 6f 00 f9	str	x9, [sp, #0xd8]
19f3cfa84:	e0 03 09 aa	mov	x0, x9
19f3cfa88:	8e 87 02 94	bl	0x19f4718c0
19f3cfa8c:	c0 1a 00 b5	cbnz	x0, 0x19f3cfde4
19f3cfa90:	e0 03 15 aa	mov	x0, x21
19f3cfa94:	5b 90 02 94	bl	0x19f473c00
19f3cfa98:	00 01 00 34	cbz	w0, 0x19f3cfab8
19f3cfa9c:	68 37 24 f0	adrp	x8, 296687 ; 0x1e7abe000
19f3cfaa0:	00 39 44 f9	ldr	x0, [x8, #0x870]
19f3cfaa4:	77 7c 02 94	bl	0x19f46ec80
19f3cfaa8:	ad 21 24 94	bl	0x19fcd815c
19f3cfaac:	f3 03 00 aa	mov	x19, x0
19f3cfab0:	16 00 80 d2	mov	x22, #0x0
19f3cfab4:	03 00 00 14	b	0x19f3cfac0
19f3cfab8:	16 00 80 d2	mov	x22, #0x0
19f3cfabc:	13 00 80 d2	mov	x19, #0x0
19f3cfac0:	e0 03 1c aa	mov	x0, x28
19f3cfac4:	a7 8b 02 94	bl	0x19f472960
19f3cfac8:	f4 fa 7e 92	and	x20, x23, #0xfffffffffffffffd
19f3cfacc:	9f 06 00 f1	cmp	x20, #0x1
19f3cfad0:	6c 0c 62 1e	fcsel	d12, d3, d2, eq
19f3cfad4:	4d 0c 63 1e	fcsel	d13, d2, d3, eq
19f3cfad8:	e0 03 13 aa	mov	x0, x19
19f3cfadc:	31 95 02 94	bl	0x19f474fa0
19f3cfae0:	0e 40 60 1e	fmov	d14, d0
19f3cfae4:	e0 03 1c aa	mov	x0, x28
19f3cfae8:	86 84 02 94	bl	0x19f470d00
19f3cfaec:	0f 40 60 1e	fmov	d15, d0
19f3cfaf0:	29 40 60 1e	fmov	d9, d1
19f3cfaf4:	4a 40 60 1e	fmov	d10, d2
19f3cfaf8:	6b 40 60 1e	fmov	d11, d3
19f3cfafc:	c0 41 60 1e	fmov	d0, d14
19f3cfb00:	14 20 24 94	bl	0x19fcd7b50
19f3cfb04:	ed 33 09 6d	stp	d13, d12, [sp, #0x90]
19f3cfb08:	e9 3f 08 6d	stp	d9, d15, [sp, #0x80]
19f3cfb0c:	c0 00 00 34	cbz	w0, 0x19f3cfb24
19f3cfb10:	68 13 26 f0	adrp	x8, 311919 ; 0x1eb63e000
19f3cfb14:	08 55 42 f9	ldr	x8, [x8, #0x4a8]
19f3cfb18:	08 25 40 6d	ldp	d8, d9, [x8]
19f3cfb1c:	0c 35 41 6d	ldp	d12, d13, [x8, #0x10]
19f3cfb20:	0a 00 00 14	b	0x19f3cfb48
19f3cfb24:	e8 19 6e 1e	fdiv	d8, d15, d14
19f3cfb28:	29 19 6e 1e	fdiv	d9, d9, d14
19f3cfb2c:	9f 06 00 f1	cmp	x20, #0x1
19f3cfb30:	81 00 00 54	b.ne	0x19f3cfb40
19f3cfb34:	6c 19 6e 1e	fdiv	d12, d11, d14
19f3cfb38:	4d 19 6e 1e	fdiv	d13, d10, d14
19f3cfb3c:	03 00 00 14	b	0x19f3cfb48
19f3cfb40:	4c 19 6e 1e	fdiv	d12, d10, d14
19f3cfb44:	6d 19 6e 1e	fdiv	d13, d11, d14
19f3cfb48:	e0 03 1c aa	mov	x0, x28
19f3cfb4c:	f5 9f 02 94	bl	0x19f477b20
19f3cfb50:	83 21 24 94	bl	0x19fcd815c
19f3cfb54:	fb 03 00 aa	mov	x27, x0
19f3cfb58:	e0 03 1c aa	mov	x0, x28
19f3cfb5c:	d9 92 02 94	bl	0x19f4746c0
19f3cfb60:	7f 21 24 94	bl	0x19fcd815c
19f3cfb64:	fa 03 00 aa	mov	x26, x0
19f3cfb68:	e0 03 1c aa	mov	x0, x28
19f3cfb6c:	f5 88 02 94	bl	0x19f471f40
