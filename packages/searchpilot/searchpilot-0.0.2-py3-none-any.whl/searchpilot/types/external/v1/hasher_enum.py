# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing_extensions import Literal, TypeAlias

__all__ = ["HasherEnum"]

HasherEnum: TypeAlias = Literal[
    "carbon.hashers.base.simple",
    "carbon.hashers.base.random_by_percent",
    "carbon.hashers.base.random_by_percent_2",
    "carbon.hashers.base.random_by_percent_3",
    "carbon.hashers.base.random_by_percent_4",
    "carbon.hashers.base.random_by_percent_5",
    "carbon.hashers.base.hash_variable",
    "carbon.hashers.base.variable_matches",
    "carbon.hashers.base.cro_random_user",
    "carbon.hashers.base.cro_always_control",
]
