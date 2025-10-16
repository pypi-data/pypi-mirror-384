import posixpath
from collections.abc import Callable, Iterable, Sequence
from functools import reduce
from pathlib import Path
from typing import Self, TypeVar

from storix.sandbox import PathSandboxer
from storix.typing import StrPathLike

T = TypeVar("T")
U = TypeVar("U")
V = TypeVar("V")


def pipeline[**P, R](*funcs: Callable[P, R]) -> Callable[P, R]:
    """Compose multiple functions into a single pipeline."""

    def compose_two(f: Callable[[U], V], g: Callable[[T], U]) -> Callable[[T], V]:
        """Compose two functions."""
        return lambda x: f(g(x))

    return reduce(compose_two, reversed(funcs), lambda x: x)  # type: ignore


class PathLogicMixin:
    """Mixin for shared path logic between sync and async BaseStorage.

    Expects the inheriting class to provide:
        - self._min_depth: Path
        - self._current_path: Path
        - self._home: Path
        - self._sandbox: PathSandboxable | None
        - self.home: property returning Path
        - self.pwd(): method returning Path
    """

    _min_depth: Path
    _current_path: Path
    _home: Path
    _sandbox: PathSandboxer | None

    def _parse_dots(self, path: StrPathLike, *, graceful: bool = True) -> Path:
        path = Path(path)
        bk_cnt: int = str(path).count("..")
        if bk_cnt:
            bk_cnt += 1
        target_path = eval(f"path{'.parent' * bk_cnt}")
        # ignore[attr-defined] because 'home' is guaranteed by inheriting class
        if target_path >= Path(self.home):  # type: ignore[attr-defined]
            return target_path
        if not graceful:
            raise ValueError(f"Cannot go back deeper than current path: {path}")
        return Path(self.home)  # type: ignore[attr-defined]

    def _parse_home(self, path: StrPathLike) -> Path:
        # ignore[attr-defined] because 'home' is guaranteed by inheriting class
        return Path(str(path).replace("~", str(self.home)))  # type: ignore[attr-defined]

    def _makeabs(self, path: StrPathLike) -> Path:
        path = Path(path)
        if path.is_absolute():
            return path
        # ignore[attr-defined] because 'pwd' is guaranteed by inheriting class
        return self.pwd() / path  # type: ignore[attr-defined]

    def _topath(self, path: StrPathLike | None) -> Path:
        sb = getattr(self, "_sandbox", None)

        path_str = str(path).strip()
        if not path or path_str == ".":
            # ignore[attr-defined] because 'pwd' is guaranteed by inheriting class
            path = self.pwd()  # type: ignore[attr-defined]
        elif path_str == "~":
            # ignore[attr-defined] because 'home' is guaranteed by inheriting class
            path = Path(self.home)  # type: ignore[attr-defined]
        else:
            p = Path(path)
            if sb and not p.is_absolute():
                # ignore[attr-defined] because '_current_path' is guaranteed by inheriting class
                path = self._current_path / p  # type: ignore[attr-defined]

        if sb:
            path = Path(sb.to_real(path))
            path = path.resolve()
            try:
                path.relative_to(sb.get_prefix().resolve())
            except ValueError as err:
                raise ValueError(f"Path '{path}' escapes sandbox boundaries") from err
        else:
            path = pipeline(
                self._parse_dots,
                self._parse_home,
                self._makeabs,
            )(path)
            path = Path(path)
        return path

    def chroot(self, new_root: StrPathLike) -> Self:
        """Change storage root to a descendant path reconstructing the storage."""
        initialpath = self._topath(new_root)
        return self._init_storage(initialpath=initialpath)

    def pwd(self) -> Path:
        """Return the current working directory."""
        return self._current_path

    def parent(self, path: StrPathLike) -> Path:
        """The logical parent of the path."""
        return self._topath(path).parent

    def parents(self, path: StrPathLike) -> Sequence[Path]:
        """A sequence of this path's logical parents."""
        path = self._topath(path)

        return path.parents

    def is_root(self, path: StrPathLike) -> bool:
        """Check if a path is the root of a filesystem.

        Note: root here can be a sandboxed virtual root.
        """
        root = getattr(self, "root", None)
        if not root:
            raise AttributeError(
                "Cannot check whether or not a path is root, when property 'root' is "
                f"undefined for class: {self.__class__.__name__}"
            )

        return self._topath(path) == root

    def _init_storage(self, initialpath: StrPathLike) -> Self:
        initialpath = self._prepend_root(initialpath)
        self._min_depth = self._home = self._current_path = initialpath
        return self

    def _prepend_root(self, path: StrPathLike | None = None) -> Path:
        if path is None:
            return Path("/")
        return Path("/") / str(path).lstrip("/")

    def _filter_hidden[T: StrPathLike](self, output: Iterable[T]) -> Iterable[T]:
        return filter(lambda q: not Path(q).name.startswith("."), output)


def craft_adlsg2_url(*, account_name: str) -> str:
    """Structure an Azure Datalake Gen2 URL."""
    return f"https://{account_name}.dfs.core.windows.net"


def craft_adlsg2_url_sas(
    *, account_name: str, container: str, directory: str, filename: str, sas_token: str
) -> str:
    """Structure an Azure Datalake Gen2 URL with a SAS token embedded."""
    base_url = craft_adlsg2_url(account_name=account_name)
    path = posixpath.join(*(p.strip("/") for p in (container, directory, filename)))
    return f"{base_url}/{path}?{sas_token.lstrip('?')}"


def get_mimetype(*, buf: bytes) -> str:
    """Detect mimetype from a buffer."""
    import magic

    return magic.from_buffer(buf, mime=True)


def to_data_url(*, buf: bytes, mimetype: str | None = None) -> str:
    """Create a data url."""
    template = "data:{mimetype};base64,{base64_data}"

    b64_data = _b64_encode(buf=buf)
    mimetype = mimetype or get_mimetype(buf=buf)

    return template.format(mimetype=mimetype, base64_data=b64_data)


def _b64_encode(*, buf: bytes) -> str:
    import base64

    return base64.b64encode(buf).decode("utf-8")
