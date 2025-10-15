from __future__ import annotations

# Limit how much we import. This module is loaded at Python startup!!!
# Don't import things until they are needed.
import re
import sys
from importlib.abc import MetaPathFinder
from importlib.machinery import ModuleSpec, SourceFileLoader
from importlib.util import spec_from_loader
from pathlib import Path
import traceback



if False: # TYPE_CHECKING
    from os import PathLike
    from collections.abc import Buffer, Sequence
    from ast import Expression, Interactive, Module
    from types import CodeType, ModuleType

magic_line = re.compile(r"\s*#\s*future[\-\_]tstrings\s*(#.*)?$")

def is_tstring_file(fp: Path) -> bool:
    in_doc: str | None = None
    with fp.open("r", errors="ignore") as f:
        for _, line in zip(range(3), f):
            if magic_line.match(line):
                return True

    return False


def _decode_path(path: str | PathLike | Buffer) -> str:
    if isinstance(path, str):
        return path
    try:
        return str(Path(path))  # type: ignore
    except Exception:
        return bytes(path).decode()  # type: ignore


class TstringFileFinder(MetaPathFinder):
    def find_spec(
        self,
        fullname: str,
        path: Sequence[str] | None,
        target: ModuleType | None = None,
    ) -> ModuleSpec | None:
        try:
            if target is not None:
                return None

            name = fullname.split(".")[-1]
            if path is None:
                path = sys.path
            for dir in path:
                for file in Path(dir).glob(f"{name}.[pP][yY]"):
                    file = file.resolve()
                    if is_tstring_file(file):
                        return spec_from_loader(
                            name=fullname,
                            loader=FutureTstringsLoader(
                                fullname=fullname, path=str(file)
                            ),
                        )
                    return None
        except (FileNotFoundError, PermissionError):
            pass
        except Exception:
            if "file" in locals():
                print(
                    f"Exception ignored in importer while importing file {file!s}: ",
                    file=sys.stderr,
                )
            else:
                print(
                    f"Exception ignored while importing '{fullname}'",
                    file=sys.stderr
                )
            traceback.print_exc(file=sys.stderr)


        return None


tstring_importer = TstringFileFinder()


class FutureTstringsLoader(SourceFileLoader):
    def __init__(self, fullname: str, path: str) -> None:
        super().__init__(fullname, path)

    def source_to_code(  # type: ignore
        self,
        data: Buffer | str | Module | Expression | Interactive,
        path: Buffer | str | PathLike[str] = "",
    ) -> CodeType:
        from ast import AST
        from future_tstrings.parser import compile_to_ast

        path = _decode_path(path)

        if isinstance(data, str):
            pass
        elif isinstance(data, AST):
            # already valid Python AST
            return super(FutureTstringsLoader, self).source_to_code(data, path)
        else:
            data = bytes(data).decode()

        ast = compile_to_ast(data, mode="exec", filepath=path)

        return super().source_to_code(ast, path)


def install_import_hook():
    sys.meta_path.insert(0, tstring_importer)


def uninstall_import_hook():
    try:
        sys.meta_path.remove(tstring_importer)
    except ValueError:
        pass
