from __future__ import annotations

from typing import Any, Optional

from flask_inputfilter.exceptions import ValidationError
from flask_inputfilter.models import BaseValidator


class XorValidator(BaseValidator):
    """
    Validates that the input passes exactly one of the provided validators.
    This composite validator ensures that the input does not pass zero or more
    than one of the specified validators.

    **Parameters:**

    - **validators** (*list[BaseValidator]*): A list of validators,
      of which exactly one must pass.
    - **error_message** (*Optional[str]*): Custom error message if the
      input does not satisfy exactly one validator.

    **Expected Behavior:**

    The validator applies each validator in the provided list to the input
    value and counts the number of validators that pass without raising a
    ``ValidationError``. If exactly one validator passes, the input is
    considered valid; otherwise, a ``ValidationError`` is raised with the
    provided or default error message.

    **Example Usage:**

    .. code-block:: python

        class XorInputFilter(InputFilter):
            value: int | string = field(validators=[
                XorValidator([IsIntegerValidator(), IsStringValidator()])
            ])
    """

    __slots__ = ("error_message", "validators")

    def __init__(
        self,
        validators: list[BaseValidator],
        error_message: Optional[str] = None,
    ) -> None:
        self.validators = validators
        self.error_message = (
            error_message or "No or multiple validators succeeded."
        )

    def validate(self, value: Any) -> None:
        success_count = 0
        for validator in self.validators:
            try:
                validator.validate(value)
                success_count += 1
            except ValidationError:
                pass

        if success_count != 1:
            raise ValidationError(self.error_message)
