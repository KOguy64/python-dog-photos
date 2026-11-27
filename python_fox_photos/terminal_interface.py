"""terminal_interface: creates a new session: handles all input and output"""

import json
import tkinter as tk
from functools import wraps
from json import JSONDecodeError
from pathlib import Path

import requests as r
from PIL import Image, UnidentifiedImageError

from .api_caller import OFFLINE_PHOTO, OFFLINE_REPLY, get_photo_file, get_photo_url
from .fox_note import FoxNote, del_foxnote, load_foxnote, save_foxnote
from .saveload_manager import ListDir, load_listdir, save_listdir
from .utils import ScoreError, UnsafePathError, display_photo

API_URL = "https://randomfox.ca/floof/"
API_JSON_KEY = "image"

welcome_msg = """Welcome to python_fox_photos !
Getting your daily fox photo...
"""


def arg_num(*allowed):
    """Creates a decorator to check if a function is getting the correct amount of arguments"""

    def decorator(func):
        @wraps(func)
        def protected(self, *args):
            if len(args) not in allowed:
                print(
                    f"Sorry ! {func.__name__} only accepts {' or '.join([str(n) for n in allowed])} arguments."
                )
                return
            return func(self, *args)

        return protected

    return decorator


class Session:
    """Creates a new session that handles all user interaction"""

    def __init__(self, listdir_path: str = "listdir.json"):
        self.listdir_path = Path(listdir_path)
        if not self.listdir_path.exists():
            self.listdir = ListDir(Path("files"), {})
            self.update_metadata()
        else:
            try:
                self.listdir = load_listdir(self.listdir_path)
            except (ValueError, KeyError, TypeError):
                print(
                    "Current listdir is not a broken. Starting with empty list of foxes"
                )
                self.listdir = ListDir(Path("files"), {})
        self._current_foxnote: FoxNote | None = None
        self.cmd_map = {
            "get": self.get_new_photo,
            "display": self.display_photo,
            "addnote": self.add_note,
            "name": self.name,
            "readnote": self.read_note,
            "editnote": self.edit_note,
            "getlist": self.get_list,
            "save": self.save_photo,
            "del": self.del_photo,
            "load": self.load_photo,
            "help": self.help,
            "exit": self.exit,
        }
        self.exit_sig = False

    @arg_num(0, 1)
    def help(self, *arg):
        """
        If typed alone, help displays all commands and what they do
        If typed with a <cmd>, such as help display, you get what that command does!
        """
        if len(arg) == 0:
            print("Here's the list of all commands and what they do...")
            width = max(len(name) for name in self.cmd_map)
            for cmdtype, function in self.cmd_map.items():
                first, *rest = (function.__doc__ or "").splitlines()
                print(f"{cmdtype:<{width}} : {first}")
                for line in rest:
                    print(f"{'':<{width}}   {line}")

        elif len(arg) == 1:
            if arg[0] not in self.cmd_map:
                print(
                    "Couldn't find the command you asked for\nType 'help' for a list of all commands"
                )
                return
            print(f"Here's what {arg[0]} does...")
            print(f"{self.cmd_map[arg[0]].__doc__}")
        else:
            print("'help' only accepts zero or one arguments!")
            raise ValueError

    @property
    def current_foxnote(self) -> FoxNote:
        """Tries to get the current fox. If that doesn't exist, get a new one"""
        if not self._current_foxnote:
            print("No fox loaded yet! Getting one for you ...")
            self.get_new_photo()
        assert self._current_foxnote is not None
        return self._current_foxnote

    def update_metadata(self):
        """Update the system's record on what foxes are saved"""
        try:
            save_listdir(self.listdir, self.listdir_path)
        except OSError:
            print(
                "Couldn't save the list of foxes to the system. Check your permissions!"
            )

    @arg_num(0)
    def display_photo(self):
        """Display the currently loaded fox"""
        try:
            print("Press any key to close the window")
            display_photo(self.current_foxnote.img)
        except tk.TclError:
            print("Couldn't open a window to show the fox (no screen found)")

    @arg_num(0)
    def get_list(self):
        """Get a list of all saved foxes"""
        if not self.listdir.saved_files:
            print(
                "No saved foxes found !\nIf you want to get one, type 'get'\nIf you want to save the current one, type 'save'"
            )
            return
        out = "Saved foxes: "
        for name in self.listdir.saved_files:
            out += f"\n\t{name}"
        print(out)
        print("If you would like to load one, type 'load <name>'")

    @arg_num(0)
    def add_note(self):
        """Add a score and a note to the current fox"""
        print("New note...")
        while True:
            try:
                score = float(input("Score? (0-10, decimals allowed): "))
                note_str = input("Note: ")
                self.current_foxnote.add_metadata(note_str, score)
            except (ValueError, ScoreError):
                print("Please give a score between 0 - 10. Try again!")
            else:
                break

    @arg_num(0)
    def name(self):
        """Give the current fox a name or read it's name!"""
        if self.current_foxnote.name:
            print(f"The fox's name is {self.current_foxnote.name}")
            return
        self.current_foxnote.name = input(
            "Warning! Foxs' names can't be changed\nName the current fox: "
        )

    @arg_num(0)
    def read_note(self):
        """Read the current fox's note"""
        if not self.current_foxnote.has_metadata:
            print("Add some notes and scores before you edit it!")
        else:
            print(f"Note: {self.current_foxnote.note}")
            print(f"Score: {self.current_foxnote.score}")

    @arg_num(0)
    def edit_note(self):
        """Edit the score and note of the current fox"""
        if not self.current_foxnote.has_metadata:
            print("Add some notes and scores before you edit it!")
        else:
            print("Old note...")
            print(f"Note: {self.current_foxnote.note}")
            print(f"Score: {self.current_foxnote.score}")
            print()
            self.add_note()

    @arg_num(0)
    def get_new_photo(self, api_url=API_URL, api_json_key=API_JSON_KEY):
        """Get a new photo from the API"""
        print("Getting a new fox...")
        try:
            photo_url = get_photo_url(api_url, api_json_key)
            print(f"API reponsded, fetching fox from {photo_url}...")
            photo_file = get_photo_file(photo_url)
            print("Fox gotten!")
            self._current_foxnote = FoxNote(photo_file)

            if input("If you would like to display it, type y: ") == "y":
                self.display_photo()
        except r.ConnectionError:
            print("Got a connection error. Check your internet")
            self.load_offline_photo()
        except r.Timeout:
            print(
                "Got a timeout, please check your internet or if the server is still up"
            )
            self.load_offline_photo()
        except r.HTTPError:
            print("Failed to get link, please check if the server is still working")
        except r.JSONDecodeError:
            print(
                "Couldn't decode to json, please check that the server is still working"
            )
        except KeyError:
            print(
                "Couldn't find the key to get the url in the json. Please check that the API you're calling and key is correct"
            )
        except UnidentifiedImageError:
            print("Image couldn't be loaded. Please check that the server is working")

    def load_offline_photo(self):
        """Load the fox saved in the package, for when there's no internet"""
        if not (OFFLINE_REPLY.exists() and OFFLINE_PHOTO.exists()):
            print("No offline fox saved either, sorry!")
            return
        try:
            reply = json.loads(OFFLINE_REPLY.read_text())
            img = Image.open(OFFLINE_PHOTO)
            img.load()
        except (OSError, JSONDecodeError):
            print("The offline fox is broken, sorry!")
            return
        print(f"You're offline, so here's our saved fox: {reply.get(API_JSON_KEY)}")
        self._current_foxnote = FoxNote(img)

    @arg_num(1)
    def load_photo(self, name):
        """Call load <name>, load one of your saved foxes by its name"""
        if name not in self.listdir.saved_files:
            print("Sorry, there's no fox with that name!")
            return
        saved_note = self.listdir.saved_files[name]
        try:
            path = self.listdir.resolve_path(Path(saved_note["path"]))
        except UnsafePathError:
            print("Sorry, that fox is outside your fox folder. Deleting the entry...")
            self.del_photo(name)
            return
        has_metadata = saved_note["has_metadata"]

        self._current_foxnote = load_foxnote(path, name, has_metadata)
        print(f"{name} the fox has been loaded!")

    @arg_num(0)
    def save_photo(self):
        """Save the current fox to memory, and update the listing"""
        if not self.current_foxnote.name:
            print("Name the current fox before you save it...")
            self.name()

        path = Path(input(f"Where should I save this in {self.listdir.main_dir}?: "))
        try:
            full_path = self.listdir.resolve_path(path)
        except UnsafePathError:
            print(f"Sorry, foxes can only be saved inside {self.listdir.main_dir}")
            return
        save_foxnote(self.current_foxnote, full_path)
        self.listdir.add_file(self.current_foxnote, path)
        self.update_metadata()

    @arg_num(1)
    def del_photo(self, name):
        """Delete a fox from memory. They'll be sad though."""
        if name not in self.listdir.saved_files:
            print("We don't have that fox saved!")
            return
        entry = self.listdir.saved_files[name]
        has_metadata = entry["has_metadata"]
        try:
            path = self.listdir.resolve_path(Path(entry["path"]))
        except UnsafePathError:
            # Never touch files outside main_dir, only forget the entry
            self.listdir.remove_file(name)
            self.update_metadata()
            return
        del_foxnote(path, has_metadata)
        self.listdir.remove_file(name)
        self.update_metadata()

    @arg_num(0)
    def exit(self):
        """Exit the program (the foxes will miss you !)"""
        self.update_metadata()
        print("Thanks for using python_fox_photos!")
        self.exit_sig = True

    def process_cmd(self, cmd: str):
        """Process an input string and call its command with arguments"""
        print()
        inputs = cmd.split(" ")
        if len(inputs) == 1:
            command = inputs[0]
            self.cmd_map[command]()
        else:
            command, *arg = inputs
            self.cmd_map[command](*arg)
        print("\n-------------------\n")

    def start(self):
        """Start the session"""
        print(welcome_msg)
        self.get_new_photo()
        print("\n-------------------\n")
        self.help()
        print("\n-------------------\n")
        while not self.exit_sig:
            self.process_cmd(input("What do you wanna do?\nType a command:"))


if __name__ == "__main__":
    session = Session("listdir.json")
    session.start()
