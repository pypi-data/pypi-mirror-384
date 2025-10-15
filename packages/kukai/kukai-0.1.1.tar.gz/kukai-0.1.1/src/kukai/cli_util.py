import inquirer
import os
from pathlib import Path
from typing import Optional


def get_inq_group(data: dict) -> str:
    selected = "back"
    while selected == "back":
        sel_key = get_inq_key(data)
        if sel_key:
            selected = get_inq_list(sel_key)
        else:
            selected = ""
    return selected


def get_inq_key(data: dict) -> Optional[list]:
    selection = []
    for key in data:
        sel = ("--> " + key, key)
        selection.append(sel)
    selection.append(("exit", "exit"))
    question = [
        inquirer.List(
            "group", message="Template Menu", choices=selection, carousel=True
        ),
    ]
    answer = inquirer.prompt(question)
    sel_group = answer["group"]
    if sel_group == "exit":
        return None
    return data[sel_group]


def get_inq_list(data: list) -> str:
    os.system("clear")
    selection = []
    for element in data:
        sel = (" * " + element, element)
        selection.append(sel)
    selection.append(("<- back", "back"))
    question = [
        inquirer.List(
            "element", message="Template Menu", choices=selection, carousel=True
        ),
    ]
    answer = inquirer.prompt(question)
    ret = answer["element"]
    return ret


def create_inq_list(data: dict):
    os.system("clear")
    folder = Path()
    parsed = data
    selection = []
    for s in parsed["sub"]:
        sel = ("--> " + s, s)
        selection.append(sel)
    for s in parsed["template"]:
        sel = (" * " + s, s)
        selection.append(sel)
    question = [
        inquirer.List(
            "template", message="Template Menu", choices=selection, carousel=True
        ),
    ]
    answer = inquirer.prompt(question)
    ret = answer["template"]
    if answer["template"] in parsed["sub"]:
        ret += "/"
        ret += create_inq_list(folder / answer["template"])
    return ret


def path_complete(text, state):
    cwd = os.getcwd()
    selection = []
    for path in Path(cwd).iterdir():
        if path.is_dir():
            selection.append(path.name)
    return selection[state % len(selection)]


def get_path():
    question = [
        inquirer.Text(
            "path",
            message="Enter Destination path",
            autocomplete=path_complete,
        ),
    ]
    answer = inquirer.prompt(question)
    return Path(answer["path"])
