"""
Utilities for invoking ScanCode and collecting license expressions.

Description:
    Provides helpers to run a single ScanCode invocation or to efficiently
    process very large projects by splitting work across subdirectories, while
    merging results into a unified license map keyed by project-relative labels
    like "//path/to/file".
"""

import sys
import json
import locale
import shutil

import threading
import subprocess
import tempfile
from pathlib import Path
from typing import Iterable, Sequence

LicenseMap = dict[str, str]

__all__ = [
    "detect_license",
    "detect_license_chunked",
    "LicenseMap",
    "ScancodeExecutionError",
]


class ScancodeExecutionError(RuntimeError):
    """Raised when scancode execution fails."""


def _normalize_label(raw_path: str, root: Path, *, base: Path | None = None) -> str:
    """Normalize a ScanCode path to a project-relative label.

    Args:
        raw_path: Path reported by ScanCode (e.g., from_file/path).
        root: Project root to which labels must be relative.
        base: Optional scan base used when the reported path is relative to a
            sub-scan root; helps unify mixed absolute/relative outputs.

    Returns:
        Normalized label like ``//dir/file.ext``.
    """
    path_obj = Path(raw_path)

    # If the path is relative and a scan base is provided, anchor it first
    if base is not None and not path_obj.is_absolute():
        try:
            path_obj = (base / path_obj).resolve()
        except Exception:
            # Fall back to as-is on any resolution issue
            path_obj = base / path_obj

    if path_obj.is_absolute():
        try:
            rel = path_obj.resolve().relative_to(root)
        except ValueError:
            parts = path_obj.parts[1:] or (path_obj.name,)
            rel = Path(*parts)
    else:
        rel = path_obj
        parts = rel.parts
        if parts and parts[0] == root.name:
            rel = Path(*parts[1:]) if len(parts) > 1 else Path(parts[-1])

    rel_str = rel.as_posix()
    if not rel_str or rel_str == ".":
        rel_str = path_obj.name or root.name

    return f"//{rel_str}"


def _collect_license_map(
    payload: dict, root: Path, *, base: Path | None = None
) -> LicenseMap:
    """Build a ``{label: spdx_expression}`` mapping from ScanCode JSON.

    Args:
        payload: Parsed ScanCode JSON (``--json-pp`` output).
        root: Project root used to normalize labels.
        base: Optional scan base to anchor relative file paths.

    Returns:
        A license map with project-relative labels as keys and SPDX expressions
        as values.
    """
    license_map: LicenseMap = {}

    for detection in payload.get("license_detections", []) or []:
        for match in detection.get("reference_matches", []) or []:
            file_hint = match.get("from_file")
            expr = match.get("license_expression_spdx")
            if not file_hint or not expr:
                continue
            license_map[_normalize_label(file_hint, root, base=base)] = expr

    for entry in payload.get("files", []) or []:
        expr = entry.get("detected_license_expression_spdx")
        file_hint = entry.get("path")
        if not expr or not file_hint:
            continue
        license_map[_normalize_label(file_hint, root, base=base)] = expr

    return license_map


def detect_license(
    target: str | Path,
    *,
    scancode_cmd: str = "scancode",
    extra_args: Iterable[str] | None = None,
) -> LicenseMap:
    """Run ScanCode on a target and return a license map.

    Description:
        Invokes ScanCode once for a single file or directory and converts the
        results into a ``{label: spdx_expression}`` mapping with labels
        normalized relative to the scan root.

    Args:
        target: File or directory to scan.
        scancode_cmd: Executable name or path of ``scancode``.
        extra_args: Additional ScanCode CLI arguments to append.

    Returns:
        Mapping from normalized labels (``//relative/path``) to SPDX license
        expressions reported by ScanCode.

    Raises:
        FileNotFoundError: If ``scancode`` or ``target`` is not found.
        ScancodeExecutionError: If ScanCode fails or JSON parsing fails.
    """
    executable = _resolve_scancode_executable(scancode_cmd)

    target_path = Path(target).expanduser().resolve()
    if not target_path.exists():
        raise FileNotFoundError(f"Target path not found: {target_path}")

    scan_root = target_path if target_path.is_dir() else target_path.parent

    data = _invoke_scancode(executable, [target_path], extra_args)
    return _collect_license_map(data, scan_root, base=scan_root)


def detect_license_chunked(
    target: str | Path,
    *,
    # How many immediate subdirectories must a folder have before recursing
    # into each child instead of scanning the folder as a whole.
    split_threshold: int = 1024,
    # How many files from the same directory to scan per scancode invocation.
    chunk_file_count: int = 128,
    scancode_cmd: str = "scancode",
    extra_args: Iterable[str] | None = None,
) -> LicenseMap:
    """Run ScanCode on large directories by splitting work across subfolders.

    Description:
        Applies a soft split strategy to handle very large projects. It scans
        top-level files in batches, then for each directory decides to scan as a
        whole or recurse into children based on the number of immediate
        subdirectories. Mixed file/directory batches are normalized back to the
        same project-relative label space.

    Args:
        target: Project root directory (or a single file) to scan.
        split_threshold: Recurse into each child if a directory has this many
            or more immediate subdirectories; scan as a whole otherwise.
        chunk_file_count: Number of direct files to include per ScanCode call.
        scancode_cmd: Executable name or path of ``scancode``.
        extra_args: Additional ScanCode CLI arguments to append.

    Returns:
        A license map of ``{label: spdx_expression}``, where labels are
        ``//``-prefixed paths relative to ``target``.

    Raises:
        FileNotFoundError: If ``scancode`` or ``target`` is not found.
        ScancodeExecutionError: If ScanCode fails or JSON parsing fails.
    """

    executable = _resolve_scancode_executable(scancode_cmd)

    root = Path(target).expanduser().resolve()
    if not root.exists():
        raise FileNotFoundError(f"Target path not found: {root}")

    # If a single file is provided, fall back to the basic scanner.
    if root.is_file():
        return detect_license(
            root, scancode_cmd=scancode_cmd, extra_args=extra_args
        )

    if split_threshold < 1:
        split_threshold = 1
    if chunk_file_count < 1:
        chunk_file_count = 1

    license_map: LicenseMap = {}

    def invoke_and_merge(targets: list[Path]) -> None:
        if not targets:
            return
        data = _invoke_scancode(executable, targets, extra_args)
        license_map.update(_collect_license_map(data, root))

    def chunked(items: Sequence[Path], size: int) -> list[list[Path]]:
        return [list(items[i : i + size]) for i in range(0, len(items), size)]

    # 1) Scan only top-level files under root (batch them)
    top_level_files = [p for p in root.iterdir() if p.is_file()]
    for batch in chunked(sorted(top_level_files), chunk_file_count):
        invoke_and_merge(batch)

    def process_dir(current: Path) -> None:
        children_dirs = [p for p in current.iterdir() if p.is_dir()]
        direct_files = [p for p in current.iterdir() if p.is_file()]

        if direct_files:
            # Always scan direct files from the same folder in batches.
            for batch in chunked(sorted(direct_files), chunk_file_count):
                invoke_and_merge(batch)

            # Then decide how to handle child directories.
            for sub in sorted(children_dirs):
                sub_children = [p for p in sub.iterdir() if p.is_dir()]
                if not sub_children or len(sub_children) < split_threshold:
                    # Do not further split: scan the subdirectory as a whole
                    invoke_and_merge([sub])
                else:
                    # Recurse further
                    process_dir(sub)
            return

        # No direct files here
        if not children_dirs or len(children_dirs) < split_threshold:
            # Scan the entire directory as a whole
            invoke_and_merge([current])
            return

        # Too many children: split by recursing into each child
        for sub in sorted(children_dirs):
            process_dir(sub)

    # 2) Process each top-level subdirectory
    top_level_dirs = [p for p in root.iterdir() if p.is_dir()]
    for subdir in sorted(top_level_dirs):
        process_dir(subdir)

    return license_map


def _resolve_scancode_executable(scancode_cmd: str) -> str:
    """Resolve the ScanCode executable on PATH.

    Args:
        scancode_cmd: Executable name or path of ``scancode``.

    Returns:
        The resolved absolute path to the ScanCode executable.

    Raises:
        FileNotFoundError: If the executable cannot be found.
    """
    executable = shutil.which(scancode_cmd)
    if not executable:
        raise FileNotFoundError(f"scancode command not found: {scancode_cmd}")
    return executable


def _invoke_scancode(
    executable: str, targets: list[Path], extra_args: Iterable[str] | None
) -> dict:
    """Invoke ScanCode on a list of targets and parse JSON output.

    Args:
        executable: Resolved path to ``scancode`` executable.
        targets: Files and/or directories to pass to one ScanCode invocation.
        extra_args: Additional ScanCode CLI arguments to append.

    Returns:
        The parsed JSON payload emitted by ScanCode (``--json-pp``).

    Raises:
        ScancodeExecutionError: If ScanCode fails or JSON parsing fails.
    """
    enc = locale.getpreferredencoding(False)

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "scancode.json"
        cmd: list[str] = [executable, "--license", "--json-pp", str(output_path)]
        if extra_args:
            cmd.extend(extra_args)
        # Use absolute paths for robust path normalization on merge
        cmd.extend(str(p.resolve()) for p in targets)

        # Launch process and stream output in real time
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,  # stream to our stdout
            stderr=subprocess.PIPE,  # stream to our stderr
            text=True,
            bufsize=1,  # line-buffered
            encoding=enc,
            errors="replace",
        )

        stdout_buf: list[str] = []
        stderr_buf: list[str] = []

        def _pump(src, dst, acc):
            try:
                for line in iter(src.readline, ""):
                    acc.append(line)
                    dst.write(line)
                    dst.flush()
            finally:
                try:
                    src.close()
                except Exception:
                    pass

        t_out = threading.Thread(
            target=_pump, args=(proc.stdout, sys.stdout, stdout_buf), daemon=True
        )
        t_err = threading.Thread(
            target=_pump, args=(proc.stderr, sys.stderr, stderr_buf), daemon=True
        )
        t_out.start()
        t_err.start()

        returncode = proc.wait()
        t_out.join()
        t_err.join()

        if returncode != 0:
            stderr_text = "".join(stderr_buf).strip()
            stdout_text = "".join(stdout_buf).strip()
            details = stderr_text or stdout_text
            raise ScancodeExecutionError(
                f"scancode failed with exit code {returncode}: {details}"
            )

        # Parse the JSON written to file by scancode
        try:
            data = json.loads(output_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ScancodeExecutionError(
                "Unable to parse scancode output as JSON"
            ) from exc

    return data
