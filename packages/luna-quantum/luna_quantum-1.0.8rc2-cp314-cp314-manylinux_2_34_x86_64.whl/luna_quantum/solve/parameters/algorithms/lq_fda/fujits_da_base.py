from __future__ import annotations

from typing import Literal

from pydantic import Field

from luna_quantum.solve.domain.abstract import LunaAlgorithm
from luna_quantum.solve.parameters.backends import Fujitsu


class FujitsuDABase(LunaAlgorithm[Fujitsu]):
    """Fujitsu Digital Annealer base parameters.

    Parameters
    ----------
    scaling_action: Literal["NOTHING", "SCALING", "AUTO_SCALING"]
        Method for scaling ``qubo`` and determining temperatures:
        - "NOTHING": No action (use parameters exactly as specified)
        - "SCALING": ``scaling_factor`` is multiplied to ``qubo``,
          ``temperature_start``, ``temperature_end`` and ``offset_increase_rate``.
        - "AUTO_SCALING": A maximum scaling factor w.r.t. ``scaling_bit_precision``
          is multiplied to ``qubo``, ``temperature_start``, ``temperature_end`` and
          ``offset_increase_rate``.
    scaling_factor: int | float
        Multiplicative factor applied to model coefficients, temperatures, and other
        parameters: the ``scaling_factor`` for ``qubo``, ``temperature_start``,
        ``temperature_end`` and ``offset_increase_rate``.
        Higher values can improve numerical precision but may lead to overflow.
        Default is 1.0 (no scaling).
    scaling_bit_precision: int
        Maximum bit precision to use when scaling. Determines the maximum allowable
        coefficient magnitude. Default is 64, using full double precision.
    random_seed: Union[int, None]
        Seed for random number generation to ensure reproducible results.
        Must be between 0 and 9_999. Default is None (random seed).
    penalty_factor: float
        Penalty factor used to scale the equality constraint penalty function,
        default 1.0.
    inequality_factor: int
        Penalty factor used to scale the inequality constraints, default 1.
    remove_ohg_from_penalty: bool
        If equality constraints, identified to be One-Hot constraints are only
        considered within one-hot groups (`remove_ohg_from_penalty=True`), i.e.,
        identified one-hot constraints are not added to the penalty function,
        default True.
    """

    scaling_action: Literal["NOTHING", "SCALING", "AUTO_SCALING"] = "NOTHING"
    scaling_factor: int | float = 1.0
    scaling_bit_precision: int = 64
    random_seed: int | None = Field(default=None, ge=0, le=9_999)

    penalty_factor: float = 1.0
    inequality_factor: int = 1
    remove_ohg_from_penalty: bool = True

    @classmethod
    def get_default_backend(cls) -> Fujitsu:
        """
        Return the default backend implementation.

        This property must be implemented by subclasses to provide
        the default backend instance to use when no specific backend
        is specified.

        Returns
        -------
            IBackend
                An instance of a class implementing the IBackend interface that serves
                as the default backend.
        """
        return Fujitsu()

    @classmethod
    def get_compatible_backends(cls) -> tuple[type[Fujitsu], ...]:
        """
        Check at runtime if the used backend is compatible with the solver.

        Returns
        -------
        tuple[type[IBackend], ...]
            True if the backend is compatible with the solver, False otherwise.

        """
        return (Fujitsu,)
