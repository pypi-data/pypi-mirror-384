from re import sub
from os import getenv
from string import punctuation
from gitlab_ps_utils.logger import myLogger

log = myLogger(__name__, app_path=getenv('APP_PATH', '.'),
               log_name=getenv('APP_NAME', 'application'))

def sanitize_name(name, full_path, is_group=False):
    """
    Validate and sanitize group and project names to satisfy the following criteria:
    Name can only contain letters, digits, emojis, '_', '.', dash, space, parenthesis (groups only).
    It must start with letter, digit, emoji or '_'.
    Example:
        " !  _-:: This.is-how/WE do\n&it#? - šđžčć_  ? " -> "This.is-how WE do it - šđžčć"
    """
    # Remove leading and trailing special characters and spaces
    stripped = name.strip(punctuation + " ")

    # Validate naming convention in docstring and sanitize name
    valid = " ".join(sub(
        r"[^\U00010000-\U0010ffff\w\_\-\.\(\) ]" if is_group else r"[^\U00010000-\U0010ffff\w\_\-\. ]", " ", stripped).split())
    if name != valid:
        log.warning(
            f"Renaming invalid {'group' if is_group else 'project'} name '{name}' -> '{valid}' ({full_path})")
        if is_group:
            log.error(
                f"Sub-group '{name}' ({full_path}) requires a rename on source or direct import")
    return valid

def sanitize_project_path(path, full_path):
    """
    Validate and sanitize project paths to satisfy the following criteria:
    Project namespace path can contain only letters, digits, '_', '-' and '.'. Cannot start with '-', end in '.git' or end in '.atom'
    Path can contain only letters, digits, '_', '-' and '.'. Cannot start with '-', end in '.git' or end in '.atom'
    Path must not start or end with a special character and must not contain consecutive special characters.
    Example:
        "!_-::This.is;;-how_we--do\n&IT#?-šđžčć_?" -> "This.is-how_we-do-IT"
    """
    # Validate path convention in docstring and sanitize path
    valid = sub(r"[._-][^A-Za-z0-9]+", "-",
                sub(r"[^A-Za-z0-9\_\-\.]+", "-", path)).strip("-_.")
    if path != valid:
        log.warning(
            f"Updating invalid project path '{path}' -> '{valid}' ({full_path})")
    return valid
