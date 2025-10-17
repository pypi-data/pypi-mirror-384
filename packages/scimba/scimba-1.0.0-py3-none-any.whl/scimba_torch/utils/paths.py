"""Path and file utilities for scimba_torch.

Defaults to saving in the user's home directory under the hidden folder
:code:`.scimba/scimba_torch`.
"""

from pathlib import Path

# Constants
S_FILEXT = ".pt"
FOLDER_FOR_SAVED_PROJECTORS = ".scimba/scimba_torch"
DEFAULT_PATH_FOR_SAVING = Path.home()  # Save in the use home directory


def _get_folder_for_save(
    parent_path: Path,
    folder_name: str,
) -> Path:
    """Get the folder path for saving files.

    Args:
        parent_path: The base path where the folder is located.
        folder_name: The name of the folder to be used for saving files.

    Returns:
        The full path to the folder for saving files.
    """
    return parent_path / Path(folder_name)


def _get_filename_from_scriptname(scriptname: str, postfix: str = "") -> str:
    """Get the filename of the currently running script.

    Args:
        scriptname: The name of the current script (usually __file__).
        postfix: An optional postfix to append to the filename.

    Returns:
        The constructed filename with the optional postfix and standard file extension.
    """
    script_path = Path(scriptname)
    filename = script_path.stem
    if len(postfix):
        postfix = "_" + postfix
    s_filename = filename + postfix + S_FILEXT
    return s_filename


def get_filepath_for_save(
    scriptname: str,
    postfix: str = "",
    parent_path: Path = DEFAULT_PATH_FOR_SAVING,
    folder_name: str = FOLDER_FOR_SAVED_PROJECTORS,
) -> Path:
    """Get the filepath of the currently running script.

    This is useful for saving files related to the script in a structured way.
    It creates the parent folder if it does not exist.
    The default location of this folder is :code:`~/.scimba/scimba_torch/`.

    Args:
        scriptname: The name of the current script (usually __file__).
        postfix: An optional postfix to append to the filename.
        parent_path: The base path where the folder is located.
            (default: :code:`~/`)
        folder_name: The name of the folder to be used for saving files.
            (default: :code:`.scimba`)

    Returns:
        The full path to the file with the constructed filename.
    """
    filename = _get_filename_from_scriptname(scriptname, postfix)
    path = _get_folder_for_save(parent_path, folder_name)
    path.mkdir(parents=True, exist_ok=True)
    return path / Path(filename)
