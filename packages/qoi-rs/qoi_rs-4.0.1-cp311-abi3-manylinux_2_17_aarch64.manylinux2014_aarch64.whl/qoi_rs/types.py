from collections.abc import Sequence, Buffer
from typing import Literal, Protocol, runtime_checkable, Never, TYPE_CHECKING

__all__ = "Data", "Image"

if TYPE_CHECKING:
    try:
        from PIL.Image import Image as PillowImage
    except ModuleNotFoundError:
        PillowImage = Never
else:
    PillowImage = Never


class ArrowArrayExportable(Protocol):
    # SEE: https://arrow.apache.org/docs/format/CDataInterface/PyCapsuleInterface.html#protocol-typehints
    def __arrow_c_array__(
        self,
        requested_schema: object | None = None
    ) -> tuple[object, object]:
        pass


class ArrowArrayExportableImage(ArrowArrayExportable):
    @property
    def width(self) -> int:
        pass

    @property
    def height(self) -> int:
        pass


type Data = (
    Sequence[tuple[int, int, int]]
    | Sequence[tuple[int, int, int, int]]
    | Sequence[int]
    | bytes
    | bytearray
    | Buffer
    | ArrowArrayExportable
    | PillowImage
)

type ColourSpace = Literal["SRGB", "linear"]

type RawChannels = Literal[
    "RGB",
    "BGR",
    "RGBA",
    "ARGB",
    "RGBX",
    "XRGB",
    "BGRA",
    "ABGR",
    "BGRX",
    "XBGR",
]
type Mode = Literal["RGB", "RGBA"]

@runtime_checkable
class Image(Protocol):
    @property
    def width(self) -> int: pass
    @property
    def height(self) -> int: pass
    @property
    def data(self) -> bytes: pass
    @property
    def channels(self) -> int: pass
    @property
    def colour_space(self) -> ColourSpace: pass
    @property
    def mode(self) -> Mode: pass
