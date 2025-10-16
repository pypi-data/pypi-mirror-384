#!/usr/bin/env python3
import argparse
import subprocess
import sys
from pathlib import Path
from watchfiles import watch

IGNORED_DIRS = {'.git', '.venv', '__pycache__'}


def run_once(cmd: list[str]) -> None:
    try:
        subprocess.run(cmd, check=False)
    except KeyboardInterrupt:
        raise
    except Exception as e:  # noqa: BLE001
        print(f"[watch] error running command: {e}", file=sys.stderr)


def watch_loop(cmd: list[str], debounce_ms: int, root: Path) -> int:
    print(f"[iuv] 👀 watching {root} recursively.")
    print(f"[iuv] command: {' '.join(cmd)}")
    print("[iuv] To rerun: change a file, or press Enter. To stop: Ctrl+C.")

    while True:
        run_once(cmd)
        try:
            for changes in watch(root, debounce=debounce_ms):  # type: ignore[arg-type]
                # Filter ignored directories manually
                filtered = [c for c in changes if not any(part in IGNORED_DIRS for part in Path(c[1]).parts)]
                if not filtered:
                    continue
                print(f"[iuv] {len(filtered)} change(s) detected -> rerun")
                break  # Exit inner loop to rerun
        except KeyboardInterrupt:
            print(f"\n[iuv] Paused. To rerun: change a file in {root}, or press Enter. To exit: Ctrl+C.")
            try:
                sys.stdin.readline()
            except KeyboardInterrupt:
                print("\n[iuv] stopped")
                return 0
    return 0


def resolve_target_path(raw: str) -> Path:
    p = Path(raw)
    try:
        return (Path.cwd() / p).resolve() if not p.is_absolute() else p.resolve()
    except Exception:
        return p


def find_watch_root(target_path: Path) -> Path:
    search_dir = target_path.parent
    for parent in [search_dir] + list(search_dir.parents):
        if (parent / 'pyproject.toml').exists():
            return parent
    return search_dir


def parse_args(argv):
    parser = argparse.ArgumentParser(prog='iuv', description='Simple uv watch wrapper.')
    parser.add_argument('--debounce', '-d', type=int, default=150, help='Debounce time in ms (default 150)')
    parser.add_argument('cmd', nargs=argparse.REMAINDER, help='iuv run <args...> -> executes `uv run <args...>` on changes')
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(sys.argv[1:] if argv is None else argv)
    if not args.cmd or args.cmd[0] != 'run':
        print('Usage: iuv run <script_or_module> [args...]', file=sys.stderr)
        return 1
    # Transform: iuv run foo.py --arg -> uv run foo.py --arg
    uv_cmd = ['uv', 'run'] + [c for c in args.cmd[1:] if c != '--']
    # Determine script path if first arg looks like a path (contains '/' or endswith .py)
    watch_root = Path.cwd()
    if len(args.cmd) > 1:
        target = args.cmd[1]
        if target.endswith('.py') or '/' in target or target.startswith('.'):
            resolved = resolve_target_path(target)
            watch_root = find_watch_root(resolved)
    return watch_loop(uv_cmd, args.debounce, watch_root)

if __name__ == "__main__":
    raise SystemExit(main())

