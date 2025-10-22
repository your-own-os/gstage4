#!/usr/bin/env python3

import os
import sys
import re
import errno
import shutil
import signal
import argparse
import tempfile
import contextlib
import subprocess
from pathlib import Path
from typing import List, Optional, Tuple

PROGRAM = Path(__file__).name

DEFERRED_SIGNAL = ""
PID = os.getpid()
TEMPFILES = []

# Unset BASH_ENV for security reasons
os.environ.pop("BASH_ENV", None)

# Prevent the --verbose option of localedef from being implicitly enabled
os.environ.pop("POSIXLY_CORRECT", None)

# Protect against the inheritance of an unduly restrictive umask
os.umask(0o022)


def main():
    try:
        # Determine the locale directory, as reported by localedef
        locale_dir = get_locale_dir()

        # Infer the path of a Gentoo Prefix environment, if any
        gentoo_prefix = ""
        if locale_dir:
            gentoo_prefix = detect_gentoo_prefix(locale_dir)
            if gentoo_prefix:
                locale_dir = locale_dir.replace(gentoo_prefix, "", 1)

        # Parse command line arguments
        args = parse_args()
        prefix = args.prefix or gentoo_prefix

        # Ensure that locale/charmap files are opened relative to the prefix
        os.environ["I18NPATH"] = str(Path(prefix) / "usr" / "share" / "i18n")

        # Collect the locales that are being requested for installation
        config_file = os.path.join(prefix, "usr", "share", "i18n", "SUPPORTED")
        locales = read_config(config_file)

        # If a non-actionable update was requested, proceed no further
        if not locales:
            print("All of the requested locales are presently installed.")
            return

        # Create a temporary directory and switch to it
        tempdir = enter_tempdir(prefix)
        TEMPFILES.append(tempdir)

        # Compile the selected locales
        generate_locales(args.jobs, locales)

        # Determine the eventual destination path of the archive
        dst_path = Path(prefix) / locale_dir / "locale-archive"
        if dst_path.exists():
            die(f"The locale archive already exists at '{dst_path}'.")

        # Integrate the compiled locales into a new locale archive
        size = generate_archive([loc[2] for loc in locales], dst_path)
        total = len(locales)
        size_mb = round(size / 2**20, 2)
        plural_s = "s" if total != 1 else ""
        print(f"Successfully installed an archive containing {total} locale{plural_s}, of {size_mb} MiB in size.")

    except Exception as e:
        die(str(e))


def get_locale_dir():
    result = subprocess.check_output(["localedef", "--help"], text=True, env={"LC_ALL": "C"})
    match = re.search(r"locale path\s*:\s+(/[^:\s]+)", result)
    return os.path.normpath(match.group(1))


def detect_gentoo_prefix(path: str) -> str:
    """Detect Gentoo Prefix environment."""
    if not path.endswith("/usr/lib/locale"):
        die(f"Can't handle unexpected locale directory of '{path}'")

    prefix = path[:-len("/usr/lib/locale")]
    if prefix and (Path(prefix) / "etc" / "gentoo-release").exists():
        return prefix
    return ""


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        prog=PROGRAM,
        description="Generate glibc locale archives from templates",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=False
    )

    parser.add_argument(
        "--jobs", "-j",
        type=int,
        help="Maximum number of localedef instances to run in parallel"
    )
    parser.add_argument(
        "--prefix", "-p",
        help="The prefix of the root filesystem"
    )

    args = parser.parse_args()

    if args.prefix and not args.prefix.startswith("/"):
        die("The --prefix option must specify either a null string or an absolute path")

    # Set default jobs
    if not args.jobs or args.jobs < 1:
        args.jobs = get_nprocs() or 1

    return args


def normalize(canonical: str) -> str:
    """Normalize locale name."""
    # Similar to the normalize_codeset() function of localedef
    match = re.search(r"(?<=\.)[^@]+", canonical)
    if not match:
        die(f"Can't normalize {canonical}")

    # en_US.UTF-8 => en_US.utf8
    # de_DE.ISO-8859-15@euro => de_DE.iso885915@euro
    codeset = re.sub(r"[^0-9A-Za-z]", "", match.group().lower())
    return canonical[:match.start()] + codeset + canonical[match.end():]


# Parse locale configuration file
def read_config(path):
    locales = []

    with open(path) as f:
        for line_num, line in enumerate(f, 1):
            line = line.rstrip("\n")

            # Skip comments and blank lines
            if re.match(r"^\s*($|#)", line):
                continue

            # Permit comments trailing locale declarations
            line = re.sub(r"\s#\s.*", "", line)

            # Expect two fields, separated by whitespace
            fields = line.strip().split()
            if len(fields) != 2:
                throw_config_error("Malformed locale declaration", path, line_num, line)

            # Parse locale entry
            locale, codeset, charmap, canonical = parse_entry(fields[0], fields[1])
            if codeset and codeset != charmap:
                throw_config_error("Mismatching codeset/charmap", path, line_num, line)

            locales.append([locale, charmap, canonical])

    if len(locales) == 0:
        die(f"No locale declarations were found within {path}")

    if ["C", "UTF-8", "C.UTF-8"] not in locales:
        die(f"The C.UTF-8 locale must be present in {path}")

    return locales


def parse_entry(locale: str, charmap: str) -> Tuple[str, Optional[str], str, str]:
    """Parse a locale configuration entry."""
    canonical = ""
    codeset = None

    if "@" in locale:
        # de_DE@euro ISO-8859-15 => de_DE.ISO-8859-15@euro
        parts = locale.split("@", 1)
        canonical = f"{parts[0]}.{charmap}@{parts[1]}"
    elif "." in locale:
        # en_US.UTF-8 UTF-8 => en_US.UTF-8
        parts = locale.split(".", 1)
        locale, codeset = parts[0], parts[1]
        canonical = f"{locale}.{codeset}"
    else:
        # en_US ISO-8859-1 => en_US.ISO-8859-1
        canonical = f"{locale}.{charmap}"

    return locale, codeset, charmap, canonical


def throw_config_error(error: str, path: str, line_num: int, line: str):
    """Throw a configuration error."""
    die(f"{error} at {path}[{line_num}]: {line}")


def enter_tempdir(prefix: str) -> str:
    """Create and enter a temporary directory."""
    # Prefer /var/tmp to avoid memory pressure
    base_dir = Path(prefix) / "var" / "tmp"
    if not base_dir.exists():
        base_dir = Path(tempfile.gettempdir())

    tempdir = tempfile.mkdtemp(prefix="locale-gen.", dir=base_dir)
    os.chdir(tempdir)
    return tempdir


def generate_locales(workers: int, locales: List[List[str]]):
    """Generate locales in parallel."""
    # Set up signal handling
    def signal_handler(signum, frame):
        global DEFERRED_SIGNAL
        DEFERRED_SIGNAL = signum

    original_int = signal.signal(signal.SIGINT, signal_handler)
    original_term = signal.signal(signal.SIGTERM, signal_handler)

    try:
        total = len(locales)
        if total < workers:
            workers = total

        plural_s1 = "s" if total != 1 else ""
        plural_s2 = "s" if workers != 1 else ""
        print(f"Compiling {total} locale{plural_s1} with {workers} worker{plural_s2} ...")

        num_width = len(str(total))
        processes = {}

        for i, (locale, charmap, canonical) in enumerate(locales):
            # Limit concurrent workers
            if i >= workers:
                pid, status = os.wait()
                if status != 0:
                    processes[pid] = status
                    break

            print(f"[{i+1:>{num_width}}/{total}] Compiling locale: {canonical}")

            # Fork and compile locale
            pid = os.fork()
            if pid == 0:
                # Child process
                signal.signal(signal.SIGINT, signal.SIG_DFL)
                signal.signal(signal.SIGTERM, signal.SIG_DFL)
                compile_locale(locale, charmap, canonical)
            elif pid > 0:
                processes[pid] = None
            else:
                print("Can't fork", file=sys.stderr)
                break

            if DEFERRED_SIGNAL:
                break

        # Reap remaining processes
        if workers > 1:
            print("Waiting for active workers to finish their jobs ...")

        while True:
            try:
                pid, status = os.wait()
                processes[pid] = status
            except ChildProcessError:
                break

        # Check for errors
        for status in processes.values():
            if status and status != 0:
                throw_child_error("localedef", status)

        if DEFERRED_SIGNAL:
            # Signal will be handled in cleanup
            sys.exit(1)

        if len(processes) != total:
            die("Aborting because not all of the selected locales were compiled")

    finally:
        # Restore signal handlers
        signal.signal(signal.SIGINT, original_int)
        signal.signal(signal.SIGTERM, original_term)


def compile_locale(locale: str, charmap: str, canonical: str):
    """Compile a single locale."""
    output_dir = f"./{canonical}"
    run(["localedef", "--no-archive", "-i", locale, "-f", charmap, "--", output_dir])


def generate_archive(canonicals: List[str], dst_path) -> Path:
    """Generate the locale archive."""
    # Create output directory
    output_dir = os.path.dirname(dst_path)
    os.makedirs(output_dir, exist_ok=True)

    # Add locales to archive
    cmd = ["localedef", "--prefix", ".", "--quiet", "--add-to-archive", "--"] + canonicals
    result = run(cmd, capture_output=True, text=True)

    # Check for errors in stderr
    if result.stderr:
        print(result.stderr, file=sys.stderr)
        # If anything was printed to stderr, treat as error
        if result.stderr.strip():
            throw_child_error("localedef", 1)

    return dst_path.stat().st_size


# Install the new locale archive
def install_archive(src_path: Path, dst_path: Path) -> int:
    # Move to interim location
    interim_path = dst_path.with_name(f"{dst_path.name}.{PID}")
    shutil.move(src_path, interim_path)
    TEMPFILES.append(interim_path)

    # Atomically replace
    interim_path.replace(dst_path)

    # Return file size
    return dst_path.stat().st_size


def get_nprocs() -> int:
    """Get number of processors."""
    try:
        # Try nproc first
        result = subprocess.run(["nproc"], capture_output=True, text=True)
        if result.returncode == 0:
            return int(result.stdout.strip())

        # Try getconf
        result = subprocess.run(["getconf", "_NPROCESSORS_CONF"], capture_output=True, text=True)
        if result.returncode == 0:
            return int(result.stdout.strip())
    except (OSError, subprocess.SubprocessError, ValueError):
        pass

    return 1


def run(cmd, **kwargs):
    """Run a command with error handling."""
    if os.getpid() == PID:
        # Parent process
        result = subprocess.run(cmd, **kwargs)
        if result.returncode != 0:
            throw_child_error(cmd[0] if isinstance(cmd, list) else cmd, result.returncode)
        return result
    else:
        # Child process - use exec
        if isinstance(cmd, str):
            os.execlp(cmd, cmd)
        else:
            os.execvp(cmd[0], cmd)
        # exec never returns, but if it fails:
        sys.exit(126 if errno.ENOENT else 127)


def throw_child_error(cmd: str, status: int = None):
    """Handle child process errors."""
    if status is None:
        status = os.getpid()  # This would need proper status handling

    if status == -1:
        sys.exit(1)
    elif status != 0:
        if status & 0x7F:
            fate = "interrupted by a signal"
        else:
            fate = "unsuccessful"
        die(f"Aborting because the execution of '{cmd}' was {fate}")


def die(message: str):
    """Print error message and exit."""
    print(f"{PROGRAM}: {message}", file=sys.stderr)
    sys.exit(1)


def cleanup():
    """Cleanup temporary files and handle signals."""
    if os.getpid() == PID:
        # Cleanup temporary files
        for t in TEMPFILES:
            if os.path.exists(t):
                if os.path.isdir(t):
                    shutil.rmtree(t, ignore_errors=True)
                else:
                    with contextlib.suppress(OSError):
                        os.unlink(t)

        # Handle deferred signals
        if DEFERRED_SIGNAL:
            os.kill(os.getpid(), DEFERRED_SIGNAL)


if __name__ == "__main__":
    try:
        main()
    finally:
        cleanup()
