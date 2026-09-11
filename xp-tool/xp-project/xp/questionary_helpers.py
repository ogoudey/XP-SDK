import questionary

HELP_TOKEN = "?"
import click

def answer_yes_or_no(prompt, help="No help provided.") -> bool:
    while True:
        raw = questionary.text(f"{prompt} (y/n, ? for help)").ask()
        if raw == HELP_TOKEN:
            print(f"\n{help}\n")
            continue
        if raw == "":
            return True

def ask_for_str(prompt, help="No help provided.", default="unknown"):
    while True:
        raw = questionary.text(f"{prompt}  (? for help)").ask()
        if raw == HELP_TOKEN:
            print(f"\n{help}\n")
            continue
        return raw