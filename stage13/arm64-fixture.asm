abi_stage13.o:
(__TEXT,__text) section
_cdx13_publish_ui_scale:
       0:	ff 43 03 d1	sub	sp, sp, #0xd0
       4:	fd 7b 0c a9	stp	x29, x30, [sp, #0xc0]
       8:	fd 03 03 91	add	x29, sp, #0xc0
       c:	08 00 00 90	adrp	x8, ___stack_chk_guard@GOTPAGE
      10:	08 01 40 f9	ldr	x8, [x8, ___stack_chk_guard@GOTPAGEOFF]
      14:	08 01 40 f9	ldr	x8, [x8]
      18:	a8 83 1f f8	stur	x8, [x29, #-0x8]
      1c:	a0 83 1c b8	stur	w0, [x29, #-0x38]
      20:	a1 43 1c b8	stur	w1, [x29, #-0x3c]
      24:	00 00 00 90	adrp	x0, l_.str@PAGE
      28:	00 00 00 91	add	x0, x0, l_.str@PAGEOFF
      2c:	00 00 00 94	bl	__ZL6optionPKc
      30:	a0 03 1c b8	stur	w0, [x29, #-0x40]
      34:	a8 03 5c b8	ldur	w8, [x29, #-0x40]
      38:	09 00 00 90	adrp	x9, _cdx13_ui_requested@PAGE
      3c:	28 01 00 b9	str	w8, [x9, _cdx13_ui_requested@PAGEOFF]
      40:	a8 03 5c b8	ldur	w8, [x29, #-0x40]
      44:	08 01 00 35	cbnz	w8, 0x64
      48:	01 00 00 14	b	0x4c
      4c:	09 00 00 90	adrp	x9, _cdx13_ui_status@PAGE
      50:	08 00 80 52	mov	w8, #0x0
      54:	28 01 00 b9	str	w8, [x9, _cdx13_ui_status@PAGEOFF]
      58:	28 00 80 52	mov	w8, #0x1
      5c:	a8 f3 1c 38	sturb	w8, [x29, #-0x31]
      60:	8d 01 00 14	b	0x694
      64:	a8 03 5c b8	ldur	w8, [x29, #-0x40]
      68:	08 0d 00 71	subs	w8, w8, #0x3
      6c:	08 03 00 54	b.hi	0xcc
      70:	01 00 00 14	b	0x74
      74:	a8 83 5c b8	ldur	w8, [x29, #-0x38]
      78:	08 51 13 71	subs	w8, w8, #0x4d4
      7c:	81 02 00 54	b.ne	0xcc
      80:	01 00 00 14	b	0x84
      84:	a8 43 5c b8	ldur	w8, [x29, #-0x3c]
      88:	08 f9 2a 71	subs	w8, w8, #0xabe
      8c:	01 02 00 54	b.ne	0xcc
      90:	01 00 00 14	b	0x94
      94:	a8 83 5c b8	ldur	w8, [x29, #-0x38]
      98:	aa 03 5c b8	ldur	w10, [x29, #-0x40]
      9c:	09 09 ca 1a	udiv	w9, w8, w10
      a0:	29 7d 0a 1b	mul	w9, w9, w10
      a4:	08 01 09 6b	subs	w8, w8, w9
      a8:	28 01 00 35	cbnz	w8, 0xcc
      ac:	01 00 00 14	b	0xb0
      b0:	a8 43 5c b8	ldur	w8, [x29, #-0x3c]
      b4:	aa 03 5c b8	ldur	w10, [x29, #-0x40]
      b8:	09 09 ca 1a	udiv	w9, w8, w10
      bc:	29 7d 0a 1b	mul	w9, w9, w10
      c0:	08 01 09 6b	subs	w8, w8, w9
      c4:	08 01 00 34	cbz	w8, 0xe4
      c8:	01 00 00 14	b	0xcc
      cc:	09 00 00 90	adrp	x9, _cdx13_ui_status@PAGE
      d0:	28 00 80 52	mov	w8, #0x1
      d4:	28 01 00 b9	str	w8, [x9, _cdx13_ui_status@PAGEOFF]
      d8:	08 00 80 52	mov	w8, #0x0
      dc:	a8 f3 1c 38	sturb	w8, [x29, #-0x31]
      e0:	6d 01 00 14	b	0x694
      e4:	08 00 00 90	adrp	x8, _gIODTPlane@GOTPAGE
      e8:	08 01 40 f9	ldr	x8, [x8, _gIODTPlane@GOTPAGEOFF]
      ec:	01 01 40 f9	ldr	x1, [x8]
      f0:	00 00 00 90	adrp	x0, l_.str.1@PAGE
      f4:	00 00 00 91	add	x0, x0, l_.str.1@PAGEOFF
      f8:	00 00 00 94	bl	__ZN15IORegistryEntry8fromPathEPKcPKv
      fc:	a0 83 1b f8	stur	x0, [x29, #-0x48]
     100:	a8 83 5b f8	ldur	x8, [x29, #-0x48]
     104:	08 01 00 b5	cbnz	x8, 0x124
     108:	01 00 00 14	b	0x10c
     10c:	09 00 00 90	adrp	x9, _cdx13_ui_status@PAGE
     110:	48 00 80 52	mov	w8, #0x2
     114:	28 01 00 b9	str	w8, [x9, _cdx13_ui_status@PAGEOFF]
     118:	08 00 80 52	mov	w8, #0x0
     11c:	a8 f3 1c 38	sturb	w8, [x29, #-0x31]
     120:	5d 01 00 14	b	0x694
     124:	09 00 00 90	adrp	x9, l___const.cdx13_publish_ui_scale.keys@PAGE
     128:	29 01 00 91	add	x9, x9, l___const.cdx13_publish_ui_scale.keys@PAGEOFF
     12c:	28 01 40 f9	ldr	x8, [x9]
     130:	29 05 40 f9	ldr	x9, [x9, #0x8]
     134:	a9 03 1f f8	stur	x9, [x29, #-0x10]
     138:	a8 83 1e f8	stur	x8, [x29, #-0x18]
     13c:	a8 03 5c b8	ldur	w8, [x29, #-0x40]
     140:	a8 03 1e b8	stur	w8, [x29, #-0x20]
     144:	08 00 80 52	mov	w8, #0x0
     148:	a8 43 1e b8	stur	w8, [x29, #-0x1c]
     14c:	09 00 80 d2	mov	x9, #0x0
     150:	a9 83 1d f8	stur	x9, [x29, #-0x28]
     154:	a9 03 1d f8	stur	x9, [x29, #-0x30]
     158:	a8 63 1b 78	sturh	w8, [x29, #-0x4a]
     15c:	a8 43 1b 78	sturh	w8, [x29, #-0x4c]
     160:	a8 03 1b b8	stur	w8, [x29, #-0x50]
     164:	a8 c3 1a b8	stur	w8, [x29, #-0x54]
     168:	01 00 00 14	b	0x16c
     16c:	a8 c3 5a b8	ldur	w8, [x29, #-0x54]
     170:	08 05 00 71	subs	w8, w8, #0x1
     174:	88 09 00 54	b.hi	0x2a4
     178:	01 00 00 14	b	0x17c
     17c:	a0 83 5b f8	ldur	x0, [x29, #-0x48]
     180:	a8 c3 5a b8	ldur	w8, [x29, #-0x54]
     184:	e9 03 08 aa	mov	x9, x8
     188:	a8 63 00 d1	sub	x8, x29, #0x18
     18c:	01 79 69 f8	ldr	x1, [x8, x9, lsl #3]
     190:	00 00 00 94	bl	__ZNK15IORegistryEntry11getPropertyEPKc
     194:	a8 c3 5a b8	ldur	w8, [x29, #-0x54]
     198:	e9 03 08 aa	mov	x9, x8
     19c:	a8 c3 00 d1	sub	x8, x29, #0x30
     1a0:	00 79 29 f8	str	x0, [x8, x9, lsl #3]
     1a4:	a9 c3 5a b8	ldur	w9, [x29, #-0x54]
     1a8:	08 79 69 f8	ldr	x8, [x8, x9, lsl #3]
     1ac:	88 06 00 b4	cbz	x8, 0x27c
     1b0:	01 00 00 14	b	0x1b4
     1b4:	a8 c3 5a b8	ldur	w8, [x29, #-0x54]
     1b8:	e9 03 08 aa	mov	x9, x8
     1bc:	a8 c3 00 d1	sub	x8, x29, #0x30
     1c0:	e8 17 00 f9	str	x8, [sp, #0x28]
     1c4:	00 79 69 f8	ldr	x0, [x8, x9, lsl #3]
     1c8:	00 00 00 94	bl	__ZN8OSObject6retainEv
     1cc:	e8 17 40 f9	ldr	x8, [sp, #0x28]
     1d0:	a9 c3 5a b8	ldur	w9, [x29, #-0x54]
     1d4:	00 79 69 f8	ldr	x0, [x8, x9, lsl #3]
     1d8:	00 00 00 94	bl	__ZN8OSObject4castEPS_
     1dc:	e0 33 00 f9	str	x0, [sp, #0x60]
     1e0:	08 00 80 52	mov	w8, #0x0
     1e4:	e8 5f 00 b9	str	w8, [sp, #0x5c]
     1e8:	e8 33 40 f9	ldr	x8, [sp, #0x60]
     1ec:	e8 00 00 b4	cbz	x8, 0x208
     1f0:	01 00 00 14	b	0x1f4
     1f4:	e0 33 40 f9	ldr	x0, [sp, #0x60]
     1f8:	00 00 00 94	bl	__ZNK6OSData9getLengthEv
     1fc:	08 10 00 71	subs	w8, w0, #0x4
     200:	a0 00 00 54	b.eq	0x214
     204:	01 00 00 14	b	0x208
     208:	68 00 80 52	mov	w8, #0x3
     20c:	a8 03 1b b8	stur	w8, [x29, #-0x50]
     210:	25 00 00 14	b	0x2a4
     214:	e0 33 40 f9	ldr	x0, [sp, #0x60]
     218:	00 00 00 94	bl	__ZNK6OSData14getBytesNoCopyEv
     21c:	e1 03 00 aa	mov	x1, x0
     220:	88 00 80 52	mov	w8, #0x4
     224:	e2 03 08 aa	mov	x2, x8
     228:	e0 73 01 91	add	x0, sp, #0x5c
     22c:	00 00 00 94	bl	_memcpy
     230:	e8 5f 40 b9	ldr	w8, [sp, #0x5c]
     234:	a9 c3 5a b8	ldur	w9, [x29, #-0x54]
     238:	ea 03 09 aa	mov	x10, x9
     23c:	a9 83 00 d1	sub	x9, x29, #0x20
     240:	29 79 6a b8	ldr	w9, [x9, x10, lsl #2]
     244:	08 01 09 6b	subs	w8, w8, w9
     248:	61 00 00 54	b.ne	0x254
     24c:	01 00 00 14	b	0x250
     250:	11 00 00 14	b	0x294
     254:	a8 c3 5a b8	ldur	w8, [x29, #-0x54]
     258:	a8 00 00 35	cbnz	w8, 0x26c
     25c:	01 00 00 14	b	0x260
     260:	e8 5f 40 b9	ldr	w8, [sp, #0x5c]
     264:	a8 00 00 34	cbz	w8, 0x278
     268:	01 00 00 14	b	0x26c
     26c:	88 00 80 52	mov	w8, #0x4
     270:	a8 03 1b b8	stur	w8, [x29, #-0x50]
     274:	0c 00 00 14	b	0x2a4
     278:	01 00 00 14	b	0x27c
     27c:	a8 c3 5a b8	ldur	w8, [x29, #-0x54]
     280:	ea 03 08 aa	mov	x10, x8
     284:	a9 2b 01 d1	sub	x9, x29, #0x4a
     288:	28 00 80 52	mov	w8, #0x1
     28c:	28 69 2a 38	strb	w8, [x9, x10]
     290:	01 00 00 14	b	0x294
     294:	a8 c3 5a b8	ldur	w8, [x29, #-0x54]
     298:	08 05 00 11	add	w8, w8, #0x1
     29c:	a8 c3 1a b8	stur	w8, [x29, #-0x54]
     2a0:	b3 ff ff 17	b	0x16c
     2a4:	a8 03 5b b8	ldur	w8, [x29, #-0x50]
     2a8:	e8 07 00 35	cbnz	w8, 0x3a4
     2ac:	01 00 00 14	b	0x2b0
     2b0:	08 00 80 52	mov	w8, #0x0
     2b4:	e8 5b 00 b9	str	w8, [sp, #0x58]
     2b8:	01 00 00 14	b	0x2bc
     2bc:	e8 5b 40 b9	ldr	w8, [sp, #0x58]
     2c0:	08 05 00 71	subs	w8, w8, #0x1
     2c4:	e8 06 00 54	b.hi	0x3a0
     2c8:	01 00 00 14	b	0x2cc
     2cc:	e8 5b 40 b9	ldr	w8, [sp, #0x58]
     2d0:	e9 03 08 aa	mov	x9, x8
     2d4:	a8 2b 01 d1	sub	x8, x29, #0x4a
     2d8:	08 69 69 38	ldrb	w8, [x8, x9]
     2dc:	88 05 00 34	cbz	w8, 0x38c
     2e0:	01 00 00 14	b	0x2e4
     2e4:	e8 5b 40 b9	ldr	w8, [sp, #0x58]
     2e8:	e9 03 08 aa	mov	x9, x8
     2ec:	a8 83 00 d1	sub	x8, x29, #0x20
     2f0:	00 09 09 8b	add	x0, x8, x9, lsl #2
     2f4:	81 00 80 52	mov	w1, #0x4
     2f8:	00 00 00 94	bl	__ZN6OSData9withBytesEPKvj
     2fc:	e0 2b 00 f9	str	x0, [sp, #0x50]
     300:	e8 2b 40 f9	ldr	x8, [sp, #0x50]
     304:	09 00 80 52	mov	w9, #0x0
     308:	e9 27 00 b9	str	w9, [sp, #0x24]
     30c:	68 01 00 b4	cbz	x8, 0x338
     310:	01 00 00 14	b	0x314
     314:	a0 83 5b f8	ldur	x0, [x29, #-0x48]
     318:	e8 5b 40 b9	ldr	w8, [sp, #0x58]
     31c:	e9 03 08 aa	mov	x9, x8
     320:	a8 63 00 d1	sub	x8, x29, #0x18
     324:	01 79 69 f8	ldr	x1, [x8, x9, lsl #3]
     328:	e2 2b 40 f9	ldr	x2, [sp, #0x50]
     32c:	00 00 00 94	bl	__ZN15IORegistryEntry11setPropertyEPKcP8OSObject
     330:	e0 27 00 b9	str	w0, [sp, #0x24]
     334:	01 00 00 14	b	0x338
     338:	e8 27 40 b9	ldr	w8, [sp, #0x24]
     33c:	08 01 00 12	and	w8, w8, #0x1
     340:	e8 3f 01 39	strb	w8, [sp, #0x4f]
     344:	e8 2b 40 f9	ldr	x8, [sp, #0x50]
     348:	a8 00 00 b4	cbz	x8, 0x35c
     34c:	01 00 00 14	b	0x350
     350:	e0 2b 40 f9	ldr	x0, [sp, #0x50]
     354:	00 00 00 94	bl	__ZN8OSObject7releaseEv
     358:	01 00 00 14	b	0x35c
     35c:	e8 3f 41 39	ldrb	w8, [sp, #0x4f]
     360:	a8 00 00 35	cbnz	w8, 0x374
     364:	01 00 00 14	b	0x368
     368:	a8 00 80 52	mov	w8, #0x5
     36c:	a8 03 1b b8	stur	w8, [x29, #-0x50]
     370:	0c 00 00 14	b	0x3a0
     374:	e8 5b 40 b9	ldr	w8, [sp, #0x58]
     378:	ea 03 08 aa	mov	x10, x8
     37c:	a9 33 01 d1	sub	x9, x29, #0x4c
     380:	28 00 80 52	mov	w8, #0x1
     384:	28 69 2a 38	strb	w8, [x9, x10]
     388:	01 00 00 14	b	0x38c
     38c:	01 00 00 14	b	0x390
     390:	e8 5b 40 b9	ldr	w8, [sp, #0x58]
     394:	08 05 00 11	add	w8, w8, #0x1
     398:	e8 5b 00 b9	str	w8, [sp, #0x58]
     39c:	c8 ff ff 17	b	0x2bc
     3a0:	01 00 00 14	b	0x3a4
     3a4:	a8 03 5b b8	ldur	w8, [x29, #-0x50]
     3a8:	a8 07 00 35	cbnz	w8, 0x49c
     3ac:	01 00 00 14	b	0x3b0
     3b0:	08 00 80 52	mov	w8, #0x0
     3b4:	e8 4b 00 b9	str	w8, [sp, #0x48]
     3b8:	01 00 00 14	b	0x3bc
     3bc:	e8 4b 40 b9	ldr	w8, [sp, #0x48]
     3c0:	08 05 00 71	subs	w8, w8, #0x1
     3c4:	a8 06 00 54	b.hi	0x498
     3c8:	01 00 00 14	b	0x3cc
     3cc:	a0 83 5b f8	ldur	x0, [x29, #-0x48]
     3d0:	e8 4b 40 b9	ldr	w8, [sp, #0x48]
     3d4:	e9 03 08 aa	mov	x9, x8
     3d8:	a8 63 00 d1	sub	x8, x29, #0x18
     3dc:	01 79 69 f8	ldr	x1, [x8, x9, lsl #3]
     3e0:	00 00 00 94	bl	__ZNK15IORegistryEntry11getPropertyEPKc
     3e4:	00 00 00 94	bl	__ZN8OSObject4castEPS_
     3e8:	e0 23 00 f9	str	x0, [sp, #0x40]
     3ec:	08 00 80 52	mov	w8, #0x0
     3f0:	e8 3f 00 b9	str	w8, [sp, #0x3c]
     3f4:	e8 23 40 f9	ldr	x8, [sp, #0x40]
     3f8:	e8 00 00 b4	cbz	x8, 0x414
     3fc:	01 00 00 14	b	0x400
     400:	e0 23 40 f9	ldr	x0, [sp, #0x40]
     404:	00 00 00 94	bl	__ZNK6OSData9getLengthEv
     408:	08 10 00 71	subs	w8, w0, #0x4
     40c:	a0 00 00 54	b.eq	0x420
     410:	01 00 00 14	b	0x414
     414:	c8 00 80 52	mov	w8, #0x6
     418:	a8 03 1b b8	stur	w8, [x29, #-0x50]
     41c:	1f 00 00 14	b	0x498
     420:	e0 23 40 f9	ldr	x0, [sp, #0x40]
     424:	00 00 00 94	bl	__ZNK6OSData14getBytesNoCopyEv
     428:	e1 03 00 aa	mov	x1, x0
     42c:	88 00 80 52	mov	w8, #0x4
     430:	e2 03 08 aa	mov	x2, x8
     434:	e0 f3 00 91	add	x0, sp, #0x3c
     438:	00 00 00 94	bl	_memcpy
     43c:	e8 3f 40 b9	ldr	w8, [sp, #0x3c]
     440:	e9 4b 40 b9	ldr	w9, [sp, #0x48]
     444:	ea 03 09 aa	mov	x10, x9
     448:	a9 83 00 d1	sub	x9, x29, #0x20
     44c:	29 79 6a b8	ldr	w9, [x9, x10, lsl #2]
     450:	08 01 09 6b	subs	w8, w8, w9
     454:	a0 00 00 54	b.eq	0x468
     458:	01 00 00 14	b	0x45c
     45c:	e8 00 80 52	mov	w8, #0x7
     460:	a8 03 1b b8	stur	w8, [x29, #-0x50]
     464:	0d 00 00 14	b	0x498
     468:	e8 4b 40 b9	ldr	w8, [sp, #0x48]
     46c:	c8 00 00 35	cbnz	w8, 0x484
     470:	01 00 00 14	b	0x474
     474:	e8 3f 40 b9	ldr	w8, [sp, #0x3c]
     478:	09 00 00 90	adrp	x9, _cdx13_ui_readback@PAGE
     47c:	28 01 00 b9	str	w8, [x9, _cdx13_ui_readback@PAGEOFF]
     480:	01 00 00 14	b	0x484
     484:	01 00 00 14	b	0x488
     488:	e8 4b 40 b9	ldr	w8, [sp, #0x48]
     48c:	08 05 00 11	add	w8, w8, #0x1
     490:	e8 4b 00 b9	str	w8, [sp, #0x48]
     494:	ca ff ff 17	b	0x3bc
     498:	01 00 00 14	b	0x49c
     49c:	a8 03 5b b8	ldur	w8, [x29, #-0x50]
     4a0:	88 06 00 34	cbz	w8, 0x570
     4a4:	01 00 00 14	b	0x4a8
     4a8:	08 00 80 52	mov	w8, #0x0
     4ac:	e8 3b 00 b9	str	w8, [sp, #0x38]
     4b0:	01 00 00 14	b	0x4b4
     4b4:	e8 3b 40 b9	ldr	w8, [sp, #0x38]
     4b8:	08 05 00 71	subs	w8, w8, #0x1
     4bc:	28 05 00 54	b.hi	0x560
     4c0:	01 00 00 14	b	0x4c4
     4c4:	e8 3b 40 b9	ldr	w8, [sp, #0x38]
     4c8:	e9 03 08 aa	mov	x9, x8
     4cc:	a8 33 01 d1	sub	x8, x29, #0x4c
     4d0:	08 69 69 38	ldrb	w8, [x8, x9]
     4d4:	c8 03 00 34	cbz	w8, 0x54c
     4d8:	01 00 00 14	b	0x4dc
     4dc:	e8 3b 40 b9	ldr	w8, [sp, #0x38]
     4e0:	e9 03 08 aa	mov	x9, x8
     4e4:	a8 c3 00 d1	sub	x8, x29, #0x30
     4e8:	08 79 69 f8	ldr	x8, [x8, x9, lsl #3]
     4ec:	08 02 00 b4	cbz	x8, 0x52c
     4f0:	01 00 00 14	b	0x4f4
     4f4:	a0 83 5b f8	ldur	x0, [x29, #-0x48]
     4f8:	e8 3b 40 b9	ldr	w8, [sp, #0x38]
     4fc:	e9 03 08 aa	mov	x9, x8
     500:	a8 63 00 d1	sub	x8, x29, #0x18
     504:	01 79 69 f8	ldr	x1, [x8, x9, lsl #3]
     508:	a8 c3 00 d1	sub	x8, x29, #0x30
     50c:	02 79 69 f8	ldr	x2, [x8, x9, lsl #3]
     510:	00 00 00 94	bl	__ZN15IORegistryEntry11setPropertyEPKcP8OSObject
     514:	a0 00 00 37	tbnz	w0, #0x0, 0x528
     518:	01 00 00 14	b	0x51c
     51c:	08 01 80 52	mov	w8, #0x8
     520:	a8 03 1b b8	stur	w8, [x29, #-0x50]
     524:	01 00 00 14	b	0x528
     528:	08 00 00 14	b	0x548
     52c:	a0 83 5b f8	ldur	x0, [x29, #-0x48]
     530:	e8 3b 40 b9	ldr	w8, [sp, #0x38]
     534:	e9 03 08 aa	mov	x9, x8
     538:	a8 63 00 d1	sub	x8, x29, #0x18
     53c:	01 79 69 f8	ldr	x1, [x8, x9, lsl #3]
     540:	00 00 00 94	bl	__ZN15IORegistryEntry14removePropertyEPKc
     544:	01 00 00 14	b	0x548
     548:	01 00 00 14	b	0x54c
     54c:	01 00 00 14	b	0x550
     550:	e8 3b 40 b9	ldr	w8, [sp, #0x38]
     554:	08 05 00 11	add	w8, w8, #0x1
     558:	e8 3b 00 b9	str	w8, [sp, #0x38]
     55c:	d6 ff ff 17	b	0x4b4
     560:	09 00 00 90	adrp	x9, _cdx13_ui_readback@PAGE
     564:	08 00 80 52	mov	w8, #0x0
     568:	28 01 00 b9	str	w8, [x9, _cdx13_ui_readback@PAGEOFF]
     56c:	19 00 00 14	b	0x5d0
     570:	08 00 80 52	mov	w8, #0x0
     574:	e8 37 00 b9	str	w8, [sp, #0x34]
     578:	01 00 00 14	b	0x57c
     57c:	e8 37 40 b9	ldr	w8, [sp, #0x34]
     580:	08 05 00 71	subs	w8, w8, #0x1
     584:	48 02 00 54	b.hi	0x5cc
     588:	01 00 00 14	b	0x58c
     58c:	e8 37 40 b9	ldr	w8, [sp, #0x34]
     590:	e9 03 08 aa	mov	x9, x8
     594:	a8 33 01 d1	sub	x8, x29, #0x4c
     598:	08 69 69 38	ldrb	w8, [x8, x9]
     59c:	e8 00 00 34	cbz	w8, 0x5b8
     5a0:	01 00 00 14	b	0x5a4
     5a4:	09 00 00 90	adrp	x9, _cdx13_ui_writes@PAGE
     5a8:	28 01 40 b9	ldr	w8, [x9, _cdx13_ui_writes@PAGEOFF]
     5ac:	08 05 00 11	add	w8, w8, #0x1
     5b0:	28 01 00 b9	str	w8, [x9, _cdx13_ui_writes@PAGEOFF]
     5b4:	01 00 00 14	b	0x5b8
     5b8:	01 00 00 14	b	0x5bc
     5bc:	e8 37 40 b9	ldr	w8, [sp, #0x34]
     5c0:	08 05 00 11	add	w8, w8, #0x1
     5c4:	e8 37 00 b9	str	w8, [sp, #0x34]
     5c8:	ed ff ff 17	b	0x57c
     5cc:	01 00 00 14	b	0x5d0
     5d0:	08 00 80 52	mov	w8, #0x0
     5d4:	e8 33 00 b9	str	w8, [sp, #0x30]
     5d8:	01 00 00 14	b	0x5dc
     5dc:	e8 33 40 b9	ldr	w8, [sp, #0x30]
     5e0:	08 05 00 71	subs	w8, w8, #0x1
     5e4:	68 02 00 54	b.hi	0x630
     5e8:	01 00 00 14	b	0x5ec
     5ec:	e8 33 40 b9	ldr	w8, [sp, #0x30]
     5f0:	e9 03 08 aa	mov	x9, x8
     5f4:	a8 c3 00 d1	sub	x8, x29, #0x30
     5f8:	08 79 69 f8	ldr	x8, [x8, x9, lsl #3]
     5fc:	08 01 00 b4	cbz	x8, 0x61c
     600:	01 00 00 14	b	0x604
     604:	e8 33 40 b9	ldr	w8, [sp, #0x30]
     608:	e9 03 08 aa	mov	x9, x8
     60c:	a8 c3 00 d1	sub	x8, x29, #0x30
     610:	00 79 69 f8	ldr	x0, [x8, x9, lsl #3]
     614:	00 00 00 94	bl	__ZN8OSObject7releaseEv
     618:	01 00 00 14	b	0x61c
     61c:	01 00 00 14	b	0x620
     620:	e8 33 40 b9	ldr	w8, [sp, #0x30]
     624:	08 05 00 11	add	w8, w8, #0x1
     628:	e8 33 00 b9	str	w8, [sp, #0x30]
     62c:	ec ff ff 17	b	0x5dc
     630:	a0 83 5b f8	ldur	x0, [x29, #-0x48]
     634:	00 00 00 94	bl	__ZN8OSObject7releaseEv
     638:	a8 03 5b b8	ldur	w8, [x29, #-0x50]
     63c:	09 00 00 90	adrp	x9, _cdx13_ui_status@PAGE
     640:	28 01 00 b9	str	w8, [x9, _cdx13_ui_status@PAGEOFF]
     644:	0a 00 00 90	adrp	x10, _cdx13_ui_readback@PAGE
     648:	09 00 00 90	adrp	x9, _cdx13_ui_writes@PAGE
     64c:	a8 03 5c b8	ldur	w8, [x29, #-0x40]
     650:	4a 01 40 b9	ldr	w10, [x10, _cdx13_ui_readback@PAGEOFF]
     654:	ab 03 5b b8	ldur	w11, [x29, #-0x50]
     658:	29 01 40 b9	ldr	w9, [x9, _cdx13_ui_writes@PAGEOFF]
     65c:	ec 03 09 aa	mov	x12, x9
     660:	e9 03 00 91	mov	x9, sp
     664:	2c 0d 00 f9	str	x12, [x9, #0x18]
     668:	2b 09 00 f9	str	x11, [x9, #0x10]
     66c:	2a 05 00 f9	str	x10, [x9, #0x8]
     670:	28 01 00 f9	str	x8, [x9]
     674:	00 00 00 90	adrp	x0, l_.str.4@PAGE
     678:	00 00 00 91	add	x0, x0, l_.str.4@PAGEOFF
     67c:	00 00 00 94	bl	_IOLog
     680:	a8 03 5b b8	ldur	w8, [x29, #-0x50]
     684:	08 01 00 71	subs	w8, w8, #0x0
     688:	e8 17 9f 1a	cset	w8, eq
     68c:	a8 f3 1c 38	sturb	w8, [x29, #-0x31]
     690:	01 00 00 14	b	0x694
     694:	a8 f3 5c 38	ldurb	w8, [x29, #-0x31]
     698:	e8 23 00 b9	str	w8, [sp, #0x20]
     69c:	a9 83 5f f8	ldur	x9, [x29, #-0x8]
     6a0:	08 00 00 90	adrp	x8, ___stack_chk_guard@GOTPAGE
     6a4:	08 01 40 f9	ldr	x8, [x8, ___stack_chk_guard@GOTPAGEOFF]
     6a8:	08 01 40 f9	ldr	x8, [x8]
     6ac:	08 01 09 eb	subs	x8, x8, x9
     6b0:	41 00 00 54	b.ne	0x6b8
     6b4:	02 00 00 14	b	0x6bc
     6b8:	00 00 00 94	bl	___stack_chk_fail
     6bc:	e0 23 40 b9	ldr	w0, [sp, #0x20]
     6c0:	fd 7b 4c a9	ldp	x29, x30, [sp, #0xc0]
     6c4:	ff 43 03 91	add	sp, sp, #0xd0
     6c8:	c0 03 5f d6	ret
__ZL6optionPKc:
     6cc:	ff 43 00 d1	sub	sp, sp, #0x10
     6d0:	e0 07 00 f9	str	x0, [sp, #0x8]
     6d4:	40 00 80 52	mov	w0, #0x2
     6d8:	ff 43 00 91	add	sp, sp, #0x10
     6dc:	c0 03 5f d6	ret
_cdx12_capture_mode:
     6e0:	ff 43 02 d1	sub	sp, sp, #0x90
     6e4:	fd 7b 08 a9	stp	x29, x30, [sp, #0x80]
     6e8:	fd 03 02 91	add	x29, sp, #0x80
     6ec:	08 00 00 90	adrp	x8, ___stack_chk_guard@GOTPAGE
     6f0:	08 01 40 f9	ldr	x8, [x8, ___stack_chk_guard@GOTPAGEOFF]
     6f4:	08 01 40 f9	ldr	x8, [x8]
     6f8:	a8 83 1f f8	stur	x8, [x29, #-0x8]
     6fc:	e0 37 00 b9	str	w0, [sp, #0x34]
     700:	e1 17 00 f9	str	x1, [sp, #0x28]
     704:	08 00 80 d2	mov	x8, #0x0
     708:	e8 0b 00 f9	str	x8, [sp, #0x10]
     70c:	e8 3b 00 f9	str	x8, [sp, #0x70]
     710:	e8 37 00 f9	str	x8, [sp, #0x68]
     714:	e8 33 00 f9	str	x8, [sp, #0x60]
     718:	e8 2f 00 f9	str	x8, [sp, #0x58]
     71c:	e8 2b 00 f9	str	x8, [sp, #0x50]
     720:	e8 27 00 f9	str	x8, [sp, #0x48]
     724:	e8 23 00 f9	str	x8, [sp, #0x40]
     728:	e8 1f 00 f9	str	x8, [sp, #0x38]
     72c:	e8 17 40 f9	ldr	x8, [sp, #0x28]
     730:	08 05 40 f1	subs	x8, x8, #0x1, lsl #12
     734:	43 01 00 54	b.lo	0x75c
     738:	01 00 00 14	b	0x73c
     73c:	e8 a3 40 39	ldrb	w8, [sp, #0x28]
     740:	08 09 00 12	and	w8, w8, #0x7
     744:	c8 00 00 35	cbnz	w8, 0x75c
     748:	01 00 00 14	b	0x74c
     74c:	e8 17 40 f9	ldr	x8, [sp, #0x28]
     750:	08 21 01 b1	adds	x8, x8, #0x48
     754:	63 00 00 54	b.lo	0x760
     758:	01 00 00 14	b	0x75c
     75c:	40 00 00 14	b	0x85c
     760:	e8 17 40 f9	ldr	x8, [sp, #0x28]
     764:	00 21 00 91	add	x0, x8, #0x8
     768:	08 08 80 52	mov	w8, #0x40
     76c:	e2 03 08 aa	mov	x2, x8
     770:	e1 e3 00 91	add	x1, sp, #0x38
     774:	00 00 00 94	bl	_copyin
     778:	e0 27 00 b9	str	w0, [sp, #0x24]
     77c:	28 00 80 52	mov	w8, #0x1
     780:	e8 23 00 b9	str	w8, [sp, #0x20]
     784:	e8 23 40 b9	ldr	w8, [sp, #0x20]
     788:	e8 0b 00 b9	str	w8, [sp, #0x8]
     78c:	08 00 00 90	adrp	x8, __ZL10cdx12_lock@PAGE
     790:	08 01 40 b9	ldr	w8, [x8, __ZL10cdx12_lock@PAGEOFF]
     794:	e8 0f 00 b9	str	w8, [sp, #0xc]
     798:	01 00 00 14	b	0x79c
     79c:	e9 0f 40 b9	ldr	w9, [sp, #0xc]
     7a0:	ec 0b 40 b9	ldr	w12, [sp, #0x8]
     7a4:	0b 00 00 90	adrp	x11, __ZL10cdx12_lock@PAGE
     7a8:	6b 01 00 91	add	x11, x11, __ZL10cdx12_lock@PAGEOFF
     7ac:	68 fd 5f 88	ldaxr	w8, [x11]
     7b0:	1f 01 09 6b	cmp	w8, w9
     7b4:	61 00 00 54	b.ne	0x7c0
     7b8:	6c fd 0a 88	stlxr	w10, w12, [x11]
     7bc:	8a ff ff 35	cbnz	w10, 0x7ac
     7c0:	09 01 09 6b	subs	w9, w8, w9
     7c4:	e8 07 00 b9	str	w8, [sp, #0x4]
     7c8:	e8 0f 00 b9	str	w8, [sp, #0xc]
     7cc:	81 fe ff 54	b.ne	0x79c
     7d0:	01 00 00 14	b	0x7d4
     7d4:	e8 07 40 b9	ldr	w8, [sp, #0x4]
     7d8:	e8 1f 00 b9	str	w8, [sp, #0x1c]
     7dc:	e8 1f 40 b9	ldr	w8, [sp, #0x1c]
     7e0:	68 00 00 34	cbz	w8, 0x7ec
     7e4:	01 00 00 14	b	0x7e8
     7e8:	1d 00 00 14	b	0x85c
     7ec:	e8 37 40 b9	ldr	w8, [sp, #0x34]
     7f0:	09 00 00 90	adrp	x9, __ZL9cdx12_pid@PAGE
     7f4:	28 01 00 b9	str	w8, [x9, __ZL9cdx12_pid@PAGEOFF]
     7f8:	e8 27 40 b9	ldr	w8, [sp, #0x24]
     7fc:	09 00 00 90	adrp	x9, __ZL11cdx12_error@PAGE
     800:	28 01 00 b9	str	w8, [x9, __ZL11cdx12_error@PAGEOFF]
     804:	e8 27 40 b9	ldr	w8, [sp, #0x24]
     808:	08 01 00 71	subs	w8, w8, #0x0
     80c:	e8 17 9f 1a	cset	w8, eq
     810:	09 00 00 90	adrp	x9, __ZL11cdx12_valid@PAGE
     814:	28 01 00 b9	str	w8, [x9, __ZL11cdx12_valid@PAGEOFF]
     818:	e8 27 40 b9	ldr	w8, [sp, #0x24]
     81c:	28 01 00 35	cbnz	w8, 0x840
     820:	01 00 00 14	b	0x824
     824:	00 00 00 90	adrp	x0, __ZL12cdx12_fields@PAGE
     828:	00 00 00 91	add	x0, x0, __ZL12cdx12_fields@PAGEOFF
     82c:	08 08 80 52	mov	w8, #0x40
     830:	e2 03 08 aa	mov	x2, x8
     834:	e1 e3 00 91	add	x1, sp, #0x38
     838:	00 00 00 94	bl	_memcpy
     83c:	01 00 00 14	b	0x840
     840:	08 00 80 52	mov	w8, #0x0
     844:	e8 1b 00 b9	str	w8, [sp, #0x18]
     848:	e8 1b 40 b9	ldr	w8, [sp, #0x18]
     84c:	09 00 00 90	adrp	x9, __ZL10cdx12_lock@PAGE
     850:	29 01 00 91	add	x9, x9, __ZL10cdx12_lock@PAGEOFF
     854:	28 fd 9f 88	stlr	w8, [x9]
     858:	01 00 00 14	b	0x85c
     85c:	a9 83 5f f8	ldur	x9, [x29, #-0x8]
     860:	08 00 00 90	adrp	x8, ___stack_chk_guard@GOTPAGE
     864:	08 01 40 f9	ldr	x8, [x8, ___stack_chk_guard@GOTPAGEOFF]
     868:	08 01 40 f9	ldr	x8, [x8]
     86c:	08 01 09 eb	subs	x8, x8, x9
     870:	41 00 00 54	b.ne	0x878
     874:	02 00 00 14	b	0x87c
     878:	00 00 00 94	bl	___stack_chk_fail
     87c:	fd 7b 48 a9	ldp	x29, x30, [sp, #0x80]
     880:	ff 43 02 91	add	sp, sp, #0x90
     884:	c0 03 5f d6	ret
_cdx12_append_mode_summary:
     888:	ff c3 04 d1	sub	sp, sp, #0x130
     88c:	fc 6f 11 a9	stp	x28, x27, [sp, #0x110]
     890:	fd 7b 12 a9	stp	x29, x30, [sp, #0x120]
     894:	fd 83 04 91	add	x29, sp, #0x120
     898:	08 00 00 90	adrp	x8, ___stack_chk_guard@GOTPAGE
     89c:	08 01 40 f9	ldr	x8, [x8, ___stack_chk_guard@GOTPAGEOFF]
     8a0:	08 01 40 f9	ldr	x8, [x8]
     8a4:	a8 83 1e f8	stur	x8, [x29, #-0x18]
     8a8:	a0 43 1a b8	stur	w0, [x29, #-0x5c]
     8ac:	a1 83 19 f8	stur	x1, [x29, #-0x68]
     8b0:	a2 03 19 f8	stur	x2, [x29, #-0x70]
     8b4:	08 00 80 d2	mov	x8, #0x0
     8b8:	e8 43 00 f9	str	x8, [sp, #0x80]
     8bc:	a8 03 1e f8	stur	x8, [x29, #-0x20]
     8c0:	a8 83 1d f8	stur	x8, [x29, #-0x28]
     8c4:	a8 03 1d f8	stur	x8, [x29, #-0x30]
     8c8:	a8 83 1c f8	stur	x8, [x29, #-0x38]
     8cc:	a8 03 1c f8	stur	x8, [x29, #-0x40]
     8d0:	a8 83 1b f8	stur	x8, [x29, #-0x48]
     8d4:	a8 03 1b f8	stur	x8, [x29, #-0x50]
     8d8:	a8 83 1a f8	stur	x8, [x29, #-0x58]
     8dc:	08 00 80 52	mov	w8, #0x0
     8e0:	a8 c3 18 b8	stur	w8, [x29, #-0x74]
     8e4:	a8 83 18 b8	stur	w8, [x29, #-0x78]
     8e8:	08 00 80 12	mov	w8, #-0x1
     8ec:	a8 43 18 b8	stur	w8, [x29, #-0x7c]
     8f0:	28 00 80 52	mov	w8, #0x1
     8f4:	a8 03 18 b8	stur	w8, [x29, #-0x80]
     8f8:	a8 03 58 b8	ldur	w8, [x29, #-0x80]
     8fc:	e8 8b 00 b9	str	w8, [sp, #0x88]
     900:	08 00 00 90	adrp	x8, __ZL10cdx12_lock@PAGE
     904:	08 01 40 b9	ldr	w8, [x8, __ZL10cdx12_lock@PAGEOFF]
     908:	e8 8f 00 b9	str	w8, [sp, #0x8c]
     90c:	01 00 00 14	b	0x910
     910:	e9 8f 40 b9	ldr	w9, [sp, #0x8c]
     914:	ec 8b 40 b9	ldr	w12, [sp, #0x88]
     918:	0b 00 00 90	adrp	x11, __ZL10cdx12_lock@PAGE
     91c:	6b 01 00 91	add	x11, x11, __ZL10cdx12_lock@PAGEOFF
     920:	68 fd 5f 88	ldaxr	w8, [x11]
     924:	1f 01 09 6b	cmp	w8, w9
     928:	61 00 00 54	b.ne	0x934
     92c:	6c fd 0a 88	stlxr	w10, w12, [x11]
     930:	8a ff ff 35	cbnz	w10, 0x920
     934:	09 01 09 6b	subs	w9, w8, w9
     938:	e8 7f 00 b9	str	w8, [sp, #0x7c]
     93c:	e8 8f 00 b9	str	w8, [sp, #0x8c]
     940:	81 fe ff 54	b.ne	0x910
     944:	01 00 00 14	b	0x948
     948:	e8 7f 40 b9	ldr	w8, [sp, #0x7c]
     94c:	a8 c3 17 b8	stur	w8, [x29, #-0x84]
     950:	a8 c3 57 b8	ldur	w8, [x29, #-0x84]
     954:	a8 00 00 34	cbz	w8, 0x968
     958:	01 00 00 14	b	0x95c
     95c:	28 00 80 52	mov	w8, #0x1
     960:	a8 83 18 b8	stur	w8, [x29, #-0x78]
     964:	1f 00 00 14	b	0x9e0
     968:	a8 43 5a b8	ldur	w8, [x29, #-0x5c]
     96c:	09 00 00 90	adrp	x9, __ZL9cdx12_pid@PAGE
     970:	29 01 40 b9	ldr	w9, [x9, __ZL9cdx12_pid@PAGEOFF]
     974:	08 01 09 6b	subs	w8, w8, w9
     978:	61 02 00 54	b.ne	0x9c4
     97c:	01 00 00 14	b	0x980
     980:	08 00 00 90	adrp	x8, __ZL11cdx12_valid@PAGE
     984:	08 01 40 b9	ldr	w8, [x8, __ZL11cdx12_valid@PAGEOFF]
     988:	a8 c3 18 b8	stur	w8, [x29, #-0x74]
     98c:	08 00 00 90	adrp	x8, __ZL11cdx12_error@PAGE
     990:	08 01 40 b9	ldr	w8, [x8, __ZL11cdx12_error@PAGEOFF]
     994:	a8 43 18 b8	stur	w8, [x29, #-0x7c]
     998:	a8 c3 58 b8	ldur	w8, [x29, #-0x74]
     99c:	28 01 00 34	cbz	w8, 0x9c0
     9a0:	01 00 00 14	b	0x9a4
     9a4:	01 00 00 90	adrp	x1, __ZL12cdx12_fields@PAGE
     9a8:	21 00 00 91	add	x1, x1, __ZL12cdx12_fields@PAGEOFF
     9ac:	08 08 80 52	mov	w8, #0x40
     9b0:	e2 03 08 aa	mov	x2, x8
     9b4:	a0 63 01 d1	sub	x0, x29, #0x58
     9b8:	00 00 00 94	bl	_memcpy
     9bc:	01 00 00 14	b	0x9c0
     9c0:	01 00 00 14	b	0x9c4
     9c4:	08 00 80 52	mov	w8, #0x0
     9c8:	a8 83 17 b8	stur	w8, [x29, #-0x88]
     9cc:	a8 83 57 b8	ldur	w8, [x29, #-0x88]
     9d0:	09 00 00 90	adrp	x9, __ZL10cdx12_lock@PAGE
     9d4:	29 01 00 91	add	x9, x9, __ZL10cdx12_lock@PAGEOFF
     9d8:	28 fd 9f 88	stlr	w8, [x9]
     9dc:	01 00 00 14	b	0x9e0
     9e0:	a8 83 59 f8	ldur	x8, [x29, #-0x68]
     9e4:	a8 00 00 b4	cbz	x8, 0x9f8
     9e8:	01 00 00 14	b	0x9ec
     9ec:	a8 03 59 f8	ldur	x8, [x29, #-0x70]
     9f0:	68 00 00 b5	cbnz	x8, 0x9fc
     9f4:	01 00 00 14	b	0x9f8
     9f8:	3d 00 00 14	b	0xaec
     9fc:	a0 83 59 f8	ldur	x0, [x29, #-0x68]
     a00:	a1 03 59 f8	ldur	x1, [x29, #-0x70]
     a04:	00 00 00 94	bl	_strnlen
     a08:	e0 4b 00 f9	str	x0, [sp, #0x90]
     a0c:	e8 4b 40 f9	ldr	x8, [sp, #0x90]
     a10:	a9 03 59 f8	ldur	x9, [x29, #-0x70]
     a14:	08 01 09 eb	subs	x8, x8, x9
     a18:	01 01 00 54	b.ne	0xa38
     a1c:	01 00 00 14	b	0xa20
     a20:	a9 83 59 f8	ldur	x9, [x29, #-0x68]
     a24:	a8 03 59 f8	ldur	x8, [x29, #-0x70]
     a28:	09 01 09 8b	add	x9, x8, x9
     a2c:	08 00 80 52	mov	w8, #0x0
     a30:	28 f1 1f 38	sturb	w8, [x9, #-0x1]
     a34:	2e 00 00 14	b	0xaec
     a38:	a8 83 59 f8	ldur	x8, [x29, #-0x68]
     a3c:	e9 4b 40 f9	ldr	x9, [sp, #0x90]
     a40:	00 01 09 8b	add	x0, x8, x9
     a44:	a8 03 59 f8	ldur	x8, [x29, #-0x70]
     a48:	01 01 09 eb	subs	x1, x8, x9
     a4c:	ac 83 5a f8	ldur	x12, [x29, #-0x58]
     a50:	ad 03 5b f8	ldur	x13, [x29, #-0x50]
     a54:	ae 83 5b f8	ldur	x14, [x29, #-0x48]
     a58:	af 03 5e f8	ldur	x15, [x29, #-0x20]
     a5c:	b0 03 5c f8	ldur	x16, [x29, #-0x40]
     a60:	b1 83 5c f8	ldur	x17, [x29, #-0x38]
     a64:	a2 03 5d f8	ldur	x2, [x29, #-0x30]
     a68:	a3 83 5d f8	ldur	x3, [x29, #-0x28]
     a6c:	04 00 00 90	adrp	x4, _cdx12_refresh_calls@PAGE
     a70:	09 00 00 90	adrp	x9, _cdx12_refresh_present@PAGE
     a74:	a8 c3 58 b8	ldur	w8, [x29, #-0x74]
     a78:	aa 43 58 b8	ldur	w10, [x29, #-0x7c]
     a7c:	ab 83 58 b8	ldur	w11, [x29, #-0x78]
     a80:	84 00 40 b9	ldr	w4, [x4, _cdx12_refresh_calls@PAGEOFF]
     a84:	29 01 40 b9	ldr	w9, [x9, _cdx12_refresh_present@PAGEOFF]
     a88:	e5 03 09 aa	mov	x5, x9
     a8c:	e9 03 00 91	mov	x9, sp
     a90:	e9 3b 00 f9	str	x9, [sp, #0x70]
     a94:	25 31 00 f9	str	x5, [x9, #0x60]
     a98:	24 2d 00 f9	str	x4, [x9, #0x58]
     a9c:	23 29 00 f9	str	x3, [x9, #0x50]
     aa0:	22 25 00 f9	str	x2, [x9, #0x48]
     aa4:	31 21 00 f9	str	x17, [x9, #0x40]
     aa8:	30 1d 00 f9	str	x16, [x9, #0x38]
     aac:	2f 19 00 f9	str	x15, [x9, #0x30]
     ab0:	2e 15 00 f9	str	x14, [x9, #0x28]
     ab4:	2d 11 00 f9	str	x13, [x9, #0x20]
     ab8:	2c 0d 00 f9	str	x12, [x9, #0x18]
     abc:	2b 09 00 f9	str	x11, [x9, #0x10]
     ac0:	2a 05 00 f9	str	x10, [x9, #0x8]
     ac4:	28 01 00 f9	str	x8, [x9]
     ac8:	02 00 00 90	adrp	x2, l_.str.5@PAGE
     acc:	42 00 00 91	add	x2, x2, l_.str.5@PAGEOFF
     ad0:	00 00 00 94	bl	_snprintf
     ad4:	a9 83 59 f8	ldur	x9, [x29, #-0x68]
     ad8:	a8 03 59 f8	ldur	x8, [x29, #-0x70]
     adc:	09 01 09 8b	add	x9, x8, x9
     ae0:	08 00 80 52	mov	w8, #0x0
     ae4:	28 f1 1f 38	sturb	w8, [x9, #-0x1]
     ae8:	01 00 00 14	b	0xaec
     aec:	a9 83 5e f8	ldur	x9, [x29, #-0x18]
     af0:	08 00 00 90	adrp	x8, ___stack_chk_guard@GOTPAGE
     af4:	08 01 40 f9	ldr	x8, [x8, ___stack_chk_guard@GOTPAGEOFF]
     af8:	08 01 40 f9	ldr	x8, [x8]
     afc:	08 01 09 eb	subs	x8, x8, x9
     b00:	41 00 00 54	b.ne	0xb08
     b04:	02 00 00 14	b	0xb0c
     b08:	00 00 00 94	bl	___stack_chk_fail
     b0c:	fd 7b 52 a9	ldp	x29, x30, [sp, #0x120]
     b10:	fc 6f 51 a9	ldp	x28, x27, [sp, #0x110]
     b14:	ff c3 04 91	add	sp, sp, #0x130
     b18:	c0 03 5f d6	ret
_cdx13_capture_validity:
     b1c:	ff c3 00 d1	sub	sp, sp, #0x30
     b20:	e0 2f 00 b9	str	w0, [sp, #0x2c]
     b24:	e1 13 00 f9	str	x1, [sp, #0x20]
     b28:	28 00 80 52	mov	w8, #0x1
     b2c:	e8 1f 00 b9	str	w8, [sp, #0x1c]
     b30:	e8 1f 40 b9	ldr	w8, [sp, #0x1c]
     b34:	e8 0f 00 b9	str	w8, [sp, #0xc]
     b38:	08 00 00 90	adrp	x8, __ZL13cdx13_vc_lock@PAGE
     b3c:	08 01 40 b9	ldr	w8, [x8, __ZL13cdx13_vc_lock@PAGEOFF]
     b40:	e8 13 00 b9	str	w8, [sp, #0x10]
     b44:	01 00 00 14	b	0xb48
     b48:	e9 13 40 b9	ldr	w9, [sp, #0x10]
     b4c:	ec 0f 40 b9	ldr	w12, [sp, #0xc]
     b50:	0b 00 00 90	adrp	x11, __ZL13cdx13_vc_lock@PAGE
     b54:	6b 01 00 91	add	x11, x11, __ZL13cdx13_vc_lock@PAGEOFF
     b58:	68 fd 5f 88	ldaxr	w8, [x11]
     b5c:	1f 01 09 6b	cmp	w8, w9
     b60:	61 00 00 54	b.ne	0xb6c
     b64:	6c fd 0a 88	stlxr	w10, w12, [x11]
     b68:	8a ff ff 35	cbnz	w10, 0xb58
     b6c:	09 01 09 6b	subs	w9, w8, w9
     b70:	e8 0b 00 b9	str	w8, [sp, #0x8]
     b74:	e8 13 00 b9	str	w8, [sp, #0x10]
     b78:	81 fe ff 54	b.ne	0xb48
     b7c:	01 00 00 14	b	0xb80
     b80:	e8 0b 40 b9	ldr	w8, [sp, #0x8]
     b84:	e8 1b 00 b9	str	w8, [sp, #0x18]
     b88:	e8 1b 40 b9	ldr	w8, [sp, #0x18]
     b8c:	68 00 00 34	cbz	w8, 0xb98
     b90:	01 00 00 14	b	0xb94
     b94:	11 00 00 14	b	0xbd8
     b98:	e8 2f 40 b9	ldr	w8, [sp, #0x2c]
     b9c:	09 00 00 90	adrp	x9, __ZL12cdx13_vc_pid@PAGE
     ba0:	28 01 00 b9	str	w8, [x9, __ZL12cdx13_vc_pid@PAGEOFF]
     ba4:	e8 13 40 f9	ldr	x8, [sp, #0x20]
     ba8:	09 00 00 90	adrp	x9, __ZL8cdx13_vc@PAGE
     bac:	28 01 00 f9	str	x8, [x9, __ZL8cdx13_vc@PAGEOFF]
     bb0:	09 00 00 90	adrp	x9, __ZL14cdx13_vc_valid@PAGE
     bb4:	28 00 80 52	mov	w8, #0x1
     bb8:	28 01 00 b9	str	w8, [x9, __ZL14cdx13_vc_valid@PAGEOFF]
     bbc:	08 00 80 52	mov	w8, #0x0
     bc0:	e8 17 00 b9	str	w8, [sp, #0x14]
     bc4:	e8 17 40 b9	ldr	w8, [sp, #0x14]
     bc8:	09 00 00 90	adrp	x9, __ZL13cdx13_vc_lock@PAGE
     bcc:	29 01 00 91	add	x9, x9, __ZL13cdx13_vc_lock@PAGEOFF
     bd0:	28 fd 9f 88	stlr	w8, [x9]
     bd4:	01 00 00 14	b	0xbd8
     bd8:	ff c3 00 91	add	sp, sp, #0x30
     bdc:	c0 03 5f d6	ret
_cdx13_append_mode_summary:
     be0:	ff c3 07 d1	sub	sp, sp, #0x1f0
     be4:	f6 57 1c a9	stp	x22, x21, [sp, #0x1c0]
     be8:	f4 4f 1d a9	stp	x20, x19, [sp, #0x1d0]
     bec:	fd 7b 1e a9	stp	x29, x30, [sp, #0x1e0]
     bf0:	fd 83 07 91	add	x29, sp, #0x1e0
     bf4:	08 00 00 90	adrp	x8, ___stack_chk_guard@GOTPAGE
     bf8:	08 01 40 f9	ldr	x8, [x8, ___stack_chk_guard@GOTPAGEOFF]
     bfc:	08 01 40 f9	ldr	x8, [x8]
     c00:	a8 83 1d f8	stur	x8, [x29, #-0x28]
     c04:	a0 43 19 b8	stur	w0, [x29, #-0x6c]
     c08:	a1 83 18 f8	stur	x1, [x29, #-0x78]
     c0c:	a2 03 18 f8	stur	x2, [x29, #-0x80]
     c10:	08 00 80 d2	mov	x8, #0x0
     c14:	a8 03 13 f8	stur	x8, [x29, #-0xd0]
     c18:	a8 03 1d f8	stur	x8, [x29, #-0x30]
     c1c:	a8 83 1c f8	stur	x8, [x29, #-0x38]
     c20:	a8 03 1c f8	stur	x8, [x29, #-0x40]
     c24:	a8 83 1b f8	stur	x8, [x29, #-0x48]
     c28:	a8 03 1b f8	stur	x8, [x29, #-0x50]
     c2c:	a8 83 1a f8	stur	x8, [x29, #-0x58]
     c30:	a8 03 1a f8	stur	x8, [x29, #-0x60]
     c34:	a8 83 19 f8	stur	x8, [x29, #-0x68]
     c38:	08 00 80 52	mov	w8, #0x0
     c3c:	a8 c3 17 b8	stur	w8, [x29, #-0x84]
     c40:	a8 83 17 b8	stur	w8, [x29, #-0x88]
     c44:	08 00 80 12	mov	w8, #-0x1
     c48:	a8 43 17 b8	stur	w8, [x29, #-0x8c]
     c4c:	28 00 80 52	mov	w8, #0x1
     c50:	a8 03 17 b8	stur	w8, [x29, #-0x90]
     c54:	a8 03 57 b8	ldur	w8, [x29, #-0x90]
     c58:	a8 83 13 b8	stur	w8, [x29, #-0xc8]
     c5c:	08 00 00 90	adrp	x8, __ZL10cdx12_lock@PAGE
     c60:	08 01 40 b9	ldr	w8, [x8, __ZL10cdx12_lock@PAGEOFF]
     c64:	a8 c3 13 b8	stur	w8, [x29, #-0xc4]
     c68:	01 00 00 14	b	0xc6c
     c6c:	a9 c3 53 b8	ldur	w9, [x29, #-0xc4]
     c70:	ac 83 53 b8	ldur	w12, [x29, #-0xc8]
     c74:	0b 00 00 90	adrp	x11, __ZL10cdx12_lock@PAGE
     c78:	6b 01 00 91	add	x11, x11, __ZL10cdx12_lock@PAGEOFF
     c7c:	68 fd 5f 88	ldaxr	w8, [x11]
     c80:	1f 01 09 6b	cmp	w8, w9
     c84:	61 00 00 54	b.ne	0xc90
     c88:	6c fd 0a 88	stlxr	w10, w12, [x11]
     c8c:	8a ff ff 35	cbnz	w10, 0xc7c
     c90:	09 01 09 6b	subs	w9, w8, w9
     c94:	a8 c3 12 b8	stur	w8, [x29, #-0xd4]
     c98:	a8 c3 13 b8	stur	w8, [x29, #-0xc4]
     c9c:	81 fe ff 54	b.ne	0xc6c
     ca0:	01 00 00 14	b	0xca4
     ca4:	a8 c3 52 b8	ldur	w8, [x29, #-0xd4]
     ca8:	a8 c3 16 b8	stur	w8, [x29, #-0x94]
     cac:	a8 c3 56 b8	ldur	w8, [x29, #-0x94]
     cb0:	a8 00 00 34	cbz	w8, 0xcc4
     cb4:	01 00 00 14	b	0xcb8
     cb8:	28 00 80 52	mov	w8, #0x1
     cbc:	a8 83 17 b8	stur	w8, [x29, #-0x88]
     cc0:	1f 00 00 14	b	0xd3c
     cc4:	a8 43 59 b8	ldur	w8, [x29, #-0x6c]
     cc8:	09 00 00 90	adrp	x9, __ZL9cdx12_pid@PAGE
     ccc:	29 01 40 b9	ldr	w9, [x9, __ZL9cdx12_pid@PAGEOFF]
     cd0:	08 01 09 6b	subs	w8, w8, w9
     cd4:	61 02 00 54	b.ne	0xd20
     cd8:	01 00 00 14	b	0xcdc
     cdc:	08 00 00 90	adrp	x8, __ZL11cdx12_valid@PAGE
     ce0:	08 01 40 b9	ldr	w8, [x8, __ZL11cdx12_valid@PAGEOFF]
     ce4:	a8 c3 17 b8	stur	w8, [x29, #-0x84]
     ce8:	08 00 00 90	adrp	x8, __ZL11cdx12_error@PAGE
     cec:	08 01 40 b9	ldr	w8, [x8, __ZL11cdx12_error@PAGEOFF]
     cf0:	a8 43 17 b8	stur	w8, [x29, #-0x8c]
     cf4:	a8 c3 57 b8	ldur	w8, [x29, #-0x84]
     cf8:	28 01 00 34	cbz	w8, 0xd1c
     cfc:	01 00 00 14	b	0xd00
     d00:	01 00 00 90	adrp	x1, __ZL12cdx12_fields@PAGE
     d04:	21 00 00 91	add	x1, x1, __ZL12cdx12_fields@PAGEOFF
     d08:	08 08 80 52	mov	w8, #0x40
     d0c:	e2 03 08 aa	mov	x2, x8
     d10:	a0 a3 01 d1	sub	x0, x29, #0x68
     d14:	00 00 00 94	bl	_memcpy
     d18:	01 00 00 14	b	0xd1c
     d1c:	01 00 00 14	b	0xd20
     d20:	08 00 80 52	mov	w8, #0x0
     d24:	a8 83 16 b8	stur	w8, [x29, #-0x98]
     d28:	a8 83 56 b8	ldur	w8, [x29, #-0x98]
     d2c:	09 00 00 90	adrp	x9, __ZL10cdx12_lock@PAGE
     d30:	29 01 00 91	add	x9, x9, __ZL10cdx12_lock@PAGEOFF
     d34:	28 fd 9f 88	stlr	w8, [x9]
     d38:	01 00 00 14	b	0xd3c
     d3c:	08 00 80 52	mov	w8, #0x0
     d40:	a8 43 16 b8	stur	w8, [x29, #-0x9c]
     d44:	08 00 80 d2	mov	x8, #0x0
     d48:	a8 83 15 f8	stur	x8, [x29, #-0xa8]
     d4c:	28 00 80 52	mov	w8, #0x1
     d50:	a8 43 15 b8	stur	w8, [x29, #-0xac]
     d54:	a8 43 55 b8	ldur	w8, [x29, #-0xac]
     d58:	a8 43 12 b8	stur	w8, [x29, #-0xdc]
     d5c:	08 00 00 90	adrp	x8, __ZL13cdx13_vc_lock@PAGE
     d60:	08 01 40 b9	ldr	w8, [x8, __ZL13cdx13_vc_lock@PAGEOFF]
     d64:	a8 83 12 b8	stur	w8, [x29, #-0xd8]
     d68:	01 00 00 14	b	0xd6c
     d6c:	a9 83 52 b8	ldur	w9, [x29, #-0xd8]
     d70:	ac 43 52 b8	ldur	w12, [x29, #-0xdc]
     d74:	0b 00 00 90	adrp	x11, __ZL13cdx13_vc_lock@PAGE
     d78:	6b 01 00 91	add	x11, x11, __ZL13cdx13_vc_lock@PAGEOFF
     d7c:	68 fd 5f 88	ldaxr	w8, [x11]
     d80:	1f 01 09 6b	cmp	w8, w9
     d84:	61 00 00 54	b.ne	0xd90
     d88:	6c fd 0a 88	stlxr	w10, w12, [x11]
     d8c:	8a ff ff 35	cbnz	w10, 0xd7c
     d90:	09 01 09 6b	subs	w9, w8, w9
     d94:	a8 03 12 b8	stur	w8, [x29, #-0xe0]
     d98:	a8 83 12 b8	stur	w8, [x29, #-0xd8]
     d9c:	81 fe ff 54	b.ne	0xd6c
     da0:	01 00 00 14	b	0xda4
     da4:	a8 03 52 b8	ldur	w8, [x29, #-0xe0]
     da8:	a8 03 15 b8	stur	w8, [x29, #-0xb0]
     dac:	a8 03 55 b8	ldur	w8, [x29, #-0xb0]
     db0:	28 03 00 35	cbnz	w8, 0xe14
     db4:	01 00 00 14	b	0xdb8
     db8:	08 00 00 90	adrp	x8, __ZL14cdx13_vc_valid@PAGE
     dbc:	08 01 40 b9	ldr	w8, [x8, __ZL14cdx13_vc_valid@PAGEOFF]
     dc0:	c8 01 00 34	cbz	w8, 0xdf8
     dc4:	01 00 00 14	b	0xdc8
     dc8:	08 00 00 90	adrp	x8, __ZL12cdx13_vc_pid@PAGE
     dcc:	08 01 40 b9	ldr	w8, [x8, __ZL12cdx13_vc_pid@PAGEOFF]
     dd0:	a9 43 59 b8	ldur	w9, [x29, #-0x6c]
     dd4:	08 01 09 6b	subs	w8, w8, w9
     dd8:	01 01 00 54	b.ne	0xdf8
     ddc:	01 00 00 14	b	0xde0
     de0:	28 00 80 52	mov	w8, #0x1
     de4:	a8 43 16 b8	stur	w8, [x29, #-0x9c]
     de8:	08 00 00 90	adrp	x8, __ZL8cdx13_vc@PAGE
     dec:	08 01 40 f9	ldr	x8, [x8, __ZL8cdx13_vc@PAGEOFF]
     df0:	a8 83 15 f8	stur	x8, [x29, #-0xa8]
     df4:	01 00 00 14	b	0xdf8
     df8:	08 00 80 52	mov	w8, #0x0
     dfc:	a8 c3 14 b8	stur	w8, [x29, #-0xb4]
     e00:	a8 c3 54 b8	ldur	w8, [x29, #-0xb4]
     e04:	09 00 00 90	adrp	x9, __ZL13cdx13_vc_lock@PAGE
     e08:	29 01 00 91	add	x9, x9, __ZL13cdx13_vc_lock@PAGEOFF
     e0c:	28 fd 9f 88	stlr	w8, [x9]
     e10:	01 00 00 14	b	0xe14
     e14:	a8 83 58 f8	ldur	x8, [x29, #-0x78]
     e18:	a8 00 00 b4	cbz	x8, 0xe2c
     e1c:	01 00 00 14	b	0xe20
     e20:	a8 03 58 f8	ldur	x8, [x29, #-0x80]
     e24:	68 00 00 b5	cbnz	x8, 0xe30
     e28:	01 00 00 14	b	0xe2c
     e2c:	70 00 00 14	b	0xfec
     e30:	a0 83 58 f8	ldur	x0, [x29, #-0x78]
     e34:	a1 03 58 f8	ldur	x1, [x29, #-0x80]
     e38:	00 00 00 94	bl	_strnlen
     e3c:	a0 03 14 f8	stur	x0, [x29, #-0xc0]
     e40:	a8 03 54 f8	ldur	x8, [x29, #-0xc0]
     e44:	a9 03 58 f8	ldur	x9, [x29, #-0x80]
     e48:	08 01 09 eb	subs	x8, x8, x9
     e4c:	01 01 00 54	b.ne	0xe6c
     e50:	01 00 00 14	b	0xe54
     e54:	a9 83 58 f8	ldur	x9, [x29, #-0x78]
     e58:	a8 03 58 f8	ldur	x8, [x29, #-0x80]
     e5c:	09 01 09 8b	add	x9, x8, x9
     e60:	08 00 80 52	mov	w8, #0x0
     e64:	28 f1 1f 38	sturb	w8, [x9, #-0x1]
     e68:	61 00 00 14	b	0xfec
     e6c:	a8 83 58 f8	ldur	x8, [x29, #-0x78]
     e70:	a9 03 54 f8	ldur	x9, [x29, #-0xc0]
     e74:	00 01 09 8b	add	x0, x8, x9
     e78:	e0 57 00 f9	str	x0, [sp, #0xa8]
     e7c:	a8 03 58 f8	ldur	x8, [x29, #-0x80]
     e80:	00 01 09 eb	subs	x0, x8, x9
     e84:	e0 5b 00 f9	str	x0, [sp, #0xb0]
     e88:	a8 c3 57 b8	ldur	w8, [x29, #-0x84]
     e8c:	e0 03 08 aa	mov	x0, x8
     e90:	e0 bf 00 b9	str	w0, [sp, #0xbc]
     e94:	a0 43 57 b8	ldur	w0, [x29, #-0x8c]
     e98:	e0 c3 00 b9	str	w0, [sp, #0xc0]
     e9c:	a0 83 57 b8	ldur	w0, [x29, #-0x88]
     ea0:	e0 c7 00 b9	str	w0, [sp, #0xc4]
     ea4:	a9 83 59 f8	ldur	x9, [x29, #-0x68]
     ea8:	e9 67 00 f9	str	x9, [sp, #0xc8]
     eac:	a9 03 5a f8	ldur	x9, [x29, #-0x60]
     eb0:	e9 6b 00 f9	str	x9, [sp, #0xd0]
     eb4:	a9 83 5a f8	ldur	x9, [x29, #-0x58]
     eb8:	e9 6f 00 f9	str	x9, [sp, #0xd8]
     ebc:	a9 03 5b f8	ldur	x9, [x29, #-0x50]
     ec0:	e9 73 00 f9	str	x9, [sp, #0xe0]
     ec4:	a9 83 5b f8	ldur	x9, [x29, #-0x48]
     ec8:	e9 77 00 f9	str	x9, [sp, #0xe8]
     ecc:	a0 43 56 b8	ldur	w0, [x29, #-0x9c]
     ed0:	a0 43 11 b8	stur	w0, [x29, #-0xec]
     ed4:	a9 83 55 f8	ldur	x9, [x29, #-0xa8]
     ed8:	a9 83 11 f8	stur	x9, [x29, #-0xe8]
     edc:	c8 00 00 34	cbz	w8, 0xef4
     ee0:	01 00 00 14	b	0xee4
     ee4:	a0 a3 01 d1	sub	x0, x29, #0x68
     ee8:	00 00 00 94	bl	__ZL19cdx13_scalar_issuesPKy
     eec:	e0 a7 00 b9	str	w0, [sp, #0xa4]
     ef0:	04 00 00 14	b	0xf00
     ef4:	00 00 80 12	mov	w0, #-0x1
     ef8:	e0 a7 00 b9	str	w0, [sp, #0xa4]
     efc:	01 00 00 14	b	0xf00
     f00:	e1 5b 40 f9	ldr	x1, [sp, #0xb0]
     f04:	e0 57 40 f9	ldr	x0, [sp, #0xa8]
     f08:	e2 bf 40 b9	ldr	w2, [sp, #0xbc]
     f0c:	e3 c3 40 b9	ldr	w3, [sp, #0xc0]
     f10:	e4 c7 40 b9	ldr	w4, [sp, #0xc4]
     f14:	e8 67 40 f9	ldr	x8, [sp, #0xc8]
     f18:	ea 6b 40 f9	ldr	x10, [sp, #0xd0]
     f1c:	eb 6f 40 f9	ldr	x11, [sp, #0xd8]
     f20:	ec 73 40 f9	ldr	x12, [sp, #0xe0]
     f24:	ed 77 40 f9	ldr	x13, [sp, #0xe8]
     f28:	a5 43 51 b8	ldur	w5, [x29, #-0xec]
     f2c:	ae 83 51 f8	ldur	x14, [x29, #-0xe8]
     f30:	e6 a7 40 b9	ldr	w6, [sp, #0xa4]
     f34:	af 03 5c f8	ldur	x15, [x29, #-0x40]
     f38:	b0 83 5c f8	ldur	x16, [x29, #-0x38]
     f3c:	b1 03 5d f8	ldur	x17, [x29, #-0x30]
     f40:	07 00 00 90	adrp	x7, _cdx13_ui_requested@PAGE
     f44:	13 00 00 90	adrp	x19, _cdx13_ui_readback@PAGE
     f48:	14 00 00 90	adrp	x20, _cdx13_ui_status@PAGE
     f4c:	09 00 00 90	adrp	x9, _cdx13_ui_writes@PAGE
     f50:	e7 00 40 b9	ldr	w7, [x7, _cdx13_ui_requested@PAGEOFF]
     f54:	73 02 40 b9	ldr	w19, [x19, _cdx13_ui_readback@PAGEOFF]
     f58:	94 02 40 b9	ldr	w20, [x20, _cdx13_ui_status@PAGEOFF]
     f5c:	29 01 40 b9	ldr	w9, [x9, _cdx13_ui_writes@PAGEOFF]
     f60:	f5 03 09 aa	mov	x21, x9
     f64:	e9 03 00 91	mov	x9, sp
     f68:	e9 4f 00 f9	str	x9, [sp, #0x98]
     f6c:	35 45 00 f9	str	x21, [x9, #0x88]
     f70:	34 41 00 f9	str	x20, [x9, #0x80]
     f74:	33 3d 00 f9	str	x19, [x9, #0x78]
     f78:	27 39 00 f9	str	x7, [x9, #0x70]
     f7c:	31 35 00 f9	str	x17, [x9, #0x68]
     f80:	30 31 00 f9	str	x16, [x9, #0x60]
     f84:	2f 2d 00 f9	str	x15, [x9, #0x58]
     f88:	ef 03 06 aa	mov	x15, x6
     f8c:	2f 29 00 f9	str	x15, [x9, #0x50]
     f90:	2e 25 00 f9	str	x14, [x9, #0x48]
     f94:	ee 03 05 aa	mov	x14, x5
     f98:	2e 21 00 f9	str	x14, [x9, #0x40]
     f9c:	2d 1d 00 f9	str	x13, [x9, #0x38]
     fa0:	2c 19 00 f9	str	x12, [x9, #0x30]
     fa4:	2b 15 00 f9	str	x11, [x9, #0x28]
     fa8:	2a 11 00 f9	str	x10, [x9, #0x20]
     fac:	28 0d 00 f9	str	x8, [x9, #0x18]
     fb0:	e8 03 04 aa	mov	x8, x4
     fb4:	28 09 00 f9	str	x8, [x9, #0x10]
     fb8:	e8 03 03 aa	mov	x8, x3
     fbc:	28 05 00 f9	str	x8, [x9, #0x8]
     fc0:	e8 03 02 aa	mov	x8, x2
     fc4:	28 01 00 f9	str	x8, [x9]
     fc8:	02 00 00 90	adrp	x2, l_.str.6@PAGE
     fcc:	42 00 00 91	add	x2, x2, l_.str.6@PAGEOFF
     fd0:	00 00 00 94	bl	_snprintf
     fd4:	a9 83 58 f8	ldur	x9, [x29, #-0x78]
     fd8:	a8 03 58 f8	ldur	x8, [x29, #-0x80]
     fdc:	09 01 09 8b	add	x9, x8, x9
     fe0:	08 00 80 52	mov	w8, #0x0
     fe4:	28 f1 1f 38	sturb	w8, [x9, #-0x1]
     fe8:	01 00 00 14	b	0xfec
     fec:	a9 83 5d f8	ldur	x9, [x29, #-0x28]
     ff0:	08 00 00 90	adrp	x8, ___stack_chk_guard@GOTPAGE
     ff4:	08 01 40 f9	ldr	x8, [x8, ___stack_chk_guard@GOTPAGEOFF]
     ff8:	08 01 40 f9	ldr	x8, [x8]
     ffc:	08 01 09 eb	subs	x8, x8, x9
    1000:	41 00 00 54	b.ne	0x1008
    1004:	02 00 00 14	b	0x100c
    1008:	00 00 00 94	bl	___stack_chk_fail
    100c:	fd 7b 5e a9	ldp	x29, x30, [sp, #0x1e0]
    1010:	f4 4f 5d a9	ldp	x20, x19, [sp, #0x1d0]
    1014:	f6 57 5c a9	ldp	x22, x21, [sp, #0x1c0]
    1018:	ff c3 07 91	add	sp, sp, #0x1f0
    101c:	c0 03 5f d6	ret
__ZL19cdx13_scalar_issuesPKy:
    1020:	ff 83 00 d1	sub	sp, sp, #0x20
    1024:	fd 7b 01 a9	stp	x29, x30, [sp, #0x10]
    1028:	fd 43 00 91	add	x29, sp, #0x10
    102c:	e0 07 00 f9	str	x0, [sp, #0x8]
    1030:	08 00 80 52	mov	w8, #0x0
    1034:	e8 07 00 b9	str	w8, [sp, #0x4]
    1038:	e8 07 40 f9	ldr	x8, [sp, #0x8]
    103c:	08 01 40 f9	ldr	x8, [x8]
    1040:	a8 02 00 b4	cbz	x8, 0x1094
    1044:	01 00 00 14	b	0x1048
    1048:	e8 07 40 f9	ldr	x8, [sp, #0x8]
    104c:	08 05 40 f9	ldr	x8, [x8, #0x8]
    1050:	28 02 00 b4	cbz	x8, 0x1094
    1054:	01 00 00 14	b	0x1058
    1058:	e8 07 40 f9	ldr	x8, [sp, #0x8]
    105c:	08 01 40 f9	ldr	x8, [x8]
    1060:	08 05 00 b1	adds	x8, x8, #0x1
    1064:	80 01 00 54	b.eq	0x1094
    1068:	01 00 00 14	b	0x106c
    106c:	e8 07 40 f9	ldr	x8, [sp, #0x8]
    1070:	08 05 40 f9	ldr	x8, [x8, #0x8]
    1074:	08 05 00 b1	adds	x8, x8, #0x1
    1078:	e0 00 00 54	b.eq	0x1094
    107c:	01 00 00 14	b	0x1080
    1080:	e8 07 40 f9	ldr	x8, [sp, #0x8]
    1084:	08 09 40 f9	ldr	x8, [x8, #0x10]
    1088:	08 05 00 b1	adds	x8, x8, #0x1
    108c:	c1 00 00 54	b.ne	0x10a4
    1090:	01 00 00 14	b	0x1094
    1094:	e8 07 40 b9	ldr	w8, [sp, #0x4]
    1098:	08 01 00 32	orr	w8, w8, #0x1
    109c:	e8 07 00 b9	str	w8, [sp, #0x4]
    10a0:	01 00 00 14	b	0x10a4
    10a4:	e8 07 40 f9	ldr	x8, [sp, #0x8]
    10a8:	00 0d 40 f9	ldr	x0, [x8, #0x18]
    10ac:	00 00 00 94	bl	__ZL24cdx13_nonnegative_finitey
    10b0:	60 01 00 34	cbz	w0, 0x10dc
    10b4:	01 00 00 14	b	0x10b8
    10b8:	e8 07 40 f9	ldr	x8, [sp, #0x8]
    10bc:	00 11 40 f9	ldr	x0, [x8, #0x20]
    10c0:	00 00 00 94	bl	__ZL24cdx13_nonnegative_finitey
    10c4:	c0 00 00 34	cbz	w0, 0x10dc
    10c8:	01 00 00 14	b	0x10cc
    10cc:	e8 07 40 f9	ldr	x8, [sp, #0x8]
    10d0:	08 11 40 f9	ldr	x8, [x8, #0x20]
    10d4:	c8 00 00 b5	cbnz	x8, 0x10ec
    10d8:	01 00 00 14	b	0x10dc
    10dc:	e8 07 40 b9	ldr	w8, [sp, #0x4]
    10e0:	08 01 1f 32	orr	w8, w8, #0x2
    10e4:	e8 07 00 b9	str	w8, [sp, #0x4]
    10e8:	01 00 00 14	b	0x10ec
    10ec:	e8 07 40 f9	ldr	x8, [sp, #0x8]
    10f0:	08 09 40 f9	ldr	x8, [x8, #0x10]
    10f4:	88 01 00 b5	cbnz	x8, 0x1124
    10f8:	01 00 00 14	b	0x10fc
    10fc:	e8 07 40 f9	ldr	x8, [sp, #0x8]
    1100:	08 0d 40 f9	ldr	x8, [x8, #0x18]
    1104:	08 f9 74 d3	ubfx	x8, x8, #52, #11
    1108:	08 29 0f f1	subs	x8, x8, #0x3ca
    110c:	c8 00 00 54	b.hi	0x1124
    1110:	01 00 00 14	b	0x1114
    1114:	e8 07 40 b9	ldr	w8, [sp, #0x4]
    1118:	08 01 1e 32	orr	w8, w8, #0x4
    111c:	e8 07 00 b9	str	w8, [sp, #0x4]
    1120:	01 00 00 14	b	0x1124
    1124:	e8 07 40 f9	ldr	x8, [sp, #0x8]
    1128:	08 15 40 f9	ldr	x8, [x8, #0x28]
    112c:	08 05 00 f1	subs	x8, x8, #0x1
    1130:	88 01 00 54	b.hi	0x1160
    1134:	01 00 00 14	b	0x1138
    1138:	e8 07 40 f9	ldr	x8, [sp, #0x8]
    113c:	08 19 40 f9	ldr	x8, [x8, #0x30]
    1140:	08 09 00 f1	subs	x8, x8, #0x2
    1144:	e8 00 00 54	b.hi	0x1160
    1148:	01 00 00 14	b	0x114c
    114c:	e8 07 40 f9	ldr	x8, [sp, #0x8]
    1150:	08 1d 40 f9	ldr	x8, [x8, #0x38]
    1154:	08 11 00 f1	subs	x8, x8, #0x4
    1158:	c3 00 00 54	b.lo	0x1170
    115c:	01 00 00 14	b	0x1160
    1160:	e8 07 40 b9	ldr	w8, [sp, #0x4]
    1164:	08 01 1d 32	orr	w8, w8, #0x8
    1168:	e8 07 00 b9	str	w8, [sp, #0x4]
    116c:	01 00 00 14	b	0x1170
    1170:	e0 07 40 b9	ldr	w0, [sp, #0x4]
    1174:	fd 7b 41 a9	ldp	x29, x30, [sp, #0x10]
    1178:	ff 83 00 91	add	sp, sp, #0x20
    117c:	c0 03 5f d6	ret
__ZL24cdx13_nonnegative_finitey:
    1180:	ff 43 00 d1	sub	sp, sp, #0x10
    1184:	e0 07 00 f9	str	x0, [sp, #0x8]
    1188:	e8 07 40 f9	ldr	x8, [sp, #0x8]
    118c:	08 fd 7f d3	lsr	x8, x8, #63
    1190:	09 00 80 52	mov	w9, #0x0
    1194:	e9 07 00 b9	str	w9, [sp, #0x4]
    1198:	48 01 00 b5	cbnz	x8, 0x11c0
    119c:	01 00 00 14	b	0x11a0
    11a0:	e8 07 40 f9	ldr	x8, [sp, #0x8]
    11a4:	08 fd 74 d3	lsr	x8, x8, #52
    11a8:	e9 03 28 2a	mvn	w9, w8
    11ac:	e8 03 09 aa	mov	x8, x9
    11b0:	08 29 40 f2	ands	x8, x8, #0x7ff
    11b4:	e8 07 9f 1a	cset	w8, ne
    11b8:	e8 07 00 b9	str	w8, [sp, #0x4]
    11bc:	01 00 00 14	b	0x11c0
    11c0:	e8 07 40 b9	ldr	w8, [sp, #0x4]
    11c4:	00 01 00 12	and	w0, w8, #0x1
    11c8:	ff 43 00 91	add	sp, sp, #0x10
    11cc:	c0 03 5f d6	ret
