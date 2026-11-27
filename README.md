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
