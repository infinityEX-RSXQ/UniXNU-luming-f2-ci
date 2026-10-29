#!/usr/bin/env python3
"""Read the luming UFS diagnostic log written by package/BootLog.c.

  read-luming-log.py DEVICE [--output DIR]

DEVICE is a block device or image of the root partition (sda36 on the tablet). The writer keeps the log in the last 32 MiB of that
partition: block 0 is the header. Two upstream writers share the window: LUMINGL2 (periodic BootLog: header, message blocks 1..128, board slots from block 129) and LUMINGL1 (panic/exec ring: header, text blocks 1..N). The reader prints whichever valid header is present; see docs/LOGGING.md. The header is written last in each round, so only the slots it counts are trusted.
"""
import argparse
import json
import struct
import sys
from pathlib import Path

BLOCK = 4096
MAGIC = b'LUMINGL2'
PANIC_MAGIC = b'LUMINGL1'
HEADER = struct.Struct('<8sIIQQ' + 'I' * 14 + '32s')
WINDOW_BLOCKS = 8192


def read_window(path):
    size = path.stat().st_size
    blocks = size // BLOCK
    if blocks < WINDOW_BLOCKS:
        sys.exit(f'{path}: {blocks} blocks is smaller than the {WINDOW_BLOCKS}-block window')
    with path.open('rb') as stream:
        stream.seek((blocks - WINDOW_BLOCKS) * BLOCK)
        return stream.read(WINDOW_BLOCKS * BLOCK)


def parse(window):
    fields = HEADER.unpack_from(window, 0)
    (magic, version, header_bytes, boot_id, first_lba, window_blocks, msg_first, msg_blocks, msg_bytes,
     slot_first, slot_blocks, slot_count, slots_written, uptime_s, rounds, write_errors, gpt_open, gpt_last,
     state, tag) = fields
    if magic != MAGIC:
        return None
    base = 0
    message = window[msg_first * BLOCK: msg_first * BLOCK + msg_bytes]
    slots = []
    for index in range(min(slots_written, slot_count)):
        at = (slot_first + index * slot_blocks) * BLOCK
        slots.append(window[at: at + slot_blocks * BLOCK])
    return {
        'version': version, 'header_bytes': header_bytes, 'boot_id': boot_id, 'first_lba': first_lba,
        'window_blocks': window_blocks, 'slot_count': slot_count, 'slots_written': slots_written,
        'uptime_s': uptime_s, 'rounds': rounds, 'write_errors': write_errors,
        'gpt_open': gpt_open, 'gpt_last': gpt_last, 'state': state,
        'tag': tag.split(b'\0')[0].decode(errors='replace'),
        'message': message, 'slots': slots,
    }


def rows(blob):
    for at in range(0, len(blob) - 120, 121):
        line = blob[at:at + 120].split(b'\0')[0].decode(errors='replace').rstrip()
        if line:
            yield line


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('device', type=Path)
    parser.add_argument('--output', type=Path, help='directory for the decoded text and the raw window')
    args = parser.parse_args()
    window = read_window(args.device)
    log = parse(window)
    if not log:
        sys.exit('no LUMINGL2/LUMINGL1 header: the writer did not open the window (check luming-log=1 and the boot-argument list)')
    print(f"boot_id {log['boot_id']} rounds {log['rounds']} uptime {log['uptime_s']}s state {log['state']} "
          f"tag {log['tag']!r} gpt {log['gpt_open']}->{log['gpt_last']} errors {log['write_errors']}")
    print(f"window {log['window_blocks']} blocks at LBA {log['first_lba']}, slots {log['slots_written']}/{log['slot_count']}")
    print('--- kernel message buffer ---')
    text = log['message'].decode(errors='replace').rstrip('\0')
    print(text[-20000:])
    print('--- newest board text ---')
    newest = rows(log['slots'][-1]) if log['slots'] else []
    for line in list(newest)[:60]:
        print(line)
    if args.output:
        args.output.mkdir(parents=True, exist_ok=True)
        (args.output / 'window.bin').write_bytes(window)
        (args.output / 'header.json').write_text(json.dumps(
            {k: v for k, v in log.items() if k not in ('message', 'slots')}, indent=2) + '\n')
        (args.output / 'message.txt').write_text(text + '\n')
        (args.output / 'board.txt').write_text('\n'.join(newest) + '\n')
        print(f'wrote {args.output}')


if __name__ == '__main__':
    main()