from typing import Annotated

from fastapi import Depends

type Inject[T, *Metadata] = Annotated[T, Depends(...), *Metadata]

type InjectThreadSafe[T, *Metadata] = Inject[T, *Metadata]
