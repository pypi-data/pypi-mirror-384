#!/usr/bin/env python
# project_to_markdown.py
# Export a (filtered) project into a single Markdown file with a tree view and code fences.
# Includes:
# - Robust extension matching (".py", "py", "*.py" all work)
# - Git-aware collection (respects .gitignore / tracked-only) when requested
# - Default directory/file excludes (e.g., .venv, .idea, node_modules, __pycache__, etc.)
# - Safe Markdown generation (language fences, backtick-escape, UTF-8 guard, optional line cap)
# - Optional tree that exactly mirrors the included files (so it matches gitignore/filters)

from __future__ import annotations

import argparse
import fnmatch
import io
import shutil
import subprocess
from pathlib import Path
from typing import Iterable, List, Tuple

# ---------- Defaults ----------

DEFAULT_INCLUDED_EXTS = ".py,.md"

DEFAULT_EXCLUDED_DIRS = {
    ".git", ".hg", ".svn",
    ".venv", "venv", ".env",
    ".idea", ".vscode",
    "__pycache__", ".mypy_cache", ".pytest_cache", ".ruff_cache", ".tox",
    ".eggs", "dist", "build",
    ".cache", ".ipynb_checkpoints",
    "site-packages", "node_modules",
}

DEFAULT_EXCLUDED_FILES = {
    ".DS_Store", "Thumbs.db",
}

_EXT_TO_LANG = {
    ".py": "python", ".md": "markdown", ".json": "json", ".yml": "yaml", ".yaml": "yaml",
    ".toml": "toml", ".ini": "", ".cfg": "", ".txt": "", ".sh": "bash",
    ".js": "javascript", ".ts": "typescript", ".html": "html", ".css": "css",
}


# ---------- CLI ----------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export a project into a single Markdown file."
    )
    parser.add_argument(
        "-r", "--root", type=Path, default=Path.cwd(),
        help="Root directory of the project to export",
    )
    parser.add_argument(
        "-o", "--output", type=Path, default=Path("project_export.md"),
        help="Output Markdown file",
    )
    parser.add_argument(
        "-t", "--title", type=str, default="Project Documentation",
        help="Title for the Markdown document",
    )
    parser.add_argument(
        "--include-exts", type=str, default=DEFAULT_INCLUDED_EXTS,
        help="Comma-separated list of file extensions/patterns to include "
             '(accepts forms like ".py", "py", "*.py").',
    )
    parser.add_argument(
        "--exclude-dirs", type=str, default="",
        help="Comma-separated list of directory names (fnmatch patterns) to exclude",
    )
    parser.add_argument(
        "--exclude-files", type=str, default="",
        help="Comma-separated list of file names (fnmatch patterns) to exclude",
    )
    parser.add_argument(
        "--no-default-excludes", action="store_true",
        help="Do NOT apply the built-in default exclude patterns for dirs/files.",
    )
    parser.add_argument(
        "--use-gitignore", action="store_true",
        help="Use Git to respect .gitignore (and optionally include untracked files).",
    )
    parser.add_argument(
        "--all-files", action="store_true",
        help="When used with --use-gitignore, include untracked files (still respecting ignore).",
    )
    parser.add_argument(
        "--tree-from-files", action="store_true",
        help="Build the project tree from the INCLUDED FILES (so it mirrors gitignore/filters).",
    )
    parser.add_argument(
        "--max-bytes", type=int, default=10_000_000,
        help="Maximum size of files to include (in bytes).",
    )
    parser.add_argument(
        "--max-lines", type=int, default=0,
        help="Maximum number of lines to include per file (0 = unlimited).",
    )
    return parser.parse_args()


# ---------- Helpers ----------

def _normalize_ext_patterns(raw_exts: Iterable[str]) -> List[str]:
    """
    Accepts forms like '.py', 'py', '*.py', '.md', 'md', '*.md'.
    Produces a list of fnmatch patterns against lowercase filenames.
    """
    patterns: List[str] = []
    for e in raw_exts:
        e = e.strip().lower()
        if not e:
            continue
        if any(ch in e for ch in "*?[]"):
            patterns.append(e)           # already a pattern
        elif e.startswith("."):
            patterns.append(f"*{e}")     # ".py" -> "*.py"
        else:
            patterns.append(f"*.{e}")    # "py"  -> "*.py"
    return patterns


def _matches_ext(path: Path, patterns: List[str]) -> bool:
    if not patterns:
        return True
    name = path.name.lower()
    return any(fnmatch.fnmatch(name, pat) for pat in patterns)


def _escape_backticks(s: str) -> str:
    # Prevent breaking fences by inserting a zero-width char inside any triple-backticks.
    return s.replace("```", "``\u200b`")


def _is_git_repo(root: Path) -> bool:
    if shutil.which("git") is None:
        return False
    try:
        out = subprocess.check_output(
            ["git", "-C", str(root), "rev-parse", "--is-inside-work-tree"],
            text=True, stderr=subprocess.DEVNULL
        ).strip()
        return out == "true"
    except Exception:
        return False


def _git_repo_toplevel(root: Path) -> Path | None:
    if shutil.which("git") is None:
        return None
    try:
        out = subprocess.check_output(
            ["git", "-C", str(root), "rev-parse", "--show-toplevel"],
            text=True, stderr=subprocess.DEVNULL
        ).strip()
        return Path(out) if out else None
    except Exception:
        return None


def _git_ls_files(root: Path, include_untracked: bool) -> List[Path]:
    """
    Return files under 'root' using Git (respects .gitignore).
    Includes tracked files; and if include_untracked=True, untracked-but-not-ignored too.
    """
    if shutil.which("git") is None:
        return []

    # Ensure we only list files under 'root' even if 'root' is a subdir of the repo.
    repo_root = _git_repo_toplevel(root)
    if repo_root is None:
        return []

    rel = "." if repo_root.samefile(root) else str(root.resolve().relative_to(repo_root.resolve()))
    cmd = ["git", "-C", str(root), "ls-files"]
    if include_untracked:
        cmd = ["git", "-C", str(root), "ls-files", "--cached", "--others", "--exclude-standard"]
    cmd += ["--", rel]
    try:
        out = subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL)
        paths = []
        # 'git -C root ...' prints paths relative to repo top-level; rebuild absolute paths:
        for line in out.splitlines():
            line = line.strip()
            if not line:
                continue
            abs_p = repo_root / line
            try:
                # Keep only files inside 'root'
                if abs_p.resolve().is_file() and abs_p.resolve().is_relative_to(root.resolve()):
                    paths.append(abs_p)
            except AttributeError:
                # Python < 3.9 compatibility: manual check
                rp = abs_p.resolve()
                rr = root.resolve()
                if str(rp).startswith(str(rr)) and rp.is_file():
                    paths.append(abs_p)
        return paths
    except Exception:
        return []


# ---------- Core ----------

def build_tree_from_scan(
    root: Path,
    exclude_dirs: set,
    exclude_files: set,
    include_patterns: List[str],
    max_bytes: int,
) -> List[Tuple[Path, bool]]:
    """
    Filesystem scan producing a list of (Path, is_dir) entries for a tree view.
    Honors ancestor dir excludes, file excludes, ext patterns, and size.
    """
    structure: List[Tuple[Path, bool]] = []
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            continue
        if path.is_dir():
            # Exclude if this dir or any ancestor matches a pattern
            if any(fnmatch.fnmatch(path.name, pat) for pat in exclude_dirs):
                continue
            if any(any(fnmatch.fnmatch(parent.name, pat) for pat in exclude_dirs) for parent in path.parents):
                continue
            structure.append((path, True))
        else:
            # File gatekeeping
            if any(any(fnmatch.fnmatch(parent.name, pat) for pat in exclude_dirs) for parent in path.parents):
                continue
            if any(fnmatch.fnmatch(path.name, pat) for pat in exclude_files):
                continue
            if include_patterns and not _matches_ext(path, include_patterns):
                continue
            try:
                if max_bytes and path.stat().st_size > max_bytes:
                    continue
            except OSError:
                continue
            structure.append((path, False))
    return structure


def build_tree_from_files(root: Path, files: List[Path]) -> List[Tuple[Path, bool]]:
    """
    Build a tree that *exactly* reflects the provided files collection (and their parent dirs).
    """
    paths: set[Path] = set()
    for f in files:
        if not f.exists() or not f.is_file():
            continue
        paths.add(f)
        # Add all parents up to root
        p = f.parent
        while True:
            if p == root or not p.is_dir():
                paths.add(p)
                break
            paths.add(p)
            p = p.parent

    # Normalize to a list of (Path, is_dir)
    entries: List[Tuple[Path, bool]] = []
    for p in sorted(paths):
        try:
            entries.append((p, p.is_dir()))
        except OSError:
            continue
    return entries


def render_tree_markdown(root: Path, structure_paths: List[Path]) -> str:
    # Flat tree (one item per line). Lightweight and predictable.
    lines = []
    for path in structure_paths:
        try:
            rel = path.relative_to(root)
        except Exception:
            # If path isn't under root (shouldn't happen), skip
            continue
        is_dir = path.is_dir()
        lines.append(f"- {'📁' if is_dir else '📄'} {rel}")
    return "\n".join(lines)


def collect_files(
    root: Path,
    include_patterns: List[str],
    exclude_dirs: set,
    exclude_files: set,
    use_gitignore: bool,
    all_files: bool,
    max_bytes: int,
) -> List[Path]:
    """
    Collect actual files to export. Prefer Git when asked, else fallback to rglob.
    """
    def candidate_files() -> List[Path]:
        if use_gitignore and _is_git_repo(root):
            gf = _git_ls_files(root, include_untracked=all_files)
            if gf:
                # Already filtered by .gitignore via Git, but we still apply size/ext/name filters.
                return [p for p in gf if p.is_file()]
        # Fallback: filesystem walk
        return [p for p in root.rglob("*") if p.is_file() and not p.is_symlink()]

    results: List[Path] = []
    for path in sorted(candidate_files()):
        # Ancestor dir excludes
        if any(any(fnmatch.fnmatch(parent.name, pat) for pat in exclude_dirs) for parent in path.parents):
            continue
        # File name excludes
        if any(fnmatch.fnmatch(path.name, pat) for pat in exclude_files):
            continue
        # Extension / pattern filter
        if include_patterns and not _matches_ext(path, include_patterns):
            continue
        try:
            size = path.stat().st_size
        except OSError:
            continue
        if max_bytes and size > max_bytes:
            continue
        results.append(path)
    return results


def write_markdown(
    root: Path,
    files: List[Path],
    tree_md: str,
    out_path: Path,
    title: str,
    max_lines: int = 0,
) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with io.open(out_path, "w", encoding="utf-8") as md_file:
        # Title
        md_file.write(f"# {title}\n\n")

        # Tree
        md_file.write("## Project Structure\n")
        md_file.write(tree_md)
        md_file.write("\n\n")

        # Files
        for fp in files:
            rel = fp.relative_to(root)
            md_file.write(f"## {rel}\n")
            lang = _EXT_TO_LANG.get(fp.suffix.lower(), "")
            try:
                with io.open(fp, "r", encoding="utf-8") as src:
                    content = src.read()
            except UnicodeDecodeError:
                md_file.write("_Skipped (not UTF-8 text file)._  \n\n")
                continue

            # Truncate by lines if requested
            if max_lines and max_lines > 0:
                lines = content.splitlines(keepends=True)
                if len(lines) > max_lines:
                    content = "".join(lines[:max_lines]) + "\n\n<!-- truncated -->\n"

            content = _escape_backticks(content)
            fence = f"```{lang}\n" if lang else "```\n"
            md_file.write(fence)
            md_file.write(content)
            md_file.write("\n```\n\n")


# ---------- Main ----------

def main() -> None:
    args = parse_args()

    root: Path = args.root.resolve()
    if not root.exists() or not root.is_dir():
        raise SystemExit(f"[error] Root directory not found: {root}")

    # Include patterns
    include_exts_raw = {e.strip().lower() for e in args.include_exts.split(",") if e.strip()}
    include_patterns = _normalize_ext_patterns(include_exts_raw)

    # Excludes (dirs/files): merge user + defaults unless disabled
    user_ex_dirs = {d.strip() for d in args.exclude_dirs.split(",") if d.strip()}
    user_ex_files = {f.strip() for f in args.exclude_files.split(",") if f.strip()}

    exclude_dirs = set(user_ex_dirs) if args.no_default_excludes else (set(DEFAULT_EXCLUDED_DIRS) | set(user_ex_dirs))
    exclude_files = set(user_ex_files) if args.no_default_excludes else (set(DEFAULT_EXCLUDED_FILES) | set(user_ex_files))

    # Collect files first (so tree can mirror exactly if requested)
    files = collect_files(
        root=root,
        include_patterns=include_patterns,
        exclude_dirs=exclude_dirs,
        exclude_files=exclude_files,
        use_gitignore=args.use_gitignore,
        all_files=bool(args.all_files),
        max_bytes=int(args.max_bytes),
    )

    # Build tree entries
    if args.tree_from_files:
        structure_entries = build_tree_from_files(root, files)
    else:
        structure_entries = build_tree_from_scan(
            root=root,
            exclude_dirs=exclude_dirs,
            exclude_files=exclude_files,
            include_patterns=include_patterns,
            max_bytes=int(args.max_bytes),
        )

    structure_paths = [p for p, _is_dir in structure_entries]
    tree_md = render_tree_markdown(root, structure_paths)

    # Write Markdown
    out_path: Path = args.output if args.output.is_absolute() else Path.cwd() / args.output
    write_markdown(root, files, tree_md, out_path, title=args.title, max_lines=int(args.max_lines))

    print(f"[ok] Wrote {len(files)} files into: {out_path}")


if __name__ == "__main__":
    main()
