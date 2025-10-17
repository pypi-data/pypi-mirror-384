from typing import Annotated

from pydantic import StringConstraints

NonEmptyStr = Annotated[str, StringConstraints(min_length=1)]
TrimmedNonEmptyStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
