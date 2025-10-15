import typing
from HorusAPI import PluginBlock as PluginBlock
from _typeshed import Incomplete

class SingletonMeta(type):
    """
    This is a thread-safe implementation of Singleton.

    Intened for internal use only.
    """
    def __call__(cls, *args, **kwargs):
        """
        Possible changes to the value of the `__init__` argument do not affect
        the returned instance.
        """

class TempFile:
    """Temporary file class used to store temporary files in user dirs"""
    name: Incomplete
    tmpFolder: Incomplete
    path: Incomplete
    def __init__(self, name: str, folder: typing.Optional[str] = None) -> None:
        """
        - Name: The name of the file.
        - Folder: The folder where the file will be stored.
        If None, the file will bestored in the tmp folder.
        """
    def __eq__(self, other): ...
    def __hash__(self): ...
    def __del__(self) -> None: ...
    def delete(self) -> None:
        """
        Delete the file.
        """
    def write(self, content: str):
        """
        Write content to the file

        - content: The content to write to the file.
        """
    def read(self):
        """
        Read the content of the file

        :return: The content of the file as a string.
        """
    def deleteTmpFolder(self) -> None:
        """
        Deletes the tmp folder.
        """

def getUserFolder() -> str:
    """
    Returns the current logged in user's folder
    """
def sanitizePath(path: str):
    """
    Replaces any invalid character in a path
    """
def structureToFile(structure: dict, filePathToWrite: typing.Optional[str] = None) -> str:
    """
    Save one structure in the correct format.
    """
def multipleStructuresToFolder(structureList: list, path: typing.Optional[str] = None) -> str:
    """
    Save more than one Mol* structure into a folder
    """

class ResetRemoteException(Exception):
    """
    Exception raised when the remote server is reset.
    """

def initPlugin() -> None:
    """
    This function will create the basic folder structure for building
    a Horus plugin.
    """
def path_exists_local(path: str) -> bool:
    """
    Checks whether the given path exists locally.
    """
def path_exists_remote(block: PluginBlock, path: str) -> bool:
    """
    Checks whether the given path exists remotely.
    """
def path_exists(block: PluginBlock, path: str) -> bool:
    """
    Checks whether the given path exists wherever the block is running (locally or remotely).
    For remote execution, checks both local and remote existence.
    """
def dir_name_exists_in_both_contexts(block: PluginBlock, dir_name: str) -> bool:
    """
    Checks if a directory name exists in both local and remote parent directories.
    This ensures the same directory name can be used consistently.
    """
def get_unique_dir_name(block: PluginBlock, base_name: str) -> str:
    """
    Returns a unique directory name that doesn't exist in either local or remote context.
    This ensures the same directory name can be used for both local and remote paths.

    Parameters
    ----------
    block : PluginBlock
        The block in which context the directory name is being generated.
    base_name : str
        The base directory name.

    Returns
    -------
    str
        A unique directory name, guaranteed not to exist in either context.
    """
def get_unique_path(block: PluginBlock, path: str) -> str:
    """
    Returns a unique path for the given block context.
    If it exists (locally or remotely), it creates a new path with a numeric suffix.
    If it does not exist, it returns the original path.
    If the path is a file, the suffix is inserted before the extension.

    Parameters
    ----------
    block : PluginBlock
        The block in which context the path is being generated.
    path : str
        The original path.

    Returns
    -------
    str
        A unique path, guaranteed not to exist in the block's runtime context.
    """
