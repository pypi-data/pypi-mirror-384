from pathlib import Path
from typing import Union

_PACKAGE_NAME = "pyguiadapterlite"
_LOCALES_DIR_NAME = "locales"
_TOOLS_DIR_NAME = "tools"
_IMAGES_DIR_NAME = "images"

# try:
#     from importlib.resources import as_file, files
#     def assets_dir(dir_name: str) -> Path:
#         with as_file(files(_PACKAGE_NAME).joinpath(dir_name)) as path:
#             return path
# except ImportError:
#     import pkg_resources
#     def assets_dir(dir_name: str) -> Path:
#         return Path(os.path.dirname(__file__), dir_name)


def assets_dir(path: Union[str, Path, None] = None):
    if isinstance(path, str):
        path = path.strip()
    path = path or ""
    try:
        from importlib.resources import as_file, files

        with as_file(files(_PACKAGE_NAME).joinpath(path)) as path:
            return path
    except ImportError:
        import pkg_resources

        return Path(pkg_resources.resource_filename(_PACKAGE_NAME, path))


def tools_dir() -> Path:
    return assets_dir(_TOOLS_DIR_NAME)


def locales_dir() -> Path:
    return assets_dir(_LOCALES_DIR_NAME)


def images_dir() -> Path:
    return assets_dir(_IMAGES_DIR_NAME)


def image_file(filename: str) -> Path:
    return images_dir().joinpath(filename)
