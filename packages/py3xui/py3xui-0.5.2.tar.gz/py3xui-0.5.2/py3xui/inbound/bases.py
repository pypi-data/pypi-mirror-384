"""This module contains the base classes for the inbound models."""

import json

from pydantic import BaseModel, model_validator


# pylint: disable=too-few-public-methods
class JsonStringModel(BaseModel):
    """Base class for models that have a JSON string as a field."""

    @model_validator(mode="before")
    def model_validate(
        cls,
        values,
    ):  # pylint: disable=no-self-argument, arguments-differ
        """Converts the JSON string to a dictionary if it is a string.

        Args:
            values (Any): The values to validate.

        Returns:
            Any: The validated values.
        """
        if isinstance(values, str):
            try:
                return json.loads(values)
            except json.JSONDecodeError:
                pass
        return values
