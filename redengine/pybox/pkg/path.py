
from pathlib import Path
from typing import Union

def find_package_root(path) -> Union[Path, None]:
    """Find package root from the path's parents.
    
    In other words, find first dir that don't contain
    __init__.py"""

    for i, path in enumerate(Path(path).parents):
        # Check whether "path/.git" exists and is a directory
        init_file = path / "__init__.py"
        if not init_file.is_file():
            if i == 0:
                # There is no package (no __init__.py file at all)
                return None
            return path
    else:
        raise FileExistsError("No package root found.")
