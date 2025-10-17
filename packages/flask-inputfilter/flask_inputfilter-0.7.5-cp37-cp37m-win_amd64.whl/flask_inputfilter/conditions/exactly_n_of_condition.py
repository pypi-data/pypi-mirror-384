from __future__ import annotations

from typing import Any

from flask_inputfilter.models import BaseCondition


class ExactlyNOfCondition(BaseCondition):
    """
    Checks that exactly ``n`` of the specified fields are present in the input
    data.

    **Parameters:**

    - **fields** (*list[str]*): A list of fields to check.
    - **n** (*int*): The exact number of fields that must be present.

    **Expected Behavior:**

    Counts the number of specified fields present in the data and
    validates that the count equals ``n``.

    **Example Usage:**

    .. code-block:: python

        class ExactFieldsFilter(InputFilter):
            field1 = field()

            field2 = field()

            field3 = field()

            condition(
                ExactlyNOfCondition(
                    fields=['field1', 'field2', 'field3'],
                    n=2
                )
            )
    """

    __slots__ = ("fields", "n")

    def __init__(self, fields: list[str], n: int) -> None:
        self.fields = fields
        self.n = n

    def check(self, data: dict[str, Any]) -> bool:
        return (
            sum(1 for field in self.fields if data.get(field) is not None)
            == self.n
        )
