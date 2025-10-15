from pydantic import BaseModel

from luna_quantum.client.schemas.wrappers.datetime_wrapper import (
    PydanticDatetimeWrapper,
)


class QpuTokenTimeQuotaOut(BaseModel):
    """
    Pydantic model for QPU token time quota OUT.

    It contains the data received from the API call.

    Attributes
    ----------
    quota: int
        The total amount of quota available on a qpu token.
    start: datetime
        Effective start date of the time quota policy.
    end: datetime
        Effective end date of the time quota policy.
    quota_used: int
        How much quota has already been used from
        the totally available amount of quota.
    """

    quota: int
    start: PydanticDatetimeWrapper
    end: PydanticDatetimeWrapper
    quota_used: int
