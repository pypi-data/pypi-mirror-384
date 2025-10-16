# iuv

Tiny wrapper that watches the current directory and reruns a Python target with `uv run` whenever files change.

[![CI](https://github.com/gueraf/iuv/actions/workflows/ci.yml/badge.svg)](https://github.com/gueraf/iuv/actions/workflows/ci.yml)

## Install
Persistent install with uv from head:
```
uv tool install git+https://github.com/gueraf/iuv.git
```

Local checkout + script (also installs uv if missing):
```
git clone https://github.com/gueraf/iuv.git
cd iuv
./install.sh
```

## Usage
From inside your project directory:
```
iuv run app.py
```
Or module mode:
```
iuv run -m package.module
```
Pass any additional args after the script/module:
```
iuv run script.py --flag value
```

On each relevant file change (excluding `.git`, `.venv`, `__pycache__`) the previous run finishes (not force killed) and the command is invoked again.

## Behavior
- Watches recursively from cwd
- Debounce default: 150ms (change with `--debounce 300`)
- Prints a short line when rerunning
- Errors just print; watcher keeps going
- Press `Enter` to manually trigger a rerun.

## Examples
```
iuv run main.py
iuv run -m mypkg.cli --help
iuv run examples/demo.py --foo bar
```

## Exit
Press `Ctrl+C` once to pause. From there, you can press `Enter` to rerun, or `Ctrl+C` again to exit.

## License
[MIT](https://github.com/gueraf/iuv/blob/main/LICENSE)
