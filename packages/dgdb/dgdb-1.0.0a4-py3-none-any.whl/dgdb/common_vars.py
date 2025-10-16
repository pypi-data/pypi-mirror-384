import os
from typing import TypeAlias, Literal, Union


# Type aliases
ConnectionFields: TypeAlias = Literal["engine", "conn", "metadata"]
SQLSource = Union[str, os.PathLike]