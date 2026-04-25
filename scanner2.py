import json
import logging
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from types import TracebackType
from typing import Callable

import lizard
import squarify


LOGGER = logging.getLogger(__name__)

# All file extensions supported by lizard
SUPPORTED_EXTENSIONS = [
    ".c",
    ".cc",
    ".cpp",
    ".cxx",
    ".c++",
    ".h",
    ".hh",
    ".hpp",
    ".hxx",
    ".h++",
    ".java",
    ".js",
    ".m",
    ".mm",
    ".py",
    ".rb",
    ".swift",
    ".go",
    ".php",
    ".pl",
    ".pm",
    ".t",
    ".cs",
    ".d",
    ".erl",
    ".ex",
    ".exs",
    ".f90",
    ".f",
    ".for",
    ".f95",
    ".groovy",
    ".hs",
    ".kt",
    ".kts",
    ".lua",
    ".nb",
    ".pas",
    ".pp",
    ".R",
    ".rs",
    ".scala",
    ".sc",
    ".sh",
    ".bash",
    ".sql",
    ".ts",
    ".tsx",
    ".vb",
    ".vbs",
    ".gd",
]

MAX_FILES = 2000
MAX_WORKERS = 20
BUG_CHURN_RE = re.compile(r"\b(fix|bug|patch|hotfix|defect|crash)\b", re.IGNORECASE)
AUTH_ERROR_RE = re.compile(
    r"(authentication failed|could not read username|permission denied|repository not found|not found)",
    re.IGNORECASE,
)


def on_rm_error(
    func: Callable[[str], None],
    path: str,
    exc_info: tuple[type[BaseException], BaseException, TracebackType | None],
) -> None:
    """Retry read-only removals when cleaning up temporary clone directories."""
    if not os.access(path, os.W_OK):
        os.chmod(path, stat.S_IWUSR)
        func(path)
        return
    raise exc_info[1]


def get_github_repo_info(url: str) -> tuple[str, str]:
    """Parse a GitHub URL into ``owner`` and ``repo``."""
    cleaned = url.rstrip("/")
    if cleaned.startswith("https://github.com/"):
        cleaned = cleaned.replace("https://github.com/", "", 1)
    if cleaned.startswith("git@github.com:"):
        cleaned = cleaned.replace("git@github.com:", "", 1)
    if cleaned.endswith(".git"):
        cleaned = cleaned[:-4]
    parts = cleaned.split("/")
    if len(parts) < 2 or not parts[0] or not parts[1]:
        raise ValueError("Invalid GitHub repository URL.")
    return parts[0], parts[1]


def _create_askpass_script() -> Path:
    suffix = ".cmd" if os.name == "nt" else ".sh"
    handle = tempfile.NamedTemporaryFile("w", suffix=suffix, delete=False, encoding="utf-8")
    script_path = Path(handle.name)
    if os.name == "nt":
        handle.write(
            "@echo off\n"
            "echo %* | findstr /I \"Username\" >nul\n"
            "if %errorlevel%==0 (\n"
            "  echo %GIT_USERNAME%\n"
            ") else (\n"
            "  echo %GIT_PASSWORD%\n"
            ")\n"
        )
    else:
        handle.write(
            "#!/bin/sh\n"
            "case \"$1\" in\n"
            "  *Username*) printf '%s\\n' \"${GIT_USERNAME}\" ;;\n"
            "  *) printf '%s\\n' \"${GIT_PASSWORD}\" ;;\n"
            "esac\n"
        )
    handle.close()
    if os.name != "nt":
        script_path.chmod(script_path.stat().st_mode | stat.S_IXUSR)
    return script_path


def _sanitize_text(value: str, secret: str | None) -> str:
    if not value or not secret:
        return value
    return value.replace(secret, "***")


def clone_repository(repo_url: str, token: str | None) -> str:
    """Clone a GitHub repository into a temporary directory and return the path."""
    owner, repo = get_github_repo_info(repo_url)
    clone_url = f"https://github.com/{owner}/{repo}.git"
    temp_dir = tempfile.mkdtemp(prefix="codecity_clone_")
    askpass_path: Path | None = None
    env = {**os.environ, "GIT_TERMINAL_PROMPT": "0"}
    if token:
        askpass_path = _create_askpass_script()
        env.update(
            {
                "GIT_ASKPASS": str(askpass_path),
                "GIT_USERNAME": "x-access-token",
                "GIT_PASSWORD": token,
            }
        )

    LOGGER.info("[PRO] Cloning repository %s into %s", clone_url, temp_dir)
    try:
        subprocess.run(
            ["git", "clone", "--depth", "1", clone_url, temp_dir],
            check=True,
            capture_output=True,
            text=True,
            env=env,
        )
        LOGGER.info("[PRO] Repository cloned successfully.")
        return temp_dir
    except subprocess.CalledProcessError as error:
        stderr_text = _sanitize_text(error.stderr or "", token)
        shutil.rmtree(temp_dir, onerror=on_rm_error)
        if AUTH_ERROR_RE.search(stderr_text):
            raise PermissionError(stderr_text or "Clone failed due to repository permissions.") from error
        raise RuntimeError(stderr_text or "git clone failed.") from error
    finally:
        if askpass_path and askpass_path.exists():
            askpass_path.unlink(missing_ok=True)


def _collect_local_module_names(local_repo_path: Path) -> set[str]:
    local_modules: set[str] = set()
    for root, dirs, files in os.walk(local_repo_path):
        dirs[:] = [directory for directory in dirs if directory != ".git"]
        root_path = Path(root)
        relative_parts = root_path.relative_to(local_repo_path).parts
        if relative_parts:
            local_modules.add(relative_parts[0])
        for file_name in files:
            if file_name.endswith(".py"):
                local_modules.add(Path(file_name).stem)
    return local_modules


def get_source_files_from_local(local_repo_path: str, max_files: int = MAX_FILES) -> list[dict]:
    """Fetch all supported source files from a local repository checkout."""
    repo_root = Path(local_repo_path).resolve()
    supported_extensions = {extension.lower() for extension in SUPPORTED_EXTENSIONS}
    local_modules = _collect_local_module_names(repo_root)
    source_files: list[dict] = []

    for root, dirs, files in os.walk(repo_root):
        dirs[:] = [directory for directory in dirs if directory != ".git"]
        root_path = Path(root)
        for file_name in files:
            extension = Path(file_name).suffix.lower()
            if extension not in supported_extensions:
                continue
            full_path = root_path / file_name
            source_files.append(
                {
                    "name": file_name,
                    "path": full_path.relative_to(repo_root).as_posix(),
                    "local_path": str(full_path),
                    "extension": extension,
                    "local_modules": local_modules,
                }
            )
            if len(source_files) >= max_files:
                LOGGER.warning(
                    "[PRO] Reached file limit of %s. Some files may be excluded.",
                    max_files,
                )
                return source_files
    return source_files


def _compute_git_churn(repo_root: str, relative_path: str) -> tuple[int, int]:
    churn = 0
    bug_churn = 0
    try:
        result = subprocess.run(
            ["git", "log", '--pretty=format:%H %s', "--", relative_path],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode != 0:
            LOGGER.debug("[PRO] git log failed for %s: %s", relative_path, result.stderr)
            return 0, 0

        lines = [line for line in result.stdout.splitlines() if line.strip()]
        churn = len(lines)
        bug_churn = sum(1 for line in lines if BUG_CHURN_RE.search(line))
    except subprocess.TimeoutExpired as error:
        LOGGER.debug("[PRO] git log timed out for %s: %s", relative_path, error)
    except Exception as error:
        LOGGER.debug("[PRO] Error computing churn for %s: %s", relative_path, error)
    return churn, bug_churn


def _count_local_python_imports(content: str, local_modules: set[str]) -> int:
    unique_imports: set[str] = set()
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("from .") or stripped.startswith("import ."):
            unique_imports.add(stripped)
            continue
        if stripped.startswith("import "):
            modules = stripped[len("import ") :].split(",")
            for module in modules:
                module_name = module.strip().split(" as ")[0].split(".")[0]
                if module_name and module_name in local_modules:
                    unique_imports.add(stripped)
                    break
        elif stripped.startswith("from "):
            module_name = stripped[len("from ") :].split(" import ", 1)[0].strip()
            root_name = module_name.split(".")[0]
            if root_name and root_name in local_modules:
                unique_imports.add(stripped)
    return len(unique_imports)


def analyze_file(file_info: dict, repo_root: str) -> dict | None:
    """Analyze a file for static metrics and git history features."""
    local_path = Path(file_info["local_path"])
    relative_path = str(file_info.get("path") or local_path.name).replace(os.sep, "/")

    try:
        content = local_path.read_text(encoding="utf-8", errors="ignore")
        byte_size = local_path.stat().st_size
    except Exception as error:
        LOGGER.debug("[PRO] Error reading %s: %s", local_path, error)
        return None

    non_empty_line_count = sum(1 for line in content.splitlines() if line.strip())
    function_list = []
    try:
        analysis = lizard.analyze_file(str(local_path))
        function_list = list(analysis.function_list)
    except Exception as error:
        LOGGER.debug("[PRO] Lizard failed for %s: %s", relative_path, error)

    complexity = (
        sum(function.cyclomatic_complexity for function in function_list) / len(function_list)
        if function_list
        else 1.0
    )
    function_count = len(function_list)
    avg_params = (
        sum(getattr(function, "parameter_count", 0) for function in function_list) / function_count
        if function_count
        else 0.0
    )
    churn, bug_churn = _compute_git_churn(repo_root, relative_path)
    extension = str(file_info.get("extension") or local_path.suffix.lower())
    local_modules = set(file_info.get("local_modules") or [])
    fan_out = _count_local_python_imports(content, local_modules) if extension == ".py" else 0

    return {
        "name": file_info["name"],
        "path": relative_path,
        "extension": extension,
        "size": non_empty_line_count,
        "byte_size": byte_size,
        "complexity": float(complexity),
        "function_count": function_count,
        "avg_params": float(avg_params),
        "depth": relative_path.count("/"),
        "churn": churn,
        "bug_churn": bug_churn,
        "fan_out": fan_out,
    }


def _complexity_color(complexity: float) -> str:
    if complexity <= 5:
        return "#00ffcc"
    if complexity <= 15:
        return "#00ff88"
    if complexity <= 30:
        return "#FFC300"
    if complexity <= 50:
        return "#ff9900"
    return "#ff4444"


def build_legacy_city_layout(file_records: list[dict]) -> list[dict]:
    """Build the legacy city-data layout used by the standalone script."""
    if not file_records:
        return []

    num_files = len(file_records)
    dynamic_area = max(150, int((num_files**0.5) * 45))
    sizes = [max(int(record.get("size", 0)), 1) for record in file_records]
    if sum(sizes) == 0:
        sizes = [1] * len(file_records)

    values = squarify.normalize_sizes(sizes, dynamic_area, dynamic_area)
    rects = squarify.squarify(values, 0, 0, dynamic_area, dynamic_area)

    city_data: list[dict] = []
    for index, record in enumerate(file_records):
        complexity = float(record.get("complexity", 1.0) or 1.0)
        city_record = dict(record)
        city_record.update(
            {
                "x": rects[index]["x"],
                "y": rects[index]["y"],
                "w": rects[index]["dx"],
                "d": rects[index]["dy"],
                "h": max(1.0, complexity * 2.0),
                "color": _complexity_color(complexity),
            }
        )
        city_data.append(city_record)
    return city_data


def build_city_from_github(repo_url: str, github_token: str | None) -> list[dict]:
    """Clone, scan, and return enriched per-file records for a GitHub repository."""
    if not github_token:
        LOGGER.warning(
            "[PRO] GITHUB_TOKEN not provided. Private repositories may fail and rate limits may apply."
        )

    owner, repo = get_github_repo_info(repo_url)
    LOGGER.info("[PRO] Fetching repository %s/%s", owner, repo)

    local_repo_path: str | None = None
    try:
        local_repo_path = clone_repository(repo_url, github_token)
        files = get_source_files_from_local(local_repo_path, MAX_FILES)
        LOGGER.info("[PRO] Found %s source files to analyze.", len(files))
        if not files:
            raise ValueError("No analyzable source files found in repository.")

        file_records: list[dict] = []
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            future_to_file = {
                executor.submit(analyze_file, file_info, local_repo_path): file_info
                for file_info in files
            }
            for index, future in enumerate(as_completed(future_to_file), start=1):
                file_info = future_to_file[future]
                LOGGER.info("[PRO] Analyzing [%s/%s]: %s", index, len(files), file_info["path"])
                try:
                    result = future.result()
                    if result is not None:
                        file_records.append(result)
                except Exception as error:
                    LOGGER.error("[ERROR] Exception analyzing %s: %s", file_info["path"], error)

        if not file_records:
            raise ValueError("No analyzable files could be processed.")

        LOGGER.info("[PRO] Scan complete for %s/%s", owner, repo)
        return sorted(file_records, key=lambda record: record.get("path", ""))
    finally:
        if local_repo_path and Path(local_repo_path).exists():
            LOGGER.info("[PRO] Cleaning up temporary directory: %s", local_repo_path)
            shutil.rmtree(local_repo_path, onerror=on_rm_error)


def main(argv: list[str]) -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    if not argv:
        LOGGER.error("[ERROR] Repository URL is required")
        return 1

    repo_url = argv[0]
    github_token = argv[1] if len(argv) > 1 else None
    try:
        file_records = build_city_from_github(repo_url, github_token)
        city_data = build_legacy_city_layout(file_records)
        output_path = Path(__file__).resolve().parent / "city_data2.json"
        output_path.write_text(json.dumps(city_data, indent=2), encoding="utf-8")
        LOGGER.info("[PRO] Legacy city data written to %s", output_path)
        return 0
    except Exception as error:
        LOGGER.exception("[ERROR] scanner2 failed: %s", error)
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
