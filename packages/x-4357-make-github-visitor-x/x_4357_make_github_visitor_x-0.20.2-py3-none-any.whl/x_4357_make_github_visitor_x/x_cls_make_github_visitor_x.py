from __future__ import annotations

import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import time
from collections.abc import Iterable, Mapping, MutableMapping, Sequence
from contextlib import suppress
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, cast

from x_make_common_x import emit_event, get_logger, make_event
from x_make_github_visitor_x.inspection_flow import VisitorRunResult

if TYPE_CHECKING:
    from x_make_common_x.telemetry import JSONValue

_LOGGER = get_logger("x_make_github_visitor")


def _info(*args: object) -> None:
    msg = " ".join(str(a) for a in args)
    with suppress(Exception):
        _LOGGER.info("%s", msg)


"""Visitor to run ruff/black/mypy/pyright on immediate child git clones.

Hidden and cache directories (for example: .mypy_cache, .ruff_cache,
__pycache__, .pyright) are ignored when discovering child repositories.
The visitor caches tool outputs for unchanged repositories and emits a
timestamped JSON report summarising any failures for downstream automation.
Failures are captured for reporting without raising so orchestrators can
continue processing while surfacing diagnostics.
"""


COMMON_CACHE_NAMES = {
    ".mypy_cache",
    ".ruff_cache",
    "__pycache__",
    ".pyright",
    ".tool_cache",
}

GENERATED_BUILD_DIR_PREFIXES: tuple[str, ...] = ("_build_temp",)

TOOL_MODULE_MAP = {
    "ruff_fix": "ruff",
    "ruff_check": "ruff",
    "black": "black",
    "mypy": "mypy",
    "pyright": "pyright",
}

ToolResult = dict[str, object]
RepoReport = dict[str, object]
FAILURE_PREVIEW_LIMIT = 5
OUTPUT_PREVIEW_LIMIT = 5
VISIBLE_DIR_PREVIEW_LIMIT = 10
DEFAULT_TIMEOUT_SECONDS = 300
REQUIRED_PACKAGES: tuple[str, ...] = (
    "ruff",
    "black",
    "mypy",
    "pyright",
)
SUMMARY_MESSAGE_LIMIT = 240
REPORTS_DIR_NAME = "reports"

_DIR_SCAN_YIELD_INTERVAL = 4
_FILE_SCAN_YIELD_INTERVAL = 8
_REPO_ITERATION_YIELD_INTERVAL = 1
_TOOL_ITERATION_YIELD_INTERVAL = 1


def _cooperative_yield() -> None:
    """Hint to the scheduler so GUI threads can process events."""

    time.sleep(0.001)


def _yield_periodically(counter: int, *, interval: int) -> None:
    if interval <= 0:
        return
    if counter % interval == 0:
        _cooperative_yield()


@dataclass(frozen=True)
class ToolConfig:
    name: str
    command: list[str]
    skip_if_no_python: bool


@dataclass
class ToolOutcome:
    result: ToolResult
    failure_message: str | None = None
    failure_detail: dict[str, object] | None = None


@dataclass
class RepoProcessingResult:
    relative_name: str
    report: RepoReport
    failure_messages: list[str]
    failure_details: list[dict[str, object]]


@dataclass(frozen=True)
class RepoContext:
    path: Path
    rel_path: str
    repo_hash: str
    has_python: bool
    files: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class _ToolEventPayload:
    repo: RepoContext
    config: ToolConfig
    module_name: str
    status: str
    result: Mapping[str, object]
    summary: str | None = None
    failures: Sequence[Mapping[str, str]] | None = None


def _coerce_exit_code(value: object) -> int | None:
    if value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return None
    return None


def _increment_counter(
    mapping: MutableMapping[str, object],
    key: str,
    delta: int = 1,
) -> None:
    current = mapping.get(key, 0)
    if isinstance(current, int):
        mapping[key] = current + delta
    else:
        mapping[key] = delta


def _preview_lines(lines: Sequence[str], limit: int) -> str:
    preview = "\n".join(lines[:limit])
    if len(lines) > limit:
        preview += "\n…"
    return preview


def _json_ready(value: object) -> JSONValue:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Mapping):
        typed_mapping = cast("Mapping[object, object]", value)
        return {str(key): _json_ready(val) for key, val in typed_mapping.items()}
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        typed_sequence = cast("Sequence[object]", value)
        return [_json_ready(entry) for entry in typed_sequence]
    return str(value)


def _is_generated_build_dir(name: str) -> bool:
    return any(name.startswith(prefix) for prefix in GENERATED_BUILD_DIR_PREFIXES)


class x_cls_make_github_visitor_x:  # noqa: N801 - legacy naming retained for compatibility
    def __init__(
        self,
        root_dir: str | Path,
        *,
        output_filename: str = "repos_index.json",
        ctx: object | None = None,
        enable_cache: bool = True,
    ) -> None:
        """Initialize visitor.

        root_dir: path to a workspace that contains immediate child git clones.
        output_filename: unused for package-local index storage but kept for
        backwards compatibility.
        enable_cache: whether to reuse cached tool outputs when repositories are
        unchanged between runs.
        """
        self.root = Path(root_dir)
        if not self.root.exists() or not self.root.is_dir():
            msg = f"root path must exist and be a directory: {self.root}"
            raise AssertionError(msg)

        # Track whether the workspace root is itself a git repository. The
        # control center operates on immediate child clones, so we tolerate a
        # git root and simply avoid treating it as an inspected repository.
        self._root_is_git_repo = (self.root / ".git").is_dir()
        if self._root_is_git_repo:
            _info(
                (
                    "workspace root is a git repository; proceeding "
                    "with child clone discovery"
                ),
                str(self.root),
            )

        self.output_filename = output_filename
        self._tool_reports: dict[str, RepoReport] = {}
        self._ctx = ctx
        self.enable_cache = enable_cache
        self._last_run_failures: bool = False
        self._failure_messages: list[str] = []
        self._failure_details: list[dict[str, object]] = []
        self._tool_versions: dict[str, str] = {}
        self._runtime_snapshot: dict[str, object] = {}
        self._last_report_path: Path | None = None
        self._last_run_result: VisitorRunResult | None = None

        # package root (the folder containing this module). Reports live here so
        # they remain alongside the visitor package rather than the workspace
        # root.
        self.package_root = Path(__file__).resolve().parent
        self._reports_dir = self.package_root / REPORTS_DIR_NAME

        self.cache_dir = self.package_root / ".tool_cache"
        if self.enable_cache:
            self.cache_dir.mkdir(exist_ok=True)

    def _child_dirs(self) -> list[Path]:
        """Return immediate child directories excluding hidden and cache dirs.

        Exclude names starting with '.' or '__' and common cache names to avoid
        treating tool caches as repositories.
        """
        out: list[Path] = []
        for index, p in enumerate(self.root.iterdir(), 1):
            _yield_periodically(index, interval=_DIR_SCAN_YIELD_INTERVAL)
            if not p.is_dir():
                continue
            name = p.name
            if name.startswith((".", "__")):
                # hidden or dunder directories (including caches)
                continue
            if name in COMMON_CACHE_NAMES:
                continue
            # Only include directories that look like git clones (contain .git)
            if not (p / ".git").exists():
                # skip non-repo helper folders
                continue
            out.append(p)
        return sorted(out)

    def _atomic_write_json(self, path: Path, data: object) -> None:
        tmp = path.with_name(path.name + ".tmp")
        with tmp.open("w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=4, sort_keys=True)
            fh.flush()
            with suppress(OSError):
                os.fsync(fh.fileno())
        tmp.replace(path)

    @staticmethod
    def _ensure_text(value: object) -> str:
        def decode_bytes(raw: bytes) -> str:
            try:
                return raw.decode("utf-8")
            except UnicodeDecodeError:  # pragma: no cover - diagnostic fallback
                return raw.decode("utf-8", "replace")

        if isinstance(value, str):
            return value

        if isinstance(value, (bytes, bytearray)):
            return decode_bytes(bytes(value))

        if isinstance(value, memoryview):
            return decode_bytes(value.tobytes())

        if value is None:
            return ""
        return str(value)

    def _cleanup_generated_build_dirs(self, repo_path: Path) -> None:
        with suppress(OSError):
            for index, child in enumerate(repo_path.iterdir(), 1):
                _yield_periodically(index, interval=_DIR_SCAN_YIELD_INTERVAL)
                if not child.is_dir():
                    continue
                if not _is_generated_build_dir(child.name):
                    continue
                _info("Removing generated build directory:", str(child))
                shutil.rmtree(child, ignore_errors=True)

    def _repo_content_hash(self, repo_path: Path) -> str:
        """Return a deterministic hash of repository contents for caching."""
        hasher = hashlib.sha256()
        for index, p in enumerate(sorted(repo_path.rglob("*")), 1):
            _yield_periodically(index, interval=_FILE_SCAN_YIELD_INTERVAL)
            if not p.is_file():

                continue
            if ".git" in p.parts or "__pycache__" in p.parts:
                continue
            if any(_is_generated_build_dir(part) for part in p.parts):
                continue
            if p.suffix in {".pyc", ".pyo"}:
                continue
            rel = p.relative_to(repo_path).as_posix().encode("utf-8")
            hasher.update(rel)
            try:
                hasher.update(p.read_bytes())
            except OSError:
                # Skip unreadable files without failing the whole hash
                continue
        return hasher.hexdigest()

    def _cache_path(self, repo_name: str, tool_name: str, repo_hash: str) -> Path:
        key = f"{repo_name}_{tool_name}_{repo_hash[:16]}"
        return self.cache_dir / f"{key}.json"

    def _prepare_environment(self, python: str, packages: Sequence[str]) -> None:
        proc = subprocess.run(  # noqa: S603
            [python, "-m", "pip", "install", "--upgrade", *packages],
            check=False,
            capture_output=True,
            text=True,
        )
        _cooperative_yield()
        if proc.returncode != 0:
            msg = f"failed to install required packages: {proc.stdout}\n{proc.stderr}"
            raise AssertionError(msg)

        self._tool_versions = self._collect_tool_versions(python)
        _cooperative_yield()
        self._runtime_snapshot = {
            "python_executable": python,
            "python_version": sys.version.replace("\n", " "),
            "platform": platform.platform(),
            "run_started_at": datetime.now(UTC).isoformat(),
            "workspace_root": str(self.root),
        }

        env_snapshot = {
            key: os.environ.get(key)
            for key in ("PATH", "PYTHONPATH", "VIRTUAL_ENV")
            if os.environ.get(key)
        }
        if env_snapshot:
            self._runtime_snapshot["environment"] = env_snapshot

        self._prune_cache()
        _cooperative_yield()

    def _tool_configurations(self, python: str) -> list[ToolConfig]:
        return [
            ToolConfig(
                name="ruff_fix",
                command=[
                    python,
                    "-m",
                    "ruff",
                    "check",
                    ".",
                    "--fix",
                    "--select",
                    "ALL",
                    "--ignore",
                    "D,COM812,ISC001,T20",
                    "--line-length",
                    "88",
                    "--target-version",
                    "py311",
                ],
                skip_if_no_python=False,
            ),
            ToolConfig(
                name="black",
                command=[
                    python,
                    "-m",
                    "black",
                    ".",
                    "--line-length",
                    "88",
                    "--target-version",
                    "py311",
                    "--check",
                    "--diff",
                ],
                skip_if_no_python=True,
            ),
            ToolConfig(
                name="ruff_check",
                command=[
                    python,
                    "-m",
                    "ruff",
                    "check",
                    ".",
                    "--select",
                    "ALL",
                    "--ignore",
                    "D,COM812,ISC001,T20",
                    "--line-length",
                    "88",
                    "--target-version",
                    "py311",
                ],
                skip_if_no_python=False,
            ),
            ToolConfig(
                name="mypy",
                command=[
                    python,
                    "-m",
                    "mypy",
                    ".",
                    "--strict",
                    "--no-warn-unused-configs",
                    "--show-error-codes",
                    "--warn-return-any",
                    "--warn-unreachable",
                    "--disallow-any-unimported",
                    "--disallow-any-expr",
                    "--disallow-any-decorated",
                    "--disallow-any-explicit",
                ],
                skip_if_no_python=True,
            ),
            ToolConfig(
                name="pyright",
                command=[
                    python,
                    "-m",
                    "pyright",
                    ".",
                    "--level",
                    "error",
                ],
                skip_if_no_python=True,
            ),
        ]

    def _collect_repo_files(self, repo_path: Path) -> list[str]:
        files: list[str] = []
        for index, pth in enumerate(repo_path.rglob("*"), 1):
            _yield_periodically(index, interval=_FILE_SCAN_YIELD_INTERVAL)
            if not pth.is_file():
                continue
            if ".git" in pth.parts or "__pycache__" in pth.parts:
                continue
            if any(_is_generated_build_dir(part) for part in pth.parts):
                continue
            if pth.suffix.lower() not in {".py", ".pyi"}:
                continue
            files.append(str(pth.relative_to(repo_path).as_posix()))
        return sorted(files)

    def _extract_failure_entries(
        self,
        *,
        repo: RepoContext,
        result: Mapping[str, object],
    ) -> list[dict[str, str]]:
        stdout_text = self._ensure_text(result.get("stdout", ""))
        stderr_text = self._ensure_text(result.get("stderr", ""))
        if not repo.files:
            return []
        combined_lines = [line.strip() for line in stdout_text.splitlines()]
        combined_lines.extend(line.strip() for line in stderr_text.splitlines())
        entries: list[dict[str, str]] = []
        seen: set[str] = set()
        for rel_path in repo.files:
            variants = {rel_path, rel_path.replace("/", os.sep)}
            snippets = [
                line
                for line in combined_lines
                if any(variant in line for variant in variants)
            ]
            if not snippets:
                continue
            if rel_path in seen:
                continue
            seen.add(rel_path)
            entries.append(
                {
                    "file": rel_path,
                    "message": "\n".join(snippets[:OUTPUT_PREVIEW_LIMIT]),
                }
            )
        return entries

    def _emit_tool_event(self, payload: _ToolEventPayload) -> None:
        result = payload.result
        duration_value = result.get("duration_seconds")
        duration_ms: int | None
        if isinstance(duration_value, (int, float)):
            duration_ms = int(max(float(duration_value), 0.0) * 1000)
        else:
            duration_ms = None
        details: dict[str, object] = {
            "repo": payload.repo.rel_path,
            "repo_path": str(payload.repo.path),
            "tool": payload.config.name,
            "tool_family": payload.module_name,
            "files": list(payload.repo.files),
            "cached": bool(result.get("cached", False)),
            "skipped": bool(result.get("skipped", False)),
            "timed_out": bool(result.get("timed_out", False)),
        }
        if payload.summary:
            details["failure_summary"] = payload.summary
        if payload.failures:
            details["failures"] = [
                {"file": entry.get("file", ""), "message": entry.get("message", "")}
                for entry in payload.failures
            ]
        json_details = cast("Mapping[str, JSONValue]", details)
        emit_event(
            make_event(
                source="visitor",
                phase="inspection",
                status=payload.status,
                repository=payload.repo.rel_path,
                tool=payload.module_name,
                attempt=1,
                duration_ms=duration_ms,
                details=json_details,
            )
        )

    def _process_repository(
        self,
        repo_path: Path,
        python: str,
        timeout: int,
    ) -> RepoProcessingResult:
        _cooperative_yield()
        self._cleanup_generated_build_dirs(repo_path)
        rel = str(repo_path.relative_to(self.root))
        repo_hash = self._repo_content_hash(repo_path)
        repo_files = self._collect_repo_files(repo_path)
        repo_context = RepoContext(
            path=repo_path,
            rel_path=rel,
            repo_hash=repo_hash,
            has_python=bool(repo_files),
            files=tuple(repo_files),
        )

        tool_reports: dict[str, ToolResult] = {}
        failure_messages: list[str] = []
        failure_details: list[dict[str, object]] = []

        configs = self._tool_configurations(python)
        for index, config in enumerate(configs, 1):
            outcome = self._run_tool_for_repo(
                repo=repo_context,
                config=config,
                timeout=timeout,
            )
            tool_reports[config.name] = outcome.result
            if outcome.failure_message:
                failure_messages.append(outcome.failure_message)
            if outcome.failure_detail:
                failure_details.append(outcome.failure_detail)
            _yield_periodically(index, interval=_TOOL_ITERATION_YIELD_INTERVAL)

        repo_report: RepoReport = {
            "timestamp": datetime.now(UTC).isoformat(),
            "repo_hash": repo_context.repo_hash,
            "tool_reports": tool_reports,
            "files": repo_files,
        }

        return RepoProcessingResult(
            relative_name=repo_context.rel_path,
            report=repo_report,
            failure_messages=failure_messages,
            failure_details=failure_details,
        )

    def _build_skip_outcome(
        self,
        *,
        repo: RepoContext,
        config: ToolConfig,
        tool_version: str,
        module_name: str,
    ) -> ToolOutcome:
        now_iso = datetime.now(UTC).isoformat()
        skip_result: ToolResult = {
            "exit": 0,
            "stdout": "",
            "stderr": "skipped - no Python source (.py/.pyi) found",
            "cached": False,
            "skipped": True,
            "skip_reason": "no_python_files",
            "cmd": list(config.command),
            "cmd_display": " ".join(str(part) for part in config.command),
            "cwd": str(repo.path),
            "started_at": now_iso,
            "ended_at": now_iso,
            "duration_seconds": 0.0,
            "repo_hash": repo.repo_hash,
            "tool_version": tool_version,
            "tool_module": module_name,
        }
        return ToolOutcome(skip_result)

    def _load_cached_outcome(
        self,
        *,
        repo: RepoContext,
        config: ToolConfig,
        tool_version: str,
        module_name: str,
    ) -> ToolOutcome | None:
        cached = self._load_cache(repo.rel_path, config.name, repo.repo_hash)
        if cached is None:
            return None
        cached_result: ToolResult = dict(cached)
        cached_result["cached"] = True
        cached_result.setdefault("cmd", list(config.command))
        cached_result.setdefault(
            "cmd_display",
            " ".join(str(part) for part in config.command),
        )
        cached_result.setdefault("cwd", str(repo.path))
        cached_result.setdefault("repo_hash", repo.repo_hash)
        cached_result.setdefault("tool_version", tool_version)
        cached_result.setdefault("tool_module", module_name)
        cached_result.setdefault("started_at", "")
        cached_result.setdefault("ended_at", "")
        cached_result.setdefault("duration_seconds", 0.0)
        _info(f"{config.name}: cache hit for {repo.rel_path}")
        return ToolOutcome(cached_result)

    def _run_tool_for_repo(
        self,
        *,
        repo: RepoContext,
        config: ToolConfig,
        timeout: int,
    ) -> ToolOutcome:
        module_name = TOOL_MODULE_MAP.get(config.name, config.name)
        tool_version = self._tool_versions.get(module_name, "<unknown>")

        self._emit_tool_event(
            _ToolEventPayload(
                repo=repo,
                config=config,
                module_name=module_name,
                status="started",
                result={
                    "duration_seconds": 0.0,
                    "cached": False,
                    "skipped": False,
                },
            )
        )

        if config.skip_if_no_python and not repo.has_python:
            _info(f"{config.name}: skipped (no Python files) in {repo.rel_path}")
            outcome = self._build_skip_outcome(
                repo=repo,
                config=config,
                tool_version=tool_version,
                module_name=module_name,
            )
            self._emit_tool_event(
                _ToolEventPayload(
                    repo=repo,
                    config=config,
                    module_name=module_name,
                    status="skipped",
                    result=outcome.result,
                    summary="No Python files detected; skipping",
                )
            )
            return outcome

        cached_outcome = self._load_cached_outcome(
            repo=repo,
            config=config,
            tool_version=tool_version,
            module_name=module_name,
        )
        if cached_outcome is not None:
            self._emit_tool_event(
                _ToolEventPayload(
                    repo=repo,
                    config=config,
                    module_name=module_name,
                    status="succeeded",
                    result=cached_outcome.result,
                    summary="Result loaded from cache",
                )
            )
            return cached_outcome

        start_wall = datetime.now(UTC)
        start_perf = time.perf_counter()
        timed_out = False
        exit_code: int | None
        stdout_obj: object
        stderr_obj: object

        try:
            _cooperative_yield()
            completed = subprocess.run(  # noqa: S603
                config.command,
                check=False,
                cwd=str(repo.path),
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            exit_code = completed.returncode
            stdout_obj = completed.stdout
            stderr_obj = completed.stderr
        except subprocess.TimeoutExpired as exc:  # pragma: no cover - diag path
            timed_out = True
            exit_code = None
            stdout_output = cast("object | None", exc.output)
            stderr_output = cast("object | None", exc.stderr)
            stdout_obj = stdout_output if stdout_output is not None else ""
            stderr_obj = stderr_output if stderr_output is not None else ""

        end_wall = datetime.now(UTC)
        duration = max(time.perf_counter() - start_perf, 0.0)

        proc_stdout = self._ensure_text(stdout_obj)
        proc_stderr = self._ensure_text(stderr_obj)

        result: ToolResult = {
            "exit": exit_code,
            "stdout": proc_stdout,
            "stderr": proc_stderr,
            "cached": False,
            "cmd": list(config.command),
            "cmd_display": " ".join(str(part) for part in config.command),
            "cwd": str(repo.path),
            "started_at": start_wall.isoformat(),
            "ended_at": end_wall.isoformat(),
            "duration_seconds": duration,
            "repo_hash": repo.repo_hash,
            "tool_version": tool_version,
            "tool_module": module_name,
        }
        if timed_out:
            result["timed_out"] = True
            result["timeout_seconds"] = timeout

        failure_condition = timed_out or exit_code is None or exit_code != 0
        if failure_condition:
            self._delete_cache(repo.rel_path, config.name, repo.repo_hash)
            message, detail = self._build_failure_payload(
                repo=repo,
                config=config,
                timed_out=timed_out,
                result=result,
            )
            _info(
                f"{config.name}: failure in {repo.rel_path};",
                "details captured",
            )
            failure_entries = self._extract_failure_entries(repo=repo, result=result)
            self._emit_tool_event(
                _ToolEventPayload(
                    repo=repo,
                    config=config,
                    module_name=module_name,
                    status="failed",
                    result=result,
                    summary=message,
                    failures=tuple(failure_entries),
                )
            )
            return ToolOutcome(result, message, detail)

        self._store_cache(repo.rel_path, config.name, repo.repo_hash, result)
        self._emit_tool_event(
            _ToolEventPayload(
                repo=repo,
                config=config,
                module_name=module_name,
                status="succeeded",
                result=result,
            )
        )
        return ToolOutcome(result)

    def _build_failure_payload(
        self,
        *,
        repo: RepoContext,
        config: ToolConfig,
        timed_out: bool,
        result: ToolResult,
    ) -> tuple[str, dict[str, object]]:
        stdout_text = self._ensure_text(result.get("stdout", ""))
        stderr_text = self._ensure_text(result.get("stderr", ""))
        truncated_stdout = stdout_text.strip().splitlines()
        truncated_stderr = stderr_text.strip().splitlines()
        preview_stdout = _preview_lines(truncated_stdout, OUTPUT_PREVIEW_LIMIT)
        preview_stderr = _preview_lines(truncated_stderr, OUTPUT_PREVIEW_LIMIT)
        exit_code = _coerce_exit_code(result.get("exit"))
        exit_display = "timeout" if timed_out else f"exit {exit_code}"
        duration_value = result.get("duration_seconds", 0.0)
        if isinstance(duration_value, (int, float)):
            duration = float(duration_value)
        else:
            duration = 0.0
        tool_version = self._ensure_text(result.get("tool_version", "<unknown>"))
        cmd_display = self._ensure_text(result.get("cmd_display", ""))
        started_at = self._ensure_text(result.get("started_at", ""))
        failure_message_lines = [
            f"{config.name} failed for {repo.rel_path} ({exit_display})",
            f"cwd: {repo.path}",
            f"command: {cmd_display}",
            f"started_at: {started_at}",
            f"duration: {duration:.3f}s",
            f"tool_version: {tool_version}",
            f"stdout:\n{preview_stdout or '<empty>'}",
            f"stderr:\n{preview_stderr or '<empty>'}",
        ]
        failure_message = "\n".join(failure_message_lines)
        failure_detail: dict[str, object] = {
            "repo": repo.rel_path,
            "repo_path": str(repo.path),
            "tool": config.name,
            "tool_module": self._ensure_text(result.get("tool_module", config.name)),
        }
        failure_detail.update(result)
        return failure_message, failure_detail

    def _ensure_reports_dir(self) -> Path:
        reports_dir = self._reports_dir
        reports_dir.mkdir(parents=True, exist_ok=True)
        return reports_dir

    def _remove_legacy_json_reports(self) -> None:
        legacy_names = (
            "x_index_a_a_priori_x.json",
            "x_index_b_a_posteriori_x.json",
            "x_summary_report_x.json",
            "x_tool_failures_x.json",
        )
        for name in legacy_names:
            stale_path = self.package_root / name
            with suppress(OSError):
                if stale_path.exists():
                    stale_path.unlink()

    def _summarize_failure_message(self, message: str) -> str:
        collapsed = " ".join(message.strip().split())
        if not collapsed:
            return "Tool failure recorded"
        if len(collapsed) <= SUMMARY_MESSAGE_LIMIT:
            return collapsed
        return collapsed[: SUMMARY_MESSAGE_LIMIT - 1] + "…"

    def _command_display(self, detail: Mapping[str, object]) -> str:
        cmd_display = detail.get("cmd_display")
        if isinstance(cmd_display, str) and cmd_display.strip():
            return cmd_display.strip()
        raw_cmd = detail.get("cmd")
        if isinstance(raw_cmd, Sequence) and not isinstance(
            raw_cmd,
            (str, bytes, bytearray),
        ):
            parts_seq = cast("Sequence[object]", raw_cmd)
            parts = [str(part) for part in parts_seq]
            if parts:
                return " ".join(parts)
        return "<command unavailable>"

    def _ensure_detail_text(self, detail: Mapping[str, object], key: str) -> str:
        value = detail.get(key)
        if value is None:
            return ""
        if isinstance(value, str):
            return value
        return str(value)

    def _detail_value(
        self,
        detail: Mapping[str, object],
        *keys: str,
        default: str = "",
    ) -> str:
        for key in keys:
            value = self._ensure_detail_text(detail, key)
            if value:
                return value
        return default

    def _stat_value(self, mapping: Mapping[str, object], key: str) -> int:
        value = mapping.get(key)
        if isinstance(value, bool):
            return int(value)
        if isinstance(value, (int, float)):
            return int(value)
        if isinstance(value, str):
            with suppress(ValueError):
                return int(value)
        return 0

    def _exit_display(self, detail: Mapping[str, object]) -> str:
        if detail.get("timed_out"):
            timeout = self._detail_value(detail, "timeout_seconds")
            return f"timeout after {timeout}s" if timeout else "timeout"

        exit_code = _coerce_exit_code(detail.get("exit"))
        if exit_code is None:
            return "exit <unknown>"
        return f"exit {exit_code}"

    def _preview_output(self, detail: Mapping[str, object], key: str) -> str:
        text = self._ensure_text(detail.get(key, ""))
        return _preview_lines(text.splitlines(), OUTPUT_PREVIEW_LIMIT)

    def _serialize_failures(
        self,
        detail_pairs: Sequence[tuple[Mapping[str, object], str]],
    ) -> list[dict[str, JSONValue]]:
        entries: list[dict[str, JSONValue]] = []
        for detail, message in detail_pairs:
            repo = self._detail_value(detail, "repo", "repo_path", default="")
            tool = self._detail_value(detail, "tool", "tool_module", default="")
            preview = self._summarize_failure_message(message)
            command_display = self._command_display(detail)
            exit_display = self._exit_display(detail)
            repo_path = self._detail_value(detail, "repo_path", "cwd") or None
            suggestion = (
                self._detail_value(
                    detail,
                    "next_action",
                    default="Investigate",
                )
                or None
            )
            captured_at = self._detail_value(detail, "ended_at", "started_at") or None
            tool_version = self._detail_value(detail, "tool_version") or None
            stdout_preview = self._preview_output(detail, "stdout") or None
            stderr_preview = self._preview_output(detail, "stderr") or None
            entries.append(
                {
                    "repo": repo or None,
                    "tool": tool or None,
                    "summary": preview,
                    "message": message,
                    "command": command_display,
                    "exit": exit_display,
                    "repo_path": repo_path,
                    "tool_version": tool_version,
                    "captured_at": captured_at,
                    "suggested_action": suggestion,
                    "stdout_preview": stdout_preview,
                    "stderr_preview": stderr_preview,
                    "detail": _json_ready(detail),
                }
            )
        entries.sort(
            key=lambda entry: (
                str(entry.get("repo") or "").casefold(),
                str(entry.get("tool") or "").casefold(),
                str(entry.get("summary") or ""),
            )
        )
        return entries

    def _write_json_failure_report(self) -> Path:
        reports_dir = self._ensure_reports_dir()
        now = datetime.now(UTC)
        timestamp = now.strftime("%Y%m%d_%H%M%S")
        filename = f"visitor_failures_{timestamp}.json"
        report_path = reports_dir / filename

        summary = self.generate_summary_report()
        detail_pairs = list(
            zip(self._failure_details, self._failure_messages, strict=False)
        )

        payload: dict[str, JSONValue] = {
            "schema_version": "1.0",
            "generated_at": now.isoformat(),
            "workspace_root": str(self.root),
            "runtime": _json_ready(dict(self._runtime_snapshot)),
            "tool_versions": _json_ready(dict(self._tool_versions)),
            "summary": _json_ready(summary),
            "failures": _json_ready(self._serialize_failures(detail_pairs)),
        }

        self._atomic_write_json(report_path, payload)
        self._last_report_path = report_path
        return report_path

    def _finalize_run_result(self, report_path: Path | None) -> VisitorRunResult:
        had_failures = bool(self._last_run_failures)
        messages = tuple(self._failure_messages)
        details = tuple(dict(detail) for detail in self._failure_details)

        if had_failures:
            preview_chunks = list(messages[:FAILURE_PREVIEW_LIMIT])
            preview = "\n\n".join(preview_chunks)
            _info("toolchain failure preview:")
            if preview:
                for block in preview.split("\n\n"):
                    _info(block)
            if len(messages) > FAILURE_PREVIEW_LIMIT:
                _info("…additional failures omitted…")
            if report_path is not None:
                _info("toolchain failures recorded in:", str(report_path))
            else:
                _info("toolchain failures recorded; JSON report path unavailable")

        result = VisitorRunResult(
            report_path=report_path,
            had_failures=had_failures,
            failure_messages=messages,
            failure_details=details,
            skipped=False,
        )
        self._last_run_result = result
        return result

    def _load_cache(
        self,
        repo_name: str,
        tool_name: str,
        repo_hash: str,
    ) -> ToolResult | None:
        if not self.enable_cache:
            return None
        cache_file = self._cache_path(repo_name, tool_name, repo_hash)
        if not cache_file.exists():
            return None
        try:
            with cache_file.open("r", encoding="utf-8") as fh:
                cached = cast("ToolResult", json.load(fh))
        except (OSError, json.JSONDecodeError):
            with suppress(OSError):
                cache_file.unlink()
            return None
        exit_value = cached.get("exit", 0)
        exit_code: int | None
        if isinstance(exit_value, int):
            exit_code = exit_value
        elif isinstance(exit_value, str):
            try:
                exit_code = int(exit_value)
            except ValueError:
                exit_code = None
        else:
            exit_code = None
        if exit_code not in (None, 0):
            self._delete_cache(repo_name, tool_name, repo_hash)
            return None
        return cached

    def _store_cache(
        self,
        repo_name: str,
        tool_name: str,
        repo_hash: str,
        payload: ToolResult,
    ) -> None:
        if not self.enable_cache:
            return
        cache_file = self._cache_path(repo_name, tool_name, repo_hash)
        with suppress(OSError):
            self._atomic_write_json(cache_file, payload)

    def _delete_cache(
        self,
        repo_name: str,
        tool_name: str,
        repo_hash: str,
    ) -> None:
        if not self.enable_cache:
            return
        cache_file = self._cache_path(repo_name, tool_name, repo_hash)
        with suppress(OSError):
            cache_file.unlink()

    def _prune_cache(self, keep: int = 500) -> None:
        if not self.enable_cache or not self.cache_dir.exists():
            return
        try:
            candidate_files = list(self.cache_dir.glob("*.json"))
        except OSError:
            return

        def _file_mtime(path: Path) -> float:
            try:
                return path.stat().st_mtime
            except OSError:
                return 0.0

        cache_files = sorted(candidate_files, key=_file_mtime)
        overflow = len(cache_files) - keep
        if overflow <= 0:
            return
        for index, stale in enumerate(cache_files[:overflow], 1):
            _yield_periodically(index, interval=_FILE_SCAN_YIELD_INTERVAL)
            with suppress(OSError):
                stale.unlink()

    def _collect_tool_versions(self, python: str) -> dict[str, str]:
        versions: dict[str, str] = {}
        for module in sorted({*TOOL_MODULE_MAP.values()}):
            try:
                proc = subprocess.run(  # noqa: S603
                    [python, "-m", module, "--version"],
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
            except (
                OSError,
                subprocess.TimeoutExpired,
                subprocess.SubprocessError,
            ) as exc:  # pragma: no cover - diagnostics only
                versions[module] = f"<error invoking --version: {exc}>"
                continue
            output = (proc.stdout or proc.stderr).strip()
            if proc.returncode != 0:
                versions[module] = f"<exit {proc.returncode}> {output}"
            else:
                versions[module] = output or "<no output>"
            _cooperative_yield()
        return versions

    def body(self, *, children: Iterable[Path] | None = None) -> None:
        """Run ruff/black/mypy/pyright against each child repository."""

        python = sys.executable
        self._prepare_environment(python, REQUIRED_PACKAGES)

        reports: dict[str, RepoReport] = {}
        failure_messages: list[str] = []
        failure_details: list[dict[str, object]] = []

        repo_iterable = list(children) if children is not None else self._child_dirs()
        for index, child in enumerate(repo_iterable, 1):
            result = self._process_repository(
                child,
                python,
                DEFAULT_TIMEOUT_SECONDS,
            )
            reports[result.relative_name] = result.report
            failure_messages.extend(result.failure_messages)
            failure_details.extend(result.failure_details)
            _yield_periodically(index, interval=_REPO_ITERATION_YIELD_INTERVAL)

        self._tool_reports = reports
        self._last_run_failures = bool(failure_messages)
        self._failure_messages = failure_messages
        self._failure_details = failure_details
        self._runtime_snapshot["run_completed_at"] = datetime.now(UTC).isoformat()

    def cleanup(self) -> None:
        """Placeholder for cleanup. Override if needed."""
        return

    def generate_summary_report(self) -> dict[str, object]:
        """Produce an aggregate summary of the most recent tool run."""
        overall_stats: dict[str, object] = {
            "cache_hits": 0,
            "cache_misses": 0,
            "failed_tools": 0,
            "total_tools_run": 0,
            "had_failures": bool(self._last_run_failures),
        }
        repos_section: dict[str, dict[str, object]] = {}
        summary: dict[str, object] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "total_repos": len(self._tool_reports),
            "overall_stats": overall_stats,
            "repos": repos_section,
        }
        for repo_name, report in self._tool_reports.items():
            tools_summary: dict[str, dict[str, object]] = {}
            repo_summary: dict[str, object] = {
                "repo_hash": report.get("repo_hash"),
                "tools": tools_summary,
                "cached": 0,
                "failed": 0,
            }
            raw_tools = report.get("tool_reports")
            tool_map: dict[str, ToolResult]
            if isinstance(raw_tools, dict):
                tool_map = cast("dict[str, ToolResult]", raw_tools)
            else:
                tool_map = {}
            for tool_name, tool_report in tool_map.items():
                exit_code = _coerce_exit_code(tool_report.get("exit"))
                cached_flag = bool(tool_report.get("cached", False))
                timed_out_flag = bool(tool_report.get("timed_out", False))
                tools_summary[tool_name] = {
                    "exit": exit_code,
                    "cached": cached_flag,
                    "timed_out": timed_out_flag,
                }
                _increment_counter(overall_stats, "total_tools_run")
                if cached_flag:
                    _increment_counter(repo_summary, "cached")
                    _increment_counter(overall_stats, "cache_hits")
                else:
                    _increment_counter(overall_stats, "cache_misses")
                if timed_out_flag or exit_code not in (None, 0):
                    _increment_counter(repo_summary, "failed")
                    _increment_counter(overall_stats, "failed_tools")
            repos_section[repo_name] = repo_summary
        return summary

    def run_inspect_flow(self) -> None:
        """Run discovery, execute tools, and emit a JSON TODO report."""

        children = self._child_dirs()
        if not children:
            try:
                entries = sorted(p.name for p in self.root.iterdir() if p.is_dir())
            except OSError:
                entries = []
            preview = ", ".join(entries[:VISIBLE_DIR_PREVIEW_LIMIT])
            suffix = "" if len(entries) <= VISIBLE_DIR_PREVIEW_LIMIT else " …"
            msg = (
                "no child git repositories found"
                f" under {self.root} (visible dirs: {preview}{suffix})"
            )
            raise AssertionError(msg)

        repo_names = [str(child.relative_to(self.root)) for child in children]
        self._runtime_snapshot["discovered_repositories"] = repo_names
        _info(
            "visitor discovery:",
            f"found {len(repo_names)} repositories under {self.root}",
        )

        self._remove_legacy_json_reports()
        self.body(children=children)
        report_path = self._write_json_failure_report()
        self.cleanup()
        self._finalize_run_result(report_path)

    @property
    def last_report_path(self) -> Path | None:
        return self._last_report_path

    @property
    def last_run_result(self) -> VisitorRunResult | None:
        return self._last_run_result


def _workspace_root() -> str:
    here = Path(__file__).resolve()
    for anc in here.parents:
        if (anc / ".git").exists():  # repo root
            return str(anc.parent)
    # Fallback: two levels up
    return str(here.parent.parent)


def init_name(
    root_dir: str | Path,
    *,
    output_filename: str | None = None,
    ctx: object | None = None,
    enable_cache: bool = True,
) -> x_cls_make_github_visitor_x:
    if output_filename is None:
        return x_cls_make_github_visitor_x(
            root_dir,
            ctx=ctx,
            enable_cache=enable_cache,
        )
    return x_cls_make_github_visitor_x(
        root_dir,
        output_filename=output_filename,
        ctx=ctx,
        enable_cache=enable_cache,
    )


def init_main(
    ctx: object | None = None,
    *,
    enable_cache: bool = True,
) -> x_cls_make_github_visitor_x:
    """Initialize the visitor using dynamic workspace root (parent of this repo)."""
    return init_name(_workspace_root(), ctx=ctx, enable_cache=enable_cache)


def run_workspace_inspection(
    root_dir: str | Path,
    *,
    ctx: object | None = None,
    enable_cache: bool = True,
) -> VisitorRunResult:
    """Run the full inspection pipeline for the provided workspace root.

    Returns a :class:`VisitorRunResult` describing the report path and any
    captured failures. When no child git repositories are discovered the
    function logs the outcome and marks the result as skipped.
    """

    try:
        visitor = init_name(root_dir, ctx=ctx, enable_cache=enable_cache)
    except (RuntimeError, ValueError, TypeError) as err:  # pragma: no cover
        # init guard
        message = f"x_make_github_visitor instantiate failed: {err}"
        raise AssertionError(message) from err

    _info(
        "Running x_make_github_visitor against cloned repos",
        f"root={Path(root_dir)!s} ...",
    )

    try:
        visitor.run_inspect_flow()
    except AssertionError as err:
        lowered_error = str(err).lower()
        if "no child git repositories found" in lowered_error:
            _info(
                "Visitor skipped: no child git repositories present at root;",
                "continuing orchestrator flow",
            )
            return VisitorRunResult(
                report_path=None,
                had_failures=False,
                skipped=True,
            )
        raise
    except (RuntimeError, ValueError) as err:
        message = f"x_make_github_visitor run failed: {err}"
        raise AssertionError(message) from err

    result = visitor.last_run_result
    if isinstance(result, VisitorRunResult):
        return result

    report_path = visitor.last_report_path
    return VisitorRunResult(
        report_path=report_path,
        had_failures=False,
    )


if __name__ == "__main__":
    inst = init_main()
    inst.run_inspect_flow()
    summary = inst.generate_summary_report()
    overall_raw = summary.get("overall_stats", {})
    overall: Mapping[str, object]
    if isinstance(overall_raw, Mapping):
        overall = cast("Mapping[str, object]", overall_raw)
    else:
        overall = {}

    hits = _coerce_exit_code(overall.get("cache_hits", 0)) or 0
    total = _coerce_exit_code(overall.get("total_tools_run", 0)) or 0
    ratio = (hits / total * 100.0) if total else 0.0

    report_path = inst.last_report_path
    if report_path is not None:
        _info("visitor JSON report saved to:", report_path)
    else:
        _info("visitor JSON report path unavailable")

    summary_line = (
        f"processed {summary.get('total_repos', 0)} repositories "
        f"| cache hits: {hits}/{total} ({ratio:.1f}%)"
    )
    _info(summary_line)
