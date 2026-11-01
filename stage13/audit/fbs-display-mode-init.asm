D:\civitoip20\lumingios-cdx\crash-symbolication\fbs-display-mode-init.macho:
(__TEXT,__text) section
19f3d0500:	ff 43 02 d1	sub	sp, sp, #0x90
19f3d0504:	e9 23 02 6d	stp	d9, d8, [sp, #0x20]
19f3d0508:	fc 6f 03 a9	stp	x28, x27, [sp, #0x30]
19f3d050c:	fa 67 04 a9	stp	x26, x25, [sp, #0x40]
19f3d0510:	f8 5f 05 a9	stp	x24, x23, [sp, #0x50]
19f3d0514:	f6 57 06 a9	stp	x22, x21, [sp, #0x60]
19f3d0518:	f4 4f 07 a9	stp	x20, x19, [sp, #0x70]
19f3d051c:	fd 7b 08 a9	stp	x29, x30, [sp, #0x80]
19f3d0520:	fd 03 02 91	add	x29, sp, #0x80
19f3d0524:	f5 03 07 aa	mov	x21, x7
19f3d0528:	f6 03 06 aa	mov	x22, x6
19f3d052c:	f7 03 05 aa	mov	x23, x5
19f3d0530:	f8 03 04 aa	mov	x24, x4
19f3d0534:	fa 03 03 aa	mov	x26, x3
19f3d0538:	f9 03 02 aa	mov	x25, x2
19f3d053c:	28 40 60 1e	fmov	d8, d1
19f3d0540:	09 40 60 1e	fmov	d9, d0
19f3d0544:	f4 03 01 aa	mov	x20, x1
19f3d0548:	bc 0f 40 f9	ldr	x28, [x29, #0x18]
19f3d054c:	68 37 24 d0	adrp	x8, 296686 ; 0x1e7abe000
19f3d0550:	08 bd 46 f9	ldr	x8, [x8, #0xd78]
19f3d0554:	e0 23 01 a9	stp	x0, x8, [sp, #0x10]
19f3d0558:	28 ca f1 f0	adrp	x8, -116409 ; 0x182d17000
19f3d055c:	01 b1 32 91	add	x1, x8, #0xcac
19f3d0560:	e0 43 00 91	add	x0, sp, #0x10
19f3d0564:	1f 1f 24 94	bl	0x19fcd81e0
19f3d0568:	f3 03 00 aa	mov	x19, x0
19f3d056c:	c0 01 00 b4	cbz	x0, 0x19f3d05a4
19f3d0570:	bb 43 40 39	ldrb	w27, [x29, #0x10]
19f3d0574:	79 ea 00 a9	stp	x25, x26, [x19, #0x8]
19f3d0578:	78 0e 00 f9	str	x24, [x19, #0x18]
19f3d057c:	00 03 63 9e	ucvtf	d0, x24
19f3d0580:	21 41 60 1e	fmov	d1, d9
19f3d0584:	67 1d 24 94	bl	0x19fcd7b20
19f3d0588:	1f 00 00 71	cmp	w0, #0x0
19f3d058c:	e0 03 67 9e	fmov	d0, xzr
19f3d0590:	00 1c 69 1e	fcsel	d0, d0, d9, ne
19f3d0594:	60 22 02 6d	stp	d0, d8, [x19, #0x20]
19f3d0598:	77 5a 03 a9	stp	x23, x22, [x19, #0x30]
19f3d059c:	75 22 00 f9	str	x21, [x19, #0x40]
19f3d05a0:	7b 22 01 39	strb	w27, [x19, #0x48]
19f3d05a4:	9f 0f 00 f1	cmp	x28, #0x3
19f3d05a8:	80 08 00 54	b.eq	0x19f3d06b8
19f3d05ac:	e0 03 13 aa	mov	x0, x19
19f3d05b0:	0f 1f 24 94	bl	0x19fcd81ec
19f3d05b4:	fb 03 00 aa	mov	x27, x0
19f3d05b8:	68 37 24 d0	adrp	x8, 296686 ; 0x1e7abe000
19f3d05bc:	00 39 44 f9	ldr	x0, [x8, #0x870]
19f3d05c0:	0b 1f 24 94	bl	0x19fcd81ec
19f3d05c4:	1f 07 00 b1	cmn	x24, #0x1
19f3d05c8:	e0 03 00 54	b.eq	0x19f3d0644
19f3d05cc:	48 07 00 91	add	x8, x26, #0x1
19f3d05d0:	1f 09 00 f1	cmp	x8, #0x2
19f3d05d4:	83 03 00 54	b.lo	0x19f3d0644
19f3d05d8:	28 07 00 91	add	x8, x25, #0x1
19f3d05dc:	1f 09 00 f1	cmp	x8, #0x2
19f3d05e0:	23 03 00 54	b.lo	0x19f3d0644
19f3d05e4:	7f 03 00 eb	cmp	x27, x0
19f3d05e8:	e1 02 00 54	b.ne	0x19f3d0644
19f3d05ec:	d8 00 00 b4	cbz	x24, 0x19f3d0604
19f3d05f0:	28 21 60 1e	fcmp	d9, #0.0
19f3d05f4:	84 02 00 54	b.mi	0x19f3d0644
19f3d05f8:	08 21 60 1e	fcmp	d8, #0.0
19f3d05fc:	28 01 00 54	b.hi	0x19f3d0620
19f3d0600:	11 00 00 14	b	0x19f3d0644
19f3d0604:	20 41 60 1e	fmov	d0, d9
19f3d0608:	52 1d 24 94	bl	0x19fcd7b50
19f3d060c:	08 21 60 1e	fcmp	d8, #0.0
19f3d0610:	a9 01 00 54	b.ls	0x19f3d0644
19f3d0614:	28 21 60 1e	fcmp	d9, #0.0
19f3d0618:	64 01 00 54	b.mi	0x19f3d0644
19f3d061c:	40 01 00 37	tbnz	w0, #0x0, 0x19f3d0644
19f3d0620:	e0 03 17 aa	mov	x0, x23
19f3d0624:	4d 00 00 94	bl	0x19f3d0758
19f3d0628:	e0 00 00 34	cbz	w0, 0x19f3d0644
19f3d062c:	e0 03 16 aa	mov	x0, x22
19f3d0630:	47 00 00 94	bl	0x19f3d074c
19f3d0634:	80 00 00 34	cbz	w0, 0x19f3d0644
19f3d0638:	e0 03 15 aa	mov	x0, x21
19f3d063c:	4a 00 00 94	bl	0x19f3d0764
19f3d0640:	c0 03 00 37	tbnz	w0, #0x0, 0x19f3d06b8
19f3d0644:	9f 0b 00 f1	cmp	x28, #0x2
19f3d0648:	40 02 00 54	b.eq	0x19f3d0690
19f3d064c:	9f 07 00 f1	cmp	x28, #0x1
19f3d0650:	00 05 00 54	b.eq	0x19f3d06f0
19f3d0654:	68 37 24 d0	adrp	x8, 296686 ; 0x1e7abe000
19f3d0658:	00 31 43 f9	ldr	x0, [x8, #0x660]
19f3d065c:	f9 84 02 94	bl	0x19f471a40
19f3d0660:	bf 1e 24 94	bl	0x19fcd815c
19f3d0664:	f5 03 00 aa	mov	x21, x0
19f3d0668:	f3 03 00 f9	str	x19, [sp]
19f3d066c:	44 36 24 d0	adrp	x4, 296650 ; 0x1e7a9a000
19f3d0670:	84 20 3f 91	add	x4, x4, #0xfc8
19f3d0674:	46 36 24 f0	adrp	x6, 296651 ; 0x1e7a9b000
19f3d0678:	c6 20 00 91	add	x6, x6, #0x8
19f3d067c:	e2 03 14 aa	mov	x2, x20
19f3d0680:	e3 03 13 aa	mov	x3, x19
19f3d0684:	05 0e 80 52	mov	w5, #0x70
19f3d0688:	f6 88 02 94	bl	0x19f472a60
19f3d068c:	0a 00 00 14	b	0x19f3d06b4
19f3d0690:	2e 37 00 94	bl	0x19f3de348
19f3d0694:	b2 1e 24 94	bl	0x19fcd815c
19f3d0698:	f4 03 00 aa	mov	x20, x0
19f3d069c:	01 02 80 52	mov	w1, #0x10
19f3d06a0:	75 1f 24 94	bl	0x19fcd8474
19f3d06a4:	e0 01 00 35	cbnz	w0, 0x19f3d06e0
19f3d06a8:	ec 1e 24 94	bl	0x19fcd8258
19f3d06ac:	f5 03 13 aa	mov	x21, x19
19f3d06b0:	13 00 80 d2	mov	x19, #0x0
19f3d06b4:	ec 1e 24 94	bl	0x19fcd8264
19f3d06b8:	e0 03 13 aa	mov	x0, x19
19f3d06bc:	fd 7b 48 a9	ldp	x29, x30, [sp, #0x80]
19f3d06c0:	f4 4f 47 a9	ldp	x20, x19, [sp, #0x70]
19f3d06c4:	f6 57 46 a9	ldp	x22, x21, [sp, #0x60]
19f3d06c8:	f8 5f 45 a9	ldp	x24, x23, [sp, #0x50]
19f3d06cc:	fa 67 44 a9	ldp	x26, x25, [sp, #0x40]
19f3d06d0:	fc 6f 43 a9	ldp	x28, x27, [sp, #0x30]
19f3d06d4:	e9 23 42 6d	ldp	d9, d8, [sp, #0x20]
19f3d06d8:	ff 43 02 91	add	sp, sp, #0x90
19f3d06dc:	c0 03 5f d6	ret
19f3d06e0:	e0 03 13 aa	mov	x0, x19
19f3d06e4:	e1 03 14 aa	mov	x1, x20
19f3d06e8:	48 b2 01 94	bl	0x19f43d008
19f3d06ec:	ef ff ff 17	b	0x19f3d06a8
19f3d06f0:	68 37 24 d0	adrp	x8, 296686 ; 0x1e7abe000
19f3d06f4:	00 a1 42 f9	ldr	x0, [x8, #0x540]
19f3d06f8:	f3 03 00 f9	str	x19, [sp]
19f3d06fc:	42 36 24 f0	adrp	x2, 296651 ; 0x1e7a9b000
19f3d0700:	42 20 00 91	add	x2, x2, #0x8
19f3d0704:	b7 9b 02 94	bl	0x19f4775e0
19f3d0708:	95 1e 24 94	bl	0x19fcd815c
19f3d070c:	f5 03 00 aa	mov	x21, x0
19f3d0710:	e0 12 26 90	adrp	x0, 311900 ; 0x1eb62c000
19f3d0714:	00 80 41 f9	ldr	x0, [x0, #0x300]
19f3d0718:	01 02 80 52	mov	w1, #0x10
19f3d071c:	56 1f 24 94	bl	0x19fcd8474
19f3d0720:	a0 00 00 34	cbz	w0, 0x19f3d0734
19f3d0724:	e0 03 14 aa	mov	x0, x20
19f3d0728:	e1 03 13 aa	mov	x1, x19
19f3d072c:	e2 03 15 aa	mov	x2, x21
19f3d0730:	53 b2 01 94	bl	0x19f43d07c
19f3d0734:	e0 03 15 aa	mov	x0, x21
19f3d0738:	ec 1e 24 94	bl	0x19fcd82e8
19f3d073c:	01 78 02 94	bl	0x19f46e740
19f3d0740:	f1 1d 24 94	bl	0x19fcd7f04
19f3d0744:	00 00 20 d4	brk	#0
19f3d0748:	20 00 20 d4	brk	#0x1
19f3d074c:	1f 0c 00 f1	cmp	x0, #0x3
19f3d0750:	e0 27 9f 1a	cset	w0, lo
19f3d0754:	c0 03 5f d6	ret
19f3d0758:	1f 08 00 f1	cmp	x0, #0x2
19f3d075c:	e0 27 9f 1a	cset	w0, lo
19f3d0760:	c0 03 5f d6	ret
19f3d0764:	1f 10 00 f1	cmp	x0, #0x4
19f3d0768:	e0 27 9f 1a	cset	w0, lo
19f3d076c:	c0 03 5f d6	ret
