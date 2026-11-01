#!/usr/bin/env python3
"""Build the minimal IOMobileFramebuffer display provider archive for UniXNU.

Self-contained and repeatable:

  1. replay the XNU compile line recorded in IOPlatformExpert.cpo.json for
     drivers/NativeMobileDisplay/NativeMobileDisplay.cpp and
     package/MobileDisplayProviderProbe.cpp;
  2. emit original-bindings.S with the three fixed 21H461 symbols and assemble it;
  3. make NativeMobileDisplay.late.o (drop __DATA,__mod_init_func, globalize the
     own static constructor so the probe can call it in init order);
  4. pack libNativeMobileDisplay.late.a and write build-report.json with
     archive_sha256 + source_sha256 (the kernel link gate checks both).

The archive is what `XNU_NATIVE_MOBILE_DISPLAY=1` links as
build/native-mobile-display/libNativeMobileDisplay.late.a (format-1 tree) and, with
--layout format2, also as build/gop-framebuffer/libGopFramebuffer.late.a
(format-2 tree whose components.toml renamed the GopFramebuffer component).

Run it on macOS with Xcode and LLVM installed; it refuses to pretend otherwise.
"""

import argparse
import hashlib
import json
import os
import shutil
import struct
import subprocess
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Fixed original-binary bindings (iPadOS 17.7.11 / 21H461 profile pin).
# The original IOMobileGraphicsFamily kext is NOT rebuilt: its constructor, its
# destructor and its metaclass are taken as absolute addresses.
# ---------------------------------------------------------------------------
DEFAULT_BINDINGS = {
    "__ZN19IOMobileFramebufferC2EPK11OSMetaClass": 0xFFFF_FFF0_0577_B318,
    "__ZN19IOMobileFramebufferD2Ev": 0xFFFF_FFF0_0577_B364,
    "__ZN19IOMobileFramebuffer10gMetaClassE": 0xFFFF_FFF0_06B3_13D8,
}
BINDINGS_ORIGIN = "ipados-17.7.11-21H461 profile pin (three fixed addresses)"

DEFAULT_RECIPE = "build/xnu/ios-obj/DEVELOPMENT_ARM64_BCM2837/iokit/DEVELOPMENT/IOPlatformExpert.cpo.json"
DEFAULT_INIT_SYMBOL = "__GLOBAL__sub_I_NativeMobileDisplay.cpp"
MOD_INIT_SECTION = ("__DATA", "__mod_init_func")

MH_MAGIC_64 = 0xFEEDFACF
LC_SEGMENT_64 = 0x19
LC_SYMTAB = 0x2
LC_BUILD_VERSION = 0x32
LC_VERSION_MIN_IPHONEOS = 0x25
ARM64_CPUTYPE = 0x0100_000C
MH_OBJECT = 1
S_ATTR_PURE_INSTRUCTIONS = 0x8000_0000
S_ATTR_SOME_INSTRUCTIONS = 0x0000_0400
N_STAB = 0xE0
N_TYPE = 0x0E
N_SECT = 0x0E
N_EXT = 0x01


class BuildError(SystemExit):
    pass


def fail(message):
    raise BuildError("build-native-mobile-display: " + message)


def note(message):
    print("build-native-mobile-display: " + message, flush=True)


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def rel(path, root):
    try:
        return Path(path).resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return Path(path).as_posix()


def run(command, what, cwd=None):
    try:
        result = subprocess.run([str(x) for x in command], cwd=cwd,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    except FileNotFoundError as error:
        fail(f"{what}: cannot execute {error.filename!r}")
    if result.returncode:
        tail = result.stdout[-4000:] if result.stdout else ""
        fail(f"{what} failed (exit {result.returncode}):\n{tail}")
    return result.stdout


def tool(name, *extra):
    for candidate in extra:
        found = shutil.which(candidate)
        if found:
            return found
    found = shutil.which(name)
    if found:
        return found
    fail(f"required tool '{name}' not found on PATH")


# ---------------------------------------------------------------------------
# Mach-O helpers (no third-party modules, works for objects and kernelcaches)
# ---------------------------------------------------------------------------

def macho_commands(data, offset=0):
    magic, _cpu, _sub, _filetype, ncmds, _sizeofcmds, _flags, _res = struct.unpack_from("<8I", data, offset)
    if magic != MH_MAGIC_64:
        fail(f"not a 64-bit Mach-O ({magic:#x})")
    commands = []
    cursor = offset + 32
    for _ in range(ncmds):
        cmd, size = struct.unpack_from("<2I", data, cursor)
        commands.append((cmd, size, cursor))
        if size < 8:
            fail("corrupt load command size")
        cursor += size
    return commands


def macho_header(data, offset=0):
    magic, cpu, sub, filetype, ncmds, sizeofcmds, flags, _res = struct.unpack_from("<8I", data, offset)
    return dict(magic=magic, cputype=cpu, cpusubtype=sub, filetype=filetype,
                ncmds=ncmds, sizeofcmds=sizeofcmds, flags=flags)


def macho_sections(data, offset=0):
    sections = []
    for cmd, size, at in macho_commands(data, offset):
        if cmd != LC_SEGMENT_64:
            continue
        segname = data[at + 8:at + 24].rstrip(b"\0").decode("latin-1")
        vmaddr, vmsize, fileoff, filesize = struct.unpack_from("<4Q", data, at + 24)
        nsects = struct.unpack_from("<I", data, at + 64)[0]
        for i in range(nsects):
            sect = at + 72 + i * 80
            sections.append(dict(
                segname=segname,
                name=data[sect:sect + 16].rstrip(b"\0").decode("latin-1"),
                addr=struct.unpack_from("<Q", data, sect + 32)[0],
                size=struct.unpack_from("<Q", data, sect + 40)[0],
                fileoff=struct.unpack_from("<I", data, sect + 48)[0],
                flags=struct.unpack_from("<I", data, sect + 64)[0],
                seg_vmaddr=vmaddr, seg_vmsize=vmsize, seg_fileoff=fileoff, seg_filesize=filesize,
            ))
    return sections


def macho_symbols(data, offset=0):
    for cmd, size, at in macho_commands(data, offset):
        if cmd != LC_SYMTAB:
            continue
        symoff, nsyms, stroff, strsize = struct.unpack_from("<4I", data, at + 8)
        symbols = []
        for i in range(nsyms):
            n_strx, n_type, n_sect, _n_desc, n_value = struct.unpack_from("<IBBHQ", data, symoff + i * 16)
            if not n_strx or n_strx >= strsize:
                continue
            end = data.index(b"\0", stroff + n_strx)
            symbols.append(dict(name=data[stroff + n_strx:end].decode("latin-1"),
                                type=n_type, sect=n_sect, value=n_value))
        return symbols
    return []


def check_object_architecture(path, what):
    data = Path(path).read_bytes()
    header = macho_header(data)
    if header["cputype"] != ARM64_CPUTYPE or header["filetype"] != MH_OBJECT:
        fail(f"{what}: unexpected object architecture/type "
             f"(cputype={header['cputype']:#x} filetype={header['filetype']})")
    deployment = None
    for cmd, _size, at in macho_commands(data):
        if cmd == LC_VERSION_MIN_IPHONEOS:
            deployment = ("min",) + struct.unpack_from("<2I", data, at + 8)
        elif cmd == LC_BUILD_VERSION:
            platform, minos, _sdk, _ntools = struct.unpack_from("<4I", data, at + 8)
            deployment = (platform, minos, 0)
    if deployment is None:
        fail(f"{what}: no iOS deployment target load command")
    return header, deployment


# ---------------------------------------------------------------------------
# Compile-line replay
# ---------------------------------------------------------------------------

def load_recipe(root, recipe):
    path = Path(recipe) if recipe else root / DEFAULT_RECIPE
    if not path.is_absolute():
        path = root / path
    if not path.is_file():
        fail(f"XNU compile recipe not found: {path}\n"
             "  Run the kernel step once so the bootstrap pass writes "
             "IOPlatformExpert.cpo.json (see INTEGRATION.md, 'common failures').")
    text = path.read_text().strip()
    if text.endswith(","):
        text = text[:-1]
    record = json.loads(text)
    for key in ("arguments", "file", "directory"):
        if key not in record:
            fail(f"{path} has no '{key}' entry; not a clang .cpo.json replay record")
    if not Path(record["directory"]).is_dir():
        fail(f"the compile directory recorded in {path.name} does not exist: "
             f"{record['directory']}\n  Re-run the kernel step on this machine, or pass --recipe "
             "with a record produced by this build tree.")
    return path, record


def replay_compile(record, source, destination, extra_flags):
    arguments = record["arguments"]
    command = []
    index = 0
    while index < len(arguments):
        value = arguments[index]
        if value == record["file"]:
            command.append(str(source))
        elif value == "-o":
            command.extend(["-o", str(destination)])
            index += 1
        elif value == "-Xclang" and index + 1 < len(arguments) and arguments[index + 1].startswith("-W"):
            index += 1
        elif value.startswith("-W"):
            # The recipe's warning flags are replayed from the XNU build; we add
            # our own below so an older Apple clang cannot fail on an unknown -W.
            pass
        else:
            command.append(value)
        index += 1
    command.extend(extra_flags)
    return command


def compile_source(source, destination, record, extra_flags, log_path):
    command = replay_compile(record, source, destination, extra_flags)
    Path(destination).parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(json.dumps(command, indent=2) + "\n")
    try:
        output = run(command, f"compile {Path(source).name}", cwd=record["directory"])
    except BuildError:
        raise
    if output.strip():
        note(f"{Path(source).name}: {output.strip().splitlines()[-1]}")
    return command


# ---------------------------------------------------------------------------
# Bindings, late object, archive
# ---------------------------------------------------------------------------

def write_bindings_assembly(path, bindings):
    lines = ["# SPDX-License-Identifier: BSD-2-Clause-Patent",
             "# Absolute bindings to the ORIGINAL IOMobileGraphicsFamily binary.",
             "# Generated by scripts/build-native-mobile-display.py; do not edit.",
             "# The original kext is not rebuilt or replaced: its constructor,",
             "# destructor and metaclass object keep their original addresses.",
             "\t.text"]
    for name, value in bindings.items():
        lines.append(f"\t.globl {name}")
        lines.append(f"\t.set {name}, {value:#x}")
    lines.append("")
    Path(path).write_text("\n".join(lines))


def detect_init_symbol(object_path, wanted):
    data = Path(object_path).read_bytes()
    symbols = macho_symbols(data)
    section_names = {s["name"] for s in macho_sections(data)}
    defined = {s["name"] for s in symbols if (s["type"] & N_TYPE) == N_SECT and not (s["type"] & N_STAB)}
    if wanted in defined:
        return wanted, True
    candidates = sorted(n for n in defined if n.startswith("__GLOBAL__sub_I"))
    if candidates:
        return candidates[0], False
    has_registration = any(name == MOD_INIT_SECTION[1] for name in section_names)
    return None, has_registration


def objcopy_tool(explicit):
    candidates = []
    if explicit:
        candidates.append(explicit)
    found = shutil.which("llvm-objcopy")
    if found:
        candidates.append(found)
    if shutil.which("xcrun"):
        result = subprocess.run(["xcrun", "--find", "llvm-objcopy"],
                                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
        if result.returncode == 0 and result.stdout.strip():
            candidates.append(result.stdout.strip())
    if shutil.which("brew"):
        result = subprocess.run(["brew", "--prefix", "llvm"],
                                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
        if result.returncode == 0:
            candidates.append(str(Path(result.stdout.strip()) / "bin" / "llvm-objcopy"))
    for candidate in candidates:
        if candidate and Path(candidate).is_file() and os.access(candidate, os.X_OK):
            return candidate
    fail("llvm-objcopy not found; install LLVM (brew install llvm) or pass --llvm-objcopy")


def make_late_object(objcopy, source_object, late_object, init_symbol):
    data = Path(source_object).read_bytes()
    sections = macho_sections(data)
    if not any(s["segname"] == MOD_INIT_SECTION[0] and s["name"] == MOD_INIT_SECTION[1] for s in sections):
        fail(f"{Path(source_object).name}: no __DATA,__mod_init_func section; the own "
             "constructor was not registered, the archive would never initialise the class")
    command = [objcopy,
               f"--remove-section={MOD_INIT_SECTION[0]},{MOD_INIT_SECTION[1]}",
               f"--globalize-symbol={init_symbol}",
               str(source_object), str(late_object)]
    run(command, "llvm-objcopy (late object)")

    late = Path(late_object).read_bytes()
    late_sections = macho_sections(late)
    if any(s["segname"] == MOD_INIT_SECTION[0] and s["name"] == MOD_INIT_SECTION[1] for s in late_sections):
        fail(f"{Path(late_object).name}: __DATA,__mod_init_func survived llvm-objcopy")
    before = {(s["segname"], s["name"]): data[s["fileoff"]:s["fileoff"] + s["size"]]
              for s in sections if s["segname"] == "__TEXT"}
    after = {(s["segname"], s["name"]): late[s["fileoff"]:s["fileoff"] + s["size"]]
             for s in late_sections if s["segname"] == "__TEXT"}
    for key, value in before.items():
        if key in after and after[key] != value:
            fail(f"{Path(late_object).name}: __TEXT,{key[1]} changed; only the initializer "
                 "registration may be deferred")
    names = {s["name"] for s in macho_symbols(late)}
    if init_symbol not in names:
        fail(f"{Path(late_object).name}: globalized {init_symbol} missing")
    return command


def pack_archive(ar, members, archive, epoch):
    archive.unlink(missing_ok=True)
    for member in members:
        if not Path(member).is_file():
            fail(f"archive member missing: {member}")
        os.utime(member, (epoch, epoch))
    run([ar, "rcs", archive, *members], "ar (archive)")
    if not Path(archive).is_file() or Path(archive).stat().st_size == 0:
        fail(f"ar produced no archive at {archive}")
    return sha256(archive)


# ---------------------------------------------------------------------------
# Optional verification against a kernelcache
# ---------------------------------------------------------------------------

def containing_section(sections, va):
    for section in sections:
        if section["seg_vmaddr"] <= va < section["seg_vmaddr"] + section["seg_vmsize"]:
            return section
    return None


# Segments that can never hold a function; landing there is a hard contradiction.
CODE_IMPOSSIBLE_SEGMENTS = ("__DATA", "__DATA_CONST", "__PRELINK_DATA", "__PLK_DATA_CONST",
                            "__LASTDATA_CONST", "__LINKEDIT", "__LINKINFO", "__PRELINK_INFO")
# Segments that hold code in the layouts we know (the prelink may put kext code in
# __PRELINK_TEXT on some builds, so a miss here is only a warning).
CODE_SEGMENTS = ("__TEXT_EXEC", "__PLK_TEXT_EXEC", "__PRELINK_TEXT", "__TEXT")


def verify_bindings(kernelcache, bindings):
    data = Path(kernelcache).read_bytes()
    if len(data) >= 8:
        magic_be = struct.unpack_from(">I", data, 0)[0]
        if magic_be == 0xCAFE_BABE:
            nfat = struct.unpack_from(">I", data, 4)[0]
            offset = 8
            for _ in range(nfat):
                cpu, _sub, off, _size, _align = struct.unpack_from(">5I", data, offset)
                if cpu == ARM64_CPUTYPE:
                    data = data[off:]
                    break
                offset += 20
    sections = macho_sections(data)
    symbols = {s["name"]: s["value"] for s in macho_symbols(data)
               if (s["type"] & N_TYPE) == N_SECT and not (s["type"] & N_STAB)}
    results = {}
    ok = True
    for name, value in bindings.items():
        section = containing_section(sections, value)
        segment = section["segname"] if section else None
        instructions = bool(section) and (
            bool(section["flags"] & (S_ATTR_PURE_INSTRUCTIONS | S_ATTR_SOME_INSTRUCTIONS))
            or segment in ("__TEXT_EXEC", "__PLK_TEXT_EXEC"))
        entry = dict(value=hex(value),
                     section=None if not section else f"{segment},{section['name']}",
                     segment=segment, instructions=instructions)
        wants_code = name != "__ZN19IOMobileFramebuffer10gMetaClassE"
        entry["expects_code"] = wants_code
        if name in symbols:
            entry["symbol_table_value"] = hex(symbols[name])
            entry["symbol_table_match"] = symbols[name] == value
        if section is None:
            entry["verdict"] = "contradiction"
            entry["reason"] = "address is not inside any mapped segment"
        elif wants_code and segment in CODE_IMPOSSIBLE_SEGMENTS:
            entry["verdict"] = "contradiction"
            entry["reason"] = f"function address lands in data segment {segment}"
        elif not wants_code and instructions:
            entry["verdict"] = "contradiction"
            entry["reason"] = f"metaclass object address lands in executable section {entry['section']}"
        elif entry.get("symbol_table_match") is False:
            entry["verdict"] = "contradiction"
            entry["reason"] = "the image's own symbol table has a different address"
        elif wants_code and not instructions:
            entry["verdict"] = "warning"
            entry["reason"] = f"function address lands in non-executable section {entry['section']}"
        else:
            entry["verdict"] = "ok"
        ok = ok and entry["verdict"] != "contradiction"
        results[name] = entry
    return dict(kernelcache=str(kernelcache), kernelcache_sha256=sha256(kernelcache),
                symbols_in_symtab=len(symbols), ok=ok,
                contradictions=[n for n, e in results.items() if e["verdict"] == "contradiction"],
                warnings=[n for n, e in results.items() if e["verdict"] == "warning"],
                entries=results)


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def discover(root, explicit, candidates, what):
    if explicit:
        path = Path(explicit)
        path = path if path.is_absolute() else (root / path)
        if not path.is_file():
            fail(f"{what} not found: {path}")
        return path
    for candidate in candidates:
        path = root / candidate
        if path.is_file():
            return path
    fail(f"{what} not found under {root}; tried: " + ", ".join(candidates))


def main(argv):
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", default=None,
                        help="repository root (default: parent of this script's directory)")
    parser.add_argument("--recipe", default=None, help=f"clang replay record (default: {DEFAULT_RECIPE})")
    parser.add_argument("--driver-source", default=None,
                        help="default: drivers/NativeMobileDisplay/NativeMobileDisplay.cpp")
    parser.add_argument("--probe-source", default=None,
                        help="default: package/MobileDisplayProviderProbe.cpp (then kits/*/)")
    parser.add_argument("--out", default=None, help="default: <root>/build/native-mobile-display")
    parser.add_argument("--layout", choices=("format1", "format2", "both"), default="format1",
                        help="format1: build/native-mobile-display/libNativeMobileDisplay.late.a; "
                             "format2: build/gop-framebuffer/libGopFramebuffer.late.a (components.toml rename)")
    parser.add_argument("--bindings", default=None,
                        help="JSON file {symbol: address} overriding the fixed 21H461 values")
    parser.add_argument("--kernelcache", default=None,
                        help="optional: verify the fixed bindings against this kernelcache image")
    parser.add_argument("--require-verified-bindings", action="store_true",
                        help="fail unless --kernelcache verification passed (use in CI)")
    parser.add_argument("--allow-failed-verification", action="store_true",
                        help="triage only: build even if --kernelcache rejects the bindings")
    parser.add_argument("--no-werror", action="store_true",
                        help="drop -Werror (older/newer Apple clang rejecting a -Wno-* option)")
    parser.add_argument("--init-mode", choices=("defer", "mod-init"), default="defer",
                        help="defer: remove __mod_init_func and call the globalized initializer "
                             "from the probe (default); mod-init: keep it (fallback)")
    parser.add_argument("--init-symbol", default=None,
                        help="override the detected __GLOBAL__sub_I_* symbol name")
    parser.add_argument("--llvm-objcopy", default=None, help="explicit llvm-objcopy path")
    parser.add_argument("--ar", default=None, help="explicit ar path (default: xcrun ar)")
    parser.add_argument("--clang", default=None, help="explicit clang path (default: xcrun clang)")
    parser.add_argument("--source-date-epoch", type=int, default=None,
                        help="timestamp stamped into archive members (default: 0 for repeatability)")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve() if args.root else Path(__file__).resolve().parents[1]
    if not root.is_dir():
        fail(f"repository root does not exist: {root}")

    driver = discover(root, args.driver_source,
                      ["drivers/NativeMobileDisplay/NativeMobileDisplay.cpp"], "driver source")
    probe = discover(root, args.probe_source,
                     ["package/MobileDisplayProviderProbe.cpp",
                      f"kits/{root.name}/MobileDisplayProviderProbe.cpp",
                      "drivers/NativeMobileDisplay/MobileDisplayProviderProbe.cpp"], "probe source")
    abi = driver.with_name("OriginalMobileFramebufferABI.h")
    if not abi.is_file():
        fail(f"vendored ABI header missing next to the driver: {abi}\n"
             "  The 21H461 header is required; without it IOMobileFramebuffer's 262-entry "
             "vtable layout is unknown.")

    recipe_path, record = load_recipe(root, args.recipe)
    out = Path(args.out) if args.out else root / "build/native-mobile-display"
    out = out if out.is_absolute() else root / out
    out.mkdir(parents=True, exist_ok=True)

    bindings = dict(DEFAULT_BINDINGS)
    if args.bindings:
        loaded = json.loads(Path(args.bindings).read_text())
        bindings = {str(k): int(v, 0) if isinstance(v, str) else int(v) for k, v in loaded.items()}

    xcrun = shutil.which("xcrun")
    if not xcrun:
        fail("xcrun not found: this builder needs macOS with Xcode command line tools")
    sdk = run([xcrun, "--sdk", "iphoneos", "--show-sdk-path"], "xcrun --show-sdk-path").strip()
    clang = [args.clang] if args.clang else [xcrun, "clang"]
    ar = args.ar or (str(Path(xcrun).with_name("ar")) if Path(xcrun).with_name("ar").is_file() else "ar")
    if not Path(ar).is_file():
        ar = tool("ar")
    epoch = args.source_date_epoch if args.source_date_epoch is not None else 0

    note(f"root      {root}")
    note(f"driver    {rel(driver, root)}")
    note(f"probe     {rel(probe, root)}")
    note(f"recipe    {rel(recipe_path, root)}")
    note(f"output    {rel(out, root)}")

    # 1. compile --------------------------------------------------------------
    warnings = ["-Wall", "-Wextra", "-Werror", "-Wno-unused-parameter",
                "-Wno-c99-designator", "-Wno-reorder-init-list",
                "-Wno-deprecated-enum-enum-conversion",
                "-Wno-unnecessary-virtual-specifier"]
    if args.no_werror:
        warnings.remove("-Werror")
        note("note: -Werror disabled by --no-werror")
    includes = ["-I", str(driver.parent)]
    osfmk = root / ".cache/xnu-work/osfmk"
    if osfmk.is_dir():
        includes += ["-I", str(osfmk)]
    else:
        note("note: .cache/xnu-work/osfmk not present; relying on the recipe's include paths")

    driver_object = out / "NativeMobileDisplay.o"
    compile_source(driver, driver_object, record, warnings + includes, out / "compile-command.json")
    header, deployment = check_object_architecture(driver_object, driver_object.name)
    note(f"driver object {driver_object.stat().st_size} B, deployment {deployment}")

    # 2. bindings -------------------------------------------------------------
    assembly = out / "original-bindings.S"
    write_bindings_assembly(assembly, bindings)
    bindings_object = out / "original-bindings.o"
    run(clang + ["-target", "arm64-apple-ios17.0", "-isysroot", sdk, "-Werror",
                 "-c", str(assembly), "-o", str(bindings_object)], "assemble original-bindings.S")
    check_object_architecture(bindings_object, bindings_object.name)

    # 3. init symbol + late object -------------------------------------------
    init_symbol = args.init_symbol
    detected = True
    if not init_symbol:
        init_symbol, detected = detect_init_symbol(driver_object, DEFAULT_INIT_SYMBOL)
        if init_symbol is None:
            if args.init_mode == "defer":
                note("warning: no __GLOBAL__sub_I_* symbol in the driver object; "
                     "falling back to --init-mode mod-init")
                args.init_mode = "mod-init"
            init_symbol = DEFAULT_INIT_SYMBOL
            detected = False
    if not detected and args.init_mode == "defer":
        note(f"warning: clang emitted {init_symbol!r} instead of {DEFAULT_INIT_SYMBOL!r}; "
             "the probe is compiled with that name")

    late_object = out / "NativeMobileDisplay.late.o"
    late_command = None
    if args.init_mode == "defer":
        late_command = make_late_object(objcopy_tool(args.llvm_objcopy),
                                        driver_object, late_object, init_symbol)
        archive_driver = late_object
    else:
        note("init-mode mod-init: keeping __DATA,__mod_init_func (kernel C++ init runs the "
             "constructor; see INTEGRATION.md 'init order')")
        archive_driver = driver_object

    # 4. probe ---------------------------------------------------------------
    probe_object = out / "MobileDisplayProviderProbe.o"
    probe_flags = list(warnings) + includes + [
        f"-DNATIVE_MOBILE_DISPLAY_DEFER_INIT={1 if args.init_mode == 'defer' else 0}",
        f'-DNATIVE_MOBILE_DISPLAY_INIT_SYMBOL="{init_symbol}"',
    ]
    compile_source(probe, probe_object, record, probe_flags, out / "compile-command-probe.json")
    check_object_architecture(probe_object, probe_object.name)
    probe_symbols = {s["name"] for s in macho_symbols(Path(probe_object).read_bytes())}
    # The kernel patch calls the probe from inside `extern "C" { ... }`
    # (iokit/Kernel/IOUserClient.cpp), so the object must export the C name.
    c_probe = "_native_mobile_display_provider_probe"
    mangled = sorted(n for n in probe_symbols
                     if "native_mobile_display_provider_probe" in n and n != c_probe)
    if c_probe not in probe_symbols:
        fail(f"the probe object does not export {c_probe}; the kernel patch calls it with C "
             f"linkage and would not link (found: {mangled or 'nothing similar'})")
    if mangled:
        fail(f"the probe also exports a C++-mangled name {mangled[0]}; keep the "
             'extern "C" block')
    if args.init_mode == "defer" and init_symbol not in probe_symbols:
        # Undefined reference is expected and wanted here: it is resolved by late.o.
        note(f"probe references {init_symbol} (resolved by the late object)")

    # 5. verification --------------------------------------------------------
    verification = None
    if args.kernelcache:
        verification = verify_bindings(args.kernelcache, bindings)
        note(f"bindings verification: {'PASS' if verification['ok'] else 'FAIL'} "
             f"({rel(args.kernelcache, root)})")
        for name, entry in verification["entries"].items():
            note(f"  {name} = {entry['value']} section={entry['section']} "
                 f"verdict={entry['verdict']}"
                 + (f" ({entry['reason']})" if entry.get("reason") else ""))
        if not verification["ok"]:
            message = ("the fixed bindings do not belong to this kernelcache: a wrong "
                       "IOMobileFramebuffer metaclass pointer panics inside "
                       "OSMetaClass::postModLoad. Re-derive the values before linking.")
            if not args.allow_failed_verification:
                fail(message + " (--allow-failed-verification overrides for triage only)")
            note("warning: " + message)
    elif args.require_verified_bindings:
        fail("--require-verified-bindings needs --kernelcache")
    else:
        note("warning: bindings not verified (no --kernelcache given); "
             "build-report.json records bindings_verified=false")

    # 6. archive + report ----------------------------------------------------
    members = [archive_driver, bindings_object, probe_object]
    archive = out / "libNativeMobileDisplay.late.a"
    archive_sha = pack_archive(ar, members, archive, epoch)

    sources = [driver, abi, probe, assembly]
    report = dict(
        schema=1,
        component="NativeMobileDisplay",
        archive=str(rel(archive, root)),
        archive_sha256=archive_sha,
        archive_bytes=archive.stat().st_size,
        archive_members=[m.name for m in members],
        source_sha256={rel(path, root): sha256(path) for path in sources},
        bindings={name: hex(value) for name, value in bindings.items()},
        bindings_origin=BINDINGS_ORIGIN,
        bindings_verified=bool(verification and verification["ok"]),
        verification=verification,
        init_mode=args.init_mode,
        init_symbol=init_symbol,
        init_symbol_detected=detected,
        objcopy_command=late_command,
        objects={path.name: dict(sha256=sha256(path), bytes=path.stat().st_size) for path in members},
        deployment=deployment,
        recipe=rel(recipe_path, root),
        recipe_sha256=sha256(recipe_path),
        builder=rel(Path(__file__), root),
        builder_sha256=sha256(Path(__file__)),
        built_by="scripts/build-native-mobile-display.py",
        source_date_epoch=epoch,
        original_code_modified=False,
        display_published=False,
        runtime_qualified=False,
    )
    (out / "build-report.json").write_text(json.dumps(report, indent=2) + "\n")

    if args.layout in ("format2", "both"):
        alternate = root / "build/gop-framebuffer"
        alternate.mkdir(parents=True, exist_ok=True)
        alternate_archive = alternate / "libGopFramebuffer.late.a"
        shutil.copyfile(archive, alternate_archive)
        os.utime(alternate_archive, (epoch, epoch))
        alternate_report = dict(report)
        alternate_report["archive"] = rel(alternate_archive, root)
        alternate_report["archive_sha256"] = sha256(alternate_archive)
        alternate_report["alias_of"] = report["archive"]
        (alternate / "build-report.json").write_text(json.dumps(alternate_report, indent=2) + "\n")
        note(f"format-2 alias {rel(alternate_archive, root)}")

    note(f"archive   {rel(archive, root)}  sha256 {archive_sha}")
    note("done (own provider archive only; the original kext is untouched)")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except BuildError as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        sys.exit(130)
