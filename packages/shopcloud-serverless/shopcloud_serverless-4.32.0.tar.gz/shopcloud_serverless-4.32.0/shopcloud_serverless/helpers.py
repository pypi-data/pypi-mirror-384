from typing import Optional


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def ask_for(variable: str, default: Optional[str] = None) -> str:
    d = '' if default is None else f' ({default})'
    v = input(f'{variable}{d}:') \
        .replace('\n', ' ') \
        .replace('\r', '') \
        .strip()
    if v == '' and default is not None:
        return default
    return v


def ask_for_yes_no(question: str):
    v = input(f'{question} (y/n):') \
        .replace('\n', ' ') \
        .replace('\r', '') \
        .strip() \
        .lower()
    return v in ['y', 'yes', 'yeahh']


def ask_for_enter():
    input('Press enter to continue...')


def fetch_secret(hub, name: str, **kwargs):
    if kwargs.get('simulate', False):
        return 'secret'
    return hub.read(name)
