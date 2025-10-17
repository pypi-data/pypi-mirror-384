# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# See the License at http://www.apache.org/licenses/LICENSE-2.0
# Distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND.

"""
derived
---------

This is used as the source relation for derived values.
"""

from orso.schema import RelationSchema

from opteryx.models import RelationStatistics

__all__ = ("schema",)


def schema():
    return RelationSchema(name="$derived", columns=[])


def statistics() -> RelationStatistics:
    return RelationStatistics()
