"""lifetime(age) transform plugin module"""

from collections.abc import Sequence

from cmem_plugin_base.dataintegration.description import (
    Plugin,
    PluginParameter,
)
from cmem_plugin_base.dataintegration.plugins import TransformPlugin
from cmem_plugin_base.dataintegration.types import BoolParameterType, IntParameterType
from ulid import ULID

URN_PREFIX = "urn:x-ulid:"


@Plugin(
    label="ULID",
    plugin_id="cmem-plugin-ulid",
    description="Generate ULID strings - Universally Unique Lexicographically"
    " Sortable Identifiers.",
    categories=["Value", "Identifier"],
    documentation="""
ULID is a proposed identifier scheme, which produces time-based, random
and sortable strings. The following features are highlighted
[in the specification](https://github.com/ulid/spec):

- 128-bit compatibility with UUID
- 1.21e+24 unique ULIDs per millisecond
- Lexicographically sortable!
- Canonically encoded as a 26 character string, as opposed to the 36 character UUID
- Uses Crockford's base32 for better efficiency and readability (5 bits per character)
- Case insensitive
- No special characters (URL safe)
- Monotonic sort order (correctly detects and handles the same millisecond)

This transform plugin allows for creation of ULID based identifiers (plain or URN).
It does not support any input entities.
""",
    parameters=[
        PluginParameter(
            name="number_of_values",
            label="Number of Values",
            description="Number of values to generate per entity.",
            default_value=1,
            param_type=IntParameterType(),
        ),
        PluginParameter(
            name="generate_urn",
            label="Generate URNs",
            description=f"Generate '{URN_PREFIX}*' strings.",
            param_type=BoolParameterType(),
        ),
    ],
)
class ULIDTransformPlugin(TransformPlugin):
    """ULID Transform Plugin"""

    def __init__(self, number_of_values: int = 1, generate_urn: bool = False):
        if number_of_values < 1:
            raise ValueError("Number of Values needs to be a positive integer.")

        self.number_of_values = number_of_values
        self.generate_urn = generate_urn

    def transform(self, inputs: Sequence[Sequence[str]]) -> Sequence[str]:
        """Transform a collection of values."""
        if inputs:
            raise ValueError("Plugin does not support processing input entities.")
        result = []
        if self.generate_urn:
            for _ in range(self.number_of_values):
                result += [f"{URN_PREFIX}{ULID()}"]
        else:
            for _ in range(self.number_of_values):
                result += [f"{ULID()}"]
        return result
