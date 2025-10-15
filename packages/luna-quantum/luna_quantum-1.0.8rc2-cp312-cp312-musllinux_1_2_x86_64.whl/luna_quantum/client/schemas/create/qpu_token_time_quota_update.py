from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from luna_quantum.client.schemas.wrappers.datetime_wrapper import (
    PydanticDatetimeWrapper,
)


class QpuTokenTimeQuotaUpdate(BaseModel):
    """Data structure to update the time quota of a qpu token."""

    quota: int | None = Field(ge=0, default=None)
    start: PydanticDatetimeWrapper | None = None
    end: PydanticDatetimeWrapper | None = None

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def check_start_end_dates(self) -> Self:
        """Cheks that start date is befor end date if both provided."""
        if self.start is not None and self.end is not None and self.start > self.end:
            raise ValueError("Start date cannot be after end date.")  # noqa: TRY003
        return self
