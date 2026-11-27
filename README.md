# python-fox-photos

A command-line program that fetches a random fox photo from the
[RandomFox API](https://randomfox.ca/floof/), lets you name it, give it a
score and a note, and save it to disk to look at again later.

## Setup and running

### Windows

```powershell
git clone https://github.com/KOguy64/python-fox-photos.git
cd python-fox-photos
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

If `activate` is blocked in PowerShell, run
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once, or use
`.venv\Scripts\activate.bat` from Command Prompt.

### macOS

```bash
git clone https://github.com/KOguy64/python-fox-photos.git
cd python-fox-photos
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

Check your Python version with `python3 --version`. If it's older than 3.12,
install a newer one (for example `sudo apt install python3.12 python3.12-venv`
and use `python3.12 -m venv .venv`), or use uv below, which downloads the
right version for you.

## Commands

Once it starts, type a command and press Enter. Type `help` to see them all,
or `help <command>` for one.

| Command          | What it does                                             |
| ---------------- | -------------------------------------------------------- |
| `get`            | Get a new fox from the API                               |
| `display`        | Show the current fox (press any key to close the window) |
| `name`           | Name the current fox, or show its name                   |
| `addnote`        | Give the current fox a score (0-10) and a note           |
| `readnote`       | Show the current fox's score and note                    |
| `editnote`       | Change the current fox's score and note                  |
| `save`           | Save the current fox                                     |
| `getlist`        | List all saved foxes                                     |
| `load <name>`    | Load a saved fox by its name                             |
| `del <name>`     | Delete a saved fox                                       |
| `help [command]` | Show all commands, or what one does                      |
| `exit`           | Quit (Ctrl+C or Ctrl+D also quit safely)                 |

Saved foxes go into the `files/` folder, and the list of them is kept in
`listdir.json`. Both are created on the first run.

## Tests and linting

With the virtual environment active:

```bash
python -m pytest
python -m ruff check .
```

The tests in `tests/test_api_caller.py` call the real API, so they need an
internet connection.

To replace the saved offline fox, delete `python_fox_photos/offline/` and run
`python -m python_fox_photos.api_caller`.
