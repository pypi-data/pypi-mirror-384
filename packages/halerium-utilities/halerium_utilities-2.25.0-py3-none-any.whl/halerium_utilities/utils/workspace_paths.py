import os
from pathlib import Path


RUNNER_MOUNT_POINT = "/home/jovyan"


def runner_path_to_workspace_path(path):
    """
    Transforms a runner path like "/home/jovyan/my/folder/file.txt" to
    a workspace path like "/my/folder/file.txt"
    Relative runner paths are first resolved with respect to the current working directly.

    Parameters
    ----------
    path : str or Path
        the runner path

    Returns
    -------
    str : the workspace path
    """
    runner_path = Path(path).resolve()
    workspace_path = runner_path.relative_to(RUNNER_MOUNT_POINT)
    workspace_path = str(workspace_path)
    workspace_path = "/" + workspace_path.lstrip("/")
    return workspace_path


def workspace_path_to_runner_path(path):
    """
    Transforms a runner path like "/my/folder/file.txt" or "my/folder/file.txt" to
    a workspace path like "/home/jovyan/my/folder/file.txt"

    Parameters
    ----------
    path : str or Path
        the workspace path

    Returns
    -------
    str : the runner path
    """
    path = str(path)
    workspace_path = path.lstrip("/")
    runner_path = os.path.join(RUNNER_MOUNT_POINT, workspace_path)

    return runner_path

