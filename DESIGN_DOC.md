# Plan
Main functionality:
Get dog photos from internet
Save and note dog photos on disk (notes are saved as note.txt in the same directory as the photo, photos without notes don't get their own directories)


# Checklist
1. It runs (S5). From a fresh clone with Python 3.12 or newer, python main.py
or python -m &lt;package&gt; starts it. The README says how to run it on 
Windows and on macOS. 

We'll see

2. Classes (S2–S4). At least 3 classes, each with one clear job. Use a
dataclass, @property or a dunder such as __str__. Use composition or
inheritance where it fits.

Classes for:
Loading photos from API : Loader -> DogImage (data (raw jpeg) , url)
Saving photos w/ notes : DogImage -> DogNote (DogImage, name, note), and updates a JSON metadata file that stores paths of all DogNotes (or creates it)

3. A package (S5). A package folder with 2 or more modules, and if __name__
== &quot;__main__&quot;:.
module for each class specified
if name == loader: loads a dog photo and displays it
if name == saver: loads one of the saved dog photos

4. Errors (S6). Bad input or a missing or broken file never crashes the program
with a traceback.
Potential Errors to track with tests:
Dog API doesn't work
DogImage is corrupted/isn't valid jpeg
Can't save notes to specified path (no priv?), can't save metadata

5. Files (S7). It saves its data to CSV or JSON with pathlib and loads it back
on the next run.
JSON metadata: stores list of paths, names, and has_note?

6. Advanced Python (S9). You write at least one generator, decorator or
context manager yourself.
Decorator - opens DogNote protectedly (without throwing any errors)

7. Tests (S10). At least 8 pytest tests for normal cases, limits and bad input.
python -m pytest passes.
See S6.

8. Code quality and Git (S11). PEP 8 names, docstrings and a .gitignore,
and python -m ruff check . is clean. Alone: at least 5 commits with clear
messages. Team: work on branches, merge at least one pull request, and
every member’s commits show in the history.

9. Bonus (S12). Use one public API that needs no key. Save a JSON copy of a
reply so the program also works offline.
DogImage API

10. Talk (S15). 7 minutes with a live demo, then 5 minutes of questions. Explain
one design choice and one bug you fixed. In a team, everyone presents and
answers questions.

Design Choice

Bug Fix
