D:\Codex\tmp\stage14-host\core-policy-arm64.o:
(__TEXT,__text) section
_cdx14_console_commit:
       0:	ff 83 00 d1	sub	sp, sp, #0x20
       4:	fd 7b 01 a9	stp	x29, x30, [sp, #0x10]
       8:	fd 43 00 91	add	x29, sp, #0x10
       c:	09 00 00 90	adrp	x9, _mock_locked@PAGE
      10:	28 01 40 b9	ldr	w8, [x9, _mock_locked@PAGEOFF]
      14:	08 05 00 11	add	w8, w8, #0x1
      18:	28 01 00 b9	str	w8, [x9, _mock_locked@PAGEOFF]
      1c:	28 00 80 52	mov	w8, #0x1
      20:	a8 c3 1f b8	stur	w8, [x29, #-0x4]
      24:	a8 c3 5f b8	ldur	w8, [x29, #-0x4]
      28:	09 00 00 90	adrp	x9, _cdx14_vt_owned@PAGE
      2c:	29 01 00 91	add	x9, x9, _cdx14_vt_owned@PAGEOFF
      30:	28 fd 9f 88	stlr	w8, [x9]
      34:	09 00 00 90	adrp	x9, _gc_enabled@PAGE
      38:	08 00 80 52	mov	w8, #0x0
      3c:	28 01 00 b9	str	w8, [x9, _gc_enabled@PAGEOFF]
      40:	00 00 00 94	bl	_console_is_serial
      44:	c0 00 00 35	cbnz	w0, 0x5c
      48:	01 00 00 14	b	0x4c
      4c:	09 00 00 90	adrp	x9, _disableConsoleOutput@PAGE
      50:	28 00 80 52	mov	w8, #0x1
      54:	28 01 00 b9	str	w8, [x9, _disableConsoleOutput@PAGEOFF]
      58:	01 00 00 14	b	0x5c
      5c:	09 00 00 90	adrp	x9, _mock_locked@PAGE
      60:	28 01 40 b9	ldr	w8, [x9, _mock_locked@PAGEOFF]
      64:	08 05 00 71	subs	w8, w8, #0x1
      68:	28 01 00 b9	str	w8, [x9, _mock_locked@PAGEOFF]
      6c:	fd 7b 41 a9	ldp	x29, x30, [sp, #0x10]
      70:	ff 83 00 91	add	sp, sp, #0x20
      74:	c0 03 5f d6	ret
_console_is_serial:
      78:	08 00 00 90	adrp	x8, _mock_serial@PAGE
      7c:	00 01 40 b9	ldr	w0, [x8, _mock_serial@PAGEOFF]
      80:	c0 03 5f d6	ret
_cdx14_console_snapshot:
      84:	ff 83 00 d1	sub	sp, sp, #0x20
      88:	e0 0f 00 f9	str	x0, [sp, #0x18]
      8c:	e8 0f 40 f9	ldr	x8, [sp, #0x18]
      90:	68 00 00 b5	cbnz	x8, 0x9c
      94:	01 00 00 14	b	0x98
      98:	1d 00 00 14	b	0x10c
      9c:	08 00 00 90	adrp	x8, _cdx14_vt_owned@PAGE
      a0:	08 01 00 91	add	x8, x8, _cdx14_vt_owned@PAGEOFF
      a4:	08 fd df 88	ldar	w8, [x8]
      a8:	e8 17 00 b9	str	w8, [sp, #0x14]
      ac:	e8 17 40 b9	ldr	w8, [sp, #0x14]
      b0:	e9 0f 40 f9	ldr	x9, [sp, #0x18]
      b4:	28 01 00 b9	str	w8, [x9]
      b8:	08 00 00 90	adrp	x8, _gc_enabled@PAGE
      bc:	08 01 40 b9	ldr	w8, [x8, _gc_enabled@PAGEOFF]
      c0:	e9 0f 40 f9	ldr	x9, [sp, #0x18]
      c4:	28 05 00 b9	str	w8, [x9, #0x4]
      c8:	08 00 00 90	adrp	x8, _disableConsoleOutput@PAGE
      cc:	08 01 40 b9	ldr	w8, [x8, _disableConsoleOutput@PAGEOFF]
      d0:	e9 0f 40 f9	ldr	x9, [sp, #0x18]
      d4:	28 09 00 b9	str	w8, [x9, #0x8]
      d8:	08 00 00 90	adrp	x8, _cdx14_vt_blocked@PAGE
      dc:	08 01 40 b9	ldr	w8, [x8, _cdx14_vt_blocked@PAGEOFF]
      e0:	e8 13 00 b9	str	w8, [sp, #0x10]
      e4:	e8 13 40 b9	ldr	w8, [sp, #0x10]
      e8:	e9 0f 40 f9	ldr	x9, [sp, #0x18]
      ec:	28 0d 00 b9	str	w8, [x9, #0xc]
      f0:	08 00 00 90	adrp	x8, _cdx14_vt_drawn@PAGE
      f4:	08 01 40 b9	ldr	w8, [x8, _cdx14_vt_drawn@PAGEOFF]
      f8:	e8 0f 00 b9	str	w8, [sp, #0xc]
      fc:	e8 0f 40 b9	ldr	w8, [sp, #0xc]
     100:	e9 0f 40 f9	ldr	x9, [sp, #0x18]
     104:	28 11 00 b9	str	w8, [x9, #0x10]
     108:	01 00 00 14	b	0x10c
     10c:	ff 83 00 91	add	sp, sp, #0x20
     110:	c0 03 5f d6	ret
_cdx14_daemon_summary:
     114:	ff 43 02 d1	sub	sp, sp, #0x90
     118:	fd 7b 08 a9	stp	x29, x30, [sp, #0x80]
     11c:	fd 03 02 91	add	x29, sp, #0x80
     120:	a0 03 1f f8	stur	x0, [x29, #-0x10]
     124:	a1 83 1e f8	stur	x1, [x29, #-0x18]
     128:	a8 03 5f f8	ldur	x8, [x29, #-0x10]
     12c:	a8 00 00 b4	cbz	x8, 0x140
     130:	01 00 00 14	b	0x134
     134:	a8 83 5e f8	ldur	x8, [x29, #-0x18]
     138:	a8 00 00 b5	cbnz	x8, 0x14c
     13c:	01 00 00 14	b	0x140
     140:	08 00 80 d2	mov	x8, #0x0
     144:	a8 83 1f f8	stur	x8, [x29, #-0x8]
     148:	6a 00 00 14	b	0x2f0
     14c:	08 00 80 d2	mov	x8, #0x0
     150:	a8 03 1e f8	stur	x8, [x29, #-0x20]
     154:	a9 03 5f f8	ldur	x9, [x29, #-0x10]
     158:	08 00 80 52	mov	w8, #0x0
     15c:	28 01 00 39	strb	w8, [x9]
     160:	a8 c3 1d b8	stur	w8, [x29, #-0x24]
     164:	01 00 00 14	b	0x168
     168:	a9 c3 5d b8	ldur	w9, [x29, #-0x24]
     16c:	08 00 80 52	mov	w8, #0x0
     170:	29 0d 00 71	subs	w9, w9, #0x3
     174:	e8 3f 00 b9	str	w8, [sp, #0x3c]
     178:	28 01 00 54	b.hi	0x19c
     17c:	01 00 00 14	b	0x180
     180:	a8 03 5e f8	ldur	x8, [x29, #-0x20]
     184:	a9 83 5e f8	ldur	x9, [x29, #-0x18]
     188:	29 05 00 f1	subs	x9, x9, #0x1
     18c:	08 01 09 eb	subs	x8, x8, x9
     190:	e8 27 9f 1a	cset	w8, lo
     194:	e8 3f 00 b9	str	w8, [sp, #0x3c]
     198:	01 00 00 14	b	0x19c
     19c:	e8 3f 40 b9	ldr	w8, [sp, #0x3c]
     1a0:	28 0a 00 36	tbz	w8, #0x0, 0x2e4
     1a4:	01 00 00 14	b	0x1a8
     1a8:	a8 03 5f f8	ldur	x8, [x29, #-0x10]
     1ac:	a9 03 5e f8	ldur	x9, [x29, #-0x20]
     1b0:	00 01 09 8b	add	x0, x8, x9
     1b4:	a8 83 5e f8	ldur	x8, [x29, #-0x18]
     1b8:	01 01 09 eb	subs	x1, x8, x9
     1bc:	a8 c3 5d b8	ldur	w8, [x29, #-0x24]
     1c0:	e9 03 08 aa	mov	x9, x8
     1c4:	08 00 00 90	adrp	x8, _cdx14_names@PAGE
     1c8:	08 01 00 91	add	x8, x8, _cdx14_names@PAGEOFF
     1cc:	08 79 69 f8	ldr	x8, [x8, x9, lsl #3]
     1d0:	0a 03 80 52	mov	w10, #0x18
     1d4:	e2 03 0a aa	mov	x2, x10
     1d8:	ec 03 02 aa	mov	x12, x2
     1dc:	29 7d ac 9b	umull	x9, w9, w12
     1e0:	0d 00 00 90	adrp	x13, _cdx14_daemons@PAGE
     1e4:	ad 01 00 91	add	x13, x13, _cdx14_daemons@PAGEOFF
     1e8:	a9 69 69 b8	ldr	w9, [x13, x9]
     1ec:	a9 43 1d b8	stur	w9, [x29, #-0x2c]
     1f0:	a9 c3 5d b8	ldur	w9, [x29, #-0x24]
     1f4:	e2 03 09 aa	mov	x2, x9
     1f8:	e9 03 02 aa	mov	x9, x2
     1fc:	29 35 ac 9b	umaddl	x9, w9, w12, x13
     200:	aa 43 5d b8	ldur	w10, [x29, #-0x2c]
     204:	29 05 40 b9	ldr	w9, [x9, #0x4]
     208:	a9 03 1d b8	stur	w9, [x29, #-0x30]
     20c:	a9 c3 5d b8	ldur	w9, [x29, #-0x24]
     210:	e2 03 09 aa	mov	x2, x9
     214:	e9 03 02 aa	mov	x9, x2
     218:	29 35 ac 9b	umaddl	x9, w9, w12, x13
     21c:	ab 03 5d b8	ldur	w11, [x29, #-0x30]
     220:	29 09 40 b9	ldr	w9, [x9, #0x8]
     224:	a9 c3 1c b8	stur	w9, [x29, #-0x34]
     228:	a9 c3 5d b8	ldur	w9, [x29, #-0x24]
     22c:	e2 03 09 aa	mov	x2, x9
     230:	e9 03 02 aa	mov	x9, x2
     234:	29 35 ac 9b	umaddl	x9, w9, w12, x13
     238:	ac c3 5c b8	ldur	w12, [x29, #-0x34]
     23c:	29 09 40 f9	ldr	x9, [x9, #0x10]
     240:	e9 23 00 f9	str	x9, [sp, #0x40]
     244:	ed 23 40 f9	ldr	x13, [sp, #0x40]
     248:	e9 03 00 91	mov	x9, sp
     24c:	2d 11 00 f9	str	x13, [x9, #0x20]
     250:	2c 0d 00 f9	str	x12, [x9, #0x18]
     254:	2b 09 00 f9	str	x11, [x9, #0x10]
     258:	2a 05 00 f9	str	x10, [x9, #0x8]
     25c:	28 01 00 f9	str	x8, [x9]
     260:	02 00 00 90	adrp	x2, l_.str@PAGE
     264:	42 00 00 91	add	x2, x2, l_.str@PAGEOFF
     268:	00 00 00 94	bl	_snprintf
     26c:	a0 83 1d b8	stur	w0, [x29, #-0x28]
     270:	a8 83 5d b8	ldur	w8, [x29, #-0x28]
     274:	68 00 f8 36	tbz	w8, #0x1f, 0x280
     278:	01 00 00 14	b	0x27c
     27c:	1a 00 00 14	b	0x2e4
     280:	a8 83 9d b8	ldursw	x8, [x29, #-0x28]
     284:	a9 83 5e f8	ldur	x9, [x29, #-0x18]
     288:	aa 03 5e f8	ldur	x10, [x29, #-0x20]
     28c:	29 01 0a eb	subs	x9, x9, x10
     290:	08 01 09 eb	subs	x8, x8, x9
     294:	a2 00 00 54	b.hs	0x2a8
     298:	01 00 00 14	b	0x29c
     29c:	a8 83 9d b8	ldursw	x8, [x29, #-0x28]
     2a0:	e8 1b 00 f9	str	x8, [sp, #0x30]
     2a4:	07 00 00 14	b	0x2c0
     2a8:	a9 83 5e f8	ldur	x9, [x29, #-0x18]
     2ac:	a8 03 5e f8	ldur	x8, [x29, #-0x20]
     2b0:	e8 03 28 aa	mvn	x8, x8
     2b4:	08 01 09 8b	add	x8, x8, x9
     2b8:	e8 1b 00 f9	str	x8, [sp, #0x30]
     2bc:	01 00 00 14	b	0x2c0
     2c0:	e9 1b 40 f9	ldr	x9, [sp, #0x30]
     2c4:	a8 03 5e f8	ldur	x8, [x29, #-0x20]
     2c8:	08 01 09 8b	add	x8, x8, x9
     2cc:	a8 03 1e f8	stur	x8, [x29, #-0x20]
     2d0:	01 00 00 14	b	0x2d4
     2d4:	a8 c3 5d b8	ldur	w8, [x29, #-0x24]
     2d8:	08 05 00 11	add	w8, w8, #0x1
     2dc:	a8 c3 1d b8	stur	w8, [x29, #-0x24]
     2e0:	a2 ff ff 17	b	0x168
     2e4:	a8 03 5e f8	ldur	x8, [x29, #-0x20]
     2e8:	a8 83 1f f8	stur	x8, [x29, #-0x8]
     2ec:	01 00 00 14	b	0x2f0
     2f0:	a0 83 5f f8	ldur	x0, [x29, #-0x8]
     2f4:	fd 7b 48 a9	ldp	x29, x30, [sp, #0x80]
     2f8:	ff 43 02 91	add	sp, sp, #0x90
     2fc:	c0 03 5f d6	ret
_cdx14_daemon_exception:
     300:	ff 43 02 d1	sub	sp, sp, #0x90
     304:	fd 7b 08 a9	stp	x29, x30, [sp, #0x80]
     308:	fd 03 02 91	add	x29, sp, #0x80
     30c:	a0 83 1f f8	stur	x0, [x29, #-0x8]
     310:	a1 43 1f b8	stur	w1, [x29, #-0xc]
     314:	a2 83 1e f8	stur	x2, [x29, #-0x18]
     318:	a3 03 1e f8	stur	x3, [x29, #-0x20]
     31c:	a8 83 5f f8	ldur	x8, [x29, #-0x8]
     320:	68 00 00 b5	cbnz	x8, 0x32c
     324:	01 00 00 14	b	0x328
     328:	6c 00 00 14	b	0x4d8
     32c:	08 00 80 52	mov	w8, #0x0
     330:	a8 c3 1d b8	stur	w8, [x29, #-0x24]
     334:	01 00 00 14	b	0x338
     338:	a8 c3 5d b8	ldur	w8, [x29, #-0x24]
     33c:	08 0d 00 71	subs	w8, w8, #0x3
     340:	c8 0c 00 54	b.hi	0x4d8
     344:	01 00 00 14	b	0x348
     348:	a0 83 5f f8	ldur	x0, [x29, #-0x8]
     34c:	a8 c3 5d b8	ldur	w8, [x29, #-0x24]
     350:	e9 03 08 aa	mov	x9, x8
     354:	08 00 00 90	adrp	x8, _cdx14_names@PAGE
     358:	08 01 00 91	add	x8, x8, _cdx14_names@PAGEOFF
     35c:	01 79 69 f8	ldr	x1, [x8, x9, lsl #3]
     360:	00 00 00 94	bl	_strcmp
     364:	60 00 00 34	cbz	w0, 0x370
     368:	01 00 00 14	b	0x36c
     36c:	57 00 00 14	b	0x4c8
     370:	a8 c3 5d b8	ldur	w8, [x29, #-0x24]
     374:	e0 03 08 aa	mov	x0, x8
     378:	08 03 80 52	mov	w8, #0x18
     37c:	e1 03 08 aa	mov	x1, x8
     380:	e9 03 01 aa	mov	x9, x1
     384:	e8 03 00 aa	mov	x8, x0
     388:	0a 00 00 90	adrp	x10, _cdx14_exceptions@PAGE
     38c:	4a 01 00 91	add	x10, x10, _cdx14_exceptions@PAGEOFF
     390:	08 29 a9 9b	umaddl	x8, w8, w9, x10
     394:	e9 03 08 aa	mov	x9, x8
     398:	e9 17 00 f9	str	x9, [sp, #0x28]
     39c:	29 00 80 52	mov	w9, #0x1
     3a0:	a9 43 1d b8	stur	w9, [x29, #-0x2c]
     3a4:	a9 43 5d b8	ldur	w9, [x29, #-0x2c]
     3a8:	e9 33 00 b9	str	w9, [sp, #0x30]
     3ac:	08 01 40 b9	ldr	w8, [x8]
     3b0:	e8 37 00 b9	str	w8, [sp, #0x34]
     3b4:	01 00 00 14	b	0x3b8
     3b8:	e9 37 40 b9	ldr	w9, [sp, #0x34]
     3bc:	eb 17 40 f9	ldr	x11, [sp, #0x28]
     3c0:	e8 33 40 b9	ldr	w8, [sp, #0x30]
     3c4:	2c 01 08 0b	add	w12, w9, w8
     3c8:	68 fd 5f 88	ldaxr	w8, [x11]
     3cc:	1f 01 09 6b	cmp	w8, w9
     3d0:	61 00 00 54	b.ne	0x3dc
     3d4:	6c fd 0a 88	stlxr	w10, w12, [x11]
     3d8:	8a ff ff 35	cbnz	w10, 0x3c8
     3dc:	09 01 09 6b	subs	w9, w8, w9
     3e0:	e8 27 00 b9	str	w8, [sp, #0x24]
     3e4:	e8 37 00 b9	str	w8, [sp, #0x34]
     3e8:	81 fe ff 54	b.ne	0x3b8
     3ec:	01 00 00 14	b	0x3f0
     3f0:	e8 27 40 b9	ldr	w8, [sp, #0x24]
     3f4:	e9 33 40 b9	ldr	w9, [sp, #0x30]
     3f8:	08 01 09 0b	add	w8, w8, w9
     3fc:	a8 03 1d b8	stur	w8, [x29, #-0x30]
     400:	a8 03 5d b8	ldur	w8, [x29, #-0x30]
     404:	a8 83 1d b8	stur	w8, [x29, #-0x28]
     408:	a8 c3 5d b8	ldur	w8, [x29, #-0x24]
     40c:	e0 03 08 aa	mov	x0, x8
     410:	08 03 80 52	mov	w8, #0x18
     414:	e1 03 08 aa	mov	x1, x8
     418:	e9 03 01 aa	mov	x9, x1
     41c:	e8 03 00 aa	mov	x8, x0
     420:	0a 00 00 90	adrp	x10, _cdx14_exceptions@PAGE
     424:	4a 01 00 91	add	x10, x10, _cdx14_exceptions@PAGEOFF
     428:	0b 29 a9 9b	umaddl	x11, w8, w9, x10
     42c:	a8 43 5f b8	ldur	w8, [x29, #-0xc]
     430:	a8 c3 1c b8	stur	w8, [x29, #-0x34]
     434:	a8 c3 5c b8	ldur	w8, [x29, #-0x34]
     438:	68 05 00 b9	str	w8, [x11, #0x4]
     43c:	a8 c3 5d b8	ldur	w8, [x29, #-0x24]
     440:	e0 03 08 aa	mov	x0, x8
     444:	e8 03 00 aa	mov	x8, x0
     448:	0b 29 a9 9b	umaddl	x11, w8, w9, x10
     44c:	a8 83 5e f8	ldur	x8, [x29, #-0x18]
     450:	e8 23 00 f9	str	x8, [sp, #0x40]
     454:	e8 23 40 f9	ldr	x8, [sp, #0x40]
     458:	68 05 00 f9	str	x8, [x11, #0x8]
     45c:	a8 c3 5d b8	ldur	w8, [x29, #-0x24]
     460:	e0 03 08 aa	mov	x0, x8
     464:	e8 03 00 aa	mov	x8, x0
     468:	09 29 a9 9b	umaddl	x9, w8, w9, x10
     46c:	a8 03 5e f8	ldur	x8, [x29, #-0x20]
     470:	e8 1f 00 f9	str	x8, [sp, #0x38]
     474:	e8 1f 40 f9	ldr	x8, [sp, #0x38]
     478:	28 09 00 f9	str	x8, [x9, #0x10]
     47c:	a8 83 5d b8	ldur	w8, [x29, #-0x28]
     480:	08 11 00 71	subs	w8, w8, #0x4
     484:	08 02 00 54	b.hi	0x4c4
     488:	01 00 00 14	b	0x48c
     48c:	a8 83 5f f8	ldur	x8, [x29, #-0x8]
     490:	ab 83 5e f8	ldur	x11, [x29, #-0x18]
     494:	ac 03 5e f8	ldur	x12, [x29, #-0x20]
     498:	a9 43 5f b8	ldur	w9, [x29, #-0xc]
     49c:	ea 03 09 aa	mov	x10, x9
     4a0:	e9 03 00 91	mov	x9, sp
     4a4:	2c 0d 00 f9	str	x12, [x9, #0x18]
     4a8:	2b 09 00 f9	str	x11, [x9, #0x10]
     4ac:	2a 05 00 f9	str	x10, [x9, #0x8]
     4b0:	28 01 00 f9	str	x8, [x9]
     4b4:	00 00 00 90	adrp	x0, l_.str.1@PAGE
     4b8:	00 00 00 91	add	x0, x0, l_.str.1@PAGEOFF
     4bc:	00 00 00 94	bl	_printf
     4c0:	01 00 00 14	b	0x4c4
     4c4:	05 00 00 14	b	0x4d8
     4c8:	a8 c3 5d b8	ldur	w8, [x29, #-0x24]
     4cc:	08 05 00 11	add	w8, w8, #0x1
     4d0:	a8 c3 1d b8	stur	w8, [x29, #-0x24]
     4d4:	99 ff ff 17	b	0x338
     4d8:	fd 7b 48 a9	ldp	x29, x30, [sp, #0x80]
     4dc:	ff 43 02 91	add	sp, sp, #0x90
     4e0:	c0 03 5f d6	ret
_cdx14_exception_summary:
     4e4:	ff 43 02 d1	sub	sp, sp, #0x90
     4e8:	fd 7b 08 a9	stp	x29, x30, [sp, #0x80]
     4ec:	fd 03 02 91	add	x29, sp, #0x80
     4f0:	a0 03 1f f8	stur	x0, [x29, #-0x10]
     4f4:	a1 83 1e f8	stur	x1, [x29, #-0x18]
     4f8:	a8 03 5f f8	ldur	x8, [x29, #-0x10]
     4fc:	a8 00 00 b4	cbz	x8, 0x510
     500:	01 00 00 14	b	0x504
     504:	a8 83 5e f8	ldur	x8, [x29, #-0x18]
     508:	a8 00 00 b5	cbnz	x8, 0x51c
     50c:	01 00 00 14	b	0x510
     510:	08 00 80 d2	mov	x8, #0x0
     514:	a8 83 1f f8	stur	x8, [x29, #-0x8]
     518:	6a 00 00 14	b	0x6c0
     51c:	08 00 80 d2	mov	x8, #0x0
     520:	a8 03 1e f8	stur	x8, [x29, #-0x20]
     524:	a9 03 5f f8	ldur	x9, [x29, #-0x10]
     528:	08 00 80 52	mov	w8, #0x0
     52c:	28 01 00 39	strb	w8, [x9]
     530:	a8 c3 1d b8	stur	w8, [x29, #-0x24]
     534:	01 00 00 14	b	0x538
     538:	a9 c3 5d b8	ldur	w9, [x29, #-0x24]
     53c:	08 00 80 52	mov	w8, #0x0
     540:	29 0d 00 71	subs	w9, w9, #0x3
     544:	e8 3f 00 b9	str	w8, [sp, #0x3c]
     548:	28 01 00 54	b.hi	0x56c
     54c:	01 00 00 14	b	0x550
     550:	a8 03 5e f8	ldur	x8, [x29, #-0x20]
     554:	a9 83 5e f8	ldur	x9, [x29, #-0x18]
     558:	29 05 00 f1	subs	x9, x9, #0x1
     55c:	08 01 09 eb	subs	x8, x8, x9
     560:	e8 27 9f 1a	cset	w8, lo
     564:	e8 3f 00 b9	str	w8, [sp, #0x3c]
     568:	01 00 00 14	b	0x56c
     56c:	e8 3f 40 b9	ldr	w8, [sp, #0x3c]
     570:	28 0a 00 36	tbz	w8, #0x0, 0x6b4
     574:	01 00 00 14	b	0x578
     578:	a8 03 5f f8	ldur	x8, [x29, #-0x10]
     57c:	a9 03 5e f8	ldur	x9, [x29, #-0x20]
     580:	00 01 09 8b	add	x0, x8, x9
     584:	a8 83 5e f8	ldur	x8, [x29, #-0x18]
     588:	01 01 09 eb	subs	x1, x8, x9
     58c:	a8 c3 5d b8	ldur	w8, [x29, #-0x24]
     590:	e9 03 08 aa	mov	x9, x8
     594:	08 00 00 90	adrp	x8, _cdx14_names@PAGE
     598:	08 01 00 91	add	x8, x8, _cdx14_names@PAGEOFF
     59c:	08 79 69 f8	ldr	x8, [x8, x9, lsl #3]
     5a0:	0a 03 80 52	mov	w10, #0x18
     5a4:	e2 03 0a aa	mov	x2, x10
     5a8:	ed 03 02 aa	mov	x13, x2
     5ac:	29 7d ad 9b	umull	x9, w9, w13
     5b0:	0e 00 00 90	adrp	x14, _cdx14_exceptions@PAGE
     5b4:	ce 01 00 91	add	x14, x14, _cdx14_exceptions@PAGEOFF
     5b8:	c9 69 69 b8	ldr	w9, [x14, x9]
     5bc:	a9 43 1d b8	stur	w9, [x29, #-0x2c]
     5c0:	a9 c3 5d b8	ldur	w9, [x29, #-0x24]
     5c4:	e2 03 09 aa	mov	x2, x9
     5c8:	e9 03 02 aa	mov	x9, x2
     5cc:	29 39 ad 9b	umaddl	x9, w9, w13, x14
     5d0:	aa 43 5d b8	ldur	w10, [x29, #-0x2c]
     5d4:	29 05 40 b9	ldr	w9, [x9, #0x4]
     5d8:	a9 03 1d b8	stur	w9, [x29, #-0x30]
     5dc:	a9 c3 5d b8	ldur	w9, [x29, #-0x24]
     5e0:	e2 03 09 aa	mov	x2, x9
     5e4:	e9 03 02 aa	mov	x9, x2
     5e8:	29 39 ad 9b	umaddl	x9, w9, w13, x14
     5ec:	ab 03 5d b8	ldur	w11, [x29, #-0x30]
     5f0:	29 05 40 f9	ldr	x9, [x9, #0x8]
     5f4:	a9 83 1c f8	stur	x9, [x29, #-0x38]
     5f8:	ac 83 5c f8	ldur	x12, [x29, #-0x38]
     5fc:	a9 c3 5d b8	ldur	w9, [x29, #-0x24]
     600:	e2 03 09 aa	mov	x2, x9
     604:	e9 03 02 aa	mov	x9, x2
     608:	29 39 ad 9b	umaddl	x9, w9, w13, x14
     60c:	29 09 40 f9	ldr	x9, [x9, #0x10]
     610:	e9 23 00 f9	str	x9, [sp, #0x40]
     614:	ed 23 40 f9	ldr	x13, [sp, #0x40]
     618:	e9 03 00 91	mov	x9, sp
     61c:	2d 11 00 f9	str	x13, [x9, #0x20]
     620:	2c 0d 00 f9	str	x12, [x9, #0x18]
     624:	2b 09 00 f9	str	x11, [x9, #0x10]
     628:	2a 05 00 f9	str	x10, [x9, #0x8]
     62c:	28 01 00 f9	str	x8, [x9]
     630:	02 00 00 90	adrp	x2, l_.str.2@PAGE
     634:	42 00 00 91	add	x2, x2, l_.str.2@PAGEOFF
     638:	00 00 00 94	bl	_snprintf
     63c:	a0 83 1d b8	stur	w0, [x29, #-0x28]
     640:	a8 83 5d b8	ldur	w8, [x29, #-0x28]
     644:	68 00 f8 36	tbz	w8, #0x1f, 0x650
     648:	01 00 00 14	b	0x64c
     64c:	1a 00 00 14	b	0x6b4
     650:	a8 83 9d b8	ldursw	x8, [x29, #-0x28]
     654:	a9 83 5e f8	ldur	x9, [x29, #-0x18]
     658:	aa 03 5e f8	ldur	x10, [x29, #-0x20]
     65c:	29 01 0a eb	subs	x9, x9, x10
     660:	08 01 09 eb	subs	x8, x8, x9
     664:	a2 00 00 54	b.hs	0x678
     668:	01 00 00 14	b	0x66c
     66c:	a8 83 9d b8	ldursw	x8, [x29, #-0x28]
     670:	e8 1b 00 f9	str	x8, [sp, #0x30]
     674:	07 00 00 14	b	0x690
     678:	a9 83 5e f8	ldur	x9, [x29, #-0x18]
     67c:	a8 03 5e f8	ldur	x8, [x29, #-0x20]
     680:	e8 03 28 aa	mvn	x8, x8
     684:	08 01 09 8b	add	x8, x8, x9
     688:	e8 1b 00 f9	str	x8, [sp, #0x30]
     68c:	01 00 00 14	b	0x690
     690:	e9 1b 40 f9	ldr	x9, [sp, #0x30]
     694:	a8 03 5e f8	ldur	x8, [x29, #-0x20]
     698:	08 01 09 8b	add	x8, x8, x9
     69c:	a8 03 1e f8	stur	x8, [x29, #-0x20]
     6a0:	01 00 00 14	b	0x6a4
     6a4:	a8 c3 5d b8	ldur	w8, [x29, #-0x24]
     6a8:	08 05 00 11	add	w8, w8, #0x1
     6ac:	a8 c3 1d b8	stur	w8, [x29, #-0x24]
     6b0:	a2 ff ff 17	b	0x538
     6b4:	a8 03 5e f8	ldur	x8, [x29, #-0x20]
     6b8:	a8 83 1f f8	stur	x8, [x29, #-0x8]
     6bc:	01 00 00 14	b	0x6c0
     6c0:	a0 83 5f f8	ldur	x0, [x29, #-0x8]
     6c4:	fd 7b 48 a9	ldp	x29, x30, [sp, #0x80]
     6c8:	ff 43 02 91	add	sp, sp, #0x90
     6cc:	c0 03 5f d6	ret
_cdx14_fixture_calls:
     6d0:	ff 83 00 d1	sub	sp, sp, #0x20
     6d4:	fd 7b 01 a9	stp	x29, x30, [sp, #0x10]
     6d8:	fd 43 00 91	add	x29, sp, #0x10
     6dc:	e0 07 00 f9	str	x0, [sp, #0x8]
     6e0:	00 00 00 94	bl	_cdx14_vt_should_block
     6e4:	e0 07 40 f9	ldr	x0, [sp, #0x8]
     6e8:	01 00 80 52	mov	w1, #0x0
     6ec:	00 00 00 94	bl	_cdx14_observe_exit
     6f0:	fd 7b 41 a9	ldp	x29, x30, [sp, #0x10]
     6f4:	ff 83 00 91	add	sp, sp, #0x20
     6f8:	c0 03 5f d6	ret
_cdx14_vt_should_block:
     6fc:	ff 83 00 d1	sub	sp, sp, #0x20
     700:	fd 7b 01 a9	stp	x29, x30, [sp, #0x10]
     704:	fd 43 00 91	add	x29, sp, #0x10
     708:	08 00 00 90	adrp	x8, _cdx14_vt_owned@PAGE
     70c:	08 01 00 91	add	x8, x8, _cdx14_vt_owned@PAGEOFF
     710:	08 fd df 88	ldar	w8, [x8]
     714:	a8 c3 1f b8	stur	w8, [x29, #-0x4]
     718:	a8 c3 5f b8	ldur	w8, [x29, #-0x4]
     71c:	09 00 80 52	mov	w9, #0x0
     720:	e9 0b 00 b9	str	w9, [sp, #0x8]
     724:	e8 00 00 34	cbz	w8, 0x740
     728:	01 00 00 14	b	0x72c
     72c:	00 00 00 94	bl	_panic_active
     730:	08 00 00 71	subs	w8, w0, #0x0
     734:	e8 17 9f 1a	cset	w8, eq
     738:	e8 0b 00 b9	str	w8, [sp, #0x8]
     73c:	01 00 00 14	b	0x740
     740:	e8 0b 40 b9	ldr	w8, [sp, #0x8]
     744:	00 01 00 12	and	w0, w8, #0x1
     748:	fd 7b 41 a9	ldp	x29, x30, [sp, #0x10]
     74c:	ff 83 00 91	add	sp, sp, #0x20
     750:	c0 03 5f d6	ret
_cdx14_observe_exit:
     754:	ff 03 03 d1	sub	sp, sp, #0xc0
     758:	fd 7b 0b a9	stp	x29, x30, [sp, #0xb0]
     75c:	fd c3 02 91	add	x29, sp, #0xb0
     760:	a0 83 1f f8	stur	x0, [x29, #-0x8]
     764:	a1 43 1f b8	stur	w1, [x29, #-0xc]
     768:	08 00 80 52	mov	w8, #0x0
     76c:	a8 03 1f b8	stur	w8, [x29, #-0x10]
     770:	01 00 00 14	b	0x774
     774:	a8 03 5f b8	ldur	w8, [x29, #-0x10]
     778:	08 0d 00 71	subs	w8, w8, #0x3
     77c:	48 12 00 54	b.hi	0x9c4
     780:	01 00 00 14	b	0x784
     784:	a0 83 5f f8	ldur	x0, [x29, #-0x8]
     788:	a8 03 5f b8	ldur	w8, [x29, #-0x10]
     78c:	e9 03 08 aa	mov	x9, x8
     790:	08 00 00 90	adrp	x8, _cdx14_names@PAGE
     794:	08 01 00 91	add	x8, x8, _cdx14_names@PAGEOFF
     798:	01 79 69 f8	ldr	x1, [x8, x9, lsl #3]
     79c:	00 00 00 94	bl	_strcmp
     7a0:	60 00 00 34	cbz	w0, 0x7ac
     7a4:	01 00 00 14	b	0x7a8
     7a8:	83 00 00 14	b	0x9b4
     7ac:	a8 03 5f b8	ldur	w8, [x29, #-0x10]
     7b0:	e0 03 08 aa	mov	x0, x8
     7b4:	08 03 80 52	mov	w8, #0x18
     7b8:	e1 03 08 aa	mov	x1, x8
     7bc:	e9 03 01 aa	mov	x9, x1
     7c0:	e8 03 00 aa	mov	x8, x0
     7c4:	0a 00 00 90	adrp	x10, _cdx14_daemons@PAGE
     7c8:	4a 01 00 91	add	x10, x10, _cdx14_daemons@PAGEOFF
     7cc:	08 29 a9 9b	umaddl	x8, w8, w9, x10
     7d0:	e9 03 08 aa	mov	x9, x8
     7d4:	a9 83 1b f8	stur	x9, [x29, #-0x48]
     7d8:	29 00 80 52	mov	w9, #0x1
     7dc:	a9 83 1e b8	stur	w9, [x29, #-0x18]
     7e0:	a9 83 5e b8	ldur	w9, [x29, #-0x18]
     7e4:	a9 03 1c b8	stur	w9, [x29, #-0x40]
     7e8:	08 01 40 b9	ldr	w8, [x8]
     7ec:	a8 43 1c b8	stur	w8, [x29, #-0x3c]
     7f0:	01 00 00 14	b	0x7f4
     7f4:	a9 43 5c b8	ldur	w9, [x29, #-0x3c]
     7f8:	ab 83 5b f8	ldur	x11, [x29, #-0x48]
     7fc:	a8 03 5c b8	ldur	w8, [x29, #-0x40]
     800:	2c 01 08 0b	add	w12, w9, w8
     804:	68 fd 5f 88	ldaxr	w8, [x11]
     808:	1f 01 09 6b	cmp	w8, w9
     80c:	61 00 00 54	b.ne	0x818
     810:	6c fd 0a 88	stlxr	w10, w12, [x11]
     814:	8a ff ff 35	cbnz	w10, 0x804
     818:	09 01 09 6b	subs	w9, w8, w9
     81c:	a8 43 1b b8	stur	w8, [x29, #-0x4c]
     820:	a8 43 1c b8	stur	w8, [x29, #-0x3c]
     824:	81 fe ff 54	b.ne	0x7f4
     828:	01 00 00 14	b	0x82c
     82c:	a8 43 5b b8	ldur	w8, [x29, #-0x4c]
     830:	a9 03 5c b8	ldur	w9, [x29, #-0x40]
     834:	08 01 09 0b	add	w8, w8, w9
     838:	a8 43 1e b8	stur	w8, [x29, #-0x1c]
     83c:	a8 43 5e b8	ldur	w8, [x29, #-0x1c]
     840:	a8 c3 1e b8	stur	w8, [x29, #-0x14]
     844:	a8 83 5f f8	ldur	x8, [x29, #-0x8]
     848:	08 15 40 f9	ldr	x8, [x8, #0x28]
     84c:	e8 00 00 b4	cbz	x8, 0x868
     850:	01 00 00 14	b	0x854
     854:	a8 83 5f f8	ldur	x8, [x29, #-0x8]
     858:	08 15 40 f9	ldr	x8, [x8, #0x28]
     85c:	08 01 40 b9	ldr	w8, [x8]
     860:	a8 03 1b b8	stur	w8, [x29, #-0x50]
     864:	04 00 00 14	b	0x874
     868:	08 00 80 52	mov	w8, #0x0
     86c:	a8 03 1b b8	stur	w8, [x29, #-0x50]
     870:	01 00 00 14	b	0x874
     874:	a8 03 5b b8	ldur	w8, [x29, #-0x50]
     878:	a8 03 1e b8	stur	w8, [x29, #-0x20]
     87c:	a8 83 5f f8	ldur	x8, [x29, #-0x8]
     880:	08 15 40 f9	ldr	x8, [x8, #0x28]
     884:	e8 00 00 b4	cbz	x8, 0x8a0
     888:	01 00 00 14	b	0x88c
     88c:	a8 83 5f f8	ldur	x8, [x29, #-0x8]
     890:	08 15 40 f9	ldr	x8, [x8, #0x28]
     894:	08 05 40 f9	ldr	x8, [x8, #0x8]
     898:	e8 2f 00 f9	str	x8, [sp, #0x58]
     89c:	04 00 00 14	b	0x8ac
     8a0:	08 00 80 d2	mov	x8, #0x0
     8a4:	e8 2f 00 f9	str	x8, [sp, #0x58]
     8a8:	01 00 00 14	b	0x8ac
     8ac:	e8 2f 40 f9	ldr	x8, [sp, #0x58]
     8b0:	a8 83 1d f8	stur	x8, [x29, #-0x28]
     8b4:	a8 03 5f b8	ldur	w8, [x29, #-0x10]
     8b8:	e0 03 08 aa	mov	x0, x8
     8bc:	08 03 80 52	mov	w8, #0x18
     8c0:	e1 03 08 aa	mov	x1, x8
     8c4:	e9 03 01 aa	mov	x9, x1
     8c8:	e9 57 00 b9	str	w9, [sp, #0x54]
     8cc:	e8 03 00 aa	mov	x8, x0
     8d0:	0a 00 00 90	adrp	x10, _cdx14_daemons@PAGE
     8d4:	4a 01 00 91	add	x10, x10, _cdx14_daemons@PAGEOFF
     8d8:	ea 27 00 f9	str	x10, [sp, #0x48]
     8dc:	08 29 a9 9b	umaddl	x8, w8, w9, x10
     8e0:	e8 23 00 f9	str	x8, [sp, #0x40]
     8e4:	a0 83 5f f8	ldur	x0, [x29, #-0x8]
     8e8:	00 00 00 94	bl	_proc_getpid
     8ec:	eb 23 40 f9	ldr	x11, [sp, #0x40]
     8f0:	ea 27 40 f9	ldr	x10, [sp, #0x48]
     8f4:	e9 57 40 b9	ldr	w9, [sp, #0x54]
     8f8:	a0 43 1d b8	stur	w0, [x29, #-0x2c]
     8fc:	a8 43 5d b8	ldur	w8, [x29, #-0x2c]
     900:	68 05 00 b9	str	w8, [x11, #0x4]
     904:	a8 03 5f b8	ldur	w8, [x29, #-0x10]
     908:	e0 03 08 aa	mov	x0, x8
     90c:	e8 03 00 aa	mov	x8, x0
     910:	0b 29 a9 9b	umaddl	x11, w8, w9, x10
     914:	a8 03 5e b8	ldur	w8, [x29, #-0x20]
     918:	a8 03 1d b8	stur	w8, [x29, #-0x30]
     91c:	a8 03 5d b8	ldur	w8, [x29, #-0x30]
     920:	68 09 00 b9	str	w8, [x11, #0x8]
     924:	a8 03 5f b8	ldur	w8, [x29, #-0x10]
     928:	e0 03 08 aa	mov	x0, x8
     92c:	e8 03 00 aa	mov	x8, x0
     930:	09 29 a9 9b	umaddl	x9, w8, w9, x10
     934:	a8 83 5d f8	ldur	x8, [x29, #-0x28]
     938:	a8 83 1c f8	stur	x8, [x29, #-0x38]
     93c:	a8 83 5c f8	ldur	x8, [x29, #-0x38]
     940:	28 09 00 f9	str	x8, [x9, #0x10]
     944:	a8 c3 5e b8	ldur	w8, [x29, #-0x14]
     948:	08 11 00 71	subs	w8, w8, #0x4
     94c:	28 03 00 54	b.hi	0x9b0
     950:	01 00 00 14	b	0x954
     954:	a0 83 5f f8	ldur	x0, [x29, #-0x8]
     958:	e0 1f 00 f9	str	x0, [sp, #0x38]
     95c:	00 00 00 94	bl	_proc_getpid
     960:	e8 1f 40 f9	ldr	x8, [sp, #0x38]
     964:	ac 83 5d f8	ldur	x12, [x29, #-0x28]
     968:	a9 43 5f b8	ldur	w9, [x29, #-0xc]
     96c:	ea 03 09 aa	mov	x10, x9
     970:	a9 03 5e b8	ldur	w9, [x29, #-0x20]
     974:	eb 03 09 aa	mov	x11, x9
     978:	a9 c3 5e b8	ldur	w9, [x29, #-0x14]
     97c:	ed 03 09 aa	mov	x13, x9
     980:	e9 03 00 91	mov	x9, sp
     984:	2d 15 00 f9	str	x13, [x9, #0x28]
     988:	2c 11 00 f9	str	x12, [x9, #0x20]
     98c:	2b 0d 00 f9	str	x11, [x9, #0x18]
     990:	2a 09 00 f9	str	x10, [x9, #0x10]
     994:	ea 03 00 aa	mov	x10, x0
     998:	2a 05 00 f9	str	x10, [x9, #0x8]
     99c:	28 01 00 f9	str	x8, [x9]
     9a0:	00 00 00 90	adrp	x0, l_.str.7@PAGE
     9a4:	00 00 00 91	add	x0, x0, l_.str.7@PAGEOFF
     9a8:	00 00 00 94	bl	_printf
     9ac:	01 00 00 14	b	0x9b0
     9b0:	05 00 00 14	b	0x9c4
     9b4:	a8 03 5f b8	ldur	w8, [x29, #-0x10]
     9b8:	08 05 00 11	add	w8, w8, #0x1
     9bc:	a8 03 1f b8	stur	w8, [x29, #-0x10]
     9c0:	6d ff ff 17	b	0x774
     9c4:	fd 7b 4b a9	ldp	x29, x30, [sp, #0xb0]
     9c8:	ff 03 03 91	add	sp, sp, #0xc0
     9cc:	c0 03 5f d6	ret
_panic_active:
     9d0:	08 00 00 90	adrp	x8, _mock_panic@PAGE
     9d4:	00 01 40 b9	ldr	w0, [x8, _mock_panic@PAGEOFF]
     9d8:	c0 03 5f d6	ret
_proc_getpid:
     9dc:	ff 43 00 d1	sub	sp, sp, #0x10
     9e0:	e0 07 00 f9	str	x0, [sp, #0x8]
     9e4:	e8 07 40 f9	ldr	x8, [sp, #0x8]
     9e8:	00 21 40 b9	ldr	w0, [x8, #0x20]
     9ec:	ff 43 00 91	add	sp, sp, #0x10
     9f0:	c0 03 5f d6	ret
