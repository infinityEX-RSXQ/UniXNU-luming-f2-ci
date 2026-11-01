D:\Codex\workspaces\2026-10-29\zai\work\stage13-mode\audit\mg-scale-data-reader.macho:
(__TEXT,__text) section
1a020fc68:	e0 03 14 aa	mov	x0, x20
1a020fc6c:	56 9b 95 95	bl	0x1a67769c4
1a020fc70:	f7 03 00 aa	mov	x23, x0
1a020fc74:	24 9b 95 95	bl	0x1a6776904
1a020fc78:	ff 02 00 eb	cmp	x23, x0
1a020fc7c:	e1 01 00 54	b.ne	0x1a020fcb8
1a020fc80:	e0 03 14 aa	mov	x0, x20
1a020fc84:	50 9b 95 95	bl	0x1a67769c4
1a020fc88:	f7 03 00 aa	mov	x23, x0
1a020fc8c:	1e 9b 95 95	bl	0x1a6776904
1a020fc90:	ff 02 00 eb	cmp	x23, x0
1a020fc94:	e1 09 00 54	b.ne	0x1a020fdd0
1a020fc98:	e0 03 14 aa	mov	x0, x20
1a020fc9c:	14 9b 95 95	bl	0x1a67768ec
1a020fca0:	1f 10 00 f1	cmp	x0, #0x4
1a020fca4:	61 09 00 54	b.ne	0x1a020fdd0
1a020fca8:	e0 03 14 aa	mov	x0, x20
1a020fcac:	0a 9b 95 95	bl	0x1a67768d4
1a020fcb0:	13 00 40 b9	ldr	w19, [x0]
1a020fcb4:	6d 00 00 14	b	0x1a020fe68
1a020fcb8:	56 03 00 b0	adrp	x22, 105 ; 0x1a0278000
1a020fcbc:	d6 ba 31 91	add	x22, x22, #0xc6e
1a020fcc0:	e0 03 16 aa	mov	x0, x22
1a020fcc4:	e1 05 80 52	mov	w1, #0x2f
1a020fcc8:	a9 9d 95 95	bl	0x1a677736c
1a020fccc:	1f 00 00 f1	cmp	x0, #0x0
1a020fcd0:	d6 06 80 9a	csinc	x22, x22, x0, eq
1a020fcd4:	e0 03 14 aa	mov	x0, x20
