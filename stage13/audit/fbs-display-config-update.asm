D:\Codex\workspaces\2026-10-29\zai\work\stage13-mode\audit\fbs-display-config-update.macho:
(__TEXT,__text) section
19f3df834:	ff 83 02 d1	sub	sp, sp, #0xa0
19f3df838:	fc 6f 04 a9	stp	x28, x27, [sp, #0x40]
19f3df83c:	fa 67 05 a9	stp	x26, x25, [sp, #0x50]
19f3df840:	f8 5f 06 a9	stp	x24, x23, [sp, #0x60]
19f3df844:	f6 57 07 a9	stp	x22, x21, [sp, #0x70]
19f3df848:	f4 4f 08 a9	stp	x20, x19, [sp, #0x80]
19f3df84c:	fd 7b 09 a9	stp	x29, x30, [sp, #0x90]
19f3df850:	fd 43 02 91	add	x29, sp, #0x90
19f3df854:	68 12 26 90	adrp	x8, 311884 ; 0x1eb62b000
19f3df858:	08 cd 47 f9	ldr	x8, [x8, #0xf98]
19f3df85c:	08 01 40 f9	ldr	x8, [x8]
19f3df860:	e8 1f 00 f9	str	x8, [sp, #0x38]
19f3df864:	00 1d 00 b4	cbz	x0, 0x19f3dfc04
19f3df868:	f9 03 02 aa	mov	x25, x2
19f3df86c:	f5 03 01 aa	mov	x21, x1
19f3df870:	f3 03 00 aa	mov	x19, x0
19f3df874:	00 04 40 f9	ldr	x0, [x0, #0x8]
19f3df878:	8a 4d 02 94	bl	0x19f472ea0
19f3df87c:	f4 03 00 aa	mov	x20, x0
19f3df880:	76 62 01 91	add	x22, x19, #0x58
19f3df884:	e0 03 16 aa	mov	x0, x22
19f3df888:	04 e3 23 94	bl	0x19fcd8498
19f3df88c:	68 f6 41 39	ldrb	w8, [x19, #0x7d]
19f3df890:	48 1b 00 35	cbnz	w8, 0x19f3dfbf8
19f3df894:	68 ee 41 39	ldrb	w8, [x19, #0x7b]
19f3df898:	48 00 00 35	cbnz	w8, 0x19f3df8a0
19f3df89c:	f5 1a 00 34	cbz	w21, 0x19f3dfbf8
19f3df8a0:	e8 13 f2 90	adrp	x8, -114052 ; 0x18365b000
19f3df8a4:	1a 85 1b 91	add	x26, x8, #0x6e1
19f3df8a8:	68 e2 41 39	ldrb	w8, [x19, #0x78]
19f3df8ac:	28 07 00 34	cbz	w8, 0x19f3df990
19f3df8b0:	e8 36 24 f0	adrp	x8, 296671 ; 0x1e7abe000
19f3df8b4:	00 1d 44 f9	ldr	x0, [x8, #0x838]
19f3df8b8:	11 e2 23 94	bl	0x19fcd80fc
19f3df8bc:	63 06 40 f9	ldr	x3, [x19, #0x8]
19f3df8c0:	e2 03 14 aa	mov	x2, x20
19f3df8c4:	24 00 80 52	mov	w4, #0x1
19f3df8c8:	ce 3d 02 94	bl	0x19f46f000
19f3df8cc:	f7 03 00 aa	mov	x23, x0
19f3df8d0:	cc 50 02 94	bl	0x19f473c00
19f3df8d4:	80 1d 00 36	tbz	w0, #0x0, 0x19f3dfc84
19f3df8d8:	e0 03 13 aa	mov	x0, x19
19f3df8dc:	e1 03 17 aa	mov	x1, x23
19f3df8e0:	4d 01 00 94	bl	0x19f3dfe14
19f3df8e4:	68 6e 40 b9	ldr	w8, [x19, #0x6c]
19f3df8e8:	1f 11 00 71	cmp	w8, #0x4
19f3df8ec:	e8 17 00 54	b.hi	0x19f3dfbe8
19f3df8f0:	69 02 00 b0	adrp	x9, 77 ; 0x19f42c000
19f3df8f4:	29 d1 20 91	add	x9, x9, #0x834
19f3df8f8:	0a 00 00 10	adr	x10, #0
19f3df8fc:	2b 79 a8 b8	ldrsw	x11, [x9, x8, lsl #2]
19f3df900:	4a 01 0b 8b	add	x10, x10, x11
19f3df904:	40 01 1f d6	br	x10
19f3df908:	1a e0 23 94	bl	0x19fcd7970
19f3df90c:	14 e2 23 94	bl	0x19fcd815c
19f3df910:	f8 03 00 aa	mov	x24, x0
19f3df914:	01 00 80 52	mov	w1, #0x0
19f3df918:	d7 e2 23 94	bl	0x19fcd8474
19f3df91c:	20 03 00 34	cbz	w0, 0x19f3df980
19f3df920:	7a ee 4c 29	ldp	w26, w27, [x19, #0x64]
19f3df924:	60 12 40 f9	ldr	x0, [x19, #0x20]
19f3df928:	5e 5f 02 94	bl	0x19f4776a0
19f3df92c:	0c e2 23 94	bl	0x19fcd815c
19f3df930:	f9 03 00 aa	mov	x25, x0
19f3df934:	48 60 80 52	mov	w8, #0x302
19f3df938:	08 80 a0 72	movk	w8, #0x400, lsl #16
19f3df93c:	e8 6b 04 29	stp	w8, w26, [sp, #0x20]
19f3df940:	08 80 80 52	mov	w8, #0x400
19f3df944:	e8 53 00 79	strh	w8, [sp, #0x28]
19f3df948:	fb a3 02 b8	stur	w27, [sp, #0x2a]
19f3df94c:	48 08 81 52	mov	w8, #0x842
19f3df950:	e8 5f 00 79	strh	w8, [sp, #0x2e]
19f3df954:	e0 1b 00 f9	str	x0, [sp, #0x30]
19f3df958:	00 ff ff d0	adrp	x0, -30 ; 0x19f3c1000
19f3df95c:	00 00 00 91	add	x0, x0, #0x0
19f3df960:	c3 03 00 b0	adrp	x3, 121 ; 0x19f458000
19f3df964:	63 88 05 91	add	x3, x3, #0x162
19f3df968:	e4 83 00 91	add	x4, sp, #0x20
19f3df96c:	e1 03 18 aa	mov	x1, x24
19f3df970:	02 00 80 52	mov	w2, #0x0
19f3df974:	05 03 80 52	mov	w5, #0x18
19f3df978:	6f e1 23 94	bl	0x19fcd7f34
19f3df97c:	46 e2 23 94	bl	0x19fcd8294
19f3df980:	42 e2 23 94	bl	0x19fcd8288
19f3df984:	e0 03 13 aa	mov	x0, x19
19f3df988:	c3 01 00 94	bl	0x19f3e0094
19f3df98c:	97 00 00 14	b	0x19f3dfbe8
19f3df990:	e0 03 14 aa	mov	x0, x20
19f3df994:	83 5f 02 94	bl	0x19f4777a0
19f3df998:	fb 03 00 aa	mov	x27, x0
19f3df99c:	e0 03 14 aa	mov	x0, x20
19f3df9a0:	98 44 02 94	bl	0x19f470c00
19f3df9a4:	ee e1 23 94	bl	0x19fcd815c
19f3df9a8:	f7 03 00 aa	mov	x23, x0
19f3df9ac:	68 12 40 f9	ldr	x8, [x19, #0x20]
19f3df9b0:	8d e2 23 94	bl	0x19fcd83e4
19f3df9b4:	f8 03 00 aa	mov	x24, x0
19f3df9b8:	1b 04 00 b4	cbz	x27, 0x19f3dfa38
19f3df9bc:	e0 03 17 aa	mov	x0, x23
19f3df9c0:	c0 47 02 94	bl	0x19f4718c0
19f3df9c4:	a0 03 00 b4	cbz	x0, 0x19f3dfa38
19f3df9c8:	d8 04 00 b4	cbz	x24, 0x19f3dfa60
19f3df9cc:	f7 0f 00 f9	str	x23, [sp, #0x18]
19f3df9d0:	e0 03 18 aa	mov	x0, x24
19f3df9d4:	db 4c 02 94	bl	0x19f472d40
19f3df9d8:	e1 e1 23 94	bl	0x19fcd815c
19f3df9dc:	fc 03 00 aa	mov	x28, x0
19f3df9e0:	48 47 02 94	bl	0x19f471700
19f3df9e4:	f7 03 00 aa	mov	x23, x0
19f3df9e8:	e0 03 14 aa	mov	x0, x20
19f3df9ec:	45 47 02 94	bl	0x19f471700
19f3df9f0:	ff 02 00 6b	cmp	w23, w0
19f3df9f4:	21 03 00 54	b.ne	0x19f3dfa58
19f3df9f8:	e0 03 18 aa	mov	x0, x24
19f3df9fc:	c1 58 02 94	bl	0x19f475d00
19f3dfa00:	f7 03 00 aa	mov	x23, x0
19f3dfa04:	e0 03 14 aa	mov	x0, x20
19f3dfa08:	be 58 02 94	bl	0x19f475d00
19f3dfa0c:	ff 02 00 6b	cmp	w23, w0
19f3dfa10:	41 02 00 54	b.ne	0x19f3dfa58
19f3dfa14:	e0 03 18 aa	mov	x0, x24
19f3dfa18:	6a 5f 02 94	bl	0x19f4777c0
19f3dfa1c:	f7 03 00 aa	mov	x23, x0
19f3dfa20:	26 e2 23 94	bl	0x19fcd82b8
19f3dfa24:	ff 02 1b eb	cmp	x23, x27
19f3dfa28:	f7 0f 40 f9	ldr	x23, [sp, #0x18]
19f3dfa2c:	a1 01 00 54	b.ne	0x19f3dfa60
19f3dfa30:	99 03 00 34	cbz	w25, 0x19f3dfaa0
19f3dfa34:	0b 00 00 14	b	0x19f3dfa60
19f3dfa38:	e0 03 13 aa	mov	x0, x19
19f3dfa3c:	01 00 80 d2	mov	x1, #0x0
19f3dfa40:	f5 00 00 94	bl	0x19f3dfe14
19f3dfa44:	17 00 00 14	b	0x19f3dfaa0
19f3dfa48:	e0 03 13 aa	mov	x0, x19
19f3dfa4c:	e1 03 19 aa	mov	x1, x25
19f3dfa50:	85 34 01 94	bl	0x19f42cc64
19f3dfa54:	65 00 00 14	b	0x19f3dfbe8
19f3dfa58:	18 e2 23 94	bl	0x19fcd82b8
19f3dfa5c:	f7 0f 40 f9	ldr	x23, [sp, #0x18]
19f3dfa60:	e8 36 24 f0	adrp	x8, 296671 ; 0x1e7abe000
19f3dfa64:	00 1d 44 f9	ldr	x0, [x8, #0x838]
19f3dfa68:	a5 e1 23 94	bl	0x19fcd80fc
19f3dfa6c:	63 06 40 f9	ldr	x3, [x19, #0x8]
19f3dfa70:	e2 03 14 aa	mov	x2, x20
19f3dfa74:	24 00 80 52	mov	w4, #0x1
19f3dfa78:	62 3d 02 94	bl	0x19f46f000
19f3dfa7c:	fb 03 00 aa	mov	x27, x0
19f3dfa80:	00 13 00 b4	cbz	x0, 0x19f3dfce0
19f3dfa84:	e0 03 1b aa	mov	x0, x27
19f3dfa88:	5e 50 02 94	bl	0x19f473c00
19f3dfa8c:	a0 12 00 35	cbnz	w0, 0x19f3dfce0
19f3dfa90:	e0 03 13 aa	mov	x0, x19
19f3dfa94:	e1 03 1b aa	mov	x1, x27
19f3dfa98:	df 00 00 94	bl	0x19f3dfe14
19f3dfa9c:	04 e2 23 94	bl	0x19fcd82ac
19f3dfaa0:	60 12 40 f9	ldr	x0, [x19, #0x20]
19f3dfaa4:	60 00 00 b4	cbz	x0, 0x19f3dfab0
19f3dfaa8:	36 50 02 94	bl	0x19f473b80
19f3dfaac:	c0 00 00 36	tbz	w0, #0x0, 0x19f3dfac4
19f3dfab0:	68 6e 40 b9	ldr	w8, [x19, #0x6c]
19f3dfab4:	08 01 1f 32	orr	w8, w8, #0x2
19f3dfab8:	1f 0d 00 71	cmp	w8, #0x3
19f3dfabc:	a0 08 00 54	b.eq	0x19f3dfbd0
19f3dfac0:	49 00 00 14	b	0x19f3dfbe4
19f3dfac4:	68 6e 40 b9	ldr	w8, [x19, #0x6c]
19f3dfac8:	1f 0d 00 71	cmp	w8, #0x3
19f3dfacc:	20 02 00 54	b.eq	0x19f3dfb10
19f3dfad0:	1f 05 00 71	cmp	w8, #0x1
19f3dfad4:	e0 01 00 54	b.eq	0x19f3dfb10
19f3dfad8:	68 08 00 35	cbnz	w8, 0x19f3dfbe4
19f3dfadc:	68 f2 41 39	ldrb	w8, [x19, #0x7c]
19f3dfae0:	a8 00 00 35	cbnz	w8, 0x19f3dfaf4
19f3dfae4:	60 12 40 f9	ldr	x0, [x19, #0x20]
19f3dfae8:	e6 5f 02 94	bl	0x19f477a80
19f3dfaec:	1f 1c 00 f1	cmp	x0, #0x7
19f3dfaf0:	a0 07 00 54	b.eq	0x19f3dfbe4
19f3dfaf4:	e0 03 13 aa	mov	x0, x19
19f3dfaf8:	67 01 00 94	bl	0x19f3e0094
19f3dfafc:	68 12 40 f9	ldr	x8, [x19, #0x20]
19f3dfb00:	39 e2 23 94	bl	0x19fcd83e4
19f3dfb04:	68 16 40 f9	ldr	x8, [x19, #0x28]
19f3dfb08:	60 16 00 f9	str	x0, [x19, #0x28]
19f3dfb0c:	35 00 00 14	b	0x19f3dfbe0
19f3dfb10:	60 16 40 f9	ldr	x0, [x19, #0x28]
19f3dfb14:	8b 4c 02 94	bl	0x19f472d40
19f3dfb18:	91 e1 23 94	bl	0x19fcd815c
19f3dfb1c:	fa 03 00 aa	mov	x26, x0
19f3dfb20:	60 12 40 f9	ldr	x0, [x19, #0x20]
19f3dfb24:	87 4c 02 94	bl	0x19f472d40
19f3dfb28:	8d e1 23 94	bl	0x19fcd815c
19f3dfb2c:	fb 03 00 aa	mov	x27, x0
19f3dfb30:	e0 03 1a aa	mov	x0, x26
19f3dfb34:	e1 03 1b aa	mov	x1, x27
19f3dfb38:	f4 df 23 94	bl	0x19fcd7b08
19f3dfb3c:	60 04 00 34	cbz	w0, 0x19f3dfbc8
19f3dfb40:	60 16 40 f9	ldr	x0, [x19, #0x28]
19f3dfb44:	07 4c 02 94	bl	0x19f472b60
19f3dfb48:	85 e1 23 94	bl	0x19fcd815c
19f3dfb4c:	fc 03 00 aa	mov	x28, x0
19f3dfb50:	60 12 40 f9	ldr	x0, [x19, #0x20]
19f3dfb54:	03 4c 02 94	bl	0x19f472b60
19f3dfb58:	81 e1 23 94	bl	0x19fcd815c
19f3dfb5c:	e8 03 00 aa	mov	x8, x0
19f3dfb60:	fc 0b 00 f9	str	x28, [sp, #0x10]
19f3dfb64:	e0 03 1c aa	mov	x0, x28
19f3dfb68:	fc 03 08 aa	mov	x28, x8
19f3dfb6c:	e1 03 08 aa	mov	x1, x8
19f3dfb70:	e6 df 23 94	bl	0x19fcd7b08
19f3dfb74:	40 02 00 34	cbz	w0, 0x19f3dfbbc
19f3dfb78:	60 16 40 f9	ldr	x0, [x19, #0x28]
19f3dfb7c:	11 5f 02 94	bl	0x19f4777c0
19f3dfb80:	f7 0f 00 f9	str	x23, [sp, #0x18]
19f3dfb84:	f7 03 00 aa	mov	x23, x0
19f3dfb88:	60 12 40 f9	ldr	x0, [x19, #0x20]
19f3dfb8c:	0d 5f 02 94	bl	0x19f4777c0
19f3dfb90:	ff 02 00 eb	cmp	x23, x0
19f3dfb94:	f7 0f 40 f9	ldr	x23, [sp, #0x18]
19f3dfb98:	21 01 00 54	b.ne	0x19f3dfbbc
19f3dfb9c:	68 f2 41 39	ldrb	w8, [x19, #0x7c]
19f3dfba0:	e8 04 00 34	cbz	w8, 0x19f3dfc3c
19f3dfba4:	c5 e1 23 94	bl	0x19fcd82b8
19f3dfba8:	e8 0b 40 f9	ldr	x8, [sp, #0x10]
19f3dfbac:	c6 e1 23 94	bl	0x19fcd82c4
19f3dfbb0:	bf e1 23 94	bl	0x19fcd82ac
19f3dfbb4:	bb e1 23 94	bl	0x19fcd82a0
19f3dfbb8:	2c 00 00 14	b	0x19f3dfc68
19f3dfbbc:	bf e1 23 94	bl	0x19fcd82b8
19f3dfbc0:	e8 0b 40 f9	ldr	x8, [sp, #0x10]
19f3dfbc4:	c0 e1 23 94	bl	0x19fcd82c4
19f3dfbc8:	b9 e1 23 94	bl	0x19fcd82ac
19f3dfbcc:	b5 e1 23 94	bl	0x19fcd82a0
19f3dfbd0:	e0 03 13 aa	mov	x0, x19
19f3dfbd4:	b4 34 01 94	bl	0x19f42cea4
19f3dfbd8:	68 16 40 f9	ldr	x8, [x19, #0x28]
19f3dfbdc:	7f 16 00 f9	str	xzr, [x19, #0x28]
19f3dfbe0:	b9 e1 23 94	bl	0x19fcd82c4
19f3dfbe4:	a9 e1 23 94	bl	0x19fcd8288
19f3dfbe8:	a5 e1 23 94	bl	0x19fcd827c
19f3dfbec:	75 00 00 34	cbz	w21, 0x19f3dfbf8
19f3dfbf0:	28 00 80 52	mov	w8, #0x1
19f3dfbf4:	68 ee 01 39	strb	w8, [x19, #0x7b]
19f3dfbf8:	e0 03 16 aa	mov	x0, x22
19f3dfbfc:	2a e2 23 94	bl	0x19fcd84a4
19f3dfc00:	96 e1 23 94	bl	0x19fcd8258
19f3dfc04:	e8 1f 40 f9	ldr	x8, [sp, #0x38]
19f3dfc08:	69 12 26 90	adrp	x9, 311884 ; 0x1eb62b000
19f3dfc0c:	29 cd 47 f9	ldr	x9, [x9, #0xf98]
19f3dfc10:	29 01 40 f9	ldr	x9, [x9]
19f3dfc14:	3f 01 08 eb	cmp	x9, x8
19f3dfc18:	21 09 00 54	b.ne	0x19f3dfd3c
19f3dfc1c:	fd 7b 49 a9	ldp	x29, x30, [sp, #0x90]
19f3dfc20:	f4 4f 48 a9	ldp	x20, x19, [sp, #0x80]
19f3dfc24:	f6 57 47 a9	ldp	x22, x21, [sp, #0x70]
19f3dfc28:	f8 5f 46 a9	ldp	x24, x23, [sp, #0x60]
19f3dfc2c:	fa 67 45 a9	ldp	x26, x25, [sp, #0x50]
19f3dfc30:	fc 6f 44 a9	ldp	x28, x27, [sp, #0x40]
19f3dfc34:	ff 83 02 91	add	sp, sp, #0xa0
19f3dfc38:	c0 03 5f d6	ret
19f3dfc3c:	60 12 40 f9	ldr	x0, [x19, #0x20]
19f3dfc40:	90 5f 02 94	bl	0x19f477a80
19f3dfc44:	f7 03 00 aa	mov	x23, x0
19f3dfc48:	9c e1 23 94	bl	0x19fcd82b8
19f3dfc4c:	e8 0b 40 f9	ldr	x8, [sp, #0x10]
19f3dfc50:	9d e1 23 94	bl	0x19fcd82c4
19f3dfc54:	96 e1 23 94	bl	0x19fcd82ac
19f3dfc58:	92 e1 23 94	bl	0x19fcd82a0
19f3dfc5c:	ff 1e 00 f1	cmp	x23, #0x7
19f3dfc60:	f7 0f 40 f9	ldr	x23, [sp, #0x18]
19f3dfc64:	60 fb ff 54	b.eq	0x19f3dfbd0
19f3dfc68:	68 6e 40 b9	ldr	w8, [x19, #0x6c]
19f3dfc6c:	1f 0d 00 71	cmp	w8, #0x3
19f3dfc70:	61 f4 ff 54	b.ne	0x19f3dfafc
19f3dfc74:	e0 03 13 aa	mov	x0, x19
19f3dfc78:	e1 03 19 aa	mov	x1, x25
19f3dfc7c:	fa 33 01 94	bl	0x19f42cc64
19f3dfc80:	9f ff ff 17	b	0x19f3dfafc
19f3dfc84:	e8 36 24 f0	adrp	x8, 296671 ; 0x1e7abe000
19f3dfc88:	00 a1 42 f9	ldr	x0, [x8, #0x540]
19f3dfc8c:	f4 5f 00 a9	stp	x20, x23, [sp]
19f3dfc90:	e2 35 24 b0	adrp	x2, 296637 ; 0x1e7a9c000
19f3dfc94:	42 a0 15 91	add	x2, x2, #0x568
19f3dfc98:	52 5e 02 94	bl	0x19f4775e0
19f3dfc9c:	30 e1 23 94	bl	0x19fcd815c
19f3dfca0:	f4 03 00 aa	mov	x20, x0
19f3dfca4:	60 12 26 b0	adrp	x0, 311885 ; 0x1eb62c000
19f3dfca8:	00 80 41 f9	ldr	x0, [x0, #0x300]
19f3dfcac:	01 02 80 52	mov	w1, #0x10
19f3dfcb0:	f1 e1 23 94	bl	0x19fcd8474
19f3dfcb4:	a0 00 00 34	cbz	w0, 0x19f3dfcc8
19f3dfcb8:	e0 03 1a aa	mov	x0, x26
19f3dfcbc:	e1 03 13 aa	mov	x1, x19
19f3dfcc0:	e2 03 14 aa	mov	x2, x20
19f3dfcc4:	cb 8b 01 94	bl	0x19f442bf0
19f3dfcc8:	e0 03 14 aa	mov	x0, x20
19f3dfccc:	87 e1 23 94	bl	0x19fcd82e8
19f3dfcd0:	9c 3a 02 94	bl	0x19f46e740
19f3dfcd4:	8c e0 23 94	bl	0x19fcd7f04
19f3dfcd8:	00 00 20 d4	brk	#0
19f3dfcdc:	20 00 20 d4	brk	#0x1
19f3dfce0:	e8 36 24 f0	adrp	x8, 296671 ; 0x1e7abe000
19f3dfce4:	00 a1 42 f9	ldr	x0, [x8, #0x540]
19f3dfce8:	f4 6f 00 a9	stp	x20, x27, [sp]
19f3dfcec:	e2 35 24 b0	adrp	x2, 296637 ; 0x1e7a9c000
19f3dfcf0:	42 a0 16 91	add	x2, x2, #0x5a8
19f3dfcf4:	3b 5e 02 94	bl	0x19f4775e0
19f3dfcf8:	19 e1 23 94	bl	0x19fcd815c
19f3dfcfc:	f4 03 00 aa	mov	x20, x0
19f3dfd00:	60 12 26 b0	adrp	x0, 311885 ; 0x1eb62c000
19f3dfd04:	00 80 41 f9	ldr	x0, [x0, #0x300]
19f3dfd08:	01 02 80 52	mov	w1, #0x10
19f3dfd0c:	da e1 23 94	bl	0x19fcd8474
19f3dfd10:	a0 00 00 34	cbz	w0, 0x19f3dfd24
19f3dfd14:	e0 03 1a aa	mov	x0, x26
19f3dfd18:	e1 03 13 aa	mov	x1, x19
19f3dfd1c:	e2 03 14 aa	mov	x2, x20
19f3dfd20:	66 8b 01 94	bl	0x19f442ab8
19f3dfd24:	e0 03 14 aa	mov	x0, x20
19f3dfd28:	70 e1 23 94	bl	0x19fcd82e8
19f3dfd2c:	85 3a 02 94	bl	0x19f46e740
19f3dfd30:	75 e0 23 94	bl	0x19fcd7f04
19f3dfd34:	00 00 20 d4	brk	#0
19f3dfd38:	20 00 20 d4	brk	#0x1
19f3dfd3c:	6f e0 23 94	bl	0x19fcd7ef8
19f3dfd40:	e8 36 24 f0	adrp	x8, 296671 ; 0x1e7abe000
19f3dfd44:	14 a1 42 f9	ldr	x20, [x8, #0x540]
19f3dfd48:	e0 03 13 aa	mov	x0, x19
19f3dfd4c:	a5 47 02 94	bl	0x19f471be0
19f3dfd50:	03 e1 23 94	bl	0x19fcd815c
19f3dfd54:	f5 03 00 aa	mov	x21, x0
19f3dfd58:	e0 03 00 f9	str	x0, [sp]
19f3dfd5c:	e2 35 24 b0	adrp	x2, 296637 ; 0x1e7a9c000
19f3dfd60:	42 20 16 91	add	x2, x2, #0x588
19f3dfd64:	e0 03 14 aa	mov	x0, x20
19f3dfd68:	1e 5e 02 94	bl	0x19f4775e0
19f3dfd6c:	fc e0 23 94	bl	0x19fcd815c
19f3dfd70:	f4 03 00 aa	mov	x20, x0
19f3dfd74:	3c e1 23 94	bl	0x19fcd8264
19f3dfd78:	60 12 26 b0	adrp	x0, 311885 ; 0x1eb62c000
19f3dfd7c:	00 80 41 f9	ldr	x0, [x0, #0x300]
19f3dfd80:	01 02 80 52	mov	w1, #0x10
19f3dfd84:	bc e1 23 94	bl	0x19fcd8474
19f3dfd88:	a0 00 00 34	cbz	w0, 0x19f3dfd9c
19f3dfd8c:	e0 03 1a aa	mov	x0, x26
19f3dfd90:	e1 03 13 aa	mov	x1, x19
19f3dfd94:	e2 03 14 aa	mov	x2, x20
19f3dfd98:	6f 8b 01 94	bl	0x19f442b54
19f3dfd9c:	e0 03 14 aa	mov	x0, x20
19f3dfda0:	52 e1 23 94	bl	0x19fcd82e8
19f3dfda4:	67 3a 02 94	bl	0x19f46e740
19f3dfda8:	57 e0 23 94	bl	0x19fcd7f04
19f3dfdac:	00 00 20 d4	brk	#0
19f3dfdb0:	20 00 20 d4	brk	#0x1
19f3dfdb4:	00 38 40 f9	ldr	x0, [x0, #0x70]
19f3dfdb8:	92 4f 02 14	b	0x19f473c00
19f3dfdbc:	f6 57 bd a9	stp	x22, x21, [sp, #-0x30]!
19f3dfdc0:	f4 4f 01 a9	stp	x20, x19, [sp, #0x10]
19f3dfdc4:	fd 7b 02 a9	stp	x29, x30, [sp, #0x20]
19f3dfdc8:	fd 83 00 91	add	x29, sp, #0x20
19f3dfdcc:	f3 03 00 aa	mov	x19, x0
19f3dfdd0:	5b e1 23 94	bl	0x19fcd833c
19f3dfdd4:	f4 03 00 aa	mov	x20, x0
19f3dfdd8:	32 4c 02 94	bl	0x19f472ea0
19f3dfddc:	f5 03 00 aa	mov	x21, x0
19f3dfde0:	e0 03 13 aa	mov	x0, x19
19f3dfde4:	e2 03 15 aa	mov	x2, x21
19f3dfde8:	e3 03 14 aa	mov	x3, x20
19f3dfdec:	04 00 80 52	mov	w4, #0x0
19f3dfdf0:	84 3c 02 94	bl	0x19f46f000
19f3dfdf4:	f3 03 00 aa	mov	x19, x0
19f3dfdf8:	18 e1 23 94	bl	0x19fcd8258
19f3dfdfc:	1a e1 23 94	bl	0x19fcd8264
19f3dfe00:	e0 03 13 aa	mov	x0, x19
19f3dfe04:	fd 7b 42 a9	ldp	x29, x30, [sp, #0x20]
19f3dfe08:	f4 4f 41 a9	ldp	x20, x19, [sp, #0x10]
19f3dfe0c:	f6 57 c3 a8	ldp	x22, x21, [sp], #0x30
19f3dfe10:	c0 03 5f d6	ret
19f3dfe14:	a0 04 00 b4	cbz	x0, 0x19f3dfea8
19f3dfe18:	f6 57 bd a9	stp	x22, x21, [sp, #-0x30]!
19f3dfe1c:	f4 4f 01 a9	stp	x20, x19, [sp, #0x10]
19f3dfe20:	fd 7b 02 a9	stp	x29, x30, [sp, #0x20]
19f3dfe24:	fd 83 00 91	add	x29, sp, #0x20
19f3dfe28:	f3 03 00 aa	mov	x19, x0
19f3dfe2c:	14 60 01 91	add	x20, x0, #0x58
19f3dfe30:	3a e1 23 94	bl	0x19fcd8318
19f3dfe34:	f5 03 00 aa	mov	x21, x0
19f3dfe38:	e0 03 14 aa	mov	x0, x20
19f3dfe3c:	94 e1 23 94	bl	0x19fcd848c
19f3dfe40:	e0 03 15 aa	mov	x0, x21
19f3dfe44:	77 46 02 94	bl	0x19f471820
19f3dfe48:	f6 03 00 aa	mov	x22, x0
19f3dfe4c:	06 e1 23 94	bl	0x19fcd8264
19f3dfe50:	f4 03 13 aa	mov	x20, x19
19f3dfe54:	88 0e 42 f8	ldr	x8, [x20, #0x20]!
19f3dfe58:	96 02 00 f9	str	x22, [x20]
19f3dfe5c:	1a e1 23 94	bl	0x19fcd82c4
19f3dfe60:	95 f2 00 91	add	x21, x20, #0x3c
19f3dfe64:	e0 03 15 aa	mov	x0, x21
19f3dfe68:	8c e1 23 94	bl	0x19fcd8498
19f3dfe6c:	81 02 40 f9	ldr	x1, [x20]
19f3dfe70:	80 82 00 91	add	x0, x20, #0x20
19f3dfe74:	1e 91 01 94	bl	0x19f4442ec
19f3dfe78:	e0 03 15 aa	mov	x0, x21
19f3dfe7c:	8a e1 23 94	bl	0x19fcd84a4
19f3dfe80:	bc de 23 94	bl	0x19fcd7970
19f3dfe84:	b6 e0 23 94	bl	0x19fcd815c
19f3dfe88:	f5 03 00 aa	mov	x21, x0
19f3dfe8c:	41 00 80 52	mov	w1, #0x2
19f3dfe90:	79 e1 23 94	bl	0x19fcd8474
19f3dfe94:	c0 00 00 35	cbnz	w0, 0x19f3dfeac
19f3dfe98:	f3 e0 23 94	bl	0x19fcd8264
19f3dfe9c:	fd 7b 42 a9	ldp	x29, x30, [sp, #0x20]
19f3dfea0:	f4 4f 41 a9	ldp	x20, x19, [sp, #0x10]
19f3dfea4:	f6 57 c3 a8	ldp	x22, x21, [sp], #0x30
19f3dfea8:	c0 03 5f d6	ret
19f3dfeac:	e0 03 13 aa	mov	x0, x19
19f3dfeb0:	e1 03 14 aa	mov	x1, x20
19f3dfeb4:	e2 03 15 aa	mov	x2, x21
19f3dfeb8:	9c 8b 01 94	bl	0x19f442d28
19f3dfebc:	f7 ff ff 17	b	0x19f3dfe98
19f3dfec0:	00 04 40 f9	ldr	x0, [x0, #0x8]
19f3dfec4:	c0 03 5f d6	ret
19f3dfec8:	f4 4f be a9	stp	x20, x19, [sp, #-0x20]!
19f3dfecc:	fd 7b 01 a9	stp	x29, x30, [sp, #0x10]
19f3dfed0:	fd 43 00 91	add	x29, sp, #0x10
19f3dfed4:	f3 03 00 aa	mov	x19, x0
19f3dfed8:	e0 03 02 aa	mov	x0, x2
19f3dfedc:	31 44 02 94	bl	0x19f470fa0
19f3dfee0:	9f e0 23 94	bl	0x19fcd815c
19f3dfee4:	f4 03 00 aa	mov	x20, x0
19f3dfee8:	e0 03 13 aa	mov	x0, x19
19f3dfeec:	e2 03 14 aa	mov	x2, x20
19f3dfef0:	84 42 02 94	bl	0x19f470900
19f3dfef4:	9a e0 23 94	bl	0x19fcd815c
19f3dfef8:	f3 03 00 aa	mov	x19, x0
19f3dfefc:	d7 e0 23 94	bl	0x19fcd8258
19f3dff00:	e0 03 13 aa	mov	x0, x19
19f3dff04:	fd 7b 41 a9	ldp	x29, x30, [sp, #0x10]
19f3dff08:	f4 4f c2 a8	ldp	x20, x19, [sp], #0x20
19f3dff0c:	8e e0 23 14	b	0x19fcd8144
19f3dff10:	f4 4f be a9	stp	x20, x19, [sp, #-0x20]!
19f3dff14:	fd 7b 01 a9	stp	x29, x30, [sp, #0x10]
19f3dff18:	fd 43 00 91	add	x29, sp, #0x10
19f3dff1c:	09 4e 02 94	bl	0x19f473740
19f3dff20:	8f e0 23 94	bl	0x19fcd815c
19f3dff24:	f3 03 00 aa	mov	x19, x0
19f3dff28:	4e 4a 02 94	bl	0x19f472860
19f3dff2c:	8c e0 23 94	bl	0x19fcd815c
19f3dff30:	f4 03 00 aa	mov	x20, x0
19f3dff34:	c6 e0 23 94	bl	0x19fcd824c
19f3dff38:	e0 03 14 aa	mov	x0, x20
19f3dff3c:	fd 7b 41 a9	ldp	x29, x30, [sp, #0x10]
19f3dff40:	f4 4f c2 a8	ldp	x20, x19, [sp], #0x20
19f3dff44:	80 e0 23 14	b	0x19fcd8144
19f3dff48:	ff c3 01 d1	sub	sp, sp, #0x70
19f3dff4c:	f6 57 04 a9	stp	x22, x21, [sp, #0x40]
19f3dff50:	f4 4f 05 a9	stp	x20, x19, [sp, #0x50]
19f3dff54:	fd 7b 06 a9	stp	x29, x30, [sp, #0x60]
19f3dff58:	fd 83 01 91	add	x29, sp, #0x60
19f3dff5c:	f4 03 00 aa	mov	x20, x0
19f3dff60:	f7 e0 23 94	bl	0x19fcd833c
19f3dff64:	f3 03 00 aa	mov	x19, x0
19f3dff68:	60 04 00 b4	cbz	x0, 0x19f3dfff4
19f3dff6c:	e8 36 24 f0	adrp	x8, 296671 ; 0x1e7abe000
19f3dff70:	00 5d 43 f9	ldr	x0, [x8, #0x6b8]
19f3dff74:	b3 42 02 94	bl	0x19f470a40
19f3dff78:	79 e0 23 94	bl	0x19fcd815c
19f3dff7c:	f5 03 00 aa	mov	x21, x0
19f3dff80:	68 12 26 90	adrp	x8, 311884 ; 0x1eb62b000
19f3dff84:	08 bd 46 f9	ldr	x8, [x8, #0xd78]
19f3dff88:	96 16 40 f9	ldr	x22, [x20, #0x28]
19f3dff8c:	e8 07 00 f9	str	x8, [sp, #0x8]
19f3dff90:	48 03 00 f0	adrp	x8, 107 ; 0x19f44a000
19f3dff94:	00 9d 46 fd	ldr	d0, [x8, #0xd38]
19f3dff98:	68 ff ff 90	adrp	x8, -20 ; 0x19f3cb000
19f3dff9c:	08 21 3a 91	add	x8, x8, #0xe88
19f3dffa0:	e0 0b 00 fd	str	d0, [sp, #0x10]
19f3dffa4:	89 35 24 f0	adrp	x9, 296627 ; 0x1e7a92000
19f3dffa8:	29 e1 1a 91	add	x9, x9, #0x6b8
19f3dffac:	e8 a7 01 a9	stp	x8, x9, [sp, #0x18]
19f3dffb0:	f4 17 00 f9	str	x20, [sp, #0x28]
19f3dffb4:	df e0 23 94	bl	0x19fcd8330
19f3dffb8:	e0 1b 00 f9	str	x0, [sp, #0x30]
19f3dffbc:	e6 e0 23 94	bl	0x19fcd8354
19f3dffc0:	f4 03 00 aa	mov	x20, x0
19f3dffc4:	e0 1f 00 f9	str	x0, [sp, #0x38]
19f3dffc8:	e1 23 00 91	add	x1, sp, #0x8
19f3dffcc:	e0 03 16 aa	mov	x0, x22
19f3dffd0:	d4 8f 01 94	bl	0x19f443f20
19f3dffd4:	f5 1f 40 f9	ldr	x21, [sp, #0x38]
19f3dffd8:	dc e0 23 94	bl	0x19fcd8348
19f3dffdc:	f4 03 00 aa	mov	x20, x0
19f3dffe0:	a1 e0 23 94	bl	0x19fcd8264
19f3dffe4:	e8 1b 40 f9	ldr	x8, [sp, #0x30]
19f3dffe8:	b7 e0 23 94	bl	0x19fcd82c4
19f3dffec:	9b e0 23 94	bl	0x19fcd8258
19f3dfff0:	02 00 00 14	b	0x19f3dfff8
19f3dfff4:	14 00 80 d2	mov	x20, #0x0
19f3dfff8:	95 e0 23 94	bl	0x19fcd824c
19f3dfffc:	e0 03 14 aa	mov	x0, x20
19f3e0000:	fd 7b 46 a9	ldp	x29, x30, [sp, #0x60]
19f3e0004:	f4 4f 45 a9	ldp	x20, x19, [sp, #0x50]
19f3e0008:	f6 57 44 a9	ldp	x22, x21, [sp, #0x40]
19f3e000c:	ff c3 01 91	add	sp, sp, #0x70
19f3e0010:	4d e0 23 14	b	0x19fcd8144
