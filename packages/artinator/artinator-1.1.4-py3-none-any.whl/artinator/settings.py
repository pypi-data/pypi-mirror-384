"""
Define artinator settings.

.. envvar:: MODE

    By default, mode is "system" if no ".git" is found in the current working
    directory or above, otherwise it's "project". You can override this with
    the MODE environment variable.

    When mode is "project": artinator will create an SQLite database in
    ./.artinator to store the repomap, and store the contexts in there.

    When mode is "system": artinator will save contexts in ~/.artinator, and
    won't bother with a repomap.

.. envvar:: REPO_PATH

    Path to your project repository if any, by default we try to find a .git
    directory in the current working directory or any above directory.

.. envvar:: ARTINATOR

    Path to the home directory of artinator, by default: in project mode it's
    REPO_PATH/.artinator, in system mode it's ~/.artinator.

    This is where we store history and other project metadata if any project.
"""
from pathlib import Path
import cli2
import os


def is_git_repo(path=None):
    """
    Check if the current directory or any parent directory is a Git repository.
    Returns the path to the .git directory if found, None otherwise.
    """
    if path is None:
        path = os.getcwd()

    current_path = os.path.abspath(path)

    while True:
        git_path = os.path.join(current_path, '.git')
        if os.path.isdir(git_path):
            return current_path

        # Move up to parent directory
        parent_path = os.path.dirname(current_path)

        # If we've reached the root directory, stop
        if parent_path == current_path:
            return None

        current_path = parent_path

REPO_PATH = os.getenv('REPO_PATH')
if 'MODE' in os.environ:
    MODE = os.getenv('MODE')
else:
    if REPO_PATH := is_git_repo():
        MODE = 'project'
    else:
        MODE = 'system'

if REPO_PATH:
    HOME = Path(os.path.join(REPO_PATH)).absolute() / '.artinator'
else:
    HOME = Path(os.path.join(os.getenv('HOME'))).absolute() / '.artinator'
