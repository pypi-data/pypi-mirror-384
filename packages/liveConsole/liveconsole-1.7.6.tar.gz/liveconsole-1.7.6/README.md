# PYSOLE

## You can finally test your code in real time without using idle!
### If you found [this repository](https://github.com/TzurSoffer/Pysole) useful, please give it a ⭐!.

## Showcase (click to watch on Youtube)
[![Watch the demo](Showcase/thumbnail.png)](https://www.youtube.com/shorts/pjoelNjc3O0)


Table of contents

- Features
- Installation
- Usage
- Parameters
- Keyboard Shortcuts
- Troubleshooting/Notes
- Contributing
- License

## Features

Pysole provides a compact but powerful set of features designed to make interactive debugging and live testing fast and pleasant.

1. Live GUI console (syntax highlighting)
    - Real-time syntax highlighting using Pygments.
    - Monokai style by default, configurable through themes.

2. Autocomplete & suggestions
    - Autocomplete for Python keywords, built-ins and variables in scope.
    - Popup suggestions after typing (configurable behavior) and insert-on-confirm.

3. Run remaining script code at startup
    - `runRemainingCode=True` will execute the remainder of the calling script after `probe()` is invoked.
    - `printStartupCode=True` prints the captured code chunks as they execute.

4. Thread-safe execution + output capture
    - User code runs in a background thread to avoid blocking the GUI.
    - `stdout` and `stderr` are redirected into the GUI console output area.

5. Multi-line input, indentation & history
    - Shift+Enter inserts a newline with proper indentation.
    - Command history with clickable entries for easy reuse.

6. Integrated Help Panel and Features tab
    - Right-hand help panel shows `help(obj)` output.
    - A Features view is available from the File menu and shows the built-in features summary.

7. Themes & persistent settings
    - Theme picker in the File menu; selected theme is written to `settings.json`.
    - Settings (THEME, BEHAVIOR, FONT) are loaded at startup from `src/pysole/settings.json`.


## Installation

Quick install

```powershell
pip install liveConsole
```

Notes: the package is published under the name `liveConsole` (see `pyproject.toml`).

If you prefer to install from source, clone this repo and run:

```powershell
pip install -e .
```

Command-line entry points

After installation, two console commands are provided:

- `pysole` — open the GUI console (same as `liveconsole`)
- `liveconsole` — open the GUI console


## Usage

Programmatic usage (embed in scripts):

- Basic, automatic caller capture:
```python
import pysole
pysole.probe()
```

- Run the remaining code in the current file inside the console and print the code as it executes
```python
pysole.probe(runRemainingCode=True, printStartupCode=True)
```

- Override appearance and prompt
```python
pysole.probe(primaryPrompt='PY> ', font='Consolas', fontSize=14)
```

## Parameters

This section documents the parameters accepted by `pysole.probe()` and the `InteractiveConsole` constructor in `src/pysole/pysole.py`. Most of these parameters are optional; reasonable defaults are taken from the calling frame and `settings.json`.

Note: `probe(...)` forwards its arguments to `InteractiveConsole(...)` so you can pass any of the parameters below to `probe()` directly.

runRemainingCode
- Meaning: When `True`, Pysole will read the remainder of the source file that contains the `probe()` call and run those lines inside the console's namespace.
- Type: bool
- Default: `False`
- Behavior: The implementation inspects `callerFrame.f_code.co_filename` for the filename and `callerFrame.f_lineno` for the line number where `probe()` was called. Lines after that line are captured into `startupCode` and executed on console startup.
- Caution: This requires the source file to be readable from disk (not packaged/compiled away). Large files will be read into memory.

printStartupCode
- Meaning: Controls how the startup code (captured by `runRemainingCode=True`) is executed: printed chunk-by-chunk to the console and executed interactively, or executed silently.
- Type: bool
- Default: `False`
- Behavior: If `True`, the startup code is split into logical top-level chunks (top-level statements and their indented blocks). Each chunk is printed and executed sequentially so you can see what runs. If `False`, the entire remaining code is executed silently in one go (but output is still captured and shown).

primaryPrompt
- Meaning: Overrides the primary prompt string (for example `>>>`). This updates the in-memory `BEHAVIOR['PRIMARY_PROMPT']` used by the console and the default can also be changed in the settings file directly.
- Type: string
- Default: The prompt value defined in `settings.json` under `BEHAVIOR -> PRIMARY_PROMPT`.
- Notes: Passing this parameter changes the prompt for the current session only.

font
- Meaning: Overrides the font family used in console widgets.
- Type: string (font family name, e.g. "Consolas", "Courier New")
- Default: The font specified by `settings.json` -> `THEME` -> `FONT`.

fontSize
- Meaning: Overrides the font size used in console widgets.
- Type: int (font size in points / pixels depending on the platform and Tk configuration)
- Default: Value from `settings.json` -> `THEME` -> `FONT_SIZE`.

removeWaterMark
- Meaning: Controls whether a short welcome watermark message (with a GitHub link and request to star the project) is printed at startup.
- Type: bool
- Default: `False` (watermark shown)

userGlobals
- Meaning: The `globals()` mapping that the console will use as its global namespace. Variables, functions, and imports in this mapping will be visible to code executed in the console.
- Type: dict-like (typically the dict returned by `globals()`)
- Default: If omitted, the console infers the caller's globals using `callerFrame.f_globals` (or from `inspect.currentframe().f_back` if `callerFrame` is also omitted).
- When to pass: Provide this when you want the console to operate on a specific module or custom namespace.

userLocals
- Meaning: The `locals()` mapping used as the console's local namespace. Local variables available at the call site will be visible here.
- Type: dict-like (typically the dict returned by `locals()`)
- Default: Inferred from the caller's frame (`callerFrame.f_locals`) if not provided.

callerFrame
- Meaning: An `inspect` frame object used to infer both `userGlobals` and `userLocals` when they are not supplied. It's also used to determine the source file and line number for the "run remaining code" feature.
- Type: frame object (as returned by `inspect.currentframe()` and `frame.f_back`)
- Default: If omitted, `probe()` sets `callerFrame = inspect.currentframe().f_back` to automatically capture the frame of the caller.
- When to pass: Use an explicit frame when calling `probe()` from helper wrappers or non-standard contexts where automatic frame detection would be wrong.

Behavioral notes and edge cases
- `probe()` replaces `sys.stdout`, `sys.stderr`, and `sys.stdin` with console-aware redirectors while the console is running. These streams are restored when the console's `onClose()` runs (but be mindful when embedding Pysole in larger apps).
- If `runRemainingCode=True` but the source file cannot be read (packaged app, missing file, permission issues), the attempt to read the file will fail — in that case either run Pysole without `runRemainingCode` or pass an explicit `startupCode` (if you extend the API).
- When `printStartupCode=True`, chunks are determined by top-level lines (zero indent) and their following indented lines. This makes printed execution easier to follow for functions, classes and loops.

## Keyboard Shortcuts

| Key | Action |
| --- | --- |
| `Enter` | Execute command (if complete) |
| `Shift+Enter` | Insert newline with auto-indent |
| `Tab` | Complete the current word / show suggestions |
| `Up/Down` | Navigate suggestion list |
| `Escape` | Hide suggestions |
| `Ctrl Click` | open help panel on the current method/func/class... |


## Troubleshooting/Notes

Behavioral notes and edge cases

- `probe()` temporarily replaces `sys.stdout`, `sys.stderr` and `sys.stdin` with redirectors that send text to the GUI console. These are restored on close (`onClose()`). Embedding Pysole in larger apps should take this into account.
- `runRemainingCode=True` requires the calling module's source file to be available on disk. Running this in frozen/packaged environments may fail.
- `printStartupCode=True` prints chunks determined by top-level statements (zero indent) and their indented blocks so function/class/loop definitions are grouped with their bodies.

Settings and themes

Default UI and behavior settings are loaded from `src/pysole/settings.json` (path built from `src/pysole/utils.py`). Themes are listed in `src/pysole/themes.json`. The in-app Theme Picker writes the selected theme back to `settings.json` to persist across sessions.

Troubleshooting

- If the GUI doesn't start, make sure `customtkinter` is installed for your Python version.
- On Linux, ensure your Tk/Tcl support is present (system package) and `DISPLAY` is set when running headful UIs.
- If `runRemainingCode` appears to run the wrong code, check where `probe()` is called (wrappers can shift the caller frame). Use `callerFrame=` to pass an explicit frame if needed.

## Contributing

- Bug reports and PRs welcome. Please open issues on the upstream GitHub repository: https://github.com/TzurSoffer/Pysole
- Keep test changes small and focused. Include a short description of the error / feature and steps to reproduce.

Changelog (high level)

- See `pyproject.toml` for the current package version.

## License

This project is available under the MIT license — see the `LICENSE` file in the repository root.

