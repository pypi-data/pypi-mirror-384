from . import (
    helpers as helpers,
    pipelines as pipelines,
    types as types
)


def abi_tag() -> str:
    """
    Get the ABI tag of the current module. Useful for debugging when adding external pipelines.
    """
