D:\Codex\tmp\stage14-host\provider-arm64.o:
(__TEXT,__text) section
_cdx14_frame_gap:
       0:	ff 83 00 d1	sub	sp, sp, #0x20
       4:	fd 7b 01 a9	stp	x29, x30, [sp, #0x10]
       8:	fd 43 00 91	add	x29, sp, #0x10
       c:	09 00 00 90	adrp	x9, __ZL14cdx14_inflight@PAGE
      10:	08 00 80 52	mov	w8, #0x0
      14:	28 01 00 39	strb	w8, [x9, __ZL14cdx14_inflight@PAGEOFF]
      18:	09 00 00 90	adrp	x9, __ZL18cdx14_has_previous@PAGE
      1c:	28 01 00 39	strb	w8, [x9, __ZL18cdx14_has_previous@PAGEOFF]
      20:	00 00 00 90	adrp	x0, l_.str@PAGE
      24:	00 00 00 91	add	x0, x0, l_.str@PAGEOFF
      28:	00 00 00 94	bl	__Z6optionPKc
      2c:	08 04 00 71	subs	w8, w0, #0x1
      30:	61 02 00 54	b.ne	0x7c
      34:	01 00 00 14	b	0x38
      38:	08 00 00 90	adrp	x8, 4 ; 0x0
      3c:	09 01 40 b9	ldr	w9, [x8]
      40:	29 05 00 11	add	w9, w9, #0x1
      44:	09 01 00 b9	str	w9, [x8]
      48:	08 01 40 b9	ldr	w8, [x8]
      4c:	08 11 00 71	subs	w8, w8, #0x4
      50:	48 01 00 54	b.hi	0x78
      54:	01 00 00 14	b	0x58
      58:	08 00 00 90	adrp	x8, 4 ; 0x0
      5c:	08 01 40 b9	ldr	w8, [x8]
      60:	e9 03 00 91	mov	x9, sp
      64:	28 01 00 f9	str	x8, [x9]
      68:	00 00 00 90	adrp	x0, l_.str.1@PAGE
      6c:	00 00 00 91	add	x0, x0, l_.str.1@PAGEOFF
      70:	00 00 00 94	bl	__Z5IOLogPKcz
      74:	01 00 00 14	b	0x78
      78:	01 00 00 14	b	0x7c
      7c:	fd 7b 41 a9	ldp	x29, x30, [sp, #0x10]
      80:	ff 83 00 91	add	sp, sp, #0x20
      84:	c0 03 5f d6	ret
_cdx14_frame_begin:
      88:	ff 83 01 d1	sub	sp, sp, #0x60
      8c:	fd 7b 05 a9	stp	x29, x30, [sp, #0x50]
      90:	fd 43 01 91	add	x29, sp, #0x50
      94:	a0 83 1f f8	stur	x0, [x29, #-0x8]
      98:	a1 03 1f f8	stur	x1, [x29, #-0x10]
      9c:	a2 83 1e f8	stur	x2, [x29, #-0x18]
      a0:	a3 03 1e f8	stur	x3, [x29, #-0x20]
      a4:	e4 17 00 f9	str	x4, [sp, #0x28]
      a8:	e5 13 00 f9	str	x5, [sp, #0x20]
      ac:	e6 1f 00 b9	str	w6, [sp, #0x1c]
      b0:	e7 1b 00 b9	str	w7, [sp, #0x18]
      b4:	09 00 00 90	adrp	x9, __ZL14cdx14_inflight@PAGE
      b8:	08 00 80 52	mov	w8, #0x0
      bc:	28 01 00 39	strb	w8, [x9, __ZL14cdx14_inflight@PAGEOFF]
      c0:	00 00 00 90	adrp	x0, l_.str@PAGE
      c4:	00 00 00 91	add	x0, x0, l_.str@PAGEOFF
      c8:	00 00 00 94	bl	__Z6optionPKc
      cc:	08 04 00 71	subs	w8, w0, #0x1
      d0:	60 00 00 54	b.eq	0xdc
      d4:	01 00 00 14	b	0xd8
      d8:	90 00 00 14	b	0x318
      dc:	08 00 00 90	adrp	x8, __ZL11cdx14_frame@PAGE
      e0:	09 01 40 f9	ldr	x9, [x8, __ZL11cdx14_frame@PAGEOFF]
      e4:	29 05 00 91	add	x9, x9, #0x1
      e8:	09 01 00 f9	str	x9, [x8, __ZL11cdx14_frame@PAGEOFF]
      ec:	00 01 40 f9	ldr	x0, [x8, __ZL11cdx14_frame@PAGEOFF]
      f0:	00 00 00 94	bl	__ZL16cdx14_sample_duey
      f4:	60 00 00 37	tbnz	w0, #0x0, 0x100
      f8:	01 00 00 14	b	0xfc
      fc:	87 00 00 14	b	0x318
     100:	e8 1f 40 b9	ldr	w8, [sp, #0x1c]
     104:	09 00 00 90	adrp	x9, 4 ; 0x0
     108:	29 01 00 91	add	x9, x9, #0x0
     10c:	28 11 00 b9	str	w8, [x9, #0x10]
     110:	e8 1b 40 b9	ldr	w8, [sp, #0x18]
     114:	28 15 00 b9	str	w8, [x9, #0x14]
     118:	08 00 80 52	mov	w8, #0x0
     11c:	28 01 00 b9	str	w8, [x9]
     120:	28 0d 00 b9	str	w8, [x9, #0xc]
     124:	28 09 00 b9	str	w8, [x9, #0x8]
     128:	28 05 00 b9	str	w8, [x9, #0x4]
     12c:	a0 03 5e f8	ldur	x0, [x29, #-0x20]
     130:	e1 17 40 f9	ldr	x1, [sp, #0x28]
     134:	e2 13 40 f9	ldr	x2, [sp, #0x20]
     138:	e3 1f 40 b9	ldr	w3, [sp, #0x1c]
     13c:	e4 1b 40 b9	ldr	w4, [sp, #0x18]
     140:	05 00 00 90	adrp	x5, __ZL12cdx14_source@PAGE
     144:	a5 00 00 91	add	x5, x5, __ZL12cdx14_source@PAGEOFF
     148:	00 00 00 94	bl	__ZL13cdx14_samplesPVKvyyjjP12Cdx14Samples
     14c:	80 01 00 34	cbz	w0, 0x17c
     150:	01 00 00 14	b	0x154
     154:	a0 83 5f f8	ldur	x0, [x29, #-0x8]
     158:	a1 03 5f f8	ldur	x1, [x29, #-0x10]
     15c:	a2 83 5e f8	ldur	x2, [x29, #-0x18]
     160:	e3 1f 40 b9	ldr	w3, [sp, #0x1c]
     164:	e4 1b 40 b9	ldr	w4, [sp, #0x18]
     168:	05 00 00 90	adrp	x5, __ZL12cdx14_before@PAGE
     16c:	a5 00 00 91	add	x5, x5, __ZL12cdx14_before@PAGEOFF
     170:	00 00 00 94	bl	__ZL13cdx14_samplesPVKvyyjjP12Cdx14Samples
     174:	c0 00 00 37	tbnz	w0, #0x0, 0x18c
     178:	01 00 00 14	b	0x17c
     17c:	09 00 00 90	adrp	x9, __ZL18cdx14_has_previous@PAGE
     180:	08 00 80 52	mov	w8, #0x0
     184:	28 01 00 39	strb	w8, [x9, __ZL18cdx14_has_previous@PAGEOFF]
     188:	64 00 00 14	b	0x318
     18c:	08 00 00 90	adrp	x8, __ZL18cdx14_has_previous@PAGE
     190:	08 01 40 39	ldrb	w8, [x8, __ZL18cdx14_has_previous@PAGEOFF]
     194:	09 00 80 52	mov	w9, #0x0
     198:	e9 13 00 b9	str	w9, [sp, #0x10]
     19c:	28 02 00 34	cbz	w8, 0x1e0
     1a0:	01 00 00 14	b	0x1a4
     1a4:	e9 1f 40 b9	ldr	w9, [sp, #0x1c]
     1a8:	08 00 00 90	adrp	x8, __ZL20cdx14_previous_width@PAGE
     1ac:	0a 01 40 b9	ldr	w10, [x8, __ZL20cdx14_previous_width@PAGEOFF]
     1b0:	08 00 80 52	mov	w8, #0x0
     1b4:	29 01 0a 6b	subs	w9, w9, w10
     1b8:	e8 13 00 b9	str	w8, [sp, #0x10]
     1bc:	21 01 00 54	b.ne	0x1e0
     1c0:	01 00 00 14	b	0x1c4
     1c4:	e8 1b 40 b9	ldr	w8, [sp, #0x18]
     1c8:	09 00 00 90	adrp	x9, __ZL21cdx14_previous_height@PAGE
     1cc:	29 01 40 b9	ldr	w9, [x9, __ZL21cdx14_previous_height@PAGEOFF]
     1d0:	08 01 09 6b	subs	w8, w8, w9
     1d4:	e8 17 9f 1a	cset	w8, eq
     1d8:	e8 13 00 b9	str	w8, [sp, #0x10]
     1dc:	01 00 00 14	b	0x1e0
     1e0:	e8 13 40 b9	ldr	w8, [sp, #0x10]
     1e4:	08 01 00 12	and	w8, w8, #0x1
     1e8:	e8 5f 00 39	strb	w8, [sp, #0x17]
     1ec:	e8 5f 40 39	ldrb	w8, [sp, #0x17]
     1f0:	48 01 00 34	cbz	w8, 0x218
     1f4:	01 00 00 14	b	0x1f8
     1f8:	00 00 00 90	adrp	x0, __ZL14cdx14_previous@PAGE
     1fc:	00 00 00 91	add	x0, x0, __ZL14cdx14_previous@PAGEOFF
     200:	01 00 00 90	adrp	x1, __ZL12cdx14_before@PAGE
     204:	21 00 00 91	add	x1, x1, __ZL12cdx14_before@PAGEOFF
     208:	00 00 00 94	bl	__ZL17cdx14_sample_diffRK12Cdx14SamplesS1_
     20c:	e8 03 00 aa	mov	x8, x0
     210:	e8 0f 00 b9	str	w8, [sp, #0xc]
     214:	04 00 00 14	b	0x224
     218:	08 00 80 52	mov	w8, #0x0
     21c:	e8 0f 00 b9	str	w8, [sp, #0xc]
     220:	01 00 00 14	b	0x224
     224:	e8 0f 40 b9	ldr	w8, [sp, #0xc]
     228:	09 00 00 90	adrp	x9, 4 ; 0x0
     22c:	28 01 00 b9	str	w8, [x9]
     230:	08 00 00 90	adrp	x8, __ZL18cdx14_has_previous@PAGE
     234:	08 01 40 39	ldrb	w8, [x8, __ZL18cdx14_has_previous@PAGEOFF]
     238:	c8 00 00 34	cbz	w8, 0x250
     23c:	01 00 00 14	b	0x240
     240:	08 00 00 90	adrp	x8, __ZL14cdx14_previous@PAGE
     244:	08 01 40 f9	ldr	x8, [x8, __ZL14cdx14_previous@PAGEOFF]
     248:	e8 03 00 f9	str	x8, [sp]
     24c:	04 00 00 14	b	0x25c
     250:	08 00 80 d2	mov	x8, #0x0
     254:	e8 03 00 f9	str	x8, [sp]
     258:	01 00 00 14	b	0x25c
     25c:	e9 03 40 f9	ldr	x9, [sp]
     260:	08 00 00 90	adrp	x8, __ZL11cdx14_frame@PAGE
     264:	08 01 00 91	add	x8, x8, __ZL11cdx14_frame@PAGEOFF
     268:	09 11 00 f9	str	x9, [x8, #0x20]
     26c:	08 01 40 f9	ldr	x8, [x8]
     270:	08 25 00 f1	subs	x8, x8, #0x9
     274:	c3 00 00 54	b.lo	0x28c
     278:	01 00 00 14	b	0x27c
     27c:	09 00 00 90	adrp	x9, 4 ; 0x0
     280:	08 00 80 52	mov	w8, #0x0
     284:	28 01 00 b9	str	w8, [x9]
     288:	01 00 00 14	b	0x28c
     28c:	08 00 00 90	adrp	x8, __ZL12cdx14_source@PAGE
     290:	08 01 00 91	add	x8, x8, __ZL12cdx14_source@PAGEOFF
     294:	0a 01 40 f9	ldr	x10, [x8]
     298:	09 00 00 90	adrp	x9, 4 ; 0x0
     29c:	29 01 00 91	add	x9, x9, #0x0
     2a0:	2a 01 00 f9	str	x10, [x9]
     2a4:	0a 00 00 90	adrp	x10, __ZL12cdx14_before@PAGE
     2a8:	4a 01 40 f9	ldr	x10, [x10, __ZL12cdx14_before@PAGEOFF]
     2ac:	2a 05 00 f9	str	x10, [x9, #0x8]
     2b0:	0a 09 40 b9	ldr	w10, [x8, #0x8]
     2b4:	2a 41 00 b9	str	w10, [x9, #0x40]
     2b8:	08 99 40 b9	ldr	w8, [x8, #0x98]
     2bc:	28 49 00 b9	str	w8, [x9, #0x48]
     2c0:	a8 83 5f f8	ldur	x8, [x29, #-0x8]
     2c4:	09 00 00 90	adrp	x9, __ZL17cdx14_destination@PAGE
     2c8:	28 01 00 f9	str	x8, [x9, __ZL17cdx14_destination@PAGEOFF]
     2cc:	a8 03 5e f8	ldur	x8, [x29, #-0x20]
     2d0:	09 00 00 90	adrp	x9, __ZL20cdx14_source_address@PAGE
     2d4:	28 01 00 f9	str	x8, [x9, __ZL20cdx14_source_address@PAGEOFF]
     2d8:	a8 03 5f f8	ldur	x8, [x29, #-0x10]
     2dc:	09 00 00 90	adrp	x9, __ZL15cdx14_dst_bytes@PAGE
     2e0:	28 01 00 f9	str	x8, [x9, __ZL15cdx14_dst_bytes@PAGEOFF]
     2e4:	e8 17 40 f9	ldr	x8, [sp, #0x28]
     2e8:	09 00 00 90	adrp	x9, __ZL15cdx14_src_bytes@PAGE
     2ec:	28 01 00 f9	str	x8, [x9, __ZL15cdx14_src_bytes@PAGEOFF]
     2f0:	a8 83 5e f8	ldur	x8, [x29, #-0x18]
     2f4:	09 00 00 90	adrp	x9, __ZL16cdx14_dst_stride@PAGE
     2f8:	28 01 00 f9	str	x8, [x9, __ZL16cdx14_dst_stride@PAGEOFF]
     2fc:	e8 13 40 f9	ldr	x8, [sp, #0x20]
     300:	09 00 00 90	adrp	x9, __ZL16cdx14_src_stride@PAGE
     304:	28 01 00 f9	str	x8, [x9, __ZL16cdx14_src_stride@PAGEOFF]
     308:	09 00 00 90	adrp	x9, __ZL14cdx14_inflight@PAGE
     30c:	28 00 80 52	mov	w8, #0x1
     310:	28 01 00 39	strb	w8, [x9, __ZL14cdx14_inflight@PAGEOFF]
     314:	01 00 00 14	b	0x318
     318:	fd 7b 45 a9	ldp	x29, x30, [sp, #0x50]
     31c:	ff 83 01 91	add	sp, sp, #0x60
     320:	c0 03 5f d6	ret
__ZL16cdx14_sample_duey:
     324:	ff 43 00 d1	sub	sp, sp, #0x10
     328:	e0 07 00 f9	str	x0, [sp, #0x8]
     32c:	e9 07 40 f9	ldr	x9, [sp, #0x8]
     330:	28 00 80 52	mov	w8, #0x1
     334:	29 25 00 f1	subs	x9, x9, #0x9
     338:	e8 07 00 b9	str	w8, [sp, #0x4]
     33c:	23 02 00 54	b.lo	0x380
     340:	01 00 00 14	b	0x344
     344:	e8 07 40 f9	ldr	x8, [sp, #0x8]
     348:	00 00 80 52	mov	w0, #0x0
     34c:	08 01 04 f1	subs	x8, x8, #0x100
     350:	e0 03 00 b9	str	w0, [sp]
     354:	08 01 00 54	b.hi	0x374
     358:	01 00 00 14	b	0x35c
     35c:	e8 07 40 f9	ldr	x8, [sp, #0x8]
     360:	09 05 00 f1	subs	x9, x8, #0x1
     364:	08 01 09 ea	ands	x8, x8, x9
     368:	e0 17 9f 1a	cset	w0, eq
     36c:	e0 03 00 b9	str	w0, [sp]
     370:	01 00 00 14	b	0x374
     374:	e8 03 40 b9	ldr	w8, [sp]
     378:	e8 07 00 b9	str	w8, [sp, #0x4]
     37c:	01 00 00 14	b	0x380
     380:	e8 07 40 b9	ldr	w8, [sp, #0x4]
     384:	00 01 00 12	and	w0, w8, #0x1
     388:	ff 43 00 91	add	sp, sp, #0x10
     38c:	c0 03 5f d6	ret
__ZL13cdx14_samplesPVKvyyjjP12Cdx14Samples:
     390:	ff 83 01 d1	sub	sp, sp, #0x60
     394:	e0 2b 00 f9	str	x0, [sp, #0x50]
     398:	e1 27 00 f9	str	x1, [sp, #0x48]
     39c:	e2 23 00 f9	str	x2, [sp, #0x40]
     3a0:	e3 3f 00 b9	str	w3, [sp, #0x3c]
     3a4:	e4 3b 00 b9	str	w4, [sp, #0x38]
     3a8:	e5 1b 00 f9	str	x5, [sp, #0x30]
     3ac:	e8 2b 40 f9	ldr	x8, [sp, #0x50]
     3b0:	68 05 00 b4	cbz	x8, 0x45c
     3b4:	01 00 00 14	b	0x3b8
     3b8:	e8 1b 40 f9	ldr	x8, [sp, #0x30]
     3bc:	08 05 00 b4	cbz	x8, 0x45c
     3c0:	01 00 00 14	b	0x3c4
     3c4:	e8 3f 40 b9	ldr	w8, [sp, #0x3c]
     3c8:	a8 04 00 34	cbz	w8, 0x45c
     3cc:	01 00 00 14	b	0x3d0
     3d0:	e8 3b 40 b9	ldr	w8, [sp, #0x38]
     3d4:	48 04 00 34	cbz	w8, 0x45c
     3d8:	01 00 00 14	b	0x3dc
     3dc:	e8 3f 40 b9	ldr	w8, [sp, #0x3c]
     3e0:	08 11 40 71	subs	w8, w8, #0x4, lsl #12
     3e4:	c8 03 00 54	b.hi	0x45c
     3e8:	01 00 00 14	b	0x3ec
     3ec:	e8 3b 40 b9	ldr	w8, [sp, #0x38]
     3f0:	08 11 40 71	subs	w8, w8, #0x4, lsl #12
     3f4:	48 03 00 54	b.hi	0x45c
     3f8:	01 00 00 14	b	0x3fc
     3fc:	e8 43 41 39	ldrb	w8, [sp, #0x50]
     400:	08 05 00 12	and	w8, w8, #0x3
     404:	c8 02 00 35	cbnz	w8, 0x45c
     408:	01 00 00 14	b	0x40c
     40c:	e8 03 41 39	ldrb	w8, [sp, #0x40]
     410:	08 05 00 12	and	w8, w8, #0x3
     414:	48 02 00 35	cbnz	w8, 0x45c
     418:	01 00 00 14	b	0x41c
     41c:	e8 23 40 f9	ldr	x8, [sp, #0x40]
     420:	e9 3f 40 b9	ldr	w9, [sp, #0x3c]
     424:	08 09 09 eb	subs	x8, x8, x9, lsl #2
     428:	a3 01 00 54	b.lo	0x45c
     42c:	01 00 00 14	b	0x430
     430:	e8 23 40 f9	ldr	x8, [sp, #0x40]
     434:	08 41 40 f1	subs	x8, x8, #0x10, lsl #12
     438:	28 01 00 54	b.hi	0x45c
     43c:	01 00 00 14	b	0x440
     440:	e8 23 40 f9	ldr	x8, [sp, #0x40]
     444:	e9 27 40 f9	ldr	x9, [sp, #0x48]
     448:	ea 3b 40 b9	ldr	w10, [sp, #0x38]
     44c:	29 09 ca 9a	udiv	x9, x9, x10
     450:	08 01 09 eb	subs	x8, x8, x9
     454:	a9 00 00 54	b.ls	0x468
     458:	01 00 00 14	b	0x45c
     45c:	08 00 80 52	mov	w8, #0x0
     460:	e8 7f 01 39	strb	w8, [sp, #0x5f]
     464:	55 00 00 14	b	0x5b8
     468:	e9 1b 40 f9	ldr	x9, [sp, #0x30]
     46c:	a8 64 84 d2	mov	x8, #0x2325
     470:	48 84 b0 f2	movk	x8, #0x8422, lsl #16
     474:	88 9c d3 f2	movk	x8, #0x9ce4, lsl #32
     478:	48 7e f9 f2	movk	x8, #0xcbf2, lsl #48
     47c:	28 01 00 f9	str	x8, [x9]
     480:	08 00 80 52	mov	w8, #0x0
     484:	e8 2f 00 b9	str	w8, [sp, #0x2c]
     488:	01 00 00 14	b	0x48c
     48c:	e8 2f 40 b9	ldr	w8, [sp, #0x2c]
     490:	08 fd 00 71	subs	w8, w8, #0x3f
     494:	c8 08 00 54	b.hi	0x5ac
     498:	01 00 00 14	b	0x49c
     49c:	e8 2f 40 b9	ldr	w8, [sp, #0x2c]
     4a0:	08 09 00 12	and	w8, w8, #0x7
     4a4:	e9 3f 40 b9	ldr	w9, [sp, #0x3c]
     4a8:	29 05 00 71	subs	w9, w9, #0x1
     4ac:	08 7d a9 9b	umull	x8, w8, w9
     4b0:	69 92 84 d2	mov	x9, #0x2493
     4b4:	29 49 b2 f2	movk	x9, #0x9249, lsl #16
     4b8:	89 24 c9 f2	movk	x9, #0x4924, lsl #32
     4bc:	49 92 e4 f2	movk	x9, #0x2492, lsl #48
     4c0:	08 7d c9 9b	umulh	x8, x8, x9
     4c4:	e8 13 00 f9	str	x8, [sp, #0x20]
     4c8:	e8 2f 40 b9	ldr	w8, [sp, #0x2c]
     4cc:	08 7d 03 53	lsr	w8, w8, #3
     4d0:	ea 3b 40 b9	ldr	w10, [sp, #0x38]
     4d4:	4a 05 00 71	subs	w10, w10, #0x1
     4d8:	08 7d aa 9b	umull	x8, w8, w10
     4dc:	08 7d c9 9b	umulh	x8, x8, x9
     4e0:	e8 0f 00 f9	str	x8, [sp, #0x18]
     4e4:	e8 2b 40 f9	ldr	x8, [sp, #0x50]
     4e8:	e9 0f 40 f9	ldr	x9, [sp, #0x18]
     4ec:	ea 23 40 f9	ldr	x10, [sp, #0x40]
     4f0:	29 7d 0a 9b	mul	x9, x9, x10
     4f4:	08 01 09 8b	add	x8, x8, x9
     4f8:	e9 13 40 f9	ldr	x9, [sp, #0x20]
     4fc:	08 09 09 8b	add	x8, x8, x9, lsl #2
     500:	e8 0b 00 f9	str	x8, [sp, #0x10]
     504:	e8 0b 40 f9	ldr	x8, [sp, #0x10]
     508:	08 01 40 b9	ldr	w8, [x8]
     50c:	e8 0f 00 b9	str	w8, [sp, #0xc]
     510:	e8 0f 40 b9	ldr	w8, [sp, #0xc]
     514:	e9 1b 40 f9	ldr	x9, [sp, #0x30]
     518:	ea 2f 40 b9	ldr	w10, [sp, #0x2c]
     51c:	29 09 0a 8b	add	x9, x9, x10, lsl #2
     520:	28 09 00 b9	str	w8, [x9, #0x8]
     524:	08 00 80 52	mov	w8, #0x0
     528:	e8 0b 00 b9	str	w8, [sp, #0x8]
     52c:	01 00 00 14	b	0x530
     530:	e8 0b 40 b9	ldr	w8, [sp, #0x8]
     534:	08 0d 00 71	subs	w8, w8, #0x3
     538:	08 03 00 54	b.hi	0x598
     53c:	01 00 00 14	b	0x540
     540:	e8 0f 40 b9	ldr	w8, [sp, #0xc]
     544:	e9 0b 40 b9	ldr	w9, [sp, #0x8]
     548:	29 71 1d 53	lsl	w9, w9, #3
     54c:	08 25 c9 1a	lsr	w8, w8, w9
     550:	08 1d 00 12	and	w8, w8, #0xff
     554:	e8 03 08 2a	mov	w8, w8
     558:	ea 03 08 aa	mov	x10, x8
     55c:	e9 1b 40 f9	ldr	x9, [sp, #0x30]
     560:	28 01 40 f9	ldr	x8, [x9]
     564:	08 01 0a ca	eor	x8, x8, x10
     568:	28 01 00 f9	str	x8, [x9]
     56c:	e9 1b 40 f9	ldr	x9, [sp, #0x30]
     570:	28 01 40 f9	ldr	x8, [x9]
     574:	6a 36 80 d2	mov	x10, #0x1b3
     578:	0a 20 c0 f2	movk	x10, #0x100, lsl #32
     57c:	08 7d 0a 9b	mul	x8, x8, x10
     580:	28 01 00 f9	str	x8, [x9]
     584:	01 00 00 14	b	0x588
     588:	e8 0b 40 b9	ldr	w8, [sp, #0x8]
     58c:	08 05 00 11	add	w8, w8, #0x1
     590:	e8 0b 00 b9	str	w8, [sp, #0x8]
     594:	e7 ff ff 17	b	0x530
     598:	01 00 00 14	b	0x59c
     59c:	e8 2f 40 b9	ldr	w8, [sp, #0x2c]
     5a0:	08 05 00 11	add	w8, w8, #0x1
     5a4:	e8 2f 00 b9	str	w8, [sp, #0x2c]
     5a8:	b9 ff ff 17	b	0x48c
     5ac:	28 00 80 52	mov	w8, #0x1
     5b0:	e8 7f 01 39	strb	w8, [sp, #0x5f]
     5b4:	01 00 00 14	b	0x5b8
     5b8:	e0 7f 41 39	ldrb	w0, [sp, #0x5f]
     5bc:	ff 83 01 91	add	sp, sp, #0x60
     5c0:	c0 03 5f d6	ret
__ZL17cdx14_sample_diffRK12Cdx14SamplesS1_:
     5c4:	ff 83 00 d1	sub	sp, sp, #0x20
     5c8:	e0 0f 00 f9	str	x0, [sp, #0x18]
     5cc:	e1 0b 00 f9	str	x1, [sp, #0x10]
     5d0:	08 00 80 52	mov	w8, #0x0
     5d4:	e8 0f 00 b9	str	w8, [sp, #0xc]
     5d8:	e8 0b 00 b9	str	w8, [sp, #0x8]
     5dc:	01 00 00 14	b	0x5e0
     5e0:	e8 0b 40 b9	ldr	w8, [sp, #0x8]
     5e4:	08 fd 00 71	subs	w8, w8, #0x3f
     5e8:	68 02 00 54	b.hi	0x634
     5ec:	01 00 00 14	b	0x5f0
     5f0:	e8 0f 40 f9	ldr	x8, [sp, #0x18]
     5f4:	e9 0b 40 b9	ldr	w9, [sp, #0x8]
     5f8:	2a f5 7e d3	lsl	x10, x9, #2
     5fc:	08 01 0a 8b	add	x8, x8, x10
     600:	08 09 40 b9	ldr	w8, [x8, #0x8]
     604:	e9 0b 40 f9	ldr	x9, [sp, #0x10]
     608:	29 01 0a 8b	add	x9, x9, x10
     60c:	29 09 40 b9	ldr	w9, [x9, #0x8]
     610:	08 01 09 6b	subs	w8, w8, w9
     614:	e8 0f 40 b9	ldr	w8, [sp, #0xc]
     618:	08 05 88 1a	cinc	w8, w8, ne
     61c:	e8 0f 00 b9	str	w8, [sp, #0xc]
     620:	01 00 00 14	b	0x624
     624:	e8 0b 40 b9	ldr	w8, [sp, #0x8]
     628:	08 05 00 11	add	w8, w8, #0x1
     62c:	e8 0b 00 b9	str	w8, [sp, #0x8]
     630:	ec ff ff 17	b	0x5e0
     634:	e0 0f 40 b9	ldr	w0, [sp, #0xc]
     638:	ff 83 00 91	add	sp, sp, #0x20
     63c:	c0 03 5f d6	ret
_cdx14_frame_end:
     640:	fc 6f be a9	stp	x28, x27, [sp, #-0x20]!
     644:	fd 7b 01 a9	stp	x29, x30, [sp, #0x10]
     648:	fd 43 00 91	add	x29, sp, #0x10
     64c:	ff c3 09 d1	sub	sp, sp, #0x270
     650:	a0 f3 1e 38	sturb	w0, [x29, #-0x11]
     654:	08 00 00 90	adrp	x8, __ZL14cdx14_inflight@PAGE
     658:	08 01 40 39	ldrb	w8, [x8, __ZL14cdx14_inflight@PAGEOFF]
     65c:	68 00 00 35	cbnz	w8, 0x668
     660:	01 00 00 14	b	0x664
     664:	7d 00 00 14	b	0x858
     668:	09 00 00 90	adrp	x9, __ZL14cdx14_inflight@PAGE
     66c:	08 00 80 52	mov	w8, #0x0
     670:	28 01 00 39	strb	w8, [x9, __ZL14cdx14_inflight@PAGEOFF]
     674:	08 21 80 52	mov	w8, #0x108
     678:	e1 03 08 aa	mov	x1, x8
     67c:	e1 2b 00 f9	str	x1, [sp, #0x50]
     680:	e0 83 05 91	add	x0, sp, #0x160
     684:	00 00 00 94	bl	_bzero
     688:	e1 2b 40 f9	ldr	x1, [sp, #0x50]
     68c:	e0 63 01 91	add	x0, sp, #0x58
     690:	00 00 00 94	bl	_bzero
     694:	a8 f3 5e 38	ldurb	w8, [x29, #-0x11]
     698:	c8 03 00 34	cbz	w8, 0x710
     69c:	01 00 00 14	b	0x6a0
     6a0:	08 00 00 90	adrp	x8, __ZL17cdx14_destination@PAGE
     6a4:	00 01 40 f9	ldr	x0, [x8, __ZL17cdx14_destination@PAGEOFF]
     6a8:	08 00 00 90	adrp	x8, __ZL15cdx14_dst_bytes@PAGE
     6ac:	01 01 40 f9	ldr	x1, [x8, __ZL15cdx14_dst_bytes@PAGEOFF]
     6b0:	08 00 00 90	adrp	x8, __ZL16cdx14_dst_stride@PAGE
     6b4:	02 01 40 f9	ldr	x2, [x8, __ZL16cdx14_dst_stride@PAGEOFF]
     6b8:	08 00 00 90	adrp	x8, 4 ; 0x0
     6bc:	08 01 00 91	add	x8, x8, #0x0
     6c0:	03 01 40 b9	ldr	w3, [x8]
     6c4:	04 05 40 b9	ldr	w4, [x8, #0x4]
     6c8:	e5 83 05 91	add	x5, sp, #0x160
     6cc:	00 00 00 94	bl	__ZL13cdx14_samplesPVKvyyjjP12Cdx14Samples
     6d0:	00 02 00 34	cbz	w0, 0x710
     6d4:	01 00 00 14	b	0x6d8
     6d8:	08 00 00 90	adrp	x8, __ZL20cdx14_source_address@PAGE
     6dc:	00 01 40 f9	ldr	x0, [x8, __ZL20cdx14_source_address@PAGEOFF]
     6e0:	08 00 00 90	adrp	x8, __ZL15cdx14_src_bytes@PAGE
     6e4:	01 01 40 f9	ldr	x1, [x8, __ZL15cdx14_src_bytes@PAGEOFF]
     6e8:	08 00 00 90	adrp	x8, __ZL16cdx14_src_stride@PAGE
     6ec:	02 01 40 f9	ldr	x2, [x8, __ZL16cdx14_src_stride@PAGEOFF]
     6f0:	08 00 00 90	adrp	x8, 4 ; 0x0
     6f4:	08 01 00 91	add	x8, x8, #0x0
     6f8:	03 01 40 b9	ldr	w3, [x8]
     6fc:	04 05 40 b9	ldr	w4, [x8, #0x4]
     700:	e5 63 01 91	add	x5, sp, #0x58
     704:	00 00 00 94	bl	__ZL13cdx14_samplesPVKvyyjjP12Cdx14Samples
     708:	e0 00 00 37	tbnz	w0, #0x0, 0x724
     70c:	01 00 00 14	b	0x710
     710:	09 00 00 90	adrp	x9, __ZL18cdx14_has_previous@PAGE
     714:	08 00 80 52	mov	w8, #0x0
     718:	28 01 00 39	strb	w8, [x9, __ZL18cdx14_has_previous@PAGEOFF]
     71c:	00 00 00 94	bl	__ZL13cdx14_publishv
     720:	4e 00 00 14	b	0x858
     724:	09 00 00 90	adrp	x9, __ZL11cdx14_frame@PAGE
     728:	29 01 00 91	add	x9, x9, __ZL11cdx14_frame@PAGEOFF
     72c:	e9 27 00 f9	str	x9, [sp, #0x48]
     730:	28 00 80 52	mov	w8, #0x1
     734:	e8 47 00 b9	str	w8, [sp, #0x44]
     738:	28 31 00 b9	str	w8, [x9, #0x30]
     73c:	28 29 40 b9	ldr	w8, [x9, #0x28]
     740:	08 05 00 11	add	w8, w8, #0x1
     744:	28 29 00 b9	str	w8, [x9, #0x28]
     748:	00 00 00 90	adrp	x0, __ZL12cdx14_source@PAGE
     74c:	00 00 00 91	add	x0, x0, __ZL12cdx14_source@PAGEOFF
     750:	e0 1b 00 f9	str	x0, [sp, #0x30]
     754:	e1 63 01 91	add	x1, sp, #0x58
     758:	00 00 00 94	bl	__ZL17cdx14_sample_diffRK12Cdx14SamplesS1_
     75c:	e9 27 40 f9	ldr	x9, [sp, #0x48]
     760:	e8 03 00 aa	mov	x8, x0
     764:	e0 1b 40 f9	ldr	x0, [sp, #0x30]
     768:	28 35 00 b9	str	w8, [x9, #0x34]
     76c:	e1 83 05 91	add	x1, sp, #0x160
     770:	e1 1f 00 f9	str	x1, [sp, #0x38]
     774:	00 00 00 94	bl	__ZL17cdx14_sample_diffRK12Cdx14SamplesS1_
     778:	e1 1f 40 f9	ldr	x1, [sp, #0x38]
     77c:	e9 27 40 f9	ldr	x9, [sp, #0x48]
     780:	20 39 00 b9	str	w0, [x9, #0x38]
     784:	e8 b3 40 f9	ldr	x8, [sp, #0x160]
     788:	28 0d 00 f9	str	x8, [x9, #0x18]
     78c:	e8 6b 41 b9	ldr	w8, [sp, #0x168]
     790:	28 4d 00 b9	str	w8, [x9, #0x4c]
     794:	e8 fb 41 b9	ldr	w8, [sp, #0x1f8]
     798:	28 55 00 b9	str	w8, [x9, #0x54]
     79c:	00 00 00 90	adrp	x0, __ZL14cdx14_previous@PAGE
     7a0:	00 00 00 91	add	x0, x0, __ZL14cdx14_previous@PAGEOFF
     7a4:	08 21 80 52	mov	w8, #0x108
     7a8:	e2 03 08 aa	mov	x2, x8
     7ac:	00 00 00 94	bl	_memcpy
     7b0:	e9 47 40 b9	ldr	w9, [sp, #0x44]
     7b4:	e8 27 40 f9	ldr	x8, [sp, #0x48]
     7b8:	0a 00 00 90	adrp	x10, __ZL18cdx14_has_previous@PAGE
     7bc:	49 01 00 39	strb	w9, [x10, __ZL18cdx14_has_previous@PAGEOFF]
     7c0:	09 41 40 b9	ldr	w9, [x8, #0x40]
     7c4:	0a 00 00 90	adrp	x10, __ZL20cdx14_previous_width@PAGE
     7c8:	49 01 00 b9	str	w9, [x10, __ZL20cdx14_previous_width@PAGEOFF]
     7cc:	08 45 40 b9	ldr	w8, [x8, #0x44]
     7d0:	09 00 00 90	adrp	x9, __ZL21cdx14_previous_height@PAGE
     7d4:	28 01 00 b9	str	w8, [x9, __ZL21cdx14_previous_height@PAGEOFF]
     7d8:	00 00 00 94	bl	__ZL13cdx14_publishv
     7dc:	e9 27 40 f9	ldr	x9, [sp, #0x48]
     7e0:	28 01 40 f9	ldr	x8, [x9]
     7e4:	2a 05 40 f9	ldr	x10, [x9, #0x8]
     7e8:	2b 0d 40 f9	ldr	x11, [x9, #0x18]
     7ec:	e9 03 00 91	mov	x9, sp
     7f0:	2b 09 00 f9	str	x11, [x9, #0x10]
     7f4:	2a 05 00 f9	str	x10, [x9, #0x8]
     7f8:	28 01 00 f9	str	x8, [x9]
     7fc:	00 00 00 90	adrp	x0, l_.str.2@PAGE
     800:	00 00 00 91	add	x0, x0, l_.str.2@PAGEOFF
     804:	00 00 00 94	bl	__Z5IOLogPKcz
     808:	e9 27 40 f9	ldr	x9, [sp, #0x48]
     80c:	28 39 40 b9	ldr	w8, [x9, #0x38]
     810:	08 01 00 71	subs	w8, w8, #0x0
     814:	e8 17 9f 1a	cset	w8, eq
     818:	2a 35 40 b9	ldr	w10, [x9, #0x34]
     81c:	2b 3d 40 b9	ldr	w11, [x9, #0x3c]
     820:	2c 59 40 b9	ldr	w12, [x9, #0x58]
     824:	29 65 40 b9	ldr	w9, [x9, #0x64]
     828:	ed 03 09 aa	mov	x13, x9
     82c:	e9 03 00 91	mov	x9, sp
     830:	2d 11 00 f9	str	x13, [x9, #0x20]
     834:	2c 0d 00 f9	str	x12, [x9, #0x18]
     838:	2b 09 00 f9	str	x11, [x9, #0x10]
     83c:	2a 05 00 f9	str	x10, [x9, #0x8]
     840:	e8 03 08 2a	mov	w8, w8
     844:	28 01 00 f9	str	x8, [x9]
     848:	00 00 00 90	adrp	x0, l_.str.3@PAGE
     84c:	00 00 00 91	add	x0, x0, l_.str.3@PAGEOFF
     850:	00 00 00 94	bl	__Z5IOLogPKcz
     854:	01 00 00 14	b	0x858
     858:	ff c3 09 91	add	sp, sp, #0x270
     85c:	fd 7b 41 a9	ldp	x29, x30, [sp, #0x10]
     860:	fc 6f c2 a8	ldp	x28, x27, [sp], #0x20
     864:	c0 03 5f d6	ret
__ZL13cdx14_publishv:
     868:	ff 83 00 d1	sub	sp, sp, #0x20
     86c:	fd 7b 01 a9	stp	x29, x30, [sp, #0x10]
     870:	fd 43 00 91	add	x29, sp, #0x10
     874:	00 00 00 90	adrp	x0, 4 ; 0x0
     878:	00 00 00 91	add	x0, x0, #0x0
     87c:	00 00 00 94	bl	_cdx14_console_snapshot
     880:	08 00 00 90	adrp	x8, _activeLegacyDisplay@GOTPAGE
     884:	08 01 40 f9	ldr	x8, [x8, _activeLegacyDisplay@GOTPAGEOFF]
     888:	08 01 40 f9	ldr	x8, [x8]
     88c:	a8 02 00 b4	cbz	x8, 0x8e0
     890:	01 00 00 14	b	0x894
     894:	00 00 00 90	adrp	x0, __ZL11cdx14_frame@PAGE
     898:	00 00 00 91	add	x0, x0, __ZL11cdx14_frame@PAGEOFF
     89c:	01 0e 80 52	mov	w1, #0x70
     8a0:	00 00 00 94	bl	__ZN6OSData9withBytesEPKvj
     8a4:	e0 07 00 f9	str	x0, [sp, #0x8]
     8a8:	e8 07 40 f9	ldr	x8, [sp, #0x8]
     8ac:	88 01 00 b4	cbz	x8, 0x8dc
     8b0:	01 00 00 14	b	0x8b4
     8b4:	08 00 00 90	adrp	x8, _activeLegacyDisplay@GOTPAGE
     8b8:	08 01 40 f9	ldr	x8, [x8, _activeLegacyDisplay@GOTPAGEOFF]
     8bc:	00 01 40 f9	ldr	x0, [x8]
     8c0:	e2 07 40 f9	ldr	x2, [sp, #0x8]
     8c4:	01 00 00 90	adrp	x1, l_.str.6@PAGE
     8c8:	21 00 00 91	add	x1, x1, l_.str.6@PAGEOFF
     8cc:	00 00 00 94	bl	__ZN7Service11setPropertyEPKcP6OSData
     8d0:	e0 07 40 f9	ldr	x0, [sp, #0x8]
     8d4:	00 00 00 94	bl	__ZN6OSData7releaseEv
     8d8:	01 00 00 14	b	0x8dc
     8dc:	01 00 00 14	b	0x8e0
     8e0:	fd 7b 41 a9	ldp	x29, x30, [sp, #0x10]
     8e4:	ff 83 00 91	add	sp, sp, #0x20
     8e8:	c0 03 5f d6	ret
_cdx14_after_release:
     8ec:	ff 83 00 d1	sub	sp, sp, #0x20
     8f0:	fd 7b 01 a9	stp	x29, x30, [sp, #0x10]
     8f4:	fd 43 00 91	add	x29, sp, #0x10
     8f8:	00 00 00 90	adrp	x0, l_.str.4@PAGE
     8fc:	00 00 00 91	add	x0, x0, l_.str.4@PAGEOFF
     900:	00 00 00 94	bl	__Z6optionPKc
     904:	08 04 00 71	subs	w8, w0, #0x1
     908:	81 00 00 54	b.ne	0x918
     90c:	01 00 00 14	b	0x910
     910:	00 00 00 94	bl	_cdx14_console_commit
     914:	01 00 00 14	b	0x918
     918:	00 00 00 90	adrp	x0, l_.str.5@PAGE
     91c:	00 00 00 91	add	x0, x0, l_.str.5@PAGEOFF
     920:	00 00 00 94	bl	__Z6optionPKc
     924:	08 04 00 71	subs	w8, w0, #0x1
     928:	41 03 00 54	b.ne	0x990
     92c:	01 00 00 14	b	0x930
     930:	08 00 00 90	adrp	x8, __ZL19cdx14_snapshot_call@PAGE
     934:	08 01 40 f9	ldr	x8, [x8, __ZL19cdx14_snapshot_call@PAGEOFF]
     938:	c8 02 00 b5	cbnz	x8, 0x990
     93c:	01 00 00 14	b	0x940
     940:	00 00 00 90	adrp	x0, __ZL23cdx14_snapshot_callbackPvS_@PAGE
     944:	00 00 00 91	add	x0, x0, __ZL23cdx14_snapshot_callbackPvS_@PAGEOFF
     948:	01 00 80 d2	mov	x1, #0x0
     94c:	00 00 00 94	bl	__Z20thread_call_allocatePFvPvS_ES_
     950:	08 00 00 90	adrp	x8, __ZL19cdx14_snapshot_call@PAGE
     954:	00 01 00 f9	str	x0, [x8, __ZL19cdx14_snapshot_call@PAGEOFF]
     958:	08 01 40 f9	ldr	x8, [x8, __ZL19cdx14_snapshot_call@PAGEOFF]
     95c:	88 01 00 b4	cbz	x8, 0x98c
     960:	01 00 00 14	b	0x964
     964:	e0 01 80 52	mov	w0, #0xf
     968:	01 40 99 52	mov	w1, #0xca00
     96c:	41 73 a7 72	movk	w1, #0x3b9a, lsl #16
     970:	e2 23 00 91	add	x2, sp, #0x8
     974:	00 00 00 94	bl	__Z26clock_interval_to_deadlinejjPy
     978:	08 00 00 90	adrp	x8, __ZL19cdx14_snapshot_call@PAGE
     97c:	00 01 40 f9	ldr	x0, [x8, __ZL19cdx14_snapshot_call@PAGEOFF]
     980:	e1 07 40 f9	ldr	x1, [sp, #0x8]
     984:	00 00 00 94	bl	__Z25thread_call_enter_delayedP11thread_cally
     988:	01 00 00 14	b	0x98c
     98c:	01 00 00 14	b	0x990
     990:	fd 7b 41 a9	ldp	x29, x30, [sp, #0x10]
     994:	ff 83 00 91	add	sp, sp, #0x20
     998:	c0 03 5f d6	ret
__ZL23cdx14_snapshot_callbackPvS_:
     99c:	fc 6f ba a9	stp	x28, x27, [sp, #-0x60]!
     9a0:	fa 67 01 a9	stp	x26, x25, [sp, #0x10]
     9a4:	f8 5f 02 a9	stp	x24, x23, [sp, #0x20]
     9a8:	f6 57 03 a9	stp	x22, x21, [sp, #0x30]
     9ac:	f4 4f 04 a9	stp	x20, x19, [sp, #0x40]
     9b0:	fd 7b 05 a9	stp	x29, x30, [sp, #0x50]
     9b4:	fd 43 01 91	add	x29, sp, #0x50
     9b8:	ff 03 14 d1	sub	sp, sp, #0x500
     9bc:	08 00 00 90	adrp	x8, ___stack_chk_guard@GOTPAGE
     9c0:	08 01 40 f9	ldr	x8, [x8, ___stack_chk_guard@GOTPAGEOFF]
     9c4:	08 01 40 f9	ldr	x8, [x8]
     9c8:	a8 03 1a f8	stur	x8, [x29, #-0x60]
     9cc:	e0 77 00 f9	str	x0, [sp, #0xe8]
     9d0:	e1 73 00 f9	str	x1, [sp, #0xe0]
     9d4:	08 40 80 52	mov	w8, #0x200
     9d8:	e1 03 08 aa	mov	x1, x8
     9dc:	e1 6f 00 f9	str	x1, [sp, #0xd8]
     9e0:	fb c3 0b 91	add	x27, sp, #0x2f0
     9e4:	e0 03 1b aa	mov	x0, x27
     9e8:	00 00 00 94	bl	_bzero
     9ec:	e1 6f 40 f9	ldr	x1, [sp, #0xd8]
     9f0:	fc c3 03 91	add	x28, sp, #0xf0
     9f4:	e0 03 1c aa	mov	x0, x28
     9f8:	00 00 00 94	bl	_bzero
     9fc:	e1 6f 40 f9	ldr	x1, [sp, #0xd8]
     a00:	e0 03 1b aa	mov	x0, x27
     a04:	00 00 00 94	bl	_cdx14_daemon_summary
     a08:	e1 6f 40 f9	ldr	x1, [sp, #0xd8]
     a0c:	e0 03 1c aa	mov	x0, x28
     a10:	00 00 00 94	bl	_cdx14_exception_summary
     a14:	13 00 00 90	adrp	x19, __ZL11cdx14_frame@PAGE
     a18:	73 02 00 91	add	x19, x19, __ZL11cdx14_frame@PAGEOFF
     a1c:	60 62 01 91	add	x0, x19, #0x58
     a20:	00 00 00 94	bl	_cdx14_console_snapshot
     a24:	68 02 40 f9	ldr	x8, [x19]
     a28:	6d 06 40 f9	ldr	x13, [x19, #0x8]
     a2c:	6e 0e 40 f9	ldr	x14, [x19, #0x18]
     a30:	14 00 00 90	adrp	x20, _native_legacy_swap_validation_calls@GOTPAGE
     a34:	94 02 40 f9	ldr	x20, [x20, _native_legacy_swap_validation_calls@GOTPAGEOFF]
     a38:	15 00 00 90	adrp	x21, _native_legacy_swap_validation_result@GOTPAGE
     a3c:	b5 02 40 f9	ldr	x21, [x21, _native_legacy_swap_validation_result@GOTPAGEOFF]
     a40:	16 00 00 90	adrp	x22, _native_legacy_transfer_calls@GOTPAGE
     a44:	d6 02 40 f9	ldr	x22, [x22, _native_legacy_transfer_calls@GOTPAGEOFF]
     a48:	17 00 00 90	adrp	x23, _native_legacy_transfer_status@GOTPAGE
     a4c:	f7 02 40 f9	ldr	x23, [x23, _native_legacy_transfer_status@GOTPAGEOFF]
     a50:	09 00 00 90	adrp	x9, _native_legacy_transfer_bytes@GOTPAGE
     a54:	29 01 40 f9	ldr	x9, [x9, _native_legacy_transfer_bytes@GOTPAGEOFF]
     a58:	6a 2a 40 b9	ldr	w10, [x19, #0x28]
     a5c:	6b 2e 40 b9	ldr	w11, [x19, #0x2c]
     a60:	6c 32 40 b9	ldr	w12, [x19, #0x30]
     a64:	6f 3a 40 b9	ldr	w15, [x19, #0x38]
     a68:	70 36 40 b9	ldr	w16, [x19, #0x34]
     a6c:	71 3e 40 b9	ldr	w17, [x19, #0x3c]
     a70:	60 4a 40 b9	ldr	w0, [x19, #0x48]
     a74:	61 4e 40 b9	ldr	w1, [x19, #0x4c]
     a78:	62 52 40 b9	ldr	w2, [x19, #0x50]
     a7c:	63 56 40 b9	ldr	w3, [x19, #0x54]
     a80:	64 5a 40 b9	ldr	w4, [x19, #0x58]
     a84:	65 5e 40 b9	ldr	w5, [x19, #0x5c]
     a88:	66 62 40 b9	ldr	w6, [x19, #0x60]
     a8c:	67 66 40 b9	ldr	w7, [x19, #0x64]
     a90:	73 6a 40 b9	ldr	w19, [x19, #0x68]
     a94:	94 02 40 b9	ldr	w20, [x20]
     a98:	b5 02 40 b9	ldr	w21, [x21]
     a9c:	d6 02 40 b9	ldr	w22, [x22]
     aa0:	f7 02 40 b9	ldr	w23, [x23]
     aa4:	38 01 40 f9	ldr	x24, [x9]
     aa8:	19 00 00 90	adrp	x25, _native_legacy_retirement_calls@GOTPAGE
     aac:	39 03 40 f9	ldr	x25, [x25, _native_legacy_retirement_calls@GOTPAGEOFF]
     ab0:	09 00 00 90	adrp	x9, _native_legacy_vsync_count@GOTPAGE
     ab4:	29 01 40 f9	ldr	x9, [x9, _native_legacy_vsync_count@GOTPAGEOFF]
     ab8:	39 03 40 b9	ldr	w25, [x25]
     abc:	29 01 40 b9	ldr	w9, [x9]
     ac0:	fa 03 09 aa	mov	x26, x9
     ac4:	e9 03 00 91	mov	x9, sp
     ac8:	3c 69 00 f9	str	x28, [x9, #0xd0]
     acc:	3b 65 00 f9	str	x27, [x9, #0xc8]
     ad0:	3a 61 00 f9	str	x26, [x9, #0xc0]
     ad4:	39 5d 00 f9	str	x25, [x9, #0xb8]
     ad8:	38 59 00 f9	str	x24, [x9, #0xb0]
     adc:	37 55 00 f9	str	x23, [x9, #0xa8]
     ae0:	36 51 00 f9	str	x22, [x9, #0xa0]
     ae4:	35 4d 00 f9	str	x21, [x9, #0x98]
     ae8:	34 49 00 f9	str	x20, [x9, #0x90]
     aec:	33 45 00 f9	str	x19, [x9, #0x88]
     af0:	27 41 00 f9	str	x7, [x9, #0x80]
     af4:	26 3d 00 f9	str	x6, [x9, #0x78]
     af8:	25 39 00 f9	str	x5, [x9, #0x70]
     afc:	24 35 00 f9	str	x4, [x9, #0x68]
     b00:	23 31 00 f9	str	x3, [x9, #0x60]
     b04:	22 2d 00 f9	str	x2, [x9, #0x58]
     b08:	21 29 00 f9	str	x1, [x9, #0x50]
     b0c:	20 25 00 f9	str	x0, [x9, #0x48]
     b10:	31 21 00 f9	str	x17, [x9, #0x40]
     b14:	30 1d 00 f9	str	x16, [x9, #0x38]
     b18:	2f 19 00 f9	str	x15, [x9, #0x30]
     b1c:	2e 15 00 f9	str	x14, [x9, #0x28]
     b20:	2d 11 00 f9	str	x13, [x9, #0x20]
     b24:	2c 0d 00 f9	str	x12, [x9, #0x18]
     b28:	2b 09 00 f9	str	x11, [x9, #0x10]
     b2c:	2a 05 00 f9	str	x10, [x9, #0x8]
     b30:	28 01 00 f9	str	x8, [x9]
     b34:	00 00 00 90	adrp	x0, l_.str.7@PAGE
     b38:	00 00 00 91	add	x0, x0, l_.str.7@PAGEOFF
     b3c:	00 00 00 94	bl	__Z5panicPKcz
