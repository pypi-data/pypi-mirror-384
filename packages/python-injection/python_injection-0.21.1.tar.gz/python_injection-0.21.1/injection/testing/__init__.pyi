from typing import Final

from injection import Module
from injection.loaders import LoadedProfile, ProfileLoader

__MODULE: Final[Module] = ...

reserve_scoped_test_slot = __MODULE.reserve_scoped_slot
set_test_constant = __MODULE.set_constant
should_be_test_injectable = __MODULE.should_be_injectable
test_constant = __MODULE.constant
test_injectable = __MODULE.injectable
test_scoped = __MODULE.scoped
test_singleton = __MODULE.singleton

def load_test_profile(loader: ProfileLoader = ...) -> LoadedProfile:
    """
    Context manager for temporary use test module.
    """
