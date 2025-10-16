from typing import TYPE_CHECKING

from planar.dependencies import lazy_exports

lazy_exports(
    __name__,
    {
        "PlanarDataset": (".dataset", "PlanarDataset"),
        "reset_connection_cache": (".connection", "reset_connection_cache"),
    },
)

if TYPE_CHECKING:
    from .dataset import PlanarDataset

    __all__ = [
        "PlanarDataset",
    ]
