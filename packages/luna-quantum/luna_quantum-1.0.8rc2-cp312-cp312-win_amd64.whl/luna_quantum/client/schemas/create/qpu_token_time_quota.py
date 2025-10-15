from __future__ import annotations

from typing import Self

from pydantic import BaseModel, Field, model_validator

from luna_quantum.client.schemas.wrappers import PydanticDatetimeWrapper


class QpuTokenTimeQuotaIn(BaseModel):
    """
    Pydantic model for creating a time quota on a qpu token.

    Attributes
    ----------
    quota: int
        The amount of quota.
    start: datetime | None
        Effective start date of the time quota policy.
        If None, policy will be in effect immediately.
    end: datetime | None
        Effective end date of the time quota policy.
        If None, policy will be in effect until 365 days after the start date.
    """

    quota: int = Field(ge=0)
    start: PydanticDatetimeWrapper | None
    end: PydanticDatetimeWrapper | None

    @model_validator(mode="after")
    def check_start_end_dates(self) -> Self:
        """Cheks that start date is befor end date if both provided."""
        if self.start is not None and self.end is not None and self.start > self.end:
            raise ValueError("Start date cannot be after end date.")  # noqa: TRY003
        return self
